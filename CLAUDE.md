# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

**Installation:**
```bash
pip install -r requirements.txt
```

**Environment Setup:**
Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
```

**Run the chatbot:**
```bash
streamlit run frontend.py
```

The UI will be available at `http://localhost:8501`

## Architecture

The project is a stateful conversational chatbot with a **graph-based backend** and **web-based frontend**.

### Backend Architecture (`backend.py`)

The backend uses **LangGraph StateGraph** to manage conversation flow:

- **ChatState**: TypedDict defining the conversation state with `messages` (Annotated list using `add_messages` reducer)
- **chat_node**: Single processing node that invokes the LLM with accumulated message history
- **Checkpointer**: Currently uses `InMemorySaver` for session-only storage; planned migration to `SqliteSaver`
- **Graph**: Linear flow (START → chat_node → END) compiled with checkpointing support

**Key Design Pattern:**
- Messages reducer (`add_messages`) automatically merges new messages into state history
- Thread-based conversation management via `RunnableConfig` with `thread_id` parameter
- Streaming support: Backend graph can stream individual message chunks

### Frontend Architecture (`frontend.py`)

Streamlit-based UI with session management:

- **Session State Management**: Maintains `chat_started`, `current_thread_id`, `threads` list, and `message_history`
- **Thread Management**: Each conversation is a separate thread with UUID identifier
- **Hybrid State Pattern**: 
  - UI state (message_history) stored in Streamlit `session_state`
  - Conversation state persisted in backend checkpointer via `thread_id`
  - `load_thread_messages()` retrieves full history from backend when switching threads
- **Streaming Integration**: Uses `st.write_stream()` to display LLM responses in real-time
- **UI Layout**: Sidebar for thread/chat history, main area for message display and input

**Key Components:**
- `new_thread_id()`: Generate unique identifier for conversations
- `load_thread_messages()`: Fetch conversation history from checkpointer
- `switch_to_thread()`: Switch active conversation and reload history

## Development Notes

### Adding New Nodes
To extend the graph with additional processing:
1. Create a new node function with signature: `def node_name(state: chatState) -> dict`
2. Add to graph: `graph.add_node("node_name", node_name)`
3. Define edges between nodes
4. Re-compile with checkpointer

### Conversation State Management
- Backend stores checkpoints per `thread_id`
- Frontend UI state resets per session (not persistent across page reloads)
- When resuming a thread, `load_thread_messages()` retrieves from backend checkpointer
- Current limitation: InMemorySaver is ephemeral; data lost on app restart

### LLM Configuration
The LLM is instantiated at module level:
```python
llm_model = ChatOpenAI()  # Uses OPENAI_API_KEY from environment
```

To change model or parameters, edit this line. Common options:
```python
ChatOpenAI(model="gpt-4o", temperature=0.7, max_tokens=2048)
```

### Streaming Behavior
- Backend supports streaming via `chatbot.stream(state, config, stream_mode="messages")`
- Frontend uses `st.write_stream()` to render chunks as they arrive
- Requires compatible LLM (OpenAI supports streaming)

## Future Roadmap

1. **Persistence**: Replace `InMemorySaver` with `SqliteSaver` for conversation persistence across restarts
2. **Database Schema**: Define conversation metadata (thread name, created_at, updated_at)
3. **Multi-node Workflows**: Add routing logic, RAG retrieval nodes, tool use
4. **Error Handling**: Add try-catch in nodes for robustness
5. **RAG Integration**: Integrate ChromaDB (already in requirements.txt) for document retrieval

## Testing

No automated tests currently exist. To manually test:
1. Run `streamlit run frontend.py`
2. Click "START CHAT" to create a thread
3. Send messages and verify responses
4. Click "NEW CHAT" to create additional threads
5. Click on previous threads to verify history loads correctly

The `demo_chat.ipynb` notebook provides an example of using the backend directly in Python.

## Known Issues

- **Pydantic V1 Warning**: LangChain uses `pydantic.v1` for compatibility; non-critical warning with Python 3.14
- **Flask Unused**: `flask>=3.1.0` is in requirements.txt but not currently used (Flask API mode removed)
