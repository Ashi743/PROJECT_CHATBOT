from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage

from langgraph.graph import StateGraph, START ,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from typing import TypedDict ,Annotated
from dotenv import load_dotenv

from tools.stock_tool import get_stock_price
from tools.india_time_tool import get_india_time
from tools.calculator_tool import calculator
from tools.web_search_tool import web_search
from tools.csv_analysis_tool import analyze_data
from tools.sql_analysis_tool import analyze_sql
from gmail_toolkit.gmail import gmail_tools

load_dotenv()

# Cost optimization: Use gpt-4o-mini for general chat, gpt-4o for heavy analysis
llm_model = ChatOpenAI(model="gpt-4o-mini")  # Main chatbot (cost-effective)
analysis_llm = ChatOpenAI(model="gpt-4o")    # Heavy analysis interpretation (high-quality)

# Combine base tools with Gmail tools and data analysis tools
base_tools = [get_stock_price, get_india_time, calculator, web_search, analyze_data, analyze_sql]
all_tools = base_tools + gmail_tools
tools = all_tools
llm_with_tools = llm_model.bind_tools(tools)

class chatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _is_analysis_result(messages: list[BaseMessage]) -> bool:
    """Check if the last message is a tool result from analysis tools"""
    if not messages:
        return False
    last_msg = messages[-1]
    if not isinstance(last_msg, ToolMessage):
        return False
    # Analysis tools produce larger, data-heavy results
    return len(last_msg.content) > 200 or any(
        keyword in last_msg.content.lower()
        for keyword in ['correlation', 'histogram', 'plot', 'statistic', 'summary', '[PLOT_IMAGE']
    )


def chat_node(state:chatState):
    message= state["messages"]
    # Use gpt-4o for interpreting analysis results, gpt-4o-mini for regular chat
    if _is_analysis_result(message):
        # Heavy analysis interpretation uses gpt-4o
        analysis_llm_with_tools = analysis_llm.bind_tools(tools)
        response = analysis_llm_with_tools.invoke(message)
    else:
        # Regular chat uses cheaper gpt-4o-mini
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

        results.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

    return {"messages": results}

def should_use_tools(state:chatState):
    """Decide whether to continue to tool execution or end"""
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


## -------------------- MEMORY CHECKPOINTING --------------------
conn= sqlite3.connect(database= "chat_memory.db", check_same_thread=False)
checkpointer= SqliteSaver(conn)
checkpointer.setup()  # Initialize database schema
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