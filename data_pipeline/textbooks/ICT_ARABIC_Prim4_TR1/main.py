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
    "book_id": "ICT_ARABIC_Prim4_TR1",
    "subject": "ICT",
    "grade": 4,
    "term": 1,
    "language": "ar",
    "unit_type": "unit"
}


#----------- Read OCR File -------------

input_file = BASE_DIR / "ICT_P4_T1" / "ICT_ARABIC_Prim4_TR1_transcription.txt"

if not input_file.exists():
    raise FileNotFoundError(f"ICT transcription file was not found: {input_file}")

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

    printed_match = re.search(
        r"(?:الفصل الدراسي الأول|تكنولوجيا المعلومات والإتصالات\s*-\s*الصف الرابع الابتدائي)\s*([٠-٩0-9]+)\s*$",
        page_content,
        flags=re.MULTILINE
    )

    printed_page = None

    if printed_match:
        printed_page = printed_match.group(1).strip()

    pages.append({
        **BOOK_INFO,
        "pdf_page_index": page_number,
        "printed_page_number": printed_page,
        "raw_content": page_content,
        "processed_content": None,
    })


#----------- Text Cleaning -------------

def clean_text(text):

    # Remove lesson headings
    text = re.sub(
        r"^الدرس\s+(الأول|الثاني|الثالث|الرابع|الخامس|السادس)\s*[:：].*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove textbook footer
    text = re.sub(
        r"^.*تكنولوجيا المعلومات.*الصف الرابع.*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove semester footer
    text = re.sub(
        r"^الفصل الدراسي الأول\s*[٠-٩0-9]*\s*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove uncertainty markers from processed content only
    # raw_content remains unchanged for reference and review
    # (The markers are a missing word, an alternative reading or a note,
    # depending on the case, so they cannot be resolved automatically. Each
    # affected source line is listed in the page field "ocr_uncertain_readings"
    # for manual review.)
    text = re.sub(
        r"\[قراءة محتملة:.*?\]",
        "",
        text,
        flags=re.DOTALL
    )

    text = re.sub(
        r"\[غير واضح\]",
        "",
        text
    )

    # Remove confirmed OCR noise
    noise_patterns = [
        r'^مه"\s*$',
        r'^t:\s*$',
        r'^ooe\s*$',
        r'^aaa\s*$',
        r'^O,\s*$',
        r'^BODOG\s*$',
        r'^رهكد\s*$',
        r'^جيا!\s*$',
        r'^00000\s*$',
        r'^\.EUE\s*$',
        r'^vcp\s*$',
        r'^9\)\s*$',
        r'^٠\s*$',
        r'^4\s*$',
        r'^:١\.\s*$',
        r'^لأ\s*$',
        r'^تد\s*$'
    ]

    for pattern in noise_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.MULTILINE
        )

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce multiple empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove spaces at the beginning and end
    text = text.strip()

    return text


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

    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات فى حياتنا",
        "lesson_id": 1,
        "lesson_title": "أدوات الاستكشافات العلمية",
        "start_page": 5,
        "end_page": 8
    },

    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات فى حياتنا",
        "lesson_id": 2,
        "lesson_title": "أجهزة الحاسب ومكوناتها",
        "start_page": 9,
        "end_page": 12
    },

    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات فى حياتنا",
        "lesson_id": 3,
        "lesson_title": "أنظمة التشغيل",
        "start_page": 13,
        "end_page": 16
    },

    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات فى حياتنا",
        "lesson_id": 4,
        "lesson_title": "التكنولوجيا المساعدة",
        "start_page": 17,
        "end_page": 20
    },

    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات فى حياتنا",
        "lesson_id": 5,
        "lesson_title": "المشكلات التكنولوجية الشائعة وحلولها",
        "start_page": 21,
        "end_page": 24
    },

    {
        "unit_id": 1,
        "unit_title": "دور تكنولوجيا المعلومات فى حياتنا",
        "lesson_id": 6,
        "lesson_title": "مصادر جمع البيانات وتحليلها",
        "start_page": 25,
        # Page 29 is the Unit 2 divider page, not part of this lesson.
        "end_page": 28
    },

    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 1,
        "lesson_title": "الحماية من مخاطر شبكة الإنترنت",
        "start_page": 30,
        "end_page": 33
    },

    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 2,
        "lesson_title": "الاستخدام الصحيح والأخلاقى لتكنولوجيا المعلومات",
        "start_page": 34,
        "end_page": 37
    },

    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 3,
        "lesson_title": "عمليات البحث على شبكة الإنترنت",
        "start_page": 38,
        "end_page": 41
    },

    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 4,
        "lesson_title": "الجهات المسئولة عن حل مشكلات الإنترنت",
        "start_page": 42,
        "end_page": 45
    },

    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 5,
        "lesson_title": "الأمان الرقمي",
        "start_page": 46,
        "end_page": 49
    },

    {
        "unit_id": 2,
        "unit_title": "احتياطات الأمن والسلامة الرقمية",
        "lesson_id": 6,
        "lesson_title": "مشروع تطبيقي",
        "start_page": 50,
        # Page 54 is blank and page 55 is the copyright page.
        "end_page": 53
    }
]


#----------- Unit Divider Pages -------------

# Unit divider pages carry only the unit number and title.
unit_dividers = {
    4: (1, "دور تكنولوجيا المعلومات فى حياتنا"),
    29: (2, "احتياطات الأمن والسلامة الرقمية")
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
    "الأول": 1, "الثاني": 2, "الثانى": 2, "الثالث": 3,
    "الرابع": 4, "الخامس": 5, "السادس": 6
}

structure_warnings = []

for page in pages:

    # Front matter (e.g. the table of contents) lists every lesson.
    if page["lesson_id"] is None:
        continue

    heading = re.search(
        r"^الدرس\s+(الأول|الثاني|الثانى|الثالث|الرابع|الخامس|السادس)",
        page["raw_content"],
        flags=re.MULTILINE
    )

    if heading and ordinal_lessons[heading.group(1)] != page["lesson_id"]:
        structure_warnings.append(
            f"PDF page {page['pdf_page_index']}: heading says lesson "
            f"{ordinal_lessons[heading.group(1)]}, map says {page['lesson_id']}"
        )


""" #----------- Check Page Mapping -------------

for page in pages:

    print(
        f"PDF Page {page['pdf_page_index']}: "
        f"Unit {page['unit_id']}, "
        f"Lesson {page['lesson_id']} - "
        f"{page['lesson_title']}"
    ) """


#----------- Mark Cover Pages -------------

# Cover pages are kept in pages.json for traceability (so every PDF page
# can be found), but they are flagged and never chunked.
cover_pages = [
    1, 2, 3, 4, 5, 9, 13, 17, 21, 25,
    29, 30, 34, 38, 42, 46, 50, 54, 55
]

excluded_page_info = {
    1: ("front_matter", "Book cover"),
    2: ("front_matter", "Authors page"),
    3: ("front_matter", "Table of contents"),
    4: ("unit_divider", "Unit 1 divider page (unit title only)"),
    29: ("unit_divider", "Unit 2 divider page (unit title only)"),
    54: ("blank", "Blank page"),
    55: ("back_matter", "Copyright page")
}

for page in pages:

    page_number = page["pdf_page_index"]

    if page_number in cover_pages:

        page_type, reason = excluded_page_info.get(
            page_number,
            ("lesson_divider", "Lesson title page (lesson title only)")
        )

        page["page_type"] = page_type
        page["include_in_rag"] = False
        page["exclusion_reason"] = reason

    else:
        page["page_type"] = "content"
        page["include_in_rag"] = True
        page["exclusion_reason"] = None

learning_pages = [
    page for page in pages
    if page["include_in_rag"]
]


#----------- Define Output Directory -------------

output_dir = BASE_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)


#----------- Save JSON -------------

output_file = output_dir / "pages.json"

output_file.write_text(
    json.dumps(pages, ensure_ascii=False, indent=4),
    encoding="utf-8"
)

print("Total PDF pages:", len(pages))
print("Learning pages:", len(learning_pages))
print("Excluded pages:", len(pages) - len(learning_pages))

if learning_pages:
    print("First learning page:", learning_pages[0]["pdf_page_index"])
    print("Last learning page:", learning_pages[-1]["pdf_page_index"])

unmapped_pages = [
    page["pdf_page_index"]
    for page in learning_pages
    if page["lesson_id"] is None
]

if unmapped_pages:
    print("WARNING - Unmapped learning pages:", unmapped_pages)

for warning in structure_warnings:
    print("WARNING -", warning)

print("Output saved successfully!")


""" #----------- Possible OCR Noise -------------

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



#----------- Inspect Suspicious Text -------------

targets = [
    '9)',
    '٠',
    '4',
    ':١.',
    'لأ',
    '١',
    'www',
    'تد',
    'كل'
]

for page in pages:

    lines = page["processed_content"].splitlines()

    for i, line in enumerate(lines):

        if line.strip() in targets:

            print("\n" + "=" * 60)
            print("PDF Page:", page["pdf_page_index"])
            print("Suspicious text:", repr(line.strip()))

            start = max(0, i - 5)
            end = min(len(lines), i + 6)

            print("\nContext:")

            for j in range(start, end):
                print(f"{j + 1}: {lines[j]}")
 """
