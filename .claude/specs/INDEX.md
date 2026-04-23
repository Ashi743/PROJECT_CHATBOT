# Spec Sheet Index

Read relevant specs before building or modifying code.

## Tools (Read these before implementing tool logic)

| Tool | Spec File | Status | Branch | Purpose |
|------|-----------|--------|--------|---------|
| datetime | tools/datetime-spec.md | [DONE] | main | Current time in India (IST) |
| calculator | tools/calculator-spec.md | [DONE] | main | Math expressions with BODMAS |
| web_search | tools/search-spec.md | [DONE] | main | DuckDuckGo real-time search |
| stock | tools/stock-spec.md | [DONE] | main | yfinance stock price data |
| commodity | tools/commodity-spec.md | [DONE] | main | CBOT commodity futures |
| nlp | tools/nlp-spec.md | [DONE] | feat/nlp-monitoring | Sentiment + keywords + summary + NER |
| gmail | tools/gmail-spec.md | [DONE] | feat/nlp-monitoring | Gmail OAuth2 (HITL required) |
| csv_analyst | tools/csv-analyst-spec.md | [WIP] | feat/nlp-monitoring | Pandas analysis + RAG + plots |
| monitor | tools/monitor-spec.md | [DONE] | feat/nlp-monitoring | Background commodity monitoring |
| sql_analyst | tools/sql-analyst-spec.md | [DONE] | feat/nlp-monitoring | SQLite analysis + CRUD |
| world_time_calendar | tools/world-time-calendar-spec.md | [WIP] | feat/time-calender | World clock + holiday queries for any country |

## Architecture (Read before designing new systems)

| Topic | Spec File | Status | Purpose |
|-------|-----------|--------|---------|
| RAG | architecture/rag-spec.md | [PLANNED] | Vector DB for analysis insights |
| Redis | architecture/redis-spec.md | [PLANNED] | Caching tool results |
| HITL | architecture/hitl-spec.md | [PLANNED] | Human approval workflow |

## Pipelines (Read before implementing background processes)

| Pipeline | Spec File | Status | Purpose |
|----------|-----------|--------|---------|
| Monitor | pipelines/monitor-spec.md | [DONE] | Commodity monitoring thread |
| Pipeline | pipelines/pipeline-spec.md | [PLANNED] | CSV upload → analysis → RAG |
| Slack | pipelines/slack-spec.md | [DONE] | Automated Slack alerts |

## Quick Reference

### To implement a new tool:
1. Read CLAUDE.md (project context)
2. Read relevant tool spec (e.g., tools/csv-analyst-spec.md)
3. Add @tool decorator with docstring
4. Add to backend.py tools list
5. Test with `if __name__ == "__main__"` block

### To implement HITL:
1. Read architecture/hitl-spec.md
2. Yield pending_approval from tool
3. Streamlit frontend handles approval modal
4. Resume execution after user approves

### To add Redis caching:
1. Read architecture/redis-spec.md
2. Apply @cache_tool(ttl=900) decorator
3. Test hit rate with monitoring

### To extend monitoring:
1. Read pipelines/monitor-spec.md + tools/monitor-spec.md
2. Add new commodity or alert condition
3. Extend _run_monitoring() loop

### To set up Slack alerts:
1. Read pipelines/slack-spec.md
2. Create webhook in Slack workspace
3. Add SLACK_WEBHOOK_URL to .env
4. Call slack_notify from monitor/pipeline

## Status Legend
- [DONE]: Built, tested, merged to main
- [WIP]: Currently building, on feature branch
- [PLANNED]: Design complete, not started
- [BLOCKED]: Blocked on dependency

## Branch Guide
- main: Stable, production-ready
- feat/nlp-monitoring: Current feature branch (will merge after testing)
- feat/pipeline-monitor: Next feature (blocked on nlp-monitoring merge)
- feat/redis-caching: After pipeline-monitor merged

## When to Add Specs
- New tool created → Add tool/{name}-spec.md
- New pipeline → Add pipelines/{name}-spec.md
- New architecture → Add architecture/{name}-spec.md
- Always update INDEX.md with new file
- Keep INDEX < 200 lines (stays loaded in context)
