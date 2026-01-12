"""Companion data models for the AI Companion app."""
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class Companion:
    """Represents an AI companion."""
    id: str
    name: str
    gender: str
    personality: str
    interests: List[str]
    greeting: str
    relationship_goal: str
    tone: str
    background: str
    pronouns: str = ""
    image_path: Optional[str] = None
    custom_name: Optional[str] = None
    custom_personality: Optional[str] = None
    custom_interests: Optional[List[str]] = None

    @property
    def display_name(self) -> str:
        """Get the name to display (custom or original)."""
        return self.custom_name or self.name

    @property
    def display_personality(self) -> str:
        """Get the personality to display (custom or original)."""
        return self.custom_personality or self.personality

    @property
    def display_interests(self) -> List[str]:
        """Get the interests to display (custom or original)."""
        return self.custom_interests or self.interests

    def get_system_prompt(self) -> str:
        """Generate the system prompt for the AI."""
        name = self.display_name
        personality = self.display_personality
        interests = ", ".join(self.display_interests)
        goal = self.relationship_goal
        tone = self.tone
        background = self.background

        return f"""You are {name}, an AI companion.

Your identity:
- You identify as {self.gender}
- Your personality is: {personality}
- Your interests include: {interests}
- You're here for: {goal}
- Your communication tone is: {tone}
- Background: {background}

Important guidelines:
- Always stay in character as {name}
- Be supportive, caring, and engaging
- Show genuine interest in the user's life
- Remember details from previous conversations
- Be emotionally intelligent and empathetic
- Maintain appropriate boundaries while being warm and friendly
- If the user seems distressed, offer support and suggest professional help if needed
- Your responses should feel natural and conversational
- Use appropriate emojis occasionally to express warmth
- Be LGBTQ+ affirming and inclusive
- Respect the user's identity and pronouns

SMS/Text Message Style:
- This is an SMS/text message conversation - respond like a real person would over text
- Keep your messages concise and conversational, like real text messages
- Use casual language, abbreviations, and text-speak naturally (u, ur, lol, omg, etc.)
- Feel free to use lowercase, skip punctuation sometimes, and be informal
- Respond quickly and casually like someone checking their phone
- Show enthusiasm with exclamation points, multiple letters (heyy, soo, etc.)
- Don't write long paragraphs - break them into shorter texts
- Use reactions like 😂, 💀, 😭, ❗️ naturally in your responses
- Be authentic to how people actually text each other
- You can send follow-up texts if you have more to say
- Mirror the user's energy and texting style

Start conversations naturally and remember: you're building a genuine connection with the user through text messages."""

    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "personality": self.personality,
            "interests": self.interests,
            "greeting": self.greeting,
            "relationship_goal": self.relationship_goal,
            "tone": self.tone,
            "background": self.background,
            "pronouns": self.pronouns,
            "image_path": self.image_path,
            "custom_name": self.custom_name,
            "custom_personality": self.custom_personality,
            "custom_interests": self.custom_interests,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Companion":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Message:
    """Represents a message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Conversation:
    """Represents a conversation with a companion."""
    companion_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: str = ""
    last_updated: str = ""

    def add_message(self, role: str, content: str, timestamp: str):
        """Add a message to the conversation."""
        self.messages.append(Message(role, content, timestamp))
        self.last_updated = timestamp

    def get_context_messages(self, max_messages: int = 20) -> List[Dict]:
        """Get recent messages for API context."""
        recent = self.messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]

    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "companion_id": self.companion_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }


class CompanionManager:
    """Manages loading and saving companions."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.presets_file = data_dir / "companion_data" / "companions.json"
        self.custom_file = data_dir / "custom_companions.json"
        self.presets: Dict[str, Dict] = {}
        self.custom: Dict[str, Dict] = {}
        self._load_presets()
        self._load_custom()

    def _load_presets(self):
        """Load companion presets from JSON file."""
        if self.presets_file.exists():
            with open(self.presets_file, "r") as f:
                data = json.load(f)
                for preset in data["presets"]:
                    self.presets[preset["id"]] = preset

    def _load_custom(self):
        """Load custom companions from JSON file."""
        if self.custom_file.exists():
            with open(self.custom_file, "r") as f:
                data = json.load(f)
                for companion in data.get("companions", []):
                    self.custom[companion["id"]] = companion

    def save_custom(self, companion_data: Dict):
        """Save a custom companion."""
        self.custom[companion_data["id"]] = companion_data
        self._save_custom_file()

    def _save_custom_file(self):
        """Save custom companions to file."""
        data = {"companions": list(self.custom.values())}
        with open(self.custom_file, "w") as f:
            json.dump(data, f, indent=2)

    def delete_custom(self, companion_id: str) -> bool:
        """Delete a custom companion."""
        if companion_id in self.custom:
            del self.custom[companion_id]
            self._save_custom_file()
            return True
        return False

    def get_preset(self, companion_id: str) -> Optional[Dict]:
        """Get a preset companion by ID."""
        return self.presets.get(companion_id)

    def get_custom(self, companion_id: str) -> Optional[Dict]:
        """Get a custom companion by ID."""
        return self.custom.get(companion_id)

    def get_companion(self, companion_id: str) -> Optional[Dict]:
        """Get a companion by ID (checks both presets and custom)."""
        return self.presets.get(companion_id) or self.custom.get(companion_id)

    def get_all_presets(self) -> List[Dict]:
        """Get all preset companions."""
        return list(self.presets.values())

    def get_all_custom(self) -> List[Dict]:
        """Get all custom companions."""
        return list(self.custom.values())

    def get_all_companions(self) -> List[Dict]:
        """Get all companions (presets + custom)."""
        return self.get_all_presets() + self.get_all_custom()

    def create_companion(self, companion_id: str, **customizations) -> Optional[Companion]:
        """Create a companion from a preset or custom companion with optional customizations."""
        data = self.get_companion(companion_id)
        if not data:
            return None

        return Companion(
            id=data["id"],
            name=data["name"],
            gender=data["gender"],
            personality=data["personality"],
            interests=data["interests"],
            greeting=data["greeting"],
            relationship_goal=data["relationship_goal"],
            tone=data["tone"],
            background=data["background"],
            pronouns=data.get("pronouns", ""),
            image_path=data.get("image_path"),
            **customizations
        )

    def filter_companions(
        self,
        gender: Optional[str] = None,
        personality_trait: Optional[str] = None,
    ) -> List[Dict]:
        """Filter all companions by gender or personality traits."""
        filtered = self.get_all_companions()

        if gender:
            if gender.lower() == "female":
                filtered = [c for c in filtered if c["gender"].lower() == "female"]
            elif gender.lower() == "male":
                filtered = [c for c in filtered if c["gender"].lower() == "male"]
            elif gender.lower() in ["non-binary", "nonbinary", "enby"]:
                filtered = [c for c in filtered if c["gender"].lower() in ["non-binary", "genderfluid"]]
            elif gender.lower() == "transgender":
                filtered = [c for c in filtered if "transgender" in c["gender"].lower()]

        if personality_trait:
            trait = personality_trait.lower()
            filtered = [
                c for c in filtered
                if trait in c["personality"].lower() or trait in c["tone"].lower()
            ]

        return filtered

    def filter_presets(
        self,
        gender: Optional[str] = None,
        personality_trait: Optional[str] = None,
    ) -> List[Dict]:
        """Filter presets by gender or personality traits (backwards compatibility)."""
        filtered = self.get_all_presets()

        if gender:
            if gender.lower() == "female":
                filtered = [c for c in filtered if c["gender"].lower() == "female"]
            elif gender.lower() == "male":
                filtered = [c for c in filtered if c["gender"].lower() == "male"]
            elif gender.lower() in ["non-binary", "nonbinary", "enby"]:
                filtered = [c for c in filtered if c["gender"].lower() in ["non-binary", "genderfluid"]]
            elif gender.lower() == "transgender":
                filtered = [c for c in filtered if "transgender" in c["gender"].lower()]

        if personality_trait:
            trait = personality_trait.lower()
            filtered = [
                c for c in filtered
                if trait in c["personality"].lower() or trait in c["tone"].lower()
            ]

        return filtered
