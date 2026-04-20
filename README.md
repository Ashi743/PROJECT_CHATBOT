# Chatbot with LangGraph

A Python-based conversational chatbot built with LangChain, LangGraph, and OpenAI's language models.

## Features

- **Stateful Conversations**: Uses LangGraph's StateGraph to manage conversation state
- **Message History**: Maintains conversation history with automatic message aggregation
- **SQLite Persistence**: Stores conversation checkpoints using SQLite
- **Chromadb** : Stores RAG based db
- **Thread Management**: Support for multiple conversation threads
- **OpenAI Integration**: Powered by GPT models via OpenAI API

## Prerequisites

- Python 3.9+
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Ashi743/PROJECT_CHATBOT.git
cd chat-bot
```

2. Create and activate virtual environment:
```bash
python -m venv myvenv
myvenv\Scripts\activate  # On Windows
source myvenv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Backend API
Run the Flask backend server:
```bash
python backend.py
```

### Interactive Demo
Run the Jupyter notebook for interactive testing:
```bash
jupyter notebook demo_chat.ipynb
```

## Project Structure

```
.
├── backend.py              # Core chatbot logic and Flask API
├── demo_chat.ipynb        # Interactive demo notebook
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── .env                   # Environment variables (not tracked)
└── chatbot.db             # SQLite database (auto-generated)
```

## Dependencies

- **langchain**: LLM framework
- **langgraph**: Graph-based workflow management
- **langchain-openai**: OpenAI integration
- **flask**: Web framework
- **python-dotenv**: Environment variable management
- **chromadb**: Vector database for embeddings
- **pydantic**: Data validation

## Key Components

### ChatState
Defines the conversation state structure with message history.

### chat_node
Processes messages through the LLM and returns responses.

### SqliteSaver
Persists conversation history to SQLite for recovery and thread management.

## Configuration

Environment variables can be set in `.env`:
- `OPENAI_API_KEY`: Your OpenAI API key
- Add additional variables as needed

## Development

To modify the chatbot behavior:
1. Edit `backend.py` to change the LLM model or add new nodes
2. Update `ChatState` to add new state variables
3. Modify the graph structure to add new workflow steps

## Database

The chatbot uses SQLite (`chatbot.db`) to store:
- Conversation checkpoints
- Message history
- Thread metadata

## License

MIT

## Author

Ashish Dangwal
