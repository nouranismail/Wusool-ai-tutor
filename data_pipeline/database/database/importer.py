import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from psycopg.types.json import Jsonb

from config import TEXTBOOKS_DIR
from db import connect

EXPECTED_BOOKS = {
    "English_Prim4_TR1", "English_Prim5_TR1",
    "ICT_ARABIC_Prim4_TR1", "ICT_ARABIC_Prim5_TR1",
    "Science_ARABIC_Prim4_TR1", "Science_ARABIC_Prim5_TR1",
}

def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def require_list(data, label, path):
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array for {label}")
    return data

def insert_book(cur, book_id, pages):
    if not pages:
        raise ValueError(f"{book_id}: pages.json is empty")
    first = pages[0]
    subject = first.get("subject") or "Unknown"
    grade = int(first.get("grade") or 0)
    term = int(first.get("term") or 1)
    language = first.get("language") or "unknown"
    title = book_id.replace("_", " ")

    cur.execute("""
        INSERT INTO textbooks (book_id, title, subject, grade, term, language)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (book_id) DO UPDATE SET
            title=EXCLUDED.title, subject=EXCLUDED.subject,
            grade=EXCLUDED.grade, term=EXCLUDED.term,
            language=EXCLUDED.language
        RETURNING id
    """, (book_id, title, subject, grade, term, language))
    textbook_pk = cur.fetchone()[0]

    # Re-import is deterministic: remove this book's old pages; cascading FKs
    # remove its old chunks and embeddings, then insert the current JSON snapshot.
    cur.execute("DELETE FROM pages WHERE textbook_id = %s", (textbook_pk,))

    page_map = {}
    for page in pages:
        page_idx = page.get("pdf_page_index")
        if page_idx is None:
            raise ValueError(f"{book_id}: page without pdf_page_index")
        if page_idx in page_map:
            raise ValueError(f"{book_id}: duplicate page index {page_idx}")

        cur.execute("""
            INSERT INTO pages (
                textbook_id, pdf_page_index, printed_page_number,
                page_type, include_in_rag, exclusion_reason,
                unit_id, unit_title, lesson_id, lesson_title,
                section_type, section_title, unit_type,
                raw_content, processed_content,
                ocr_uncertain_readings, source_metadata
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            ) RETURNING id
        """, (
            textbook_pk, page_idx, page.get("printed_page_number"),
            page.get("page_type"),
            bool(page.get("include_in_rag", True)),
            page.get("exclusion_reason"),
            str(page["unit_id"]) if page.get("unit_id") is not None else None,
            page.get("unit_title"),
            str(page["lesson_id"]) if page.get("lesson_id") is not None else None,
            page.get("lesson_title"),
            page.get("section_type"), page.get("section_title"),
            page.get("unit_type"), page.get("raw_content"),
            page.get("processed_content"),
            Jsonb(page.get("ocr_uncertain_readings"))
                if page.get("ocr_uncertain_readings") is not None else None,
            Jsonb(page)
        ))
        page_map[page_idx] = cur.fetchone()[0]

    return textbook_pk, page_map

def import_one(conn, folder):
    book_id = folder.name
    output_dir = folder / "output"
    pages_path, chunks_path = output_dir / "pages.json", output_dir / "chunks.json"
    if not pages_path.is_file() or not chunks_path.is_file():
        raise FileNotFoundError(f"{book_id}: missing output/pages.json or chunks.json")

    pages = require_list(read_json(pages_path), "pages", pages_path)
    chunks = require_list(read_json(chunks_path), "chunks", chunks_path)

    seen_chunk_ids = set()
    with conn.transaction():
        with conn.cursor() as cur:
            textbook_pk, page_map = insert_book(cur, book_id, pages)
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id")
                content = chunk.get("text")
                metadata = chunk.get("metadata") or {}
                if not chunk_id or not isinstance(content, str) or not content.strip():
                    raise ValueError(f"{book_id}: chunk missing chunk_id or non-empty text")
                if chunk_id in seen_chunk_ids:
                    raise ValueError(f"{book_id}: duplicate chunk_id {chunk_id}")
                seen_chunk_ids.add(chunk_id)

                # The corpus uses metadata.pdf_page_index; fail loudly rather than
                # guessing a page association if the metadata is incomplete.
                page_idx = metadata.get("pdf_page_index")
                if page_idx not in page_map:
                    raise ValueError(
                        f"{book_id}: chunk {chunk_id} references unknown "
                        f"pdf_page_index={page_idx}"
                    )
                if metadata.get("book_id") not in (None, book_id):
                    raise ValueError(f"{chunk_id}: metadata book_id mismatch")

                cur.execute("""
                    INSERT INTO chunks (
                        chunk_id, textbook_id, page_id, content, chunk_type,
                        unit_id, unit_title, lesson_id, lesson_title,
                        section_type, section_title, pdf_page_index,
                        printed_page_number, metadata
                    ) VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                """, (
                    chunk_id, textbook_pk, page_map[page_idx], content,
                    metadata.get("chunk_type"),
                    str(metadata["unit_id"]) if metadata.get("unit_id") is not None else None,
                    metadata.get("unit_title"),
                    str(metadata["lesson_id"]) if metadata.get("lesson_id") is not None else None,
                    metadata.get("lesson_title"),
                    metadata.get("section_type"), metadata.get("section_title"),
                    page_idx, metadata.get("printed_page_number"), Jsonb(metadata)
                ))

    return len(pages), len(chunks)

def main():
    if not TEXTBOOKS_DIR.is_dir():
        raise FileNotFoundError(f"Textbooks directory not found: {TEXTBOOKS_DIR}")
    folders = sorted(
        p for p in TEXTBOOKS_DIR.iterdir()
        if p.is_dir() and (p / "output").is_dir()
    )
    found = {p.name for p in folders}
    missing = EXPECTED_BOOKS - found
    if missing:
        raise RuntimeError(f"Missing expected textbook folders: {sorted(missing)}")

    totals = [0, 0]
    with connect() as conn:
        for folder in folders:
            page_count, chunk_count = import_one(conn, folder)
            totals[0] += page_count
            totals[1] += chunk_count
            print(f"Imported {folder.name}: {page_count} pages, {chunk_count} chunks")
    print(f"Done. Total: {len(folders)} books, {totals[0]} pages, {totals[1]} chunks")

if __name__ == "__main__":
    main()
