#!/usr/bin/env python3
"""Test suite for gmail.py"""

import os
import sys
from dotenv import load_dotenv

# Handle Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, "..")
from tools.gmail import send_email


class GmailToolTester:
    """Base class for testing gmail tool functionality"""

    def __init__(self):
        """Initialize Gmail tool tester"""
        load_dotenv()
        self.results = {}
        self.credentials_file = os.path.join('..', 'gmail_toolkit', 'credentials.json')
        self.token_file = os.path.join('..', 'gmail_toolkit', 'token.json')

    def check_setup(self):
        """Check if OAuth2 credentials are set up"""
        print("=" * 60)
        print("Gmail Tool Setup Check")
        print("=" * 60)

        # Check if credentials.json exists
        if not os.path.exists(self.credentials_file):
            print(f"[FAIL] {self.credentials_file} not found")
            print("\nTo set up Gmail OAuth2:")
            print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
            print("2. Create a new project")
            print("3. Enable Gmail API")
            print("4. Create OAuth2 credentials (Desktop app)")
            print("5. Download credentials JSON and save as 'credentials.json' in gmail_toolkit folder")
            return False

        print(f"[OK] {self.credentials_file} found")

        # Check if token.json exists (previous authentication)
        if os.path.exists(self.token_file):
            print(f"[OK] {self.token_file} found (already authenticated)")
        else:
            print(f"[INFO] {self.token_file} not found (will authenticate on first use)")

        print()
        return True

    def test_send_email(self, to_email: str, subject: str = "Test Email", body: str = "This is a test email"):
        """
        Test sending an email

        Args:
            to_email: Recipient email address
            subject: Email subject (default: "Test Email")
            body: Email body (default: "This is a test email")

        Returns:
            Result string from send_email
        """
        print("\n" + "=" * 60)
        print(f"Test: Send Email to {to_email}")
        print("=" * 60)
        result = send_email.invoke({
            "to_email": to_email,
            "subject": subject,
            "body": body
        })
        self.results[to_email] = result
        print(result)
        return result

    def test_invalid_email(self):
        """Test sending to invalid email address"""
        print("\n" + "=" * 60)
        print("Test: Invalid Email Address")
        print("=" * 60)
        result = send_email.invoke({
            "to_email": "invalid-email",
            "subject": "Test",
            "body": "Test"
        })
        self.results["invalid"] = result
        print(result)
        return result

    def run_tests(self):
        """Run setup check and optionally test email sending"""
        if not self.check_setup():
            print("\n[STOP] Setup incomplete. Please configure OAuth2 first.")
            return False

        print("[INFO] Gmail tool is ready to send emails")
        print("\nTo test sending an email, uncomment the test_send_email() call in this script")
        print("and provide a valid recipient email address.\n")

        # Uncomment below to test actual email sending:
        # self.test_send_email("recipient@example.com", "Test Subject", "Test Body")
        # self.test_invalid_email()

        return True

    def get_results(self):
        """Return test results dictionary"""
        return self.results


if __name__ == "__main__":
    tester = GmailToolTester()
    tester.run_tests()
