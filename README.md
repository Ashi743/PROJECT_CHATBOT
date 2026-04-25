# Chat Bot — Multi-Tool AI Assistant

AI-powered chatbot with real-time monitoring, data analysis, and intelligent document search.

## Quick Start

```bash
pip install -r requirements.txt
```

Then run the **3 services** (open 3 terminals):

```bash
# Terminal 1: Redis (memory & caching)
redis-server
# Or: docker run -d -p 6379:6379 --name redis redis:latest

# Terminal 2: ChromaDB (document search)
chroma run --host localhost --port 8000

# Terminal 3: The app
streamlit run frontend.py
```

Open http://localhost:8501 in your browser.

## What It Does

### Chat
- Talk to an AI with **19 tools** — search, stock prices, weather, analysis, file conversion
- Your conversation history is saved automatically
- Asks for approval before sending emails or alerts

### Data Analysis
- Upload CSV/Excel files and ask questions about the data
- Run SQL queries on your databases
- Get visualizations and insights

### Document Search
- Upload PDFs, Word docs, or spreadsheets
- Ask questions about the content — the AI searches through them intelligently
- Detects when it doesn't have enough info and searches the web

### System Monitoring
- Check API health, commodity prices, file integrity
- Get daily email or Slack reports
- See all issues in a clean dashboard

## Configuration

Create a `.env` file with:

```env
OPENAI_API_KEY=your-key-here
GMAIL_USER=your-email@gmail.com
GMAIL_RECIPIENT=where-to-send-reports@gmail.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
CALENDARIFIC_API_KEY=optional-api-key
```

## Data Storage

Everything is saved automatically:
- **Chat history** → SQLite database (persists between restarts)
- **Documents & search indexes** → ChromaDB (survives resets)
- **Memory & cache** → Redis (speeds up repeat queries 50-100x)

To back up Redis: `redis-cli BGSAVE`  
To back up ChromaDB: `cp -r data/chroma_db data/chroma_db.backup`

## Shutting Down

Press Ctrl+C in each terminal in reverse order:
1. Streamlit (terminal 3)
2. ChromaDB (terminal 2)  
3. Redis (terminal 1)

## Learn More

See `.claude/specs/` for detailed tool documentation and architecture details.
