#!/usr/bin/env python3
"""Comprehensive test of all tools and RAG system."""

import sys
import json
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from backend import chatbot, tools
from uuid import uuid4

print("[TEST] Comprehensive System Validation")
print("=" * 80)

# Test 1: Verify tools are loaded
print("\n[1] TOOLS VERIFICATION")
print("-" * 80)
print(f"Total tools loaded: {len(tools)}")
tool_names = sorted([t.name for t in tools])
for name in tool_names:
    print(f"  [OK] {name}")

# Test 2: Create config
config = RunnableConfig(configurable={"thread_id": str(uuid4())})

# Test 3: Test queries
test_queries = [
    ("What time is it in India?", "WORLD_TIME"),
    ("Tell me about upcoming holidays in India next 3 months", "HOLIDAYS"),
    ("What's 25 + 17?", "CALCULATOR"),
    ("Search for machine learning tutorials", "WEB_SEARCH"),
    ("Tell me about LangChain framework", "RAG_QUERY"),
]

print(f"\n[2] TOOL EXECUTION TESTS")
print("-" * 80)

for query, test_type in test_queries:
    print(f"\nTest: {test_type}")
    print(f"Query: {query}")

    try:
        messages = []
        tool_calls_found = []
        response_text = ""

        for chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=query)]},
            config=config,
            stream_mode="messages"
        ):
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    tool_calls_found.append(tc["name"])
            if hasattr(chunk, "content") and chunk.content:
                response_text += str(chunk.content)
            messages.append(chunk)

        if tool_calls_found:
            print(f"  [OK] Tools called: {set(tool_calls_found)}")
        else:
            print(f"  [WARN] No tools called (LLM answered directly)")

        print(f"  [OK] Response: {response_text[:150]}...")

    except Exception as e:
        print(f"  [ERROR] {str(e)}")

# Test 4: RAG System Check
print(f"\n[3] RAG SYSTEM CHECK")
print("-" * 80)

try:
    from tools.RAG.retriever import get_indexed_documents

    docs = get_indexed_documents()
    print(f"[OK] Total documents indexed: {len(docs)}")

    # Group by name
    doc_names = {}
    for doc in docs:
        name = doc["name"]
        doc_names[name] = doc_names.get(name, 0) + 1

    for name, count in sorted(doc_names.items()):
        print(f"  - {name}: {count} chunks")

except Exception as e:
    print(f"[ERROR] RAG Error: {str(e)}")

# Test 5: Direct tool tests
print(f"\n[4] DIRECT TOOL TESTS")
print("-" * 80)

try:
    from tools.world_time_tool import get_world_time
    result = get_world_time.invoke({"city_or_timezone": "India"})
    print(f"[OK] get_world_time('India'): {result.split(chr(10))[0]}")
except Exception as e:
    print(f"[ERROR] get_world_time: {e}")

try:
    from tools.calculator_tool import calculator
    result = calculator.invoke({"expression": "25 + 17"})
    print(f"[OK] calculator('25 + 17'): {result}")
except Exception as e:
    print(f"[ERROR] calculator: {e}")

try:
    from tools.stock_tool import get_stock_price
    result = get_stock_price.invoke({"symbol": "AAPL"})
    print(f"[OK] get_stock_price('AAPL'): {result[:100]}")
except Exception as e:
    print(f"[ERROR] get_stock_price: {e}")

try:
    from tools.RAG.self_rag_tool import self_rag_query
    result = self_rag_query.invoke({"question": "What is machine learning?"})
    parsed = json.loads(result)
    print(f"[OK] self_rag_query: {parsed['answer'][:100]}...")
except Exception as e:
    print(f"[ERROR] self_rag_query: {e}")

print("\n" + "=" * 80)
print("[DONE] System validation complete")
