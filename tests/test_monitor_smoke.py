"""Smoke tests for monitoring checks."""
import pytest


def test_commodity_check():
    from monitoring.checks.commodity_check import check_commodities
    result = check_commodities()
    assert isinstance(result, dict)
    assert "status" in result or "commodities" in result


def test_file_check():
    from monitoring.checks.file_check import check_files
    result = check_files()
    assert isinstance(result, dict)


def test_api_check():
    from monitoring.checks.api_check import check_apis
    result = check_apis()
    assert isinstance(result, dict)


def test_app_check():
    from monitoring.checks.app_check import check_app
    result = check_app()
    assert isinstance(result, dict)


def test_chromadb_check():
    from monitoring.checks.chromadb_check import check_chromadb
    result = check_chromadb()
    assert isinstance(result, dict)


def test_database_check():
    from monitoring.checks.database_check import check_databases
    result = check_databases()
    assert isinstance(result, dict)


def test_run_all_checks():
    from monitoring.runner import run_all_checks
    results = run_all_checks()
    assert isinstance(results, dict)
    assert "commodities" in results
    assert "files" in results
    assert "apis" in results
    assert "databases" in results
    assert "chromadb" in results
    assert "app" in results
