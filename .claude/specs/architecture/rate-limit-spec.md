# Rate Limiting Architecture Specification

## Overview
Token-bucket rate limiter for external API calls to prevent rate limit violations and ensure smooth operation under load.

## Status
[DONE]

## Module
`utils/rate_limit.py`

## Design

### Mechanism
Token-bucket algorithm with minimum interval between calls:
- Tracks last call time per tool
- Sleeps if minimum interval hasn't elapsed
- Thread-safe via mutex lock

### Suggested Intervals
| Tool | Interval | Reason |
|------|----------|--------|
| web_search | 2.0s | DuckDuckGo soft limits |
| stock | 1.0s | yfinance API |
| commodity | 1.0s | CME data provider |
| calendarific | 1.0s | API quota |

## Usage

### In Tool Definition
```python
from utils.rate_limit import rate_limit
from langchain_core.tools import tool

@tool
def web_search(query: str, num_results: int = 5) -> str:
    rate_limit("web_search", 2.0)  # Max 1 call per 2 seconds
    # ... actual search logic ...
```

### Function Signature
```python
def rate_limit(key: str, min_interval_seconds: float) -> None:
    """Block until min_interval_seconds has passed since last call with this key."""
```

## Integration Points
- `tools/web_search_tool.py` → rate_limit("web_search", 2.0)
- `tools/stock_tool.py` → rate_limit("stock", 1.0)
- `tools/commodity_tool.py` → rate_limit("commodity", 1.0)
- `tools/calendarific_tool.py` → rate_limit("calendarific", 1.0)

## Benefits
- Prevents API rate limit errors
- Graceful degradation under load
- No external rate-limit library needed
- Operates within LLM tool invocations
