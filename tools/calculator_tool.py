from langchain_core.tools import tool
import math
import re

@tool
def calculator(expression: str) -> str:
    """
    Advanced calculator that evaluates mathematical expressions with support for:
    - Basic operations: +, -, *, /, % (modulo), ** (power)
    - BODMAS/PEMDAS order of operations
    - Trigonometric functions: sin, cos, tan, asin, acos, atan
    - Other math functions: sqrt, log, log10, exp, abs, ceil, floor
    - Constants: pi, e

    Examples:
    - "2 + 3 * 4" returns 14 (BODMAS applied)
    - "sqrt(16)" returns 4
    - "sin(pi/2)" returns 1
    - "log(10)" returns 2.303 (natural log)
    - "45 * 2 + 10 / 2" returns 95
    """
    try:
        # Sanitize the expression
        expression = expression.strip()

        if not expression:
            return "[ERROR] Please provide a mathematical expression."

        # Create a safe namespace with math functions
        safe_dict = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'abs': abs,
            'ceil': math.ceil,
            'floor': math.floor,
            'pow': pow,
            'pi': math.pi,
            'e': math.e,
            'degrees': math.degrees,
            'radians': math.radians,
        }

        # Replace common mathematical notation
        expression = expression.replace('^', '**')  # ^ to ** for power
        expression = expression.replace('π', str(math.pi))  # π symbol
        expression = expression.replace('∏', str(math.pi))  # Alternative π
        expression = expression.replace('√', 'sqrt')  # √ symbol to sqrt

        # Validate expression contains only safe characters
        allowed_chars = set('0123456789+-*/.%() abcdefghijklmnopqrstuvwxyzπe., ')
        if not all(c in allowed_chars for c in expression.lower()):
            return "[ERROR] Expression contains invalid characters."

        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, safe_dict)

        # Format the result
        if isinstance(result, complex):
            return f"Result: {result.real:.6g} + {result.imag:.6g}i"
        else:
            # Remove unnecessary decimal places
            if isinstance(result, float):
                if result == int(result):
                    return f"Result: {int(result)}"
                else:
                    return f"Result: {result:.10g}"
            return f"Result: {result}"

    except ZeroDivisionError:
        return "[ERROR] Division by zero is not allowed."
    except ValueError as e:
        return f"[ERROR] Invalid value (e.g., sqrt of negative, invalid trig input). Details: {str(e)}"
    except SyntaxError:
        return "[ERROR] Invalid mathematical expression syntax."
    except NameError as e:
        return f"[ERROR] Unknown function or variable. {str(e)}"
    except Exception as e:
        return f"[ERROR] {str(e)}"
