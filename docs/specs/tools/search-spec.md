# Web Search Spec Sheet

## Purpose
Search the web in real-time using DuckDuckGo.
Retrieve current news, events, and up-to-date information.
No API key required - completely free.

## Status
[DONE]

## Trigger Phrases
- "search for latest AI news"
- "find information about climate change"
- "what's new in technology"
- "search wheat prices today"
- "latest news on commodity markets"

## Input Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | str | yes | none | Search query term(s) |
| num_results | int | no | 5 | Number of results (1-10) |

## Output Format
Search Results for: 'wheat prices today'
============================================================
Top 5 Results:
------------------------------------------------------------

1. Wheat Price Today - USDA Report
   URL: https://www.usda.gov/...
   Summary: Current wheat futures trading at $7.25/bu, up 0.5% from yesterday...

2. Global Wheat Market Outlook
   URL: https://market.example.com/...
   Summary: Analysts predict continued volatility due to weather patterns...

## Dependencies
- ddgs (pip: duckduckgo-search)
- langchain_core.tools

## HITL
No - read-only search, no action

## Chaining
Combines with:
- nlp_tool → "search for wheat news and analyze sentiment"
- monitor_tool → "search commodity prices and alert on changes"

## Known Issues
- Results clamped to 1-10 range
- DDGS may occasionally rate-limit; error handling catches exceptions
- Snippet truncated to 200 chars max

## Test Command
python -c "
from tools.web_search_tool import web_search
print(web_search.invoke({'query': 'wheat prices', 'num_results': 5}))
"

## Bunge Relevance
Real-time market intelligence for agricultural commodities and price discovery.

## Internal Notes
- Uses DDGS() from duckduckgo_search for DuckDuckGo API
- Returns title, href, body from each result
- Handles empty queries and clamps num_results
- Output: formatted text list with separators
