from .config import EMBEDDING_MODEL
from .text_tools import clean_text


class Embedder:
    def __init__(self, model_name=EMBEDDING_MODEL):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.is_e5 = "e5" in model_name.lower()

    def passages(self, texts):
        prefix = "passage: " if self.is_e5 else ""
        cleaned = [prefix + clean_text(text) for text in texts]
        return self.model.encode(cleaned, normalize_embeddings=True, show_progress_bar=True)

    def question(self, text):
        prefix = "query: " if self.is_e5 else ""
        return self.model.encode(prefix + clean_text(text), normalize_embeddings=True)
