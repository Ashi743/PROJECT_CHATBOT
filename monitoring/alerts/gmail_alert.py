from tools.gmail import send_email
from monitoring.reports.formatter import format_daily_report
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def send_gmail_report(results: dict, subject: str = None):
    if not subject:
        subject = f"[Report] Pipeline Status - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    body = format_daily_report(results)

    try:
        result = send_email(
            to="ashishdangwal97@gmail.com",
            subject=subject,
            body=body
        )
        logger.info(f"Gmail report sent: {subject}")
        return result
    except Exception as e:
        logger.error(f"Failed to send Gmail report: {e}")
        raise


if __name__ == "__main__":
    sample_results = {
        "commodities": {
            "wheat": {"price": 543.20, "change": -0.8, "status": "[OK]"}
        }
    }
    send_gmail_report(sample_results)
