from backend.app.rag.vector_store import VectorStore

store = VectorStore()

def retrieve_context(question: str, lesson_id: str = None, threshold: float = 0.15) -> dict:
    """استرجاع السياق المباشر للسؤال مع التأكد من عتبة التشابه المحددة."""
    results = store.search(question, top_k=3)
    
    if not results:
        return {"context": [], "citations": [], "not_covered": True, "used_fallback": True}

    best_doc, best_score = results[0]

    # إذا كانت نسبة التشابه ضعيفة جداً يعتبر خارج المنهج
    if best_score < threshold:
        return {
            "context": [],
            "citations": [],
            "not_covered": True,
            "used_fallback": True,
            "score": best_score
        }

    context_list = []
    citations = []

    for doc, score in results:
        if score >= threshold:
            context_list.append(doc["text_ar"])
            citations.append({
                "file": doc.get("source_file", "curriculum.json"),
                "pages": doc.get("pages", [1])
            })

    return {
        "context": context_list,
        "citations": citations,
        "not_covered": False,
        "used_fallback": False,
        "score": best_score
    }