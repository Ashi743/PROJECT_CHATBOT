import os
from pathlib import Path
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = "data/chroma_db"
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def get_chroma_vectorstore():
    Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name="documents"
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

    elif file_path.endswith((".csv", ".xlsx", ".xls")):
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        text = df.to_string()
        docs = [Document(page_content=text, metadata={"source": file_path})]

    else:
        return {"status": "error", "message": "Unsupported file type"}

    if not docs:
        return {"status": "error", "message": "No documents extracted"}

    for doc in docs:
        doc.metadata["doc_name"] = doc_name

    vectorstore = get_chroma_vectorstore()
    vectorstore.add_documents(docs)

    return {
        "status": "ok",
        "message": f"Document '{doc_name}' added to Chroma vector store",
        "doc_count": len(docs)
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
