from pathlib import Path
import re
import sys
import json
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent

# Force UTF-8 console output (Arabic text and Arabic-Indic digits).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


#----------- Read Pages JSON -------------

input_file = BASE_DIR / "output" / "pages.json"
pages = json.loads(input_file.read_text(encoding="utf-8"))

#----------- Chunking Settings -------------

max_chunk_chars = 1000

max_activity_chars = 1500

#----------- Text Patterns -------------

# Block headings, in the order they are checked. Each heading starts a
# new block that runs until the next heading (reading order is kept).
# Instructions such as "اختر الإجابة الصحيحة" and "ضع علامة" belong to a
# question and must NOT start a new section.
question_section_headings = [
    "حاول", "تدرَّب", "تدرب", "الأسئلة والتدريبات", "مراجعة وتدريب"
]

# Only "نشاط" opens an activity. Words such as "جرِّب" or "اكتشف" also
# appear INSIDE activities (as steps), so they are not block headings.
activity_headings = [
    "نشاط:", "نشاط"
]

objective_headings = ["أهداف الدرس", "أهداف التعلُّم", "أهداف التعلم"]

# "تعلَّم" (learn) boxes hold the core scientific explanation of a lesson.
learn_headings = ["تعلَّم:", "تعلَّم", "تعلم:", "تعلم"]

# Chapter-level extension / enrichment / review blocks.
enrichment_headings = [
    "هيَّا نتوسَّع", "هيا نتوسع",
    "هيَّا نصنعه!", "هيا نصنعه",
    "ركن إثرائي",
    "هيَّا نُراجع", "هيا نراجع"
]

option_pattern = re.compile(r"^\s*[أبجدهـA-E]\s*[:.)-]\s*")
# Main question with nested part: ١ (١) ...
top_level_with_part_pattern = re.compile(r"^\s*([٠-٩0-9]+)\s*[.)-]?\s*\(([٠-٩0-9]+)\)\s*\S")
# Standalone numbered question: (١) ...
parenthesized_question_pattern = re.compile(r"^\s*\(([٠-٩0-9]+)\)\s*\S")
# Standalone numbered question: ١- ... / ١. ...
numbered_question_pattern = re.compile(r"^\s*([٠-٩0-9]+)\s*[.)-]\s*\S")
# Main question number followed by a space: "١ ما ..." (Primary 5 style)
spaced_question_pattern = re.compile(r"^\s*([٠-٩0-9]+)\s+(?!\()\S")

# Numbered step inside an activity: "١ التحضير:", "٢ التجربة:" ...
activity_step_pattern = re.compile(r"^\s*([٠-٩0-9]+)\s+\S")

# Page running headers (the information is already in the page metadata):
#   "١-٢ كيف نلاحظ؟ | الفصل ١"  /  "الفصل ١ | ١-٢ كيف نلاحظ؟"
#   "الفصل الأول: الطبيعة من حولنا"  /  "ركن إثرائي الفصل ١ | ..."
running_header_patterns = [
    re.compile(r"^(?:الفصل\s*[١-٩]\s*\|\s*)?[١-٩]\s*-\s*[١-٩]+\s"),
    re.compile(r"^الفصل\s+(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع)\s*:"),
    re.compile(r"^ركن إثرائي"),
]

# Decorative number badge printed beside some activity titles, e.g. "[١٠]".
# Its meaning is not stated on the page; it stays in raw_content only.
badge_pattern = re.compile(r"^\[\s*[٠-٩0-9]+\s*\]$")

# Activity parts recognised from step labels (used for metadata only).
activity_component_labels = [
    ("materials", r"التحضير|الأدوات|المواد|ما نحتاجه"),
    ("prediction", r"خمِّن|خمن|توقَّع|توقع"),
    ("procedure", r"التجربة|طريقة الصنع|خطوات|جرِّب|جرب"),
    ("observation", r"الملاحظة|لاحظ|راقب"),
    ("results", r"النتائج|النتيجة"),
    ("recording", r"سجِّل|سجل|دوِّن"),
    ("conclusion", r"الاستنتاج|استنتج|اكتشف|استكشف"),
]

# Section codes used in chunk IDs for pages that are not numbered lessons.
section_codes = {
    "enrichment": "ENR",
    "chapter_review": "REV",
    "appendix": "APX",
}

#----------- Text Helpers -------------

def normalize_lines(text):
    ignored_lines = {"الفصل الدراسي الأول", "العلوم", "الصف الرابع", "الصف الخامس"}
    return [line.strip() for line in text.splitlines() if line.strip() and line.strip() not in ignored_lines]


def normalize_heading(line):
    return re.sub(r"\s+", " ", line.strip()).rstrip(":：")


def matches_heading(line, headings):
    normalized = normalize_heading(line)
    return any(
        normalized == normalize_heading(h)
        or normalized.startswith(normalize_heading(h) + " ")
        or normalized.startswith(normalize_heading(h) + ":")
        for h in headings
    )


def is_question_section_heading(line):
    # Question-section headings ("حاول", "تدرَّب", ...) are always printed
    # alone on their line. An exact match is required because ordinary
    # sentences can start with the same word, e.g.
    # "حاول أن تلمس منتصف ظهرك ..." (explanation text, not a heading).
    normalized = normalize_heading(line)
    return any(normalized == normalize_heading(h) for h in question_section_headings)


def is_activity_heading(line):
    return matches_heading(line, activity_headings)


def is_objective_heading(line):
    return matches_heading(line, objective_headings)


def is_learn_heading(line):
    return matches_heading(line, learn_headings)


def is_enrichment_heading(line):
    return matches_heading(line, enrichment_headings)


def build_chunk_id(page, chunk_number):
    # Book prefix + original U/L/P/C convention. Pages that are not part of
    # a numbered lesson use a section code instead of the lesson number.
    parts = [page["book_id"]]

    if page.get("unit_id") is not None:
        parts.append(f"U{page['unit_id']}")

    if page.get("section_type") == "lesson":
        parts.append(f"L{page['lesson_id']}")
    else:
        parts.append(section_codes.get(page.get("section_type"), "SEC"))

    parts.append(f"P{page['pdf_page_index']}")
    parts.append(f"C{chunk_number:03d}")

    return "_".join(parts)


def make_chunk(page, text, chunk_type, chunk_number, extra_metadata=None):
    chunk = {
        "chunk_id": build_chunk_id(page, chunk_number),
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


def is_sub_heading(line):
    # Short lines ending with ":" or "؟" (e.g. "أين توجد الكائنات الحية؟",
    # "كيفية استخدام العدسة المكبِّرة") or numbered headings start a new idea.
    return len(line) <= 60 and (
        line.rstrip().endswith((":", "：", "؟", "?"))
        or bool(activity_step_pattern.match(line))
    )


def split_long_text(lines, max_chars=max_chunk_chars):
    # Split at the last sub-heading before the limit so that a heading is
    # never separated from its explanation; fall back to a line boundary.
    result, current = [], []
    for line in lines:
        if current and len("\n".join(current)) + len(line) + 1 > max_chars:
            cut = None
            for index in range(len(current) - 1, 0, -1):
                if is_sub_heading(current[index]):
                    cut = index
                    break
            if cut is not None and len("\n".join(current[:cut])) >= max_chars // 3:
                result.append("\n".join(current[:cut]))
                current = current[cut:]
            else:
                result.append("\n".join(current))
                current = []
        current.append(line)
    if current:
        result.append("\n".join(current))
    return result

#----------- Question Classification -------------

def classify_question(text):
    lines = text.splitlines()
    has_options = sum(bool(option_pattern.match(line)) for line in lines) >= 2

    # Fill-in blanks are identified by dotted blanks or explicit fill-in wording.
    # Plain ( ) is NOT enough: it is commonly used by true/false and matching questions.
    has_fill_blank = bool(re.search(
        r"\(\s*(?:\.{2,}|…{2,}|ـ{2,})\s*\)|\.{4,}|…{2,}|(?:أكمل|املأ|ملء|لإكمال)\s+(?:ال)?(?:فراغ|جملة|الجدول)",
        text
    ))

    has_true_false = bool(re.search(
        r"(?:ضع\s+علامة.{0,100}(?:الصحيحة|غير الصحيحة)|صح\s+أم\s+خطأ|صواب\s+أم\s+خطأ|علامة\s*\(\s*[✓✗√×])",
        text
    ))

    # Matching: "صِل ..." (connect) / "طابق ..." (match).
    has_matching = bool(re.search(r"(?:^|\s)(?:صِل|صل|وصِّل|وصل|طابق)\s", text))

    # In a matching question the answers are written in dotted blanks, so
    # those blanks do not make it a separate fill-in task.
    if has_matching:
        has_fill_blank = False

    # Matching items with blank parentheses but without true/false wording are open response.
    task_kinds = sum([has_options, has_fill_blank, has_true_false, has_matching])
    if task_kinds >= 2:
        return "mixed_question"
    if has_true_false:
        return "true_false"
    if has_matching:
        return "matching"
    if has_fill_blank:
        return "fill_in_the_blank"
    if has_options:
        return "mcq"
    return "open_ended"

#----------- Question Parsing Helpers -------------

def split_question_groups(lines):
    """Split at each numbered question/sub-question; keep its instructions and options attached."""
    groups, current = [], []

    for line in lines:
        top_level_match = top_level_with_part_pattern.match(line)
        standalone_parenthesized = parenthesized_question_pattern.match(line)
        standalone_numbered = numbered_question_pattern.match(line)
        spaced_numbered = spaced_question_pattern.match(line)

        # A line like "١ (١) ..." starts a new main question.
        # A line like "(٢) ..." starts a separate sub-question, not a new section.
        starts_new = bool(top_level_match or standalone_parenthesized or standalone_numbered or spaced_numbered)

        if starts_new:
            if current:
                groups.append(current)
            current = [line]
        elif current:
            current.append(line)
        elif line.strip():
            # Keep section instructions / context with the first question.
            current.append(line)

    if current:
        groups.append(current)
    return groups

#----------- Extract Learning Objectives -------------

def extract_objectives(block, page, chunks):
    if block["lines"]:
        chunks.append(make_chunk(page, "\n".join(block["lines"]), "learning_objective", len(chunks) + 1))

#----------- Extract Questions -------------

def extract_question_chunks(block, page, chunks, continued_from=None):
    section_name = normalize_heading(block["heading"]) if block["heading"] else None
    groups = split_question_groups(block["lines"])

    # A very short fragment (e.g. a stray answer line) is attached to the
    # previous group instead of being dropped (it used to be discarded).
    merged = []
    for group in groups:
        if merged and len("\n".join(group).strip()) < 8:
            merged[-1].extend(group)
        else:
            merged.append(group)

    main_number = None
    main_instruction = None
    pending_instruction = None

    for position, group in enumerate(merged):
        text = "\n".join(group).strip()
        if not text:
            continue

        # A main question that is only an instruction, e.g.
        # "١ اختر الإجابة الصحيحة:" followed by "(١) ...", "(٢) ...".
        # It is attached to its first sub-question (text) and stored as
        # question_instruction on every sub-question, instead of becoming
        # a meaningless one-line chunk.
        next_group = merged[position + 1] if position + 1 < len(merged) else None
        main_only = (
            len(group) == 1
            and not top_level_with_part_pattern.match(group[0])
            and (numbered_question_pattern.match(group[0]) or spaced_question_pattern.match(group[0]))
            and next_group is not None
            and parenthesized_question_pattern.match(next_group[0])
        )
        if main_only:
            number_match = numbered_question_pattern.match(group[0]) or spaced_question_pattern.match(group[0])
            main_number = number_match.group(1)
            main_instruction = group[0]
            pending_instruction = group[0]
            continue

        if pending_instruction:
            text = pending_instruction + "\n" + text
            pending_instruction = None

        first = group[0]
        q_number = None
        sub_question_number = None

        top = top_level_with_part_pattern.match(first)
        sub = parenthesized_question_pattern.match(first)
        numbered = numbered_question_pattern.match(first) or spaced_question_pattern.match(first)

        if top:
            main_number = top.group(1)
            main_instruction = None
            q_number, sub_question_number = top.group(1), top.group(2)
        elif sub:
            # "(٢) ..." is a sub-question of the current main question.
            # (Previously its sub-number was stored as the question number.)
            q_number, sub_question_number = main_number, sub.group(1)
        elif numbered:
            main_number = numbered.group(1)
            main_instruction = None
            q_number = numbered.group(1)

        extra = {
            "question_number": q_number,
            "sub_question_number": sub_question_number,
            "question_section": section_name
        }
        if sub and main_instruction:
            extra["question_instruction"] = main_instruction
        if continued_from:
            extra["continued_from_page"] = continued_from

        chunks.append(make_chunk(page, text, classify_question(text), len(chunks) + 1, extra))

#----------- Extract Practical Activities -------------

def detect_activity_components(lines):
    components = []
    for line in lines:
        # Component labels are numbered steps ("١ التحضير:") or short
        # unnumbered labels ("الأدوات المستخدمة", "طريقة الصنع").
        if not (activity_step_pattern.match(line) or len(line) <= 25):
            continue
        for name, pattern in activity_component_labels:
            if re.search(pattern, line) and name not in components:
                components.append(name)
    return components


def split_activity(lines, max_chars=max_activity_chars):
    # Keep the activity whole when possible. Otherwise cut only before a
    # numbered step, so no step is separated from its own instructions.
    if len("\n".join(lines)) <= max_chars:
        return [lines]
    parts, current = [], []
    for line in lines:
        if current and activity_step_pattern.match(line) and len("\n".join(current + [line])) > max_chars:
            parts.append(current)
            current = []
        current.append(line)
    if current:
        parts.append(current)
    return parts


def extract_activities(block, page, chunks, continued_from=None):
    heading = block["heading"]
    activity_lines = ([heading] if heading else []) + block["lines"]
    text = "\n".join(activity_lines).strip()
    if not text:
        return

    title = None
    if heading:
        title = re.sub(r"^(نشاط|هيَّا نتوسَّع|هيا نتوسع|هيَّا نصنعه!?|هيا نصنعه)\s*:?\s*", "", heading).strip() or None
        if title is None and block["lines"]:
            # e.g. "هيَّا نتوسَّع" followed by "لنُربِّي الفراشات بدءًا من البيض!"
            title = block["lines"][0]

    components = detect_activity_components(block["lines"])

    # An activity with an explicit experiment step or an experiment title
    # is classified as an experiment; other activities stay practical.
    is_experiment = "procedure" in components and bool(re.search(r"التجربة", "\n".join(block["lines"]))) \
        or bool(title and re.search(r"تجربة", title))
    chunk_type = "experiment" if is_experiment else "practical_activity"

    parts = split_activity(activity_lines)
    for number, part in enumerate(parts, start=1):
        extra = {
            "activity_title": title,
            "activity_components": components
        }
        if len(parts) > 1:
            extra["part"] = number
            extra["total_parts"] = len(parts)
        if continued_from:
            extra["continued_from_page"] = continued_from
        chunks.append(make_chunk(page, "\n".join(part), chunk_type, len(chunks) + 1, extra))

#----------- Header Detection -------------

def is_metadata_header_only(text, page):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return True
    lesson_title = (page.get("lesson_title") or "").strip()
    for line in lines:
        line = re.sub(r"\[\s*[٠-٩0-9]+\s*\]", "", line).strip()
        if not line:
            continue
        is_lesson_title = bool(lesson_title and line.strip(" | الفصل١٢٣٤٥٦٧٨٩٠-ـ") == lesson_title)
        is_chapter_header = bool(re.search(r"الفصل\s*[١-٩0-9]", line))
        is_lesson_code_header = bool(re.match(r"^[١-٩0-9]\s*[-ـ]\s*[١-٩0-9]+\s+", line))
        if not (is_lesson_title or is_chapter_header or is_lesson_code_header):
            return False
    return True

#----------- Extract Explanation Chunks -------------

def extract_explanation_chunks(block, page, chunks):
    lines = ([block["heading"]] if block["heading"] else []) + block["lines"]
    for part in split_long_text(lines):
        # Previously, parts shorter than 20 characters were silently
        # dropped. They are now kept (validation reports them as short).
        if part.strip() and not is_metadata_header_only(part, page):
            chunks.append(make_chunk(page, part, "explanation", len(chunks) + 1))


def is_procedure_block(block):
    # "هيَّا نتوسَّع" / "هيَّا نصنعه!" blocks that contain at least two
    # numbered steps are hands-on activities; otherwise they are reading.
    steps = [line for line in block["lines"] if activity_step_pattern.match(line)]
    return len(steps) >= 2 and not matches_heading(block["heading"] or "", ["ركن إثرائي", "هيَّا نُراجع", "هيا نراجع"])

#----------- Segment Page Into Blocks -------------

def block_kind(line):
    if is_objective_heading(line):
        return "objectives"
    if is_question_section_heading(line):
        return "questions"
    if is_activity_heading(line):
        return "activity"
    if is_learn_heading(line):
        return "explanation"
    if is_enrichment_heading(line):
        return "enrichment"
    return None


def segment_page(lines, carry_over=None):
    """Split a page into blocks in reading order.

    Each block runs from its heading to the next block heading. This
    replaces the previous four independent passes, in which the
    explanation pass set a skip flag at the first activity/question
    heading and never reset it, and activities ran past the following
    "تعلَّم" explanation.
    """
    blocks = []
    if carry_over:
        # The page continues an activity/question block from the previous page.
        current = {"kind": carry_over["kind"], "heading": None, "lines": [], "continued": True}
    else:
        current = {"kind": "explanation", "heading": None, "lines": [], "continued": False}

    for line in lines:
        kind = block_kind(line)
        if kind:
            if current["lines"] or current["heading"]:
                blocks.append(current)
            current = {"kind": kind, "heading": line, "lines": [], "continued": False}
        else:
            current["lines"].append(line)

    if current["lines"] or current["heading"]:
        blocks.append(current)
    return blocks


def clean_page_lines(lines):
    cleaned = []
    for position, line in enumerate(lines):
        # Running headers only appear in the first lines of a page.
        if position < 3 and any(pattern.match(line) for pattern in running_header_patterns):
            continue
        if badge_pattern.match(line):
            continue
        cleaned.append(line)
    return cleaned

#----------- Build Chunks -------------

chunks = []
carry_over = None
previous_page = None

for page in pages:
    page_text = page.get("processed_content") or ""
    if not page.get("include_in_rag", True) or not page_text.strip():
        carry_over = None
        previous_page = None
        continue

    # Only continue a block across pages inside the same lesson/section.
    same_section = previous_page is not None and (
        previous_page["pdf_page_index"] + 1 == page["pdf_page_index"]
        and previous_page.get("unit_id") == page.get("unit_id")
        and previous_page.get("lesson_id") == page.get("lesson_id")
        and previous_page.get("section_type") == page.get("section_type")
    )

    lines = clean_page_lines(normalize_lines(page_text))
    blocks = segment_page(lines, carry_over if same_section else None)
    page_chunks = []

    for block in blocks:
        continued_from = previous_page["pdf_page_index"] if block.get("continued") else None

        if block["kind"] == "objectives":
            extract_objectives(block, page, page_chunks)
        elif block["kind"] == "questions":
            extract_question_chunks(block, page, page_chunks, continued_from)
        elif block["kind"] == "activity":
            extract_activities(block, page, page_chunks, continued_from)
        elif block["kind"] == "enrichment" and is_procedure_block(block):
            extract_activities(block, page, page_chunks)
        else:
            extract_explanation_chunks(block, page, page_chunks)

    # A page that ends inside an activity may continue on the next page
    # (which then starts without a heading). Question pages always print
    # their own "حاول" / "تدرَّب" heading in both Science books, so question
    # blocks are not carried over (doing so mislabelled the untitled
    # seed-picture page 46 of Primary 5 as a question).
    last_block = blocks[-1] if blocks else None
    carry_over = (
        {"kind": last_block["kind"]}
        if last_block and last_block["kind"] == "activity"
        else None
    )
    previous_page = page
    chunks.extend(page_chunks)

#----------- Save Chunks JSON -------------

output_dir = BASE_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "chunks.json"
output_file.write_text(json.dumps(chunks, ensure_ascii=False, indent=4), encoding="utf-8")

#----------- Print Chunking Results -------------

counts = Counter(chunk["metadata"]["chunk_type"] for chunk in chunks)
print("Learning pages:", sum(1 for page in pages if page.get("include_in_rag", True)))
print("Total chunks:", len(chunks))
print("\nChunks by type:")
for chunk_type, count in sorted(counts.items()):
    print(f"{chunk_type}: {count}")
print("\nOutput saved successfully!")
print("Output file:", output_file)

#----------- Inspect Chunks -------------

for chunk in chunks[:5]:
    print("\n" + "=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Type:", chunk["metadata"]["chunk_type"])
    print("Page:", chunk["metadata"]["pdf_page_index"])
    print("Text:")
    print(chunk["text"])
