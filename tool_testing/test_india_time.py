#!/usr/bin/env python3
"""Test suite for india_time_tool.py"""

import os
import sys
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.india_time_tool import get_india_time


class IndiaTimeToolTester:
    """Base class for testing India time tool functionality"""

    def __init__(self):
        """Initialize tester"""
        load_dotenv()
        self.results = {}

    def test_india_time(self):
        """Test India time tool"""
        print(f"\n{'='*60}")
        print("Testing: India Current Time")
        print(f"{'='*60}")
        result = get_india_time.invoke({})
        self.results["india_time"] = result
        print(result)
        return result

    def run_tests(self):
        """Run tests"""
        print("[OK] Testing India Time Tool\n")
        self.test_india_time()
        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = IndiaTimeToolTester()
    tester.run_tests()
