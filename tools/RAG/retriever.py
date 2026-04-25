import os
from pathlib import Path
from typing import List, Dict
import chromadb
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import pandas as pd
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Use server-based Chroma (same as chatbot memory system)
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Document chunking settings
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""]
)

def get_chroma_vectorstore():
    """Get Chroma vectorstore (server-based for consistency with chatbot)."""
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return Chroma(
        client=client,
        embedding_function=embeddings,
        collection_name="rag_documents"
    )

def save_document_to_chroma(file_path: str, doc_name: str) -> Dict:
    docs = []

    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        docs = loader.load()

    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        docs = loader.load()

    elif file_path.endswith(".doc"):
        import subprocess
        text = subprocess.run(
            ["python", "-m", "docx2txt", file_path],
            capture_output=True,
            text=True
        ).stdout
        docs = [Document(page_content=text, metadata={"source": file_path})]

    elif file_path.endswith(".md"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        docs = [Document(page_content=text, metadata={"source": file_path})]

    elif file_path.endswith((".csv", ".xlsx", ".xls")):
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        text = df.to_string()
        docs = [Document(page_content=text, metadata={"source": file_path})]

    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        docs = [Document(page_content=text, metadata={"source": file_path})]

    else:
        return {"status": "error", "message": "Unsupported file type. Supported: PDF, DOCX, DOC, MD, TXT, CSV, XLSX, XLS"}

    if not docs:
        return {"status": "error", "message": "No documents extracted"}

    # Add metadata to all docs
    for doc in docs:
        doc.metadata["doc_name"] = doc_name

    # Chunk documents for better retrieval
    chunked_docs = text_splitter.split_documents(docs)
    logger.info(f"Chunked '{doc_name}' into {len(chunked_docs)} chunks (from {len(docs)} pages)")

    vectorstore = get_chroma_vectorstore()
    vectorstore.add_documents(chunked_docs)

    return {
        "status": "ok",
        "message": f"Document '{doc_name}' chunked into {len(chunked_docs)} pieces and added to Chroma",
        "doc_count": len(docs),
        "chunk_count": len(chunked_docs)
    }


def retrieve_documents(question: str, k: int = 4) -> List[Dict]:
    try:
        vectorstore = get_chroma_vectorstore()
        docs = vectorstore.similarity_search(question, k=k)
        return [
            {
                "content": doc.page_content[:500],
                "source": doc.metadata.get("doc_name", "unknown"),
                "page": doc.metadata.get("page", None)
            }
            for doc in docs
        ]
    except Exception as e:
        return []


def get_indexed_documents() -> List[Dict]:
    try:
        vectorstore = get_chroma_vectorstore()
        collection = vectorstore._collection
        results = collection.get()

        documents = []
        for i, doc_id in enumerate(results.get("ids", [])):
            documents.append({
                "id": doc_id,
                "name": results.get("metadatas", [{}])[i].get("doc_name", "unknown"),
                "source": results.get("metadatas", [{}])[i].get("source", "unknown"),
                "preview": results.get("documents", [""])[i][:100] + "..." if len(results.get("documents", [""])[i]) > 100 else results.get("documents", [""])[i]
            })
        return documents
    except Exception as e:
        return []


def delete_document(doc_name: str) -> Dict:
    """Delete all indexed chunks for a document (FAST batch delete)."""
    try:
        vectorstore = get_chroma_vectorstore()
        collection = vectorstore._collection

        # Get all documents
        results = collection.get()
        metadatas = results.get("metadatas", [])
        doc_ids = results.get("ids", [])

        # Find all chunks belonging to this document
        ids_to_delete = [
            doc_ids[i]
            for i in range(len(doc_ids))
            if metadatas[i].get("doc_name") == doc_name
        ]

        if not ids_to_delete:
            return {"status": "ok", "message": f"Document '{doc_name}' not found", "deleted_count": 0}

        # Batch delete all chunks at once (fast)
        collection.delete(ids=ids_to_delete)

        return {
            "status": "ok",
            "message": f"[OK] Deleted '{doc_name}' ({len(ids_to_delete)} chunks removed)",
            "deleted_count": len(ids_to_delete)
        }
    except Exception as e:
        return {"status": "error", "message": f"[ERROR] Delete failed: {str(e)}", "deleted_count": 0}


def delete_all_documents() -> Dict:
    """Delete all indexed documents (clear entire collection)."""
    try:
        vectorstore = get_chroma_vectorstore()
        collection = vectorstore._collection

        results = collection.get()
        all_ids = results.get("ids", [])

        if not all_ids:
            return {"status": "ok", "message": "No documents to delete", "deleted_count": 0}

        # Delete all at once
        collection.delete(ids=all_ids)

        return {
            "status": "ok",
            "message": f"[OK] Cleared all ({len(all_ids)} chunks removed)",
            "deleted_count": len(all_ids)
        }
    except Exception as e:
        return {"status": "error", "message": f"[ERROR] Clear failed: {str(e)}", "deleted_count": 0}
