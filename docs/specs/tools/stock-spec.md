# Stock Price Spec Sheet

## Purpose
Fetch current stock price and key metrics for any stock ticker.
Returns OHLC, volume, market cap, P/E ratio, 52-week range, dividend yield.
Powered by yfinance (free, no API key).

## Status
[DONE]

## Trigger Phrases
- "what is the price of Apple stock"
- "show me Tesla stock info"
- "get stock price for AAPL"
- "tell me about RELIANCE.BO"
- "show stock fundamentals for GOOGL"

## Input Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| symbol | str | yes | none | Stock ticker (AAPL, TSLA, RELIANCE.BO, etc) |

## Output Format
Stock: Apple Inc. (AAPL)
Sector: Technology | Industry: Consumer Electronics

Price: $192.45  [UP] +2.15 (+1.13%)
As of: 2026-04-22

Today:
  Open:  $190.30
  High:  $193.50
  Low:   $189.90
  Prev Close: $190.30
  Volume: 45,230,000

Fundamentals:
  Market Cap:     $3.02T
  P/E Ratio:      28.45
  52-Week High:   $199.62
  52-Week Low:    $145.32
  Dividend Yield: 0.42%

## Dependencies
- yfinance (pip: yfinance)
- langchain_core.tools

## HITL
No - read-only market data

## Chaining
Combines with:
- calculator → "calculate PE ratio vs market average"
- nlp_tool → "search and analyze sentiment for AAPL"

## Known Issues
- If ticker invalid, returns "No data found" message
- Market cap formatted: $xyz.xB, $xyz.xT, $xyz.xM
- PE ratio may be "N/A" for unprofitable stocks
- Dividend yield "N/A" for non-dividend stocks

## Test Command
python -c "
from tools.stock_tool import get_stock_price
print(get_stock_price.invoke({'symbol': 'AAPL'}))
"

## Bunge Relevance
Market intelligence for agricultural input suppliers and export pricing.

## Internal Notes
- Fetches 1-day history + 2-day for prev close + 1-year for 52-week range
- Uses yfinance.Ticker() for data
- Status: [UP] if change >= 0, [DOWN] if negative
- Handles missing data with "N/A" fallback
