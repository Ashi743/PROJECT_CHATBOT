<img width="1280" height="734" alt="chatbot_stream" src="https://github.com/user-attachments/assets/456399ce-0821-4063-bfb2-ab7f742c814d" />
# LangGraph Conversational Chatbot

> A stateful, multi-turn chatbot with real-time streaming, thread management, and persistent conversation history — built with LangChain, LangGraph, and OpenAI.

---

## Why LangGraph?

Most chatbots lose context the moment a request completes. This project uses **LangGraph's `StateGraph`** to model conversation as a persistent state machine — each message appended to a typed state object (`ChatState`), with a checkpointer ensuring threads survive across interactions. The design intentionally separates graph logic (`backend.py`) from the UI layer (`frontend.py`), making it easy to swap in SQLite or Redis persistence without touching the frontend.

---

## Architecture

```
User (Streamlit UI)
        │
        ▼
  frontend.py  ──── thread_id ────▶  SqliteSaver (checkpointer)
        │                                    │
        ▼                                    ▼
  backend.py                        LangGraph StateGraph
   chatbot.stream()                  ┌─────────────────┐
        │                            │   START         │
        ▼                            │     │           │
  ChatOpenAI (GPT)                   │   chat_node     │
        │                            │     │           │
        └────── streaming ──────────▶│   END           │
                                     └─────────────────┘
```

**Key design decisions:**
- `add_messages` reducer on `ChatState` — appends new messages rather than replacing, enabling full conversation memory
- `stream_mode="messages"` — tokens stream to the UI in real-time as the LLM generates them
- UUID-based thread IDs — each conversation is fully isolated; switching threads restores prior history from the checkpointer

---

## Features

- **Stateful Conversations** — LangGraph `StateGraph` manages message history across turns
- **Real-time Streaming** — responses appear token-by-token via `chatbot.stream()`
- **Multi-thread Support** — create and switch between independent conversation threads
- **Thread History Restore** — switching to a past thread reloads messages from the checkpointer
- **Clean UI** — Streamlit-based chat interface with sidebar thread management

---

## Project Structure

```
.
├── backend.py          # LangGraph graph definition, ChatState, checkpointer
├── frontend.py         # Streamlit UI, thread management, streaming integration
├── demo_chat.ipynb     # Notebook demo of core graph logic
├── requirements.txt    # Dependencies
└── .env                # API keys (not tracked)
```

---

## Setup

**Prerequisites:** Python 3.11+, OpenAI API key

```bash
# 1. Clone
git clone https://github.com/Ashi743/PROJECT_CHATBOT.git
cd PROJECT_CHATBOT

# 2. Create virtual environment
python -m venv myvenv
myvenv\Scripts\activate       # Windows
source myvenv/bin/activate    # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
echo OPENAI_API_KEY=your_key_here > .env

# 5. Run
python -m streamlit run frontend.py
```

App available at `http://localhost:8501`

---

## Dependencies

| Package | Purpose |
|---|---|
| `langgraph` | State machine graph for conversation flow |
| `langchain-core` | Message types, runnables |
| `langchain-openai` | OpenAI LLM integration |
| `streamlit` | Web UI and streaming rendering |
| `python-dotenv` | Environment variable management |
| `chromadb` | Vector store (for upcoming RAG integration) |

---

## Roadmap

- [ ] SQLite persistence — conversation history survives app restarts
- [ ] RAG integration — ChromaDB already installed, documents Q&A planned
- [ ] Human-in-the-loop (HITL) — interrupt graph execution for user approval steps
- [ ] Multi-model support — swap between OpenAI, Claude, and local models
- [ ] Docker deployment

---

## Author

**Ashish Dangwal**  
[GitHub: Ashi743](https://github.com/Ashi743)

---

## License

MIT
