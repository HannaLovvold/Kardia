"""Conversation storage and persistence layer."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from companion_data.models import Conversation, Companion, Message


class ConversationStorage:
    """Handles saving and loading conversations."""

    def __init__(self, conversations_dir: Path):
        """Initialize with conversations directory."""
        self.conversations_dir = conversations_dir
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def get_conversation_path(self, companion_id: str) -> Path:
        """Get the file path for a companion's conversation."""
        return self.conversations_dir / f"{companion_id}.json"

    def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation to disk."""
        try:
            path = self.get_conversation_path(conversation.companion_id)
            with open(path, "w") as f:
                json.dump(conversation.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False

    def load_conversation(self, companion_id: str) -> Optional[Conversation]:
        """Load a conversation from disk."""
        try:
            path = self.get_conversation_path(companion_id)
            if not path.exists():
                return None

            with open(path, "r") as f:
                data = json.load(f)

            messages = [Message.from_dict(m) for m in data.get("messages", [])]
            return Conversation(
                companion_id=data["companion_id"],
                messages=messages,
                created_at=data.get("created_at", ""),
                last_updated=data.get("last_updated", ""),
            )
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return None

    def get_or_create_conversation(self, companion_id: str) -> Conversation:
        """Get existing conversation or create new one."""
        conv = self.load_conversation(companion_id)
        if conv is None:
            now = datetime.now().isoformat()
            conv = Conversation(
                companion_id=companion_id,
                created_at=now,
                last_updated=now,
            )
        return conv

    def list_conversations(self) -> list:
        """List all conversation files."""
        try:
            files = list(self.conversations_dir.glob("*.json"))
            conversations = []

            for file_path in files:
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        conversations.append({
                            "companion_id": data["companion_id"],
                            "message_count": len(data.get("messages", [])),
                            "last_updated": data.get("last_updated", ""),
                        })
                except Exception:
                    continue

            return conversations
        except Exception as e:
            print(f"Error listing conversations: {e}")
            return []

    def delete_conversation(self, companion_id: str) -> bool:
        """Delete a conversation file."""
        try:
            path = self.get_conversation_path(companion_id)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    def export_conversation(self, companion_id: str, output_path: str) -> bool:
        """Export conversation to a text file."""
        try:
            conv = self.load_conversation(companion_id)
            if not conv:
                return False

            with open(output_path, "w") as f:
                f.write(f"Conversation with {companion_id}\n")
                f.write(f"Created: {conv.created_at}\n")
                f.write(f"Last Updated: {conv.last_updated}\n")
                f.write("=" * 50 + "\n\n")

                for msg in conv.messages:
                    role_name = "You" if msg.role == "user" else "Companion"
                    f.write(f"[{msg.timestamp}] {role_name}:\n")
                    f.write(f"{msg.content}\n\n")

            return True
        except Exception as e:
            print(f"Error exporting conversation: {e}")
            return False


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Path):
        """Initialize with config directory."""
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = config_dir / "config.json"
        self._config = {}
        self.load()

    def load(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self._config = json.load(f)
            else:
                self._config = self._get_default_config()
                self.save()
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = self._get_default_config()

    def save(self):
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default=None):
        """Get a config value."""
        return self._config.get(key, default)

    def set(self, key: str, value):
        """Set a config value."""
        self._config[key] = value
        self.save()

    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            "ai_backend": "ollama",
            "ollama_model": "mistral",
            "ollama_url": "http://localhost:11434",
            "api_key": "",
            "api_url": "https://api.openai.com/v1",
            "api_model": "gpt-3.5-turbo",
            "sms_forwarding_enabled": False,
            "auto_save_enabled": True,
            "theme": "system",
            "last_companion": None,
        }
