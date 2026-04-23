import streamlit as st
from backend import chatbot, retrieve_thread, save_thread_label, delete_thread, rename_thread
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from uuid import uuid4
from pathlib import Path
from tools.csv_ingest_tool import save_and_prepare_file, ingest_file_to_rag, list_datasets, get_dataset_info, update_dataset_description, delete_dataset
from tools.sql_file_ingest_tool import ingest_sql_file, get_database_list, get_database_schema, delete_database

st.set_page_config(
    page_title="Chat Bot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

## Available Tools Info
AVAILABLE_TOOLS = {
    "Stock Price": "Get real-time stock prices (yfinance)",
    "Commodity Price": "Get wheat, soy, corn, sugar prices",
    "India Time": "Current date and time in India (IST)",
    "Calculator": "Math with BODMAS and trigonometry",
    "Web Search": "Real-time web search (DuckDuckGo)",
    "NLP Analysis": "Sentiment, keywords, summary, NER analysis",
    "Commodity Monitor": "Start/stop real-time monitoring with alerts",
    "Send Email": "Send emails via Gmail",
    "Create Draft": "Create email drafts",
    "Search Email": "Search your Gmail messages",
    "Get Email": "Fetch email details by ID",
    "Get Thread": "Get email conversations",
    "Analyze Data": "Analyze CSV/Excel data with pandas",
    "Analyze SQL": "Query SQLite database with SQL",
    "Upload SQL Files": "Create databases from .sql files (CREATE TABLE + INSERT)",
    "List Databases": "See all uploaded SQL databases",
    "Query Database": "Run SELECT queries on any uploaded database"
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
            # Ensure content is always a string
            content = msg.content if isinstance(msg.content, str) else str(msg.content)

            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": content})
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

def render_plots_grid(plots_metadata: dict):
    """Render plots in a 2-column grid."""
    if not plots_metadata or len(plots_metadata) == 0:
        return

    st.subheader("📈 Generated Visualizations")

    plot_items = list(plots_metadata.items())
    for i in range(0, len(plot_items), 2):
        col1, col2 = st.columns(2)

        # First plot
        plot_type, plot_info = plot_items[i]
        with col1:
            st.markdown(f"**{plot_info['title']}**")
            try:
                st.image(plot_info['path'], use_container_width=True)
            except Exception as e:
                st.error(f"Could not load plot: {e}")

        # Second plot (if exists)
        if i + 1 < len(plot_items):
            plot_type, plot_info = plot_items[i + 1]
            with col2:
                st.markdown(f"**{plot_info['title']}**")
                try:
                    st.image(plot_info['path'], use_container_width=True)
                except Exception as e:
                    st.error(f"Could not load plot: {e}")

##-------------------Session setup ------------------------------------

if "chat_started" not in st.session_state:
    st.session_state["chat_started"] = False

if "current_thread_id" not in st.session_state:
    st.session_state["current_thread_id"] = None

if "threads" not in st.session_state:
    st.session_state["threads"] =  retrieve_thread()   #unique list of threads 

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "pending_plots" not in st.session_state:
    st.session_state["pending_plots"] = []

if "monitor_running" not in st.session_state:
    st.session_state["monitor_running"] = False
if "monitor_selections" not in st.session_state:
    st.session_state["monitor_selections"] = []
if "monitor_interval" not in st.session_state:
    st.session_state["monitor_interval"] = 30
if "monitor_thread" not in st.session_state:
    st.session_state["monitor_thread"] = None
if "last_check_results" not in st.session_state:
    st.session_state["last_check_results"] = None
if "report_scheduled" not in st.session_state:
    st.session_state["report_scheduled"] = False
if "report_paused" not in st.session_state:
    st.session_state["report_paused"] = False
if "scheduled_time" not in st.session_state:
    st.session_state["scheduled_time"] = None
if "awaiting_hitl" not in st.session_state:
    st.session_state["awaiting_hitl"] = False
if "hitl_context" not in st.session_state:
    st.session_state["hitl_context"] = None


## ------------------- Streamlit UI ---------------------
with st.sidebar:
    st.title("💬 Chat Bot")

    # Show available tools
    st.subheader("📚 Available Tools")
    with st.expander("View Tools (14 available)", expanded=False):
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
                if not dataset_name or not dataset_name.strip():
                    st.error("Dataset name cannot be empty")
                else:
                    # Persistent spinner at top during entire upload process
                    with st.spinner("⏳ Processing dataset..."):
                        # Step 1: Save file (fast)
                        st.info("💾 Saving file...")
                        save_result = save_and_prepare_file(
                            file_bytes=uploaded_file.getvalue(),
                            file_name=uploaded_file.name,
                            dataset_name=dataset_name
                        )

                        if save_result["status"] != "ok":
                            st.error(f"✗ {save_result['message']}")
                        else:
                            # Step 2: Analyze and ingest to RAG with live progress steps
                            with st.status("📊 Analyzing and indexing data...", expanded=True) as status:
                                try:
                                    rag_result = ingest_file_to_rag(
                                        file_path=save_result["file_path"],
                                        dataset_name=dataset_name,
                                        user_description=user_desc,
                                        file_name=uploaded_file.name,
                                        on_progress=st.write
                                    )

                                    if rag_result["status"] == "ok":
                                        status.update(label="✓ Analysis complete", state="complete")
                                        chunks = rag_result.get('chunks_created', 0)
                                        st.success(f"✓ File saved: {save_result['rows']} rows, {save_result['cols']} columns")
                                        st.success(f"✓ {rag_result['message']}")
                                        st.info(f"Chunks: {chunks} | Numeric cols: {len(rag_result.get('numeric_columns', []))} | Categorical cols: {len(rag_result.get('categorical_columns', []))}")
                                        st.rerun()
                                    else:
                                        status.update(label="✗ Analysis failed", state="error")
                                        st.error(f"✗ {rag_result['message']}")
                                except Exception as e:
                                    status.update(label="✗ Error during analysis", state="error")
                                    st.error(f"✗ Error: {str(e)}")

    # Show available datasets with HITL controls
    datasets = list_datasets()
    if datasets:
        st.subheader("📁 Available Datasets")
        for ds in datasets:
            is_confirming_delete = st.session_state.get(f"confirm_delete_dataset_{ds}", False)
            with st.expander(f"📊 {ds}", expanded=is_confirming_delete):
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
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("💾 Save", key=f"save_desc_{ds}"):
                            update_result = update_dataset_description(ds, new_desc or "")
                            if update_result["status"] == "ok":
                                st.success("Description updated")
                            else:
                                st.error(f"Error: {update_result['message']}")

                    with col2:
                        if st.button("📈 Visualize", key=f"visualize_{ds}"):
                            st.session_state[f"visualizing_{ds}"] = True
                            st.rerun()

                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{ds}"):
                            st.session_state[f"confirm_delete_dataset_{ds}"] = True
                            st.rerun()

                    # Generate plots if visualization requested
                    if st.session_state.get(f"visualizing_{ds}", False):
                        from tools.csv_ingest_tool import UPLOAD_DIR
                        dataset_file = None
                        for ext in ['.csv', '.xlsx', '.xls']:
                            candidate = UPLOAD_DIR / f"{ds}{ext}"
                            if candidate.exists():
                                dataset_file = candidate
                                break

                        if dataset_file:
                            with st.status("📊 Generating visualizations...", expanded=True) as status:
                                try:
                                    from tools.plot_utils import PlotGenerator
                                    import pandas as pd

                                    st.write("📖 Loading data...")
                                    df = pd.read_csv(dataset_file) if str(dataset_file).endswith('.csv') else pd.read_excel(dataset_file)

                                    st.write("🎨 Creating plots...")
                                    generator = PlotGenerator(df, ds)
                                    result = generator.generate_all_plots()

                                    if result["status"] == "ok":
                                        status.update(label="✓ Visualizations ready", state="complete")
                                        st.session_state[f"visualizing_{ds}"] = False
                                        st.session_state[f"plots_{ds}"] = result["plots"]
                                        st.rerun()
                                    else:
                                        status.update(label="✗ Visualization failed", state="error")
                                        st.error(f"Error: {result.get('message', 'Unknown error')}")
                                        st.session_state[f"visualizing_{ds}"] = False
                                except Exception as e:
                                    status.update(label="✗ Error generating plots", state="error")
                                    st.error(f"Error: {str(e)}")
                                    st.session_state[f"visualizing_{ds}"] = False
                        else:
                            st.error(f"Could not find dataset file for '{ds}'")

                    # Display plots if they exist
                    if st.session_state.get(f"plots_{ds}"):
                        render_plots_grid(st.session_state[f"plots_{ds}"])

                    # HITL Confirmation for dataset deletion
                    if st.session_state.get(f"confirm_delete_dataset_{ds}", False):
                        st.warning(f"⚠️ Are you sure you want to delete '{ds}'? This cannot be undone.")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("Yes, Delete", key=f"confirm_delete_dataset_yes_{ds}", type="primary"):
                                delete_result = delete_dataset(ds)
                                if delete_result["status"] == "ok":
                                    st.success("Dataset deleted")
                                    st.session_state[f"confirm_delete_dataset_{ds}"] = False
                                    st.rerun()
                                else:
                                    st.error(f"Error: {delete_result['message']}")
                        with col_cancel:
                            if st.button("Cancel", key=f"confirm_delete_dataset_no_{ds}"):
                                st.session_state[f"confirm_delete_dataset_{ds}"] = False
                                st.rerun()

    st.divider()
    st.subheader("SQL Databases")

    with st.expander("Upload SQL File", expanded=False):
        uploaded_sql_file = st.file_uploader(
            "Choose a .sql file",
            type=["sql"],
            key="sql_uploader"
        )

        if uploaded_sql_file is not None:
            if st.button("Upload SQL File", key="upload_sql_btn"):
                with st.spinner("Processing SQL file..."):
                    result = ingest_sql_file(
                        file_bytes=uploaded_sql_file.getvalue(),
                        file_name=uploaded_sql_file.name
                    )

                    if result["status"] == "ok":
                        st.success(f"[OK] {result['message']}")
                        st.info(f"Tables created: {', '.join(result['tables']) if result['tables'] else 'None'}")
                        if result.get('warnings'):
                            st.warning(f"[WARNING] {len(result['warnings'])} statement(s) had issues")
                        st.rerun()
                    else:
                        st.error(f"[ERROR] {result['message']}")

    # Show available databases
    databases = get_database_list()
    if databases:
        st.subheader("Available Databases")
        for db_name in sorted(databases.keys()):
            db_info = databases[db_name]
            is_confirming_delete = st.session_state.get(f"confirm_delete_db_{db_name}", False)

            with st.expander(f"[DB] {db_name}", expanded=is_confirming_delete):
                # Show metadata
                created_date = db_info.get('created_at', 'N/A')[:10]
                table_count = len(db_info.get('tables', []))
                st.caption(f"**Created:** {created_date} | **Tables:** {table_count}")

                if db_info.get('tables'):
                    st.caption(f"**Tables:** {', '.join(db_info['tables'])}")

                # Get and show schema
                schema = get_database_schema(db_name)
                if "error" not in schema:
                    with st.expander("View Schema", expanded=False):
                        for table_name, table_info in schema.get('tables', {}).items():
                            st.markdown(f"**{table_name}** ({table_info['row_count']} rows)")
                            col_names = [col['name'] for col in table_info['columns']]
                            col_types = [col['type'] for col in table_info['columns']]
                            st.caption(", ".join([f"{n}: {t}" for n, t in zip(col_names, col_types)]))

                # AI-suggested queries
                with st.expander("Sample Queries", expanded=False):
                    st.markdown("**Sample queries you can ask the AI to run:**")
                    tables = db_info.get('tables', [])
                    if tables:
                        primary_table = tables[0]
                        st.code(f"SELECT * FROM {primary_table} LIMIT 5", language="sql")
                        st.code(f"SELECT COUNT(*) FROM {primary_table}", language="sql")
                        if len(tables) > 1:
                            st.code(f"SELECT * FROM {primary_table} JOIN {tables[1]} ON ...", language="sql")
                        st.caption("[TIP] Use these in your chat: 'Run this query against the {database_name}' or 'Show me all data from {table_name}'")

                # Delete button
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Delete Database", key=f"delete_db_{db_name}"):
                        st.session_state[f"confirm_delete_db_{db_name}"] = True
                        st.rerun()

                # HITL Confirmation for database deletion
                if st.session_state.get(f"confirm_delete_db_{db_name}", False):
                    st.warning(f"[CONFIRM] Are you sure you want to delete '{db_name}'? This cannot be undone.")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("Yes, Delete", key=f"confirm_delete_db_yes_{db_name}", type="primary"):
                            delete_result = delete_database(db_name)
                            if delete_result["status"] == "ok":
                                st.success("Database deleted")
                                st.session_state[f"confirm_delete_db_{db_name}"] = False
                                st.rerun()
                            else:
                                st.error(f"Error: {delete_result['message']}")
                    with col_cancel:
                        if st.button("Cancel", key=f"confirm_delete_db_no_{db_name}"):
                            st.session_state[f"confirm_delete_db_{db_name}"] = False
                            st.rerun()

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
                    st.session_state[f"confirm_delete_chat_{thread['id']}"] = True

            # HITL Confirmation for chat deletion
            if st.session_state.get(f"confirm_delete_chat_{thread['id']}", False):
                st.warning(f"⚠️ Delete chat '{thread['label']}'? This cannot be undone.")
                col_confirm, col_cancel = st.columns([1, 1])
                with col_confirm:
                    if st.button("Yes, Delete", key=f"confirm_delete_chat_yes_{thread['id']}", type="primary"):
                        delete_thread(thread["id"])
                        st.session_state["threads"] = [t for t in st.session_state["threads"] if t["id"] != thread["id"]]
                        if st.session_state["current_thread_id"] == thread["id"]:
                            st.session_state["chat_started"] = False
                            st.session_state["current_thread_id"] = None
                            st.session_state["message_history"] = []
                        st.session_state[f"confirm_delete_chat_{thread['id']}"] = False
                        st.rerun()
                with col_cancel:
                    if st.button("Cancel", key=f"confirm_delete_chat_no_{thread['id']}"):
                        st.session_state[f"confirm_delete_chat_{thread['id']}"] = False
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

    st.divider()
    st.subheader("Pipeline Monitor")

    monitor_selection = st.multiselect(
        "Select monitors:",
        options=[
            "Commodity Prices",
            "Data Files",
            "API Health",
            "Database Health",
            "ChromaDB",
            "App Health",
            "All"
        ],
        default=[]
    )

    interval = st.selectbox(
        "Check interval:",
        options=[
            "Every 15 minutes",
            "Every 30 minutes",
            "Every hour",
            "Every 6 hours"
        ],
        index=1
    )

    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("Start Monitor", use_container_width=True, type="primary")
    with col2:
        stop_btn = st.button("Stop Monitor", use_container_width=True, type="secondary")

    if st.session_state.get("monitor_running"):
        st.success("Monitor: RUNNING")
        st.caption(f"Checking: {', '.join(st.session_state['monitor_selections'])}")
        st.caption(f"Interval: {st.session_state['monitor_interval']} min")
    else:
        st.info("Monitor: STOPPED")

    if st.session_state.get("monitor_running"):
        st.divider()
        st.caption("Report Actions:")

        report_col1, report_col2 = st.columns(2)
        with report_col1:
            gmail_now_btn = st.button("Email Report Now", use_container_width=True)
        with report_col2:
            slack_now_btn = st.button("Slack Report Now", use_container_width=True)

        schedule_btn = st.button("Schedule Reports", use_container_width=True)
        stop_reports_btn = st.button("Pause Reports", use_container_width=True)

## ------------------- Initialize chatbot and database ---------------------


## ------------------- Monitor Button Handlers ---------------------

if start_btn and not st.session_state.get("monitor_running"):
    if not monitor_selection:
        st.error("Select at least one monitor.")
    else:
        interval_map = {
            "Every 15 minutes": 15,
            "Every 30 minutes": 30,
            "Every hour": 60,
            "Every 6 hours": 360
        }
        interval_minutes = interval_map[interval]

        selections = monitor_selection
        if "All" in selections:
            selections = [
                "Commodity Prices",
                "Data Files",
                "API Health",
                "Database Health",
                "ChromaDB",
                "App Health"
            ]

        from monitoring.runner import start_background, run_selected_checks
        thread = start_background(selections, interval_minutes)

        st.session_state["monitor_running"] = True
        st.session_state["monitor_selections"] = selections
        st.session_state["monitor_interval"] = interval_minutes
        st.session_state["monitor_thread"] = thread

        results = run_selected_checks(selections)
        st.session_state["last_check_results"] = results

        from monitoring.reports.formatter import format_daily_report
        report = format_daily_report(results)

        st.session_state["message_history"].append({
            "role": "assistant",
            "content": f"Monitor started.\n\nInitial check:\n{report}"
        })

        st.session_state["awaiting_hitl"] = True
        st.session_state["hitl_context"] = "monitor_started"
        st.rerun()

if stop_btn and st.session_state.get("monitor_running"):
    st.session_state["monitor_running"] = False
    st.session_state["monitor_selections"] = []
    st.session_state["monitor_thread"] = None
    st.session_state["report_scheduled"] = False
    st.session_state["report_paused"] = False
    st.session_state["scheduled_time"] = None

    st.session_state["message_history"].append({
        "role": "assistant",
        "content": "Monitor stopped. All scheduled reports cancelled."
    })
    st.rerun()

if st.session_state.get("monitor_running") and gmail_now_btn:
    results = st.session_state.get("last_check_results")
    if results:
        st.session_state["awaiting_hitl"] = True
        st.session_state["hitl_context"] = "gmail_now"
        st.rerun()
    else:
        st.warning("No check results yet. Wait for first check to complete.")

if st.session_state.get("monitor_running") and slack_now_btn:
    results = st.session_state.get("last_check_results")
    if results:
        from monitoring.alerts.slack_alert import alert_daily
        alert_daily(results)

        st.session_state["message_history"].append({
            "role": "assistant",
            "content": "Report sent to Slack."
        })
        st.rerun()

if st.session_state.get("monitor_running") and schedule_btn:
    st.session_state["awaiting_hitl"] = True
    st.session_state["hitl_context"] = "schedule_report"
    st.rerun()

if st.session_state.get("monitor_running") and stop_reports_btn:
    st.session_state["report_paused"] = True

    st.session_state["message_history"].append({
        "role": "assistant",
        "content": (
            "Reports paused. Monitor continues running.\n"
            "Click 'Email Report Now' or 'Slack Report Now' to send manually.\n"
            "Click 'Schedule Reports' to resume."
        )
    })
    st.rerun()

## ------------------- Main Chat Area ---------------------

if not st.session_state["chat_started"]:
    st.markdown("# 🤖 Welcome to Your AI Chat Bot!")

    st.markdown("""
    ### What can I do?
    I'm powered by **15 amazing tools** that let me:

    **General Tools:**
    1. **📈 Stock Price** - Get real-time stock quotes and fundamentals
    2. **🌾 Commodity Price** - Get wheat, soy, corn, sugar prices
    3. **🕐 India Time** - Tell you the current date & time in India (IST)
    4. **🧮 Calculator** - Solve complex math with BODMAS & trigonometry
    5. **🔍 Web Search** - Search the web for latest information

    **NLP & Monitoring Tools:**
    6. **🧠 NLP Analysis** - Analyze text sentiment, extract keywords, summarize, NER
    7. **📊 Commodity Monitor** - Start real-time monitoring with sentiment + price alerts
    8. **🎯 Get Monitoring Results** - View monitoring data and alert history

    **Data Analysis Tools:**
    9. **📊 Analyze Data** - Analyze CSV/Excel files with semantic search (RAG)
    10. **🗄️ Analyze SQL** - Query SQLite database with SQL commands

    **Email Tools (Gmail):**
    11. **✉️ Send Email** - Send emails to anyone
    12. **📝 Create Draft** - Create email drafts
    13. **🔎 Search Email** - Search your Gmail messages
    14. **📧 Get Email** - Fetch specific email details
    15. **💬 Get Thread** - View email conversations

    ### Try asking me:
    - "What's the current price of wheat and corn?"
    - "Analyze the sentiment of this text: The market is booming with growth"
    - "Start monitoring soy prices every 30 minutes"
    - "Check my active monitoring tasks"
    - "What's the current price of Apple stock?"
    - "What time is it in India?"
    - "Calculate sin(pi/2) + sqrt(16)"
    - "Search for latest AI news"
    - "Show all users from USA in the database"
    - "Send an email to user@example.com with subject 'Hello' and message 'Hi there'"

    """)

    st.info("<-- Click **START CHAT** in the sidebar to begin")
else:
    st.title("Chat")

    for messages in st.session_state["message_history"]:
        with st.chat_message(messages['role']):
            st.markdown(messages['content'])

    ## ------------------- HITL Flows ---------------------

    if st.session_state.get("awaiting_hitl"):
        context = st.session_state.get("hitl_context")

        if context == "monitor_started":
            st.divider()
            st.warning("Monitor started. What would you like to do with the report?")

            h_col1, h_col2, h_col3, h_col4 = st.columns(4)

            with h_col1:
                if st.button("Email Now", key="h_email_now"):
                    st.session_state["awaiting_hitl"] = True
                    st.session_state["hitl_context"] = "gmail_now"
                    st.rerun()

            with h_col2:
                if st.button("Slack Now", key="h_slack_now"):
                    results = st.session_state["last_check_results"]
                    from monitoring.alerts.slack_alert import alert_daily
                    alert_daily(results)

                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": "Report sent to Slack."
                    })
                    st.session_state["awaiting_hitl"] = False
                    st.rerun()

            with h_col3:
                if st.button("Schedule", key="h_schedule"):
                    st.session_state["awaiting_hitl"] = True
                    st.session_state["hitl_context"] = "schedule_report"
                    st.rerun()

            with h_col4:
                if st.button("Skip", key="h_skip"):
                    st.session_state["awaiting_hitl"] = False
                    st.session_state["hitl_context"] = None
                    st.rerun()

        elif context == "gmail_now":
            results = st.session_state.get("last_check_results", {})
            from monitoring.reports.formatter import format_daily_report
            report = format_daily_report(results)

            st.divider()
            st.warning("Email Report Preview:")
            st.text_area(
                "Report content:",
                value=report[:500] + "..." if len(report) > 500 else report,
                height=200,
                disabled=True
            )

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                if st.button("Send Email", key="h_send_email", type="primary"):
                    from monitoring.alerts.gmail_alert import send_gmail_report
                    send_gmail_report(results)

                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": "Report sent to your Gmail inbox."
                    })
                    st.session_state["awaiting_hitl"] = False
                    st.session_state["hitl_context"] = None
                    st.rerun()

            with g_col2:
                if st.button("Cancel", key="h_cancel_email"):
                    st.session_state["awaiting_hitl"] = False
                    st.session_state["hitl_context"] = None
                    st.rerun()

        elif context == "schedule_report":
            st.divider()
            st.warning("Schedule recurring reports:")

            s_channel = st.radio(
                "Send to:",
                options=["Slack", "Gmail", "Both"],
                horizontal=True,
                key="schedule_channel"
            )

            s_time = st.time_input(
                "Daily report time:",
                value=None,
                key="schedule_time"
            )

            s_col1, s_col2 = st.columns(2)
            with s_col1:
                if st.button("Confirm Schedule", key="h_confirm_schedule", type="primary"):
                    import schedule
                    from monitoring.runner import run_all_checks

                    time_str = s_time.strftime("%H:%M") if s_time else "09:00"
                    channel = s_channel

                    def scheduled_job():
                        if not st.session_state.get("report_paused"):
                            results = run_all_checks()
                            st.session_state["last_check_results"] = results
                            report = format_daily_report(results)

                            if channel in ["Slack", "Both"]:
                                from monitoring.alerts.slack_alert import alert_daily
                                alert_daily(results)

                            if channel in ["Gmail", "Both"]:
                                from monitoring.alerts.gmail_alert import send_gmail_report
                                send_gmail_report(results)

                    schedule.every().day.at(time_str).do(scheduled_job)

                    st.session_state["report_scheduled"] = True
                    st.session_state["scheduled_time"] = time_str
                    st.session_state["report_paused"] = False

                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": (
                            f"Daily report scheduled at {time_str}.\n"
                            f"Channel: {channel}\n"
                            f"Click 'Pause Reports' to stop temporarily.\n"
                            f"Click 'Stop Monitor' to cancel everything."
                        )
                    })
                    st.session_state["awaiting_hitl"] = False
                    st.session_state["hitl_context"] = None
                    st.rerun()

            with s_col2:
                if st.button("Cancel", key="h_cancel_schedule"):
                    st.session_state["awaiting_hitl"] = False
                    st.session_state["hitl_context"] = None
                    st.rerun()

    user_input = st.chat_input("type here")

    if user_input:
        ## Monitor chat commands
        monitor_commands = {
            "stop monitoring": "stop_monitor",
            "pause reports": "pause_reports",
            "send report now": "gmail_now",
            "send to slack": "slack_now",
            "show monitor status": "monitor_status",
            "schedule report": "schedule_report"
        }

        def get_monitor_status() -> str:
            if not st.session_state.get("monitor_running"):
                return "Monitor is not running. Click 'Start Monitor' in sidebar."

            lines = [
                "Monitor Status: RUNNING",
                f"Checking: {', '.join(st.session_state['monitor_selections'])}",
                f"Interval: every {st.session_state['monitor_interval']} minutes",
            ]

            if st.session_state.get("report_scheduled"):
                lines.append(
                    f"Scheduled report: daily at {st.session_state['scheduled_time']}"
                )

            if st.session_state.get("report_paused"):
                lines.append("Reports: PAUSED")

            results = st.session_state.get("last_check_results")
            if results:
                from monitoring.reports.formatter import has_issues, format_issue_alert
                if has_issues(results):
                    lines.append("\nCurrent Issues:")
                    lines.append(format_issue_alert(results))
                else:
                    lines.append("\nAll systems: [OK]")

            return "\n".join(lines)

        command_executed = False
        for phrase, action in monitor_commands.items():
            if phrase in user_input.lower():
                if action == "stop_monitor":
                    st.session_state["monitor_running"] = False
                    st.session_state["monitor_selections"] = []
                    st.session_state["monitor_thread"] = None
                    st.session_state["report_scheduled"] = False
                    st.session_state["report_paused"] = False

                    st.session_state["message_history"].append({
                        "role": "user",
                        "content": user_input
                    })
                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": "Monitor stopped. All scheduled reports cancelled."
                    })
                    command_executed = True
                    break

                elif action == "pause_reports":
                    st.session_state["report_paused"] = True
                    st.session_state["message_history"].append({
                        "role": "user",
                        "content": user_input
                    })
                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": (
                            "Reports paused. Monitor continues running.\n"
                            "Type 'schedule report' to resume."
                        )
                    })
                    command_executed = True
                    break

                elif action == "gmail_now":
                    if st.session_state.get("monitor_running"):
                        st.session_state["awaiting_hitl"] = True
                        st.session_state["hitl_context"] = "gmail_now"
                        command_executed = True
                        break

                elif action == "slack_now":
                    if st.session_state.get("monitor_running"):
                        results = st.session_state.get("last_check_results")
                        if results:
                            from monitoring.alerts.slack_alert import alert_daily
                            alert_daily(results)
                            st.session_state["message_history"].append({
                                "role": "user",
                                "content": user_input
                            })
                            st.session_state["message_history"].append({
                                "role": "assistant",
                                "content": "Report sent to Slack."
                            })
                            command_executed = True
                            break

                elif action == "monitor_status":
                    st.session_state["message_history"].append({
                        "role": "user",
                        "content": user_input
                    })
                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": get_monitor_status()
                    })
                    command_executed = True
                    break

                elif action == "schedule_report":
                    if st.session_state.get("monitor_running"):
                        st.session_state["awaiting_hitl"] = True
                        st.session_state["hitl_context"] = "schedule_report"
                        command_executed = True
                        break

        if command_executed:
            st.rerun()

        st.session_state["message_history"].append({'role': 'user', 'content': user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Update thread label on first user message
        current_thread = next((t for t in st.session_state["threads"] if t["id"] == st.session_state["current_thread_id"]), None)
        if current_thread and current_thread["label"].startswith("Chat "):
            update_thread_label(st.session_state["current_thread_id"], user_input)

        CONFIG = RunnableConfig(configurable={"thread_id": st.session_state["current_thread_id"]})

        def response_generator():
            from langchain_core.messages import AIMessage, ToolMessage
            import re

            full_response = ""
            last_ai_message = None

            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"):

                # Only process AIMessage for display (skip ToolMessages and others)
                if isinstance(message_chunk, AIMessage):
                    last_ai_message = message_chunk
                    # Only yield if it has text content and no tool_calls
                    if hasattr(message_chunk, 'content') and message_chunk.content:
                        if not message_chunk.tool_calls:  # Skip if it's a tool call message
                            content_str = str(message_chunk.content) if not isinstance(message_chunk.content, str) else message_chunk.content
                            full_response += content_str
                            yield content_str
                elif isinstance(message_chunk, str):
                    full_response += message_chunk
                    yield message_chunk
                # Skip ToolMessage - don't display tool execution details

            # Extract plot paths from response
            plot_paths = re.findall(r'\[PLOT_IMAGE:([^\]]+)\]', full_response)

            # Remove plot markers from response for display
            display_response = re.sub(r'\[PLOT_IMAGE:[^\]]+\]\n?', '', full_response)

            # Only store if there's actual content to display
            if display_response.strip():
                st.session_state["message_history"].append({'role': 'assistant', 'content': display_response})

            # Store plots for display
            if plot_paths:
                st.session_state["pending_plots"] = plot_paths

        with st.chat_message("assistant"):
            st.write_stream(response_generator())

        # Display any generated plots
        if st.session_state.get("pending_plots"):
            st.divider()
            st.subheader("📊 Generated Plots")
            plot_paths = st.session_state.pop("pending_plots")

            for i, plot_path in enumerate(plot_paths):
                try:
                    if Path(plot_path).exists():
                        col = st.columns(1)[0]
                        with col:
                            st.image(plot_path, use_container_width=True)
                    else:
                        st.warning(f"Plot not found: {plot_path}")
                except Exception as e:
                    st.error(f"Could not display plot: {e}")
         