# HITL (Human In The Loop) Spec Sheet

## Purpose
Ensure critical operations require user review and approval before execution.
Prevents unintended data loss, sends, or deletes.

## HITL Requirements by Operation

### Always HITL (Every Time)
- **Gmail send**: User confirms recipient, subject, body before sending
- **SQL DELETE**: User confirms WHERE clause and row count before deletion
- **SQL UPDATE**: User confirms SET clause and row count before update
- **CSV ingest to RAG**: User confirms analysis quality before storing
- **SQL analysis ingest to RAG**: User confirms query + results before storing
- **Admin commands**: Database reset, config changes, tool reloading

### Never HITL (Background)
- **SQL SELECT**: Read-only, no risk
- **CSV/SQL describe**: Read-only schema inspection
- **Stock/commodity prices**: Read-only market data
- **Web search**: Read-only external API
- **NLP analysis**: Read-only text processing
- **Monitor alerts**: Automatic background thread (time-sensitive)
- **Monitor report (daily 09:00)**: Auto-scheduled, no HITL

### Conditional HITL
- **CSV draft creation**: User can create without HITL, but only HITL send
- **CSV preview**: No HITL for preview, HITL for ingest
- **Monitor callback**: No HITL in background, HITL only if user manually requests "report now"

## HITL Flow Architecture

### Frontend (Streamlit)
```
User executes command
  ↓
LLM processes → identifies HITL requirement
  ↓
Backend returns: {
  "status": "pending_approval",
  "operation": "send_email",
  "params": {to, subject, body},
  "preview": "Email to john@example.com: Monthly Report"
}
  ↓
Frontend displays modal/confirmation UI
  ↓
User clicks: [APPROVE] [CANCEL] [EDIT]
  ↓
Frontend sends: {approved: true, edited_params: {...}}
  ↓
Backend executes operation
  ↓
Frontend displays result
```

### Backend Integration
```python
# In tool or subgraph:
def send_email_with_hitl(to, subject, body):
    # Prepare parameters
    pending = {
        "status": "pending_approval",
        "operation": "send_email",
        "params": {"to": to, "subject": subject, "body": body},
        "preview": f"Send email to {to}: {subject}"
    }
    
    # Yield to frontend for HITL
    yield pending  # Requires user approval in Streamlit
    
    # User approved (or edited params)
    # Execute operation
    send_email(**pending["params"])
    
    return "Email sent successfully"
```

### Streamlit UI Patterns
```python
# In frontend.py - handle HITL responses from backend
if response.get("status") == "pending_approval":
    operation = response["operation"]
    params = response["params"]
    preview = response["preview"]
    
    st.warning(f"APPROVAL REQUIRED: {operation}")
    st.text_area("Preview:", value=preview, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve"):
            # Send approval to backend with current params
            ...
    with col2:
        if st.button("Cancel"):
            st.info("Operation cancelled")
```

## Tool Requirements

### Gmail Tool
```python
@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Requires HITL approval before sending.
    
    Yields:
    {
        "status": "pending_approval",
        "operation": "send_email",
        "params": {"to": to, "subject": subject, "body": body},
        "preview": f"Email to {to}"
    }
    """
    # Yield pending for HITL
    # Upon approval, execute send
```

### SQL Tool
```python
@tool
def analyze_sql(query_type: str, ...):
    if query_type == 'delete':
        # Count rows first
        count = get_row_count(...)
        
        # Yield HITL
        yield {
            "status": "pending_approval",
            "operation": "delete",
            "params": {"table": table_name, "condition": where},
            "preview": f"Delete {count} rows from {table_name}?"
        }
        
        # Upon approval, execute delete
    elif query_type == 'update':
        # Similar HITL flow
        ...
```

### CSV Ingest
```python
@tool
def ingest_csv_to_rag(dataset: str, analysis_results: dict):
    # User ran CSV analysis
    # Now requests to ingest to RAG
    
    yield {
        "status": "pending_approval",
        "operation": "ingest_rag",
        "params": {"dataset": dataset, "results": analysis_results},
        "preview": f"Store analysis of {dataset}: {len(results)} insights"
    }
    
    # Upon approval, call rag.ingest()
```

## Interrupt Mechanism (Backend)

### Option 1: Generator-based (Current)
Tools yield pending approval, wait for user response.
Streamlit handles yield → input → resume.

```python
def operation_with_hitl():
    yield {"status": "pending_approval", ...}
    # Waits here for user response
    # Resume execution after approval
```

### Option 2: LangGraph Subgraph (Planned)
Dedicated subgraph node for HITL decisions.

```python
from langgraph.graph import StateGraph

def hitl_node(state):
    if state.requires_hitl:
        return {"status": "pending_approval", "params": ...}
    return {"approved": True}

graph.add_edge("hitl_node", conditional_approve)
```

## Admin Overrides
For non-production/testing:

```python
# Environment variable to skip HITL
SKIP_HITL=false  # default: require all HITL
SKIP_HITL=true   # dangerous: skip all confirmations
```

Or per-operation:
```python
send_email(..., skip_hitl=True)  # Skip only this operation
```

## Audit Logging
All HITL decisions logged:
```
[2026-04-22 14:30:15] Operation: send_email
[2026-04-22 14:30:15] Params: {to: john@example.com, subject: Report}
[2026-04-22 14:30:20] Result: APPROVED
[2026-04-22 14:30:21] Execution: Success
```

## Testing HITL Flows
```python
# Test HITL approval
response = send_email_with_hitl(...)
assert response["status"] == "pending_approval"

# Simulate user approval
response_approved = approve_operation(response)
assert response_approved["status"] == "sent"

# Test cancellation
response_cancel = cancel_operation(response)
assert response_cancel["status"] == "cancelled"
```

## Bunge Relevance
Compliance requirement: Audit trail of all automated trades, alerts, and data modifications.
