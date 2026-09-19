from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .chunking import lesson_chunks
from .vector_store import SQLiteVectorStore


class CurriculumRetriever:
    def __init__(self, curriculum_path: Path, index_path: Path) -> None:
        self.curriculum_path = curriculum_path
        self.store = SQLiteVectorStore(index_path)

    def _source_hash(self) -> str:
        return hashlib.sha256(self.curriculum_path.read_bytes()).hexdigest()

    def ensure_index(self) -> None:
        source_hash = self._source_hash()
        if self.store.indexed_hash() == source_hash:
            return
        lessons = json.loads(self.curriculum_path.read_text(encoding="utf-8"))
        chunks = [chunk for lesson in lessons for chunk in lesson_chunks(lesson)]
        self.store.rebuild(chunks, source_hash)

    def search(self, query: str, subject: str, limit: int = 3) -> list[dict]:
        self.ensure_index()
        return self.store.search(query, subject, limit)

