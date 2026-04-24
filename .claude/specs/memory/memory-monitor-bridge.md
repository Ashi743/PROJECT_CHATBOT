# TOOL SPEC: Monitor-to-Memory Bridge (`monitoring/memory_bridge.py`)

## Purpose
Connect monitoring system to memory system. When monitors detect events (commodity alerts, API issues, etc.), automatically update user memory.

---

## Implementation Notes

Reference `integrated-memory-spec.md` section 10 for monitor-to-memory bridge implementation.

## Module Should Include

### Main Function
```python
async def store_monitor_event(
    user_id: str,
    session_id: str,
    event: MonitorEvent
) -> dict:
    """
    Store a monitoring event as episodic memory.
    Called when monitor detects a noteworthy event.

    Args:
        user_id: User whose memory to update
        session_id: Current session ID
        event: MonitorEvent from monitoring system

    Returns:
        {status: "ok", doc_id: "..."} or {status: "error", message: "..."}
    """
```

### Sync Wrapper for Streamlit
```python
def sync_store_monitor_event(
    user_id: str,
    session_id: str,
    event: MonitorEvent
) -> dict:
    """Sync wrapper for Streamlit compatibility"""
```

---

## Event Flow

1. **Monitor detects something**
   - Commodity alert: wheat price surge
   - API down: connectivity issue
   - Database error: storage problem

2. **Create MonitorEvent**
   ```python
   event = MonitorEvent(
       event_type="commodity_alert",
       severity="alert",
       message="Wheat price surged 15%",
       timestamp=datetime.now(timezone.utc),
       commodities=["wheat"]
   )
   ```

3. **Convert to episodic doc**
   ```python
   doc = event.to_episodic_doc(user_id, session_id)
   # doc.document = "[ALERT] commodity_alert: Wheat price surged 15%"
   ```

4. **Store in ChromaDB**
   ```python
   await save_episodic(doc)
   ```

5. **Update semantic memory**
   - If commodity alert, add to `commodity_interests`
   - If API down, mark `api_health_checks`
   - Update `last_monitor_alert` timestamp

---

## Event-to-Update Mapping

### Commodity Alert → Semantic Update
```python
if event.event_type == "commodity_alert" and event.commodities:
    sem = await load_semantic(user_id)
    
    # Add commodities to user's interests
    existing = set(sem.commodity_interests or [])
    for comm in event.commodities:
        existing.add(comm)
    
    updates = {
        "commodity_interests": list(existing),
        "last_monitor_alert": datetime.now(timezone.utc).isoformat()
    }
    await update_semantic(user_id, updates)
```

### API Down → Semantic Update
```python
if event.event_type == "api_down":
    updates = {
        "api_health_checks": True,  # User now monitors API health
        "last_monitor_alert": datetime.now(timezone.utc).isoformat()
    }
    await update_semantic(user_id, updates)
```

### Storage Issue → Episodic Only
```python
if event.event_type == "storage_issue":
    # Just store as episodic memory
    # Don't update semantic (not user-actionable)
    await save_episodic(doc)
```

---

## Integration with Monitoring Runner

In `monitoring/runner.py`, add callbacks:

```python
from monitoring.memory_bridge import sync_store_monitor_event

def run_selected_checks(selections, user_id="default_user", session_id=None):
    """Run checks and auto-update memory"""
    results = {}
    
    for check_name in selections:
        results[check_name] = _run_check(check_name)
        
        # Convert results to monitor events
        if MONITOR_MEMORY_ENABLED:
            events = _extract_events(check_name, results[check_name])
            
            for event in events:
                sync_store_monitor_event(user_id, session_id, event)
    
    return results
```

---

## Example: Commodity Monitor Integration

**Monitor detects**: Wheat price +15%

**Code**:
```python
# In monitoring/checks.py or similar
def check_commodities():
    wheat_data = yfinance.Ticker("ZWZ23")
    change = (wheat_data.current_price - wheat_data.prev_close) / wheat_data.prev_close
    
    if change > 0.10:  # 10% threshold
        event = MonitorEvent(
            event_type="commodity_alert",
            severity="alert" if change > 0.15 else "warning",
            message=f"Wheat price surge {change*100:.1f}%",
            timestamp=datetime.now(timezone.utc),
            commodities=["wheat"]
        )
        result = sync_store_monitor_event(user_id, session_id, event)
        logger.info(f"Commodity alert stored: {result}")
    
    return {"status": "[ALERT]", "change": change}
```

**Memory updates**:
- Episodic: `EpisodicDoc(type="monitor_event", document="[ALERT] commodity_alert: Wheat price surge 15.2%")`
- Semantic: `commodity_interests = ["wheat", ...]`
- Semantic: `last_monitor_alert = 2025-04-24T15:30:45Z`

**Next chat**: LLM retrieves memory → aware of wheat monitoring

---

## Implementation Pattern

```python
async def store_monitor_event(user_id, session_id, event):
    """Store event → update memory"""
    try:
        # Step 1: Convert to episodic doc
        doc = event.to_episodic_doc(user_id, session_id)
        
        # Step 2: Save to ChromaDB
        await save_episodic(doc)
        
        # Step 3: Update semantic if applicable
        if event.event_type == "commodity_alert" and event.commodities:
            sem = await load_semantic(user_id)
            existing = set(sem.commodity_interests or [])
            existing.update(event.commodities)
            
            updates = {
                "commodity_interests": list(existing),
                "last_monitor_alert": event.timestamp.isoformat()
            }
            await update_semantic(user_id, updates)
        
        logger.info(f"Monitor event stored: {doc.doc_id}")
        return {"status": "ok", "doc_id": doc.doc_id}
    
    except Exception as e:
        logger.error(f"Failed to store monitor event: {e}")
        return {"status": "error", "message": str(e)}
```

---

## Configuration

From `memory/config.py`:

```python
# When monitors detect events, store with this importance
MONITOR_EVENT_IMPORTANCE = 0.7

# Enable/disable monitor → memory updates globally
MONITOR_MEMORY_ENABLED = True
```

Set `MONITOR_MEMORY_ENABLED=false` in `.env` to disable without code changes.

---

## Error Handling

```python
async def store_monitor_event(user_id, session_id, event):
    try:
        # Store event
        doc = event.to_episodic_doc(user_id, session_id)
        await save_episodic(doc)
        
        # Update semantic
        if event.event_type == "commodity_alert":
            await update_semantic(user_id, {...})
    
    except ChromaError as e:
        logger.error(f"ChromaDB error: {e}")
        return {"status": "error", "message": "Database unavailable"}
    
    except RedisError as e:
        logger.error(f"Redis error: {e}")
        # Continue anyway; episodic memory is critical
        return {"status": "partial", "message": "Semantic update failed but episodic saved"}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "message": str(e)}
```

---

## Testing

```python
def test_commodity_alert_to_memory():
    user_id = "test_user"
    session_id = "test_session"
    
    event = MonitorEvent(
        event_type="commodity_alert",
        severity="alert",
        message="Wheat surge 15%",
        timestamp=datetime.now(timezone.utc),
        commodities=["wheat"]
    )
    
    # Store event
    result = sync_store_monitor_event(user_id, session_id, event)
    assert result["status"] == "ok"
    
    # Verify episodic memory
    doc = sync_load_episodic(user_id, result["doc_id"])
    assert doc.type == "monitor_event"
    assert "[ALERT]" in doc.document
    
    # Verify semantic memory
    sem = sync_load_semantic(user_id)
    assert "wheat" in sem.commodity_interests
```

---

## Notes

- Non-blocking: monitor events update memory asynchronously
- Graceful degradation: memory unavailability doesn't break monitoring
- Semantic updates are event-type specific (commodity → interests, API → health_checks)
- Next chat automatically retrieves updated memory
