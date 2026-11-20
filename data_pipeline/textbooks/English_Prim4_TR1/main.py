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
    "book_id": "English_Prim4_TR1",
    "subject": "English",
    "grade": 4,
    "term": 1,
    "language": "en",
    "unit_type": "unit"
}


#----------- Read OCR File -------------

input_file = BASE_DIR / "English_P4_T1" / "English_language_prim4_t1_corrected.txt"

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
    1: "The Five Senses",
    2: "My Community",
    3: "Animals in Our World",
    4: "Egypt - My Homeland",
    5: "A Day at Work",
    6: "The Hundred Dresses"
}

# Lesson start pages and titles are taken from the "Lesson N" headings.
# A lesson label ("Story Time", "Writing", "Think and Create") is joined
# to the lesson title with ": ".
lessons = [

    #----------- Unit 1 -------------

    {"unit_id": 1, "lesson_id": 1, "lesson_title": "What are the Five Senses?", "start_page": 8, "end_page": 10},
    {"unit_id": 1, "lesson_id": 2, "lesson_title": "Healthy Habits", "start_page": 11, "end_page": 13},
    {"unit_id": 1, "lesson_id": 3, "lesson_title": "Story Time: Goha's Great Meal", "start_page": 14, "end_page": 17},
    {"unit_id": 1, "lesson_id": 4, "lesson_title": "Writing: Sequence Words", "start_page": 18, "end_page": 19},
    {"unit_id": 1, "lesson_id": 5, "lesson_title": "Think and Create: A Presentation", "start_page": 20, "end_page": 20},

    #----------- Unit 2 -------------

    {"unit_id": 2, "lesson_id": 1, "lesson_title": "Helping the Community", "start_page": 24, "end_page": 26},
    {"unit_id": 2, "lesson_id": 2, "lesson_title": "Community Problems and Solutions", "start_page": 27, "end_page": 29},
    {"unit_id": 2, "lesson_id": 3, "lesson_title": "Egypt - My Culture", "start_page": 30, "end_page": 33},
    {"unit_id": 2, "lesson_id": 4, "lesson_title": "Writing: A Diary Entry", "start_page": 34, "end_page": 35},
    {"unit_id": 2, "lesson_id": 5, "lesson_title": "Think and Create: A Poster", "start_page": 36, "end_page": 36},

    #----------- Unit 3 -------------

    {"unit_id": 3, "lesson_id": 1, "lesson_title": "Let's Meet the Animals!", "start_page": 40, "end_page": 42},
    {"unit_id": 3, "lesson_id": 2, "lesson_title": "Taking Care of Animals", "start_page": 43, "end_page": 45},
    {"unit_id": 3, "lesson_id": 3, "lesson_title": "Story Time: The Old Lion and The Fox", "start_page": 46, "end_page": 49},
    {"unit_id": 3, "lesson_id": 4, "lesson_title": "Writing: A Research Report", "start_page": 50, "end_page": 53},
    {"unit_id": 3, "lesson_id": 5, "lesson_title": "Think and Create: A Collage", "start_page": 54, "end_page": 54},

    #----------- Unit 4 -------------

    {"unit_id": 4, "lesson_id": 1, "lesson_title": "Places in Egypt", "start_page": 62, "end_page": 64},
    {"unit_id": 4, "lesson_id": 2, "lesson_title": "My City", "start_page": 65, "end_page": 67},
    {"unit_id": 4, "lesson_id": 3, "lesson_title": "The World of Big Numbers", "start_page": 68, "end_page": 69},
    {"unit_id": 4, "lesson_id": 4, "lesson_title": "Writing: A Blog", "start_page": 70, "end_page": 73},
    # Pages 75-76 continue the leaflet task (tip + template) without a
    # new heading, so they stay in lesson 5.
    {"unit_id": 4, "lesson_id": 5, "lesson_title": "Think and Create: A Leaflet", "start_page": 74, "end_page": 76},

    #----------- Unit 5 -------------

    {"unit_id": 5, "lesson_id": 1, "lesson_title": "Different Jobs", "start_page": 80, "end_page": 82},
    {"unit_id": 5, "lesson_id": 2, "lesson_title": "Jobs I Love!", "start_page": 83, "end_page": 85},
    {"unit_id": 5, "lesson_id": 3, "lesson_title": "Story Time: \"The Last House\"", "start_page": 86, "end_page": 89},
    {"unit_id": 5, "lesson_id": 4, "lesson_title": "Writing: Non-Fiction", "start_page": 90, "end_page": 91},
    {"unit_id": 5, "lesson_id": 5, "lesson_title": "Think and Create: Origami Art", "start_page": 92, "end_page": 92}
]

# Pages that belong to the book structure but not to a numbered lesson.
# Unit 6 is a story unit without numbered lessons; the reviews and the
# glossary are book-level sections (unit_id = None).
special_sections = [
    {"section_type": "unit_opener", "unit_id": 1, "section_title": "Unit 1 - Learning Outcomes", "start_page": 7, "end_page": 7},
    {"section_type": "quick_review", "unit_id": 1, "section_title": "Quick Review", "start_page": 21, "end_page": 21},
    {"section_type": "self_assessment", "unit_id": 1, "section_title": "Self-Assessment", "start_page": 22, "end_page": 22},

    {"section_type": "unit_opener", "unit_id": 2, "section_title": "Unit 2 - Learning Outcomes", "start_page": 23, "end_page": 23},
    {"section_type": "quick_review", "unit_id": 2, "section_title": "Quick Review", "start_page": 37, "end_page": 37},
    {"section_type": "self_assessment", "unit_id": 2, "section_title": "Self-Assessment", "start_page": 38, "end_page": 38},

    {"section_type": "unit_opener", "unit_id": 3, "section_title": "Unit 3 - Learning Outcomes", "start_page": 39, "end_page": 39},
    {"section_type": "quick_review", "unit_id": 3, "section_title": "Quick Review", "start_page": 55, "end_page": 55},
    {"section_type": "self_assessment", "unit_id": 3, "section_title": "Self-Assessment", "start_page": 56, "end_page": 56},

    {"section_type": "review", "unit_id": None, "section_title": "Review 1", "start_page": 57, "end_page": 59},
    {"section_type": "review", "unit_id": None, "section_title": "Review 1 - Self-Assessment", "start_page": 60, "end_page": 60},

    {"section_type": "unit_opener", "unit_id": 4, "section_title": "Unit 4 - Learning Outcomes", "start_page": 61, "end_page": 61},
    {"section_type": "quick_review", "unit_id": 4, "section_title": "Quick Review", "start_page": 77, "end_page": 77},
    {"section_type": "self_assessment", "unit_id": 4, "section_title": "Self-Assessment", "start_page": 78, "end_page": 78},

    {"section_type": "unit_opener", "unit_id": 5, "section_title": "Unit 5 - Learning Outcomes", "start_page": 79, "end_page": 79},
    {"section_type": "quick_review", "unit_id": 5, "section_title": "Quick Review", "start_page": 93, "end_page": 93},
    {"section_type": "self_assessment", "unit_id": 5, "section_title": "Self-Assessment", "start_page": 94, "end_page": 94},

    {"section_type": "unit_opener", "unit_id": 6, "section_title": "Unit 6 - Learning Outcomes", "start_page": 95, "end_page": 95},
    {"section_type": "story", "unit_id": 6, "section_title": "The Hundred Dresses (by Eleanor Estes)", "start_page": 96, "end_page": 107},
    {"section_type": "self_assessment", "unit_id": 6, "section_title": "Self-Assessment", "start_page": 108, "end_page": 108},

    {"section_type": "review", "unit_id": None, "section_title": "Review 2", "start_page": 109, "end_page": 112},
    {"section_type": "review", "unit_id": None, "section_title": "Review 2 - Self-Assessment", "start_page": 113, "end_page": 113},

    {"section_type": "glossary", "unit_id": None, "section_title": "Glossary of Words and Phrases", "start_page": 114, "end_page": 116}
]

# Non-learning pages are kept in pages.json for traceability.
excluded_page_info = {
    1: ("front_matter", "Book cover"),
    2: ("front_matter", "Dedication, copyright and student name page"),
    3: ("front_matter", "Term 1 scope and sequence table (curriculum overview)"),
    4: ("front_matter", "Term 1 scope and sequence table (curriculum overview)"),
    5: ("front_matter", "Term 1 scope and sequence table (curriculum overview)"),
    6: ("front_matter", "Message from the Ministry (not lesson content)"),
    117: ("notes", "Blank lined notes page"),
    118: ("notes", "Blank lined notes page"),
    119: ("notes", "Blank lined notes page"),
    120: ("back_matter", "Back cover with credits and printing data"),
    121: ("back_matter", "Back cover with general values messages")
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
carry_forward_pages = {75, 76}

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
