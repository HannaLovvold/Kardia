"""REST API server for Kardia AI Companion.

Provides a REST API for external clients (e.g., mobile apps) to interact
with the AI companion application.

Features:
- Bearer token authentication
- Companion management with avatars
- Messaging with typing indicators
- Memory management
- Push notification support via webhooks

Copyright (c) 2025 Hanna Lovvold
All rights reserved.
"""
import base64
import json
import os
from functools import wraps
from pathlib import Path
from threading import Thread
from typing import Optional, List, Dict
from datetime import datetime
import time

from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()


# Storage for webhook registrations
WEBHOOKS_FILE = Path(__file__).parent / "config" / "webhooks.json"


def load_webhooks() -> dict:
    """Load registered webhooks from file."""
    if WEBHOOKS_FILE.exists():
        try:
            with open(WEBHOOKS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"urls": []}


def save_webhooks(webhooks: dict):
    """Save webhooks to file."""
    try:
        WEBHOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WEBHOOKS_FILE, 'w') as f:
            json.dump(webhooks, f, indent=2)
    except Exception as e:
        print(f"Error saving webhooks: {e}")


def send_webhook_notification(event_type: str, data: dict):
    """Send notification to all registered webhooks."""
    webhooks = load_webhooks()
    payload = {
        "event": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    for url in webhooks.get("urls", []):
        def send_webhook(url=url, payload=payload):
            try:
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                print(f"Webhook error for {url}: {e}")

        # Send in background thread
        Thread(target=send_webhook, daemon=True).start()


def require_auth(f):
    """Decorator to require Bearer token authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'success': False, 'error': 'Missing Authorization header'}), 401

        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Invalid Authorization format. Use: Bearer <token>'}), 401

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Get the expected token from the app instance
        expected_token = os.getenv('API_BEARER_TOKEN', 'kardia-api-key')

        if token != expected_token:
            return jsonify({'success': False, 'error': 'Invalid API token'}), 401

        return f(*args, **kwargs)
    return decorated_function


class APIServer:
    """Flask REST API server for Kardia."""

    def __init__(self, app_instance):
        """
        Initialize the API server.

        Args:
            app_instance: Reference to the KardiaApp instance
        """
        self.app_instance = app_instance
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes

        # Enable strict slashes off - allow trailing slashes
        self.app.url_map.strict_slashes = False

        self.port = int(os.getenv("API_SERVER_PORT", "5000"))
        self.thread = None
        self.running = False

        # Typing indicator state
        self.typing = False
        self.typing_companion_id = None

        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint (no auth required)."""
            return jsonify({
                'status': 'ok',
                'service': 'kardia-api',
                'version': '1.1.0'
            })

        @self.app.route('/api/status', methods=['GET'])
        @require_auth
        def get_status():
            """Get current API status including typing indicator."""
            status = {
                'success': True,
                'typing': self.typing,
                'companion_id': self.typing_companion_id
            }
            if self.app_instance.current_companion:
                status['current_companion'] = {
                    'id': self.app_instance.current_companion.id,
                    'name': self.app_instance.current_companion.name
                }
            else:
                status['current_companion'] = None
            return jsonify(status)

        @self.app.route('/api/webhook', methods=['POST', 'DELETE'])
        @require_auth
        def manage_webhook():
            """Register or remove a webhook URL for push notifications."""
            if request.method == 'POST':
                data = request.get_json()
                if not data or 'url' not in data:
                    return jsonify({'success': False, 'error': 'Missing url'}), 400

                url = data['url'].strip()
                if not url:
                    return jsonify({'success': False, 'error': 'Empty url'}), 400

                webhooks = load_webhooks()
                if url not in webhooks.get("urls", []):
                    webhooks.setdefault("urls", []).append(url)
                    save_webhooks(webhooks)

                return jsonify({
                    'success': True,
                    'message': 'Webhook registered',
                    'url': url
                })

            elif request.method == 'DELETE':
                data = request.get_json()
                if not data or 'url' not in data:
                    return jsonify({'success': False, 'error': 'Missing url'}), 400

                url = data['url'].strip()
                webhooks = load_webhooks()
                if url in webhooks.get("urls", []):
                    webhooks["urls"].remove(url)
                    save_webhooks(webhooks)
                    return jsonify({'success': True, 'message': 'Webhook removed'})

                return jsonify({'success': False, 'error': 'URL not registered'}), 404

        @self.app.route('/api/companions', methods=['GET'])
        @require_auth
        def get_companions():
            """Get list of all companions with avatar info."""
            try:
                companions = self.app_instance.companion_manager.get_all_companions()

                # Get current companion ID
                current_id = None
                if self.app_instance.current_companion:
                    current_id = self.app_instance.current_companion.id

                # Add avatar info to each companion
                for comp in companions:
                    comp['has_avatar'] = 'image_path' in comp and comp['image_path']
                    # For API, return image_url instead of local path
                    if comp.get('image_path'):
                        comp['image_url'] = f"/api/companions/{comp['id']}/avatar"
                    else:
                        comp['image_url'] = None

                return jsonify({
                    'success': True,
                    'companions': companions,
                    'current_companion_id': current_id
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/companions/<companion_id>/avatar', methods=['GET'])
        @require_auth
        def get_companion_avatar(companion_id):
            """Get a companion's avatar image."""
            try:
                companion = self.app_instance.companion_manager.create_companion(companion_id)
                if not companion or not companion.image_path:
                    # Return default avatar
                    return jsonify({'success': False, 'error': 'No avatar found'}), 404

                image_path = Path(companion.image_path)
                if not image_path.exists():
                    return jsonify({'success': False, 'error': 'Image file not found'}), 404

                return send_file(image_path, mimetype='image/png')
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/companion/current', methods=['GET'])
        @require_auth
        def get_current_companion():
            """Get current companion info with avatar."""
            try:
                if not self.app_instance.current_companion:
                    return jsonify({
                        'success': False,
                        'error': 'No companion selected'
                    }), 404

                companion = self.app_instance.current_companion
                return jsonify({
                    'success': True,
                    'companion': {
                        'id': companion.id,
                        'name': companion.name,
                        'display_name': companion.display_name,
                        'gender': companion.gender,
                        'pronouns': companion.pronouns,
                        'personality': companion.personality,
                        'interests': companion.interests,
                        'greeting': companion.greeting,
                        'relationship_goal': companion.relationship_goal,
                        'tone': companion.tone,
                        'background': companion.background,
                        'has_avatar': bool(companion.image_path),
                        'image_url': f"/api/companions/{companion.id}/avatar" if companion.image_path else None
                    }
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/companions/select', methods=['POST'])
        @require_auth
        def select_companion():
            """Select a companion by ID."""
            try:
                data = request.get_json()
                if not data or 'companion_id' not in data:
                    return jsonify({'success': False, 'error': 'Missing companion_id'}), 400

                companion_id = data['companion_id']

                # Create the companion
                companion = self.app_instance.companion_manager.create_companion(companion_id)
                if not companion:
                    return jsonify({'success': False, 'error': 'Companion not found'}), 404

                # Set as current
                self.app_instance.set_current_companion(companion)

                # Send webhook notification
                send_webhook_notification("companion_selected", {
                    "companion_id": companion.id,
                    "companion_name": companion.name
                })

                return jsonify({
                    'success': True,
                    'companion': {
                        'id': companion.id,
                        'name': companion.name,
                        'display_name': companion.display_name,
                        'gender': companion.gender,
                        'image_url': f"/api/companions/{companion.id}/avatar" if companion.image_path else None
                    }
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/message', methods=['POST'])
        @require_auth
        def send_message():
            """Send a message to the AI and get a response."""
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({'success': False, 'error': 'Missing message'}), 400

                message = data['message'].strip()
                if not message:
                    return jsonify({'success': False, 'error': 'Empty message'}), 400

                # Check if a companion is selected
                if not self.app_instance.current_companion:
                    return jsonify({
                        'success': False,
                        'error': 'No companion selected. Use POST /api/companions/select first.'
                    }), 400

                companion_id = self.app_instance.current_companion.id
                companion_name = self.app_instance.current_companion.name

                # Store result for async callback
                result_container = {'response': None, 'error': None}

                # Set typing indicator
                self.typing = True
                self.typing_companion_id = companion_id
                send_webhook_notification("typing_started", {
                    "companion_id": companion_id,
                    "companion_name": companion_name
                })

                def callback(response: str):
                    result_container['response'] = response

                # Send message through the app
                self.app_instance.send_message(message, callback)

                # Wait for response (with timeout)
                timeout = 60  # 60 seconds
                start = time.time()
                while result_container['response'] is None and result_container['error'] is None:
                    if time.time() - start > timeout:
                        self.typing = False
                        self.typing_companion_id = None
                        return jsonify({'success': False, 'error': 'Response timeout'}), 504
                    time.sleep(0.1)

                # Clear typing indicator
                self.typing = False
                self.typing_companion_id = None

                if result_container['error']:
                    return jsonify({'success': False, 'error': result_container['error']}), 500

                response_data = {
                    'success': True,
                    'response': result_container['response'],
                    'companion': {
                        'id': self.app_instance.current_companion.id,
                        'name': self.app_instance.current_companion.name
                    },
                    'timestamp': datetime.now().isoformat()
                }

                # Send webhook notification for new message
                send_webhook_notification("new_message", response_data)

                return jsonify(response_data)

            except Exception as e:
                self.typing = False
                self.typing_companion_id = None
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/conversation', methods=['GET'])
        @require_auth
        def get_conversation():
            """Get conversation history for current companion."""
            try:
                if not self.app_instance.current_conversation:
                    return jsonify({
                        'success': True,
                        'messages': [],
                        'companion_id': None
                    })

                messages = self.app_instance.current_conversation.messages

                return jsonify({
                    'success': True,
                    'companion_id': self.app_instance.current_conversation.companion_id,
                    'messages': [
                        {
                            'role': msg.role,
                            'content': msg.content,
                            'timestamp': msg.timestamp
                        }
                        for msg in messages
                    ]
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/conversation', methods=['DELETE'])
        @require_auth
        def clear_conversation():
            """Clear conversation history for current companion."""
            try:
                if not self.app_instance.current_companion:
                    return jsonify({'success': False, 'error': 'No companion selected'}), 400

                companion_id = self.app_instance.current_companion.id

                # Delete the conversation
                self.app_instance.storage.delete_conversation(companion_id)

                # Create new conversation
                self.app_instance.set_current_companion(
                    self.app_instance.current_companion
                )

                # Send webhook notification
                send_webhook_notification("conversation_cleared", {
                    "companion_id": companion_id
                })

                return jsonify({
                    'success': True,
                    'message': 'Conversation cleared'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/memories', methods=['GET'])
        @require_auth
        def get_memories():
            """Get user memories."""
            try:
                limit = request.args.get('limit', 50, type=int)
                memories = self.app_instance.memory_store.get_recent_memories(limit=limit)

                return jsonify({
                    'success': True,
                    'memories': [
                        {
                            'id': mem.id,
                            'memory_type': mem.memory_type,
                            'content': mem.content,
                            'key': mem.key,
                            'value': mem.value,
                            'importance': mem.importance,
                            'is_shared': mem.is_shared,
                            'companion_id': mem.companion_id,
                            'created_at': mem.created_at
                        }
                        for mem in memories
                    ]
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/memories', methods=['POST'])
        @require_auth
        def add_memory():
            """Add a new memory."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Missing data'}), 400

                # Required fields
                if 'memory_type' not in data or 'content' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Missing required fields: memory_type, content'
                    }), 400

                memory_type = data['memory_type']
                content = data['content'].strip()
                key = data.get('key')
                value = data.get('value')
                importance = data.get('importance', 3)
                is_shared = data.get('is_shared', True)

                # Add memory
                memory = self.app_instance.memory_store.add_memory(
                    memory_type=memory_type,
                    content=content,
                    key=key,
                    value=value,
                    importance=importance,
                    companion_id=self.app_instance.current_companion.id if self.app_instance.current_companion else "",
                    is_shared=is_shared,
                )

                return jsonify({
                    'success': True,
                    'memory': {
                        'id': memory.id,
                        'memory_type': memory.memory_type,
                        'content': memory.content
                    }
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/proactive/settings', methods=['GET'])
        @require_auth
        def get_proactive_settings():
            """Get proactive messaging settings."""
            try:
                from proactive_messenger import load_proactive_config
                config = load_proactive_config()

                return jsonify({
                    'success': True,
                    'settings': {
                        'enabled': config.get('enabled', True),
                        'global_frequency': config.get('global_frequency', 3),
                        'time_window': config.get('time_window', {
                            'start': '09:00',
                            'end': '22:00'
                        }),
                        'companion_settings': config.get('companion_settings', {})
                    }
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/proactive/settings', methods=['PUT'])
        @require_auth
        def update_proactive_settings():
            """Update global proactive messaging settings."""
            try:
                from proactive_messenger import load_proactive_config, save_proactive_config
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Missing data'}), 400

                config = load_proactive_config()

                if 'enabled' in data:
                    config['enabled'] = data['enabled']
                if 'frequency' in data:
                    config['global_frequency'] = data['frequency']
                if 'time_start' in data:
                    config.setdefault('time_window', {})['start'] = data['time_start']
                if 'time_end' in data:
                    config.setdefault('time_window', {})['end'] = data['time_end']

                save_proactive_config(config)

                # Update running scheduler if it exists
                if hasattr(self.app_instance, 'proactive_scheduler'):
                    self.app_instance.proactive_scheduler.config = config

                return jsonify({'success': True, 'message': 'Settings updated'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/proactive/companions/<companion_id>', methods=['GET', 'PUT'])
        @require_auth
        def companion_proactive_settings(companion_id):
            """Get or update proactive settings for a specific companion."""
            try:
                from proactive_messenger import load_proactive_config, save_proactive_config

                if request.method == 'GET':
                    config = load_proactive_config()
                    comp_settings = config.get('companion_settings', {}).get(companion_id, {
                        'enabled': True,
                        'frequency': None  # uses global
                    })
                    return jsonify({'success': True, 'settings': comp_settings})

                else:  # PUT
                    data = request.get_json()
                    if not data:
                        return jsonify({'success': False, 'error': 'Missing data'}), 400

                    config = load_proactive_config()
                    config.setdefault('companion_settings', {})[companion_id] = data
                    save_proactive_config(config)

                    return jsonify({'success': True, 'message': 'Companion settings updated'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors."""
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

    def notify_new_message(self, message: str, companion_id: str, companion_name: str):
        """Send a webhook notification when a new message is received (from desktop app)."""
        send_webhook_notification("new_message", {
            "response": message,
            "companion": {
                "id": companion_id,
                "name": companion_name
            },
            "timestamp": datetime.now().isoformat(),
            "source": "desktop"
        })

    def start(self):
        """Start the API server in a background thread."""
        if self.running:
            print("API server is already running")
            return

        def run_server():
            print(f"🚀 Starting Kardia API server on port {self.port}")
            print(f"📡 API URL: http://localhost:{self.port}")
            print(f"🔑 Make sure to set API_BEARER_TOKEN in .env file")
            self.app.run(
                host='0.0.0.0',
                port=self.port,
                debug=False,
                use_reloader=False
            )

        self.thread = Thread(target=run_server, daemon=True)
        self.thread.start()
        self.running = True
        print("✅ API server started in background thread")

    def stop(self):
        """Stop the API server."""
        self.running = False
        print("⚠️  API server marked for shutdown")

    def is_running(self) -> bool:
        """Check if the API server is running."""
        return self.running


# Test the server standalone
if __name__ == '__main__':
    class MockApp:
        """Mock app for testing."""
        def __init__(self):
            self.companion_manager = None
            self.current_companion = None
            self.current_conversation = None
            self.memory_store = None
            self.storage = None

        def set_current_companion(self, companion):
            self.current_companion = companion

        def send_message(self, message, callback):
            callback("Test response to: " + message)

    print("⚠️  Running API server in standalone mode (mock only)")
    print("   Use the main application for full functionality")

    mock_app = MockApp()
    server = APIServer(mock_app)
    server.start()

    print("\n🔄 Server is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.stop()
