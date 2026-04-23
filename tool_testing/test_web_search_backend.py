#!/usr/bin/env python3
"""Test backend integration with web search tool"""

import sys
import os
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from backend import chatbot
from langchain_core.messages import HumanMessage
import uuid

def test_backend():
    """Test the backend with web search tool"""

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    test_queries = [
        "Search for latest AI news",
        "What's the current stock price of Tesla?",
        "Calculate 15 * 20 + 50",
        "What time is it in India?",
        "Find information about climate change",
        "Search the web for Python programming tips",
        "Give me latest news about space exploration",
    ]

    print("[OK] Testing Backend with Web Search Tool\n")

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        input_message = HumanMessage(content=query)
        try:
            result = chatbot.invoke(
                {"messages": [input_message]},
                config,
                timeout=20
            )

            # Get the last message from the response
            last_message = result["messages"][-1]
            response_text = last_message.content[:300] if len(last_message.content) > 300 else last_message.content
            print(f"Response: {response_text}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")

if __name__ == "__main__":
    test_backend()
