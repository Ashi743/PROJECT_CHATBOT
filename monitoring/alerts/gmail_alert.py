from monitoring.reports.formatter import format_daily_report
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")


def send_gmail_report(results: dict, subject: str = None):
    if not GMAIL_RECIPIENT:
        return {"status": "error", "message": "GMAIL_RECIPIENT not set in .env"}

    if not subject:
        subject = f"[Report] Pipeline Status - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    body = format_daily_report(results)

    try:
        from tools.gmail import send_email

        if send_email is None:
            logger.warning("Gmail not configured. Skipping email send.")
            return {"status": "skipped", "reason": "Gmail not configured"}

        result = send_email.invoke({
            "to": GMAIL_RECIPIENT,
            "subject": subject,
            "message": body
        })
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
