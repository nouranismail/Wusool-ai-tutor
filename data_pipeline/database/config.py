import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/educational_tutor"
)

# Relative paths are resolved against the project root (not the current
# working directory), so scripts work no matter where they are launched from.
_textbooks = Path(os.getenv("TEXTBOOKS_DIR", "textbooks")).expanduser()
TEXTBOOKS_DIR = _textbooks if _textbooks.is_absolute() else (PROJECT_ROOT / _textbooks).resolve()

# Output dimension of the chosen embedding model (768 for multilingual-e5-base).
# Used by semantic_search.py so queries match the HNSW expression index.
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))
