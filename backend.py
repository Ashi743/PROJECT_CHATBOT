from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, HumanMessage

from langgraph.graph import StateGraph, START ,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import atexit
import signal
import logging

from typing import TypedDict ,Annotated
from dotenv import load_dotenv
from utils.logging_config import setup_logging

# Set up logging
setup_logging()

from tools.stock_tool import get_stock_price
from tools.world_time_tool import get_world_time, get_world_time_multiple, get_holidays, get_upcoming_holidays, list_supported_countries
from tools.calculator_tool import calculator
from tools.web_search_tool import web_search
from tools.csv_analysis_tool import analyze_data
from tools.sql_analysis_tool import analyze_sql
from tools.nlp_tool import nlp_analyze
from tools.commodity_tool import get_commodity_price
from tools.monitor_tool import start_monitoring, stop_monitoring, get_monitoring_results, get_active_monitors
from tools.slack_alert_tool import slack_notify
from gmail_toolkit.gmail import gmail_tools

load_dotenv()

# Dual-LLM: gpt-4o-mini for general chat, gpt-4o for analysis (handles longer outputs)
llm_model = ChatOpenAI(model="gpt-4o-mini")  # Main chatbot (cost-effective)
analysis_llm = ChatOpenAI(model="gpt-4o")    # Analysis interpretation (no token limits)

# Combine base tools with Gmail tools, data analysis tools, NLP, monitoring, alerting, and calendar tools
base_tools = [
    get_stock_price, get_world_time, get_world_time_multiple, calculator, web_search, analyze_data, analyze_sql,
    nlp_analyze, get_commodity_price, start_monitoring, stop_monitoring,
    get_monitoring_results, get_active_monitors, slack_notify,
    get_holidays, get_upcoming_holidays, list_supported_countries
]
all_tools = base_tools + gmail_tools
tools = all_tools
llm_with_tools = llm_model.bind_tools(tools)

class chatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _message_content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    if content is None:
        return ""
    return str(content)

def _requires_analysis_llm(messages: list[BaseMessage]) -> bool:
    """Check if conversation needs analysis LLM (keyword or recent analysis result)"""
    if not messages:
        return False

    # Check last message for analysis keywords or large data
    last_msg = messages[-1]
    analysis_keywords = {
        "analyze", "interpret", "explain", "insight", "trend",
        "correlate", "compare", "anomaly", "outlier", "statistic",
        "summary", "pattern", "forecast", "predict"
    }

    # If last message is tool result from analysis tools
    if isinstance(last_msg, ToolMessage):
        content_str = _message_content_text(last_msg.content).lower()
        # Large results or analysis outputs need gpt-4o
        return len(content_str) > 200 or any(
            kw in content_str for kw in ['correlation', 'histogram', 'plot', 'statistic']
        )

    # If last message is user question with analysis keywords
    if isinstance(last_msg, HumanMessage):
        text = _message_content_text(last_msg.content).lower()
        return any(kw in text for kw in analysis_keywords)

    return False


def chat_node(state:chatState):
    message= state["messages"]
    # Route to appropriate LLM based on analysis keywords or recent results
    if _requires_analysis_llm(message):
        analysis_llm_with_tools = analysis_llm.bind_tools(tools)
        response = analysis_llm_with_tools.invoke(message)
    else:
        response = llm_with_tools.invoke(message)
    return {'messages': [response]}

def tool_node(state:chatState):
    """Execute tool calls from the LLM"""
    messages = state["messages"]
    last_message = messages[-1]

    tool_calls = last_message.tool_calls if isinstance(last_message, AIMessage) else []
    results = []

    # Create a tool map for easy lookup
    tool_map = {tool.name: tool for tool in tools}

    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]

        try:
            if tool_name in tool_map:
                # Some tools don't take arguments
                if tool_input:
                    result = tool_map[tool_name].invoke(tool_input)
                else:
                    result = tool_map[tool_name].invoke({})
            else:
                result = f"Unknown tool: {tool_name}"
        except Exception as e:
            result = f"Error executing {tool_name}: {str(e)}"

        # Ensure result is always a string
        result_str = str(result) if not isinstance(result, str) else result

        results.append(ToolMessage(content=result_str, tool_call_id=tool_call["id"]))

    return {"messages": results}

def should_use_tools(state:chatState):
    """Decide whether to continue to tool execution or end"""
    messages = state["messages"]
    if not messages:
        return END

    last_message = messages[-1]

    # Only route to tools if last message is AIMessage with tool_calls
    # AND the tool calls have not already been responded to
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Check if each tool_call has a corresponding ToolMessage response
        tool_call_ids = {tc["id"] for tc in last_message.tool_calls}
        tool_response_ids = set()

        # Look backwards to find ToolMessages that responded to these tool calls
        for msg in reversed(messages[:-1]):  # Exclude the current AIMessage
            if isinstance(msg, ToolMessage):
                tool_response_ids.add(msg.tool_call_id)

        # Only use tools if there are unresponded tool_calls
        if tool_call_ids - tool_response_ids:
            return "tools"

    return END


## -------------------- MEMORY CHECKPOINTING --------------------
conn= sqlite3.connect(database= "chat_memory.db", check_same_thread=False)
checkpointer= SqliteSaver(conn)
checkpointer.setup()  # Initialize database schema

def _graceful_shutdown(*args):
    try:
        if hasattr(checkpointer, "conn") and checkpointer.conn is not None:
            checkpointer.conn.commit()
            checkpointer.conn.close()
    except Exception as e:
        print(f"[ERROR] Shutdown error: {e}")

atexit.register(_graceful_shutdown)
signal.signal(signal.SIGTERM, _graceful_shutdown)
## --------------------------------------------------------------

# Create thread_metadata table for storing custom labels
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS thread_metadata (
        thread_id TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
    )
""")
conn.commit()


graph= StateGraph(chatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", should_use_tools, {"tools": "tools", END: END})
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

#----------------- utility functions for thread management -----------------
def get_thread_label(thread_id: str):
    """Retrieve custom label for a thread from database"""
    cursor = conn.cursor()
    cursor.execute("SELECT label FROM thread_metadata WHERE thread_id = ?", (thread_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def save_thread_label(thread_id: str, label: str):
    """Save custom label for a thread to database"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO thread_metadata (thread_id, label) VALUES (?, ?)",
        (thread_id, label)
    )
    conn.commit()

def retrieve_thread():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        if checkpoint.config and 'configurable' in checkpoint.config:
            all_threads.add(checkpoint.config['configurable']["thread_id"])

    threads = []
    for i, tid in enumerate(sorted(all_threads)):
        label = get_thread_label(tid)
        if not label:
            label = f"Chat {i+1}"
        threads.append({"id": tid, "label": label})
    return threads

def delete_thread(thread_id: str):
    """Delete a thread and its metadata from the database"""
    cursor = conn.cursor()
    # Delete from thread_metadata
    cursor.execute("DELETE FROM thread_metadata WHERE thread_id = ?", (thread_id,))
    # Delete all checkpoints for this thread (SqliteSaver uses 'checkpoints' and 'writes' tables)
    cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    conn.commit()

def rename_thread(thread_id: str, new_label: str):
    """Rename a thread by updating its label"""
    save_thread_label(thread_id, new_label)