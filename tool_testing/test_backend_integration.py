#!/usr/bin/env python3
"""Test backend integration with tools"""

import sys
import os
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

# Set default country code for holidays tool
os.environ["HOLIDAY_COUNTRY"] = "US"

from backend import chatbot
from langchain_core.messages import HumanMessage
import uuid

def test_backend():
    """Test the backend with tool integration"""

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    test_queries = [
        "What's the current price of AAPL stock?",
        "What are the upcoming holidays in the US?",
        "Tell me about Tesla's stock performance",
        "Is today a holiday in America?",
    ]

    print("[OK] Testing Backend Tool Integration\n")

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
