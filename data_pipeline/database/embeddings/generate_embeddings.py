"""
Embedding generation scaffold.
Choose/benchmark the model first. This example uses multilingual-e5-base.
The pgvector column is dimensionless in schema.sql; after selecting a model,
you may optionally add a dimension-specific ANN index.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector
from db import connect

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

def main():
    model = SentenceTransformer(MODEL_NAME)
    with connect() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.chunk_id, c.content
                FROM chunks c
                WHERE NOT EXISTS (
                    SELECT 1 FROM chunk_embeddings e
                    WHERE e.chunk_id=c.id AND e.embedding_model=%s
                )
                ORDER BY c.id
            """, (MODEL_NAME,))
            rows = cur.fetchall()
        # End the implicit transaction opened by the SELECT. Without this,
        # conn.transaction() below becomes a savepoint and nothing is committed
        # until the script exits, so a crash would lose every embedding.
        conn.commit()

        for start in range(0, len(rows), BATCH_SIZE):
            batch = rows[start:start+BATCH_SIZE]
            texts = ["passage: " + row[2] for row in batch]
            vectors = model.encode(texts, normalize_embeddings=True)
            with conn.transaction():
                with conn.cursor() as cur:
                    for row, vector in zip(batch, vectors):
                        cur.execute("""
                            INSERT INTO chunk_embeddings
                                (chunk_id, embedding_model, embedding)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (chunk_id, embedding_model)
                            DO UPDATE SET embedding=EXCLUDED.embedding,
                                          created_at=CURRENT_TIMESTAMP
                        """, (row[0], MODEL_NAME, vector))
            print(f"Embedded {min(start+BATCH_SIZE, len(rows))}/{len(rows)}")

if __name__ == "__main__":
    main()
