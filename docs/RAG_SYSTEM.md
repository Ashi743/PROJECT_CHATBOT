# RAG CSV/Excel Analysis System

## Overview

A complete **Retrieval-Augmented Generation (RAG)** system for analyzing CSV and Excel files using:
- **Semantic search** via ChromaDB vector embeddings
- **Human-In-The-Loop (HITL)** metadata management
- **Pandas-based analysis** for structured data
- **Streamlit UI** for data ingestion and management

Two completely independent tools prevent cross-contamination of bugs:

1. **CSV Ingestion Tool** (`tools/csv_ingest_tool.py`) — Data loading and RAG indexing
2. **CSV Analysis Tool** (`tools/csv_analysis_tool.py`) — LLM-callable analysis operations

---

## Architecture

```
                    ┌─────────────────────────┐
                    │   Streamlit Frontend    │
                    │   (Upload, Manage)      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼────────┐      ┌────────▼──────┐
            │  CSV Ingest    │      │  CSV Analysis │
            │  Tool (plain   │      │  Tool (@tool) │
            │   function)    │      │  (LLM calls)  │
            └───────┬────────┘      └────────┬──────┘
                    │                        │
        ┌───────────┼────────────┬───────────┘
        │           │            │
    ┌───▼──┐   ┌────▼────┐  ┌───▼──────┐
    │ Disk │   │ChromaDB │  │ Metadata │
    │Files │   │  (RAG)  │  │  (JSON)  │
    └──────┘   └─────────┘  └──────────┘
```

---

## Ingestion Tool: `csv_ingest_tool.py`

### Features
- **File Support**: CSV, XLSX, XLS
- **RAG Chunking**: Splits dataframes into 50-row chunks for semantic search
- **Metadata Storage**: Tracks column types, statistics, user descriptions
- **Persistent Storage**: Files on disk, vectors in ChromaDB, metadata in JSON
- **HITL Feedback**: User can update descriptions after ingestion

### Key Functions

#### `ingest_file(file_bytes, file_name, dataset_name, user_description="")`
Ingests a file and stores it in RAG system.

**Returns:**
```python
{
    "status": "ok",
    "message": "Successfully ingested 250 rows into dataset 'sales_data'",
    "rows": 250,
    "columns": ["Date", "Region", "Sales", "Quantity"],
    "chunks_created": 5,
    "dataset_name": "sales_data",
    "numeric_columns": ["Sales", "Quantity"],
    "categorical_columns": ["Region"]
}
```

#### `list_datasets() → list[str]`
Returns all available dataset names.

#### `get_dataset_info(dataset_name) → dict`
Retrieves metadata about a dataset including:
- Row/column counts
- Data types
- User description
- Ingestion timestamp
- Column categorization

#### `search_dataset(dataset_name, query, n_results=5) → list[dict]`
RAG-based semantic search within a dataset.

**Example:**
```python
search_dataset("sales_data", "high performing regions", n_results=3)
# Returns: chunks of data most similar to the query
```

#### `update_dataset_description(dataset_name, new_description) → dict`
HITL: Update user description after initial ingestion.

#### `delete_dataset(dataset_name) → dict`
HITL: Clean up a dataset (removes files, vectors, metadata).

---

## Analysis Tool: `csv_analysis_tool.py`

### Features
- **LangChain @tool**: Directly callable by the LLM
- **Safe Operations**: Named operations only, no `exec()` or code generation
- **RAG-Aware**: Can use semantic search results alongside traditional pandas
- **Comprehensive**: 18+ analysis operations

### Key Function

#### `analyze_data(dataset_name, operation, params="")`
Main analysis tool called by the LLM.

### Supported Operations

| Operation | Params | Example | Notes |
|-----------|--------|---------|-------|
| `head` | N (rows) | `head,10` | First N rows |
| `tail` | N (rows) | `tail,5` | Last N rows |
| `describe` | — | `describe` | Statistical summary |
| `info` | — | `info` | Column info, dtypes, nulls |
| `shape` | — | `shape` | Rows × columns |
| `columns` | — | `columns` | List column names |
| `dtypes` | — | `dtypes` | Data type of each column |
| `value_counts` | column | `value_counts,Region` | Unique values in column |
| `groupby_sum` | group,value | `groupby_sum,Region,Sales` | Sum by group |
| `groupby_mean` | group,value | `groupby_mean,Region,Sales` | Mean by group |
| `groupby_count` | column | `groupby_count,Region` | Count by group |
| `filter` | query | `filter,Sales>1000` | Pandas query syntax |
| `correlation` | — | `correlation` | Correlation matrix |
| `unique` | — | `unique` | Count of unique values |
| `sort` | col,order,N | `sort,Sales,desc,10` | Top/bottom N rows |
| `null_count` | — | `null_count` | Null value counts |
| `sample` | N | `sample,10` | Random N rows |
| `rag_search` | query | `rag_search,best regions` | **Semantic search** |
| `dataset_info` | — | `dataset_info` | Metadata summary |

### RAG Search Example

```python
analyze_data(
    dataset_name='sales_data',
    operation='rag_search',
    params='Which regions had the highest sales?'
)
```

Returns relevant data chunks most similar to the query, allowing the LLM to draw insights.

---

## Streamlit UI (Frontend)

### Upload Section
1. **File Uploader**: Drag-and-drop CSV/Excel files
2. **Dataset Name**: Auto-filled from filename, user-editable
3. **Description**: Optional HITL metadata
4. **Feedback**: Shows chunk count, column types

### Dataset Management
Each dataset shows:
- **Metadata**: Row count, columns, data types
- **Current Description**: User-provided context
- **Update Description**: HITL feedback form
- **Delete Button**: Remove dataset and data

### Integration with Chat
After upload, ask the LLM questions:
- "What are the top 5 regions by sales in sales_data?"
- "Show me the average by region from sales_data"
- "Find customers with orders over $5000 in customers_data"
- "What's the correlation between price and quantity in sales_data?"

The LLM automatically calls `analyze_data` with appropriate operations.

---

## Folder Structure

```
chat-bot/
├── tools/
│   ├── csv_ingest_tool.py      ← Ingestion (plain functions)
│   ├── csv_analysis_tool.py    ← Analysis (@tool for LLM)
│   └── ...other tools
├── data/
│   ├── uploads/                ← CSV/Excel files
│   └── metadata/               ← JSON metadata files
├── chroma_db/                  ← ChromaDB persistent store (gitignored)
└── frontend.py                 ← Streamlit UI with HITL controls
```

---

## Bug Isolation & Testing

### Testing Ingestion Independently
```bash
python tools/csv_ingest_tool.py
```
Lists available datasets and their metadata.

### Testing Analysis Independently
```bash
python tools/csv_analysis_tool.py
```
Documents supported operations.

### Manual Testing Flow
1. **Upload** a CSV via Streamlit UI
2. **Update Description** to add context
3. **Ask the chatbot**: "Analyze [dataset_name]"
4. **Verify Results** in chat output
5. **Refine** via metadata updates

---

## Key Design Decisions

### Why Two Separate Tools?
- **Ingestion bugs** (file loading, chunking) don't break analysis
- **Analysis bugs** (pandas operations) don't affect data loading
- **Independent testing** and debugging
- **Clear separation of concerns**

### Why RAG + Pandas?
- **RAG** for semantic understanding ("high-value customers")
- **Pandas** for precise aggregations (groupby, sum, mean)
- **Combined**: LLM uses RAG to understand data, then calls pandas for exact results

### Why ChromaDB + Disk Files?
- **ChromaDB**: Semantic search on data chunks
- **Disk files**: Exact pandas operations on full dataset
- **Metadata JSON**: Human-readable audit trail of what was ingested

### Why HITL?
- Users can **add context** after upload
- Users can **manage** datasets (update, delete)
- Improves **LLM understanding** of domain-specific data
- Creates **audit trail** of data lineage

---

## Future Enhancements

1. **Data Profiling**: Auto-detect schema, outliers
2. **Visualization**: Auto-generate charts from analysis results
3. **Multi-file Joins**: Combine datasets for cross-analysis
4. **Data Versioning**: Track changes to datasets over time
5. **Custom Aggregations**: User-defined pandas operations
6. **Export**: Save analysis results to CSV/PDF
