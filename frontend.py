import streamlit as st
from backend import chatbot, retrieve_thread, save_thread_label, delete_thread, rename_thread
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from uuid import uuid4

st.set_page_config(
    page_title="Chat Bot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

## Available Tools Info
AVAILABLE_TOOLS = {
    "Stock Price": "Get real-time stock prices (yfinance)",
    "India Time": "Current date & time in India (IST)",
    "Calculator": "Math with BODMAS & trigonometry",
    "Holidays": "Public holidays calendar (Calendarific)",
    "Web Search": "Real-time web search (Tavily)",
    "Telegram Alert": "Send alerts to Telegram (BotFather)"
}

## ----------------- utility functions for thread management -----------------


def new_thread_id():
    return str(uuid4())

def load_thread_messages(thread_id):

    CONFIG = RunnableConfig(configurable={"thread_id": thread_id})

    state = chatbot.get_state(config=CONFIG)
    if state and state.values.get("messages"):
        messages = []
        for msg in state.values["messages"]:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        return messages
    return []

def switch_to_thread(thread_id):
    st.session_state["current_thread_id"] = thread_id
    st.session_state["message_history"] = load_thread_messages(thread_id)
    st.session_state["chat_started"] = True

def extract_first_5_words(text: str) -> str:
    """Extract first 5 words from text and create a label"""
    words = text.split()[:5]
    label = " ".join(words)
    if len(text.split()) > 5:
        label += "..."
    return label

def update_thread_label(thread_id: str, user_input: str):
    """Update thread label based on user input"""
    label = extract_first_5_words(user_input)
    save_thread_label(thread_id, label)
    # Update the label in session state
    for thread in st.session_state["threads"]:
        if thread["id"] == thread_id:
            thread["label"] = label
            break

##-------------------Session setup ------------------------------------

if "chat_started" not in st.session_state:
    st.session_state["chat_started"] = False

if "current_thread_id" not in st.session_state:
    st.session_state["current_thread_id"] = None

if "threads" not in st.session_state:
    st.session_state["threads"] =  retrieve_thread()   #unique list of threads 

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []


## ------------------- Streamlit UI ---------------------
with st.sidebar:
    st.title("💬 Chat Bot")

    # Show available tools
    st.subheader("📚 Available Tools")
    with st.expander("View Tools (6 available)", expanded=False):
        for tool_name, tool_desc in AVAILABLE_TOOLS.items():
            st.caption(f"**{tool_name}**: {tool_desc}")

    st.divider()
    st.subheader("My Conversations")

    if not st.session_state["chat_started"]:
        if st.button("--START CHAT--", key="start_chat"):
            thread_id = new_thread_id()
            st.session_state["threads"].append({"id": thread_id, "label": f"Chat {len(st.session_state['threads']) + 1}"})
            switch_to_thread(thread_id)
            st.rerun()

    if len(st.session_state["threads"]) > 0:
        if st.button("➕ NEW CHAT", key="new_chat"):
            thread_id = new_thread_id()
            st.session_state["threads"].append({"id": thread_id, "label": f"Chat {len(st.session_state['threads']) + 1}"})
            switch_to_thread(thread_id)
            st.rerun()

    if len(st.session_state["threads"]) > 0:
        st.divider()
        st.write("**Chat History**")
        for thread in reversed(st.session_state["threads"]):
            col1, col2, col3 = st.columns([5, 1, 1])
            with col1:
                if st.button(thread["label"], key=f"thread_{thread['id']}", use_container_width=True):
                    switch_to_thread(thread["id"])
                    st.rerun()
            with col2:
                if st.button("✏️", key=f"rename_{thread['id']}", help="Rename chat"):
                    st.session_state[f"rename_mode_{thread['id']}"] = True
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_{thread['id']}", help="Delete chat"):
                    delete_thread(thread["id"])
                    st.session_state["threads"] = [t for t in st.session_state["threads"] if t["id"] != thread["id"]]
                    if st.session_state["current_thread_id"] == thread["id"]:
                        st.session_state["chat_started"] = False
                        st.session_state["current_thread_id"] = None
                        st.session_state["message_history"] = []
                    st.rerun()

            # Rename input field
            if st.session_state.get(f"rename_mode_{thread['id']}", False):
                new_label = st.text_input("New name:", value=thread["label"], key=f"rename_input_{thread['id']}")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("Save", key=f"save_rename_{thread['id']}"):
                        if new_label and new_label.strip():
                            rename_thread(thread["id"], new_label)
                            thread["label"] = new_label
                            st.session_state[f"rename_mode_{thread['id']}"] = False
                            st.rerun()
                with col_cancel:
                    if st.button("Cancel", key=f"cancel_rename_{thread['id']}"):
                        st.session_state[f"rename_mode_{thread['id']}"] = False
                        st.rerun()

## ------------------- Initialize chatbot and database ---------------------


if not st.session_state["chat_started"]:
    st.markdown("# 🤖 Welcome to Your AI Chat Bot!")

    st.markdown("""
    ### What can I do?
    I'm powered by **6 amazing tools** that let me:

    1. **📈 Stock Price** - Get real-time stock quotes and fundamentals
    2. **🕐 India Time** - Tell you the current date & time in India (IST)
    3. **🧮 Calculator** - Solve complex math with BODMAS & trigonometry
    4. **📅 Holidays** - Show public holidays for 200+ countries
    5. **🔍 Web Search** - Search the web for latest information
    6. **📱 Telegram Alert** - Send messages directly to your Telegram

    ### Try asking me:
    - "What's the current price of Apple stock?"
    - "What time is it in India?"
    - "Calculate sin(pi/2) + sqrt(16)"
    - "What holidays are coming up?"
    - "Search for latest AI news"
    - "Send a message to Telegram: Task completed"

    """)

    st.info("<-- Click **START CHAT** in the sidebar to begin")
else:
    st.title("Chat")

    for messages in st.session_state["message_history"]:
        with st.chat_message(messages['role']):
            st.markdown(messages['content'])

    user_input = st.chat_input("type here")

    if user_input:
        st.session_state["message_history"].append({'role': 'user', 'content': user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Update thread label on first user message
        current_thread = next((t for t in st.session_state["threads"] if t["id"] == st.session_state["current_thread_id"]), None)
        if current_thread and current_thread["label"].startswith("Chat "):
            update_thread_label(st.session_state["current_thread_id"], user_input)

        CONFIG = RunnableConfig(configurable={"thread_id": st.session_state["current_thread_id"]})

        def response_generator():
            full_response = ""
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"):
                if isinstance(message_chunk, str):
                    full_response += message_chunk
                    yield message_chunk
                elif hasattr(message_chunk, 'content'):
                    full_response += message_chunk.content
                    yield message_chunk.content
            st.session_state["message_history"].append({'role': 'assistant', 'content': full_response})

        with st.chat_message("assistant"):
            st.write_stream(response_generator())
         