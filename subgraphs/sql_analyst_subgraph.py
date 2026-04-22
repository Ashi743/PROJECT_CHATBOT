"""
SQL Analyst Subgraph: 4-node workflow with 1 HITL interrupt.
- parse_node → classify query (SELECT vs destructive)
- safety_node → interrupt #1 (confirm destructive operations)
- execute_node → run query
- result_node → format results
"""

import sqlite3
from typing import TypedDict, Annotated
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from langchain_core.messages import BaseMessage


class SQLAnalystState(TypedDict):
    """State for SQL analysis workflow."""
    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    db_path: str
    is_destructive: bool
    safety_report: str
    result: str
    status: str  # "completed" | "cancelled" | "error"


DESTRUCTIVE_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER"}


def parse_node(state: SQLAnalystState) -> dict:
    """Classify query as SELECT (safe) or destructive (mutating)."""
    try:
        query_upper = state["query"].upper().strip()

        # Check if destructive
        is_destructive = any(kw in query_upper for kw in DESTRUCTIVE_KEYWORDS)

        # Generate safety report
        if is_destructive:
            # Extract operation type
            for kw in DESTRUCTIVE_KEYWORDS:
                if kw in query_upper:
                    safety_report = f"Destructive operation: {kw}. This will modify the database."
                    break
        else:
            safety_report = "Safe SELECT query — read-only."

        return {
            "is_destructive": is_destructive,
            "safety_report": safety_report,
            "status": "in_progress",
            "messages": [],
        }
    except Exception as e:
        return {
            "status": "error",
            "is_destructive": False,
            "safety_report": str(e),
            "messages": [],
        }


def safety_node(state: SQLAnalystState) -> dict:
    """Interrupt for destructive queries."""
    if not state["is_destructive"]:
        # Safe query, skip interrupt
        return {"status": "in_progress", "messages": []}

    confirmed = interrupt({
        "step": "confirm_destructive",
        "message": "This query will modify the database. Confirm?",
        "query": state["query"],
        "risk": state["safety_report"]
    })

    if confirmed != "yes":
        return {"status": "cancelled", "messages": []}

    return {"status": "in_progress", "messages": []}


def execute_node(state: SQLAnalystState) -> dict:
    """Execute the SQL query."""
    if state["status"] == "cancelled":
        return {"status": "cancelled", "result": "Query cancelled", "messages": []}

    try:
        conn = sqlite3.connect(state["db_path"])
        cursor = conn.cursor()

        cursor.execute(state["query"])

        if state["is_destructive"]:
            conn.commit()
            return {
                "result": f"Query executed successfully. Rows affected: {cursor.rowcount}",
                "status": "in_progress",
                "messages": [],
            }
        else:
            rows = cursor.fetchall()
            conn.close()
            return {
                "result": str(rows[:10]),  # First 10 rows
                "status": "in_progress",
                "messages": [],
            }

    except Exception as e:
        return {
            "result": f"Error: {str(e)}",
            "status": "error",
            "messages": [],
        }


def result_node(state: SQLAnalystState) -> dict:
    """Format and finalize results."""
    return {
        "status": "completed" if state["status"] != "error" else "error",
        "messages": [],
    }


def should_continue(state: SQLAnalystState) -> str:
    """Route based on status."""
    if state["status"] in ["cancelled", "error", "completed"]:
        return "end"
    return "continue"


# Build graph
def _build_sql_analyst_graph():
    graph = StateGraph(SQLAnalystState)
    graph.add_node("parse", parse_node)
    graph.add_node("safety", safety_node)
    graph.add_node("execute", execute_node)
    graph.add_node("result", result_node)

    graph.add_edge(START, "parse")
    graph.add_edge("parse", "safety")
    graph.add_edge("safety", "execute")
    graph.add_edge("execute", "result")
    graph.add_conditional_edges("result", should_continue, {"continue": "execute", "end": END})

    return graph


_sql_analyst_graph = _build_sql_analyst_graph()
sql_analyst_graph = None  # Will be compiled in frontend.py with shared checkpointer
