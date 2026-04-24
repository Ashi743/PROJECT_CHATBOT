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

def parse_rag_response(response_text: str) -> dict:
    """Parse RAG JSON response and return structured data."""
    import json
    try:
        data = json.loads(response_text)
        if "answer" in data and "sources" in data:
            return {"is_rag": True, "data": data}
    except (json.JSONDecodeError, ValueError):
        pass
    return {"is_rag": False, "text": response_text}

def format_rag_output(response_data: dict):
    """Format and display RAG response with source attribution."""
    import streamlit as st

    answer = response_data["data"]["answer"]
    sources = response_data["data"]["sources"]
    metrics = response_data["data"]["metrics"]

    st.write(answer)

    if sources:
        st.divider()
        st.markdown("### Sources")

        for i, source in enumerate(sources, 1):
            source_name = source.get("name", "Unknown")
            page_info = f" (Page {source.get('page')})" if source.get("page") else ""
            st.caption(f"**{i}. {source_name}{page_info}**")

    st.divider()
    st.caption(f"Response time: {metrics.get('response_time', 0):.2f}s | Loops: {metrics.get('total_loops', 0)} | Web search: {'Yes' if metrics.get('web_search_triggered') else 'No'}")
