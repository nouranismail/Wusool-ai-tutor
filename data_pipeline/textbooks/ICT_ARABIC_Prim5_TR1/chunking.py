from pathlib import Path
import re
import sys
import json

BASE_DIR = Path(__file__).resolve().parent

# Force UTF-8 console output (Arabic text and Arabic-Indic digits).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


#----------- Read Pages JSON -------------

input_file = Path(
    BASE_DIR / "output" / "pages.json"
)

pages = json.loads(
    input_file.read_text(encoding="utf-8")
)

# pages.json keeps every PDF page for traceability.
# Only learning pages (include_in_rag = true) are chunked.
pages = [
    page for page in pages
    if page.get("include_in_rag", True)
]


#----------- Chunking Settings -------------

max_chunk_chars = 1000


#----------- Text Patterns -------------

objective_headings = [
    "نواتج التعلم",
    "أهداف الدرس"
]

mcq_headings = [
    "اختر الإجابة الصحيحة من بين الاختيارات التالية",
    "أولًا اختر الإجابة الصحيحة من بين الاختيارات التالية",
    "ثانيًا اختر الإجابة الصحيحة من بين الاختيارات التالية",
    "أولا اختر الإجابة الصحيحة من بين الاختيارات التالية",
    "ثانيا اختر الإجابة الصحيحة من بين الاختيارات التالية"
]

true_false_headings = [
    "ضع علامة",
    "أولًا ضع علامة",
    "أولا ضع علامة",
    "ثانيًا ضع علامة",
    "ثانيا ضع علامة"
]

activity_headings = [
    "التطبيق العملي:",
    "تطبيق العملي:",
    "التطبيق العملي",
    "تطبيق عملي:"
]

section_headings = (
    objective_headings
    + mcq_headings
    + true_false_headings
    + activity_headings
    + [
        "الأسئلة والتدريبات",
        "الأسئلة والتدريبات:"
    ]
)

# Headings that open the questions part of a page. Numbered lines and
# answer options are question content only AFTER one of these headings.
question_headings = mcq_headings + true_false_headings + [
    "الأسئلة والتدريبات",
    "الأسئلة والتدريبات:"
]

# True/False answer box: "( )", "(  )", "(√)", "(×)" with optional spaces
# (including the non-breaking space used in some source lines).
true_false_marker = re.compile(r"\(\s*[√×✓✗]?\s*\)")

# Arabic and English question options.
option_pattern = re.compile(r"^\s*[أبجدA-D][.)]\s*")

# Arabic-Indic and Western numerals at the beginning of a line.
number_pattern = re.compile(r"^\s*([٠-٩0-9]+)[\s.)-]")


#----------- Text Helpers -------------

def normalize_lines(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    ignored_lines = {
        "الوحدة الأولى",
        "الوحدة الثانية"
    }

    return [
        line for line in lines
        if line not in ignored_lines
    ]


def make_chunk(page, text, chunk_type, chunk_number, extra_metadata=None):

    # Chunk ID = book prefix + original U/L/P/C convention.
    # The book prefix keeps IDs unique across the six-book corpus.
    chunk = {
        "chunk_id": (
            f"{page['book_id']}_"
            f"U{page['unit_id']}_"
            f"L{page['lesson_id']}_"
            f"P{page['pdf_page_index']}_"
            f"C{chunk_number:03d}"
        ),
        "text": text.strip(),
        "metadata": {
            "book_id": page["book_id"],
            "subject": page["subject"],
            "grade": page["grade"],
            "term": page["term"],
            "language": page["language"],
            "unit_id": page["unit_id"],
            "unit_title": page["unit_title"],
            "lesson_id": page["lesson_id"],
            "lesson_title": page["lesson_title"],
            "section_type": page.get("section_type"),
            "section_title": page.get("section_title"),
            "pdf_page_index": page["pdf_page_index"],
            "printed_page_number": page.get("printed_page_number"),
            "chunk_type": chunk_type
        }
    }

    if extra_metadata:
        chunk["metadata"].update(extra_metadata)

    return chunk


def matches_heading(line, headings):

    return any(line.startswith(heading) for heading in headings)


def find_section(lines, headings):

    for index, line in enumerate(lines):

        if matches_heading(line, headings):
            return index

    return None


def get_section_lines(lines, start_index, stop_headings):

    section_lines = []

    for line in lines[start_index + 1:]:

        if matches_heading(line, stop_headings):
            break

        section_lines.append(line)

    return section_lines


def is_sub_heading(line):

    return (
        len(line) <= 80
        and (
            line.rstrip().endswith((":", "："))
            or re.match(r"^\s*[٠-٩0-9]+\s+\S", line)
        )
    )


def split_long_lines(lines, max_chars=max_chunk_chars):

    # Split an explanation that is longer than max_chars.
    # Prefer to cut just before a sub-heading so a heading stays with
    # its content. Fall back to a plain line boundary otherwise.
    parts = []
    current = []

    for line in lines:

        too_long = len("\n".join(current + [line])) > max_chars

        if current and too_long:

            cut = None

            for index in range(len(current) - 1, 0, -1):
                if is_sub_heading(current[index]):
                    cut = index
                    break

            if cut is not None and len("\n".join(current[:cut])) >= max_chars // 3:
                parts.append(current[:cut])
                current = current[cut:]
            else:
                parts.append(current)
                current = []

        current.append(line)

    if current:
        parts.append(current)

    return parts


#----------- Extract Learning Objectives -------------

def extract_objectives(lines, page, chunks):

    start = find_section(lines, objective_headings)

    if start is None:
        return

    objective_lines = []

    for line in lines[start + 1:]:

        if matches_heading(line, section_headings):
            break

        if number_pattern.match(line):
            objective_lines.append(line)

        # The objectives list ends at the first ordinary text line.
        # Numbered lines further down the page are explanation content.
        elif not line.startswith("من المتوقع"):
            break

    if objective_lines:

        chunks.append(
            make_chunk(
                page,
                "\n".join(objective_lines),
                "learning_objective",
                len(chunks) + 1
            )
        )


#----------- Extract MCQ Questions -------------

def extract_mcq_chunks(lines, page, chunks):

    start = find_section(lines, mcq_headings)

    if start is None:
        return

    question_lines = []
    question_number = None

    # The section instruction is stored with every question so it is not lost.
    instruction = lines[start]

    section_lines = get_section_lines(
        lines,
        start,
        section_headings
    )

    def save_question():

        nonlocal question_lines, question_number

        if question_lines:

            chunks.append(
                make_chunk(
                    page,
                    "\n".join(question_lines),
                    "mcq",
                    len(chunks) + 1,
                    {
                        "question_number": question_number,
                        "question_instruction": instruction
                    }
                )
            )

        question_lines = []
        question_number = None

    for line in section_lines:

        number_match = number_pattern.match(line)

        if number_match and not option_pattern.match(line):

            save_question()
            question_number = number_match.group(1)
            question_lines = [line]

        elif option_pattern.match(line):

            if question_lines:
                question_lines.append(line)

        elif question_lines:
            question_lines.append(line)

    save_question()


#----------- Extract True False Questions -------------

def extract_true_false_chunks(lines, page, chunks):

    start = find_section(lines, true_false_headings)

    if start is None:
        return

    instruction = lines[start]

    section_lines = get_section_lines(
        lines,
        start,
        section_headings
    )

    question_number = 0

    for line in section_lines:

        if true_false_marker.search(line):

            question_number += 1

            chunks.append(
                make_chunk(
                    page,
                    line,
                    "true_false",
                    len(chunks) + 1,
                    {
                        "question_number": question_number,
                        "question_instruction": instruction
                    }
                )
            )


#----------- Extract Practical Activities -------------

def extract_activities(lines, page, chunks):

    start = find_section(lines, activity_headings)

    if start is None:
        return

    # The activity runs until the next section heading (or the page end),
    # so questions placed after an activity are never swallowed by it.
    activity_lines = [lines[start]] + get_section_lines(
        lines,
        start,
        question_headings + objective_headings
    )

    if activity_lines:

        chunks.append(
            make_chunk(
                page,
                "\n".join(activity_lines),
                "practical_activity",
                len(chunks) + 1
            )
        )


#----------- Extract Explanation Chunks -------------

def extract_explanation_chunks(lines, page, chunks):

    current_chunk = []

    def save_chunk():

        if current_chunk:

            # Long explanations are split at sub-headings where possible.
            for part in split_long_lines(current_chunk):

                chunks.append(
                    make_chunk(
                        page,
                        "\n".join(part),
                        "explanation",
                        len(chunks) + 1
                    )
                )

            current_chunk.clear()

    skip_objectives = False
    skip_activity = False

    # in_questions is True after a questions heading. Only there are
    # numbered lines and answer options treated as question content.
    # (Previously every numbered line was dropped, which deleted numbered
    # explanation items such as the steps for creating a new folder.)
    in_questions = False

    for line in lines:

        #----------- Skip Non-Content Lines -------------

        # Skip the printed page number at the bottom of the page.
        # The original page text remains محفوظًا في pages.json.
        printed_page = page.get("printed_page_number")

        if printed_page is not None and line.strip() == str(printed_page).strip():
            continue

        # Skip OCR placeholder lines that do not contain the image description.
        if line.strip() == "[نص داخل الصورة:]":
            continue

        # Skip a repeated lesson title if it appears as a standalone line.
        lesson_title = (page.get("lesson_title") or "").strip()

        # Fixed: the original pattern r"[\\s...]" matched a literal
        # backslash and "s" instead of whitespace.
        normalized_line = re.sub(r"[\s.،:：]+$", "", line.strip())
        normalized_title = re.sub(r"[\s.،:：]+$", "", lesson_title)

        if normalized_title and normalized_line == normalized_title:
            continue

        if matches_heading(line, objective_headings):
            save_chunk()
            skip_objectives = True
            continue

        if matches_heading(line, activity_headings):
            save_chunk()
            skip_activity = True
            continue

        if matches_heading(line, section_headings):
            save_chunk()
            skip_objectives = False
            # A new section heading ends the activity block.
            skip_activity = False
            in_questions = matches_heading(line, question_headings)
            continue

        if skip_activity or in_questions:
            continue

        if skip_objectives:

            if (
                not number_pattern.match(line)
                and not line.startswith("من المتوقع")
            ):
                skip_objectives = False
            else:
                continue

        current_chunk.append(line)

    save_chunk()


#----------- Classify and Create Chunks -------------

chunks = []

for page in pages:

    page_text = page.get("processed_content", "")

    if not page_text.strip():
        continue

    # A page without a lesson mapping should not receive a misleading chunk ID.
    if page.get("unit_id") is None or page.get("lesson_id") is None:
        print(
            "WARNING: Skipping unmapped page:",
            page.get("pdf_page_index")
        )
        continue

    lines = normalize_lines(page_text)

    # Drop the printed page number footer (kept in raw_content and in the
    # printed_page_number field). It previously leaked into activity chunks.
    printed_page = page.get("printed_page_number")

    if printed_page is not None and lines and lines[-1] == str(printed_page):
        lines = lines[:-1]

    page_chunks = []

    extract_objectives(lines, page, page_chunks)
    extract_mcq_chunks(lines, page, page_chunks)
    extract_true_false_chunks(lines, page, page_chunks)
    extract_activities(lines, page, page_chunks)
    extract_explanation_chunks(lines, page, page_chunks)

    chunks.extend(page_chunks)


#----------- Save Chunks JSON -------------

output_dir = Path(
    BASE_DIR / "output"
)

output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "chunks.json"

output_file.write_text(
    json.dumps(chunks, ensure_ascii=False, indent=4),
    encoding="utf-8"
)


#----------- Chunk Summary -------------

chunk_types = {}

for chunk in chunks:

    chunk_type = chunk["metadata"]["chunk_type"]
    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1


print("Total pages:", len(pages))
print("Total chunks:", len(chunks))
print("\nChunks by type:")

for chunk_type, count in chunk_types.items():
    print(f"{chunk_type}: {count}")

print("\nOutput saved successfully!")
print("Output file:", output_file)


#----------- Inspect First Chunks -------------

for chunk in chunks[:5]:

    print("\n" + "=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Type:", chunk["metadata"]["chunk_type"])
    print("Page:", chunk["metadata"]["pdf_page_index"])
    print("Text:")
    print(chunk["text"])
