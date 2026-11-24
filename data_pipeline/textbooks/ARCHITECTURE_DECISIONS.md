# Architecture Decisions

This file records the significant design decisions of the six-textbook data
preparation pipeline: what existed, what problem was found, which alternatives
were considered, what was chosen and why. Each decision lists the affected files
and its compatibility impact.

Decisions are numbered `AD-01` … `AD-14`. The complete system description is in
[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md); the list of concrete code
changes is in [FINAL_CHANGELOG.md](FINAL_CHANGELOG.md).

---

## Starting point (the existing architecture)

At the start of this work the project contained six book folders. Each folder
had three scripts run in order — `main.py` → `chunking.py` → `validation.py` —
writing `output/pages.json`, `output/chunks.json` and
`output/validation_report.json`.

| Book | State of the code | State of the outputs |
|---|---|---|
| ICT Primary 4 | Original reference implementation | Valid for ICT P4 |
| ICT Primary 5 | ICT design, adapted for grade 5 | Valid for ICT P5 |
| Science Primary 4 | Own implementation (questions classified, activities, page types) | Valid for Science P4 |
| Science Primary 5 | **Byte-identical copy of ICT P4's three scripts** | **Identical to ICT P4's outputs** |
| English Primary 4 | **Byte-identical copy of ICT P4's three scripts** | **Identical to ICT P4's outputs** |
| English Primary 5 | **Byte-identical copy of ICT P4's three scripts** | **Identical to ICT P4's outputs** |

The three copied books read `ICT_P4_T1/ICT_ARABIC_Prim4_TR1_transcription.txt`,
a path that does not exist in their folders, so their outputs were stale ICT P4
data (same MD5 hash). The copies were intentional templates for code format
(see the project brief); they had never been adapted to their books.

The ICT design philosophy that was kept:

* one standalone folder per book, three scripts, readable top-to-bottom code
  separated by `#----------- Section -------------` comments;
* an explicit, hand-verified structure map (unit / lesson page ranges) instead
  of guessing structure from text;
* `raw_content` (untouched source) next to `processed_content` (cleaned);
* chunk IDs built from unit, lesson, page and a per-page counter.

---

## AD-01 Keep standalone book folders; share logic by identical files, not by a package

**Problem.** Some logic is now common (validation for all six books, chunking
for each subject pair). A shared Python package would avoid duplicated code.

**Alternatives considered.**

1. A shared module (e.g. `common/pipeline.py`) imported by every script.
   Requires `sys.path` manipulation or packaging, changes how every script is
   run, and breaks the ability to copy or run one book folder on its own.
2. Configuration-driven single pipeline for all books. Large rewrite; would
   force the six books into one internal logic, which the books do not share.
3. **Chosen:** keep each folder standalone. Where logic is genuinely common,
   the *same file* is placed in each folder:
   * `validation.py` is identical in all six folders (the expected `book_id`
     is read from the folder name);
   * `chunking.py` is identical for English P4/P5 and for Science P4/P5
     (each pair is one textbook series with one layout);
   * ICT P4 and ICT P5 keep their own original `chunking.py` files.

**Why.** Smallest change that keeps the original organisation and run
commands. All book-specific facts (paths, maps, cleaning rules) live in each
book's `main.py`, so the shared files contain no book-specific constants.

**Trade-off.** A fix to a shared file must be copied to its sibling folders.
The maintenance guide (PROJECT_DOCUMENTATION.md, section N) gives the exact
copy commands, and `validate_corpus.py` fails if a book's report is stale.

**Affected files.** All `validation.py`; English and Science `chunking.py`.

---

## AD-02 Keep every PDF page in `pages.json`; flag non-learning pages instead of deleting them

**Existing.** ICT P4 deleted 19 "cover pages", ICT P5 deleted 9 pages and
Science P4 deleted 8 pages from `pages.json`. Science P4 additionally forced
`include_in_rag = true` on all remaining pages.

**Problem.** Deleted pages cannot be traced; the page count could not be
checked against the PDF; the reason for an exclusion was only a code comment.
ICT P4 also mapped the Unit 2 divider (page 29) and the copyright page (55) to
lessons — hidden only because those pages were deleted.

**Chosen.** `pages.json` contains every PDF page. New fields:

| Field | Meaning |
|---|---|
| `page_type` | `content`, `front_matter`, `back_matter`, `unit_divider`, `lesson_divider`, `blank`, `notes` |
| `include_in_rag` | `true` only for learning pages; chunkers process only these |
| `exclusion_reason` | Human-readable reason for every excluded page, else `null` |

**Benefits.** Full PDF provenance; validation checks the page sequence
`1..N`; every exclusion has an explicit, reviewable reason.

**Compatibility.** Consumers of `pages.json` must filter on
`include_in_rag == true` to get the previous set of learning pages. The number
of learning pages for ICT P4 (36), ICT P5 (37) and Science P4 (98) is unchanged.

---

## AD-03 One shared page and chunk metadata schema

**Problem.** The six books will be merged. The original chunk metadata had no
book, subject, grade, term or language, so merged chunks could not be traced
to a book. English and Science also need to represent pages that are not
numbered lessons.

**Chosen.** Common fields on every page and every chunk:

* identity: `book_id`, `subject`, `grade`, `term`, `language`;
* structure: `unit_id`, `unit_title`, `lesson_id`, `lesson_title`,
  `section_type`, `section_title`;
* provenance: `pdf_page_index`, `printed_page_number`;
* pages also carry `unit_type` (`unit` or `chapter`).

Type-specific fields (question numbers, exercise instruction, activity
components…) are optional extras. The original field names were kept.

**Compatibility.** All previous metadata keys keep their names and meaning;
fields were only added. `validate_corpus.py` enforces the common keys.

---

## AD-04 Chunk IDs: book prefix + the original convention

**Existing.** `U{unit}_L{lesson}_P{page}_C{nnn}` — unique inside one book.

**Problem (measured).** Across the current six books, **487 of 1,291**
chunk IDs would collide without a book prefix. In the original outputs
674 of 956 chunks shared an ID with a chunk of another book.

**Alternatives.** UUIDs (not stable between runs, not readable); content hashes
(change on every text fix). **Chosen:** prefix the original convention with the
folder name:

```
ICT_ARABIC_Prim4_TR1_U2_L4_P44_C003
```

Pages that are not a numbered lesson use a section code in place of `L{n}`:

| Code | section_type | Example |
|---|---|---|
| `OPEN` | `unit_opener` | `English_Prim4_TR1_U1_OPEN_P7_C001` |
| `QR` | `quick_review` | `English_Prim4_TR1_U2_QR_P37_C001` |
| `SA` | `self_assessment` | `English_Prim4_TR1_U1_SA_P22_C001` |
| `REV` | `review` / `chapter_review` | `English_Prim4_TR1_REV_P57_C001`, `Science_ARABIC_Prim4_TR1_U2_REV_P36_C001` |
| `STORY` | `story` | `English_Prim4_TR1_U6_STORY_P98_C001` |
| `GLO` | `glossary` | `English_Prim4_TR1_GLO_P114_C001` |
| `ENR` | `enrichment` | `Science_ARABIC_Prim4_TR1_U1_ENR_P25_C001` |
| `APX` | `appendix` | `Science_ARABIC_Prim4_TR1_APX_P101_C001` |

Uniqueness is guaranteed by `book_id + P{page} + C{counter}` alone; the other
parts are for readability. IDs are stable as long as the page's chunk order
does not change.

**Compatibility.** Every chunk ID changed (prefix added). Any store keyed by old
IDs must be rebuilt — acceptable because no database stage exists yet.

---

## AD-05 Science chapters keep the `unit_id` / `unit_title` field names

**Problem.** Science books are organised in chapters (الفصل), not units.

**Alternatives.** Add `chapter_id`/`chapter_title` fields (two parallel schemas;
every consumer must branch) or rename everything to a neutral name (breaks the
established ICT schema). **Chosen:** keep `unit_id` / `unit_title` for the
top-level division in all books and record `unit_type: "chapter"` on Science
pages (`"unit"` elsewhere).

---

## AD-06 Pages outside numbered lessons get `lesson_id = null` and a `section_type`

**Problem.** Reviews, glossaries, enrichment corners, unit openers and the
Science appendix are not lessons. Science P4 assigned enrichment and review
pages to whichever lesson preceded them, and attached the appendix (pages
101–104) to chapter 8 as an invented "lesson 0".

**Chosen.** Such pages have `lesson_id = null`, `lesson_title = null` and a
`section_type` (`unit_opener`, `quick_review`, `self_assessment`, `review`,
`story`, `glossary`, `enrichment`, `chapter_review`, `appendix`) with a
`section_title` taken from the page heading. Book-level sections (English
reviews and glossary, Science appendix) also have `unit_id = null`.

Validation rule: `lesson` pages require `lesson_id`; unit-level sections require
`unit_id`; book-level sections require neither.

**Two enrichment corners span two chapters** (Science P4 pages 91–92 "الفصل
السادس والسابع", Science P5 pages 53–54 "الفصل ٣ و٤"). They are attached to
the chapter whose page range contains them; the full heading is kept in
`section_title`. A `related_unit_ids` field was considered but not added for two
cases; this is listed as a possible improvement.

---

## AD-07 Explicit structure maps, cross-checked against page headings

**Existing.** ICT and Science P4 use hand-written page-range maps.

**Alternatives.** Detect units/lessons purely from headings (fragile: OCR,
running headers, sub-section titles such as "Where Life Flows" printed under
"Lesson 1" on later pages, printing errors) or keep maps without any check.

**Chosen.** Keep explicit maps as the source of truth (as in ICT) and add an
automatic check in every `main.py` that compares the headings printed on each
page (`الدرس …`, `١-٢ …`, `Lesson N`, `Unit N`, `Review N`) with the map and
prints a `WARNING` on disagreement. The English and Science P5 maps were built
from the page headers and verified with this check (0 disagreements); the only
expected warning is Science P5 page 46 (an untitled picture page, see the test
report).

---

## AD-08 ICT: targeted bug fixes, not a rewrite

**Problems found (measured with a line-coverage audit).**

1. The explanation extractor dropped *every* line starting with a number,
   because numbered lines were assumed to be questions. This deleted numbered
   explanation content: 25 lines in ICT P4 (e.g. the tool names
   `١ الرادار المخترق للأرض:` and three fraud definitions on page 44) and
   50 lines in ICT P5 (e.g. the 7-step "create a new folder" procedure on
   page 21, four security tips on page 28).
2. The question-section instruction (e.g. `اختر الإجابة الصحيحة …`) was not
   stored anywhere.
3. `skip_activity` was never reset and activities ran to the end of the page;
   in ICT P5 the printed page number leaked into all 12 activity chunks.
4. ICT P5: the lesson-title comparison used `r"[\\s.،:：]"`, which matches a
   literal backslash and `s` instead of whitespace.
5. ICT P4: lesson U1-L6 was mapped to page 29 (the Unit 2 divider) and U2-L6
   to pages 54–55 (blank + copyright).
6. Long explanations were cut purely by character count.

**Chosen.** Minimal changes inside the existing functions: a question-region
flag (numbered lines are question content only after a question heading);
`question_instruction` metadata on MCQ and T/F chunks; activities stop at the
next section heading; the trailing page-number line is removed before
extraction; the regex is fixed; the two map ranges are corrected; long
explanations are split before a sub-heading (`digit + space` headings or lines
ending with `:`), never between numbered steps (`digit + dot`).

**Not changed.** Objective / MCQ / T/F / activity detection, headings lists,
cleaning rules, `max_chunk_chars = 1000`, chunk order. The counts of
learning objectives (12/12), MCQs (27/50), T/F (47/43) and activities (12/12)
are identical to the original outputs.

The ICT question instruction is stored in metadata (not prepended to the text)
to keep the ICT chunk text unchanged; English and Science keep the instruction
inside the chunk text because their questions are segmented per exercise.

---

## AD-09 Science: single reading-order segmentation pass

**Existing.** Four independent passes over each page (objectives, questions,
activities, explanations). The explanation pass set `skip_section = True` at
the first objective/activity/question heading and never reset it; the activity
boundaries did not include the `تعلَّم` (learn) heading, and generic words such
as `جرِّب` or `استكشف` were treated as activity headings even inside an activity.

**Why a smaller change was insufficient.** Resetting the flag fixes one
symptom, but four passes over the same lines cannot guarantee that every line
is assigned exactly once (no loss, no duplication) when sections alternate.

**Chosen.** One pass splits each page into blocks in reading order. A block
runs from its heading to the next block heading:

| Heading | Block | Output |
|---|---|---|
| `تعلَّم` | explanation | `explanation` (split > 1000 chars at sub-headings) |
| `نشاط` | activity | one `practical_activity` or `experiment` chunk |
| `حاول`, `تدرَّب`, `مراجعة وتدريب` (exact line) | questions | one chunk per (sub-)question, classified |
| `هيَّا نتوسَّع`, `هيَّا نصنعه!`, `ركن إثرائي`, `هيَّا نُراجع` | enrichment | activity if ≥ 2 numbered steps, else explanation |
| (text before the first heading) | explanation | `explanation` |

The existing helpers were kept (`classify_question`, `split_question_groups`,
`is_metadata_header_only`, `matches_heading`, the `extract_*` names).

**Observed impact.** In the old Science P4 output no text was actually lost
(in that book `تعلَّم` always precedes `نشاط`), so the skip bug was latent; the
new structure removes it for both books. Other corrections: sub-questions
`(٢)` now carry their parent question number (they were stored as question
`٢`); question fragments shorter than 8 characters and explanation parts shorter
than 20 characters are no longer silently discarded; `(١)…` groups whose parent
line is only an instruction (`١ اختر الإجابة الصحيحة:`) keep that instruction;
matching (`صِل`, `طابق`) and `experiment` types were added.

---

## AD-10 English: exercise-centred chunking with instruction-based classification

**Problem.** The English books are organised in numbered exercises
(`3 Read the sentences and complete …`) plus boxes (`Learning Outcomes`,
`Language in use`, `Tip!`, `Think`, `Now I can ...`), reading texts, dialogues,
a story unit and a glossary. The copied ICT logic looked for Arabic headings
that never occur in these books.

**Chosen.** A new `chunking.py` (shared by both English books) that:

* removes running headers (`Unit N`, `Lesson N`, lesson-title lines) and keeps
  sub-titles printed at the page top (`Pronunciation`, `Where Life Flows`) as
  `page_label`;
* detects an exercise header only if it carries the next expected exercise
  number **and** reads like an instruction (verb list collected from both books,
  or a question / later imperative). This separates exercises from numbered
  items such as `1 owner   a. to give …` or `2 Miss Mason`;
* keeps each exercise whole (instruction + items + options) — answer options
  are never separated from their question;
* classifies each exercise from its instruction (concrete task types first;
  `mixed_question` only when lettered sub-tasks `A. Choose … / B. Answer …`
  exist);
* separates reading texts embedded inside other exercises
  (e.g. "Animals in the Desert" after an MCQ) into `reading_passage` chunks;
* applies no Arabic cleaning; preserves line breaks and inline spacing.

Printing errors in the books are tolerated only for clear instructions and are
recorded in `exercise_number_note` (English P4 page 83 prints exercise "2"
twice).

---

## AD-11 Validation: errors / warnings / info, content coverage, exit code

**Existing.** One flat `issues` list; any short chunk was an issue; no page
validation; no check that page content reached a chunk.

**Chosen.** One identical `validation.py` for all books with:

* **errors** (must be fixed; script exits with code 1): schema mismatches,
  missing/duplicate IDs, IDs without the book prefix, empty text, invalid
  chunk/section/page types, missing unit/lesson references, chunks from
  excluded or unknown pages, metadata inconsistent with the page record,
  excluded pages without a reason;
* **warnings** (review): short/long chunks, duplicate text, OCR uncertainty
  markers, MCQ with fewer than 2 detectable options, very short activities,
  learning pages without chunks, printed page numbers not increasing,
  page sequence gaps, and **uncovered content** — every non-structural line of
  a learning page must appear in a chunk of that page (text or descriptive
  metadata);
* **info**: counts by type and section, lengths, page totals, printed-page
  offsets.

The original summary keys (`total_chunks`, `total_issues`, `valid_chunks`,
`chunk_type_counts`, `average_chunk_length`, thresholds, `duplicate_chunk_ids`)
were kept; each issue now has a `severity`.

A new root script `validate_corpus.py` checks what a single book cannot:
corpus-wide ID uniqueness, `book_id`/folder agreement, common schema keys and
stale per-book reports. It is the only new code file.

---

## AD-12 Chunk sizes and no overlap

* ICT: `max_chunk_chars = 1000` (unchanged).
* Science: explanations 1000; activities kept whole up to 1500 (largest actual
  activity: 1,021 characters), split only between numbered steps.
* English: 1500 (largest actual chunks: 1,353 characters in P4, 1,456 in P5)
  so that whole exercises and texts stay intact; splits only between
  items/paragraphs.
* Validation warns above 1500 characters (unchanged threshold).

**Overlap was not introduced.** Chunks are self-contained educational units
(a whole exercise, activity or explanation block) and carry their context in
metadata (unit, lesson, section, instruction, titles). Overlap would duplicate
questions and options across chunks and inflate retrieval results. This can be
revisited per chunk type at embedding time.

---

## AD-13 Per-page chunks

Chunks never span two PDF pages (as in the original design), so every chunk
has one exact `pdf_page_index` for citation. Content that continues on the
next page without a heading is linked with `continued_from_page` (English
exercises; Science activities). Trade-off: a story or text spread over several
pages is retrieved page by page (English Unit 6 story pages); this is listed
as a known limitation.

---

## AD-14 UTF-8 console output and OCR uncertainty markers

* Every script calls `sys.stdout.reconfigure(encoding="utf-8")`. On the
  development machine the console code page (cp1256) cannot print
  Arabic-Indic digits, which made the existing scripts crash while printing.
* The 7 `[قراءة محتملة: …]` markers (ICT P4: 5, ICT P5: 2) are still removed
  from `processed_content` as in the original design. A change that kept the
  marker's text was tried and **reverted**: the markers mean different things
  (a missing word, an alternative to the preceding OCR token, or a
  transcriber's note), so no single rule is correct. Each affected source line
  is now listed in the ICT page field `ocr_uncertain_readings` for manual
  review.
