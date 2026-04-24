# Chat-Bot Tools Integration Summary

## Overview
The chatbot now has **3 fully integrated tools** that work seamlessly with the LLM backend.

## Tools Implemented

### 1. Stock Price Tool (yfinance)
**File:** `tools/stock_tool.py`
- Fetches real-time stock prices and fundamentals
- Uses yfinance (free, no API key required)
- Supports global stock symbols

**Capabilities:**
- Current price and price change (% and $)
- OHLC data (Open, High, Low, Close)
- Trading volume
- Market cap
- P/E ratio
- 52-week high/low
- Dividend yield

**Examples:**
- "What's the price of Apple stock?"
- "Get AAPL stock information"
- "Tell me about Tesla's fundamentals"

---

### 2. India Time Tool
**File:** `tools/india_time_tool.py`
- Returns current date and time in India (IST)
- Displays timezone information (UTC+5:30)
- Uses Python's built-in zoneinfo module

**Capabilities:**
- Current date with day name
- Current time (HH:MM:SS)
- Timezone indicator

**Examples:**
- "What time is it in India?"
- "What's the current date and time in India?"
- "What day is it in India?"

---

### 3. Advanced Calculator Tool
**File:** `tools/calculator_tool.py`
- Evaluates mathematical expressions with full BODMAS/PEMDAS support
- Includes trigonometric and logarithmic functions
- Safe expression evaluation with error handling

**Supported Operations:**
- Basic arithmetic: `+`, `-`, `*`, `/`, `%`, `**` (power)
- Parentheses for grouping: `(`, `)`
- Order of operations: BODMAS/PEMDAS

**Trigonometric Functions:**
- `sin`, `cos`, `tan` (all angles in radians)
- `asin`, `acos`, `atan` (inverse trig)
- `sinh`, `cosh`, `tanh` (hyperbolic)

**Other Functions:**
- `sqrt` - Square root
- `log` - Natural logarithm
- `log10` - Logarithm base 10
- `exp` - Exponential (e^x)
- `abs` - Absolute value
- `ceil` - Ceiling (round up)
- `floor` - Floor (round down)
- `pow` - Power function

**Constants:**
- `pi` - π (3.14159...)
- `e` - Euler's number (2.71828...)

**Features:**
- BODMAS order: `2 + 3 * 4` = 14 (multiplication before addition)
- Parentheses: `(2 + 3) * 4` = 20
- Angle in radians: `sin(pi/2)` = 1
- Symbol support: `√` → sqrt, `π` → pi, `^` → **

**Examples:**
- "Calculate 2 + 3 * 4"
- "What is the square root of 144?"
- "Calculate sin(pi/2)"
- "What is (10 + 5) * 2 - 3?"
- "Calculate log10(1000) + sqrt(16)"

---

## Test Results

### Calculator Tests (All Passing ✓)
```
BODMAS: 2 + 3 * 4 = 14
Parentheses: (2 + 3) * 4 = 20
Trigonometry: sin(pi/2) = 1
Power: 2 ** 10 = 1024
Modulo: 10 % 3 = 1
Square Root: sqrt(16) = 4
Logarithm: log10(100) = 2
Complex: (5 + 3) * 2 - 4 / 2 = 14
Constants: pi = 3.14159...
```

### Stock Tool Tests (All Passing ✓)
```
AAPL: $266.34 (-2.46%)
MSFT: $423.93 (+1.40%)
Market Cap: $3.91T
P/E Ratio: 33.76
52-Week High: $288.62
```

### India Time Tests (All Passing ✓)
```
Current Date: Tuesday, 21 April 2026
Current Time: 21:43:20 IST
Timezone: UTC+5:30
```

---

## Backend Integration

### Graph Architecture
```
START → chat_node → [conditional routing]
                    ├→ calculator (if math expression)
                    ├→ get_stock_price (if stock query)
                    ├→ get_india_time (if time query)
                    └→ END (if no tool needed)
        ↑_____________|
        └── tool_node (executes tools and passes results back)
```

### LLM Decision Making
- The LLM automatically decides which tool to use based on user query
- Tools are called with appropriate parameters
- Results are passed back to LLM for context-aware responses
- Multi-tool queries supported (e.g., "Get AAPL price and tell me the time in India")

---

## Files Structure

### Tools
```
tools/
├── stock_tool.py
├── india_time_tool.py
└── calculator_tool.py
```

### Tests
```
tool_testing/
├── test_stock.py
├── test_india_time.py
└── test_calculator.py
```

### Main Files
```
backend.py              - LangGraph with tool integration
frontend.py             - Streamlit UI
requirements.txt        - Dependencies (includes yfinance)
CLAUDE.md              - Documentation
TOOLS_SUMMARY.md       - This file
```

---

## Environment Setup

### Required
```env
OPENAI_API_KEY=your_openai_key_here
```

### Optional
None! All tools are free:
- Stock prices: yfinance (free)
- India time: Python built-in
- Calculator: Pure Python math

---

## Running Tests

From the root directory:
```bash
# Test individual tools
cd tool_testing
python test_stock.py
python test_india_time.py
python test_calculator.py

# Test backend integration
cd ..
python test_calculator_backend.py

# Run the chatbot
streamlit run frontend.py
```

---

## Usage Examples

### In the Chatbot
User: "Calculate 2 + 3 * 4"
Bot: "The result is 14"

User: "What's the price of Tesla stock?"
Bot: "TSLA is currently at $392.50 with a -2.03% change..."

User: "What time is it in India?"
Bot: "The current time in India is Tuesday, 21 April 2026, 21:43 IST..."

User: "Calculate sin(pi/2) + sqrt(16)"
Bot: "sin(pi/2) = 1 and sqrt(16) = 4, so the sum is 5"

---

## Security Features

- Expression validation before evaluation
- Only safe math functions exposed
- No arbitrary code execution
- Error handling for all edge cases
- Division by zero protection
- Invalid input detection

---

## Future Enhancements

Potential tools to add:
- Currency converter
- Weather information
- Unit converter
- Statistics calculator
- Matrix operations
- Derivatives/Integrals
