"""Selfie Sender for Kardia AI Companion.

Sends pre-generated character selfies to the Android app based on:
- Time of day (Day/Night)
- Location context (Home/Outside)
- Random chance (~1/3 per day)
- Maximum one selfie per day per character
- Each picture sent only once

Copyright (c) 2025 Hanna Lovvold
All rights reserved.
"""
import base64
import fcntl
import json
import random
import shutil
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import List, Dict, Optional, Tuple

# Storage for selfie tracking
SELFIE_TRACKING_FILE = Path(__file__).parent / "config" / "selfies_sent.json"
# Avatars directory
AVATARS_DIR = Path(__file__).parent / "avatars"


# Time periods and location contexts
# Folder naming format: {Location}_{Time}
# Time periods: Day (06:00-18:00), Night (18:00-06:00)
# Locations: Home, Outside


def load_selfie_tracking() -> dict:
    """Load selfie tracking data."""
    if SELFIE_TRACKING_FILE.exists():
        try:
            with open(SELFIE_TRACKING_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "sent_selfies": {},  # {companion_id: [file_paths]}
        "last_sent_date": {}  # {companion_id: date_string}
    }


def save_selfie_tracking(tracking: dict):
    """Save selfie tracking data."""
    try:
        SELFIE_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SELFIE_TRACKING_FILE, 'w') as f:
            json.dump(tracking, f, indent=2)
    except Exception as e:
        print(f"Error saving selfie tracking: {e}")


def get_time_context() -> Tuple[str, str]:
    """
    Determine the current time context.

    Returns:
        Tuple of (location, time_period) where:
        - location: "Home" or "Outside" (random choice for now)
        - time_period: "Day" or "Night"
    """
    now = datetime.now()
    hour = now.hour

    # Determine time period
    if 6 <= hour < 18:
        time_period = "Day"
    else:
        time_period = "Night"

    # For location, we'll randomly choose between Home and Outside
    # This could be made smarter based on user context in the future
    location = random.choice(["Home", "Outside"])

    return location, time_period


def find_selfie_folders() -> Dict[str, Path]:
    """
    Scan the avatars directory for character selfie folders.

    Returns:
        Dict mapping character names to their selfie folder paths.
        Looks for folders named like "Sarah_Selfies", "Cloe_Selfies", etc.
    """
    selfie_folders = {}

    if not AVATARS_DIR.exists():
        return selfie_folders

    for item in AVATARS_DIR.iterdir():
        if item.is_dir() and item.name.endswith("_Selfies"):
            # Extract character name from folder name
            character_name = item.name.replace("_Selfies", "")
            selfie_folders[character_name] = item

    return selfie_folders


def get_available_selfies(selfie_folder: Path, location: str, time_period: str,
                          sent_selfies: List[str]) -> List[Path]:
    """
    Get available selfies for a character that haven't been sent yet.

    Args:
        selfie_folder: Path to the character's selfie folder
        location: "Home" or "Outside"
        time_period: "Day" or "Night"
        sent_selfies: List of already sent selfie file paths

    Returns:
        List of available selfie file paths
    """
    context_folder = selfie_folder / f"{location}_{time_period}"

    if not context_folder.exists():
        return []

    available = []
    for image_file in context_folder.iterdir():
        if image_file.is_file() and image_file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
            # Check if this selfie has been sent before
            if str(image_file) not in sent_selfies:
                available.append(image_file)

    return available


def encode_image_to_base64(image_path: Path) -> str:
    """Encode an image file to base64 string."""
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            return image_data
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return ""


def should_send_selfie_today(companion_id: str, tracking: dict) -> bool:
    """
    Check if a character should send a selfie today.

    Args:
        companion_id: The character's ID
        tracking: The tracking data dictionary

    Returns:
        True if selfie can be sent today, False otherwise
    """
    today = datetime.now().date().isoformat()
    last_sent = tracking.get("last_sent_date", {}).get(companion_id)

    # Already sent today
    if last_sent == today:
        return False

    # Random chance: approximately 1 in 3 chance to send on any given day
    # This means roughly every 3 days on average
    if random.random() < 0.33:  # ~33% chance
        return True

    return False


def move_selfie_to_sent(image_path: Path, selfie_folder: Path) -> bool:
    """
    Move a sent selfie to the Sent subfolder.

    Args:
        image_path: Path to the sent image
        selfie_folder: The character's selfie folder

    Returns:
        True if moved successfully, False otherwise
    """
    try:
        # Create Sent folder if it doesn't exist
        sent_folder = selfie_folder / "Sent"
        sent_folder.mkdir(parents=True, exist_ok=True)

        # Destination path
        dest_path = sent_folder / image_path.name

        # Handle duplicate filenames
        counter = 1
        original_dest = dest_path
        while dest_path.exists():
            stem = original_dest.stem
            suffix = original_dest.suffix
            dest_path = sent_folder / f"{stem}_{counter}{suffix}"
            counter += 1

        # Move the file
        shutil.move(str(image_path), str(dest_path))
        print(f"📁 Moved {image_path.name} to Sent folder")
        return True

    except Exception as e:
        print(f"Error moving selfie to Sent folder: {e}")
        return False


def send_selfie_webhook(companion_id: str, companion_name: str, image_path: Path,
                        base64_data: str, location: str, time_period: str):
    """
    Send a selfie notification via webhook.

    Args:
        companion_id: The character's ID
        companion_name: The character's display name
        image_path: Path to the image file
        base64_data: Base64 encoded image data
        location: Location context (Home/Outside)
        time_period: Time period (Day/Night)
    """
    try:
        # Import here to avoid circular dependency
        from api_server import send_webhook_notification

        # Get file extension for mime type
        ext = image_path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        message_data = {
            "companion_id": companion_id,
            "companion_name": companion_name,
            "type": "selfie",
            "image_base64": base64_data,
            "image_mime_type": mime_type,
            "image_name": image_path.name,
            "context": {
                "location": location,
                "time_period": time_period
            },
            "timestamp": datetime.now().isoformat()
        }

        send_webhook_notification("selfie", message_data)
        print(f"📸 Sent selfie from {companion_name}: {image_path.name} ({location}_{time_period})")

    except Exception as e:
        print(f"Error sending selfie webhook: {e}")


def get_companion_id_from_name(companion_name: str, app_instance) -> Optional[str]:
    """
    Find a companion ID from a display name.

    Args:
        companion_name: The display name of the character
        app_instance: The KardiaApp instance

    Returns:
        The companion ID if found, None otherwise
    """
    try:
        all_companions = app_instance.companion_manager.get_all_companions()
        for comp in all_companions:
            if comp.get('name') == companion_name:
                return comp.get('id')
            # Also check custom_name
            if comp.get('custom_name') == companion_name:
                return comp.get('id')
    except Exception as e:
        print(f"Error finding companion ID for {companion_name}: {e}")

    return None


def send_companion_selfie(companion_name: str, app_instance) -> bool:
    """
    Attempt to send a selfie for a specific companion.

    Args:
        companion_name: Name of the character
        app_instance: The KardiaApp instance

    Returns:
        True if a selfie was sent, False otherwise
    """
    # Load tracking data
    tracking = load_selfie_tracking()

    # Find companion ID
    companion_id = get_companion_id_from_name(companion_name, app_instance)
    if not companion_id:
        print(f"⚠️  Companion ID not found for {companion_name}")
        return False

    # Check if we should send a selfie today
    if not should_send_selfie_today(companion_id, tracking):
        return False

    # Get current time context
    location, time_period = get_time_context()

    # Find selfie folder for this character
    selfie_folders = find_selfie_folders()
    if companion_name not in selfie_folders:
        return False

    selfie_folder = selfie_folders[companion_name]

    # Get list of already sent selfies for this character
    sent_selfies = tracking.get("sent_selfies", {}).get(companion_id, [])

    # Get available selfies
    available_selfies = get_available_selfies(
        selfie_folder, location, time_period, sent_selfies
    )

    if not available_selfies:
        # Try the other time period if nothing available for current
        other_time = "Night" if time_period == "Day" else "Day"
        available_selfies = get_available_selfies(
            selfie_folder, location, other_time, sent_selfies
        )

    if not available_selfies:
        # Try the other location
        other_location = "Outside" if location == "Home" else "Home"
        available_selfies = get_available_selfies(
            selfie_folder, other_location, time_period, sent_selfies
        )

    if not available_selfies:
        return False

    # Pick a random selfie
    chosen_selfie = random.choice(available_selfies)

    # Encode image to base64
    base64_data = encode_image_to_base64(chosen_selfie)
    if not base64_data:
        return False

    # Send webhook notification
    send_selfie_webhook(
        companion_id,
        companion_name,
        chosen_selfie,
        base64_data,
        location,
        time_period
    )

    # Add selfie to conversation history
    try:
        ext = chosen_selfie.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')

        timestamp = datetime.now().isoformat()

        # First, reload to ensure we have latest version
        conversation = app_instance.storage.load_conversation(companion_id)
        if not conversation:
            conversation = app_instance.storage.get_or_create_conversation(companion_id)

        # Add a note for AI context - it knows it sent a selfie
        # The Android app can display just the image
        selfie_note = "[Sent a selfie]"
        conversation.add_message(
            role="assistant",
            content=selfie_note,
            timestamp=timestamp,
            image_base64=base64_data,
            image_mime_type=mime_type,
            image_name=chosen_selfie.name
        )
        app_instance.storage.save_conversation(conversation)
        print(f"💾 Saved selfie to conversation for {companion_name}")

    except Exception as e:
        print(f"Error saving selfie to conversation: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Error saving selfie to conversation: {e}")

    # Move selfie to Sent folder
    move_selfie_to_sent(chosen_selfie, selfie_folder)

    # Update tracking
    tracking.setdefault("sent_selfies", {}).setdefault(companion_id, []).append(str(chosen_selfie))
    tracking.setdefault("last_sent_date", {})[companion_id] = datetime.now().date().isoformat()
    save_selfie_tracking(tracking)

    return True


class SelfieScheduler:
    """Background scheduler for sending character selfies."""

    def __init__(self, app_instance):
        """
        Initialize the selfie scheduler.

        Args:
            app_instance: Reference to the KardiaApp instance
        """
        self.app_instance = app_instance
        self.running = False
        self.thread = None
        self.check_interval = 3600  # Check every hour

    def _run_scheduler(self):
        """Main scheduler loop."""
        print("📸 Selfie scheduler started")

        while self.running:
            try:
                # Get all companions
                companions = self.app_instance.companion_manager.get_all_companions()

                for companion in companions:
                    comp_name = companion.get('name')

                    # Try to send a selfie for this companion
                    send_companion_selfie(comp_name, self.app_instance)

                # Sleep until next check
                import time
                time.sleep(self.check_interval)

            except Exception as e:
                print(f"Error in selfie scheduler: {e}")
                import time
                time.sleep(self.check_interval)

        print("🛑 Selfie scheduler stopped")

    def start(self):
        """Start the selfie scheduler in a background thread."""
        if self.running:
            print("Selfie scheduler is already running")
            return

        self.running = True
        self.thread = Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("✅ Selfie scheduler started")

    def stop(self):
        """Stop the selfie scheduler."""
        self.running = False
        print("⚠️  Selfie scheduler stopping...")

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self.running


def send_selfie_now(companion_id: str, app_instance, force: bool = False) -> bool:
    """
    Manually trigger sending a selfie for a specific companion.

    Args:
        companion_id: The companion's ID
        app_instance: The KardiaApp instance
        force: If True, bypass daily limit and random chance

    Returns:
        True if a selfie was sent, False otherwise
    """
    # Get companion info
    companion = app_instance.companion_manager.get_companion(companion_id)
    if not companion:
        return False

    companion_name = companion.get('name')

    # Load tracking data
    tracking = load_selfie_tracking()

    # Check if we should send (unless forced)
    if not force and not should_send_selfie_today(companion_id, tracking):
        return False

    # Get current time context
    location, time_period = get_time_context()

    # Find selfie folder
    selfie_folders = find_selfie_folders()
    if companion_name not in selfie_folders:
        return False

    selfie_folder = selfie_folders[companion_name]

    # Get sent selfies
    sent_selfies = tracking.get("sent_selfies", {}).get(companion_id, [])

    # Get available selfies
    available_selfies = get_available_selfies(
        selfie_folder, location, time_period, sent_selfies
    )

    if not available_selfies:
        # Try other contexts
        for other_loc in ["Home", "Outside"]:
            for other_time in ["Day", "Night"]:
                if other_loc == location and other_time == time_period:
                    continue
                more = get_available_selfies(
                    selfie_folder, other_loc, other_time, sent_selfies
                )
                available_selfies.extend(more)

    if not available_selfies:
        return False

    # Pick random selfie
    chosen_selfie = random.choice(available_selfies)

    # Encode and send
    base64_data = encode_image_to_base64(chosen_selfie)
    if not base64_data:
        return False

    send_selfie_webhook(
        companion_id,
        companion_name,
        chosen_selfie,
        base64_data,
        location,
        time_period
    )

    # Add selfie to conversation history
    try:
        ext = chosen_selfie.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')

        timestamp = datetime.now().isoformat()

        # First, reload to ensure we have latest version
        conversation = app_instance.storage.load_conversation(companion_id)
        if not conversation:
            conversation = app_instance.storage.get_or_create_conversation(companion_id)

        selfie_note = "[Sent a selfie]"
        conversation.add_message(
            role="assistant",
            content=selfie_note,
            timestamp=timestamp,
            image_base64=base64_data,
            image_mime_type=mime_type,
            image_name=chosen_selfie.name
        )
        app_instance.storage.save_conversation(conversation)
        print(f"💾 Saved selfie to conversation for {companion_name}")

    except Exception as e:
        print(f"Error saving selfie to conversation: {e}")
        import traceback
        traceback.print_exc()

    # Move selfie to Sent folder
    move_selfie_to_sent(chosen_selfie, selfie_folder)

    # Update tracking
    tracking.setdefault("sent_selfies", {}).setdefault(companion_id, []).append(str(chosen_selfie))
    tracking.setdefault("last_sent_date", {})[companion_id] = datetime.now().date().isoformat()
    save_selfie_tracking(tracking)

    return True
