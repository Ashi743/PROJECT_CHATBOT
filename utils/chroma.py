"""Lazy ChromaDB client."""
import threading
import chromadb
from utils.paths import CHROMA_DIR

_client = None
_lock = threading.Lock()


def get_client():
    global _client
    with _lock:
        if _client is None:
            _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return _client
