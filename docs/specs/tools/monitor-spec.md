# Monitor Tool Spec Sheet

## Purpose
Real-time background monitoring of commodity prices with sentiment analysis.
Runs in background threads, monitors web news + NLP sentiment + price changes.
Triggers alerts on NEGATIVE sentiment + price drop > 1.5%.

## Status
[DONE]

## Trigger Phrases
- "start monitoring wheat"
- "monitor corn every 30 minutes"
- "what's being monitored"
- "stop monitoring soy"
- "show me monitoring results for wheat"

## Input Parameters (by tool)

### start_monitoring
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| commodity | str | yes | none | Commodity to monitor (wheat, soy, corn, sugar, cotton, rice) |
| interval_minutes | int | no | 30 | Check interval in minutes |

### stop_monitoring
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| commodity | str | yes | Commodity to stop monitoring |

### get_monitoring_results
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| commodity | str | no | Specific commodity, or None for all |

### get_active_monitors
No parameters required

## Output Format
[OK] Monitoring started for wheat (every 30 min)

[OK] Monitoring stopped for wheat

Results for wheat:
  - 2026-04-22T14:30:00: positive sentiment, +1.25% change
  - 2026-04-22T13:45:00: neutral sentiment, -0.50% change
  - 2026-04-22T13:00:00: negative sentiment, -2.15% change

Active Monitors:
  - WHEAT (started: 2026-04-22T14:00:00)
  - CORN (started: 2026-04-22T13:30:00)

## Monitoring Flow
1. get_commodity_price → fetch current price
2. web_search → search for market news
3. nlp_analyze → extract sentiment from news
4. Check alert condition: NEGATIVE sentiment AND price drop > 1.5%
5. Store result in memory (_monitoring_results)
6. Optional: Send alert via callback

## Internal Monitoring Loop
Each interval:
- Parse sentiment from NLP result (POSITIVE/NEGATIVE/NEUTRAL)
- Parse price change % from commodity price output
- Log result with timestamp, commodity, sentiment, price_change
- Trigger alert if: sentiment == negative AND price_change < -1.5%
- Sleep until next interval

## Dependencies
- threading (Python stdlib)
- web_search (internal tool)
- commodity_tool (internal tool)
- nlp_tool (internal tool)
- langchain_core.tools

## HITL
No for background monitoring
YES for manual reporting (alert_callback requires user action)

## Chaining
Combines with:
- commodity_tool → source of price data
- nlp_tool → source of sentiment
- web_search → source of market news

## Known Issues
- Results stored in memory only (lost on app restart)
- No persistence to ChromaDB yet
- No email/Slack alerting in base version (extensible via callbacks)
- Parsing price_change_pct from commodity output is fragile (regex-based)

## Test Command
python -c "
from tools.monitor_tool import start_monitoring, get_active_monitors
print(start_monitoring.invoke({'commodity': 'wheat', 'interval_minutes': 30}))
print(get_active_monitors.invoke({}))
"

## Bunge Relevance
24/7 commodity price monitoring with automated sentiment-based alerts for trading operations.

## Internal Notes
- Uses threading.Thread (daemon=True) for background monitoring
- _monitoring_lock for thread-safe access to _monitoring_threads dict
- stop_event (threading.Event) for clean shutdown
- Alert message format: [ALERT] COMMODITY ALERT [ALERT] with commodity, sentiment, price_change, timestamp
- _send_alert can be extended: currently logs, can call custom callback
- _log_to_storage can persist to ChromaDB (callback-based)
- Stores last 10 results per commodity in _monitoring_results
