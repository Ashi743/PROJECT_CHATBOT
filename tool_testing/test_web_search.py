#!/usr/bin/env python3
"""Test suite for web_search_tool.py with DuckDuckGo"""

import sys
import os
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.web_search_tool import web_search


class WebSearchTester:
    """Base class for testing web search tool functionality"""

    def __init__(self, test_queries=None):
        """
        Initialize tester with optional list of test queries

        Args:
            test_queries: List of test queries to run
        """
        load_dotenv()
        self.test_queries = test_queries or [
            "latest AI news",
            "climate change 2026",
            "Python programming tips",
            "stock market trends",
        ]
        self.results = {}

    def test_single_query(self, query, num_results=3):
        """
        Test a single search query

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            Result string from web_search
        """
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Results: {num_results}")
        print(f"{'='*60}")
        result = web_search.invoke({"query": query, "num_results": num_results})
        self.results[query] = result
        print(result)
        return result

    def run_tests(self):
        """Run tests for all configured queries"""
        print("[OK] Testing Web Search Tool with DuckDuckGo\n")
        print("Note: DuckDuckGo search is free and requires no API key!\n")

        for query in self.test_queries:
            self.test_single_query(query, num_results=3)

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = WebSearchTester()
    tester.run_tests()
