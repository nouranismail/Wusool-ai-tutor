from .config import CHROMA_DIR, EMBEDDING_MODEL, TEXTBOOKS_DIR
from .embedder import Embedder
from .loader import load_chunks
from .text_tools import is_title_only, passage_for_embedding
from .vector_store import VectorStore


def build_index(textbooks_dir=TEXTBOOKS_DIR, chroma_dir=CHROMA_DIR,
                model_name=EMBEDDING_MODEL, embedder=None):
    chunks = [chunk for chunk in load_chunks(textbooks_dir) if not is_title_only(chunk)]
    if not chunks:
        raise ValueError("No searchable textbook chunks were found")

    embedder = embedder or Embedder(model_name)
    vectors = embedder.passages([passage_for_embedding(chunk) for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("The embedder must return one vector per chunk")
    store = VectorStore(chroma_dir, model_name, create=True)
    store.replace(chunks, vectors)
    print(f"Indexed {store.count()} chunks in the '{store.name}' collection")


if __name__ == "__main__":
    build_index()
