import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# LLM: "groq" (reads GROQ_API_KEY) or "mistral" (reads MISTRAL_API_KEY)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_MODEL = os.getenv("LLM_MODEL")  # empty = provider default

COLLECTION_NAME = "legal_docs"
EMBEDDING_MODEL_NAME = "BAAI/bge-large-en-v1.5"
TOP_K = 3

# Postgres
POSTGRES_DB   = os.getenv("POSTGRES_DB", "legal_ai")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASS = os.getenv("POSTGRES_PASSWORD", "admin")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", 3600))