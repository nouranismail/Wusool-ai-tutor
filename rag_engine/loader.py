
import json
from pathlib import Path

from .config import TEXTBOOKS_DIR


def read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def load_chunks(textbooks_dir=TEXTBOOKS_DIR):
    """Return one dictionary per usable chunk from every book folder."""
    textbooks_dir = Path(textbooks_dir)
    if not textbooks_dir.is_dir():
        raise FileNotFoundError(f"Textbooks folder not found: {textbooks_dir}")

    all_chunks = []
    seen_ids = set()
    folders = sorted(path for path in textbooks_dir.iterdir() if (path / "output").is_dir())
    if not folders:
        raise FileNotFoundError(f"No book output folders found in {textbooks_dir}")

    for folder in folders:
        pages = read_json(folder / "output" / "pages.json")
        raw_chunks = read_json(folder / "output" / "chunks.json")
        if not pages:
            raise ValueError(f"{folder.name}: pages.json is empty")

        book_info = pages[0]
        page_map = {page["pdf_page_index"]: page for page in pages}

        for raw in raw_chunks:
            chunk_id = raw.get("chunk_id")
            text = raw.get("text")
            metadata = raw.get("metadata") or {}
            page_index = metadata.get("pdf_page_index")

            if not chunk_id or not isinstance(text, str) or not text.strip():
                raise ValueError(f"{folder.name}: chunk is missing an ID or text")
            if chunk_id in seen_ids:
                raise ValueError(f"Duplicate chunk ID: {chunk_id}")
            if page_index not in page_map:
                raise ValueError(f"{chunk_id}: page {page_index} is missing from pages.json")
            if not page_map[page_index].get("include_in_rag", True):
                continue

            seen_ids.add(chunk_id)
            all_chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "book_id": folder.name,
                "subject": book_info.get("subject", "Unknown"),
                "grade": int(book_info.get("grade", 0)),
                "term": int(book_info.get("term", 1)),
                "language": book_info.get("language", "unknown"),
                "unit_id": str(metadata["unit_id"]) if metadata.get("unit_id") is not None else None,
                "unit_title": metadata.get("unit_title"),
                "lesson_id": str(metadata["lesson_id"]) if metadata.get("lesson_id") is not None else None,
                "lesson_title": metadata.get("lesson_title"),
                "section_title": metadata.get("section_title"),
                "chunk_type": metadata.get("chunk_type"),
                "printed_page_number": metadata.get("printed_page_number"),
                "pdf_page_index": page_index,
                "extra": metadata,
            })

        print(f"Loaded {folder.name}")

    return all_chunks
