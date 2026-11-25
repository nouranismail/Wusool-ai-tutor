import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
load_dotenv(PROJECT_ROOT / ".env")

textbooks_path = Path(
    os.getenv("TEXTBOOKS_DIR", "data_pipeline/database/textbooks")
).expanduser()
TEXTBOOKS_DIR = (
    textbooks_path
    if textbooks_path.is_absolute()
    else (PROJECT_ROOT / textbooks_path).resolve()
)

chroma_path = os.getenv("VECTOR_DB_DIR") or os.getenv("CHROMA_DIR")
CHROMA_DIR = Path(chroma_path).expanduser() if chroma_path else ROOT / "chroma_db"
if not CHROMA_DIR.is_absolute():
    CHROMA_DIR = (PROJECT_ROOT / CHROMA_DIR).resolve()

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "intfloat/multilingual-e5-base"
)
try:
    TOP_K = int(os.getenv("TOP_K", "10"))
except ValueError as error:
    raise ValueError("TOP_K must be a positive integer") from error
if TOP_K < 1:
    raise ValueError("TOP_K must be a positive integer")

KNOWLEDGE_TYPES = [
    "explanation",
    "grammar_explanation",
    "vocabulary",
    "reading_passage",
    "dialogue",
    "learning_objective",
    "practical_activity",
    "experiment",
]
