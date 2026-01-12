"""Manages SMS-to-companion mappings and multi-companion SMS support."""
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


class SMSCompanionManager:
    """Manages mappings between phone numbers and companions."""

    def __init__(self, storage_path: Path):
        """
        Initialize the SMS companion manager.

        Args:
            storage_path: Path to store mapping data
        """
        self.storage_path = storage_path / "sms_companion_mapping.json"
        self.mappings: Dict[str, dict] = {}
        self.load_mappings()

    def load_mappings(self):
        """Load phone number to companion mappings from file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.mappings = data.get('mappings', {})
            except Exception as e:
                print(f"Error loading SMS mappings: {e}")
                self.mappings = {}
        else:
            self.mappings = {}

    def save_mappings(self):
        """Save phone number to companion mappings to file."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'mappings': self.mappings,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving SMS mappings: {e}")

    def get_companion_id(self, phone_number: str) -> Optional[str]:
        """
        Get the companion ID associated with a phone number.

        Args:
            phone_number: Phone number (can be formatted or unformatted)

        Returns:
            Companion ID or None if not mapped
        """
        # Normalize phone number (remove spaces, dashes, etc.)
        normalized = self._normalize_phone_number(phone_number)

        if normalized in self.mappings:
            return self.mappings[normalized]['companion_id']
        return None

    def set_companion_id(self, phone_number: str, companion_id: str, companion_name: str = None):
        """
        Set the companion for a phone number.

        Args:
            phone_number: Phone number
            companion_id: ID of the companion
            companion_name: Optional name of the companion
        """
        normalized = self._normalize_phone_number(phone_number)

        self.mappings[normalized] = {
            'companion_id': companion_id,
            'companion_name': companion_name or companion_id,
            'phone_number': phone_number,
            'assigned_at': datetime.now().isoformat(),
            'last_interaction': datetime.now().isoformat()
        }
        self.save_mappings()

    def update_last_interaction(self, phone_number: str):
        """Update the last interaction time for a phone number."""
        normalized = self._normalize_phone_number(phone_number)
        if normalized in self.mappings:
            self.mappings[normalized]['last_interaction'] = datetime.now().isoformat()
            self.save_mappings()

    def remove_mapping(self, phone_number: str):
        """Remove a phone number mapping."""
        normalized = self._normalize_phone_number(phone_number)
        if normalized in self.mappings:
            del self.mappings[normalized]
            self.save_mappings()

    def get_all_mappings(self) -> Dict[str, dict]:
        """Get all phone number mappings."""
        return self.mappings.copy()

    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Normalize a phone number for consistent mapping.

        Removes spaces, dashes, parentheses, and plus sign.

        Args:
            phone_number: Phone number in any format

        Returns:
            Normalized phone number (digits only)
        """
        import re
        # Remove all non-digit characters
        return re.sub(r'[^\d]', '', phone_number)

    def get_phone_info(self, phone_number: str) -> Optional[dict]:
        """Get full information about a phone number mapping."""
        normalized = self._normalize_phone_number(phone_number)
        return self.mappings.get(normalized)


class SMSCommandParser:
    """Parses and handles SMS commands."""

    def __init__(self, companion_manager, companion_mgr):
        """
        Initialize SMS command parser.

        Args:
            companion_manager: SMSCompanionManager instance
            companion_mgr: CompanionManager instance
        """
        self.sms_companion_mgr = companion_manager
        self.companion_mgr = companion_mgr

        # Command prefixes
        self.commands = {
            'switch': self._cmd_switch,
            'list': self._cmd_list,
            'help': self._cmd_help,
            'who': self._cmd_who,
            'reset': self._cmd_reset,
        }

    def parse_message(self, message: str, phone_number: str) -> tuple:
        """
        Parse an SMS message for commands.

        Args:
            message: The SMS message body
            phone_number: Sender's phone number

        Returns:
            Tuple of (is_command, response_message, new_companion_id)
        """
        message = message.strip()

        # Check if this is a command
        if message.startswith('/') or message.lower().startswith('switch to'):
            # It's a command
            return self._handle_command(message, phone_number)
        elif message.lower().startswith('who are you'):
            return self._handle_command('/who', phone_number)
        elif message.lower() in ['help', 'help me', 'commands']:
            return self._handle_command('/help', phone_number)
        elif message.lower() in ['list companions', 'list', 'show companions']:
            return self._handle_command('/list', phone_number)

        # Not a command
        return (False, None, None)

    def _handle_command(self, message: str, phone_number: str) -> tuple:
        """
        Handle a command message.

        Returns:
            Tuple of (is_command, response_message, new_companion_id)
        """
        message_lower = message.lower().strip()

        # Check for "switch to [companion]" format
        if message_lower.startswith('switch to '):
            companion_name = message_lower[10:].strip()
            return self._cmd_switch(companion_name, phone_number)

        # Check for /command format
        if message.startswith('/'):
            parts = message[1:].split()
            command = parts[0].lower() if parts else ''

            if command in self.commands:
                args = ' '.join(parts[1:]) if len(parts) > 1 else None
                return self.commands[command](args, phone_number)

        # Unknown command
        response = "❓ Unknown command. Text 'help' for available commands."
        return (True, response, None)

    def _cmd_switch(self, companion_name: str, phone_number: str) -> tuple:
        """Handle: switch to [companion name]"""
        # Find companion by name (fuzzy search)
        companions = self.companion_mgr.get_all_companions()
        companion_name_lower = companion_name.lower()

        # Try exact match first
        matched = None
        for comp in companions:
            if comp['name'].lower() == companion_name_lower:
                matched = comp
                break
            # Try fuzzy match (contains)
            if companion_name_lower in comp['name'].lower():
                if not matched:  # Take first fuzzy match
                    matched = comp

        if matched:
            # Update mapping
            self.sms_companion_mgr.set_companion_id(
                phone_number,
                matched['id'],
                matched['name']
            )

            response = f"✅ Switched to {matched['name']}! I'm now {matched['name']}."
            return (True, response, matched['id'])
        else:
            available = ', '.join([c['name'] for c in companions[:5]])
            response = f"❌ Couldn't find '{companion_name}'. Available: {available}..."
            return (True, response, None)

    def _cmd_list(self, args, phone_number: str) -> tuple:
        """Handle: list"""
        companions = self.companion_mgr.get_all_companions()

        current_id = self.sms_companion_mgr.get_companion_id(phone_number)
        current_name = "None"
        if current_id:
            for comp in companions:
                if comp['id'] == current_id:
                    current_name = comp['name']
                    break

        response = f"📱 Current companion: {current_name}\n\n"
        response += "Available companions:\n"

        for i, comp in enumerate(companions[:10], 1):
            marker = "👉 " if comp['id'] == current_id else "   "
            response += f"{marker}{i}. {comp['name']} ({comp['gender']})\n"

        if len(companions) > 10:
            response += f"\n... and {len(companions) - 10} more"

        response += "\n💡 Text 'switch to [name]' to change companions"

        return (True, response, None)

    def _cmd_help(self, args, phone_number: str) -> tuple:
        """Handle: help"""
        response = """🤖 SMS Commands:

/switch [name] - Switch to a different companion
/list - Show all available companions
/who - Who am I currently talking to?
/reset - Reset to default companion
/help - Show this help message

You can also use natural language:
• "Switch to [companion name]"
• "Who are you?"
• "List companions"
• "Help me"

💬 Or just chat normally!"""
        return (True, response, None)

    def _cmd_who(self, args, phone_number: str) -> tuple:
        """Handle: who"""
        companion_id = self.sms_companion_mgr.get_companion_id(phone_number)

        if companion_id:
            companions = self.companion_mgr.get_all_companions()
            for comp in companions:
                if comp['id'] == companion_id:
                    response = f"👤 You're talking to {comp['name']}!\n"
                    response += f"Gender: {comp['gender']}\n"
                    response += f"Personality: {comp.get('personality', 'Friendly')[:50]}..."
                    return (True, response, None)

        response = "👤 No companion selected. Text 'switch to [name]' to pick one!"
        return (True, response, None)

    def _cmd_reset(self, args, phone_number: str) -> tuple:
        """Handle: reset"""
        self.sms_companion_mgr.remove_mapping(phone_number)
        response = "🔄 Reset! Next message will use the default companion from the app."
        return (True, response, None)
