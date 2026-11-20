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
    "book_id": "Science_ARABIC_Prim4_TR1",
    "subject": "Science",
    "grade": 4,
    "term": 1,
    "language": "ar",
    "unit_type": "chapter"
}

input_file = (
    BASE_DIR
    / "Science_P4_T1"
    / "Science_Ar_prim4_t1_corrected.txt"
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
        r"^.*الصف الرابع الابتدائي.*$",
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
    {"unit_id": 1, "unit_title": "الطبيعة من حولنا", "start_page": 7, "end_page": 26},
    {"unit_id": 2, "unit_title": "كيف تنمو الحشرات؟", "start_page": 27, "end_page": 36},
    {"unit_id": 3, "unit_title": "كيف تنمو النباتات؟", "start_page": 37, "end_page": 50},
    {"unit_id": 4, "unit_title": "خصائص الضوء", "start_page": 51, "end_page": 68},
    {"unit_id": 5, "unit_title": "خصائص الصوت", "start_page": 69, "end_page": 78},
    {"unit_id": 6, "unit_title": "قوة الرياح", "start_page": 79, "end_page": 84},
    {"unit_id": 7, "unit_title": "قوة المطاط", "start_page": 85, "end_page": 92},
    {"unit_id": 8, "unit_title": "التربة والماء والحياة في مصر", "start_page": 93, "end_page": 100},
]

# Lesson starts and titles are taken from the lesson headings in the transcription.
#----------- Lesson Structure -------------

lesson_starts = {
    1: [
        (7, 1, "لنبحث عن الكائنات الحية"),
        (9, 2, "كيف نلاحظ؟"),
        (13, 3, "ألوان وأشكال الكائنات الحية"),
        (17, 4, "أماكن مختلفة، كائنات حية مختلفة"),
        (21, 5, "الكائنات الحية الصحراوية"),
    ],
    2: [
        (27, 1, "البيض واليرقات"),
        (29, 2, "الشرنقة والحشرات البالغة"),
        (33, 3, "تركيب جسم الحشرات البالغة"),
    ],
    3: [
        (37, 1, "زراعة البذور"),
        (39, 2, "بعد الإنبات"),
        (43, 3, "الأزهار والثمار"),
        (47, 4, "أجزاء النبات"),
    ],
    4: [
        (51, 1, "كيف ينتقل ضوء الشمس؟"),
        (53, 2, "تجميع الضوء"),
        (57, 3, "الظلال والشمس (١)"),
        (59, 4, "الظلال والشمس (٢)"),
        (63, 5, "الشمس والظل"),
    ],
    5: [
        (69, 1, "كيف ينتج الصوت؟"),
        (71, 2, "شدة الصوت والاهتزاز"),
        (75, 3, "كيف ينتقل الصوت؟"),
    ],
    6: [
        (79, 1, "السيارات التي تعمل بقوة الرياح"),
        (81, 2, "حجم الشراع"),
    ],
    7: [
        (85, 1, "السيارات التي تعمل بقوة المطاط"),
        (87, 2, "قوة الأشرطة المطاطية"),
    ],
    8: [
        (93, 1, "العلاقة بين اليابسة والماء"),
        (97, 2, "نقل التماثيل الحجرية الضخمة"),
    ],
}

# Chapter-level pages that are not part of a numbered lesson.
# They keep their chapter but get lesson_id = None and their own section
# type, instead of being attributed to whichever lesson came before them.
# Titles are taken from the page headings.
special_sections = {
    15: ("enrichment", "هيَّا نتوسَّع"),
    16: ("enrichment", "هيَّا نتوسَّع"),
    25: ("enrichment", "ركن إثرائي الفصل الأول: الجِعران.. منظِّف الصحراء"),
    26: ("enrichment", "ركن إثرائي الفصل الأول: الجِعران.. منظِّف الصحراء"),
    36: ("chapter_review", "هيَّا نُراجع ما تعلَّمناه، ونلخِّصه!"),
    46: ("enrichment", "هيَّا نتوسَّع"),
    66: ("enrichment", "هيَّا نتوسَّع"),
    67: ("enrichment", "ركن إثرائي الفصل الرابع: \"سحر التاريخ\" الذي صنعه الضوء والصوت"),
    68: ("enrichment", "ركن إثرائي الفصل الرابع: \"سحر التاريخ\" الذي صنعه الضوء والصوت"),
    78: ("enrichment", "هيَّا نصنعه!"),
    # This enrichment corner covers chapters 6 and 7; it is printed inside
    # chapter 7's page range, so it is attached to chapter 7.
    91: ("enrichment", "ركن إثرائي الفصل السادس والسابع: الرياح التي تعبُر النيل، والطاقة المخزنة في المطاط"),
    92: ("enrichment", "ركن إثرائي الفصل السادس والسابع: الرياح التي تعبُر النيل، والطاقة المخزنة في المطاط"),
}

# Book-level appendix (scientific inquiry skills). Not part of any chapter.
appendix_pages = {
    101: "إتقان بطاقة تسجيل الملاحظة",
    102: "كيفية استخدام أدوات الملاحظة ①: مقياس الحرارة",
    103: "كيفية استخدام أدوات الملاحظة ②: البوصلة",
    104: "كيفية إجراء البحث العلمي (دورة الاستقصاء العلمي)",
}

# Non-learning pages kept in pages.json for traceability.
excluded_page_info = {
    1: ("front_matter", "Book cover"),
    2: ("front_matter", "Dedication and student name page"),
    3: ("front_matter", "Authors and copyright page"),
    4: ("front_matter", "Introduction to the book (not lesson content)"),
    5: ("front_matter", "Characters page (\"هيا نتعلَّم معًا!\")"),
    6: ("front_matter", "Table of contents"),
    105: ("back_matter", "Back cover"),
    106: ("back_matter", "Back cover (publisher logos)"),
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
