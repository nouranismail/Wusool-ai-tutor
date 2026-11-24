import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Set these in .env when the data pipeline or index folder lives elsewhere.
TEXTBOOKS_DIR = Path(os.getenv("TEXTBOOKS_DIR", "../data_pipeline/database/textbooks"))
if not TEXTBOOKS_DIR.is_absolute():
    TEXTBOOKS_DIR = (ROOT / TEXTBOOKS_DIR).resolve()

CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "chroma_db"))
if not CHROMA_DIR.is_absolute():
    CHROMA_DIR = (ROOT / CHROMA_DIR).resolve()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
TOP_K = int(os.getenv("TOP_K", "10"))

KNOWLEDGE_TYPES = [
    "explanation", "grammar_explanation", "vocabulary", "reading_passage",
    "dialogue", "learning_objective", "practical_activity", "experiment",
]
