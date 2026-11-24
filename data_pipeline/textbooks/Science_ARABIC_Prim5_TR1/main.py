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
# The Science book is organised in chapters (الفصل); the shared schema
# keeps the field names unit_id / unit_title and records unit_type.
BOOK_INFO = {
    "book_id": "Science_ARABIC_Prim5_TR1",
    "subject": "Science",
    "grade": 5,
    "term": 1,
    "language": "ar",
    "unit_type": "chapter"
}

input_file = (
    BASE_DIR
    / "Science_P5_T1"
    / "Science_Ar_prim5_t1_corrected.txt"
)

if not input_file.exists():
    raise FileNotFoundError(f"Science transcription file was not found: {input_file}")

#----------- Read OCR File -------------

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
        r"\[رقم الصفحة:\s*([٠-٩0-9]+)\s*\]",
        page_content
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

    # Remove the printed-page marker only; keep the actual textbook content.
    text = re.sub(
        r"^\[رقم الصفحة:\s*[٠-٩0-9]+\s*\]\s*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove recurring page headers/footers where they appear.
    text = re.sub(
        r"^.*الفصل الدراسي الأول\s*[٠-٩0-9]*\s*$",
        "",
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r"^.*الصف الخامس الابتدائي.*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove OCR uncertainty annotations from processed text only.
    # raw_content remains unchanged for review and provenance.
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

    # Normalize excessive spaces without changing Arabic wording.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

#----------- Apply Cleaning -------------

for page in pages:
    page["processed_content"] = clean_text(page["raw_content"])

# Chapter boundaries are taken from the Science book's contents page.
# PDF page indices are used here (not the printed page numbers).
#----------- Textbook Structure -------------

chapters = [
    {"unit_id": 1, "unit_title": "العظام والعضلات", "start_page": 9, "end_page": 22},
    {"unit_id": 2, "unit_title": "التغيرات في الفصول", "start_page": 23, "end_page": 30},
    {"unit_id": 3, "unit_title": "شروط الإنبات", "start_page": 31, "end_page": 46},
    {"unit_id": 4, "unit_title": "شروط النمو", "start_page": 47, "end_page": 54},
    {"unit_id": 5, "unit_title": "من الزهرة إلى الثمرة", "start_page": 55, "end_page": 66},
    {"unit_id": 6, "unit_title": "نمو الإنسان والتكاثر", "start_page": 67, "end_page": 74},
    {"unit_id": 7, "unit_title": "نمو الحيوانات وتكاثرها", "start_page": 75, "end_page": 82},
    {"unit_id": 8, "unit_title": "تغيرات الطقس", "start_page": 83, "end_page": 94},
    {"unit_id": 9, "unit_title": "دورة الماء", "start_page": 95, "end_page": 106},
]

# Lesson starts and titles are taken from the lesson headings in the transcription.
#----------- Lesson Structure -------------

lesson_starts = {
    1: [
        (9, 1, "العظام والعضلات"),
        (11, 2, "تركيب العظام"),
        (15, 3, "الهيكل العظمي الكامل للجسم"),
        (17, 4, "أجسام الحيوانات"),
    ],
    2: [
        (23, 1, "التغيرات خلال السنة"),
        (25, 2, "الحيوانات ودرجة الحرارة"),
    ],
    3: [
        (31, 1, "ما بداخل البذرة"),
        (33, 2, "الماء والإنبات"),
        (37, 3, "الهواء والإنبات"),
        (39, 4, "درجة الحرارة والإنبات"),
        # PDF page 46 (seed pictures) has no heading of its own; it follows
        # lesson 3-5's question page and keeps lesson 3-5 (carry-forward).
        (43, 5, "ملخص الإنبات"),
    ],
    4: [
        (47, 1, "ضوء الشمس والنمو"),
        (49, 2, "السماد والنمو"),
    ],
    5: [
        (55, 1, "تركيب زهرة نبات اللوف"),
        (58, 2, "كيف نستخدم المجهر؟"),
        (63, 3, "التلقيح وكيف تنمو الثمار"),
    ],
    6: [
        (67, 1, "مراحل نمو الإنسان"),
        (69, 2, "أوجه التشابه بين الآباء والأبناء"),
        (71, 3, "شروط النمو الصحي"),
    ],
    7: [
        (75, 1, "حيوانات تلد صغارًا"),
        (77, 2, "حيوانات تضع البيض"),
        (79, 3, "مقارنة الحيوانات والحفاظ على النوع"),
    ],
    8: [
        (83, 1, "السحب والطقس"),
        (85, 2, "حركة السحب"),
        (89, 3, "التنبؤ بالطقس"),
    ],
    9: [
        (95, 1, "تبخُّر الماء"),
        (97, 2, "بخار الماء في الهواء"),
        (101, 3, "إلى أين يذهب الماء؟"),
    ],
}

# Chapter-level pages that are not part of a numbered lesson.
# They keep their chapter but get lesson_id = None and their own section
# type, instead of being attributed to whichever lesson came before them.
# Titles are taken from the page headings.
special_sections = {
    21: ("enrichment", "ركن إثرائي الفصل ١: الميكانيكا الحيوية (كيف يتحرك الجسم) لعدَّاء الصحراء (الجمل)"),
    22: ("enrichment", "ركن إثرائي الفصل ١: الميكانيكا الحيوية (كيف يتحرك الجسم) لعدَّاء الصحراء (الجمل)"),
    29: ("enrichment", "ركن إثرائي الفصل ٢: حكمة الصحراء (ثعلب الفنك والملابس التقليدية)"),
    30: ("enrichment", "ركن إثرائي الفصل ٢: حكمة الصحراء (ثعلب الفنك والملابس التقليدية)"),
    # This enrichment corner covers chapters 3 and 4; it is printed inside
    # chapter 4's page range, so it is attached to chapter 4.
    53: ("enrichment", "ركن إثرائي الفصل ٣ و٤: البذور السحرية التي تسافر عبر آلاف السنين"),
    54: ("enrichment", "ركن إثرائي الفصل ٣ و٤: البذور السحرية التي تسافر عبر آلاف السنين"),
    66: ("chapter_review", "مراجعة وتدريب"),
    92: ("enrichment", "هيَّا نتوسَّع"),
    93: ("enrichment", "ركن إثرائي الفصل ٨: قراءة سماء الصحراء: سحب مصر وطقسها"),
    94: ("enrichment", "ركن إثرائي الفصل ٨: قراءة سماء الصحراء: سحب مصر وطقسها"),
    105: ("enrichment", "ركن إثرائي الفصل ٩: الماء الذي يختفي ويعود: دورة ماء النيل"),
    106: ("enrichment", "ركن إثرائي الفصل ٩: الماء الذي يختفي ويعود: دورة ماء النيل"),
}

# Book-level appendix (scientific inquiry skills). Not part of any chapter.
appendix_pages = {
    107: "كيفية إجراء البحث العلمي: التجارب العادلة",
    108: "كيفية استخدام أدوات الملاحظة: المِجهر (مراجعة)",
    109: "تسجيل الملاحظات والتجارب: تتبُّع التغيّرات",
    110: "دورة الاستقصاء العلمي (كيف تمارس العلم؟)",
}

# Non-learning pages kept in pages.json for traceability.
excluded_page_info = {
    1: ("front_matter", "Book cover"),
    2: ("front_matter", "Dedication and student name page"),
    3: ("blank", "Blank page"),
    4: ("front_matter", "Authors and copyright page"),
    5: ("blank", "Blank page"),
    6: ("front_matter", "Introduction to the book (not lesson content)"),
    7: ("front_matter", "Characters page (\"هيا نتعلَّم معًا!\")"),
    8: ("front_matter", "Table of contents"),
    111: ("blank", "Blank page"),
    112: ("back_matter", "Back cover"),
    113: ("back_matter", "Printer information"),
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

    page["page_type"] = "unmapped"
    page["include_in_rag"] = False
    page["exclusion_reason"] = None

    # Front matter and back-cover pages are retained in pages.json,
    # but are not sent to RAG.
    if page_number in excluded_page_info:
        page["page_type"], page["exclusion_reason"] = excluded_page_info[page_number]
        continue

    for chapter in chapters:
        if chapter["start_page"] <= page_number <= chapter["end_page"]:
            page["unit_id"] = chapter["unit_id"]
            page["unit_title"] = chapter["unit_title"]

            current_lessons = lesson_starts[chapter["unit_id"]]
            selected_lesson = None

            for lesson_start in current_lessons:
                if lesson_start[0] <= page_number:
                    selected_lesson = lesson_start
                else:
                    break

            if selected_lesson:
                _, lesson_id, lesson_title = selected_lesson
                page["lesson_id"] = lesson_id
                page["lesson_title"] = lesson_title
                page["section_type"] = "lesson"
                page["section_title"] = lesson_title

            page["page_type"] = "content"
            page["include_in_rag"] = True
            break

    # Chapter-level enrichment / review pages have no lesson.
    if page_number in special_sections:
        page["lesson_id"] = None
        page["lesson_title"] = None
        page["section_type"], page["section_title"] = special_sections[page_number]

    # The last four pages are a book-level appendix on scientific inquiry
    # skills. Previously they were attached to chapter 8 with an invented
    # "lesson 0"; they now carry no chapter or lesson.
    if page_number in appendix_pages:
        page["section_type"] = "appendix"
        page["section_title"] = appendix_pages[page_number]
        page["page_type"] = "content"
        page["include_in_rag"] = True

    if page["page_type"] == "unmapped":
        page["exclusion_reason"] = "Page is not covered by the chapter map"


#----------- Verify Structure Against Page Headings -------------

# The chapter/lesson map above is the source of truth. Every lesson page
# prints a header such as "١-٢ كيف نلاحظ؟"; warn if it disagrees with the map.
arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

structure_warnings = []

for page in pages:

    # Odd pages print "١-٢ title | الفصل ١", even pages "الفصل ١ | ١-٢ title".
    header = re.search(
        r"^(?:الفصل\s*[١-٩]\s*\|\s*)?([١-٩])\s*-\s*([١-٩])\s",
        page["raw_content"],
        flags=re.MULTILINE
    )

    if page["section_type"] == "lesson":
        if not header:
            structure_warnings.append(
                f"PDF page {page['pdf_page_index']}: lesson page without a lesson header"
            )
        else:
            chapter_no = int(header.group(1).translate(arabic_digits))
            lesson_no = int(header.group(2).translate(arabic_digits))

            if (chapter_no, lesson_no) != (page["unit_id"], page["lesson_id"]):
                structure_warnings.append(
                    f"PDF page {page['pdf_page_index']}: header says "
                    f"{chapter_no}-{lesson_no}, map says {page['unit_id']}-{page['lesson_id']}"
                )

    elif page["include_in_rag"] and header:
        structure_warnings.append(
            f"PDF page {page['pdf_page_index']}: special page has a lesson header"
        )


# pages.json keeps every PDF page (front and back matter are flagged with
# include_in_rag = false and an exclusion_reason) so the PDF provenance of
# every page stays traceable.

#----------- Check Page Mapping -------------

print("----------- Page Mapping -------------")

for page in pages:
    print(
        f"PDF Page {page['pdf_page_index']}: "
        f"Unit {page['unit_id']}, "
        f"Lesson {page['lesson_id']} - "
        f"{page['lesson_title']} | "
        f"{page['section_type']} | "
        f"{page['page_type']}"
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

print("\nTotal PDF pages:", len(pages))
print("Pages included in RAG:", sum(page["include_in_rag"] for page in pages))
print("Unmapped content pages:", sum(
    page["page_type"] == "unmapped" for page in pages
))

for warning in structure_warnings:
    print("WARNING -", warning)

print("Output saved successfully!")
print("Output file:", output_file)

#----------- Possible OCR Noise -------------

suspicious_lines = defaultdict(list)

for page in pages:
    if not page["include_in_rag"]:
        continue

    lines = page["processed_content"].splitlines()

    for line_number, line in enumerate(lines, start=1):
        line = line.strip()

        if line and len(line) <= 3:
            suspicious_lines[line].append({
                "page": page["pdf_page_index"],
                "line": line_number
            })


print("\nPossible short OCR lines (review before deleting):\n")

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
