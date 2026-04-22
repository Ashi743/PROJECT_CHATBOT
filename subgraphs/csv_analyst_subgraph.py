"""
CSV Analyst Subgraph: 4-node workflow with HITL interrupts.
- load_node → interrupt #1 (preview confirm)
- clean_node → interrupt #2 (cleaning plan)
- analyze_node → interrupt #3 (drop duplicates)
- rag_node → interrupt #4 (save to ChromaDB)
"""

import pandas as pd
from pathlib import Path
from typing import TypedDict, Annotated
import json

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from langchain_core.messages import BaseMessage


class CSVAnalystState(TypedDict):
    """State for CSV analysis workflow with HITL checkpoints."""
    messages: Annotated[list[BaseMessage], add_messages]
    dataset_name: str
    file_path: str
    file_name: str
    user_description: str
    preview: str
    null_summary: str
    cleaning_plan: str
    duplicates_count: int
    chunks_created: int
    status: str  # "in_progress" | "completed" | "cancelled"


def load_node(state: CSVAnalystState) -> dict:
    """Load file and show preview interrupt."""
    try:
        df = pd.read_csv(state["file_path"]) if state["file_path"].endswith('.csv') else pd.read_excel(state["file_path"])
        preview = df.head(5).to_string()

        confirmed = interrupt({
            "step": "preview",
            "message": f"Loaded {len(df)} rows × {len(df.columns)} columns. Continue?",
            "preview": preview,
            "columns": df.columns.tolist(),
            "rows": len(df)
        })

        if confirmed != "yes":
            return {"status": "cancelled", "messages": []}

        return {
            "preview": preview,
            "status": "in_progress",
            "messages": [],
        }
    except Exception as e:
        return {"status": "error", "messages": []}


def clean_node(state: CSVAnalystState) -> dict:
    """Plan cleaning operations and show interrupt."""
    try:
        df = pd.read_csv(state["file_path"]) if state["file_path"].endswith('.csv') else pd.read_excel(state["file_path"])

        null_counts = df.isnull().sum()
        null_summary = null_counts[null_counts > 0].to_string() if (null_counts > 0).any() else "No null values"

        cleaning_plan = []
        if (null_counts > 0).any():
            cleaning_plan.append("Drop rows with null values")
        for col in df.columns:
            if df[col].dtype == 'object':
                cleaning_plan.append(f"Fix dtypes: {col} → string")

        plan_str = "\n".join(f"- {step}" for step in cleaning_plan) if cleaning_plan else "No cleaning needed"

        confirmed = interrupt({
            "step": "cleaning_plan",
            "message": "Proposed cleaning steps:",
            "plan": plan_str,
            "null_summary": null_summary
        })

        if confirmed != "yes":
            return {"status": "cancelled", "messages": []}

        return {
            "null_summary": null_summary,
            "cleaning_plan": json.dumps(cleaning_plan),
            "status": "in_progress",
            "messages": [],
        }
    except Exception as e:
        return {"status": "error", "messages": []}


def analyze_node(state: CSVAnalystState) -> dict:
    """Check for duplicates and show interrupt."""
    try:
        df = pd.read_csv(state["file_path"]) if state["file_path"].endswith('.csv') else pd.read_excel(state["file_path"])

        duplicates_count = df.duplicated().sum()
        sample = df[df.duplicated(keep=False)].head(3).to_string() if duplicates_count > 0 else "No duplicates"

        confirmed = interrupt({
            "step": "drop_duplicates",
            "message": f"Found {duplicates_count} duplicate rows. Drop them?",
            "count": duplicates_count,
            "sample": sample
        })

        if confirmed != "yes":
            return {"status": "cancelled", "messages": []}

        return {
            "duplicates_count": duplicates_count,
            "status": "in_progress",
            "messages": [],
        }
    except Exception as e:
        return {"status": "error", "messages": []}


def rag_node(state: CSVAnalystState) -> dict:
    """Save to ChromaDB and show final interrupt."""
    try:
        from tools.csv_ingest_tool import client, METADATA_DIR, _chunk_dataframe

        df = pd.read_csv(state["file_path"]) if state["file_path"].endswith('.csv') else pd.read_excel(state["file_path"])
        chunks = _chunk_dataframe(df, chunk_size=50)

        confirmed = interrupt({
            "step": "save_to_chromadb",
            "message": f"Save {len(chunks)} chunks to ChromaDB?",
            "dataset_name": state["dataset_name"],
            "chunks": len(chunks)
        })

        if confirmed != "yes":
            return {"status": "cancelled", "messages": []}

        # Actually save to ChromaDB (same as RAG subgraph embed_node)
        dtypes_dict = df.dtypes.to_dict()
        columns = df.columns.tolist()
        numeric_cols = [col for col in columns if df[col].dtype in ['int64', 'float64']]
        categorical_cols = [col for col in columns if df[col].dtype == 'object']

        collection = client.get_or_create_collection(
            name=state["dataset_name"],
            metadata={"hnsw:space": "cosine"}
        )

        metadata_doc = {
            "dataset_name": state["dataset_name"],
            "file_name": state["file_name"],
            "file_path": state["file_path"],
            "rows": len(df),
            "cols": len(columns),
            "user_description": state["user_description"],
            "numeric_columns": str(numeric_cols),
            "categorical_columns": str(categorical_cols),
            "dtypes": str({str(k): str(v) for k, v in dtypes_dict.items()})
        }

        collection.upsert(
            ids=[f"metadata_{state['dataset_name']}"],
            documents=[f"Metadata: {state['dataset_name']}\n{state['user_description']}"],
            metadatas=[metadata_doc]
        )

        for chunk_text, chunk_meta in chunks:
            chunk_id = f"{state['dataset_name']}_{chunk_meta['chunk_id']}"
            collection.upsert(
                ids=[chunk_id],
                documents=[chunk_text],
                metadatas=[{**chunk_meta, "dataset_name": state["dataset_name"]}]
            )

        return {
            "chunks_created": len(chunks),
            "status": "completed",
            "messages": [],
        }
    except Exception as e:
        return {"status": "error", "messages": []}


def should_continue(state: CSVAnalystState) -> str:
    """Route to END if user cancelled."""
    if state["status"] == "cancelled":
        return "end"
    return "continue"


# Build graph
def _build_csv_analyst_graph():
    graph = StateGraph(CSVAnalystState)
    graph.add_node("load", load_node)
    graph.add_node("clean", clean_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("rag", rag_node)

    graph.add_edge(START, "load")
    graph.add_conditional_edges("load", should_continue, {"continue": "clean", "end": END})
    graph.add_conditional_edges("clean", should_continue, {"continue": "analyze", "end": END})
    graph.add_conditional_edges("analyze", should_continue, {"continue": "rag", "end": END})
    graph.add_conditional_edges("rag", should_continue, {"continue": END, "end": END})

    return graph


_csv_analyst_graph = _build_csv_analyst_graph()
csv_analyst_graph = None  # Will be compiled in frontend.py with shared checkpointer
