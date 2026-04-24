# RAG (Retrieval Augmented Generation) Spec Sheet

## Purpose
Store and retrieve analysis insights via semantic search in ChromaDB.
Augments LLM responses with domain knowledge from past analyses.

## Architecture
- Vector DB: ChromaDB (data/chroma_db/)
- Embedding: Sentence transformers (default model)
- Storage: SQLite-backed ChromaDB for persistence
- Indexing: Automatic on ingest, semantic similarity on search

## Ingest Sources
- CSV analyst results (after HITL approval)
- SQL analyst results (after HITL approval)
- Monitor reports (automatic, no HITL)
- Uploaded documents (PDF, txt - future)

## Retrieval Flow
1. User asks: "find insights about wheat supply"
2. LLM calls csv_analyst or monitor tool with operation='rag_search'
3. Search query vectorized by embedding model
4. ChromaDB returns top 5 similar chunks
5. Chunk text + metadata returned to LLM context
6. LLM synthesizes response from retrieved docs + user query

## Metadata Structure
Each chunk stored with:
```
{
  "source": "csv_analysis | sql_analysis | monitor_report | document",
  "date": "2026-04-22T14:30:00",
  "type": "csv_analysis | sql_analysis | monitor | pdf | txt",
  "query": "original question or analysis task",
  "dataset": "name of dataset analyzed",
  "summary": "one-line summary"
}
```

## ChromaDB Path
`data/chroma_db/` - persistent collection storage
- Auto-created on first ingest
- Survives app restarts
- Can be backed up/migrated

## Cache Strategy
Redis (planned): 30-min TTL on rag_search results
- Caches query → results pairs
- Invalidates after 30 min or manual refresh
- Reduces duplicate embeddings

## Storage Limits
- Max chunk size: 1000 tokens (estimated)
- Max results: 5 per query (configurable)
- Retention: Indefinite (no auto-cleanup)
- Manual: delete_analysis(id) to remove chunks

## Integration Points
```python
# CSV analyst with HITL
results = analyze_data(dataset='sales', operation='describe')
user_confirms = HITL("Ingest these insights?")
if user_confirms:
    rag.ingest(results, source='csv', dataset='sales')

# Monitor reports (auto-ingest)
monitor_result = {timestamp, commodity, sentiment, price_change}
rag.ingest(monitor_result, source='monitor')  # No HITL

# Retrieval
results = rag_tool.invoke({'query': 'wheat supply trends'})
```

## RAG Tool (rag_tool.py - PLANNED)
```python
@tool
def rag_retriever(query: str, source_filter: str = "", num_results: int = 5) -> str:
    """
    Search ChromaDB for analysis insights.
    
    Args:
        query: Natural language search query
        source_filter: Optional filter (csv, sql, monitor, document)
        num_results: Number of results to return
    
    Returns: Formatted search results with source + metadata
    """
```

## Dependencies
- chromadb (pip: chromadb)
- sentence-transformers (pip: sentence-transformers) - embeddings
- langchain_core.tools (for @tool decorator)

## Chaining
With csv_analyst:
```
csv_analyst('sales', 'rag_search', 'regional performance 2026')
→ retrieves past analyses of regional sales patterns
```

With monitor_tool:
```
monitor_tool → generates insight → auto-stores in RAG
user queries: "wheat trends this month"
→ retrieves recent monitor reports + sentiment
```

## HITL Requirements
- CSV analysis ingest: User confirms insights are accurate before storing
- SQL analysis ingest: User confirms query results before storing
- Monitor reports: NO HITL (automatic storage for continuous monitoring)
- Manual deletion: User confirms before removing chunks

## Known Issues
- [PLANNED] Similarity thresholding (filter low-confidence results)
- [PLANNED] Duplicate detection (avoid storing same analysis twice)
- [PLANNED] TTL on old data (auto-archive after 90 days)

## Performance Notes
- First search: ~500ms (cold start)
- Subsequent: ~50ms (warm cache)
- Embedding: ~100ms per document chunk

## Security
- All data stored locally in data/chroma_db/
- No external embedding service calls
- Metadata never exposed to frontend (internal only)

## Testing
```python
from tools.rag_tool import rag_retriever
results = rag_retriever.invoke({
    'query': 'wheat price trends',
    'num_results': 5
})
```

## Bunge Relevance
Institutional knowledge base for commodity trading, combining historical analysis with real-time monitoring.
