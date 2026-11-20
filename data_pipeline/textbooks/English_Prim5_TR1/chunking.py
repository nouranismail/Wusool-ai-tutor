from pathlib import Path
import re
import sys
import json
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent

# Force UTF-8 console output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")



#----------- Read Pages JSON -------------

input_file = BASE_DIR / "output" / "pages.json"

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

max_chunk_chars = 1500
max_glossary_chars = 900


#----------- Text Patterns -------------

instruction_verbs = {
    "Read", "Listen", "Look", "Work", "Choose", "Think", "Write", "Complete",
    "Ask", "Match", "Make", "Fill", "Find", "Prepare", "Give", "Exchange",
    "Discuss", "Answer", "Circle", "Re-write", "Rewrite", "Put", "Create",
    "Draw", "Crack", "Imagine", "Sort", "Number", "Correct", "Order", "Say",
    "Underline", "Check", "Role-play", "Talk", "Tell", "Share", "Present",
    "Solve", "Use", "Describe", "Search", "Plan", "Design", "Rate"
}

exercise_pattern = re.compile(r"^(\d{1,2})\s+(\S.*)$")

# Running headers / section labels printed at the top of a page.
structural_header_pattern = re.compile(
    r"^(?:(?:Unit|Lesson|Review)\s+\d+|Story|Glossary|Quick Review|Self\s*-\s*Assessment)$",
    re.IGNORECASE
)

# Box headings that start a new block anywhere on a page.
box_headings = {
    "learning outcomes": "objectives",
    "language in use": "grammar",
    "tip": "tip",
    "tip!": "tip",
    "learn!": "tip",
    "think": "think",
    "now i can ...": "self_assessment",
    "now i can...": "self_assessment",
    "now i can": "self_assessment"
}

# Story-unit headings. They are only headings OUTSIDE an exercise
# (e.g. "Characters" is also a row label inside a chart exercise).
story_headings = {
    "story vocabulary": "vocabulary",
    "vocabulary": "vocabulary",
    "definitions": "vocabulary",
    "characters": "characters"
}

# Answer options: "a. room   b. garden" (inline) or one per line.
option_pattern = re.compile(r"(?:^|\s)[a-dA-D][.)]\s")

# Dialogue turn: "Ms. Mona: Good morning ..." / "Sami: I can hear ..."
speaker_pattern = re.compile(r"^[A-Z][A-Za-z.' ]{1,20}:\s+\S")

# A line that only describes a picture/visual, e.g. "[Four pictures]".
visual_note_pattern = re.compile(r"^\[[^\]]+\]$")

# Section codes used in chunk IDs for pages that are not numbered lessons.
section_codes = {
    "unit_opener": "OPEN",
    "quick_review": "QR",
    "self_assessment": "SA",
    "review": "REV",
    "story": "STORY",
    "glossary": "GLO"
}


#----------- Text Helpers -------------

def normalize_lines(text):

    # Keep every non-empty line. Inner spacing is preserved because it
    # separates inline answer options and matching columns.
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def simplify(text):

    return re.sub(r"[^a-z0-9]+", "", text.lower())


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
        chunk["metadata"].update(
            {key: value for key, value in extra_metadata.items() if value is not None}
        )

    return chunk


def is_title_line(line):

    # A short heading such as "My Healthy Day" or "Four Amazing Jobs",
    # not a sentence such as "Ahmed and Laila are talking about ...".
    return (
        len(line) <= 60
        and not re.search(r"[.:,]$", line)
        and not visual_note_pattern.match(line)
        and not re.match(r"^[•\-–·*]", line)        # bullet items
        and not re.fullmatch(r"[\d,.\s]+", line)      # bare numbers
    )


def is_title_part(line, page):

    # A header line that is (part of) the lesson / unit / section title,
    # e.g. "Story Time" + "Goha's Great Meal" for "Story Time: Goha's Great Meal".
    key = simplify(line)

    if len(key) < 4:
        return False

    titles = [
        page.get("lesson_title"),
        page.get("unit_title"),
        page.get("section_title")
    ]

    return any(title and key in simplify(title) for title in titles)


#----------- Header Zone -------------

def split_header_zone(lines, page):

    """Remove running headers at the top of a page.

    Returns (labels, body). Structural headers ("Unit 1", "Lesson 2",
    "Story") and lines that repeat the lesson/unit title are dropped (they
    are in the metadata). Other short label lines before the first content
    line (e.g. "Pronunciation", "Where Life Flows", "By: Eleanor Estes")
    are returned as labels so they can be kept with the page content.
    """

    labels = []
    index = 0

    for index, line in enumerate(lines):

        if structural_header_pattern.match(line):
            continue

        # Content starts are checked before title parts: "Learning Outcomes"
        # is also part of the opener's section title but must be kept.
        if (
            exercise_pattern.match(line)
            or line.lower().rstrip(":") in box_headings
            or line.lower() in story_headings
            or line.startswith("|")
            or len(line) > 60
        ):
            return labels, lines[index:]

        if is_title_part(line, page):
            continue

        # Only title-like lines can be labels. List items ("A. Choose ...",
        # "1. ...") and sentences are page content (e.g. a page that
        # continues an exercise from the previous page).
        if not is_title_line(line) or re.match(r"^([A-Da-d]|\d+)[.)]\s", line):
            return labels, lines[index:]

        labels.append(line)

        # At most two label lines; anything more is page content.
        if len(labels) >= 2:
            return labels, lines[index + 1:]

    else:
        return labels, []


#----------- Exercise Detection -------------

def exercise_start(line, expected_number, exercises_on_page, exercises_in_section=1):

    """Return (number, note) if the line starts an exercise, else None.

    note is None for a normally numbered exercise, otherwise it explains a
    numbering irregularity that exists in the printed book.
    """

    match = exercise_pattern.match(line)

    if not match:
        return None

    number = int(match.group(1))
    rest = match.group(2).strip()
    words = rest.split()
    first_word = re.sub(r"[^A-Za-z-]", "", words[0])

    later_words = {re.sub(r"[^A-Za-z-]", "", word).capitalize() for word in words[1:]}

    looks_like_instruction = first_word in instruction_verbs or (
        not option_pattern.search(rest)
        and (
            # Question-style instructions: "Who said this: ...?",
            # "Do you agree with the action? Why or why not?"
            "?" in rest
            # An imperative later in the line: "You are Wanda. Write back ...",
            # "Now, work in groups ...", "When you make a flyer, make sure to ..."
            or bool(later_words & instruction_verbs)
            # Section-style header: "5 Group discussion."
            or "discussion" in rest.lower()
        )
    )
    # Statements such as "3 An image is a photo or drawing." (a list item)
    # match none of the above and are not exercise headers.

    if not looks_like_instruction:
        return None

    if number == expected_number:
        return number, None

    strong = first_word in instruction_verbs

    # A sub-section (e.g. "Pronunciation") may restart numbering at 1.
    if number == 1 and not exercises_on_page and strong:
        return number, None

    # Printing errors in the book are tolerated for clear instructions only:
    # the first exercise of a section may carry another number, and a number
    # may be printed twice (English P4 p.83 numbers two exercises "2").
    if strong and exercises_in_section == 0:
        return number, f"first exercise of the section is numbered {number} in the book"

    if strong and number == expected_number - 1:
        return number, f"exercise number {number} is printed twice in the book"

    return None


#----------- Segment Page Into Blocks -------------

def segment_page(lines, state):

    """Split page lines into blocks in reading order.

    Block kinds: exercise, objectives, grammar, tip, think,
    self_assessment, vocabulary, characters, glossary, prose.
    `state` carries the expected exercise number across pages of the same
    lesson/section.
    """

    blocks = []
    current = {"kind": "prose", "heading": None, "lines": [], "number": None}
    exercises_on_page = 0

    def push():
        if current["lines"] or current["heading"]:
            blocks.append(current)

    for line in lines:

        detected = exercise_start(line, state["expected"], exercises_on_page, state["count"])

        if detected is not None:
            number, note = detected
            push()
            current = {"kind": "exercise", "heading": line, "lines": [], "number": number, "note": note}
            state["expected"] = number + 1
            state["count"] += 1
            exercises_on_page += 1
            continue

        key = line.lower().rstrip(":").strip()

        if key in box_headings:
            push()
            current = {"kind": box_headings[key], "heading": line, "lines": [], "number": None}
            continue

        if key in story_headings and current["kind"] != "exercise":
            push()
            current = {"kind": story_headings[key], "heading": line, "lines": [], "number": None}
            continue

        if line.startswith("|") and current["kind"] == "prose" and not current["lines"]:
            current["kind"] = "glossary" if state["section_type"] == "glossary" else "prose"

        current["lines"].append(line)

    push()

    return blocks


#----------- Exercise Classification -------------

def count_options(text):

    return len(option_pattern.findall(text))


def classify_exercise(instruction, body_lines):

    """Classify an exercise from its instruction (and body as fallback)."""

    instr = instruction.lower()
    body = "\n".join(body_lines)

    # Explanations and vocabulary presented as numbered steps.
    if re.search(r"read and learn", instr):
        return "explanation"

    if "listen" in instr and "repeat" in instr:
        return "vocabulary"

    # Puzzles, rating tasks and peer-review checklists.
    if re.search(r"find and circle|give your feedback|crack the code|check \(.\) these points", instr):
        return "practical_activity"

    kinds = instruction_kinds(instr, body)

    # Lettered sub-instructions in the body ("A. Choose the correct answer",
    # "B. Answer the following questions") are separate tasks. Only this
    # evidence of different tasks produces a mixed_question.
    for line in body_lines:
        sub = re.match(r"^[A-D]\.\s+((?:Choose|Answer|Write|Complete|Match|Read|Circle|Fill|Put)\b.*)$", line)
        if sub:
            kinds |= instruction_kinds(sub.group(1).lower(), "")

    # Options in the body decide only when the instruction says nothing
    # (items labelled "a." "b." also appear in T/F and matching tasks).
    if not kinds and count_options(body) >= 2:
        kinds.add("mcq")

    activity_cue = re.search(
        r"work (in|with)|ask and answer|role-?play|prepare|present|make (a|an|your)\b|"
        r"create|draw|collage|poster|flyer|leaflet|exchange|share|take turns|"
        r"in pairs|in groups|origami|research",
        instr
    )

    if activity_cue and kinds <= {"open_ended"}:
        return "practical_activity"

    if len(kinds) >= 2:
        return "mixed_question"

    if kinds:
        return kinds.pop()

    if re.search(r"\.{4,}|_{3,}", body):
        return "fill_in_the_blank"

    return "open_ended"


def instruction_kinds(instr, body):

    """Question types named by one instruction (lower-case text).

    Concrete task types (true/false, MCQ, matching, fill-in) take
    precedence. Words such as "answer", "think" or a question word only
    make a task open-ended when no concrete type is named, e.g.
    "check (✔) the best answer" is an MCQ and "Answer with T (True) or
    F (False)" is a true/false task.
    """

    kinds = set()

    if re.search(r"true\W.*false|\bt\b\s*\(true\)|true or false", instr):
        kinds.add("true_false")

    # "Choose/circle the correct ...", "Read and circle", "check (✔)".
    # A bare "Look, choose, and write" is a writing task, not an MCQ.
    if re.search(r"(choose|circle) the (correct|right|best)|read and circle|"
                 r"listen and circle|\bcheck\b\s*\(|choose the|circle\. what", instr):
        kinds.add("mcq")

    # Matching includes numbering pictures and "Who said this?" tasks.
    if re.search(r"\bmatch\b|\bnumber\b|who said", instr):
        kinds.add("matching")

    if re.search(r"complete|fill|missing|correct form|correct the|between brackets|"
                 r"put the words|\border\b|\bsort\b|re-?write|negative form", instr):
        kinds.add("fill_in_the_blank")

    if kinds:
        return kinds

    if re.search(r"\banswers?\b|discuss|\bthink\b|\bwhy\b|describe|\btell\b|explain|"
                 r"\bwhat\b|\bhow\b|\?", instr):
        kinds.add("open_ended")

    elif re.search(r"\bwrite\b", instr):
        # Short numbered blanks next to pictures ("1 ......   2 ......") are
        # labelling (fill-in); long writing lines are open writing.
        short_blanks = re.search(r"(?<!\.)\.{4,30}(?!\.)", body)
        writing_lines = re.search(r"\.{40,}", body)
        kinds.add("fill_in_the_blank" if short_blanks and not writing_lines and "?" not in body
                  else "open_ended")

    return kinds


def reading_type(instruction, body_lines):

    """Return 'dialogue' / 'reading_passage' for read-only exercises, else None."""

    instr = instruction.lower()

    is_reading = re.search(
        r"listen and read|read and listen|^read\.?$|read the (text|story|dialog|"
        r"conversation|passage|blog|diary|letter|recipe|poem)",
        instr
    )

    # "Read the text again. Who said these sentences?" asks a question.
    asks_questions = re.search(r"answer|choose|complete|match|true|circle|write|discuss|\?", instr)

    if not is_reading or asks_questions:
        return None

    speaker_lines = sum(1 for line in body_lines if speaker_pattern.match(line))

    if speaker_lines >= 3:
        return "dialogue"

    if sum(len(line) for line in body_lines) >= 200:
        return "reading_passage"

    return None


def is_prompted_reading(instruction, body_lines):

    # "Read the text. How do vets and forest officers help animals?" is a
    # reading text with a pre-reading prompt: a reading instruction, a long
    # text and no numbered question items.
    instr = instruction.lower()
    numbered_items = sum(1 for line in body_lines if re.match(r"^\d+[.)]?\s", line))

    return bool(
        re.match(r"(listen and )?read the (text|story)|listen and read", instr)
        and not re.search(r"answer|choose|complete|match|true|circle|write|discuss", instr)
        and numbered_items == 0
        and sum(len(line) for line in body_lines) >= 400
    )


def split_embedded_passage(body_lines):

    """Find a titled reading text placed inside a non-reading exercise.

    Example (Primary 5, p.11): exercise "1 Read and check" lists options,
    then the text "Animals in the Desert / The desert is hot ..." follows
    before exercise 2. Returns (exercise_lines, passage_lines, rest_lines):
    the passage is its title plus the paragraph lines after it; anything
    after the paragraphs (e.g. the "Fiction" / "Plot" boxes on Primary 5
    p.52) is returned separately so it is not merged into the text.
    """

    for index, line in enumerate(body_lines):

        if len(line) < 150:
            continue

        # Walk back over paragraph lines to the passage title.
        title_index = index - 1

        while title_index >= 1 and len(body_lines[title_index]) >= 60:
            title_index -= 1

        if (
            title_index >= 1
            and is_title_line(body_lines[title_index])
            and not body_lines[title_index].endswith("?")
            and not option_pattern.search(body_lines[title_index])
        ):
            end = index

            while end < len(body_lines) and len(body_lines[end]) >= 60:
                end += 1

            return body_lines[:title_index], body_lines[title_index:end], body_lines[end:]

        return body_lines, [], []

    return body_lines, [], []


#----------- Split Long Text -------------

def split_lines(lines, max_chars=max_chunk_chars, boundary=None):

    """Split a list of lines into parts of at most max_chars.

    Cuts happen only before a line accepted by `boundary` (e.g. a new
    numbered item), so a question is never separated from its options.
    """

    if len("\n".join(lines)) <= max_chars:
        return [lines]

    parts, current = [], []

    for line in lines:

        if (
            current
            and len("\n".join(current + [line])) > max_chars
            and (boundary is None or boundary(line))
        ):
            parts.append(current)
            current = []

        current.append(line)

    if current:
        parts.append(current)

    return parts


def is_item_boundary(line):

    # "1. ...", "2 ...", "A. Choose ...", "B. Answer ..."
    return bool(re.match(r"^(\d{1,2}[.)]?\s|[A-D]\.\s)", line))


#----------- Extract Learning Objectives -------------

def extract_objectives(block, page, chunks, prefix):

    lines = prefix + [block["heading"]] + block["lines"]

    chunks.append(
        make_chunk(page, "\n".join(lines), "learning_objective", len(chunks) + 1)
    )


#----------- Extract Exercises -------------

def extract_exercise(block, page, chunks, prefix, continued_from=None):

    heading = block["heading"]
    instruction = (
        exercise_pattern.match(heading).group(2)
        if heading else block.get("instruction", "")
    )

    body_lines = block["lines"]

    # A reading exercise ("Read the text.") keeps its whole text together.
    # Only other exercises can contain a separate embedded reading text.
    if reading_type(instruction, body_lines) or re.search(r"read the (text|story)", instruction.lower()):
        exercise_lines, passage_lines, rest_lines = body_lines, [], []
    else:
        exercise_lines, passage_lines, rest_lines = split_embedded_passage(body_lines)

    chunk_type = reading_type(instruction, exercise_lines) or classify_exercise(instruction, exercise_lines)

    if is_prompted_reading(instruction, exercise_lines):
        speakers = sum(1 for line in exercise_lines if speaker_pattern.match(line))
        chunk_type = "dialogue" if speakers >= 3 else "reading_passage"

    extra = {
        "exercise_number": block["number"],
        "exercise_instruction": instruction,
        "exercise_number_note": block.get("note"),
        "continued_from_page": continued_from
    }

    if chunk_type in {"dialogue", "reading_passage"}:
        title = next((line for line in exercise_lines[:2] if is_title_line(line) and not line.endswith("?")), None)
        extra["passage_title"] = title

    all_lines = prefix + ([heading] if heading else []) + exercise_lines

    boundary = None if chunk_type in {"dialogue", "reading_passage"} else is_item_boundary
    parts = split_lines(all_lines, boundary=boundary)

    for number, part in enumerate(parts, start=1):

        part_extra = dict(extra)

        if len(parts) > 1:
            part_extra["part"] = number
            part_extra["total_parts"] = len(parts)

        chunks.append(
            make_chunk(page, "\n".join(part), chunk_type, len(chunks) + 1, part_extra)
        )

    # A reading text embedded after the exercise items gets its own chunk,
    # and content printed after that text (e.g. a definition box) too.
    if passage_lines:
        extract_prose({"lines": passage_lines}, page, chunks, [], passage=True)

    if rest_lines:
        extract_prose({"lines": rest_lines}, page, chunks, [])


#----------- Extract Boxes -------------

def extract_box(block, page, chunks, prefix):

    lines = prefix + [block["heading"]] + block["lines"]
    text = "\n".join(lines)

    if block["kind"] == "grammar":
        chunk_type, extra = "grammar_explanation", {"box": "Language in use"}

    elif block["kind"] == "tip":
        chunk_type, extra = "explanation", {"box": block["heading"].rstrip("!")}

    elif block["kind"] == "think":
        chunk_type, extra = "open_ended", {"box": "Think", "question_section": "Think"}

    elif block["kind"] == "self_assessment":
        chunk_type, extra = "self_assessment", {}

    elif block["kind"] == "vocabulary":
        chunk_type, extra = "vocabulary", {}

    else:
        # Story characters list.
        chunk_type, extra = "explanation", {"box": block["heading"]}

    for part in split_lines(lines):
        chunks.append(
            make_chunk(page, "\n".join(part), chunk_type, len(chunks) + 1, extra)
        )


#----------- Extract Glossary -------------

def extract_glossary(block, page, chunks):

    # Table rows "| Category | Word | Definition |" are grouped by category.
    header = "| Category | Word | Definition |"
    rows = [
        line for line in block["lines"]
        if line.startswith("|")
        and not re.fullmatch(r"\|[\s|:-]+\|", line)
        and simplify(line) != simplify(header)
    ]
    other_lines = [line for line in block["lines"] if not line.startswith("|")]

    groups = []

    for row in rows:

        category = row.strip("|").split("|")[0].strip()

        if (
            groups
            and groups[-1]["category"] == category
            and len("\n".join(groups[-1]["rows"] + [row])) <= max_glossary_chars
        ):
            groups[-1]["rows"].append(row)
        else:
            groups.append({"category": category, "rows": [row]})

    for group in groups:
        chunks.append(
            make_chunk(
                page,
                "\n".join([header] + group["rows"]),
                "vocabulary",
                len(chunks) + 1,
                {"glossary_category": group["category"]}
            )
        )

    if other_lines:
        extract_prose({"lines": other_lines}, page, chunks, [])


#----------- Extract Explanation Chunks -------------

def extract_prose(block, page, chunks, prefix, passage=False):

    lines = prefix + block["lines"]

    if not lines:
        return

    text_lines = [line for line in lines if not visual_note_pattern.match(line)]
    total_chars = sum(len(line) for line in text_lines)

    if not text_lines:
        # Only picture / template descriptions, e.g. "[Blank leaflet template]".
        chunk_type = "diagram"

    elif passage or page.get("section_type") == "story" or (
        total_chars >= 200 and any(len(line) >= 120 for line in text_lines)
    ):
        chunk_type = "reading_passage"

    elif any(line.startswith("|") for line in lines):
        chunk_type = "table"

    else:
        chunk_type = "explanation"

    extra = {}

    if chunk_type == "reading_passage" and is_title_line(lines[0]):
        extra["passage_title"] = lines[0]

    parts = split_lines(lines)

    for number, part in enumerate(parts, start=1):

        part_extra = dict(extra)

        if len(parts) > 1:
            part_extra["part"] = number
            part_extra["total_parts"] = len(parts)

        chunks.append(
            make_chunk(page, "\n".join(part), chunk_type, len(chunks) + 1, part_extra)
        )


#----------- Classify and Create Chunks -------------

chunks = []
numbering_notes = []

state = {"key": None, "expected": 1, "count": 0, "section_type": None, "last_exercise": None, "last_page": None}

for page in pages:

    page_text = page.get("processed_content") or ""

    if not page_text.strip():
        continue

    # Exercise numbering continues across the pages of one lesson/section.
    section_key = (
        page.get("unit_id"),
        page.get("lesson_id"),
        page.get("section_type"),
        page.get("section_title")
    )

    if section_key != state["key"]:
        state.update({"key": section_key, "expected": 1, "count": 0, "last_exercise": None})

    state["section_type"] = page.get("section_type")

    labels, body = split_header_zone(normalize_lines(page_text), page)
    blocks = segment_page(body, state)

    # A page made only of short label lines (e.g. "My Restaurant Flyer!" +
    # "[Blank space for drawing the flyer]") is still page content.
    if not blocks and labels:
        blocks = [{"kind": "prose", "heading": None, "lines": labels, "number": None}]
        labels = []

    page_chunks = []
    prefix = labels
    only_continuation = False

    for position, block in enumerate(blocks):

        kind = block["kind"]

        # A heading with no content (e.g. "Characters" printed above an
        # exercise) is a label for the next block, not a chunk of its own.
        if kind not in {"exercise", "prose"} and not block["lines"]:
            prefix = prefix + [block["heading"]]
            continue

        # Page-top content that continues the previous page's exercise
        # (same section, no new heading), e.g. a drawing template.
        continued = (
            position == 0
            and kind == "prose"
            and state["last_exercise"] is not None
            and state["last_page"] == page["pdf_page_index"] - 1
        )

        if continued:
            continued_block = dict(state["last_exercise"])
            continued_block["heading"] = None
            continued_block["instruction"] = exercise_pattern.match(
                state["last_exercise"]["heading"]
            ).group(2)
            continued_block["lines"] = block["lines"]
            extract_exercise(continued_block, page, page_chunks, prefix, page["pdf_page_index"] - 1)
            only_continuation = len(blocks) == 1

        elif kind == "exercise":
            extract_exercise(block, page, page_chunks, prefix)

        elif kind == "objectives":
            extract_objectives(block, page, page_chunks, prefix)

        elif kind == "glossary":
            extract_glossary(block, page, page_chunks)

        elif kind == "prose":
            extract_prose(block, page, page_chunks, prefix)

        else:
            extract_box(block, page, page_chunks, prefix)

        # Labels are attached to the first block of the page only.
        prefix = []

    # Remember the last exercise so a following page can continue it.
    # A page that only continues the previous exercise keeps it open.
    last_block = blocks[-1] if blocks else None

    if last_block and last_block["kind"] == "exercise":
        state["last_exercise"] = last_block
    elif not only_continuation:
        state["last_exercise"] = None

    state["last_page"] = page["pdf_page_index"]

    # Page labels (e.g. "Pronunciation") are also stored on every chunk.
    if labels:
        for chunk in page_chunks:
            chunk["metadata"]["page_label"] = " / ".join(labels)

    chunks.extend(page_chunks)


#----------- Save Chunks JSON -------------

output_dir = BASE_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "chunks.json"

output_file.write_text(
    json.dumps(chunks, ensure_ascii=False, indent=4),
    encoding="utf-8"
)


#----------- Chunk Summary -------------

chunk_types = Counter(
    chunk["metadata"]["chunk_type"] for chunk in chunks
)

print("Total pages:", len(pages))
print("Total chunks:", len(chunks))
print("\nChunks by type:")

for chunk_type, count in sorted(chunk_types.items()):
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
