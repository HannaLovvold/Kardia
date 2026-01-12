"""Long-term memory system for AI companions."""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class MemoryType(Enum):
    """Types of memories."""
    PERSONAL_INFO = "personal_info"  # Name, age, location, etc.
    PREFERENCE = "preference"  # Likes, dislikes, favorites
    LIFE_EVENT = "life_event"  # Important life events
    EMOTIONAL_STATE = "emotional_state"  # Recurring emotions/moods
    INTEREST = "interest"  # Hobbies, passions, topics
    RELATIONSHIP = "relationship"  # Family, friends, partners
    GOAL = "goal"  # User's goals and aspirations
    IMPORTANT_FACT = "important_fact"  # Other important information
    CONVERSATION_TOPIC = "conversation_topic"  # Topics user likes discussing


@dataclass
class Memory:
    """Represents a single memory."""
    id: str
    memory_type: str  # MemoryType value
    content: str  # The actual memory content
    key: Optional[str] = None  # Optional key for quick lookup (e.g., "name", "birthday")
    value: Optional[str] = None  # Optional value (e.g., "Alice", "1990-05-15")
    importance: int = 1  # 1-5, how important this memory is
    created_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
    companion_id: str = ""  # Which companion created this memory
    conversation_id: Optional[str] = None  # Source conversation
    is_shared: bool = True  # If True, shared across all companions; if False, specific to this companion

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        """Create from dictionary."""
        return cls(**data)

    def touch(self):
        """Update access timestamp and count."""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1


class MemoryStore:
    """Manages long-term memories for the user."""

    def __init__(self, data_dir: Path):
        """Initialize memory store."""
        self.data_dir = data_dir
        self.memory_file = data_dir / "memories.json"
        self._memories: List[Memory] = []
        self._index_by_key: Dict[str, Memory] = {}
        self.load()

    def load(self):
        """Load memories from disk."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    self._memories = [Memory.from_dict(m) for m in data]
                    self._rebuild_index()
            except Exception as e:
                print(f"Error loading memories: {e}")
                self._memories = []
        else:
            self._memories = []
        self._rebuild_index()

    def save(self):
        """Save memories to disk."""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            data = [m.to_dict() for m in self._memories]
            with open(self.memory_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving memories: {e}")

    def _rebuild_index(self):
        """Rebuild the key index."""
        self._index_by_key = {}
        for memory in self._memories:
            if memory.key:
                self._index_by_key[memory.key] = memory

    def add_memory(
        self,
        memory_type: str,
        content: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        importance: int = 1,
        companion_id: str = "",
        is_shared: bool = True,
    ) -> Memory:
        """Add a new memory."""
        import uuid

        memory = Memory(
            id=str(uuid.uuid4()),
            memory_type=memory_type,
            content=content,
            key=key,
            value=value,
            importance=importance,
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            companion_id=companion_id,
            is_shared=is_shared,
        )

        # If memory with same key exists, update it
        if key and key in self._index_by_key:
            existing = self._index_by_key[key]
            existing.value = value
            existing.content = content
            existing.importance = max(existing.importance, importance)
            existing.last_accessed = datetime.now().isoformat()
            self.save()
            return existing

        self._memories.append(memory)
        if key:
            self._index_by_key[key] = memory
        self.save()

        return memory

    def get_memory_by_key(self, key: str) -> Optional[Memory]:
        """Get memory by key."""
        memory = self._index_by_key.get(key)
        if memory:
            memory.touch()
            self.save()
        return memory

    def get_memories_by_type(self, memory_type: str) -> List[Memory]:
        """Get all memories of a specific type."""
        memories = [m for m in self._memories if m.memory_type == memory_type]
        for m in memories:
            m.touch()
        self.save()
        return memories

    def get_important_memories(self, min_importance: int = 3) -> List[Memory]:
        """Get memories above importance threshold."""
        memories = [m for m in self._memories if m.importance >= min_importance]
        for m in memories:
            m.touch()
        self.save()
        return sorted(memories, key=lambda m: m.importance, reverse=True)

    def get_recent_memories(self, limit: int = 20) -> List[Memory]:
        """Get recently accessed memories."""
        memories = sorted(
            self._memories,
            key=lambda m: m.last_accessed,
            reverse=True,
        )[:limit]
        for m in memories:
            m.touch()
        self.save()
        return memories

    def get_all_memories(self) -> List[Memory]:
        """Get all memories."""
        return sorted(
            self._memories,
            key=lambda m: m.last_accessed,
            reverse=True,
        )

    def search_memories(self, query: str) -> List[Memory]:
        """Search memories by content."""
        query_lower = query.lower()
        return [
            m for m in self._memories
            if query_lower in m.content.lower() or
            (m.key and query_lower in m.key.lower()) or
            (m.value and query_lower in m.value.lower())
        ]

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        for i, memory in enumerate(self._memories):
            if memory.id == memory_id:
                if memory.key:
                    self._index_by_key.pop(memory.key, None)
                self._memories.pop(i)
                self.save()
                return True
        return False

    def update_memory_importance(self, memory_id: str, importance: int) -> bool:
        """Update memory importance."""
        for memory in self._memories:
            if memory.id == memory_id:
                memory.importance = max(1, min(5, importance))
                self.save()
                return True
        return False

    def get_memories_for_context(self, max_count: int = 15) -> List[Memory]:
        """Get memories formatted for AI context."""
        # Prioritize by importance and recent access
        important = self.get_important_memories(3)
        recent = [m for m in self.get_recent_memories(20) if m not in important]

        # Combine and limit
        memories = important + recent
        return memories[:max_count]

    def get_context_summary(self) -> str:
        """Get a summary of memories for AI context."""
        memories = self.get_memories_for_context()

        if not memories:
            return "No information about the user yet."

        summary_parts = []

        # Group by type
        by_type = {}
        for memory in memories:
            if memory.memory_type not in by_type:
                by_type[memory.memory_type] = []
            by_type[memory.memory_type].append(memory)

        # Format each type
        type_labels = {
            "personal_info": "Personal Information",
            "preference": "Preferences",
            "life_event": "Life Events",
            "emotional_state": "Emotional Patterns",
            "interest": "Interests",
            "relationship": "Relationships",
            "goal": "Goals",
            "important_fact": "Important Facts",
        }

        for memory_type, type_memories in by_type.items():
            label = type_labels.get(memory_type, memory_type.replace("_", " ").title())
            items = []
            for m in type_memories[:5]:  # Limit per type
                if m.key and m.value:
                    items.append(f"- {m.key}: {m.value}")
                else:
                    items.append(f"- {m.content}")

            if items:
                summary_parts.append(f"{label}:\n" + "\n".join(items))

        return "\n\n".join(summary_parts) if summary_parts else "No information about the user yet."

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "total_memories": len(self._memories),
            "by_type": {
                mt.value: len([m for m in self._memories if m.memory_type == mt.value])
                for mt in MemoryType
            },
            "important_count": len(self.get_important_memories(3)),
            "companion_breakdown": self._count_by_companion(),
        }

    def _count_by_companion(self) -> Dict[str, int]:
        """Count memories by companion."""
        counts = {}
        for memory in self._memories:
            cid = memory.companion_id or "unknown"
            counts[cid] = counts.get(cid, 0) + 1
        return counts

    def export_memories(self, export_path: str, format: str = "json") -> Dict:
        """
        Export memories to a file.

        Args:
            export_path: Path to export file
            format: Export format ("json" or "txt")

        Returns:
            Dict with success status and info
        """
        try:
            export_file = Path(export_path)

            if format == "json":
                # Export as JSON
                data = {
                    "version": "1.0",
                    "export_date": datetime.now().isoformat(),
                    "total_memories": len(self._memories),
                    "memories": [m.to_dict() for m in self._memories],
                }

                with open(export_file, "w") as f:
                    json.dump(data, f, indent=2)

                return {
                    "success": True,
                    "format": "json",
                    "count": len(self._memories),
                    "path": str(export_file),
                }

            elif format == "txt":
                # Export as readable text
                with open(export_file, "w") as f:
                    f.write("=" * 60 + "\n")
                    f.write("AI Companion Memory Export\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Memories: {len(self._memories)}\n")
                    f.write("=" * 60 + "\n\n")

                    # Group by type
                    by_type = {}
                    for memory in self._memories:
                        if memory.memory_type not in by_type:
                            by_type[memory.memory_type] = []
                        by_type[memory.memory_type].append(memory)

                    type_labels = {
                        "personal_info": "Personal Information",
                        "preference": "Preferences",
                        "life_event": "Life Events",
                        "emotional_state": "Emotional States",
                        "interest": "Interests",
                        "relationship": "Relationships",
                        "goal": "Goals",
                        "important_fact": "Important Facts",
                    }

                    for memory_type, memories in sorted(by_type.items()):
                        label = type_labels.get(memory_type, memory_type.replace("_", " ").title())
                        f.write(f"\n{label}\n")
                        f.write("-" * 40 + "\n")

                        for memory in sorted(memories, key=lambda m: m.importance, reverse=True):
                            stars = "★" * memory.importance + "☆" * (5 - memory.importance)
                            f.write(f"\n[{stars}] {memory.content}\n")

                            if memory.key and memory.value:
                                f.write(f"  Key: {memory.key} = {memory.value}\n")

                            f.write(f"  Created: {memory.created_at[:10]}\n")

                            if not memory.is_shared:
                                f.write(f"  Companion-specific: {memory.companion_id}\n")

                    f.write("\n" + "=" * 60 + "\n")

                return {
                    "success": True,
                    "format": "txt",
                    "count": len(self._memories),
                    "path": str(export_file),
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown format: {format}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def import_memories(
        self,
        import_path: str,
        merge: bool = True,
    ) -> Dict:
        """
        Import memories from a file.

        Args:
            import_path: Path to import file
            merge: If True, merge with existing memories. If False, replace all.

        Returns:
            Dict with success status and info
        """
        try:
            import_file = Path(import_path)

            if not import_file.exists():
                return {
                    "success": False,
                    "error": "File not found",
                }

            with open(import_file, "r") as f:
                data = json.load(f)

            # Check if this is an export file with metadata
            if isinstance(data, dict) and "memories" in data:
                memories_data = data["memories"]
                source_version = data.get("version", "unknown")
                source_date = data.get("export_date", "unknown")
            elif isinstance(data, list):
                # Direct list of memories
                memories_data = data
                source_version = "unknown"
                source_date = "unknown"
            else:
                return {
                    "success": False,
                    "error": "Invalid import file format",
                }

            if not merge:
                # Replace all memories
                self._memories = []
                self._index_by_key = {}

            added_count = 0
            updated_count = 0
            skipped_count = 0

            for mem_data in memories_data:
                try:
                    # Handle old exports without is_shared field
                    if "is_shared" not in mem_data:
                        mem_data["is_shared"] = True

                    memory = Memory.from_dict(mem_data)

                    # Check for duplicate by key
                    if memory.key and memory.key in self._index_by_key:
                        if merge:
                            # Update existing
                            existing = self._index_by_key[memory.key]
                            existing.value = memory.value
                            existing.content = memory.content
                            existing.importance = max(existing.importance, memory.importance)
                            updated_count += 1
                        else:
                            # In replace mode, still track as added
                            self._memories.append(memory)
                            if memory.key:
                                self._index_by_key[memory.key] = memory
                            added_count += 1
                    else:
                        # Add new memory
                        self._memories.append(memory)
                        if memory.key:
                            self._index_by_key[memory.key] = memory
                        added_count += 1

                except Exception as e:
                    print(f"Error importing memory: {e}")
                    skipped_count += 1
                    continue

            self.save()

            return {
                "success": True,
                "added": added_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "total": added_count + updated_count,
                "source_version": source_version,
                "source_date": source_date,
            }

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON: {str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_shared_memories(self) -> List[Memory]:
        """Get memories that are shared across all companions."""
        return [m for m in self._memories if m.is_shared]

    def get_companion_specific_memories(self, companion_id: str) -> List[Memory]:
        """Get memories specific to a companion."""
        return [
            m for m in self._memories
            if m.companion_id == companion_id and not m.is_shared
        ]

    def get_memories_for_companion(self, companion_id: str) -> List[Memory]:
        """
        Get all relevant memories for a specific companion.
        Includes shared memories + companion-specific memories.
        """
        # Get shared memories
        shared = [m for m in self._memories if m.is_shared]

        # Get companion-specific memories
        specific = [m for m in self._memories if m.companion_id == companion_id and not m.is_shared]

        # Combine (shared first, then specific)
        return shared + specific
