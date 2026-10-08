import json
from pathlib import Path
from backend.app.rag.chunking import load_all_chunks
from backend.app.rag.embeddings import HashingEmbedder, cosine_similarity

ROOT_DIR = Path(__file__).resolve().parents[3]
STORE_FILE = ROOT_DIR / "backend" / "app" / "rag" / "vector_store.json"


class VectorStore:
    def __init__(self):
        self.embedder = HashingEmbedder()
        self.documents = []
        self.vectors = []
        self.load_or_build()

    def build_and_save(self):
        chunks = load_all_chunks()
        self.documents = chunks
        self.vectors = [self.embedder.embed(c["text_ar"]) for c in chunks]

        # حفظ الفهرس في ملف محلي
        data_to_save = {
            "documents": self.documents,
            "vectors": self.vectors
        }
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        print(f"✅ تم حفظ وفهرسة {len(chunks)} جزء بنجاح في vector_store.json")

    def load_or_build(self):
        if STORE_FILE.exists():
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents = data.get("documents", [])
                self.vectors = data.get("vectors", [])
        else:
            self.build_and_save()

    def search(self, query: str, top_k: int = 3) -> list[tuple[dict, float]]:
        query_vector = self.embedder.embed(query)
        results = []
        for doc, doc_vector in zip(self.documents, self.vectors):
            score = cosine_similarity(query_vector, doc_vector)
            results.append((doc, score))
        
        # ترتيب النتائج بالأعلى تشابهاً
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


if __name__ == "__main__":
    store = VectorStore()
    store.build_and_save()