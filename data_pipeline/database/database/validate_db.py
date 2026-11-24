import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import connect

QUERIES = {
    "books": "SELECT COUNT(*) FROM textbooks",
    "pages": "SELECT COUNT(*) FROM pages",
    "chunks": "SELECT COUNT(*) FROM chunks",
    "chunks_without_page": """
        SELECT COUNT(*) FROM chunks c
        LEFT JOIN pages p ON p.id=c.page_id WHERE p.id IS NULL
    """,
    "chunks_on_excluded_pages": """
        SELECT COUNT(*) FROM chunks c
        JOIN pages p ON p.id=c.page_id
        WHERE p.include_in_rag=FALSE
    """,
    "duplicate_chunk_ids": """
        SELECT COUNT(*) FROM (
            SELECT chunk_id FROM chunks GROUP BY chunk_id HAVING COUNT(*) > 1
        ) d
    """,
}

def main():
    with connect() as conn, conn.cursor() as cur:
        results = {}
        for name, sql in QUERIES.items():
            cur.execute(sql)
            results[name] = cur.fetchone()[0]
        print("DATABASE VALIDATION")
        for key, value in results.items():
            print(f"{key}: {value}")
        cur.execute("""
            SELECT t.book_id, COUNT(DISTINCT p.id), COUNT(DISTINCT c.id)
            FROM textbooks t
            LEFT JOIN pages p ON p.textbook_id=t.id
            LEFT JOIN chunks c ON c.textbook_id=t.id
            GROUP BY t.book_id ORDER BY t.book_id
        """)
        print("\nPER BOOK")
        for row in cur.fetchall():
            print(f"{row[0]}: {row[1]} pages, {row[2]} chunks")
        # Embeddings are a separate, optional step: report coverage per model
        # and warn (not fail) if a model exists but does not cover every chunk.
        cur.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cur.fetchone()[0]
        cur.execute("""
            SELECT embedding_model, COUNT(*), COUNT(DISTINCT vector_dims(embedding))
            FROM chunk_embeddings GROUP BY embedding_model ORDER BY embedding_model
        """)
        emb_rows = cur.fetchall()
        print("\nEMBEDDINGS")
        if not emb_rows:
            print("none yet (run embeddings/generate_embeddings.py)")
        for model, count, dims in emb_rows:
            print(f"{model}: {count}/{total_chunks} chunks embedded")
            if count < total_chunks:
                print(f"  WARNING: {total_chunks - count} chunks have no embedding for this model")
            if dims != 1:
                print("  WARNING: mixed vector dimensions for this model")
        cur.execute("""
            SELECT COUNT(*) FROM chunk_embeddings e
            JOIN chunks c ON c.id=e.chunk_id
            JOIN pages p ON p.id=c.page_id WHERE p.include_in_rag=FALSE
        """)
        assert cur.fetchone()[0] == 0, "embeddings exist for excluded pages"

        assert results["chunks_without_page"] == 0
        assert results["chunks_on_excluded_pages"] == 0
        assert results["duplicate_chunk_ids"] == 0
        print("\nPASS: relational integrity checks passed.")

if __name__ == "__main__":
    main()
