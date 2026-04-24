# Redis Caching Spec Sheet

## Purpose
Cache repeated tool results to reduce:
- Token usage (LLM API costs)
- Latency (instant response for repeated queries)
- External API calls (reduce rate limiting)

## Cache Strategy by Tool
Tool results cached with TTL:

| Tool | TTL | Rationale |
|------|-----|-----------|
| commodity_price | 900s (15 min) | Prices update intraday, 15-min stale acceptable |
| stock_price | 900s (15 min) | Market data updates during trading hours |
| web_search | 1800s (30 min) | News/content stable for 30 min windows |
| get_india_time | 0s (no cache) | Changes every second, no point caching |
| calculator | 0s (no cache) | Pure function, no repeated calls valuable |
| nlp_analyze | 3600s (1 hr) | Text analysis stable, rarely repeated |
| rag_retriever | 1800s (30 min) | Embedding-based, stable results |
| get_monitoring_results | 300s (5 min) | Results updated by monitor thread |

## What to Cache
- Tool invoke() call results
- LLM model inference outputs
- API responses (stock prices, commodity futures)
- Search results (web, RAG)

## What NOT to Cache
- Chat message history (ephemeral)
- User inputs (unique queries)
- HITL confirmations (user action, not repeated)
- File uploads (one-time operations)
- Monitoring alerts (time-sensitive)

## Implementation: cache_tool() Decorator
Location: `utils/cache.py`

```python
from utils.cache import cache_tool

@cache_tool(ttl=900)
def get_commodity_price(commodity: str) -> str:
    # Function body unchanged
    ...
```

Decorator wraps tool to:
1. Hash input parameters → cache key
2. Check Redis for key (if exists + not expired → return)
3. If cache miss → execute function
4. Store result in Redis with TTL
5. Return result

## Redis Setup
Install: `pip install redis`

Start Redis (Docker):
```bash
docker run -d -p 6379:6379 redis:latest
```

Or local installation:
- Windows: WSL2 + redis-server, or Docker Desktop
- Mac: `brew install redis` + `redis-server`
- Linux: `sudo apt install redis-server` + `redis-server`

Environment:
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # optional
```

## Cache Key Format
```
{tool_name}:{param1}={value1}:{param2}={value2}
```

Examples:
```
commodity_price:commodity=wheat
stock_price:symbol=AAPL
web_search:query=wheat prices:num_results=5
```

## Invalidation Strategy
1. **TTL-based**: Automatic expiry per tool config
2. **Manual**: Clear specific key via admin command
3. **Pattern**: Clear all keys matching pattern (e.g., all commodity_* on market close)

```python
redis_client.delete(key)  # Single key
redis_client.delete_pattern("commodity_*")  # Pattern
redis_client.flushdb()  # Clear entire cache (careful!)
```

## Metrics to Monitor
- Cache hit rate (should be 20-50% after warmup)
- Cache size (should stay < 100MB for typical usage)
- Stale data incidents (ttl too long → wrong results)
- False negatives (ttl too short → cache thrashing)

## Branch & Timeline
**Branch**: feat/redis-caching
**Timing**: After feat/pipeline-monitor merged to main
**Order**:
1. Implement cache_tool() decorator
2. Apply to commodity_price, stock_price (high volume)
3. Apply to web_search (reduces DuckDuckGo calls)
4. Monitor metrics
5. Apply to nlp_analyze (expensive operation)

## Performance Impact
Without caching:
- commodity_price: 1-2 sec per call (yfinance + formatting)
- stock_price: 1-2 sec
- web_search: 2-3 sec (DDGS)

With caching (hit):
- All tools: <10ms (Redis lookup + return)

Estimated savings (100 user queries/day):
- 20% hit rate = 20 cache hits × 1.5 sec = 30 sec saved
- Token usage: ~200K tokens/day → ~160K with cache = -20% savings
- Cost impact: ~$0.30/day saved per 100 queries

## Testing
```python
from tools.commodity_tool import get_commodity_price

# First call → cache miss, slow
result1 = get_commodity_price.invoke({'commodity': 'wheat'})

# Second call (within 15 min) → cache hit, fast
result2 = get_commodity_price.invoke({'commodity': 'wheat'})

# Different param → cache miss
result3 = get_commodity_price.invoke({'commodity': 'corn'})
```

## Security Notes
- Cache keys are deterministic hashes (safe)
- Sensitive data (user emails, tokens) NOT cached
- Redis ACLs should restrict access to localhost only
- No password needed for local-only access

## Bunge Relevance
Reduce API costs for commodity price feeds, improve response time for trading decisions.
