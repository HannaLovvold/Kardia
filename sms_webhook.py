"""Webhook server for receiving incoming SMS from Twilio."""
import os
import sys
from threading import Thread
from flask import Flask, request, Response
from dotenv import load_dotenv

load_dotenv()


class SMSWebhookServer:
    """Flask server to handle incoming SMS webhooks from Twilio."""

    def __init__(self, message_callback=None):
        """
        Initialize the webhook server.

        Args:
            message_callback: Function to call when SMS is received.
                           Should accept (phone_number, message_body) as args.
        """
        self.app = Flask(__name__)
        self.message_callback = message_callback
        self.port = int(os.getenv("WEBHOOK_PORT", "5000"))
        self.thread = None
        self.running = False

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes for SMS webhook."""

        @self.app.route('/sms/incoming', methods=['POST'])
        def incoming_sms():
            """Handle incoming SMS from Twilio webhook."""
            try:
                # Get message details from Twilio request
                from_number = request.form.get('From', '')
                body = request.form.get('Body', '')
                message_sid = request.form.get('MessageSid', '')

                print(f"📩 Received SMS from {from_number}: {body}")

                # Call the callback if provided
                if self.message_callback:
                    self.message_callback(from_number, body, message_sid)

                # Return TwiML to acknowledge receipt (empty response = no reply)
                return Response('', status=200, mimetype='text/xml')

            except Exception as e:
                print(f"Error processing incoming SMS: {e}")
                return Response('Error', status=500)

        @self.app.route('/sms/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return {'status': 'ok', 'service': 'sms-webhook'}

    def start(self):
        """Start the webhook server in a background thread."""
        if self.running:
            print("Webhook server is already running")
            return

        def run_server():
            print(f"🚀 Starting SMS webhook server on port {self.port}")
            print(f"📡 Webhook URL: http://your-server:{self.port}/sms/incoming")
            print(f"   (Use ngrok or similar for local development)")
            self.app.run(
                host='0.0.0.0',
                port=self.port,
                debug=False,
                use_reloader=False  # Important: disable reloader in thread
            )

        self.thread = Thread(target=run_server, daemon=True)
        self.thread.start()
        self.running = True
        print("✅ Webhook server started in background thread")

    def stop(self):
        """Stop the webhook server."""
        self.running = False
        if self.thread:
            # Note: Flask doesn't have a clean shutdown from thread
            # The thread will exit when the main process exits
            print("⚠️  Webhook server marked for shutdown (will exit when app exits)")

    def is_running(self) -> bool:
        """Check if the webhook server is running."""
        return self.running


# Test the server standalone
if __name__ == '__main__':
    def test_callback(from_number, body, message_sid):
        print(f"\n📨 CALLBACK TRIGGERED:")
        print(f"   From: {from_number}")
        print(f"   Message: {body}")
        print(f"   SID: {message_sid}\n")

    server = SMSWebhookServer(message_callback=test_callback)
    server.start()

    print("\n🔄 Server is running. Press Ctrl+C to stop.")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.stop()
