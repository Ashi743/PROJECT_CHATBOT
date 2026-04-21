from langchain_core.tools import tool
import os
import requests
from datetime import datetime

@tool
def send_telegram_alert(message: str, alert_type: str = "info") -> str:
    """
    Send a message/alert to Telegram.
    Use when user asks to send message, notification, or alert to Telegram.

    Args:
        message: The message to send to Telegram
        alert_type: Type of alert (info, success, warning, error, critical)

    Examples:
    - "Send a message to Telegram: Task completed"
    - "Alert: High temperature detected"
    - "Notify on Telegram: Stock price drop"
    """
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token:
            return "Error: TELEGRAM_BOT_TOKEN not set in .env file. Get a bot token from @BotFather on Telegram."

        if not chat_id:
            return "Error: TELEGRAM_CHAT_ID not set in .env file. Add your chat ID to .env file."

        # Validate alert type
        valid_types = ["info", "success", "warning", "error", "critical"]
        if alert_type not in valid_types:
            alert_type = "info"

        # Add emoji prefix based on alert type
        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }

        emoji = emoji_map.get(alert_type, "ℹ️")
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Format the message
        formatted_message = f"{emoji} [{alert_type.upper()}] {message}\n⏰ {timestamp}"

        # Send via Telegram Bot API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": formatted_message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 200:
            return f"Message sent to Telegram: {message}"
        else:
            error_msg = response.json().get("description", "Unknown error")
            return f"Failed to send Telegram message: {error_msg}"

    except requests.exceptions.Timeout:
        return "Error: Telegram request timed out. Try again."
    except requests.exceptions.RequestException as e:
        return f"Error: Network error sending to Telegram. {str(e)}"
    except Exception as e:
        return f"Error sending Telegram alert: {str(e)}"
