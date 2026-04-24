#!/usr/bin/env python3
"""Test all tools integrated in backend"""

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
    """Test the backend with all tools"""

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    test_queries = [
        "What's the current price of Apple stock?",
        "Calculate 2 + 3 * 4 + sqrt(16)",
        "What time is it in India?",
        "What holidays are coming up in India?",
        "Is today a holiday in India?",
        "Give me the square root of 256",
        "What's the stock price of MSFT and the time in India?",
    ]

    print("[OK] Testing All Tools Integration\n")

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        input_message = HumanMessage(content=query)
        try:
            result = chatbot.invoke(
                {"messages": [input_message]},
                config,
                timeout=15
            )

            # Get the last message from the response
            last_message = result["messages"][-1]
            response_text = last_message.content[:200] if len(last_message.content) > 200 else last_message.content
            print(f"Response: {response_text}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")

if __name__ == "__main__":
    test_backend()
