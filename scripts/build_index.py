from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.rag.retriever import CurriculumRetriever


retriever = CurriculumRetriever(
    ROOT / "data" / "reviewed" / "curriculum.json",
    ROOT / "data" / "vector_db" / "curriculum.sqlite3",
)
retriever.ensure_index()
print(f"Built vector index at {retriever.store.path}")
