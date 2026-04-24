# Data Pipeline Specification

## Purpose
Background data processing: CSV upload → analysis → RAG ingest.
Orchestrates multi-step workflows independently of user chat.

## Pipeline Stages

### Stage 1: CSV Upload & Validation
```
User uploads CSV file
  ↓
Frontend validates file type (.csv, .xlsx, .xls)
  ↓
Backend saves to data/uploads/{filename}
  ↓
Returns: upload_id, rows, columns, sample data
```

### Stage 2: Analysis
```
User runs: analyze_data(dataset='sales', operation='describe')
  ↓
Backend loads CSV from data/uploads/
  ↓
Executes analysis operation (statistics, groupby, etc.)
  ↓
Returns formatted results to user
```

### Stage 3: HITL Approval
```
User reviews analysis results
  ↓
Clicks: "Store this in knowledge base"
  ↓
HITL modal appears with approval prompt
  ↓
User confirms accuracy + relevance
```

### Stage 4: RAG Ingest
```
User approves
  ↓
Results processed into chunks
  ↓
Chunks embedded (Sentence Transformers)
  ↓
Stored in ChromaDB (data/chroma_db/)
  ↓
Indexed for semantic search
```

### Stage 5: Future Queries
```
User asks: "What were the top regions last month?"
  ↓
LLM calls: rag_retriever(query='top regions last month')
  ↓
ChromaDB returns similar past analyses
  ↓
LLM synthesizes response from retrieved docs
```

## Directory Structure
```
pipelines/
  __init__.py
  data_pipeline.py           main orchestration
  csv_pipeline.py            CSV upload → analysis → RAG
  sql_pipeline.py            SQL ingest → query → RAG
  monitor_pipeline.py        commodity monitor → alerts → RAG
  
data/
  uploads/                   CSV/Excel files
    sales.csv
    inventory.xlsx
  chroma_db/                 ChromaDB vector store
    index/
    metadata/
  databases/
    analytics.db             SQLite
    registry.json            DB registry
  plots/                     Generated visualizations
    sales_histogram.png
    sales_heatmap.png
```

## Pipeline Execution

### Synchronous (User-triggered)
```python
# User in chat: "analyze sales data"
# LLM calls analyze_data(operation='describe')
# Execution: ~2 sec (pandas operations)
# Result returned immediately to user
```

### Asynchronous (HITL + Ingest)
```python
# User approves HITL → "Store insights"
# Backend queues ingest operation
# Execution: ~1 sec (embedding + ChromaDB store)
# Notification when complete
```

### Background (Monitor + Report)
```python
# Monitor thread runs continuously
# Every 30 min: check commodity price, sentiment, alert
# Daily 09:00: generate consolidated report
# Auto-ingest to RAG (no HITL)
```

## Data Flow Diagram
```
CSV Upload
    ↓
[Validate] → Reject if invalid
    ↓
Save to data/uploads/
    ↓
User triggers: analyze_data()
    ↓
[Analysis] (pandas operations)
    ↓
Display results to user
    ↓
User: "Store this?"
    ↓
[HITL] User confirms
    ↓
Process into chunks
    ↓
[Embedding] (Sentence Transformers)
    ↓
[Store in ChromaDB]
    ↓
Done. Indexed for future retrieval.

Monitor Thread
    ↓
[Every 30 min]
    ↓
Fetch commodity price
    ↓
Web search news
    ↓
NLP sentiment analysis
    ↓
Check alert: negative + drop > 1.5%
    ↓
[If triggered] Send alert
    ↓
Store result in _monitoring_results
    ↓
[Daily 09:00] Generate consolidated report
    ↓
Auto-ingest to RAG
```

## Configuration

### data_pipeline.py
```python
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
CHROMA_DB_PATH = Path(__file__).parent.parent / "data" / "chroma_db"
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
```

### Monitor Schedule (APScheduler planned)
```python
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=commodity_monitor,
    trigger="interval",
    minutes=30,
    args=['wheat']
)
scheduler.add_job(
    func=daily_report,
    trigger="cron",
    hour=9,
    minute=0
)
scheduler.start()
```

## Error Handling
| Error | Handling |
|-------|----------|
| Invalid file type | Reject, suggest valid types |
| File too large | Reject, suggest smaller file |
| Corrupted CSV | Return parse error + line number |
| Analysis fails | Return error details to user |
| HITL timeout | Auto-reject after 24 hours |
| ChromaDB unavailable | Fall back to in-memory storage, warn user |
| Embedding fails | Retry 3x, skip if persistent |

## Performance Targets
- CSV upload: < 100MB files
- Analysis: < 5 sec for 1M rows
- HITL approval: < 1 min typical
- Ingest: < 2 sec per 100 chunks
- RAG search: < 500ms cold start, < 50ms cached

## Monitoring & Debugging
```bash
# Check pipeline health
curl http://localhost:8000/pipeline/status

# Get pipeline logs
tail -f logs/pipeline.log

# Monitor ChromaDB
sqlite3 data/chroma_db/chroma.db ".tables"
```

## Future Enhancements
1. Parallel ingest (multi-threaded embedding)
2. Incremental updates (only re-analyze changed rows)
3. Pipeline versioning (track analysis versions)
4. Cost tracking (token usage, API calls)
5. Alerting for pipeline failures

## Bunge Relevance
End-to-end data workflow: commodities data → insights → knowledge base for trading decisions.
