from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .embeddings import HashingEmbedder, cosine_similarity


class SQLiteVectorStore:
    def __init__(self, path: Path, embedder: HashingEmbedder | None = None) -> None:
        self.path = path
        self.embedder = embedder or HashingEmbedder()

    def rebuild(self, chunks: list[dict], curriculum_hash: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.executescript(
                """
                DROP TABLE IF EXISTS chunks;
                DROP TABLE IF EXISTS metadata;
                CREATE TABLE chunks (
                    id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL, subject TEXT NOT NULL,
                    title_ar TEXT NOT NULL, kind TEXT NOT NULL, text_ar TEXT NOT NULL,
                    source_file TEXT NOT NULL, pages_json TEXT NOT NULL,
                    review_status TEXT NOT NULL, embedding_json TEXT NOT NULL
                );
                CREATE INDEX idx_chunks_subject ON chunks(subject);
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                """
            )
            for chunk in chunks:
                connection.execute(
                    "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        chunk["id"], chunk["lesson_id"], chunk["subject"], chunk["title_ar"],
                        chunk["kind"], chunk["text_ar"], chunk["source_file"],
                        json.dumps(chunk["pages"]), chunk["review_status"],
                        json.dumps(self.embedder.embed(chunk["text_ar"])),
                    ),
                )
            connection.execute("INSERT INTO metadata VALUES ('curriculum_hash', ?)", (curriculum_hash,))

    def indexed_hash(self) -> str | None:
        if not self.path.exists():
            return None
        try:
            with sqlite3.connect(self.path) as connection:
                row = connection.execute("SELECT value FROM metadata WHERE key='curriculum_hash'").fetchone()
                return row[0] if row else None
        except sqlite3.DatabaseError:
            return None

    def search(self, query: str, subject: str, limit: int = 3) -> list[dict]:
        query_vector = self.embedder.embed(query)
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT * FROM chunks WHERE subject = ?", (subject,)).fetchall()
        scored = []
        for row in rows:
            item = dict(row)
            item["pages"] = json.loads(item.pop("pages_json"))
            item["score"] = round(cosine_similarity(query_vector, json.loads(item.pop("embedding_json"))), 4)
            scored.append(item)
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]

