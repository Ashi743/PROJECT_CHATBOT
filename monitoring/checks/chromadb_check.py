from pathlib import Path
import logging
import shutil

logger = logging.getLogger(__name__)


def check_chromadb() -> dict:
    chroma_dir = Path("data/chroma_db")

    if not chroma_dir.exists():
        return {
            "chromadb": {
                "status": "[NOT_FOUND]",
                "documents": 0,
                "disk_mb": 0
            }
        }

    disk_usage = shutil.disk_usage(chroma_dir)
    disk_mb = disk_usage.used / (1024 * 1024)

    try:
        from langchain_community.vectorstores import Chroma
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings()
        db = Chroma(persist_directory=str(chroma_dir), embedding_function=embeddings)

        doc_count = db._collection.count()

        test_query_status = "[OK]"
        try:
            results = db.similarity_search("test", k=1)
        except Exception as e:
            logger.warning(f"ChromaDB test search failed: {e}")
            test_query_status = "[WARN]"

        if doc_count == 0:
            status = "[EMPTY]"
        elif disk_mb > 1024:
            status = "[WARN]"
        else:
            status = "[OK]"

        return {
            "chromadb": {
                "status": status,
                "documents": doc_count,
                "disk_mb": round(disk_mb, 2),
                "test_query": test_query_status
            }
        }

    except Exception as e:
        logger.error(f"Error checking ChromaDB: {e}")
        return {
            "chromadb": {
                "status": "[ERROR]",
                "documents": 0,
                "disk_mb": round(disk_mb, 2),
                "error": str(e)
            }
        }


if __name__ == "__main__":
    import json
    result = check_chromadb()
    print(json.dumps(result, indent=2))
