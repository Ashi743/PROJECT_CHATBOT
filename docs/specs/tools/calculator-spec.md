# Calculator Spec Sheet

## Purpose
Evaluate mathematical expressions with BODMAS/PEMDAS support.
Includes trigonometry, logarithms, and scientific functions.
No API required - pure Python math module.

## Status
[DONE]

## Trigger Phrases
- "what is 2 + 3 * 4"
- "calculate sqrt(16)"
- "sin(pi/2)"
- "solve 45 * 2 + 10 / 2"
- "log(10)"
- "2^10" or "2**10"

## Input Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| expression | str | yes | none | Math expression to evaluate |

## Output Format
Result: 14

Result: 4.0

Result: 1

## Dependencies
- math (Python stdlib)
- langchain_core.tools

## HITL
No - read-only calculation

## Supported Functions
- Basic: +, -, *, /, %, ** (power)
- Trigonometric: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh
- Other: sqrt, log, log10, exp, abs, ceil, floor, pow
- Constants: pi, e
- Symbol support: ^ → **, π → pi, √ → sqrt

## Chaining
Combines with:
- stock tool → "calculate PE ratio from earnings"
- commodity tool → "compute price averages"

## Known Issues
None - clean, safe evaluation using restricted namespace

## Test Command
python -c "
from tools.calculator_tool import calculator
print(calculator.invoke({'expression': '2 + 3 * 4'}))
"

## Bunge Relevance
Financial calculations for commodity price analysis and agricultural metrics.

## Internal Notes
- Uses eval() with restricted __builtins__ and safe_dict for security
- Complex number support in output
- Handles division by zero and invalid math operations
- Symbol substitution: ^, π, √ converted before evaluation
- Allowed characters whitelist: 0-9+-*/.%() abcdefghijklmnopqrstuvwxyzπe., 
