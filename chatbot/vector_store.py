import re
import threading
from pathlib import Path

from django.conf import settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

_VECTOR_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
_cache_lock = threading.Lock()
_embedding_function = None
_vector_store_cache: dict[str, Chroma] = {}


def _normalize_vector_id(vector_id: str) -> str:
    normalized = (vector_id or "").strip()
    if not normalized or not _VECTOR_ID_PATTERN.match(normalized):
        raise ValueError("Invalid vector_id. Use letters, numbers, '.', '_' or '-'.")
    return normalized


def _collection_root() -> Path:
    root = Path(getattr(settings, "CHROMA_PERSIST_ROOT", "db"))
    return root if root.is_absolute() else Path(settings.BASE_DIR) / root


def _validate_collection_exists(vector_id: str) -> Path:
    collection_dir = _collection_root() / vector_id
    sqlite_path = collection_dir / "chroma.sqlite3"
    if not collection_dir.exists() or not sqlite_path.exists():
        raise FileNotFoundError(
            f"Chroma collection for vector_id '{vector_id}' was not found at '{collection_dir}'."
        )
    return collection_dir


def get_vector_store(vector_id: str) -> Chroma:
    """
    Returns a cached Chroma vector store instance for an existing collection.
    This is intentionally inference-only and does not trigger crawling/ingestion.
    """
    normalized_id = _normalize_vector_id(vector_id)
    collection_dir = _validate_collection_exists(normalized_id)

    global _embedding_function
    with _cache_lock:
        if _embedding_function is None:
            model_name = getattr(settings, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
            _embedding_function = HuggingFaceEmbeddings(model_name=model_name)

        cached = _vector_store_cache.get(normalized_id)
        if cached is not None:
            return cached

        store = Chroma(
            collection_name=normalized_id,
            embedding_function=_embedding_function,
            persist_directory=str(collection_dir),
        )
        _vector_store_cache[normalized_id] = store
        return store
