import re
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).resolve().parent

# Force UTF-8 console output (Arabic text and Arabic-Indic digits).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


#----------- File Paths -------------

input_file = Path(
    BASE_DIR / "output" / "chunks.json"
)

pages_file = Path(
    BASE_DIR / "output" / "pages.json"
)

output_dir = Path(
    BASE_DIR / "output"
)

#----------- Validation Settings -------------

expected_book_id = BASE_DIR.name

# Union of the chunk types used across the six books. A book does not
# have to use every type, but it may not use a type outside this list.
valid_chunk_types = {
    # Shared
    "explanation",
    "learning_objective",
    "example",
    "practical_activity",
    "table",
    "diagram",
    # Questions
    "mcq",
    "true_false",
    "fill_in_the_blank",
    "matching",
    "open_ended",
    "mixed_question",
    # Science
    "experiment",
    # English
    "vocabulary",
    "grammar_explanation",
    "reading_passage",
    "dialogue",
    "self_assessment"
}

question_chunk_types = {
    "mcq",
    "true_false",
    "fill_in_the_blank",
    "matching",
    "open_ended",
    "mixed_question"
}

# Where a page sits in the textbook structure.
valid_section_types = {
    "lesson",           # a numbered lesson page
    "unit_opener",      # English unit opener (unit title + learning outcomes)
    "quick_review",     # English end-of-unit quick review
    "self_assessment",  # English end-of-unit self-assessment
    "review",           # English cross-unit review (Review 1 / Review 2)
    "story",            # English Unit 6 story pages (no numbered lessons)
    "glossary",         # English glossary
    "enrichment",       # Science chapter-level enrichment pages
    "chapter_review",   # Science chapter-level review pages
    "appendix"          # Science scientific-inquiry appendix
}

# Sections that must belong to a unit/chapter.
unit_level_sections = {
    "lesson",
    "unit_opener",
    "quick_review",
    "self_assessment",
    "story",
    "enrichment",
    "chapter_review"
}

valid_page_types = {
    "content",
    "front_matter",
    "back_matter",
    "unit_divider",
    "lesson_divider",
    "blank",
    "notes"
}

min_chunk_chars = 20
max_chunk_chars = 1500

required_metadata = [
    "book_id",
    "subject",
    "grade",
    "term",
    "language",
    "pdf_page_index",
    "chunk_type",
    "section_type"
]

# Keys that must exist (their value may be null where the structure allows).
expected_metadata_keys = required_metadata + [
    "unit_id",
    "unit_title",
    "lesson_id",
    "lesson_title",
    "section_title",
    "printed_page_number"
]

required_page_fields = [
    "book_id",
    "subject",
    "grade",
    "term",
    "language",
    "unit_type",
    "pdf_page_index",
    "printed_page_number",
    "raw_content",
    "processed_content",
    "unit_id",
    "unit_title",
    "lesson_id",
    "lesson_title",
    "section_type",
    "section_title",
    "page_type",
    "include_in_rag",
    "exclusion_reason"
]

uncertainty_markers = [
    "[غير واضح]",
    "[قراءة محتملة:"
]

# Structural lines (running headers, section labels, page numbers) that
# are intentionally not repeated inside chunk text. Everything else on a
# learning page must appear in some chunk, or a warning is raised.
structural_line_patterns = [
    r"^(Unit|Lesson|Review)\s+\d+$",
    r"^(Story|Glossary|Quick Review|Self\s*-\s*Assessment|Story Time|Writing|Think and Create)$",
    r"^الوحدة\s+(الأولى|الأولي|الثانية)$",
    r"^الدرس\s+\S+(\s*[:：].*)?$",
    r"^(أهداف الدرس|نواتج التعلم|الأسئلة\s*و\s*(ال)?تدريبات:?)$",
    r"^من المتوقع بعد نهاية الدرس",
    r"^[١-٩0-9]\s*-\s*[١-٩0-9]+\s",
    r"^الفصل\s*[١-٩0-9]",
    r"^الفصل\s+(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع)\s*:",
    r"^ركن إثرائي\s+الفصل",
    r"^\[رقم الصفحة:\s*[٠-٩0-9]+\s*\]$",
    r"^\[[٠-٩0-9]+\]$",
    r"^[٠-٩0-9]+$",
    r"^(حاول|تدرَّب|تدرب)$",
    r"^\[نص داخل الصورة:\]$",
    r"^\|[\s|:-]+\|$"
]

arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

#----------- Helper Functions -------------

def to_int(value):

    # Printed page numbers may use Arabic-Indic digits.
    if value is None:
        return None

    digits = str(value).translate(arabic_digits).strip()

    return int(digits) if digits.isdigit() else None


def normalize_for_coverage(text):

    # Ignore whitespace, tatweel, Arabic diacritics and table pipes.
    return re.sub(r"[\sـً-ٟ|]+", "", text)


def is_structural_line(line):

    return any(
        re.search(pattern, line)
        for pattern in structural_line_patterns
    )


def count_options(text):

    # Arabic options: "أ." "أ:" "أ)" / Latin options: "a." "A)" (inline or per line)
    arabic = re.findall(r"(?:^|\s)[أبجده]\s*[.:)]", text, flags=re.MULTILINE)
    english = re.findall(r"(?:^|\s)[a-dA-D][.)]\s", text, flags=re.MULTILINE)

    # English choice formats: "drinks/runs" alternatives, "feed - pot"
    # word pairs, and check boxes "[ ]" / "(   )".
    alternatives = re.findall(r"[A-Za-z]+/[A-Za-z]+", text)
    word_pairs = re.findall(r"^\d+\.?\s+[A-Za-z]+(?:\s+-\s+[A-Za-z]+)+$", text, flags=re.MULTILINE)
    # Word bank lines: "read   cup   thumb   book" (words separated by 2+ spaces)
    word_banks = re.findall(r"^[A-Za-z]+(?:\s{2,}[A-Za-z]+){2,}$", text, flags=re.MULTILINE)
    boxes = re.findall(r"\[\s*\]|\(\s+\)", text)

    return max(len(arabic), len(english), 2 * len(alternatives), 2 * len(word_pairs),
               2 * len(word_banks), len(boxes))


#----------- Load JSON Files -------------

if not input_file.exists():
    raise FileNotFoundError(
        f"Chunks file was not found: {input_file}"
    )

if not pages_file.exists():
    raise FileNotFoundError(
        f"Pages file was not found: {pages_file}"
    )

chunks = json.loads(
    input_file.read_text(encoding="utf-8")
)

pages = json.loads(
    pages_file.read_text(encoding="utf-8")
)

if not isinstance(chunks, list):
    raise ValueError("chunks.json must contain a JSON list.")

if not isinstance(pages, list):
    raise ValueError("pages.json must contain a JSON list.")

#----------- Initialize Validation Results -------------

issues = []
chunk_type_counts = Counter()
section_type_counts = Counter()
chunk_lengths = []

seen_ids = set()
duplicate_ids = []

seen_texts = {}


def add_issue(severity, issue, details, chunk_index=None, chunk_id=None, pdf_page_index=None):

    issues.append({
        "severity": severity,
        "issue": issue,
        "chunk_index": chunk_index,
        "chunk_id": chunk_id,
        "pdf_page_index": pdf_page_index,
        "details": details
    })


#----------- Validate Pages -------------

page_by_index = {}

for position, page in enumerate(pages, start=1):

    if not isinstance(page, dict):
        add_issue("error", "invalid_page_structure",
                  f"Page record #{position} must be a JSON object.")
        continue

    page_index = page.get("pdf_page_index")

    missing_fields = [
        field for field in required_page_fields
        if field not in page
    ]

    if missing_fields:
        add_issue("error", "page_schema_mismatch",
                  "Missing page field(s): " + ", ".join(missing_fields),
                  pdf_page_index=page_index)

    if not isinstance(page_index, int) or isinstance(page_index, bool) or page_index < 1:
        add_issue("error", "invalid_page_number",
                  f"Invalid pdf_page_index: {page_index!r}")
        continue

    if page_index in page_by_index:
        add_issue("error", "duplicate_page",
                  f"pdf_page_index {page_index} appears more than once.",
                  pdf_page_index=page_index)

    page_by_index[page_index] = page

    if page.get("book_id") != expected_book_id:
        add_issue("error", "invalid_book_id",
                  f"Page book_id {page.get('book_id')!r} does not match folder {expected_book_id!r}.",
                  pdf_page_index=page_index)

    if page.get("page_type") not in valid_page_types:
        add_issue("error", "invalid_page_type",
                  f"Unknown page_type: {page.get('page_type')!r}",
                  pdf_page_index=page_index)

    if page.get("include_in_rag"):

        if page.get("page_type") != "content":
            add_issue("error", "inconsistent_page_flags",
                      "A page included in RAG must have page_type 'content'.",
                      pdf_page_index=page_index)

        section_type = page.get("section_type")

        if section_type not in valid_section_types:
            add_issue("error", "invalid_section_type",
                      f"Learning page has invalid section_type: {section_type!r}",
                      pdf_page_index=page_index)

        if section_type in unit_level_sections and page.get("unit_id") is None:
            add_issue("error", "missing_unit_reference",
                      f"Section '{section_type}' must belong to a unit/chapter.",
                      pdf_page_index=page_index)

        if section_type == "lesson" and (
            page.get("lesson_id") is None or not page.get("lesson_title")
        ):
            add_issue("error", "missing_lesson_reference",
                      "Lesson page without lesson_id / lesson_title.",
                      pdf_page_index=page_index)

        if not (page.get("processed_content") or "").strip():
            add_issue("warning", "empty_learning_page",
                      "Learning page has no processed content.",
                      pdf_page_index=page_index)

    elif not page.get("exclusion_reason"):
        add_issue("error", "missing_exclusion_reason",
                  "Excluded page must state an exclusion_reason.",
                  pdf_page_index=page_index)

#----------- Validate Page Numbering -------------

page_indices = sorted(page_by_index)

if page_indices and page_indices != list(range(1, page_indices[-1] + 1)):
    missing_pages = sorted(set(range(1, page_indices[-1] + 1)) - set(page_indices))
    add_issue("warning", "page_sequence_gap",
              f"pages.json does not contain every PDF page. Missing: {missing_pages}")

previous_printed = None
page_offsets = Counter()

for page_index in page_indices:

    page = page_by_index[page_index]
    printed = to_int(page.get("printed_page_number"))

    if printed is None:
        continue

    page_offsets[page_index - printed] += 1

    if previous_printed is not None and printed <= previous_printed:
        add_issue("warning", "printed_page_not_increasing",
                  f"Printed page {page.get('printed_page_number')} does not increase "
                  f"after printed page {previous_printed}.",
                  pdf_page_index=page_index)

    previous_printed = printed

#----------- Validate Each Chunk -------------

chunks_by_page = defaultdict(list)

for index, chunk in enumerate(chunks, start=1):

    if not isinstance(chunk, dict):
        add_issue("error", "invalid_chunk_structure",
                  "Chunk must be a JSON object.", chunk_index=index)
        continue

    chunk_id = chunk.get("chunk_id")
    text = chunk.get("text")
    metadata = chunk.get("metadata")

    #----------- Validate Chunk ID -------------

    if not chunk_id:
        add_issue("error", "missing_chunk_id",
                  "Chunk ID is missing or empty.", chunk_index=index)

    elif chunk_id in seen_ids:
        duplicate_ids.append(chunk_id)
        add_issue("error", "duplicate_chunk_id",
                  "This Chunk ID already exists.",
                  chunk_index=index, chunk_id=chunk_id)

    else:
        seen_ids.add(chunk_id)

        if not chunk_id.startswith(expected_book_id + "_"):
            add_issue("error", "chunk_id_without_book_prefix",
                      f"Chunk ID must start with '{expected_book_id}_' to stay unique across books.",
                      chunk_index=index, chunk_id=chunk_id)

    #----------- Validate Text -------------

    if not isinstance(text, str) or not text.strip():
        add_issue("error", "empty_text",
                  "Chunk text is missing, invalid, or empty.",
                  chunk_index=index, chunk_id=chunk_id)
        text = ""

    else:
        text_length = len(text.strip())
        chunk_lengths.append(text_length)

        if text_length < min_chunk_chars:
            add_issue("warning", "short_chunk",
                      f"Chunk contains only {text_length} characters.",
                      chunk_index=index, chunk_id=chunk_id)

        if text_length > max_chunk_chars:
            add_issue("warning", "long_chunk",
                      f"Chunk contains {text_length} characters.",
                      chunk_index=index, chunk_id=chunk_id)

        normalized_text = normalize_for_coverage(text)

        if normalized_text in seen_texts:
            add_issue("warning", "duplicate_text",
                      f"Same text as chunk {seen_texts[normalized_text]}.",
                      chunk_index=index, chunk_id=chunk_id)
        else:
            seen_texts[normalized_text] = chunk_id

    #----------- Validate Metadata -------------

    if not isinstance(metadata, dict):
        add_issue("error", "invalid_metadata",
                  "Metadata must be a JSON object.",
                  chunk_index=index, chunk_id=chunk_id)
        continue

    for field in expected_metadata_keys:
        if field not in metadata:
            add_issue("error", "schema_mismatch",
                      f"Missing metadata key: {field}",
                      chunk_index=index, chunk_id=chunk_id)

    for field in required_metadata:
        if metadata.get(field) is None:
            add_issue("error", "missing_metadata",
                      f"Missing metadata field: {field}",
                      chunk_index=index, chunk_id=chunk_id)

    if metadata.get("book_id") != expected_book_id:
        add_issue("error", "invalid_book_id",
                  f"Chunk book_id {metadata.get('book_id')!r} does not match folder {expected_book_id!r}.",
                  chunk_index=index, chunk_id=chunk_id)

    chunk_type = metadata.get("chunk_type")

    if chunk_type:
        chunk_type_counts[chunk_type] += 1

        if chunk_type not in valid_chunk_types:
            add_issue("error", "invalid_chunk_type",
                      f"Unknown chunk type: {chunk_type}",
                      chunk_index=index, chunk_id=chunk_id)

    section_type = metadata.get("section_type")
    section_type_counts[section_type] += 1

    if section_type is not None and section_type not in valid_section_types:
        add_issue("error", "invalid_section_type",
                  f"Unknown section type: {section_type}",
                  chunk_index=index, chunk_id=chunk_id)

    if section_type in unit_level_sections and metadata.get("unit_id") is None:
        add_issue("error", "missing_unit_reference",
                  f"Section '{section_type}' requires unit_id.",
                  chunk_index=index, chunk_id=chunk_id)

    if section_type == "lesson" and (
        metadata.get("lesson_id") is None or not metadata.get("lesson_title")
    ):
        add_issue("error", "missing_lesson_reference",
                  "Lesson chunk without lesson_id / lesson_title.",
                  chunk_index=index, chunk_id=chunk_id)

    page_index = metadata.get("pdf_page_index")

    if not isinstance(page_index, int) or isinstance(page_index, bool) or page_index < 0:
        add_issue("error", "invalid_page_reference",
                  f"Invalid pdf_page_index: {page_index}",
                  chunk_index=index, chunk_id=chunk_id)
        continue

    #----------- Validate Chunk Against Its Page -------------

    page = page_by_index.get(page_index)

    if page is None:
        add_issue("error", "missing_page_reference",
                  f"pdf_page_index {page_index} does not exist in pages.json.",
                  chunk_index=index, chunk_id=chunk_id)
        continue

    if not page.get("include_in_rag"):
        add_issue("error", "chunk_from_excluded_page",
                  f"Chunk comes from excluded page {page_index} ({page.get('exclusion_reason')}).",
                  chunk_index=index, chunk_id=chunk_id)

    for field in [
        "subject", "grade", "term", "language", "unit_id", "unit_title",
        "lesson_id", "lesson_title", "section_type", "section_title",
        "printed_page_number"
    ]:
        if metadata.get(field) != page.get(field):
            add_issue("error", "inconsistent_metadata",
                      f"Metadata '{field}' ({metadata.get(field)!r}) differs from its page ({page.get(field)!r}).",
                      chunk_index=index, chunk_id=chunk_id)

    chunks_by_page[page_index].append(chunk)

    #----------- Validate Question and Activity Content -------------

    if chunk_type == "mcq" and count_options(text) < 2:
        add_issue("warning", "mcq_without_options",
                  "Multiple-choice chunk has fewer than two answer options.",
                  chunk_index=index, chunk_id=chunk_id)

    if chunk_type in {"practical_activity", "experiment"} and len(text.strip()) < 40:
        add_issue("warning", "incomplete_activity",
                  "Activity chunk is very short; check that its steps were kept.",
                  chunk_index=index, chunk_id=chunk_id)

    #----------- Check OCR Uncertainty -------------

    found_markers = [
        marker for marker in uncertainty_markers
        if marker in text
    ]

    if found_markers:
        add_issue("warning", "ocr_uncertainty",
                  "Found uncertainty marker(s): " + ", ".join(found_markers),
                  chunk_index=index, chunk_id=chunk_id)

#----------- Check Content Coverage -------------

# Every non-structural line of a learning page must be found in a chunk
# of that page (text or descriptive metadata). Missing lines are reported
# as warnings so content is reviewed instead of being silently dropped.
coverage_metadata_keys = [
    "unit_title", "lesson_title", "section_title", "question_instruction",
    "exercise_instruction", "question_section", "activity_title"
]

uncovered_lines = 0

for page_index in page_indices:

    page = page_by_index[page_index]

    if not page.get("include_in_rag"):
        continue

    page_chunks = chunks_by_page.get(page_index, [])

    if not page_chunks:
        add_issue("warning", "content_page_without_chunks",
                  "Learning page produced no chunks.",
                  pdf_page_index=page_index)
        continue

    covered_text = normalize_for_coverage("\n".join(
        chunk.get("text", "") + "\n" + "\n".join(
            str(chunk["metadata"].get(key) or "")
            for key in coverage_metadata_keys
        )
        for chunk in page_chunks
    ))

    for line in (page.get("processed_content") or "").splitlines():

        line = line.strip()

        if len(line) < 4 or is_structural_line(line):
            continue

        if normalize_for_coverage(line) not in covered_text:
            uncovered_lines += 1
            add_issue("warning", "uncovered_content",
                      f"Line not found in any chunk: {line[:120]}",
                      pdf_page_index=page_index)

#----------- Build Validation Summary -------------

total_chunks = len(chunks)
errors = [issue for issue in issues if issue["severity"] == "error"]
warnings = [issue for issue in issues if issue["severity"] == "warning"]

learning_pages = [
    page for page in pages
    if isinstance(page, dict) and page.get("include_in_rag")
]

summary = {
    "book_id": expected_book_id,
    "status": "failed" if errors else ("passed_with_warnings" if warnings else "passed"),
    "total_chunks": total_chunks,
    "total_issues": len(issues),
    "total_errors": len(errors),
    "total_warnings": len(warnings),
    "valid_chunks": total_chunks - len({
        issue["chunk_index"]
        for issue in errors
        if issue["chunk_index"] is not None
    }),
    "issue_counts": dict(Counter(
        f"{issue['severity']}:{issue['issue']}" for issue in issues
    )),
    "chunk_type_counts": dict(chunk_type_counts),
    "section_type_counts": {
        str(key): value for key, value in section_type_counts.items()
    },
    "average_chunk_length": (
        round(sum(chunk_lengths) / len(chunk_lengths), 2)
        if chunk_lengths else 0
    ),
    "min_chunk_length": min(chunk_lengths) if chunk_lengths else 0,
    "max_chunk_length": max(chunk_lengths) if chunk_lengths else 0,
    "short_chunks_threshold": min_chunk_chars,
    "long_chunks_threshold": max_chunk_chars,
    "duplicate_chunk_ids": sorted(set(duplicate_ids)),
    "total_pages": len(pages),
    "learning_pages": len(learning_pages),
    "excluded_pages": len(pages) - len(learning_pages),
    "learning_pages_without_chunks": sorted(
        page["pdf_page_index"] for page in learning_pages
        if page["pdf_page_index"] not in chunks_by_page
    ),
    "uncovered_content_lines": uncovered_lines,
    "printed_page_offsets": {
        str(offset): count for offset, count in sorted(page_offsets.items())
    }
}

#----------- Save Validation Report -------------

output_dir.mkdir(parents=True, exist_ok=True)

report = {
    "summary": summary,
    "issues": issues
}

report_file = output_dir / "validation_report.json"

report_file.write_text(
    json.dumps(report, ensure_ascii=False, indent=4),
    encoding="utf-8"
)

#----------- Print Validation Results -------------

print("----------- Validation Summary -------------")
print(f"Book: {summary['book_id']}")
print(f"Status: {summary['status']}")
print(f"Pages: {summary['total_pages']} total, {summary['learning_pages']} learning, {summary['excluded_pages']} excluded")
print(f"Total chunks: {summary['total_chunks']}")
print(f"Valid chunks: {summary['valid_chunks']}")
print(f"Errors: {summary['total_errors']}")
print(f"Warnings: {summary['total_warnings']}")
print(f"Average chunk length: {summary['average_chunk_length']}")

print("\n----------- Chunk Types -------------")

for chunk_type, count in sorted(chunk_type_counts.items()):
    print(f"{chunk_type}: {count}")

print("\n----------- Issue Counts -------------")

if issues:
    for name, count in sorted(summary["issue_counts"].items()):
        print(f"{name}: {count}")
else:
    print("No validation issues found.")

print("\n----------- Errors -------------")

if errors:
    for issue in errors:
        print(
            f"{issue['chunk_id'] or issue['chunk_index'] or 'page ' + str(issue['pdf_page_index'])} | "
            f"{issue['issue']} | {issue['details']}"
        )
else:
    print("No errors.")

print(f"\nReport saved to: {report_file}")

# A non-zero exit code lets scripts and CI detect a failed validation.
if errors:
    sys.exit(1)
