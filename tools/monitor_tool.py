from langchain_core.tools import tool
import threading
import time
from datetime import datetime
from typing import Optional, Callable
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global monitoring state
_monitoring_threads = {}
_monitoring_lock = threading.Lock()
_monitoring_results = {}


def _send_alert(message: str, callback: Optional[Callable] = None):
    """
    Send alert via callback, Slack, or log it.
    Default: Send to Slack webhook (if configured)
    Optional callback: Custom handler (email, sms, etc.)
    """
    if callback:
        try:
            callback(message)
        except Exception as e:
            logger.error(f"Alert callback error: {e}")
    else:
        # Default: Send to Slack
        try:
            from tools.slack_alert_tool import send_slack_alert
            result = send_slack_alert(
                message,
                title="Commodity Alert",
                severity="alert"
            )
            if result["status"] == "ok":
                logger.info("Alert sent to Slack")
            else:
                logger.warning(f"Slack alert failed: {result['message']}")
        except ImportError:
            # Slack tool not available, fall back to logging
            logger.warning(f"ALERT: {message}")


def _log_to_storage(commodity: str, result: dict, storage_callback: Optional[Callable] = None):
    """
    Log monitoring result to ChromaDB or other storage.
    """
    if storage_callback:
        try:
            storage_callback(commodity, result)
        except Exception as e:
            logger.error(f"Storage callback error: {e}")
    else:
        # Silent logging - just store in memory
        if commodity not in _monitoring_results:
            _monitoring_results[commodity] = []
        _monitoring_results[commodity].append(result)


def _run_monitoring(
    commodity: str,
    interval_seconds: int,
    alert_callback: Optional[Callable] = None,
    storage_callback: Optional[Callable] = None,
    stop_event: Optional[threading.Event] = None
):
    """
    Run the monitoring loop for a single commodity.
    Imports tools at runtime to avoid circular imports.
    """
    from tools.web_search_tool import web_search
    from tools.commodity_tool import get_commodity_price
    from tools.nlp_tool import nlp_analyze

    logger.info(f"Starting monitoring for {commodity}")

    while stop_event is None or not stop_event.is_set():
        try:
            timestamp = datetime.now().isoformat()
            logger.info(f"[{timestamp}] Checking {commodity}...")

            # Step 1: Web search for news
            search_query = f"{commodity} price news market {datetime.now().strftime('%B %Y')}"
            search_results = web_search.invoke({"query": search_query, "num_results": 3})

            # Step 2: Extract text from search results for NLP analysis
            text_to_analyze = f"Search results for {commodity}:\n{search_results}"

            # Step 3: NLP sentiment analysis
            nlp_result = nlp_analyze.invoke({"text": text_to_analyze, "task": "sentiment"})

            # Step 4: Get commodity price
            price_result = get_commodity_price.invoke({"commodity": commodity})

            # Parse sentiment from NLP result
            sentiment = "neutral"
            if "NEGATIVE" in nlp_result:
                sentiment = "negative"
            elif "POSITIVE" in nlp_result:
                sentiment = "positive"

            # Parse price change from commodity result
            price_change_pct = 0
            try:
                # Extract percentage from price result
                for line in price_result.split('\n'):
                    if '%' in line and '+' in line:
                        change_str = line.split('(')[1].split('%')[0].replace('+', '').strip()
                        price_change_pct = float(change_str)
                        break
                    elif '%' in line and '-' in line:
                        change_str = line.split('(')[1].split('%')[0].replace('+', '').strip()
                        price_change_pct = float(change_str)
                        break
            except Exception:
                price_change_pct = 0

            # Log result
            result = {
                "timestamp": timestamp,
                "commodity": commodity,
                "sentiment": sentiment,
                "price_change_pct": price_change_pct,
                "search_summary": search_results[:200] if search_results else "",
                "nlp_result": nlp_result[:300] if nlp_result else "",
                "price_info": price_result[:300] if price_result else ""
            }

            _log_to_storage(commodity, result, storage_callback)

            # Check alert conditions: NEGATIVE sentiment AND price drop > 1.5%
            if sentiment == "negative" and price_change_pct < -1.5:
                alert_msg = (
                    f"[ALERT] COMMODITY ALERT [ALERT]\n"
                    f"Commodity: {commodity.upper()}\n"
                    f"Sentiment: {sentiment.upper()}\n"
                    f"Price Change: {price_change_pct:.2f}%\n"
                    f"Time: {timestamp}\n"
                    f"Details: {search_results[:150]}"
                )
                _send_alert(alert_msg, alert_callback)
                logger.warning(f"ALERT TRIGGERED for {commodity}: Negative sentiment + Price drop {price_change_pct:.2f}%")

        except Exception as e:
            logger.error(f"Error in monitoring loop for {commodity}: {e}")

        # Wait for next interval
        if stop_event is None:
            time.sleep(interval_seconds)
        else:
            stop_event.wait(interval_seconds)


@tool
def start_monitoring(
    commodity: str,
    interval_minutes: int = 30,
    confirm: bool = False
) -> str:
    """
    Start real-time monitoring for a commodity.
    Monitors web sentiment and price changes in background.
    First call returns confirmation request; set confirm=True to actually start.

    Args:
        commodity: Commodity name (wheat, soy, corn, sugar, cotton, rice)
        interval_minutes: Check interval in minutes (default: 30)
        confirm: Set to True to confirm and start monitoring (HITL)

    Returns:
        Confirmation request on first call, status message on confirmed call
    """
    commodity_lower = commodity.lower().strip()

    if not confirm:
        return (
            f"[CONFIRM] Ready to start monitoring {commodity} every {interval_minutes} min. "
            f"This will spawn a background thread. "
            f"Call again with confirm=True to proceed."
        )

    with _monitoring_lock:
        if commodity_lower in _monitoring_threads:
            return f"[WARN] Monitoring already active for {commodity}"

        # Create stop event for clean shutdown
        stop_event = threading.Event()

        # Create and start thread
        thread = threading.Thread(
            target=_run_monitoring,
            args=(commodity_lower, interval_minutes * 60, None, None, stop_event),
            daemon=True,
            name=f"monitor-{commodity_lower}"
        )

        _monitoring_threads[commodity_lower] = {
            "thread": thread,
            "stop_event": stop_event,
            "started_at": datetime.now().isoformat()
        }

        thread.start()
        return f"[OK] Monitoring started for {commodity} (every {interval_minutes} min)"


@tool
def stop_monitoring(commodity: str) -> str:
    """
    Stop monitoring for a specific commodity.

    Args:
        commodity: Commodity name to stop monitoring

    Returns:
        Status message
    """
    commodity_lower = commodity.lower().strip()

    with _monitoring_lock:
        if commodity_lower not in _monitoring_threads:
            return f"No active monitoring for {commodity}"

        stop_event = _monitoring_threads[commodity_lower]["stop_event"]
        stop_event.set()
        del _monitoring_threads[commodity_lower]

    return f"[OK] Monitoring stopped for {commodity}"


@tool
def get_monitoring_results(commodity: Optional[str] = None) -> str:
    """
    Get stored monitoring results for a commodity or all commodities.

    Args:
        commodity: Specific commodity to get results for, or None for all

    Returns:
        Formatted monitoring results
    """
    if commodity:
        commodity_lower = commodity.lower().strip()
        results = _monitoring_results.get(commodity_lower, [])
        if not results:
            return f"No results found for {commodity}"
        return f"Results for {commodity}:\n" + "\n".join(
            [f"  - {r.get('timestamp')}: {r.get('sentiment')} sentiment, {r.get('price_change_pct'):.2f}% change" for r in results[-10:]]
        )
    else:
        output = "Monitoring Results:\n"
        for comm, results in _monitoring_results.items():
            if results:
                latest = results[-1]
                output += f"\n{comm.upper()}:\n"
                output += f"  Latest: {latest.get('timestamp')}\n"
                output += f"  Sentiment: {latest.get('sentiment')}\n"
                output += f"  Price Change: {latest.get('price_change_pct'):.2f}%\n"
        return output if output != "Monitoring Results:\n" else "No monitoring data available"


@tool
def get_active_monitors() -> str:
    """
    Get list of currently active commodity monitors.

    Returns:
        List of monitored commodities
    """
    with _monitoring_lock:
        if not _monitoring_threads:
            return "No active monitors"

        output = "Active Monitors:\n"
        for commodity, info in _monitoring_threads.items():
            output += f"  - {commodity.upper()} (started: {info['started_at']})\n"
        return output
