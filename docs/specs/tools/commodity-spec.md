# Commodity Price Spec Sheet

## Purpose
Fetch current commodity prices and metrics using yfinance futures.
Supports: wheat, soy, corn, sugar, cotton, rice.
Returns price, change%, volume, and 52-week range.

## Status
[DONE]

## Trigger Phrases
- "what is the price of wheat"
- "get corn futures price"
- "show me sugar commodity data"
- "wheat price today"
- "check cotton and soy prices"

## Input Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| commodity | str | yes | none | Commodity name (wheat, soy, corn, sugar, cotton, rice) |

## Output Format
Commodity: WHEAT (ZW=F)

Price: $7.25  [UP] +0.15 (+2.11%)
As of: 2026-04-22

Today's Trading:
  Open:  $7.10
  High:  $7.30
  Low:   $7.05
  Prev Close: $7.10
  Volume: 2,450,000

52-Week Range:
  High: $8.15
  Low:  $6.45

## Valid Commodities
- wheat → ZW=F
- soy/soybeans → ZS=F
- corn → ZC=F
- sugar → SB=F
- cotton → CT=F
- rice → ZR=F

## Dependencies
- yfinance (pip: yfinance)
- langchain_core.tools

## HITL
No - read-only market data

## Chaining
Combines with:
- nlp_tool → "get wheat price and analyze market sentiment"
- monitor_tool → "track wheat price every 30 min and alert on drops"

## Known Issues
- Only supports 6 commodities; invalid commodity returns helpful error with valid options
- Price data fetched from 5-day history for prev_close, 1-year for 52-week
- Volume may be "N/A" if no trading activity

## Test Command
python -c "
from tools.commodity_tool import get_commodity_price
print(get_commodity_price.invoke({'commodity': 'wheat'}))
"

## Bunge Relevance
Core pricing intelligence for Bunge commodity trading and hedging operations.

## Internal Notes
- Maps commodity names to CBOT futures ticker symbols
- Case-insensitive input
- [UP]/[DOWN] indicator based on change >= 0
- 52-week high/low from 1-year history using max/min
