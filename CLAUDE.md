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
OPENAI_API_KEY=your_openai_key_here
CALENDARIFIC_API_KEY=your_api_key_here  (optional, for holidays)
HOLIDAY_COUNTRY=IN                       (optional, defaults to IN)
```

**Required Keys:**
- `OPENAI_API_KEY` - Get from OpenAI (required)

**Optional Keys (Free Tier Available):**
- `CALENDARIFIC_API_KEY` - Get free key from https://calendarific.com/ (100 requests/month)
- `HOLIDAY_COUNTRY` - Holiday country code (defaults to IN for India)

**Run the chatbot:**
```bash
streamlit run frontend.py
```

The UI will be available at `http://localhost:8501`

## Architecture

The project is a stateful conversational chatbot with a **graph-based backend** and **web-based frontend**.

### Backend Architecture (`backend.py`)

The backend uses **LangGraph StateGraph** to manage conversation flow with tool integration:

- **ChatState**: TypedDict defining the conversation state with `messages` (Annotated list using `add_messages` reducer)
- **chat_node**: Processing node that invokes the LLM with accumulated message history
- **tool_node**: Execution node that handles tool calls (stock prices, holidays)
- **Graph Flow**: START → chat_node → [conditional: tools or END] → chat_node (loops for multi-turn tool use)
- **Checkpointer**: Uses `SqliteSaver` for persistent conversation storage across sessions

**Available Tools:**
- **get_stock_price**: Fetch current stock prices and fundamentals using yfinance (free, no API key required)
  - Input: Stock ticker symbol (e.g., "AAPL", "TSLA", "GOOGL", "RELIANCE.BO")
  - Returns: Price, change %, OHLC, volume, market cap, P/E ratio, 52-week high/low
  
- **get_india_time**: Get current date and time in India (IST - Indian Standard Time)
  - Input: None
  - Returns: Current date, time, and timezone
  
- **calculator**: Advanced mathematical expression evaluator with BODMAS and trigonometry
  - Input: Mathematical expression (e.g., "2 + 3 * 4", "sin(pi/2)", "sqrt(16)")
  - Supports: Basic arithmetic (+, -, *, /, %, **), parentheses, BODMAS/PEMDAS
  - Functions: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, sqrt, log, log10, exp, abs, ceil, floor, pow
  - Constants: pi, e
  - Returns: Calculated result

- **get_holidays**: Fetch public holidays using Calendarific API (requires free API key)
  - Input: Optional query (empty defaults to today, or specify year/month, or "list all")
  - Supports: 2000+ holidays for countries worldwide
  - Returns: Today's holidays, upcoming holidays, full year/month list, plus "On This Day" Wikipedia facts
  - API Key: Get free key at https://calendarific.com/ (100 requests/month)

- **web_search**: Search the web in real-time using DuckDuckGo (free, no API key required)
  - Input: Search query (e.g., "latest AI news", "climate change 2026")
  - Options: number of results (1-10)
  - Returns: Search results with titles, URLs, and summaries
  - No API key needed - completely free and anonymous

- **send_telegram_alert**: Send alerts/messages to Telegram
  - Input: Message text and alert type (info/success/warning/error/critical)
  - Returns: Confirmation that message was sent to Telegram
  - Setup: Get bot token from @BotFather, add to .env
  - Examples: "Alert: Task completed", "Send critical alert: System error"

**Key Design Pattern:**
- Messages reducer (`add_messages`) automatically merges new messages into state history
- Thread-based conversation management via `RunnableConfig` with `thread_id` parameter
- Tool binding: LLM decides when to call tools based on user queries
- Tool results passed back to LLM for context-aware responses
- Persistent storage of all conversation history with SqliteSaver

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

## Tools Directory Structure

```
tools/
├── stock_tool.py              # Stock price fetching tool (yfinance)
├── india_time_tool.py         # India time and date tool (zoneinfo)
├── calculator_tool.py         # Advanced calculator with BODMAS & trigonometry
├── calender_tool.py           # Holidays and calendar tool (Calendarific API)
├── web_search_tool.py         # Web search tool (Tavily API)
└── telegram_alert_tool.py     # Telegram alerts/notifications (BotFather)

tool_testing/
├── test_stock.py              # Stock tool test suite
├── test_india_time.py         # India time tool test suite
├── test_calculator.py         # Calculator tool test suite
├── test_calender_calendarific.py  # Calendar tool test suite (Calendarific)
├── test_web_search.py         # Web search tool test suite (Tavily)
└── test_telegram_alert.py     # Telegram alert tool test suite
```

Run tests from the root directory:
```bash
cd tool_testing
python test_stock.py
python test_calender.py
```

## Development Notes

### Adding New Tools
1. Create new tool in `tools/` directory using `@tool` decorator from `langchain_core.tools`
2. Add tool to the `tools` list in `backend.py` (line ~19)
3. Tool will automatically be available to the LLM once bound

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
