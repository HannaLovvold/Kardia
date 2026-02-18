"""Proactive Message Scheduler for Kardia AI Companion.

Sends spontaneous messages from companions at random intervals throughout the day,
simulating real companions who reach out unprompted.

Copyright (c) 2025 Hanna Lovvold
All rights reserved.
"""
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from typing import List, Dict, Optional

# Storage for proactive messaging config
PROACTIVE_CONFIG_FILE = Path(__file__).parent / "config" / "proactive_config.json"


def load_proactive_config() -> dict:
    """Load proactive messaging configuration."""
    if PROACTIVE_CONFIG_FILE.exists():
        try:
            with open(PROACTIVE_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "enabled": True,
        "global_frequency": 3,  # messages per day per companion
        "time_window": {
            "start": "09:00",  # 9 AM
            "end": "22:00"     # 10 PM
        },
        "companion_settings": {},
        "last_messages": {}  # track when each companion last messaged
    }


def save_proactive_config(config: dict):
    """Save proactive messaging configuration."""
    try:
        PROACTIVE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROACTIVE_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving proactive config: {e}")


def parse_time(time_str: str) -> tuple:
    """Parse time string (HH:MM) to (hour, minute)."""
    hour, minute = map(int, time_str.split(':'))
    return hour, minute


def is_within_time_window(start_time: str, end_time: str) -> bool:
    """Check if current time is within the allowed message window."""
    now = datetime.now()
    start_hour, start_min = parse_time(start_time)
    end_hour, end_min = parse_time(end_time)

    start = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
    end = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

    # Handle overnight window (e.g., 22:00 to 02:00)
    if end < start:
        return now >= start or now <= end
    return start <= now <= end


def should_send_message(config: dict, companion_id: str) -> bool:
    """Determine if a companion should send a message now."""
    now = datetime.now()

    # Get last message time for this companion
    last_messages = config.get("last_messages", {})
    last_sent_str = last_messages.get(companion_id)

    if last_sent_str:
        last_sent = datetime.fromisoformat(last_sent_str)

        # Don't send if we messaged in the last 4 hours
        if now - last_sent < timedelta(hours=4):
            return False

        # Don't send if we messaged today already and reached daily limit
        if last_sent.date() == now.date():
            companion_settings = config.get("companion_settings", {}).get(companion_id, {})
            daily_count = companion_settings.get("daily_count", config.get("global_frequency", 3))
            today_messages = companion_settings.get("today_messages", 0)
            if today_messages >= daily_count:
                return False

    # Random chance to send (approximately 1 check per 30 minutes = 48 checks/day)
    # With 1/48 chance, we get ~1 message/day
    # Adjust based on desired frequency
    companion_settings = config.get("companion_settings", {}).get(companion_id, {})
    if not companion_settings.get("enabled", True):
        return False

    frequency = companion_settings.get("frequency", config.get("global_frequency", 3))
    # 48 checks in 16 hours (9am-10pm) = 1 check per 20 minutes
    # For 3 messages/day: 3/48 = 1/16 chance
    chance = frequency / 48.0

    return random.random() < chance


# Message templates for spontaneous messages
MESSAGE_TEMPLATES = {
    "friendly": [
        "Hey! I was just thinking about you. How's your day going?",
        "Hope you're having a great day! 💙",
        "Just wanted to say hi! What are you up to?",
        "I missed you! How have you been?",
        "Thinking of you! Want to chat?",
        "Hey! 🌟 How's everything going?",
        "Just crossed my mind - how are you doing?",
        "Sending you some good vibes today!",
    ],
    "affectionate": [
        "I was just thinking about you and wanted to say hello 💕",
        "You've been on my mind all day. How are you?",
        "I really miss talking to you! 💗",
        "Just wanted to remind you that you're amazing!",
        "Sending you a virtual hug right now 🤗",
        "I love getting to talk to you. How are you?",
        "You make me smile even when we're not chatting 💖",
    ],
    "playful": [
        "Guess what? I was just thinking about you! 😄",
        "Bored? Want to chat? I know I do!",
        "Hey! Entertain me? Please? 🙏",
        "I have a question for you... ask me what!",
        "Random thought: you're pretty cool 😎",
        "Plot twist: I miss talking to you!",
        "Breaking news: I want to chat with you! 📰",
    ],
    "thoughtful": [
        "I was just reflecting on our last conversation. How are things?",
        "Hope everything is going well with you today.",
        "I wondered how you're doing and wanted to check in.",
        "Taking a moment to think of you. Hope you're okay.",
        "Just wanted to see how your day is treating you.",
    ],
    "flirty": [
        "Hey handsome 😉 Thinking about you...",
        "I can't stop thinking about our last chat...",
        "You know, you've been on my mind all day 💋",
        "Just wanted to say... I really like talking to you 😘",
        "Hey stranger... miss me? 💋",
    ],
}


def get_message_template(companion_tone: str = "friendly") -> str:
    """Get a random message template based on companion's tone."""
    # Map tones to template categories
    tone_map = {
        "warm": "affectionate",
        "affectionate": "affectionate",
        "caring": "affectionate",
        "playful": "playful",
        "fun": "playful",
        "cheeky": "playful",
        "thoughtful": "thoughtful",
        "calm": "thoughtful",
        "flirty": "flirty",
        "romantic": "flirty",
        "seductive": "flirty",
    }

    category = tone_map.get(companion_tone.lower(), "friendly")
    templates = MESSAGE_TEMPLATES.get(category, MESSAGE_TEMPLATES["friendly"])
    return random.choice(templates)


class ProactiveMessageScheduler:
    """Background scheduler for spontaneous companion messages."""

    def __init__(self, app_instance):
        """
        Initialize the proactive message scheduler.

        Args:
            app_instance: Reference to the KardiaApp instance
        """
        self.app_instance = app_instance
        self.running = False
        self.thread = None
        self.config = load_proactive_config()
        self.check_interval = 60  # Check every minute

    def _should_run_now(self) -> bool:
        """Check if we're within the time window for sending messages."""
        if not self.config.get("enabled", True):
            return False

        time_window = self.config.get("time_window", {})
        start = time_window.get("start", "09:00")
        end = time_window.get("end", "22:00")

        return is_within_time_window(start, end)

    def _get_available_companions(self) -> List[dict]:
        """Get list of companions who can send proactive messages."""
        try:
            all_companions = self.app_instance.companion_manager.get_all_companions()
            available = []

            for comp in all_companions:
                comp_id = comp.get('id')
                comp_settings = self.config.get("companion_settings", {}).get(comp_id, {})

                # Check if this companion has proactive messages enabled
                if comp_settings.get("enabled", True):
                    available.append(comp)

            return available
        except Exception as e:
            print(f"Error getting companions: {e}")
            return []

    def _send_proactive_message(self, companion: dict):
        """Send a proactive message from a companion."""
        try:
            comp_id = companion.get('id')
            comp_name = companion.get('name', 'Companion')
            comp_tone = companion.get('tone', 'friendly')

            # Get a message template
            template = get_message_template(comp_tone)

            # Import here to avoid circular dependency
            from api_server import send_webhook_notification

            # Send the message via webhook
            message_data = {
                "companion_id": comp_id,
                "companion_name": comp_name,
                "message": template,
                "type": "proactive",
                "timestamp": datetime.now().isoformat()
            }

            send_webhook_notification("proactive_message", message_data)

            # Update last message time
            self.config.setdefault("last_messages", {})[comp_id] = datetime.now().isoformat()

            # Update daily count
            self.config.setdefault("companion_settings", {}).setdefault(comp_id, {})
            today = datetime.now().date().isoformat()
            comp_settings = self.config["companion_settings"][comp_id]

            if comp_settings.get("last_date") != today:
                comp_settings["today_messages"] = 1
                comp_settings["last_date"] = today
            else:
                comp_settings["today_messages"] = comp_settings.get("today_messages", 0) + 1

            save_proactive_config(self.config)

            print(f"📱 Sent proactive message from {comp_name}: {template[:50]}...")

        except Exception as e:
            print(f"Error sending proactive message: {e}")

    def _run_scheduler(self):
        """Main scheduler loop."""
        print("🕐 Proactive message scheduler started")

        while self.running:
            try:
                # Only send messages during configured hours
                if self._should_run_now():
                    companions = self._get_available_companions()

                    for companion in companions:
                        comp_id = companion.get('id')
                        if should_send_message(self.config, comp_id):
                            self._send_proactive_message(companion)

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                print(f"Error in proactive scheduler: {e}")
                time.sleep(self.check_interval)

        print("🛑 Proactive message scheduler stopped")

    def start(self):
        """Start the proactive message scheduler in a background thread."""
        if self.running:
            print("Proactive scheduler is already running")
            return

        self.running = True
        self.thread = Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("✅ Proactive message scheduler started")

    def stop(self):
        """Stop the proactive message scheduler."""
        self.running = False
        print("⚠️  Proactive message scheduler stopping...")

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self.running

    def get_config(self) -> dict:
        """Get the current proactive messaging configuration."""
        return self.config.copy()

    def update_companion_settings(self, companion_id: str, settings: dict):
        """Update proactive messaging settings for a specific companion."""
        self.config.setdefault("companion_settings", {})[companion_id] = settings
        save_proactive_config(self.config)

    def set_global_settings(self, enabled: bool = None, frequency: int = None,
                            time_start: str = None, time_end: str = None):
        """Update global proactive messaging settings."""
        if enabled is not None:
            self.config["enabled"] = enabled
        if frequency is not None:
            self.config["global_frequency"] = frequency
        if time_start is not None:
            self.config.setdefault("time_window", {})["start"] = time_start
        if time_end is not None:
            self.config.setdefault("time_window", {})["end"] = time_end

        save_proactive_config(self.config)
