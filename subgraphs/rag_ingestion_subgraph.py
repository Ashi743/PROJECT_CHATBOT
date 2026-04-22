"""
RAG Ingestion Subgraph: 3-node workflow for file upload → chunk → embed.
No HITL interrupts — fully autonomous once started.
"""

import pandas as pd
from pathlib import Path
from typing import TypedDict, Annotated
from datetime import datetime
import json

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from tools.csv_ingest_tool import _chunk_dataframe

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class RAGIngestionState(TypedDict):
    """State for RAG ingestion workflow."""
    messages: Annotated[list[BaseMessage], add_messages]
    file_bytes: bytes  # Will be cleared after validate_node
    file_name: str
    dataset_name: str
    user_description: str
    file_path: str  # Absolute path, set by validate_node
    rows: int
    columns: list[str]
    chunks_created: int
    status: str  # "in_progress" | "completed" | "error"


def validate_node(state: RAGIngestionState) -> dict:
    """Validate file and save to disk."""
    try:
        file_ext = Path(state["file_name"]).suffix.lower()
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            return {
                "status": "error",
                "messages": [],
            }

        # Save file to disk
        file_path = UPLOAD_DIR / f"{state['dataset_name']}{file_ext}"
        with open(file_path, 'wb') as f:
            f.write(state["file_bytes"])

        # Read with pandas
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        rows, cols = df.shape

        return {
            "file_path": str(file_path),
            "rows": rows,
            "columns": df.columns.tolist(),
            "file_bytes": b"",  # Clear bytes from state (not serializable)
            "status": "in_progress",
            "messages": [],
        }

    except Exception as e:
        return {
            "status": "error",
            "messages": [],
        }


def chunk_node(state: RAGIngestionState) -> dict:
    """Chunk the dataframe for RAG indexing."""
    try:
        df = pd.read_csv(state["file_path"]) if state["file_path"].endswith('.csv') else pd.read_excel(state["file_path"])
        chunks = _chunk_dataframe(df, chunk_size=50)

        return {
            "chunks_created": len(chunks),
            "status": "in_progress",
            "messages": [],
        }

    except Exception as e:
        return {
            "status": "error",
            "messages": [],
        }


def embed_node(state: RAGIngestionState) -> dict:
    """Upsert chunks to ChromaDB and save metadata."""
    try:
        from tools.csv_ingest_tool import client, METADATA_DIR

        df = pd.read_csv(state["file_path"]) if state["file_path"].endswith('.csv') else pd.read_excel(state["file_path"])
        dtypes_dict = df.dtypes.to_dict()
        numeric_cols = [col for col in state["columns"] if df[col].dtype in ['int64', 'float64']]
        categorical_cols = [col for col in state["columns"] if df[col].dtype == 'object']

        # Create ChromaDB collection
        collection = client.get_or_create_collection(
            name=state["dataset_name"],
            metadata={"hnsw:space": "cosine"}
        )

        # Store metadata (ChromaDB compatible — only primitives/lists)
        metadata_doc = {
            "dataset_name": state["dataset_name"],
            "file_name": state["file_name"],
            "file_path": state["file_path"],
            "rows": state["rows"],
            "cols": len(state["columns"]),
            "user_description": state["user_description"],
            "ingested_at": datetime.now().isoformat(),
            "numeric_columns": str(numeric_cols),
            "categorical_columns": str(categorical_cols),
            "dtypes": str({str(k): str(v) for k, v in dtypes_dict.items()})
        }

        collection.upsert(
            ids=[f"metadata_{state['dataset_name']}"],
            documents=[f"Metadata: {state['dataset_name']}\n{state['user_description'] or 'No description provided'}"],
            metadatas=[metadata_doc]
        )

        # Store sample rows
        sample_doc = df.head(10).to_string()
        collection.upsert(
            ids=[f"sample_{state['dataset_name']}"],
            documents=[f"Sample data from {state['dataset_name']}:\n{sample_doc}"],
            metadatas=[{"type": "sample", "sample_size": min(10, len(df))}]
        )

        # Chunk and store
        chunks = _chunk_dataframe(df, chunk_size=50)
        for chunk_text, chunk_meta in chunks:
            chunk_id = f"{state['dataset_name']}_{chunk_meta['chunk_id']}"
            merged_metadata = {**chunk_meta, "dataset_name": state["dataset_name"]}
            collection.upsert(
                ids=[chunk_id],
                documents=[chunk_text],
                metadatas=[merged_metadata]
            )

        # Store statistics
        stats_text = f"Statistics for {state['dataset_name']}:\n{df.describe().to_string()}"
        collection.upsert(
            ids=[f"stats_{state['dataset_name']}"],
            documents=[stats_text],
            metadatas=[{"type": "statistics"}]
        )

        # Save full metadata to JSON
        full_metadata = {
            "dataset_name": state["dataset_name"],
            "file_name": state["file_name"],
            "file_path": state["file_path"],
            "rows": state["rows"],
            "columns": state["columns"],
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "dtypes": {str(k): str(v) for k, v in dtypes_dict.items()},
            "user_description": state["user_description"],
            "ingested_at": datetime.now().isoformat(),
            "chunks_created": len(chunks)
        }

        metadata_file = METADATA_DIR / f"{state['dataset_name']}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(full_metadata, f, indent=2, default=str)

        return {
            "chunks_created": len(chunks),
            "status": "completed",
            "messages": [],
        }

    except Exception as e:
        return {
            "status": "error",
            "messages": [],
        }


# Build graph
def _build_rag_graph():
    graph = StateGraph(RAGIngestionState)
    graph.add_node("validate", validate_node)
    graph.add_node("chunk", chunk_node)
    graph.add_node("embed", embed_node)

    graph.add_edge(START, "validate")
    graph.add_edge("validate", "chunk")
    graph.add_edge("chunk", "embed")
    graph.add_edge("embed", END)

    return graph


# This will be compiled in frontend.py with shared checkpointer
_rag_graph = _build_rag_graph()
rag_ingestion_graph = None  # Will be set by frontend.py after importing checkpointer
