#!/usr/bin/env python3
"""Test suite for calculator_tool.py"""

import sys
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.calculator_tool import calculator


class CalculatorTester:
    """Base class for testing calculator tool functionality"""

    def __init__(self):
        """Initialize tester"""
        load_dotenv()
        self.results = {}

    def test_expression(self, expression):
        """Test a single expression"""
        print(f"Expression: {expression}")
        result = calculator.invoke({"expression": expression})
        self.results[expression] = result
        print(f"{result}\n")
        return result

    def run_tests(self):
        """Run comprehensive calculator tests"""
        print("[OK] Testing Calculator Tool\n")

        test_cases = [
            # Basic arithmetic with BODMAS
            ("2 + 3 * 4", "BODMAS: multiplication before addition"),
            ("(2 + 3) * 4", "BODMAS: parentheses first"),
            ("10 - 5 + 3", "Left-to-right: 8"),
            ("20 / 4 * 2", "Left-to-right: 10"),
            ("2 ** 3", "Power: 8"),
            ("10 % 3", "Modulo: 1"),

            # Trigonometric functions (radians)
            ("sin(0)", "sin(0) = 0"),
            ("cos(0)", "cos(0) = 1"),
            ("sin(pi/2)", "sin(π/2) = 1"),
            ("cos(pi)", "cos(π) = -1"),
            ("tan(0)", "tan(0) = 0"),

            # Square root and power
            ("sqrt(16)", "Square root: 4"),
            ("sqrt(2)", "Square root: 1.414..."),
            ("2 ** 10", "Power: 1024"),

            # Logarithmic
            ("log(e)", "Natural log of e = 1"),
            ("log10(100)", "Log base 10 of 100 = 2"),
            ("exp(1)", "e^1 = e ≈ 2.718"),

            # Complex expressions
            ("(5 + 3) * 2 - 4 / 2", "Complex with BODMAS: 14"),
            ("sqrt(16) + sqrt(9)", "Multiple functions: 7"),
            ("sin(pi/6) + cos(pi/3)", "Trig sum: 1"),

            # Other functions
            ("abs(-10)", "Absolute value: 10"),
            ("ceil(3.2)", "Ceiling: 4"),
            ("floor(3.8)", "Floor: 3"),

            # Constants
            ("pi", "π constant"),
            ("e", "e constant"),
            ("pi * 2", "2π"),
        ]

        for expression, description in test_cases:
            print(f"{'='*60}")
            print(f"Test: {description}")
            print(f"{'='*60}")
            self.test_expression(expression)

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = CalculatorTester()
    tester.run_tests()
