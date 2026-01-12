"""Twilio SMS integration for sending and receiving messages."""
import os
from typing import Optional, Callable
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import threading
from dotenv import load_dotenv

load_dotenv()


class TwilioIntegration:
    """Handles SMS functionality via Twilio API."""

    def __init__(self):
        """Initialize Twilio client with credentials from environment."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.user_phone_number = os.getenv("USER_PHONE_NUMBER")

        self.client = None
        self._configured = False
        self._message_callback = None

        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self._configured = True

    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return (
            self._configured
            and self.twilio_number is not None
            and self.user_phone_number is not None
        )

    def get_configuration_status(self) -> dict:
        """Get the status of Twilio configuration."""
        return {
            "account_sid_configured": self.account_sid is not None,
            "auth_token_configured": self.auth_token is not None,
            "twilio_number_configured": self.twilio_number is not None,
            "user_number_configured": self.user_phone_number is not None,
            "fully_configured": self.is_configured(),
        }

    def send_message(self, message: str) -> dict:
        """
        Send an SMS message to the user's phone.

        Args:
            message: The message text to send

        Returns:
            Dict with success status and message/error info
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Twilio is not fully configured. Please check your settings."
            }

        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.twilio_number,
                to=self.user_phone_number
            )

            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "to": self.user_phone_number,
            }

        except TwilioRestException as e:
            return {
                "success": False,
                "error": f"Twilio API error: {str(e)}",
                "code": e.code,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    def send_message_async(self, message: str, callback: Optional[Callable] = None):
        """
        Send an SMS message asynchronously.

        Args:
            message: The message text to send
            callback: Optional callback with result dict
        """
        def _send():
            result = self.send_message(message)
            if callback:
                callback(result)

        thread = threading.Thread(target=_send, daemon=True)
        thread.start()

    def get_recent_messages(self, limit: int = 10) -> list:
        """
        Get recent SMS messages from Twilio.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dicts
        """
        if not self.is_configured():
            return []

        try:
            messages = self.client.messages.list(
                to=self.user_phone_number,
                limit=limit
            )

            return [
                {
                    "sid": msg.sid,
                    "from": msg.from_,
                    "to": msg.to,
                    "body": msg.body,
                    "date_sent": msg.date_sent,
                    "status": msg.status,
                    "direction": msg.direction,
                }
                for msg in messages
            ]

        except Exception as e:
            print(f"Error retrieving messages: {str(e)}")
            return []

    def get_setup_instructions(self) -> str:
        """Get instructions for setting up Twilio."""
        return """
To set up Twilio SMS:

1. Create a Twilio account at https://www.twilio.com/
   - You can start with a free trial account

2. Get your credentials:
   - Account SID: Found in your Twilio Console
   - Auth Token: Found in your Twilio Console
   - Phone Number: Get a Twilio phone number from the Console

3. Create a .env file in the ai-companion directory with:
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   USER_PHONE_NUMBER=your_actual_phone_number

4. Verify your phone number (for trial accounts):
   - In Twilio Console, go to "Verified Caller IDs"
   - Add and verify your phone number

5. Restart this app

Note: With a trial account, you can only send messages to verified numbers.
Upgrade to send to any number.
"""

    def test_connection(self) -> dict:
        """
        Test the Twilio connection by attempting to fetch account info.

        Returns:
            Dict with success status and account info
        """
        if not self._configured:
            return {
                "success": False,
                "error": "Twilio credentials not configured",
            }

        try:
            account = self.client.api.fetch(self.account_sid)
            return {
                "success": True,
                "account_sid": account.sid,
                "friendly_name": account.friendly_name,
                "status": account.status,
            }
        except TwilioRestException as e:
            return {
                "success": False,
                "error": f"Twilio API error: {str(e)}",
                "code": e.code,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
            }


class MessageForwarder:
    """Handles forwarding messages between the app and SMS."""

    def __init__(self, twilio: TwilioIntegration):
        """Initialize with Twilio integration."""
        self.twilio = twilio
        self.forward_to_sms = False
        self.forward_to_app = False

    def should_forward_to_sms(self) -> bool:
        """Check if messages should be forwarded to SMS."""
        return self.forward_to_sms and self.twilio.is_configured()

    def should_forward_to_app(self) -> bool:
        """Check if messages should be forwarded to app."""
        return self.forward_to_app and self.twilio.is_configured()

    def send_companion_message_to_sms(self, message: str) -> dict:
        """Send a companion's message to the user via SMS."""
        if not self.should_forward_to_sms():
            return {"success": False, "error": "SMS forwarding disabled"}

        return self.twilio.send_message(message)

    def toggle_sms_forwarding(self, enabled: bool):
        """Enable or disable SMS forwarding."""
        self.forward_to_sms = enabled
