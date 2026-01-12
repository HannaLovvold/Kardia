"""Memory extraction from conversations using AI."""
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from memory import MemoryStore, Memory, MemoryType


class MemoryExtractor:
    """Extracts memories from conversations using AI."""

    def __init__(self, ai_backend, memory_store: MemoryStore):
        """
        Initialize memory extractor.

        Args:
            ai_backend: OllamaBackend instance
            memory_store: MemoryStore instance
        """
        self.ai_backend = ai_backend
        self.memory_store = memory_store

    def extract_from_conversation(
        self,
        messages: List[Dict],
        companion_id: str,
    ) -> List[Memory]:
        """
        Extract memories from a conversation.

        Args:
            messages: List of conversation messages
            companion_id: ID of the companion

        Returns:
            List of extracted Memory objects
        """
        if not messages:
            return []

        # Get recent user messages
        user_messages = [
            m["content"] for m in messages[-10:]
            if m["role"] == "user"
        ]

        if not user_messages:
            return []

        # Use AI to extract memories
        extraction_prompt = self._create_extraction_prompt(user_messages)

        try:
            response = self.ai_backend.generate_response(
                messages=[{"role": "user", "content": extraction_prompt}],
                system_prompt=self._get_extraction_system_prompt(),
            )

            # Parse the AI response
            memories = self._parse_extraction_response(response, companion_id)

            # Add to memory store
            added_memories = []
            for memory_data in memories:
                memory = self.memory_store.add_memory(
                    memory_type=memory_data["type"],
                    content=memory_data["content"],
                    key=memory_data.get("key"),
                    value=memory_data.get("value"),
                    importance=memory_data.get("importance", 2),
                    companion_id=companion_id,
                    is_shared=True,  # Auto-extracted memories are shared by default
                )
                added_memories.append(memory)

            return added_memories

        except Exception as e:
            print(f"Error extracting memories: {e}")
            return []

    def _get_extraction_system_prompt(self) -> str:
        """Get system prompt for memory extraction."""
        return """You are a memory extraction assistant. Your task is to analyze conversation messages and extract important information about the user.

Extract memories in these categories:
1. Personal Information: name, age, birthday, location, job, etc.
2. Preferences: likes, dislikes, favorites (food, music, movies, etc.)
3. Life Events: important past or upcoming events
4. Emotional States: recurring emotions, moods, feelings
5. Interests: hobbies, passions, topics they enjoy
6. Relationships: family, friends, partners
7. Goals: aspirations, things they want to achieve
8. Important Facts: other significant information

For each memory, provide:
- type: one of the categories above
- content: brief description
- key: short identifier (e.g., "name", "favorite_color")
- value: the actual value (e.g., "Alice", "blue")
- importance: 1-5 (5 = very important)

Respond ONLY with valid JSON array of memories. Format:
[
  {
    "type": "personal_info",
    "content": "User's name is Alice",
    "key": "name",
    "value": "Alice",
    "importance": 5
  }
]"""

    def _create_extraction_prompt(self, user_messages: List[str]) -> str:
        """Create prompt for extraction."""
        messages_text = "\n\n".join(
            f"Message {i+1}: {msg}"
            for i, msg in enumerate(user_messages)
        )

        return f"""Analyze these recent messages from the user and extract important memories.

Messages:
{messages_text}

Extract any important information about the user. Focus on:
- Personal details (name, age, location, job)
- Preferences (likes, dislikes, favorites)
- Important events or life updates
- Emotional patterns
- Interests and hobbies
- Goals and aspirations
- Relationships mentioned

Respond ONLY with a JSON array of memory objects. If no important information is found, return an empty array []."""

    def _parse_extraction_response(self, response: str, companion_id: str) -> List[Dict]:
        """Parse AI response into memory data."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                return []

            data = json.loads(json_match.group(0))

            memories = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                memory_type = item.get("type", "important_fact")

                # Validate memory type
                try:
                    MemoryType(memory_type)
                except ValueError:
                    memory_type = "important_fact"

                memories.append({
                    "type": memory_type,
                    "content": item.get("content", "")[:500],  # Limit length
                    "key": item.get("key", "")[:100] if item.get("key") else None,
                    "value": item.get("value", "")[:200] if item.get("value") else None,
                    "importance": max(1, min(5, item.get("importance", 2))),
                })

            return memories

        except json.JSONDecodeError as e:
            print(f"Error parsing memory extraction JSON: {e}")
            return []
        except Exception as e:
            print(f"Error parsing extraction response: {e}")
            return []

    def extract_quick_facts(
        self,
        message: str,
        companion_id: str,
    ) -> List[Memory]:
        """
        Quick extraction from a single message.
        Uses pattern matching for common facts.

        Args:
            message: User message
            companion_id: Companion ID

        Returns:
            List of extracted Memory objects
        """
        memories = []
        message_lower = message.lower()

        # Name extraction patterns
        name_patterns = [
            r"my name is (\w+)",
            r"i'm called (\w+)",
            r"call me (\w+)",
            r"i am (\w+) and",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).title()
                existing = self.memory_store.get_memory_by_key("name")

                if not existing or existing.value != name:
                    memory = self.memory_store.add_memory(
                        memory_type="personal_info",
                        content=f"User's name is {name}",
                        key="name",
                        value=name,
                        importance=5,
                        companion_id=companion_id,
                        is_shared=True,
                    )
                    memories.append(memory)

        # Location patterns
        location_patterns = [
            r"i live in ([\w\s]+)",
            r"i'm from ([\w\s]+)",
            r"i stay in ([\w\s]+)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                location = match.group(1).title()
                memory = self.memory_store.add_memory(
                    memory_type="personal_info",
                    content=f"User lives in {location}",
                    key="location",
                    value=location,
                    importance=3,
                    companion_id=companion_id,
                    is_shared=True,
                )
                memories.append(memory)

        # Preference patterns
        preferences = [
            (r"i love (\w+)", "loves", 3),
            (r"i hate (\w+)", "hates", 3),
            (r"i really like (\w+)", "likes", 2),
            (r"i can't stand (\w+)", "dislikes", 3),
            (r"my favorite (\w+) is (\w+)", "favorite", 4),
        ]

        for pattern, relation, importance in preferences:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if "favorite" in pattern:
                    thing = match.group(1)
                    value = match.group(2)
                    key = f"favorite_{thing}"
                    content = f"User's favorite {thing} is {value}"
                else:
                    value = match.group(1)
                    key = f"{relation}_{value}"
                    content = f"User {relation} {value}"

                memory = self.memory_store.add_memory(
                    memory_type="preference",
                    content=content,
                    key=key,
                    value=value,
                    importance=importance,
                    companion_id=companion_id,
                    is_shared=True,
                )
                memories.append(memory)

        return memories


class MemoryManager:
    """High-level manager for memory operations."""

    def __init__(self, ai_backend, memory_store: MemoryStore):
        """Initialize memory manager."""
        self.ai_backend = ai_backend
        self.memory_store = memory_store
        self.extractor = MemoryExtractor(ai_backend, memory_store)

    def process_conversation(
        self,
        messages: List[Dict],
        companion_id: str,
    ) -> Dict:
        """
        Process a conversation and extract memories.

        Args:
            messages: Conversation messages
            companion_id: Current companion

        Returns:
            Dict with extraction results
        """
        # Quick extraction from recent messages
        new_memories = []

        if messages:
            last_user_msg = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break

            if last_user_msg:
                quick_memories = self.extractor.extract_quick_facts(
                    last_user_msg,
                    companion_id,
                )
                new_memories.extend(quick_memories)

        # Deep extraction every 10 messages
        if len(messages) % 10 == 0 and len(messages) > 0:
            deep_memories = self.extractor.extract_from_conversation(
                messages,
                companion_id,
            )
            new_memories.extend(deep_memories)

        return {
            "new_memories": len(new_memories),
            "total_memories": self.memory_store.get_stats()["total_memories"],
            "memories": new_memories,
        }

    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Memory]:
        """Get memories relevant to a query."""
        # Search by query
        results = self.memory_store.search_memories(query)

        # Also get important memories
        important = self.memory_store.get_important_memories()

        # Combine and deduplicate
        seen = {m.id for m in results}
        for m in important:
            if m.id not in seen:
                results.append(m)
                seen.add(m.id)

        return results[:limit]

    def should_trigger_extraction(self, message_count: int) -> bool:
        """Check if extraction should run."""
        return message_count > 0 and message_count % 5 == 0
