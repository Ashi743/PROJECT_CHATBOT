from langchain_core.tools import tool
import requests
import os
import logging

logger = logging.getLogger(__name__)


def send_slack_alert(
    message: str,
    title: str = "",
    severity: str = "info"
) -> dict:
    """
    Send alert to Slack webhook.

    Args:
        message: Plain text message body
        title: Optional title/header
        severity: Alert level - 'info', 'warning', 'alert', 'error'

    Returns:
        {status: "ok"} or {status: "error", message: "..."}
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        return {
            "status": "error",
            "message": "SLACK_WEBHOOK_URL not set in environment"
        }

    # Emoji and color by severity
    severity_map = {
        "info": ":information_source:",
        "warning": ":warning:",
        "alert": ":alert:",
        "error": ":x:"
    }

    emoji = severity_map.get(severity, ":information_source:")

    # Build message payload
    header_text = f"{emoji} {title}" if title else f"{emoji} Alert"

    payload = {
        "text": header_text,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{header_text}*\n{message}"
                }
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info(f"Slack alert sent: {title or 'notification'}")
            return {"status": "ok"}
        else:
            error_msg = f"Slack API returned {response.status_code}: {response.text}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }

    except requests.exceptions.Timeout:
        error_msg = "Slack API request timeout"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    except Exception as e:
        error_msg = f"Slack alert failed: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}


@tool
def slack_notify(
    message: str,
    title: str = "Alert",
    severity: str = "info"
) -> str:
    """
    Send message to Slack channel.
    No HITL required - fires automatically for background alerts.

    Args:
        message: Message body (plain text or markdown)
        title: Message title/header
        severity: Alert level - 'info', 'warning', 'alert', 'error'

    Returns:
        Success message or error details

    Examples:
        slack_notify.invoke({
            'message': 'Wheat price dropped 2.5%',
            'title': 'Commodity Alert',
            'severity': 'alert'
        })
    """
    if not message or not message.strip():
        return "[ERROR] Message cannot be empty"

    result = send_slack_alert(message, title, severity)

    if result["status"] == "ok":
        return f"[OK] Slack message sent: {title}"
    else:
        return f"[ERROR] {result['message']}"


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing Slack alert tool...")
    print()

    # Test 1: Simple info message
    print("[Test 1] Info message:")
    result = slack_notify.invoke({
        "message": "This is a test info message",
        "title": "Test Info",
        "severity": "info"
    })
    print(f"  {result}")
    print()

    # Test 2: Warning alert
    print("[Test 2] Warning alert:")
    result = slack_notify.invoke({
        "message": "Commodity price volatility detected. Check market conditions.",
        "title": "Market Warning",
        "severity": "warning"
    })
    print(f"  {result}")
    print()

    # Test 3: Critical alert
    print("[Test 3] Critical alert:")
    result = slack_notify.invoke({
        "message": "WHEAT: Negative sentiment + 2.15% price drop detected",
        "title": "Commodity Alert",
        "severity": "alert"
    })
    print(f"  {result}")
    print()

    # Test 4: Error message
    print("[Test 4] Error message:")
    result = slack_notify.invoke({
        "message": "Monitor thread crashed. Check logs for details.",
        "title": "System Error",
        "severity": "error"
    })
    print(f"  {result}")
    print()

    print("Tests complete. Check your Slack channel for messages.")
