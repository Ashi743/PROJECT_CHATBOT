import schedule
import time
import logging
import threading
from monitoring.checks.commodity_check import check_commodities
from monitoring.checks.file_check import check_files
from monitoring.checks.api_check import check_apis
from monitoring.checks.database_check import check_databases
from monitoring.checks.chromadb_check import check_chromadb
from monitoring.checks.app_check import check_app
from monitoring.alerts.slack_alert import alert_issues, alert_daily, alert_all_clear
from monitoring.reports.formatter import has_issues

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_all_checks() -> dict:
    results = {}
    results["commodities"] = check_commodities()
    results["files"] = check_files()
    results["apis"] = check_apis()
    results["databases"] = check_databases()
    results["chromadb"] = check_chromadb()
    results["app"] = check_app()
    return results


def run_quick_checks() -> dict:
    results = {}
    results["commodities"] = check_commodities()
    results["apis"] = check_apis()
    return results


def run_selected_checks(selections: list) -> dict:
    """
    Run only selected checks (for frontend monitor control).

    Args:
        selections: List of monitor names from sidebar

    Returns:
        Dict with results for each selected monitor
    """
    results = {}
    check_map = {
        "Commodity Prices": check_commodities,
        "Data Files": check_files,
        "API Health": check_apis,
        "Database Health": check_databases,
        "ChromaDB": check_chromadb,
        "App Health": check_app
    }

    for selection in selections:
        if selection in check_map:
            try:
                results[selection] = check_map[selection]()
            except Exception as e:
                logger.error(f"Error running {selection}: {e}")
                results[selection] = {"status": "[ERROR]", "error": str(e)}

    return results


def start_background(selections: list, interval_minutes: int) -> threading.Thread:
    """
    Start background monitoring in daemon thread (for frontend).

    Args:
        selections: List of monitor names
        interval_minutes: Check interval in minutes

    Returns:
        Thread reference for tracking
    """
    def job():
        results = run_selected_checks(selections)
        if has_issues(results):
            alert_issues(results)

    schedule.every(interval_minutes).minutes.do(job)

    def thread_loop():
        from utils.runtime_state import get_flag
        while not get_flag("monitor_stop_requested", False):
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=thread_loop, daemon=True)
    thread.start()
    return thread


def daily_report_job():
    logger.info("Running daily report job...")
    results = run_all_checks()
    alert_daily(results)


def monitor_job():
    logger.info("Running quick monitoring check...")
    results = run_quick_checks()
    if has_issues(results):
        alert_issues(results)


def start():
    logger.info("=" * 50)
    logger.info("Pipeline Monitor starting...")
    logger.info("=" * 50)

    logger.info("Schedules:")
    logger.info("  every 30 min  : commodities + apis")
    logger.info("  every 1 hour  : files + databases")
    logger.info("  every 6 hours : chromadb + app")
    logger.info("  daily 09:00   : full report to Slack")

    schedule.every(30).minutes.do(monitor_job)
    schedule.every(1).hour.do(check_files)
    schedule.every(1).hour.do(check_databases)
    schedule.every(6).hours.do(check_chromadb)
    schedule.every(6).hours.do(check_app)
    schedule.every().day.at("09:00").do(daily_report_job)

    logger.info("Running initial check...")
    results = run_all_checks()
    if has_issues(results):
        alert_issues(results)
    else:
        logger.info("Initial check: All systems [OK]")

    logger.info("Monitor loop started. Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")


if __name__ == "__main__":
    start()
