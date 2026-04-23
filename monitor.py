#!/usr/bin/env python3
"""
Monitoring system entry point.
Starts background monitoring for commodities, APIs, files, databases, ChromaDB, and app health.

Run independently: python monitor.py
"""

from monitoring.runner import start

if __name__ == "__main__":
    start()
