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

def _chunk_dataframe(df: pd.DataFrame, chunk_size: int = 50) -> list[tuple[str, dict]]:
    """
    Split dataframe into chunks for RAG ingestion.
    Returns list of (document_text, metadata) tuples.
    """
    chunks = []
    num_chunks = (len(df) + chunk_size - 1) // chunk_size

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(df))
        chunk = df.iloc[start_idx:end_idx]

        # Convert chunk to readable text
        doc_text = chunk.to_string()

        # Add context about the chunk
        metadata = {
            "chunk_id": f"chunk_{i}",
            "start_row": start_idx,
            "end_row": end_idx,
            "rows_in_chunk": len(chunk),
            "columns": str(chunk.columns.tolist())
        }

        chunks.append((doc_text, metadata))

    return chunks

def ingest_file(file_bytes: bytes, file_name: str, dataset_name: str, user_description: str = "") -> dict:
    """
    Ingest a CSV or Excel file with full RAG support.

    Args:
        file_bytes: Raw file bytes from upload
        file_name: Original file name (e.g., 'sales.csv')
        dataset_name: User-provided name for this dataset (e.g., 'sales_data')
        user_description: Optional user description of the dataset (HITL)

    Returns:
        dict with status, row count, columns, and dataset_name
    """
    try:
        # Determine file extension
        file_ext = Path(file_name).suffix.lower()
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            return {
                "status": "error",
                "message": f"Unsupported file type: {file_ext}. Use .csv or .xlsx"
            }

        # Save file to disk
        file_path = UPLOAD_DIR / f"{dataset_name}{file_ext}"
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        # Read file with pandas
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        rows, cols = df.shape
        columns = df.columns.tolist()
        dtypes_dict = df.dtypes.to_dict()

        # Create ChromaDB collection for this dataset
        collection = client.get_or_create_collection(
            name=dataset_name,
            metadata={"hnsw:space": "cosine"}
        )

        # 1. Store metadata document
        metadata_doc = {
            "dataset_name": dataset_name,
            "file_name": file_name,
            "file_path": str(file_path),
            "rows": rows,
            "columns": columns,
            "dtypes": {str(k): str(v) for k, v in dtypes_dict.items()},
            "user_description": user_description,
            "ingested_at": datetime.now().isoformat(),
            "numeric_columns": [col for col in columns if df[col].dtype in ['int64', 'float64']],
            "categorical_columns": [col for col in columns if df[col].dtype == 'object'],
            "summary_stats": df.describe().to_dict()
        }

        collection.upsert(
            ids=[f"metadata_{dataset_name}"],
            documents=[f"Metadata: {dataset_name}\n{user_description or 'No description provided'}"],
            metadatas=[metadata_doc]
        )

        # 2. Store sample rows
        sample_doc = df.head(10).to_string()
        collection.upsert(
            ids=[f"sample_{dataset_name}"],
            documents=[f"Sample data from {dataset_name}:\n{sample_doc}"],
            metadatas=[{
                "type": "sample",
                "sample_size": min(10, len(df))
            }]
        )

        # 3. Chunk and store full data for RAG
        chunks = _chunk_dataframe(df, chunk_size=50)
        for chunk_text, chunk_meta in chunks:
            chunk_id = f"{dataset_name}_{chunk_meta['chunk_id']}"
            merged_metadata = {**chunk_meta, "dataset_name": dataset_name}
            collection.upsert(
                ids=[chunk_id],
                documents=[chunk_text],
                metadatas=[merged_metadata]
            )

        # 4. Store statistics document for quick analysis
        stats_text = f"Statistics for {dataset_name}:\n{df.describe().to_string()}"
        collection.upsert(
            ids=[f"stats_{dataset_name}"],
            documents=[stats_text],
            metadatas=[{"type": "statistics"}]
        )

        # 5. Save metadata to JSON (for HITL review)
        metadata_file = METADATA_DIR / f"{dataset_name}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata_doc, f, indent=2, default=str)

        return {
            "status": "ok",
            "message": f"Successfully ingested {rows} rows into dataset '{dataset_name}'",
            "rows": rows,
            "columns": columns,
            "chunks_created": len(chunks),
            "dataset_name": dataset_name,
            "numeric_columns": metadata_doc["numeric_columns"],
            "categorical_columns": metadata_doc["categorical_columns"]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error ingesting file: {str(e)}"
        }

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
        collection = client.get_collection(name=dataset_name)
        results = collection.get(ids=[f"metadata_{dataset_name}"])

        if results and results['metadatas']:
            metadata = results['metadatas'][0]
            return {
                "dataset_name": dataset_name,
                "rows": metadata.get("rows"),
                "columns": metadata.get("columns", []),
                "file_name": metadata.get("file_name"),
                "file_path": metadata.get("file_path"),
                "user_description": metadata.get("user_description", ""),
                "numeric_columns": metadata.get("numeric_columns", []),
                "categorical_columns": metadata.get("categorical_columns", []),
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
        collection = client.get_collection(name=dataset_name)
        results = collection.get(ids=[f"metadata_{dataset_name}"])

        if results and results['metadatas']:
            metadata = results['metadatas'][0]
            metadata['user_description'] = new_description
            metadata['updated_at'] = datetime.now().isoformat()

            collection.upsert(
                ids=[f"metadata_{dataset_name}"],
                documents=[f"Metadata: {dataset_name}\n{new_description}"],
                metadatas=[metadata]
            )

            # Update JSON file
            metadata_file = METADATA_DIR / f"{dataset_name}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

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
