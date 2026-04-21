import streamlit as st
from backend import chatbot, retrieve_thread
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from uuid import uuid4

st.set_page_config(layout="wide")

## ----------------- utility functions for thread management -----------------
def new_thread_id():
    return str(uuid4())

def load_thread_messages(thread_id):
    config = RunnableConfig(configurable={"thread_id": thread_id})
    state = chatbot.get_state(config)
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
    st.title("My Conversations")

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
            if st.button(thread["label"], key=f"thread_{thread['id']}", use_container_width=True):
                switch_to_thread(thread["id"])
                st.rerun()

if not st.session_state["chat_started"]:
    st.markdown("# Welcome to Chat App!")
    st.info("<-- Click **START CHAT** in the sidebar to begin")
else:
    st.title("Chat")

    for messages in st.session_state["message_history"]:
        with st.chat_message(messages['role']):
            st.text(messages['content'])

    user_input = st.chat_input("type here")

    if user_input:
        st.session_state["message_history"].append({'role': 'user', 'content': user_input})
        with st.chat_message("user"):
            st.text(user_input)

        config = RunnableConfig(configurable={"thread_id": st.session_state["current_thread_id"]})

        def response_generator():
            full_response = ""
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=config,
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
         