#!/usr/bin/env python3
"""Test suite for calender_tool.py"""

import os
import sys
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.calender_tool import get_holidays


class CalenderToolTester:
    """Base class for testing calendar tool functionality"""

    def __init__(self, test_queries=None, country_code="US"):
        """
        Initialize tester with optional list of test queries

        Args:
            test_queries: List of test queries to run
            country_code: Country code for holidays (default: US)
        """
        load_dotenv()
        os.environ["HOLIDAY_COUNTRY"] = country_code
        self.country_code = country_code
        self.test_queries = test_queries or [
            "",  # Today's holidays (default)
            "2026",  # All holidays for 2026
            "january",  # January holidays
            "july",  # July holidays
            "list all",  # Full year list
        ]
        self.results = {}

    def test_single_query(self, query):
        """
        Test a single query

        Args:
            query: Query string to test

        Returns:
            Result string from get_holidays
        """
        display_query = query if query else "default (today)"
        print(f"\n{'='*60}")
        print(f"Query: {display_query}")
        print(f"{'='*60}")
        result = get_holidays.invoke({"query": query})
        self.results[display_query] = result
        print(result)
        return result

    def run_tests(self):
        """Run tests for all configured queries"""
        print(f"[OK] Testing Calendar Tool (Country: {self.country_code})\n")

        for query in self.test_queries:
            self.test_single_query(query)

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = CalenderToolTester()
    tester.run_tests()
