import os
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

# Database Settings
QDRANT_PATH = "./civic_db"
COLLECTION_NAME = "city_council"