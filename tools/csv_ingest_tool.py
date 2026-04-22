import os
import pandas as pd
import chromadb
from pathlib import Path
from datetime import datetime
import json

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
METADATA_DIR = Path(__file__).parent.parent / "data" / "metadata"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

def _calculate_optimal_chunk_size(df_rows: int) -> int:
    """
    Calculate optimal chunk size based on file size.
    Larger files get bigger chunks to reduce processing time.
    """
    if df_rows <= 100:
        return 10
    elif df_rows <= 1000:
        return 25
    elif df_rows <= 10000:
        return 50
    elif df_rows <= 50000:
        return 100
    elif df_rows <= 100000:
        return 250
    else:
        return 500

def _chunk_dataframe(df: pd.DataFrame, chunk_size: int | None = None) -> list[tuple[str, dict]]:
    """
    Split dataframe into chunks for RAG ingestion.
    If chunk_size not provided, calculates optimal size based on DataFrame rows.
    Returns list of (document_text, metadata) tuples.
    """
    if chunk_size is None:
        chunk_size = _calculate_optimal_chunk_size(len(df))

    chunks = []
    num_chunks = (len(df) + chunk_size - 1) // chunk_size

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(df))
        chunk = df.iloc[start_idx:end_idx]

        doc_text = chunk.to_string()

        metadata = {
            "chunk_id": f"chunk_{i}",
            "start_row": start_idx,
            "end_row": end_idx,
            "rows_in_chunk": len(chunk),
            "columns": str(chunk.columns.tolist())
        }

        chunks.append((doc_text, metadata))

    return chunks

def save_and_prepare_file(file_bytes: bytes, file_name: str, dataset_name: str) -> dict:
    """
    Save file to disk and prepare basic metadata (fast operation).

    Args:
        file_bytes: Raw file bytes from upload
        file_name: Original file name (e.g., 'sales.csv')
        dataset_name: User-provided name for this dataset

    Returns:
        dict with status, rows, columns, dtypes, file_path
    """
    try:
        file_ext = Path(file_name).suffix.lower()
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            return {
                "status": "error",
                "message": f"Unsupported file type: {file_ext}. Use .csv or .xlsx"
            }

        file_path = UPLOAD_DIR / f"{dataset_name}{file_ext}"
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        rows, cols = df.shape
        columns = df.columns.tolist()
        dtypes_dict = df.dtypes.to_dict()

        return {
            "status": "ok",
            "file_path": str(file_path),
            "file_ext": file_ext,
            "rows": rows,
            "cols": cols,
            "columns": columns,
            "dtypes_dict": dtypes_dict
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error saving file: {str(e)}"
        }

def ingest_file_to_rag(file_path: str, dataset_name: str, user_description: str, file_name: str, on_progress=None) -> dict:
    """
    Ingest prepared file into RAG system (can be slower).

    Args:
        file_path: Path to saved file
        dataset_name: Name of dataset
        user_description: User's description
        file_name: Original file name
        on_progress: Optional callable(message: str) for real-time step updates

    Returns:
        dict with status and RAG ingestion results
    """
    def _progress(msg: str):
        if on_progress:
            on_progress(msg)

    try:
        file_path_obj = Path(file_path)

        _progress("📥 Loading file into memory...")
        if file_path_obj.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        rows, cols = df.shape
        columns = df.columns.tolist()
        dtypes_dict = df.dtypes.to_dict()
        _progress(f"✓ Loaded {rows:,} rows × {cols} columns")

        _progress("🗂️ Creating vector database collection...")
        collection = client.get_or_create_collection(
            name=dataset_name,
            metadata={"hnsw:space": "cosine"}
        )

        numeric_cols = [col for col in columns if df[col].dtype in ['int64', 'float64']]
        categorical_cols = [col for col in columns if df[col].dtype == 'object']

        _progress("📝 Storing metadata...")
        metadata_doc = {
            "dataset_name": dataset_name,
            "file_name": file_name,
            "file_path": str(file_path),
            "rows": rows,
            "cols": cols,
            "user_description": user_description,
            "ingested_at": datetime.now().isoformat(),
            "numeric_columns": str(numeric_cols),
            "categorical_columns": str(categorical_cols),
            "dtypes": str({str(k): str(v) for k, v in dtypes_dict.items()})
        }
        collection.upsert(
            ids=[f"metadata_{dataset_name}"],
            documents=[f"Metadata: {dataset_name}\n{user_description or 'No description provided'}"],
            metadatas=[metadata_doc]
        )

        _progress("🔎 Storing sample rows...")
        sample_doc = df.head(10).to_string()
        collection.upsert(
            ids=[f"sample_{dataset_name}"],
            documents=[f"Sample data from {dataset_name}:\n{sample_doc}"],
            metadatas=[{"type": "sample", "sample_size": min(10, len(df))}]
        )

        chunk_size = _calculate_optimal_chunk_size(rows)
        chunks = _chunk_dataframe(df, chunk_size=chunk_size)
        _progress(f"✂️ Chunking into {len(chunks)} pieces (chunk size: {chunk_size} rows)...")
        for chunk_text, chunk_meta in chunks:
            chunk_id = f"{dataset_name}_{chunk_meta['chunk_id']}"
            collection.upsert(
                ids=[chunk_id],
                documents=[chunk_text],
                metadatas=[{**chunk_meta, "dataset_name": dataset_name}]
            )

        _progress("📊 Computing statistics...")
        stats_text = f"Statistics for {dataset_name}:\n{df.describe().to_string()}"
        collection.upsert(
            ids=[f"stats_{dataset_name}"],
            documents=[stats_text],
            metadatas=[{"type": "statistics"}]
        )

        _progress("💾 Saving metadata to disk...")
        full_metadata = {
            "dataset_name": dataset_name,
            "file_name": file_name,
            "file_path": str(file_path),
            "rows": rows,
            "columns": columns,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "dtypes": {str(k): str(v) for k, v in dtypes_dict.items()},
            "user_description": user_description,
            "ingested_at": datetime.now().isoformat(),
            "chunks_created": len(chunks)
        }
        metadata_file = METADATA_DIR / f"{dataset_name}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(full_metadata, f, indent=2, default=str)

        _progress("✅ Done!")

        return {
            "status": "ok",
            "message": f"Successfully ingested {rows} rows into dataset '{dataset_name}'",
            "rows": rows,
            "columns": columns,
            "chunks_created": len(chunks),
            "dataset_name": dataset_name,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error ingesting to RAG: {str(e)}"
        }

def ingest_file(file_bytes: bytes, file_name: str, dataset_name: str, user_description: str = "") -> dict:
    """
    Wrapper that combines save and RAG ingestion (keeps backward compatibility).
    """
    save_result = save_and_prepare_file(file_bytes, file_name, dataset_name)
    if save_result["status"] != "ok":
        return save_result

    rag_result = ingest_file_to_rag(
        file_path=save_result["file_path"],
        dataset_name=dataset_name,
        user_description=user_description,
        file_name=file_name
    )
    return rag_result

def list_datasets() -> list[str]:
    """List all available datasets (ChromaDB collections)."""
    try:
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        print(f"Error listing datasets: {str(e)}")
        return []

def get_dataset_info(dataset_name: str) -> dict:
    """Get metadata about a specific dataset."""
    try:
        # Try reading from JSON file first (most reliable)
        metadata_file = METADATA_DIR / f"{dataset_name}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            return metadata

        # Fallback to ChromaDB metadata
        collection = client.get_collection(name=dataset_name)
        results = collection.get(ids=[f"metadata_{dataset_name}"])

        if results and results['metadatas']:
            metadata = results['metadatas'][0]
            columns_val = metadata.get("columns", "[]")
            numeric_cols_val = metadata.get("numeric_columns", "[]")
            categorical_cols_val = metadata.get("categorical_columns", "[]")
            
            return {
                "dataset_name": dataset_name,
                "rows": metadata.get("rows"),
                "columns": eval(columns_val) if isinstance(columns_val, str) else columns_val or [],
                "file_name": metadata.get("file_name"),
                "file_path": metadata.get("file_path"),
                "user_description": metadata.get("user_description", ""),
                "numeric_columns": eval(numeric_cols_val) if isinstance(numeric_cols_val, str) else numeric_cols_val or [],
                "categorical_columns": eval(categorical_cols_val) if isinstance(categorical_cols_val, str) else categorical_cols_val or [],
                "ingested_at": metadata.get("ingested_at")
            }
        return {"error": f"No metadata found for dataset '{dataset_name}'"}
    except Exception as e:
        return {"error": str(e)}

def search_dataset(dataset_name: str, query: str, n_results: int = 5) -> list[dict]:
    """
    RAG-based search within a dataset.
    Finds relevant data chunks based on semantic similarity.

    Args:
        dataset_name: Name of dataset to search
        query: Natural language query (e.g., "high sales regions")
        n_results: Number of results to return

    Returns:
        List of relevant data chunks with metadata
    """
    try:
        collection = client.get_collection(name=dataset_name)
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, 10)
        )

        formatted_results = []
        if results and results['ids']:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    "id": doc_id,
                    "document": results['documents'][0][i] if results['documents'] else "",
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })

        return formatted_results

    except Exception as e:
        return [{"error": str(e)}]

def update_dataset_description(dataset_name: str, new_description: str) -> dict:
    """
    Update user description for a dataset (HITL feedback).

    Args:
        dataset_name: Name of dataset
        new_description: New description from user

    Returns:
        Success/error status
    """
    try:
        # Update JSON file if it exists
        metadata_file = METADATA_DIR / f"{dataset_name}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            metadata['user_description'] = new_description
            metadata['updated_at'] = datetime.now().isoformat()
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

        # Also update ChromaDB metadata
        collection = client.get_collection(name=dataset_name)
        results = collection.get(ids=[f"metadata_{dataset_name}"])

        if results and results['metadatas']:
            metadata = dict(results['metadatas'][0])
            metadata['user_description'] = new_description
            metadata['updated_at'] = datetime.now().isoformat()

            collection.upsert(
                ids=[f"metadata_{dataset_name}"],
                documents=[f"Metadata: {dataset_name}\n{new_description}"],
                metadatas=[metadata]
            )

            return {
                "status": "ok",
                "message": f"Updated description for '{dataset_name}'"
            }

        return {"status": "error", "message": f"Dataset '{dataset_name}' not found"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_dataset(dataset_name: str) -> dict:
    """
    Delete a dataset and its data (HITL cleanup).

    Args:
        dataset_name: Name of dataset to delete

    Returns:
        Success/error status
    """
    try:
        client.delete_collection(name=dataset_name)

        # Delete uploaded file
        for ext in ['.csv', '.xlsx', '.xls']:
            file_path = UPLOAD_DIR / f"{dataset_name}{ext}"
            if file_path.exists():
                file_path.unlink()

        # Delete metadata file
        metadata_file = METADATA_DIR / f"{dataset_name}_metadata.json"
        if metadata_file.exists():
            metadata_file.unlink()

        return {
            "status": "ok",
            "message": f"Successfully deleted dataset '{dataset_name}'"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("CSV Ingestion Tool with RAG Support")
    print("Available datasets:", list_datasets())
    for ds in list_datasets():
        print(f"  - {ds}: {get_dataset_info(ds)}")
