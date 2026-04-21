#!/usr/bin/env python3
"""Test suite for web_search_tool.py with Tavily API"""

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
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.test_queries = test_queries or [
            ("latest AI news", 3, "basic"),
            ("climate change 2026", 3, "basic"),
            ("Python programming tips", 3, "basic"),
            ("stock market trends", 3, "basic"),
        ]
        self.results = {}

    def check_api_key(self):
        """Check if API key is configured"""
        if not self.api_key:
            print("[FAIL] TAVILY_API_KEY not found in .env file")
            print("\nTo get a free API key:")
            print("1. Visit: https://tavily.com/")
            print("2. Sign up for a free account")
            print("3. Get your API key from the dashboard")
            print("4. Add to .env: TAVILY_API_KEY=your_key_here")
            print("\nFree tier includes:")
            print("- Unlimited searches")
            print("- Real-time web search")
            print("- AI-optimized results")
            return False
        print("[OK] API Key found\n")
        return True

    def test_single_query(self, query, num_results=3, search_depth="basic"):
        """
        Test a single search query

        Args:
            query: Search query
            num_results: Number of results
            search_depth: Search depth (basic or advanced)

        Returns:
            Result string from web_search
        """
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Results: {num_results} | Depth: {search_depth}")
        print(f"{'='*60}")
        result = web_search.invoke({"query": query, "num_results": num_results, "search_depth": search_depth})
        self.results[query] = result
        print(result)
        return result

    def run_tests(self):
        """Run tests for all configured queries"""
        if not self.check_api_key():
            return False

        print("[OK] Testing Web Search Tool with Tavily\n")

        for query_tuple in self.test_queries:
            if isinstance(query_tuple, tuple):
                query, num_results, search_depth = query_tuple
            else:
                query = query_tuple
                num_results = 3
                search_depth = "basic"

            self.test_single_query(query, num_results, search_depth)

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = WebSearchTester()
    tester.run_tests()
