"""Smoke tests — tools return strings, do not crash."""
import pytest


def test_calculator_basic():
    from tools.calculator_tool import calculator
    result = calculator.invoke({"expression": "2+2"})
    assert isinstance(result, str)
    assert "4" in result


def test_world_time():
    from tools.world_time_tool import get_world_time
    result = get_world_time.invoke({})
    assert isinstance(result, str)
    assert len(result) > 0


def test_commodity_wheat():
    from tools.commodity_tool import get_commodity_price
    result = get_commodity_price.invoke({"commodity": "wheat"})
    assert isinstance(result, str)


def test_stock_price():
    from tools.stock_tool import get_stock_price
    result = get_stock_price.invoke({"symbol": "AAPL"})
    assert isinstance(result, str)


def test_web_search():
    from tools.web_search_tool import web_search
    result = web_search.invoke({"query": "Python", "num_results": 3})
    assert isinstance(result, str)


def test_nlp_analyze():
    from tools.nlp_tool import nlp_analyze
    result = nlp_analyze.invoke({"text": "This is great!", "task": "sentiment"})
    assert isinstance(result, str)


def test_monitor_startup_confirmation():
    from tools.monitor_tool import start_monitoring
    # First call should return confirmation request
    result = start_monitoring.invoke({"commodity": "wheat"})
    assert isinstance(result, str)
    assert "[CONFIRM]" in result or "confirm" in result.lower()


def test_stop_monitoring_no_active():
    from tools.monitor_tool import stop_monitoring
    result = stop_monitoring.invoke({"commodity": "wheat"})
    assert isinstance(result, str)
    # Should handle gracefully when no monitoring active


def test_get_holidays():
    from tools.world_time_tool import get_holidays
    result = get_holidays.invoke({"country": "US", "year": 2026})
    assert isinstance(result, str)
