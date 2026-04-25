#!/usr/bin/env python3
"""Test tool execution in the chatbot backend."""

import sys
import json
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from backend import chatbot
from uuid import uuid4

# Test configuration
config = RunnableConfig(configurable={"thread_id": str(uuid4())})

test_queries = [
    "What time is it in India right now? Give me the exact current time.",
    "Tell me what the current time is in Tokyo, London, and New York",
    "What are the upcoming holidays in India for the next 3 months?",
    "Get me the current time in Mumbai",
]

print("[TEST] Running tool execution tests...\n")

for query in test_queries:
    print(f"[QUERY] {query}")
    print("-" * 80)

    try:
        messages = []
        for chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=query)]},
            config=config,
            stream_mode="messages"
        ):
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                print(f"[TOOL_CALLS] {json.dumps([{'name': tc['name'], 'args': tc['args']} for tc in chunk.tool_calls], indent=2)}")
            if hasattr(chunk, "content") and chunk.content:
                print(f"[RESPONSE] {chunk.content}")
            messages.append(chunk)

        print(f"[OK] Query executed, {len(messages)} messages returned")

    except Exception as e:
        print(f"[ERROR] {str(e)}")

    print()

print("[DONE] Tool execution tests completed")
