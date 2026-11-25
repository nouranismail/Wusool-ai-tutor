import uuid
import warnings

import chromadb

from .config import CHROMA_DIR, EMBEDDING_MODEL, TOP_K

BATCH_SIZE = 500
COLLECTION_SETTINGS = {"hnsw:space": "cosine"}
FIELDS = [
    "book_id", "subject", "grade", "term", "language", "unit_id", "unit_title",
    "lesson_id", "lesson_title", "section_title", "chunk_type",
    "printed_page_number", "pdf_page_index",
]


class VectorStore:
    def __init__(self, path=CHROMA_DIR, model_name=EMBEDDING_MODEL, create=False):
        self.name = "textbooks_" + model_name.replace("/", "_")
        self.client = chromadb.PersistentClient(path=str(path))
        if create:
            self.collection = self.client.get_or_create_collection(
                self.name, metadata=COLLECTION_SETTINGS, embedding_function=None
            )
        else:
            try:
                self.collection = self.client.get_collection(self.name, embedding_function=None)
            except chromadb.errors.NotFoundError as error:
                raise RuntimeError(
                    f"Index not found. From the repository root run: "
                    f"python -m {__package__}.build_index"
                ) from error

    def count(self):
        return self.collection.count()

    def add_to(self, collection, chunks, vectors):
        """Write records in manageable batches; Chroma limits batch sizes."""
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            embeddings = vectors[start:start + BATCH_SIZE]
            metadatas = []
            for chunk in batch:
                metadata = {key: chunk[key] for key in FIELDS if chunk.get(key) is not None}
                for key, value in metadata.items():
                    if not isinstance(value, (str, int, float, bool)):
                        raise ValueError(f"Metadata {key} must be a simple value")
                metadatas.append(metadata)

            collection.add(
                ids=[chunk["chunk_id"] for chunk in batch],
                documents=[chunk["text"] for chunk in batch],
                embeddings=[[float(value) for value in vector] for vector in embeddings],
                metadatas=metadatas,
            )

    def replace(self, chunks, vectors):
        """Build a new collection first, then switch to it after it is complete."""
        if not chunks or len(chunks) != len(vectors):
            raise ValueError("Need at least one chunk and one embedding per chunk")
        try:
            dimension = len(vectors[0])
            if dimension == 0 or any(len(vector) != dimension for vector in vectors):
                raise ValueError("All embeddings must have the same non-zero dimension")
        except TypeError as error:
            raise ValueError("Embeddings must be one-dimensional vectors") from error

        suffix = uuid.uuid4().hex[:10]
        stage_name = f"stage_{suffix}"
        backup_name = f"backup_{suffix}"
        stage = self.client.create_collection(
            stage_name, metadata=COLLECTION_SETTINGS, embedding_function=None
        )
        try:
            self.add_to(stage, chunks, vectors)
            if stage.count() != len(chunks):
                raise RuntimeError("Staging collection is missing chunks")

            old = None
            try:
                old = self.client.get_collection(self.name, embedding_function=None)
            except chromadb.errors.NotFoundError:
                pass

            if old:
                old.modify(name=backup_name)
            try:
                stage.modify(name=self.name)
            except Exception:
                if old:
                    self.client.get_collection(backup_name, embedding_function=None).modify(name=self.name)
                raise

            self.collection = self.client.get_collection(self.name, embedding_function=None)
            if old:
                try:
                    self.client.delete_collection(backup_name)
                except Exception as error:
                    warnings.warn(f"New index is active; old backup remains: {error}", RuntimeWarning)
        except Exception:
            try:
                self.client.delete_collection(stage_name)
            except chromadb.errors.NotFoundError:
                pass
            raise

    def search(self, vector, top_k=TOP_K, filters=None):
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        result = self.collection.query(
            query_embeddings=[[float(value) for value in vector]],
            n_results=top_k,
            where=filters,
            include=["documents", "metadatas", "distances"],
        )
        matches = []
        for chunk_id, text, metadata, distance in zip(
            result["ids"][0], result["documents"][0],
            result["metadatas"][0], result["distances"][0],
        ):
            item = {field: metadata.get(field) for field in FIELDS}
            item.update({"chunk_id": chunk_id, "text": text, "score": round(1 - distance, 4)})
            matches.append(item)
        return matches
