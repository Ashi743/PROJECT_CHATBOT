from monitoring.reports.formatter import format_daily_report, format_report_as_html
from datetime import datetime
import logging
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")


def create_html_email(to: str, subject: str, html_body: str) -> dict:
    """Create HTML email in Gmail API format."""
    msg = MIMEMultipart('alternative')
    msg['subject'] = subject
    msg['to'] = to

    # Also add plain text version
    text_version = "View this email in HTML format"
    msg.attach(MIMEText(text_version, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw_message}


def send_gmail_report(results: dict, subject: str = None):
    if not GMAIL_RECIPIENT:
        return {"status": "error", "message": "GMAIL_RECIPIENT not set in .env"}

    if not subject:
        subject = f"[Report] Pipeline Status - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    body = format_report_as_html(results)

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
