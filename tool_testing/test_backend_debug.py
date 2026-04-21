#!/usr/bin/env python3
"""Debug test for backend tool integration"""

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
from langchain.messages import HumanMessage
import uuid

def test_backend_debug():
    """Debug the backend with detailed output"""

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    test_query = "What are the upcoming holidays in the US?"

    print("[DEBUG] Testing Backend Tool Integration\n")
    print(f"Query: {test_query}")
    print(f"{'='*60}\n")

    input_message = HumanMessage(content=test_query)

    # Invoke the chatbot
    result = chatbot.invoke(
        {"messages": [input_message]},
        config
    )

    # Print all messages
    print(f"Number of messages: {len(result['messages'])}")
    print()

    for i, msg in enumerate(result["messages"]):
        print(f"\nMessage {i}:")
        print(f"  Type: {type(msg).__name__}")
        print(f"  Content: {msg.content[:100] if len(msg.content) > 100 else msg.content}")

        if hasattr(msg, "tool_calls"):
            print(f"  Tool calls: {msg.tool_calls}")

if __name__ == "__main__":
    test_backend_debug()
