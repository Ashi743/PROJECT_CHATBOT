from tools.slack_alert_tool import send_slack_alert
from monitoring.reports.formatter import format_issue_alert, format_daily_report, format_all_clear, has_issues
import logging

logger = logging.getLogger(__name__)


def alert_issues(results: dict):
    if has_issues(results):
        msg = format_issue_alert(results)
        result = send_slack_alert(msg, title="Pipeline Alert", severity="alert")
        if result["status"] == "ok":
            logger.info("Slack issue alert sent")
        else:
            logger.error(f"Failed to send Slack issue alert: {result}")


def alert_daily(results: dict):
    msg = format_daily_report(results)
    result = send_slack_alert(msg, title="Daily System Report", severity="info")
    if result["status"] == "ok":
        logger.info("Slack daily report sent")
    else:
        logger.error(f"Failed to send Slack daily report: {result}")


def alert_all_clear():
    msg = format_all_clear()
    result = send_slack_alert(msg, title="All Systems OK", severity="info")
    if result["status"] == "ok":
        logger.info("Slack all-clear message sent")
    else:
        logger.error(f"Failed to send Slack all-clear message: {result}")


if __name__ == "__main__":
    sample_results = {
        "commodities": {
            "wheat": {"price": 543.20, "change": -0.8, "status": "[OK]"}
        }
    }
    alert_daily(sample_results)
