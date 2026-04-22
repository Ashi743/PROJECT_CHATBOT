import streamlit as st
from backend import chatbot, retrieve_thread, save_thread_label, delete_thread, rename_thread
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from uuid import uuid4
from tools.csv_ingest_tool import ingest_file, list_datasets, get_dataset_info, update_dataset_description, delete_dataset

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
    "Web Search": "Real-time web search (DuckDuckGo)",
    "Send Email": "Send emails via Gmail",
    "Create Draft": "Create email drafts",
    "Search Email": "Search your Gmail messages",
    "Get Email": "Fetch email details by ID",
    "Get Thread": "Get email conversations",
    "Analyze Data": "Analyze CSV/Excel data with pandas"
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
    with st.expander("View Tools (10 available)", expanded=False):
        for tool_name, tool_desc in AVAILABLE_TOOLS.items():
            st.caption(f"**{tool_name}**: {tool_desc}")

    st.divider()
    st.subheader("📊 Data Analysis")

    with st.expander("Upload CSV/Excel", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            key="csv_uploader"
        )

        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            with col1:
                dataset_name = st.text_input(
                    "Dataset name",
                    value=uploaded_file.name.rsplit('.', 1)[0],
                    key="dataset_name_input"
                )
            with col2:
                user_desc = st.text_input(
                    "Description (optional)",
                    placeholder="e.g., Q1 Sales Data",
                    key="dataset_desc_input"
                )

            if st.button("Upload", key="upload_btn"):
                with st.spinner("Ingesting file..."):
                    result = ingest_file(
                        file_bytes=uploaded_file.getvalue(),
                        file_name=uploaded_file.name,
                        dataset_name=dataset_name,
                        user_description=user_desc
                    )

                    if result["status"] == "ok":
                        st.success(f"✓ {result['message']}")
                        st.info(f"Chunks: {result.get('chunks_created', 0)} | Numeric cols: {len(result.get('numeric_columns', []))} | Categorical cols: {len(result.get('categorical_columns', []))}")
                    else:
                        st.error(f"✗ {result['message']}")

    # Show available datasets with HITL controls
    datasets = list_datasets()
    if datasets:
        st.subheader("📁 Available Datasets")
        for ds in datasets:
            with st.expander(f"📊 {ds}", expanded=False):
                info = get_dataset_info(ds)
                if "error" not in info:
                    st.caption(f"**Rows:** {info.get('rows')} | **Columns:** {info.get('columns', [])}")

                    if info.get('user_description'):
                        st.caption(f"**Description:** {info['user_description']}")

                    # HITL: Update description
                    new_desc = st.text_input(
                        "Update description",
                        value=info.get('user_description', ''),
                        key=f"desc_{ds}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", key=f"save_desc_{ds}"):
                            update_result = update_dataset_description(ds, new_desc)
                            if update_result["status"] == "ok":
                                st.success("Description updated")
                            else:
                                st.error(f"Error: {update_result['message']}")

                    with col2:
                        if st.button("Delete", key=f"delete_{ds}"):
                            delete_result = delete_dataset(ds)
                            if delete_result["status"] == "ok":
                                st.success("Dataset deleted")
                                st.rerun()
                            else:
                                st.error(f"Error: {delete_result['message']}")

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
    I'm powered by **9 amazing tools** that let me:

    **General Tools:**
    1. **📈 Stock Price** - Get real-time stock quotes and fundamentals
    2. **🕐 India Time** - Tell you the current date & time in India (IST)
    3. **🧮 Calculator** - Solve complex math with BODMAS & trigonometry
    4. **🔍 Web Search** - Search the web for latest information

    **Email Tools (Gmail):**
    5. **✉️ Send Email** - Send emails to anyone
    6. **📝 Create Draft** - Create email drafts
    7. **🔎 Search Email** - Search your Gmail messages
    8. **📧 Get Email** - Fetch specific email details
    9. **💬 Get Thread** - View email conversations

    ### Try asking me:
    - "What's the current price of Apple stock?"
    - "What time is it in India?"
    - "Calculate sin(pi/2) + sqrt(16)"
    - "Search for latest AI news"
    - "Send an email to test@example.com with subject 'Hello' and message 'Hi there'"
    - "Search my emails for 'important meeting'"

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
         