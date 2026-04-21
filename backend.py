from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from langgraph.graph import StateGraph, START ,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from typing import TypedDict ,Annotated
from dotenv import load_dotenv


load_dotenv()

llm_model= ChatOpenAI()

class chatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state:chatState):
    message= state["messages"]
    response =llm_model.invoke(message)
    return {'messages': [response]}


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
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

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