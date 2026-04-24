# Web Search Tool Setup with Tavily API

## Overview
The chatbot now includes a **Web Search Tool** that provides real-time web search using the **Tavily API**. This is a modern search API designed specifically for AI applications.

## Quick Setup

### Step 1: Get Your Free API Key
1. Visit: https://tavily.com/
2. Click "Sign Up" and create a free account
3. Go to your account dashboard
4. Copy your API key from the settings

### Step 2: Add to .env File
```env
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_api_key_from_tavily
```

### Step 3: Test the Setup
```bash
cd tool_testing
python test_web_search.py
```

## Features

### Search Capabilities
- **Real-time web search** - Get latest information from the internet
- **Customizable results** - Choose 1-10 results per query
- **Search depth** - Basic (quick) or Advanced (detailed)
- **AI-generated answers** - Quick summary answers for queries
- **Content snippets** - Relevant excerpts from search results

### Supported Queries
```
"latest AI news"
"climate change 2026"
"Python programming tips"
"artificial intelligence trends"
"what is machine learning"
"best practices for web development"
"how to learn data science"
```

### Response Includes
1. **Quick Answer** - AI-generated summary (if available)
2. **Search Results** - 1-10 results with:
   - Title
   - URL
   - Content snippet (first 200 characters)

## API Details

### Free Tier
- **Searches**: Unlimited
- **Speed**: Fast real-time indexing
- **Content**: Latest web results
- **No credit card required**

### Paid Tiers
- More features and priority support
- See https://tavily.com/pricing for details

## Response Example

```
Search Results for: 'latest AI news'
============================================================

Quick Answer:
Recent AI developments include breakthroughs in large language models, 
multimodal AI systems, and their deployment in real-world applications...

Top 3 Results:
-----------

1. OpenAI Announces GPT-5 with Reasoning Capabilities
   URL: https://openai.com/...
   Summary: In their latest announcement, OpenAI revealed GPT-5, which 
   features enhanced reasoning capabilities...

2. Google DeepMind Introduces New AI Architecture
   URL: https://deepmind.google.com/...
   Summary: Google DeepMind has announced a new AI architecture that 
   improves efficiency and performance...

3. Microsoft Azure AI Services Update
   URL: https://azure.microsoft.com/...
   Summary: Microsoft announced significant updates to their Azure AI 
   services, including new models and features...
```

## Usage Examples

### In the Chatbot
```
User: "Search for latest AI news"
Bot: [Displays search results with quick answer]

User: "Find information about climate change"
Bot: [Displays relevant climate change articles]

User: "What are the latest Python programming trends?"
Bot: [Displays recent Python development articles]

User: "Search for space exploration news"
Bot: [Displays space agency announcements and discoveries]
```

### Advanced Usage
```
User: "Search for quantum computing research"
Bot: [Basic search - quick results]

User: "Do a deep search for quantum computing breakthroughs"
Bot: [Advanced search - detailed analysis]
```

## Troubleshooting

### Error: "TAVILY_API_KEY not set in .env"
**Solution**: 
1. Get API key from https://tavily.com/
2. Add to .env file: `TAVILY_API_KEY=your_key_here`
3. Restart the chatbot

### Error: "No results found for: '{query}'"
**Solution**:
- Try a different, more specific query
- Use simpler search terms
- Example: Instead of "philosophical implications of AI", try "AI ethics"

### Error: "API request failed (403)"
**Solution**:
- Your API key might be invalid or revoked
- Check https://tavily.com/ to verify your key
- Regenerate your API key if needed

### Slow search results?
**Solution**:
- Use "basic" search depth for faster results
- Reduce number of results (try 3 instead of 10)
- Use simpler, more specific keywords

## Advanced Configuration

### Search Parameters

#### Number of Results
```python
web_search("AI news", num_results=5)  # Default: 5 results
web_search("AI news", num_results=1)  # Just the top result
web_search("AI news", num_results=10) # Maximum results
```

#### Search Depth
```python
web_search("AI news", search_depth="basic")    # Quick search
web_search("AI news", search_depth="advanced") # Detailed search
```

## Comparison with Other Tools

| Feature | Tavily | Google | Bing |
|---------|--------|--------|------|
| API-First Design | ✓ | ✓ | ✓ |
| AI-Optimized | ✓ | - | - |
| Free Tier | ✓ (Unlimited) | Limited | Limited |
| Real-time Results | ✓ | ✓ | ✓ |
| Content Freshness | High | High | High |

## File Structure
```
tools/
└── web_search_tool.py              # Main search implementation

tool_testing/
└── test_web_search.py              # Test suite

WEB_SEARCH_SETUP.md                 # This file
CLAUDE.md                           # Updated with search info
```

## Integration with Other Tools

The web search tool works seamlessly with other tools:

```
User: "Search for Tesla stock and compare with its current price"
Bot: [Uses web_search tool for news + get_stock_price for current price]

User: "What's new in AI? Also calculate the impact ratio"
Bot: [Uses web_search for news + calculator for analysis]
```

## Best Practices

### Do's
- ✓ Use specific, clear search terms
- ✓ Include dates for time-sensitive queries ("news 2026")
- ✓ Use basic depth for general questions
- ✓ Use advanced depth for research/detailed analysis
- ✓ Combine with other tools for richer answers

### Don'ts
- ✗ Don't use overly long search queries
- ✗ Don't search for private/personal information
- ✗ Don't expect results for very niche topics
- ✗ Don't rely solely on search - combine with other sources

## Testing

### Run Full Test Suite
```bash
cd tool_testing
python test_web_search.py
```

### Run Backend Integration Test
```bash
cd ..
python test_web_search_backend.py
```

### Manual Testing
```bash
python
>>> from tools.web_search_tool import web_search
>>> result = web_search.invoke({"query": "latest AI news", "num_results": 3})
>>> print(result)
```

## Support

- **Tavily Docs**: https://tavily.com/docs
- **API Reference**: https://tavily.com/api
- **Free API Key**: https://tavily.com/
- **GitHub**: https://github.com/tavily-ai

## Next Steps

1. ✅ Get free API key from Tavily
2. ✅ Add to .env file
3. ✅ Restart chatbot: `streamlit run frontend.py`
4. ✅ Test: "Search for latest AI news"
5. ✅ Enjoy real-time web search!

## Quick Command Reference

```bash
# Get API key
Visit https://tavily.com/

# Add to .env
TAVILY_API_KEY=tvly-xxxxxxxxxxxx

# Test setup
python tool_testing/test_web_search.py

# Run chatbot
streamlit run frontend.py

# Example queries
"Search for Python 3.14 features"
"Latest news about renewable energy"
"What's trending in web development?"
"Find information about quantum computing"
"Search for artificial intelligence breakthroughs"
```

