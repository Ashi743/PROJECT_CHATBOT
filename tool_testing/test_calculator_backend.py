#!/usr/bin/env python3
"""Test backend integration with calculator tool"""

import sys
import os
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from backend import chatbot
from langchain.messages import HumanMessage
import uuid

def test_backend():
    """Test the backend with calculator tool"""

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    test_queries = [
        "Calculate 2 + 3 * 4",
        "What is the square root of 144?",
        "Calculate sin(pi/2)",
        "What is (10 + 5) * 2 - 3?",
        "Calculate log10(1000) + sqrt(16)",
        "What time is it in India?",
        "What's the stock price of AAPL?",
        "Calculate tan(0) + cos(0)",
    ]

    print("[OK] Testing Calculator Integration with Backend\n")

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        input_message = HumanMessage(content=query)
        result = chatbot.invoke(
            {"messages": [input_message]},
            config
        )

        # Get the last message from the response
        last_message = result["messages"][-1]
        print(f"Response: {last_message.content}\n")

if __name__ == "__main__":
    test_backend()
