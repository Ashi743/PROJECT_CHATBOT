from uuid import uuid4
from langchain_core.runnables import RunnableConfig
from backend import chatbot, save_thread_label

def new_thread_id():
    return str(uuid4())

def load_thread_messages(thread_id):
    CONFIG = RunnableConfig(configurable={"thread_id": thread_id})
    state = chatbot.get_state(config=CONFIG)
    if state and state.values.get("messages"):
        from langchain_core.messages import HumanMessage, AIMessage
        messages = []
        for msg in state.values["messages"]:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": content})
        return messages
    return []

def extract_first_5_words(text: str) -> str:
    words = text.split()[:5]
    label = " ".join(words)
    if len(text.split()) > 5:
        label += "..."
    return label

def update_thread_label(thread_id: str, user_input: str):
    label = extract_first_5_words(user_input)
    save_thread_label(thread_id, label)
    import streamlit as st
    for thread in st.session_state["threads"]:
        if thread["id"] == thread_id:
            thread["label"] = label
            break
