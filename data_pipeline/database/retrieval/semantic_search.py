"""
Basic semantic search example. `search_text` encodes a question with the same
model used for the stored chunk vectors (E5 models need the "query: " prefix,
while stored chunks use "passage: "). `search` accepts a ready-made vector.

The distance expression casts the dimensionless column to vector(EMBEDDING_DIM)
so PostgreSQL can use the HNSW expression index described in the README.
Set EMBEDDING_DIM in .env to match the model (768 for multilingual-e5-base).
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pgvector.psycopg import register_vector
from config import EMBEDDING_DIM
from db import connect

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
_encoder = None

def encode_query(text, model_name=DEFAULT_MODEL):
    """Return a normalized query vector using the E5 "query: " prefix."""
    global _encoder
    if _encoder is None or _encoder[0] != model_name:
        from sentence_transformers import SentenceTransformer
        _encoder = (model_name, SentenceTransformer(model_name))
    return _encoder[1].encode("query: " + text, normalize_embeddings=True)

def search_text(question, model_name=DEFAULT_MODEL, **kwargs):
    """Encode `question` and run `search` (limit/subject/grade via kwargs)."""
    return search(encode_query(question, model_name), model_name, **kwargs)

def search(query_vector, model_name, limit=5, subject=None, grade=None):
    dim = int(EMBEDDING_DIM)  # validated int, safe to inline (type modifiers can't be parameters)
    if len(query_vector) != dim:
        raise ValueError(
            f"Query vector has {len(query_vector)} dims but EMBEDDING_DIM={dim}. "
            "Set EMBEDDING_DIM in .env to the model's output size."
        )
    dist = f"(e.embedding::vector({dim})) <=> %s"
    sql = f"""
        SELECT c.chunk_id, c.content, t.book_id, p.printed_page_number,
               c.unit_title, c.lesson_title,
               {dist} AS distance
        FROM chunk_embeddings e
        JOIN chunks c ON c.id=e.chunk_id
        JOIN textbooks t ON t.id=c.textbook_id
        JOIN pages p ON p.id=c.page_id
        WHERE e.embedding_model=%s AND p.include_in_rag=TRUE
    """
    params = [query_vector, model_name]
    if subject:
        sql += " AND t.subject=%s"
        params.append(subject)
    if grade:
        sql += " AND t.grade=%s"
        params.append(grade)
    sql += f" ORDER BY {dist} LIMIT %s"
    params.extend([query_vector, limit])

    with connect() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
