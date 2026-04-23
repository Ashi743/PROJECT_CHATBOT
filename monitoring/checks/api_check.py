import time
import logging
import requests
import yfinance as yf
import smtplib
import os
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 1


def _retry_check(check_func, name: str) -> dict:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()
            check_func()
            response_ms = int((time.time() - start) * 1000)

            return {
                "status": "[OK]",
                "response_ms": response_ms,
                "attempts": attempt
            }
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"{name} check failed after {attempt} attempts: {e}")
                return {
                    "status": "[DOWN]",
                    "response_ms": None,
                    "attempts": attempt,
                    "error": str(e)
                }


def _check_duckduckgo():
    search = DuckDuckGoSearchRun()
    search("test")


def _check_yfinance():
    yf.Ticker("AAPL").history(period="1d")


def _check_calendarific():
    api_key = os.getenv("CALENDARIFIC_API_KEY")
    if not api_key:
        raise Exception("CALENDARIFIC_API_KEY not set")
    response = requests.get(
        "https://calendarific.com/api/v2/holidays",
        params={"api_key": api_key, "country": "US", "year": 2026},
        timeout=10
    )
    response.raise_for_status()


def _check_gmail_smtp():
    gmail_user = os.getenv("GMAIL_USER")
    if not gmail_user:
        raise Exception("GMAIL_USER not set")
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
    server.quit()


def _check_slack_webhook():
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise Exception("SLACK_WEBHOOK_URL not set")
    response = requests.post(
        webhook_url,
        json={"text": "monitoring-test"},
        timeout=10
    )
    response.raise_for_status()


def check_apis() -> dict:
    results = {}

    results["DuckDuckGo"] = _retry_check(_check_duckduckgo, "DuckDuckGo")
    results["yfinance"] = _retry_check(_check_yfinance, "yfinance")
    results["Calendarific"] = _retry_check(_check_calendarific, "Calendarific")
    results["Gmail SMTP"] = _retry_check(_check_gmail_smtp, "Gmail SMTP")
    results["Slack webhook"] = _retry_check(_check_slack_webhook, "Slack webhook")

    return results


if __name__ == "__main__":
    import json
    result = check_apis()
    print(json.dumps(result, indent=2, default=str))
