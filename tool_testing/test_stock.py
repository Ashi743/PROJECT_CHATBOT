#!/usr/bin/env python3
"""Test suite for stock_tool.py"""

import os
import sys
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.stock_tool import get_stock_price


class StockToolTester:
    """Base class for testing stock tool functionality"""

    def __init__(self, symbols=None):
        """
        Initialize tester with optional list of stock symbols

        Args:
            symbols: List of stock symbols to test (default: ["AAPL", "TSLA", "GOOGL", "MSFT"])
        """
        load_dotenv()
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.symbols = symbols or ["AAPL", "TSLA", "GOOGL", "MSFT"]
        self.results = {}

    def check_api_key(self):
        """Check if API key is configured"""
        if not self.api_key:
            print("[FAIL] ALPHA_VANTAGE_API_KEY not found in .env file")
            print("Please add ALPHA_VANTAGE_API_KEY to your .env file")
            return False
        print("[OK] API Key found\n")
        return True

    def test_single_symbol(self, symbol):
        """
        Test a single stock symbol

        Args:
            symbol: Stock ticker symbol to test

        Returns:
            Result string from get_stock_price
        """
        print(f"\n{'='*60}")
        print(f"Testing: {symbol}")
        print(f"{'='*60}")
        result = get_stock_price.invoke({"symbol": symbol})
        self.results[symbol] = result
        print(result)
        return result

    def run_tests(self):
        """Run tests for all configured symbols"""
        if not self.check_api_key():
            return False

        for symbol in self.symbols:
            self.test_single_symbol(symbol)

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = StockToolTester()
    tester.run_tests()
