from .config import CHROMA_DIR, EMBEDDING_MODEL, KNOWLEDGE_TYPES, TOP_K
from .embedder import Embedder
from .text_tools import expand_query
from .vector_store import VectorStore


class Retriever:
    def __init__(self, embedder=None, chroma_dir=CHROMA_DIR, model_name=EMBEDDING_MODEL):
        self.store = VectorStore(chroma_dir, model_name)
        if not self.store.count():
            raise RuntimeError("The index is empty. Run python build_index.py first.")
        self.embedder = embedder or Embedder(model_name)

    def search(self, question, top_k=TOP_K, grade=None, subject=None, chunk_types=None):
        if not question or not question.strip():
            raise ValueError("Please enter a question")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        if chunk_types == []:
            return []

        conditions = []
        if grade is not None:
            conditions.append({"grade": grade})
        if subject:
            conditions.append({"subject": subject})
        if chunk_types is not None:
            conditions.append({"chunk_type": {"$in": list(chunk_types)}})
        where = conditions[0] if len(conditions) == 1 else ({"$and": conditions} if conditions else None)

        vector = self.embedder.question(expand_query(question))
        return self.store.search(vector, top_k, where)

    def retrieve(self, question, **filters):
        filters.setdefault("chunk_types", KNOWLEDGE_TYPES)
        matches = self.search(question, **filters)
        sources = []
        for rank, item in enumerate(matches, start=1):
            location = item.get("lesson_title") or item.get("section_title") or "Textbook"
            page = item.get("printed_page_number") or item.get("pdf_page_index") or "?"
            label = f"{item.get('subject')} Grade {item.get('grade')} | {location} | page {page}"
            sources.append({**item, "source": label, "rank": rank})
        context = "\n\n".join(f"[Source {x['rank']}: {x['source']}]\n{x['text']}" for x in sources)
        return {"found": bool(sources), "context": context, "sources": sources}
