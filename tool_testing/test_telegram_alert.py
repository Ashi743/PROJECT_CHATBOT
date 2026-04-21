#!/usr/bin/env python3
"""Test suite for telegram_alert_tool.py"""

import sys
import os
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.telegram_alert_tool import send_telegram_alert


class TelegramAlertTester:
    """Base class for testing Telegram alert tool functionality"""

    def __init__(self):
        """Initialize tester"""
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.results = {}

    def check_setup(self):
        """Check if Telegram setup is complete"""
        if not self.bot_token or not self.chat_id:
            print("[FAIL] Telegram setup incomplete\n")
            print("To enable Telegram alerts:")
            print("1. Go to Telegram and find '@BotFather'")
            print("2. Send: /newbot")
            print("3. Follow steps to create bot")
            print("4. Copy bot token")
            print("5. Get your chat ID:")
            print("   - Send message to your bot")
            print("   - Visit: https://api.telegram.org/botYOUR_TOKEN/getUpdates")
            print("   - Find your chat ID in response")
            print("\n6. Add to .env:")
            print("   TELEGRAM_BOT_TOKEN=your_token_here")
            print("   TELEGRAM_CHAT_ID=your_chat_id_here")
            print("\nFor detailed setup, see: TELEGRAM_SETUP.md")
            return False

        print("[OK] Telegram setup found\n")
        return True

    def test_alert(self, message, alert_type="info"):
        """Test sending an alert"""
        print(f"\nTesting {alert_type.upper()} alert:")
        print("-" * 60)
        print(f"Message: {message}")

        result = send_telegram_alert.invoke({
            "message": message,
            "alert_type": alert_type
        })

        self.results[f"{alert_type}: {message}"] = result
        print(f"Result: {result}\n")
        return result

    def run_tests(self):
        """Run tests for all alert types"""
        if not self.check_setup():
            return False

        print("[OK] Testing Telegram Alert Tool\n")

        test_cases = [
            ("Test info message", "info"),
            ("Operation completed successfully", "success"),
            ("High memory usage detected", "warning"),
            ("Connection failed", "error"),
            ("System critical alert", "critical"),
        ]

        print("="*60)
        print("Sending Test Alerts")
        print("="*60)

        for message, alert_type in test_cases:
            self.test_alert(message, alert_type)

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = TelegramAlertTester()
    tester.run_tests()
