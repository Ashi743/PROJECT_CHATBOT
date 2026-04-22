#!/usr/bin/env python3
"""
Standalone commodity monitoring script with scheduling.
Run independently: python monitor.py

Features:
- Monitors commodities every 30 minutes
- Daily summary at 9:00 AM with sentiment and price data
- Stores results silently
"""

import schedule
import time
from datetime import datetime
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('monitor.log')
    ]
)
logger = logging.getLogger(__name__)

# Import monitoring tools
from tools.commodity_tool import get_commodity_price
from tools.nlp_tool import nlp_analyze
from tools.web_search_tool import web_search

# Commodities to monitor
COMMODITIES = ["wheat", "soy", "corn", "sugar"]


def _send_telegram_alert(message: str):
    """
    Send alert via Telegram (placeholder for implementation).
    Can be extended to integrate with actual Telegram bot.
    """
    logger.warning(f"TELEGRAM ALERT: {message}")


def _save_monitoring_result(commodity: str, result: dict):
    """Save monitoring result to JSON log file."""
    log_file = Path("monitor_results.jsonl")

    with open(log_file, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "commodity": commodity,
            **result
        }) + "\n")


def _check_single_commodity(commodity: str):
    """
    Check a single commodity: search -> sentiment -> price -> alert if needed
    """
    try:
        logger.info(f"Checking {commodity}...")

        # Get current price
        price_result = get_commodity_price.invoke({"commodity": commodity})

        # Parse price change
        price_change = 0.0
        for line in price_result.split('\n'):
            if '%' in line and '(' in line:
                try:
                    change_str = line.split('(')[1].split('%')[0].strip()
                    price_change = float(change_str.replace('+', ''))
                    break
                except ValueError:
                    pass

        # Get news sentiment
        search_query = f"{commodity} price news market"
        news = web_search.invoke({"query": search_query, "num_results": 2})

        nlp_result = nlp_analyze.invoke({
            "text": news,
            "task": "sentiment"
        })

        # Parse sentiment
        sentiment = "neutral"
        if "NEGATIVE" in nlp_result:
            sentiment = "negative"
        elif "POSITIVE" in nlp_result:
            sentiment = "positive"

        result = {
            "sentiment": sentiment,
            "price_change": price_change,
            "status": "ok"
        }

        _save_monitoring_result(commodity, result)

        # Alert on negative sentiment + price drop > 1.5%
        if sentiment == "negative" and price_change < -1.5:
            alert_msg = (
                f"COMMODITY ALERT: {commodity.upper()}\n"
                f"Sentiment: NEGATIVE\n"
                f"Price Change: {price_change:.2f}%\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            _send_telegram_alert(alert_msg)

        logger.info(f"  {commodity}: {sentiment} sentiment, {price_change:+.2f}% change")

    except Exception as e:
        logger.error(f"Error checking {commodity}: {e}")
        _save_monitoring_result(commodity, {"error": str(e)})


def _monitor_all_commodities():
    """Monitor all commodities."""
    logger.info("=" * 50)
    logger.info("Running commodity check for all items")
    logger.info("=" * 50)

    for commodity in COMMODITIES:
        _check_single_commodity(commodity)


def _daily_summary():
    """Generate daily summary of all commodities."""
    logger.info("=" * 50)
    logger.info("Generating daily summary")
    logger.info("=" * 50)

    summary_lines = [
        f"Daily Commodity Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "=" * 50
    ]

    for commodity in COMMODITIES:
        try:
            price_result = get_commodity_price.invoke({"commodity": commodity})

            # Extract price change
            price_change = 0.0
            for line in price_result.split('\n'):
                if '%' in line and '(' in line:
                    try:
                        change_str = line.split('(')[1].split('%')[0].strip()
                        price_change = float(change_str.replace('+', ''))
                        break
                    except ValueError:
                        pass

            # Get sentiment
            search_query = f"{commodity} market sentiment"
            news = web_search.invoke({"query": search_query, "num_results": 2})

            nlp_result = nlp_analyze.invoke({
                "text": news,
                "task": "sentiment"
            })

            sentiment = "neutral"
            if "NEGATIVE" in nlp_result:
                sentiment = "NEGATIVE"
            elif "POSITIVE" in nlp_result:
                sentiment = "POSITIVE"

            summary_lines.append(
                f"\n{commodity.upper()}:\n"
                f"  Sentiment: {sentiment}\n"
                f"  Price Change: {price_change:+.2f}%"
            )

        except Exception as e:
            summary_lines.append(f"\n{commodity.upper()}: Error - {str(e)}")
            logger.error(f"Error in daily summary for {commodity}: {e}")

    summary_lines.append("\n" + "=" * 50)
    summary_msg = "\n".join(summary_lines)

    logger.info(summary_msg)
    _send_telegram_alert(summary_msg)

    # Save to file
    with open("monitor_summary.txt", "a") as f:
        f.write(summary_msg + "\n\n")


def start_scheduler():
    """Start the scheduler with monitoring jobs."""
    logger.info("Starting commodity monitoring scheduler...")

    # Schedule monitoring every 30 minutes
    schedule.every(30).minutes.do(_monitor_all_commodities)

    # Schedule daily summary at 09:00
    schedule.every().day.at("09:00").do(_daily_summary)

    logger.info("Scheduler started. Running monitoring loops...")
    logger.info("  - Every 30 minutes: Check all commodities")
    logger.info("  - Daily at 09:00: Generate summary")

    # Run scheduler
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check pending jobs every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Commodity Monitoring Service Started")
    logger.info("=" * 50)

    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
