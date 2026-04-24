# Monitor Tool Detailed Spec

## Purpose
Background monitoring agent for commodity prices with sentiment-based alerting.
Runs independently in threads, does NOT block user chat.

## Internal Architecture

### 1. Monitoring Thread
```python
def _run_monitoring(commodity, interval_seconds, alert_callback, storage_callback, stop_event):
    while not stop_event.is_set():
        # Step 1: Fetch commodity price
        price = get_commodity_price(commodity)  # Blocking call
        
        # Step 2: Search for market news
        news = web_search(f"{commodity} price news")  # Blocking call
        
        # Step 3: Analyze sentiment
        sentiment = nlp_analyze(news, task='sentiment')  # Blocking call
        
        # Step 4: Check alert condition
        if sentiment == NEGATIVE and price_change < -1.5%:
            _send_alert(message, alert_callback)
        
        # Step 5: Log result
        _log_to_storage(commodity, result, storage_callback)
        
        # Wait for next interval
        stop_event.wait(interval_seconds)
```

### 2. Threading Model
- Global dict: `_monitoring_threads[commodity] = {thread, stop_event, started_at}`
- Global lock: `_monitoring_lock` (mutex for thread-safe access)
- Daemon threads: Exit when main app exits
- Thread-safe shutdown: `stop_event.set()` signals thread to clean exit

### 3. State Management
- `_monitoring_threads`: Active monitors (dict)
- `_monitoring_results`: Results history, per commodity (list of dicts)
- `_monitoring_lock`: Protects access to above

## Tool Definitions

### start_monitoring(commodity, interval_minutes=30)
```
Input:
  commodity: str (wheat, soy, corn, sugar, cotton, rice)
  interval_minutes: int = 30

Output:
  "[OK] Monitoring started for wheat (every 30 min)"

Side effects:
  - Creates thread: monitor-{commodity}
  - Starts background loop
  - Thread runs until stop_monitoring() called or app exits
```

### stop_monitoring(commodity)
```
Input:
  commodity: str

Output:
  "[OK] Monitoring stopped for wheat"

Side effects:
  - Sets stop_event
  - Thread gracefully exits
  - Thread removed from _monitoring_threads
```

### get_monitoring_results(commodity=None)
```
Input:
  commodity: str (optional, None → all commodities)

Output (single commodity):
  Results for wheat:
    - 2026-04-22T14:30:00: negative sentiment, -2.15% change
    - 2026-04-22T13:00:00: neutral sentiment, -0.50% change

Output (all commodities):
  Monitoring Results:
  
  WHEAT:
    Latest: 2026-04-22T14:30:00
    Sentiment: negative
    Price Change: -2.15%
  
  CORN:
    Latest: 2026-04-22T14:25:00
    Sentiment: positive
    Price Change: +1.50%
```

### get_active_monitors()
```
Input: None

Output:
  Active Monitors:
    - WHEAT (started: 2026-04-22T14:00:00)
    - CORN (started: 2026-04-22T13:30:00)
```

## Alert Condition
```
if sentiment == "negative" AND price_change_pct < -1.5%:
    trigger_alert()
```

Alert message format:
```
[ALERT] COMMODITY ALERT [ALERT]
Commodity: WHEAT
Sentiment: NEGATIVE
Price Change: -2.15%
Time: 2026-04-22T14:30:00
Details: [search result snippet]
```

## Extensibility: Callbacks

### Alert Callback
```python
def custom_alert_handler(message: str):
    # Send to Slack, email, database, etc.
    pass

start_monitoring('wheat', alert_callback=custom_alert_handler)
```

### Storage Callback
```python
def custom_storage_handler(commodity: str, result: dict):
    # Store in ChromaDB, MySQL, S3, etc.
    pass

start_monitoring('wheat', storage_callback=custom_storage_handler)
```

Default behavior: Log to in-memory _monitoring_results dict.

## Limitations & Fixes
| Issue | Current | Planned |
|-------|---------|---------|
| Data persistence | In-memory only | Redis + ChromaDB |
| Storage | _monitoring_results dict | SQL table |
| Price parsing | Regex fragile | Structured return from commodity_tool |
| Alerting | Logging only | Slack webhook + Email callbacks |
| Sentiment source | Web search only | News APIs + RSS feeds |
| Manual reporting | Results query tool | Daily 09:00 consolidated report |

## Testing
```python
# Start monitoring
result = start_monitoring.invoke({
    'commodity': 'wheat',
    'interval_minutes': 1  # Test every 1 min
})
print(result)  # "[OK] Monitoring started..."

# Check active
active = get_active_monitors.invoke({})
print(active)  # "WHEAT (started: ...)"

# Let it run for 2+ minutes
time.sleep(130)

# Get results
results = get_monitoring_results.invoke({'commodity': 'wheat'})
print(results)  # Should have 2+ entries

# Stop
stop = stop_monitoring.invoke({'commodity': 'wheat'})
print(stop)  # "[OK] Monitoring stopped..."
```

## Performance Notes
- Interval 30 min = ~48 checks/day per commodity
- Per check: ~2 sec (search + sentiment + price)
- Thread time: ~20% CPU usage while checking, <1% idle
- Memory: ~10MB per monitor thread + results dict

## Bunge Relevance
24/7 commodity price surveillance with automated alerts for trading operations.
