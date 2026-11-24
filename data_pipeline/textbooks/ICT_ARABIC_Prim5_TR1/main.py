from pathlib import Path
import re
import sys
import json
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent

# Force UTF-8 output so the script never crashes while printing.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


#----------- Book Information -------------

# book_id is the textbook folder name. It prefixes every chunk ID so
# chunks stay unique when the six books are merged into one corpus.
BOOK_INFO = {
    "book_id": "ICT_ARABIC_Prim5_TR1",
    "subject": "ICT",
    "grade": 5,
    "term": 1,
    "language": "ar",
    "unit_type": "unit"
}


#----------- Read OCR File -------------

input_file = Path(
    BASE_DIR / "ICT_P5_T1" / "ICT_ARABIC_Prim5_TR1_transcription.txt"
)

if not input_file.exists():
    raise FileNotFoundError(f"ICT transcription file was not found: {input_file}")

raw_text = input_file.read_text(encoding="utf-8")


#----------- Extract Pages -------------

page_pattern = r"(?m)^Page\s+(\d+)\s*$"
matches = list(re.finditer(page_pattern, raw_text))

pages = []

for i, match in enumerate(matches):

    page_number = int(match.group(1))
    start = match.end()

    if i + 1 < len(matches):
        end = matches[i + 1].start()
    else:
        end = len(raw_text)

    page_content = raw_text[start:end].strip()

    # Detect the printed page number from the final standalone number.
    # Keep it as text because the source may use Arabic-Indic digits.
    content_lines = [
        line.strip()
        for line in page_content.splitlines()
        if line.strip()
    ]

    printed_page = None

    if content_lines:
        printed_match = re.fullmatch(r"[٠-٩0-9]+", content_lines[-1])
        if printed_match:
            printed_page = content_lines[-1]

    pages.append({
        **BOOK_INFO,
        "pdf_page_index": page_number,
        "printed_page_number": printed_page,
        "raw_content": page_content,
        "processed_content": None,
    })


#----------- Text Cleaning -------------

def clean_text(text):

    # Remove standalone lesson heading lines only.
    # Lesson titles and body content are preserved.
    text = re.sub(
        r"^الدرس\s+(الأول|الأولى|الثاني|الثانى|الثالث|الرابع|الخامس|السادس)\s*[:：]?\s*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove OCR uncertainty markers from processed content only.
    # raw_content remains unchanged for reference and review.
    # (The markers are a missing word, an alternative reading or a note,
    # depending on the case, so they cannot be resolved automatically. Each
    # affected source line is listed in the page field "ocr_uncertain_readings"
    # for manual review.)
    text = re.sub(
        r"\[قراءة محتملة:[^\]]*\]",
        "",
        text
    )

    text = re.sub(
        r"\[غير واضح\]",
        "",
        text
    )

    # Normalize excessive spaces and empty lines.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


#----------- Apply Cleaning -------------

for page in pages:

    page["processed_content"] = clean_text(
        page["raw_content"]
    )

    # Source lines containing an OCR uncertainty marker, kept for manual review.
    page["ocr_uncertain_readings"] = [
        line.strip()
        for line in page["raw_content"].splitlines()
        if "[قراءة محتملة:" in line or "[غير واضح]" in line
    ]


#----------- Textbook Structure -------------

lessons = [

    #----------- Unit 1 -------------

    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات في حياتنا",
        "lesson_id": 1,
        "lesson_title": "الأجهزة الملحقة بالحاسب الآلي",
        "start_page": 7,
        "end_page": 9
    },
    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات في حياتنا",
        "lesson_id": 2,
        "lesson_title": "الشبكات وأنواعها",
        "start_page": 10,
        "end_page": 12
    },
    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات في حياتنا",
        "lesson_id": 3,
        "lesson_title": "أنظمة التواصل الذكية",
        "start_page": 13,
        "end_page": 15
    },
    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات في حياتنا",
        "lesson_id": 4,
        "lesson_title": "مشكلات الاتصال بالإنترنت وخطوات حلها",
        "start_page": 16,
        "end_page": 18
    },
    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات في حياتنا",
        "lesson_id": 5,
        "lesson_title": "الملفات الرقمية وكيفية التعامل معها",
        "start_page": 19,
        "end_page": 22
    },
    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات في حياتنا",
        "lesson_id": 6,
        "lesson_title": "مشاركة المعلومات: متى وأين وكيف؟",
        "start_page": 23,
        "end_page": 25
    },

    #----------- Unit 2 -------------

    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 1,
        "lesson_title": "أساليب حماية البيانات والمعلومات",
        "start_page": 27,
        "end_page": 29
    },
    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 2,
        "lesson_title": "إدارة كلمات المرور",
        "start_page": 30,
        "end_page": 32
    },
    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 3,
        "lesson_title": "طرق التعامل مع المواقع الإلكترونية الاحتيالية",
        "start_page": 33,
        "end_page": 35
    },
    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 4,
        "lesson_title": "حقوق النشر",
        "start_page": 36,
        "end_page": 38
    },
    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 5,
        "lesson_title": "الأمن الوقائي وانتقاء المصادر الرقمية",
        "start_page": 39,
        "end_page": 41
    },
    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 6,
        "lesson_title": "توثيق المعلومات",
        "start_page": 42,
        "end_page": 44
    }
]


#----------- Unit Divider Pages -------------

# Unit divider pages carry only unit artwork and keywords.
unit_dividers = {
    6: (1, "دور تكنولوجيا المعلومات في حياتنا"),
    26: (2, "احتياطات الأمن والسلامة الرقمية")
}


#----------- Assign Unit and Lesson -------------

for page in pages:

    page_number = page["pdf_page_index"]

    page["unit_id"] = None
    page["unit_title"] = None
    page["lesson_id"] = None
    page["lesson_title"] = None

    for lesson in lessons:

        if lesson["start_page"] <= page_number <= lesson["end_page"]:

            page["unit_id"] = lesson["unit_id"]
            page["unit_title"] = lesson["unit_title"]
            page["lesson_id"] = lesson["lesson_id"]
            page["lesson_title"] = lesson["lesson_title"]

            break

    if page_number in unit_dividers:
        page["unit_id"], page["unit_title"] = unit_dividers[page_number]

    # Every ICT learning page belongs to a numbered lesson.
    page["section_type"] = "lesson" if page["lesson_id"] is not None else None
    page["section_title"] = page["lesson_title"]


#----------- Verify Lesson Map Against Headings -------------

# The lesson map above is the source of truth. This check only warns when
# a lesson heading printed on a page disagrees with the mapped lesson.
ordinal_lessons = {
    "الأول": 1, "الأولى": 1, "الثاني": 2, "الثانى": 2, "الثالث": 3,
    "الرابع": 4, "الخامس": 5, "السادس": 6
}

structure_warnings = []

for page in pages:

    # Front matter (e.g. the index page) lists every lesson.
    if page["lesson_id"] is None:
        continue

    heading = re.search(
        r"^الدرس\s+(الأول|الأولى|الثاني|الثانى|الثالث|الرابع|الخامس|السادس)",
        page["raw_content"],
        flags=re.MULTILINE
    )

    if heading and ordinal_lessons[heading.group(1)] != page["lesson_id"]:
        structure_warnings.append(
            f"PDF page {page['pdf_page_index']}: heading says lesson "
            f"{ordinal_lessons[heading.group(1)]}, map says {page['lesson_id']}"
        )


#----------- Check Page Mapping -------------

print("\nPage Mapping:\n")

for page in pages:

    print(
        f"PDF Page {page['pdf_page_index']}: "
        f"Unit {page['unit_id']}, "
        f"Lesson {page['lesson_id']} - "
        f"{page['lesson_title']}"
    )


#----------- Remove Non-Learning Pages -------------

excluded_pages = [
    1, 2, 3, 4, 5, 6,   # Cover, introductory pages, index and Unit 1 divider
    26,                 # Unit 2 divider
    45, 46              # Blank page and copyright page
]

# Excluded pages are kept in pages.json for traceability (so every PDF
# page can be found), but they are flagged and never chunked.
excluded_page_info = {
    1: ("front_matter", "Book cover"),
    2: ("blank", "Page without text"),
    3: ("front_matter", "Authors page"),
    4: ("blank", "Page without text"),
    5: ("front_matter", "Table of contents"),
    6: ("unit_divider", "Unit 1 divider page (unit artwork and keywords only)"),
    26: ("unit_divider", "Unit 2 divider page (unit artwork and keywords only)"),
    45: ("blank", "Page without text"),
    46: ("back_matter", "Copyright page")
}

for page in pages:

    if page["pdf_page_index"] in excluded_pages:
        page_type, reason = excluded_page_info[page["pdf_page_index"]]
        page["page_type"] = page_type
        page["include_in_rag"] = False
        page["exclusion_reason"] = reason
    else:
        page["page_type"] = "content"
        page["include_in_rag"] = True
        page["exclusion_reason"] = None

all_pages = pages

pages = [
    page for page in all_pages
    if page["include_in_rag"]
]


#----------- Define Output Directory -------------

output_dir = Path(
    BASE_DIR / "output"
)

output_dir.mkdir(parents=True, exist_ok=True)


#----------- Save JSON -------------

output_file = output_dir / "pages.json"

output_file.write_text(
    json.dumps(all_pages, ensure_ascii=False, indent=4),
    encoding="utf-8"
)


#----------- Print Summary -------------

print("\nProcessing Summary")
print("------------------")
print("Total extracted PDF pages:", len(matches))
print("Excluded pages:", len(excluded_pages))
print("Total learning pages:", len(pages))

if pages:
    print("First learning page:", pages[0]["pdf_page_index"])
    print("Last learning page:", pages[-1]["pdf_page_index"])

unmapped_pages = [
    page["pdf_page_index"]
    for page in pages
    if page["lesson_id"] is None
]

if unmapped_pages:
    print("WARNING - Unmapped pages:", unmapped_pages)
else:
    print("All learning pages mapped successfully.")

for warning in structure_warnings:
    print("WARNING -", warning)

print("Output saved to:", output_file)


#----------- Possible OCR Noise -------------

suspicious_lines = defaultdict(list)

for page in pages:

    lines = page["processed_content"].splitlines()

    for line_number, line in enumerate(lines, start=1):

        line = line.strip()

        if line and len(line) <= 5:

            suspicious_lines[line].append({
                "page": page["pdf_page_index"],
                "line": line_number
            })


print("\nPossible OCR Noise:\n")

for line, locations in sorted(
    suspicious_lines.items(),
    key=lambda item: len(item[1]),
    reverse=True
):

    print(f"\nText: {repr(line)}")
    print(f"Count: {len(locations)}")
    print("Locations:")

    for location in locations:
        print(
            f"  Page {location['page']}, "
            f"Line {location['line']}"
        )
