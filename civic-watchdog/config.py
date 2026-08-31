import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model Configurations for Civic Watchdog
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2" #
SPARSE_MODEL = "Qdrant/bm25" #
RERANKER_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2" #
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")
CHUNK_LENGTH_SECONDS = int(os.getenv("CHUNK_LENGTH_SECONDS", "60"))
CHUNK_OVERLAP_SECONDS = int(os.getenv("CHUNK_OVERLAP_SECONDS", "15"))
TEXT_CHUNK_SIZE = int(os.getenv("TEXT_CHUNK_SIZE", "1600"))
TEXT_CHUNK_OVERLAP = int(os.getenv("TEXT_CHUNK_OVERLAP", "240"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(500 * 1024 * 1024)))
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000")
CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in _cors_origins.split(",")
    if origin.strip()
]
CORS_ORIGINS = list(dict.fromkeys(CORS_ORIGINS))

# Database Settings
QDRANT_PATH = str(Path(__file__).resolve().parent / "civic_db")
COLLECTION_NAME = "city_council"