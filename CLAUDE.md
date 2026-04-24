# Chatbot Project — Claude Code Context

## Project Overview
LangGraph agentic chatbot with Streamlit frontend.
Multi-tool AI assistant with monitoring, analysis, and alerting.

## Environment
- Python 3.14, Windows machine
- NO emojis in any tool output (Windows cp1252 encoding)
- Use [OK] [ALERT] [DOWN] [WARN] [ERROR] [STALE] instead

## Tech Stack
- LangGraph + SqliteSaver (checkpointer)
- Streamlit frontend with streaming
- OpenAI (ChatOpenAI)
- ChromaDB (RAG)
- SQLite (data analysis)
- Redis (caching — planned)

## Alert System
- Gmail smtplib  : user-initiated reports, always HITL
- Slack webhook  : automated monitor alerts, no HITL
- NO Telegram anywhere in codebase

## Search
- DuckDuckGo only (langchain_community DuckDuckGoSearchRun)
- NO Tavily, NO TAVILY_API_KEY

## Branch Strategy
- main                   : stable, always runnable
- feat/production-fixes  : current branch (hardening, no new features)
- feat/c-rag             : next (corrective RAG)
- feat/memory            : user/context memory system
- feat/frontend-redesign : split frontend into modules
- feat/docker            : containerization + Redis
- never merge broken code to main
- always test before committing

## Commit Convention (Conventional Commits)
- feat:   new feature
- fix:    bug fix
- chore:  config, dependencies, cleanup
- docs:   documentation only
- refactor: code restructure, no behavior change

## Directory Structure
- tools/        single @tool decorated functions
- subgraphs/    multi-step LangGraph flows with HITL
- pipelines/    background processes, schedulers, health checks
- docs/         spec files, read before building
- data/         databases, chroma_db, cleaned files, plots
- utils/        shared helpers (cache, formatting)

## HITL Rules
- Gmail send          : always HITL
- Slack user-facing   : always HITL
- CSV cleaning        : always HITL
- SQL DELETE/UPDATE   : always HITL
- RAG ingest          : always HITL
- Slack monitor auto  : NO HITL (background)
- SELECT queries      : NO HITL
- Read operations     : NO HITL

## Key Rules
- test each file independently before committing
- no emojis anywhere (cp1252)
- plain text output from all tools
- HITL on all write/send/delete operations
- Gmail = user initiated only
- Slack = automated monitor alerts only
- Redis caches tool results, not chat messages
- each tool file has if __name__ == "__main__" test block

## Specs
Read relevant specs before building anything.
**Index:** .claude/specs/INDEX.md

**Tools:** .claude/specs/tools/
  - datetime-spec.md, calculator-spec.md, search-spec.md
  - stock-spec.md, commodity-spec.md, nlp-spec.md
  - gmail-spec.md, csv-analyst-spec.md, monitor-spec.md, sql-analyst-spec.md

**Architecture:** .claude/specs/architecture/
  - rag-spec.md, redis-spec.md, hitl-spec.md

**Pipelines:** .claude/specs/pipelines/
  - monitor-spec.md, pipeline-spec.md, slack-spec.md

Also mirrored in docs/specs/ (GitHub-visible)

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
