from pathlib import Path
import re
import sys
import json
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent

# Force UTF-8 console output (the book contains some Arabic front matter).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


#----------- Book Information -------------

# book_id is the textbook folder name. It prefixes every chunk ID so
# chunks stay unique when the six books are merged into one corpus.
BOOK_INFO = {
    "book_id": "English_Prim5_TR1",
    "subject": "English",
    "grade": 5,
    "term": 1,
    "language": "en",
    "unit_type": "unit"
}


#----------- Read OCR File -------------

input_file = BASE_DIR / "English_P5_T1" / "English_language_prim5_t1_corrected.txt"

if not input_file.exists():
    raise FileNotFoundError(f"English transcription file was not found: {input_file}")

raw_text = input_file.read_text(encoding="utf-8")


#----------- Extract Pages -------------

page_pattern = r"(?m)^Page\s+(\d+)\s*$"

matches = list(re.finditer(page_pattern, raw_text))

if not matches:
    raise ValueError("No page markers were found. Expected markers like: Page 1")

pages = []

for i, match in enumerate(matches):

    page_number = int(match.group(1))

    start = match.end()

    if i + 1 < len(matches):
        end = matches[i + 1].start()
    else:
        end = len(raw_text)

    page_content = raw_text[start:end].strip()

    # The printed page number is the last standalone number on the page.
    content_lines = [
        line.strip()
        for line in page_content.splitlines()
        if line.strip()
    ]

    printed_page = None

    if content_lines and re.fullmatch(r"\d{1,3}", content_lines[-1]):
        printed_page = content_lines[-1]

    pages.append({
        **BOOK_INFO,
        "pdf_page_index": page_number,
        "printed_page_number": printed_page,
        "raw_content": page_content,
        "processed_content": None,
    })


#----------- Text Cleaning -------------

def clean_text(text, printed_page=None):

    lines = text.splitlines()

    # Remove the printed page number footer only (kept in printed_page_number).
    while lines and not lines[-1].strip():
        lines.pop()

    if printed_page is not None and lines and lines[-1].strip() == printed_page:
        lines.pop()

    # Remove trailing spaces. Inner spacing is kept because it separates
    # inline answer options ("a. room   b. garden") and matching columns.
    text = "\n".join(line.rstrip() for line in lines)

    # Reduce multiple empty lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


#----------- Apply Cleaning -------------

for page in pages:

    page["processed_content"] = clean_text(
        page["raw_content"],
        page["printed_page_number"]
    )


#----------- Textbook Structure -------------

# Unit titles are taken from the unit opener pages (verified against the
# rendered PDF pages; titles printed on two lines are joined with " - ").
units = {
    1: "Food, Nature, and Culture",
    2: "My Healthy Body",
    3: "When Nature Changes",
    4: "My Community",
    5: "Our World, Our Resources",
    6: "The Talking Earth"
}

# Lesson start pages and titles are taken from the "Lesson N" headings.
# A lesson label ("Story Time", "Writing", "Think and Create") is joined
# to the lesson title with ": ".
lessons = [

    #----------- Unit 1 -------------

    {"unit_id": 1, "lesson_id": 1, "lesson_title": "Life Along The Nile", "start_page": 8, "end_page": 10},
    {"unit_id": 1, "lesson_id": 2, "lesson_title": "Food in the Hot Desert", "start_page": 11, "end_page": 12},
    {"unit_id": 1, "lesson_id": 3, "lesson_title": "Story Time: The Giving Tree", "start_page": 13, "end_page": 16},
    {"unit_id": 1, "lesson_id": 4, "lesson_title": "Writing: Let's Make a Recipe!", "start_page": 17, "end_page": 19},
    {"unit_id": 1, "lesson_id": 5, "lesson_title": "Think and Create: A Flyer", "start_page": 20, "end_page": 22},

    #----------- Unit 2 -------------

    {"unit_id": 2, "lesson_id": 1, "lesson_title": "Sports for Better Health", "start_page": 26, "end_page": 27},
    {"unit_id": 2, "lesson_id": 2, "lesson_title": "My Habits: Then and Now", "start_page": 28, "end_page": 30},
    {"unit_id": 2, "lesson_id": 3, "lesson_title": "Heart and Blood", "start_page": 31, "end_page": 33},
    {"unit_id": 2, "lesson_id": 4, "lesson_title": "Writing: Life Savers in Action", "start_page": 34, "end_page": 37},
    {"unit_id": 2, "lesson_id": 5, "lesson_title": "Think and Create: A Poster", "start_page": 38, "end_page": 38},

    #----------- Unit 3 -------------

    {"unit_id": 3, "lesson_id": 1, "lesson_title": "Weather Wonders and Warnings!", "start_page": 42, "end_page": 44},
    {"unit_id": 3, "lesson_id": 2, "lesson_title": "Extreme Weather in Ancient Egypt", "start_page": 45, "end_page": 47},
    {"unit_id": 3, "lesson_id": 3, "lesson_title": "Story Time: The Two Frogs", "start_page": 48, "end_page": 51},
    {"unit_id": 3, "lesson_id": 4, "lesson_title": "Writing: Once Upon My Imagination", "start_page": 52, "end_page": 53},
    {"unit_id": 3, "lesson_id": 5, "lesson_title": "Think and Create: A Collage", "start_page": 54, "end_page": 54},

    #----------- Unit 4 -------------

    {"unit_id": 4, "lesson_id": 1, "lesson_title": "Places in Our Community", "start_page": 62, "end_page": 64},
    {"unit_id": 4, "lesson_id": 2, "lesson_title": "Egyptian Villages", "start_page": 65, "end_page": 67},
    {"unit_id": 4, "lesson_id": 3, "lesson_title": "Multiply It with Words!", "start_page": 68, "end_page": 69},
    {"unit_id": 4, "lesson_id": 4, "lesson_title": "Writing: The New Administrative Capital", "start_page": 70, "end_page": 73},
    {"unit_id": 4, "lesson_id": 5, "lesson_title": "Think and Create: Research", "start_page": 74, "end_page": 74},

    #----------- Unit 5 -------------

    {"unit_id": 5, "lesson_id": 1, "lesson_title": "The Gifts of Nature", "start_page": 78, "end_page": 80},
    {"unit_id": 5, "lesson_id": 2, "lesson_title": "Metals and Minerals in Our World", "start_page": 81, "end_page": 83},
    {"unit_id": 5, "lesson_id": 3, "lesson_title": "Story Time: \"Just Watch!\"—a Story by the Little Digger", "start_page": 84, "end_page": 86},
    {"unit_id": 5, "lesson_id": 4, "lesson_title": "Writing: Who Am I?", "start_page": 87, "end_page": 88},
    {"unit_id": 5, "lesson_id": 5, "lesson_title": "Think and Create: A Poster", "start_page": 89, "end_page": 89}
]

# Pages that belong to the book structure but not to a numbered lesson.
# Unit 6 is a story unit without numbered lessons; the reviews and the
# glossary are book-level sections (unit_id = None).
special_sections = [
    {"section_type": "unit_opener", "unit_id": 1, "section_title": "Unit 1 - Learning Outcomes", "start_page": 7, "end_page": 7},
    {"section_type": "quick_review", "unit_id": 1, "section_title": "Quick Review", "start_page": 23, "end_page": 23},
    {"section_type": "self_assessment", "unit_id": 1, "section_title": "Self-Assessment", "start_page": 24, "end_page": 24},

    {"section_type": "unit_opener", "unit_id": 2, "section_title": "Unit 2 - Learning Outcomes", "start_page": 25, "end_page": 25},
    {"section_type": "quick_review", "unit_id": 2, "section_title": "Quick Review", "start_page": 39, "end_page": 39},
    {"section_type": "self_assessment", "unit_id": 2, "section_title": "Self-Assessment", "start_page": 40, "end_page": 40},

    {"section_type": "unit_opener", "unit_id": 3, "section_title": "Unit 3 - Learning Outcomes", "start_page": 41, "end_page": 41},
    {"section_type": "quick_review", "unit_id": 3, "section_title": "Quick Review", "start_page": 55, "end_page": 55},
    {"section_type": "self_assessment", "unit_id": 3, "section_title": "Self-Assessment", "start_page": 56, "end_page": 56},

    {"section_type": "review", "unit_id": None, "section_title": "Review 1", "start_page": 57, "end_page": 59},
    {"section_type": "review", "unit_id": None, "section_title": "Review 1 - Self-Assessment", "start_page": 60, "end_page": 60},

    {"section_type": "unit_opener", "unit_id": 4, "section_title": "Unit 4 - Learning Outcomes", "start_page": 61, "end_page": 61},
    {"section_type": "quick_review", "unit_id": 4, "section_title": "Quick Review", "start_page": 75, "end_page": 75},
    {"section_type": "self_assessment", "unit_id": 4, "section_title": "Self-Assessment", "start_page": 76, "end_page": 76},

    {"section_type": "unit_opener", "unit_id": 5, "section_title": "Unit 5 - Learning Outcomes", "start_page": 77, "end_page": 77},
    {"section_type": "quick_review", "unit_id": 5, "section_title": "Quick Review", "start_page": 90, "end_page": 90},
    {"section_type": "self_assessment", "unit_id": 5, "section_title": "Self-Assessment", "start_page": 91, "end_page": 91},

    {"section_type": "unit_opener", "unit_id": 6, "section_title": "Unit 6 - Learning Outcomes", "start_page": 92, "end_page": 92},
    {"section_type": "story", "unit_id": 6, "section_title": "The Talking Earth (by Jean Craighead George)", "start_page": 93, "end_page": 104},
    # Unit 6 has a story quick review instead of a self-assessment page.
    {"section_type": "quick_review", "unit_id": 6, "section_title": "Quick Review", "start_page": 105, "end_page": 105},

    {"section_type": "review", "unit_id": None, "section_title": "Review 2", "start_page": 106, "end_page": 108},

    {"section_type": "glossary", "unit_id": None, "section_title": "Glossary of Words and Phrases", "start_page": 109, "end_page": 111}
]

# Non-learning pages are kept in pages.json for traceability.
excluded_page_info = {
    1: ("front_matter", "Book cover"),
    2: ("front_matter", "Dedication, copyright and student name page"),
    3: ("front_matter", "Term 1 scope and sequence table (curriculum overview)"),
    4: ("front_matter", "Term 1 scope and sequence table (curriculum overview)"),
    5: ("front_matter", "Term 1 scope and sequence table (curriculum overview)"),
    6: ("front_matter", "Message from the Ministry (not lesson content)"),
    112: ("back_matter", "Back cover with credits and printing data"),
    113: ("back_matter", "Back cover with general values messages")
}


#----------- Assign Unit and Lesson -------------

for page in pages:

    page_number = page["pdf_page_index"]

    page["unit_id"] = None
    page["unit_title"] = None
    page["lesson_id"] = None
    page["lesson_title"] = None
    page["section_type"] = None
    page["section_title"] = None

    for lesson in lessons:

        if lesson["start_page"] <= page_number <= lesson["end_page"]:

            page["unit_id"] = lesson["unit_id"]
            page["unit_title"] = units[lesson["unit_id"]]
            page["lesson_id"] = lesson["lesson_id"]
            page["lesson_title"] = lesson["lesson_title"]
            page["section_type"] = "lesson"
            page["section_title"] = lesson["lesson_title"]

            break

    for section in special_sections:

        if section["start_page"] <= page_number <= section["end_page"]:

            page["unit_id"] = section["unit_id"]
            page["unit_title"] = units.get(section["unit_id"])
            page["section_type"] = section["section_type"]
            page["section_title"] = section["section_title"]

            break

    if page_number in excluded_page_info:

        page["page_type"], page["exclusion_reason"] = excluded_page_info[page_number]
        page["include_in_rag"] = False

    elif page["section_type"] is not None:

        page["page_type"] = "content"
        page["include_in_rag"] = True
        page["exclusion_reason"] = None

    else:

        page["page_type"] = "content"
        page["include_in_rag"] = False
        page["exclusion_reason"] = "Page is not covered by the structure map"


#----------- Verify Structure Against Page Headings -------------

# The maps above are the source of truth. Every lesson page prints
# "Lesson N" and most pages print a "Unit N" side tab; warn on any
# disagreement so a wrong map entry is noticed immediately.
structure_warnings = []

# Lesson pages that continue a lesson without printing "Lesson N"
# (checked against the rendered PDF pages).
carry_forward_pages = set()

for page in pages:

    if not page["include_in_rag"] or page["pdf_page_index"] in carry_forward_pages:
        continue

    head_lines = page["raw_content"].splitlines()[:6]

    lesson_heading = next(
        (int(m.group(1)) for line in head_lines
         for m in [re.fullmatch(r"Lesson\s+(\d+)", line.strip())] if m),
        None
    )

    unit_heading = next(
        (int(m.group(1)) for line in head_lines
         for m in [re.fullmatch(r"Unit\s+(\d+)", line.strip())] if m),
        None
    )

    review_heading = next(
        (line.strip() for line in head_lines
         if re.fullmatch(r"Review\s+\d+", line.strip())),
        None
    )

    if page["section_type"] == "lesson" and lesson_heading != page["lesson_id"]:
        structure_warnings.append(
            f"PDF page {page['pdf_page_index']}: heading says lesson {lesson_heading}, "
            f"map says {page['lesson_id']}"
        )

    if page["section_type"] != "lesson" and lesson_heading is not None:
        structure_warnings.append(
            f"PDF page {page['pdf_page_index']}: 'Lesson {lesson_heading}' heading on a "
            f"{page['section_type']} page"
        )

    if unit_heading is not None and unit_heading != page["unit_id"]:
        structure_warnings.append(
            f"PDF page {page['pdf_page_index']}: heading says unit {unit_heading}, "
            f"map says {page['unit_id']}"
        )

    if review_heading and not (page["section_title"] or "").startswith(review_heading):
        structure_warnings.append(
            f"PDF page {page['pdf_page_index']}: heading says {review_heading}, "
            f"map says {page['section_title']}"
        )


#----------- Check Page Mapping -------------

print("----------- Page Mapping -------------")

for page in pages:

    print(
        f"PDF Page {page['pdf_page_index']}: "
        f"Unit {page['unit_id']}, "
        f"Lesson {page['lesson_id']} - "
        f"{page['section_type']} - "
        f"{page['section_title'] or page['exclusion_reason']}"
    )


#----------- Define Output Directory -------------

output_dir = BASE_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)


#----------- Save JSON -------------

output_file = output_dir / "pages.json"

output_file.write_text(
    json.dumps(pages, ensure_ascii=False, indent=4),
    encoding="utf-8"
)

learning_pages = [
    page for page in pages
    if page["include_in_rag"]
]

print("\nTotal PDF pages:", len(pages))
print("Learning pages:", len(learning_pages))
print("Excluded pages:", len(pages) - len(learning_pages))

if learning_pages:
    print("First learning page:", learning_pages[0]["pdf_page_index"])
    print("Last learning page:", learning_pages[-1]["pdf_page_index"])

unmapped_pages = [
    page["pdf_page_index"]
    for page in pages
    if page["exclusion_reason"] == "Page is not covered by the structure map"
]

if unmapped_pages:
    print("WARNING - Unmapped pages:", unmapped_pages)

for warning in structure_warnings:
    print("WARNING -", warning)

print("Output saved successfully!")


#----------- Possible OCR Noise -------------

# Very short lines are listed for manual review only; nothing is deleted.
suspicious_lines = defaultdict(list)

for page in learning_pages:

    for line_number, line in enumerate(page["processed_content"].splitlines(), start=1):

        line = line.strip()

        if line and len(line) <= 2 and not line.isdigit():
            suspicious_lines[line].append(page["pdf_page_index"])

if suspicious_lines:
    print("\nVery short lines (review only, nothing deleted):")

    for line, locations in sorted(suspicious_lines.items()):
        print(f"  {line!r}: pages {locations}")
