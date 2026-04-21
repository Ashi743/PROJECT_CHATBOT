# Tool Testing Suite

This folder contains all test files for the chatbot and its integrated tools.

## Overview

13 comprehensive test files organized by tool and integration level.

---

## Test Files Organization

### Individual Tool Tests

#### 1. **test_stock.py**
- Tests stock price fetching via yfinance
- Checks: AAPL, TSLA, GOOGL, MSFT
- Validates: Price, fundamentals, formatting
- **Run**: `python test_stock.py`

#### 2. **test_india_time.py**
- Tests India time tool (IST)
- Checks: Date, time, timezone
- Validates: Correct time in India
- **Run**: `python test_india_time.py`

#### 3. **test_calculator.py**
- Tests advanced calculator
- Checks: BODMAS, trigonometry, math functions
- Tests: 20+ expressions
- **Run**: `python test_calculator.py`

#### 4. **test_calender_calendarific.py**
- Tests Calendarific API for holidays
- Checks: Today's holidays, upcoming, full year
- Supports: 200+ countries
- **Setup**: Requires CALENDARIFIC_API_KEY
- **Run**: `python test_calender_calendarific.py`

#### 5. **test_web_search.py**
- Tests Tavily web search API
- Checks: Search results, quick answers
- Tests: AI news, climate, programming tips
- **Setup**: Requires TAVILY_API_KEY
- **Run**: `python test_web_search.py`

#### 6. **test_telegram_alert.py**
- Tests Telegram alert sending
- Checks: All 5 alert types
- Tests: Info, success, warning, error, critical
- **Setup**: Requires TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID
- **Run**: `python test_telegram_alert.py`

---

### Backend Integration Tests

#### 7. **test_backend_integration.py**
- Tests backend with all tools
- Uses: Stock, India time, calculator, holidays
- Validates: Tool selection and execution
- **Run**: `python test_backend_integration.py`

#### 8. **test_backend_debug.py**
- Debug test for backend
- Shows: Message types and tool calls
- Validates: LLM decision making
- **Run**: `python test_backend_debug.py`

#### 9. **test_calculator_backend.py**
- Tests calculator integration in backend
- Validates: Math expressions via chatbot
- **Run**: `python test_calculator_backend.py`

#### 10. **test_new_tools.py**
- Tests India time tool with backend
- Validates: Multiple tools working together
- **Run**: `python test_new_tools.py`

#### 11. **test_web_search_backend.py**
- Tests web search integration in backend
- Validates: Search results through chatbot
- **Run**: `python test_web_search_backend.py`

---

### Complete System Tests

#### 12. **test_all_tools.py**
- Tests all 6 tools working together
- Comprehensive integration test
- Tests: Stock, calculator, India time, holidays, web search, telegram
- Validates: Multi-tool support
- **Run**: `python test_all_tools.py`

---

### Legacy/Reference Tests

#### 13. **test_calender.py**
- Legacy calendar test (Nager.Date API)
- Reference for previous implementation
- **Status**: Superseded by test_calender_calendarific.py

---

## Quick Reference

### Run Individual Tool Tests
```bash
python test_stock.py                    # Stock prices
python test_india_time.py               # India time
python test_calculator.py               # Calculator
python test_calender_calendarific.py    # Holidays (requires API key)
python test_web_search.py               # Web search (requires API key)
python test_telegram_alert.py           # Telegram (requires bot setup)
```

### Run Backend Integration Tests
```bash
python test_backend_integration.py      # Full integration
python test_backend_debug.py            # Debug tool calls
python test_calculator_backend.py       # Calculator + backend
python test_new_tools.py                # India time + backend
python test_web_search_backend.py       # Web search + backend
python test_all_tools.py                # All 6 tools together
```

---

## Test Coverage

| Tool | Individual Test | Backend Test | All Tools Test |
|------|-----------------|--------------|----------------|
| Stock Price | ✓ test_stock.py | - | ✓ test_all_tools.py |
| India Time | ✓ test_india_time.py | ✓ test_new_tools.py | ✓ test_all_tools.py |
| Calculator | ✓ test_calculator.py | ✓ test_calculator_backend.py | ✓ test_all_tools.py |
| Holidays | ✓ test_calender_calendarific.py | ✓ test_backend_integration.py | ✓ test_all_tools.py |
| Web Search | ✓ test_web_search.py | ✓ test_web_search_backend.py | ✓ test_all_tools.py |
| Telegram Alert | ✓ test_telegram_alert.py | - | ✓ test_all_tools.py |

---

## Setup Requirements

### No Setup Needed
- Stock Price (test_stock.py)
- India Time (test_india_time.py)
- Calculator (test_calculator.py)

### Optional Setup (Free API Keys)
- Holidays: `CALENDARIFIC_API_KEY` from https://calendarific.com/
- Web Search: `TAVILY_API_KEY` from https://tavily.com/
- Telegram: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` from @BotFather

---

## Running All Tests

### Run all individual tool tests:
```bash
python test_stock.py
python test_india_time.py
python test_calculator.py
python test_calender_calendarific.py  # (with API key)
python test_web_search.py             # (with API key)
python test_telegram_alert.py         # (with bot setup)
```

### Run all backend integration tests:
```bash
python test_backend_integration.py
python test_backend_debug.py
python test_calculator_backend.py
python test_new_tools.py
python test_web_search_backend.py
python test_all_tools.py
```

### Run complete system test:
```bash
python test_all_tools.py
```

---

## Test Output Format

Each test provides:
- Configuration status
- Individual test results
- Success/failure for each component
- Error messages if applicable
- Timing information

Example:
```
[OK] API Key found

============================================================
Testing: AAPL
============================================================
Stock: Apple Inc. (AAPL)
Price: $268.54 (-1.65%)
Market Cap: $3.95T
P/E Ratio: 34.03
...
```

---

## Troubleshooting Tests

### "API Key not set"
- Get free API key from service
- Add to .env file
- Restart test

### "No results found"
- Check internet connection
- Verify API key is valid
- Try different search query

### "Connection timeout"
- API might be down
- Try again in a few moments
- Check API status page

---

## Test File Structure

```
tool_testing/
├── README.md                           # This file
├── test_stock.py                       # Stock price tests
├── test_india_time.py                  # India time tests
├── test_calculator.py                  # Calculator tests
├── test_calender_calendarific.py       # Holiday tests
├── test_web_search.py                  # Web search tests
├── test_telegram_alert.py              # Telegram tests
├── test_backend_integration.py         # Backend integration
├── test_backend_debug.py               # Backend debug
├── test_calculator_backend.py          # Calculator + backend
├── test_new_tools.py                   # India time + backend
├── test_web_search_backend.py          # Web search + backend
└── test_all_tools.py                   # Complete system test
```

---

## Test Classes

Most tests use class-based approach for reusability:

```python
class StockToolTester:
    def check_api_key(self): ...
    def test_single_symbol(self, symbol): ...
    def run_tests(self): ...
    def get_results(self): ...
```

This allows:
- Easy extension
- Reusable test logic
- Clear test structure
- Good for inheritance

---

## Best Practices

✓ Run individual tool tests first
✓ Check API keys before running tests
✓ Use test_all_tools.py for complete validation
✓ Check logs for detailed error messages
✓ Run tests after any code changes

---

## Test Results

All tests should show:
- Configuration validation
- Each tool execution
- Success/failure status
- Result summary

---

## For Developers

To add new tests:
1. Create `test_tool_name.py` in this folder
2. Use class-based structure
3. Include setup validation
4. Add to README.md

To modify existing tests:
1. Check dependencies
2. Update README.md if needed
3. Run test_all_tools.py to validate
4. Document changes

---

## Quick Start

```bash
# Test individual tools
cd tool_testing
python test_stock.py
python test_india_time.py
python test_calculator.py

# Test all tools together
python test_all_tools.py

# Run chatbot
cd ..
streamlit run frontend.py
```

---

**All tests are organized and ready to run!** ✅
