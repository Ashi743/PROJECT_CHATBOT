#!/usr/bin/env python3
"""Test suite for calender_tool.py with Calendarific API"""

import os
import sys
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.calender_tool import get_holidays


class CalenderCalendarificTester:
    """Base class for testing calendar tool with Calendarific API"""

    def __init__(self, test_queries=None, country_code="IN"):
        """
        Initialize tester with optional list of test queries

        Args:
            test_queries: List of test queries to run
            country_code: Country code for holidays (default: IN for India)
        """
        load_dotenv()
        os.environ["HOLIDAY_COUNTRY"] = country_code
        self.country_code = country_code
        self.api_key = os.getenv("CALENDARIFIC_API_KEY")
        self.test_queries = test_queries or [
            "",  # Today's holidays (default)
            "2026",  # All holidays for 2026
            "january",  # January holidays
            "march",  # March holidays
            "list all",  # Full year list
        ]
        self.results = {}

    def check_api_key(self):
        """Check if API key is configured"""
        if not self.api_key:
            print("[FAIL] CALENDARIFIC_API_KEY not found in .env file")
            print("\nTo get a free API key:")
            print("1. Visit: https://calendarific.com/")
            print("2. Sign up for a free account")
            print("3. Get your API key from the dashboard")
            print("4. Add to .env: CALENDARIFIC_API_KEY=your_key_here")
            print("\nFree tier includes:")
            print("- Up to 100 requests per month")
            print("- 2000+ holidays for countries worldwide")
            return False
        print("[OK] API Key found\n")
        return True

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
        print(f"Country: {self.country_code}")
        print(f"{'='*60}")
        result = get_holidays.invoke({"query": query})
        self.results[display_query] = result
        print(result)
        return result

    def run_tests(self):
        """Run tests for all configured queries"""
        if not self.check_api_key():
            return False

        print(f"[OK] Testing Calendar Tool with Calendarific (Country: {self.country_code})\n")

        for query in self.test_queries:
            self.test_single_query(query)

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = CalenderCalendarificTester()
    tester.run_tests()
