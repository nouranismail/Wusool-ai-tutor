import re

DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670]")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def clean_text(text):
    """Make common Arabic spelling variants easier for the model to match."""
    text = DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = re.sub("[إأآٱ]", "ا", text)
    text = text.replace("ى", "ي").translate(ARABIC_DIGITS)
    return " ".join(text.split())


def expand_query(question):
    """Add textbook wording for a router question that is often phrased briefly."""
    normalized = clean_text(question)
    if "راوتر" in normalized or "جهاز التوجيه" in normalized:
        return f"{question} ربط الأجهزة بمزود خدمة الإنترنت"
    return question


def is_title_only(chunk):
    """Skip short explanation chunks that only repeat a section title."""
    text = clean_text(chunk["text"])
    if chunk.get("chunk_type") != "explanation" or len(text) >= 80:
        return False
    titles = [chunk.get(key) for key in ("unit_title", "lesson_title", "section_title")]
    return text.startswith("الدرس") or text in [clean_text(title) for title in titles if title]


def passage_for_embedding(chunk):
    """Add book context so a short passage has a little more meaning."""
    labels = [f"{chunk['subject']} Grade {chunk['grade']}"]
    for key in ("unit_title", "lesson_title", "section_title"):
        if chunk.get(key) and chunk[key] not in labels:
            labels.append(chunk[key])
    return " | ".join(labels) + "\n" + chunk["text"]
