# C-RAG + Self-RAG System

Complete implementation of **Corrective RAG** (C-RAG) + **Self-Reflective RAG** (Self-RAG) with dual-layer quality control.

## Architecture

```
User Query
    ↓
[PHASE 1] RETRIEVE → ChromaDB (k=4 documents)
    ↓
[PHASE 2] GRADE [C-RAG] → Document Relevance (Prompt 1)
    ↓
    ├─ All docs irrelevant? → Web Search Fallback (DuckDuckGo)
    └─ Relevant docs found? → Continue
    ↓
[PHASE 3] GENERATE → Answer from context (Prompt 2)
    ↓
[PHASE 4] HALLUCINATION CHECK [Self-RAG] → Is grounded? (Prompt 3)
    ├─ YES → Continue to usefulness check
    └─ NO → Re-retrieve (max 3 loops)
    ↓
[PHASE 5] USEFULNESS CHECK [Self-RAG] → Answers question? (Prompt 4)
    ├─ YES → Return answer ✓
    └─ NO → Regenerate (max 3 loops)
    ↓
Final Answer + Metrics
```

## Features

✓ **Dual-Layer Quality Control**
- C-RAG: Document relevance grading before generation
- Self-RAG: Hallucination & usefulness checks after generation

✓ **Multi-Format Support**
- PDF files
- Word documents (.docx, .doc)
- CSV files
- Excel spreadsheets (.xlsx, .xls)

✓ **Automatic Web Search Fallback**
- DuckDuckGo integration
- Triggered when all indexed documents irrelevant

✓ **Loop Control**
- Max 3 retrieval loops (hallucination detection)
- Max 3 generation loops (usefulness check)
- 30-second timeout per query

✓ **OpenAI Integration**
- Uses GPT-4o-mini (cost-effective)
- Deterministic grading (temperature=0)

## Usage

### 1. Upload Documents (Frontend)

In the Streamlit UI:
1. Expand "📄 Upload Documents (C-RAG + Self-RAG)"
2. Choose a PDF, Word, CSV, or Excel file
3. Enter document name
4. Click "Upload to RAG"
5. Document is indexed to ChromaDB

### 2. Query Documents (Chat)

Ask the chatbot questions about your documents:
```
"What is the main topic of the document?"
"Summarize the key findings"
"What are the risks mentioned?"
```

The system will:
- Retrieve relevant chunks from ChromaDB
- Grade for relevance
- Generate grounded answer
- Check for hallucinations
- Verify usefulness

### 3. Programmatic Usage

```python
from tools.RAG.self_rag_tool import self_rag_query, unified_rag_pipeline
from tools.RAG.retriever import save_document_to_chroma

# Upload document
result = save_document_to_chroma("path/to/document.pdf", "My Document")

# Query with full pipeline
pipeline_result = unified_rag_pipeline("What is in the document?")
print(pipeline_result["answer"])
print(pipeline_result["metrics"])

# Use as LangChain tool
response = self_rag_query("Your question here")
```

## Configuration

### `graders.py`
- Model: `gpt-4o-mini`
- Temperature: `0` (deterministic)
- Max tokens: `100` (grading), `1000` (generation)

### `retriever.py`
- Vector DB: ChromaDB
- Embeddings: OpenAI text-embedding-3-small
- Path: `data/chroma_db/`

### `self_rag_tool.py`
- Max loops: 3
- Timeout: 30 seconds
- Web search: DuckDuckGo

## Prompts

### Prompt 1: Document Relevance [IsRel]
Evaluates if a retrieved document is relevant to the question (strict grading).

### Prompt 2: Answer Generation
Generates answer using ONLY provided context (no hallucination).

### Prompt 3: Hallucination Check [IsSup]
Verifies every claim in the answer comes from the documents.

### Prompt 4: Usefulness Check [IsUse]
Confirms the answer adequately addresses the user's question.

## Output Metrics

```json
{
  "answer": "Generated answer...",
  "metrics": {
    "retrieval_loops": 1,
    "generation_retries": 0,
    "total_loops": 1,
    "response_time": 2.34,
    "web_search_triggered": false,
    "success": true
  }
}
```

## Testing

```bash
python tool_testing/test_self_rag.py
```

Tests:
- RAG pipeline execution
- Tool integration
- Document indexing
- ChromaDB retrieval

## Performance

| Metric | Typical | Best | Worst |
|--------|---------|------|-------|
| Latency (1 loop) | 2-3s | 1s | 5s |
| Token usage | 3-4k | 1k | 8k |
| Retrieval loops | 1 | 1 | 3 |
| Generation retries | 0-1 | 0 | 3 |

## Error Handling

- **No documents indexed**: Falls back to web search
- **Web search fails**: Returns error with fallback message
- **Hallucination detected**: Re-retrieves documents (up to 3 times)
- **Answer not useful**: Regenerates (up to 3 times)
- **Timeout**: Returns best attempt with timeout flag

## Integration with Backend

The tool is automatically available as `self_rag_query` when bound to the LLM:

```python
from tools.RAG.self_rag_tool import self_rag_query
# Already integrated in backend.py
```

## Future Enhancements

- Adaptive loop limits based on query complexity
- Redis caching for repeated queries
- Token tracking and cost optimization
- Confidence scores instead of binary grading
- Multi-provider web search
- Conversation memory (multi-turn RAG)
