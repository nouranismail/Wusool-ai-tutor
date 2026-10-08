# Dataset: Grade 3 curriculum for Wusool

The tutor teaches only from this dataset. Nothing else is allowed as a source of lesson content.

**File:** `data/reviewed/curriculum.json` (a JSON list of lessons)

## What is in it

| | Lessons | Questions | Source |
|---|---|---|---|
| Math | 6 | 37 | Egyptian Ministry of Education, Grade 3 Math, term 1, Chapter 1 (`IMG_9540.pdf`) |
| ICT | 5 | 5 | ICT Literacy Basics (`ICT_Literacy_Basics.pdf`) |

| Lesson id | Subject | Title (EN) | Title (AR) | Questions | PDF pages |
|---|---|---|---|---|---|
| `math-properties-1` | math | Multiplication properties - part one | خواص الضرب - الجزء الأول | 8 | 2, 3 |
| `math-properties-2` | math | Multiplication properties - part two | خواص الضرب - الجزء الثاني | 5 | 4, 5 |
| `math-times-ten-zero` | math | Multiplying by ten and zero | الضرب في عشرة وفي صفر | 6 | 6, 7 |
| `math-times-ten-zero-2` | math | Multiplying by ten and zero - part two | الضرب في عشرة وفي صفر - الجزء الثاني | 5 | 9, 10 |
| `math-missing-number` | math | Finding the missing number | إيجاد العدد المجهول | 7 | 8, 11 |
| `math-chapter-review` | math | Chapter one review and practice | مراجعة وتدريب - الفصل الأول | 6 | 12, 13 |
| `ict-computer` | ict | What is a computer? | ما هو الكمبيوتر؟ | 1 | 2 |
| `ict-input-output` | ict | Inputs and outputs | المدخلات والمخرجات | 1 | 2 |
| `ict-algorithm` | ict | Ordered steps and algorithms | الخطوات المرتبة والخوارزمية | 1 | 2, 3 |
| `ict-if-then` | ict | The if-then rule | قاعدة لو... إذن | 1 | 2, 3 |
| `ict-instructions` | ict | Computers need instructions | الكمبيوتر ذكي لكنه يحتاج تعليمات | 1 | 2, 3 |

## Status: needs teacher review

Every lesson is `needs_owner_review`. The math content was transcribed from page images (not OCR-verified by a teacher), so numbers and answers can contain mistakes. A teacher must check each lesson against the book before it is marked `approved`. Do not present this content to children as verified.

## Fields of one lesson

| Field | Meaning |
|---|---|
| `id`, `subject` (`math` or `ict`), `grade` | Identity. Ids and question ids must be unique. |
| `title_ar`, `title_en`, `keywords` | Used by the retriever. Arabic text is what gets embedded. |
| `explanation_ar`, `explanation_en` | Short explanation in our own words (not copied from the book). |
| `lesson_steps_ar` | The explanation split into spoken steps. |
| `questions[]` | `id`, `question_ar`, `question_en`, `accepted_answers`, `hint_ar`, `hint_en` |
| `source` | `file` and `pages` (page-level citations). |
| `review_status` | `needs_owner_review` or `approved`. |

`accepted_answers` lists digits, Arabic number words and common spoken spellings (for example `40`, `أربعون`, `أربعين`), plus the unit for word problems. Answer checking is an exact match after Arabic digits are converted, so add every variant a child might say.

## Page numbers

`source.pages` are **PDF page numbers**, not printed book page numbers. Printed page = PDF page + 6 (PDF page 2 is book page 8). In the math PDF, pages 8 to 11 are out of order: they are book pages 16, 15, 14, 17.

## Rules

- Do **not** commit the textbook PDFs. Keep them in `data/raw/` (git-ignored).
- Never use unreviewed OCR output to teach a child. One wrong symbol can reverse a maths problem.
- No personal data about children in this file.

## Add or change a lesson

1. Edit `data/reviewed/curriculum.json` with a new unique lesson id and question ids.
2. Run:
   ```
   python scripts/validate_curriculum.py
   python scripts/build_index.py
   python -m pytest -q
   ```
3. Open a PR. The vector index in `data/vector_db/` is rebuilt automatically when the file changes (it is git-ignored).

## Known limitations

- The retriever uses hashing embeddings over Arabic text. It handles word forms poorly (a query with "فكك" does not find a lesson about "تفكيك"). English questions do not match at all unless translated to Arabic first.
- Retrieval always returns a best match, even for unrelated questions (an off-topic question scored about 0.20, real matches about 0.36 and above). A score threshold is needed before the AI answers.
- Only Chapter 1 of the math book is included.
