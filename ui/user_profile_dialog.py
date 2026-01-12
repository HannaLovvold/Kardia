"""
User profile dialog for entering personal details (GTK4).

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

Part of the Kardia AI Companion application.
"""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class UserProfileDialog(Adw.PreferencesWindow):
    """Dialog for editing user profile (GTK4)."""

    def __init__(self, parent, app):
        """Initialize user profile dialog."""
        super().__init__()
        self.set_transient_for(parent)
        self.set_default_size(500, 600)
        self.set_title("Your Profile")

        self.app = app

        # Create page
        page = Adw.PreferencesPage()

        # Basic info group
        group = Adw.PreferencesGroup()
        group.set_title("Basic Information")

        # Name
        self.name_entry = Adw.EntryRow()
        self.name_entry.set_title("Name")
        group.add(self.name_entry)

        # Birthday
        self.birthday_entry = Adw.EntryRow()
        self.birthday_entry.set_title("Age/Birthday")
        group.add(self.birthday_entry)

        # Location
        self.location_entry = Adw.EntryRow()
        self.location_entry.set_title("Location")
        group.add(self.location_entry)

        # Gender
        self.gender_entry = Adw.EntryRow()
        self.gender_entry.set_title("Gender/Pronouns")
        group.add(self.gender_entry)

        # Occupation
        self.occupation_entry = Adw.EntryRow()
        self.occupation_entry.set_title("Occupation")
        group.add(self.occupation_entry)

        page.add(group)

        # Interests group
        group = Adw.PreferencesGroup()
        group.set_title("Interests & Preferences")

        # Interests
        self.interests_entry = Adw.EntryRow()
        self.interests_entry.set_title("Interests")
        group.add(self.interests_entry)

        # Likes
        self.likes_entry = Adw.EntryRow()
        self.likes_entry.set_title("Likes")
        group.add(self.likes_entry)

        # Dislikes
        self.dislikes_entry = Adw.EntryRow()
        self.dislikes_entry.set_title("Dislikes")
        group.add(self.dislikes_entry)

        page.add(group)

        # Additional info group
        group = Adw.PreferencesGroup()
        group.set_title("Additional Information")

        # Goals
        self.goals_entry = Adw.EntryRow()
        self.goals_entry.set_title("Goals/Aspirations")
        group.add(self.goals_entry)

        # Notes
        self.notes_entry = Adw.EntryRow()
        self.notes_entry.set_title("Additional Notes")
        group.add(self.notes_entry)

        page.add(group)

        # Save button
        save_button = Gtk.Button(label="Save Profile")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self._on_save_clicked)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_margin_top(10)
        button_box.set_margin_bottom(10)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.append(save_button)

        page.add(button_box)

        self.add(page)

        # Load existing profile
        self._load_profile()

    def _load_profile(self):
        """Load existing user profile from memories."""
        memories = self.app.memory_store.get_all_memories()

        # Map memory keys to entry fields
        field_map = {
            "name": self.name_entry,
            "location": self.location_entry,
            "gender": self.gender_entry,
            "occupation": self.occupation_entry,
        }

        for memory in memories:
            if memory.key and memory.key in field_map:
                field_map[memory.key].set_text(memory.value or "")
            elif memory.memory_type == "preference":
                if "love" in memory.content.lower() or "likes" in memory.content.lower():
                    current = self.likes_entry.get_text()
                    if memory.value:
                        self.likes_entry.set_text(f"{current}, {memory.value}" if current else memory.value)
                elif "hate" in memory.content.lower() or "dislikes" in memory.content.lower():
                    current = self.dislikes_entry.get_text()
                    if memory.value:
                        self.dislikes_entry.set_text(f"{current}, {memory.value}" if current else memory.value)
            elif memory.memory_type == "interest":
                interests = self.interests_entry.get_text()
                if memory.value:
                    self.interests_entry.set_text(f"{interests}, {memory.value}" if interests else memory.value)
            elif memory.memory_type == "goal":
                goals = self.goals_entry.get_text()
                if memory.content:
                    self.goals_entry.set_text(f"{goals}, {memory.content}" if goals else memory.content)

    def _on_save_clicked(self, button):
        """Handle save button click."""
        saved_count = self._save_profile()

        # Show toast notification
        toast = Adw.Toast(title=f"Saved {saved_count} memories from your profile.")
        self.toast_overlay.add_toast(toast)

        self.close()

    def _save_profile(self):
        """Save user profile as memories."""
        import uuid

        saved_count = 0

        # Save basic info
        if self.name_entry.get_text().strip():
            self.app.memory_store.add_memory(
                memory_type="personal_info",
                content=f"User's name is {self.name_entry.get_text().strip()}",
                key="name",
                value=self.name_entry.get_text().strip(),
                importance=5,
                companion_id="user_profile",
                is_shared=True,
            )
            saved_count += 1

        if self.birthday_entry.get_text().strip():
            self.app.memory_store.add_memory(
                memory_type="personal_info",
                content=f"User's birthday is {self.birthday_entry.get_text().strip()}",
                key="birthday",
                value=self.birthday_entry.get_text().strip(),
                importance=5,
                companion_id="user_profile",
                is_shared=True,
            )
            saved_count += 1

        if self.location_entry.get_text().strip():
            self.app.memory_store.add_memory(
                memory_type="personal_info",
                content=f"User lives in {self.location_entry.get_text().strip()}",
                key="location",
                value=self.location_entry.get_text().strip(),
                importance=4,
                companion_id="user_profile",
                is_shared=True,
            )
            saved_count += 1

        if self.gender_entry.get_text().strip():
            self.app.memory_store.add_memory(
                memory_type="personal_info",
                content=f"User identifies as: {self.gender_entry.get_text().strip()}",
                key="gender",
                value=self.gender_entry.get_text().strip(),
                importance=4,
                companion_id="user_profile",
                is_shared=True,
            )
            saved_count += 1

        if self.occupation_entry.get_text().strip():
            self.app.memory_store.add_memory(
                memory_type="personal_info",
                content=f"User works as: {self.occupation_entry.get_text().strip()}",
                key="occupation",
                value=self.occupation_entry.get_text().strip(),
                importance=3,
                companion_id="user_profile",
                is_shared=True,
            )
            saved_count += 1

        # Save interests
        if self.interests_entry.get_text().strip():
            interests = [i.strip() for i in self.interests_entry.get_text().split(",")]
            for interest in interests[:10]:
                if interest:
                    self.app.memory_store.add_memory(
                        memory_type="interest",
                        content=f"User is interested in {interest}",
                        key=f"interest_{interest.lower().replace(' ', '_')}",
                        value=interest,
                        importance=3,
                        companion_id="user_profile",
                        is_shared=True,
                    )
                    saved_count += 1

        # Save likes
        if self.likes_entry.get_text().strip():
            likes = [i.strip() for i in self.likes_entry.get_text().split(",")]
            for like in likes[:10]:
                if like:
                    self.app.memory_store.add_memory(
                        memory_type="preference",
                        content=f"User likes {like}",
                        key=f"likes_{like.lower().replace(' ', '_')}",
                        value=like,
                        importance=3,
                        companion_id="user_profile",
                        is_shared=True,
                    )
                    saved_count += 1

        # Save dislikes
        if self.dislikes_entry.get_text().strip():
            dislikes = [i.strip() for i in self.dislikes_entry.get_text().split(",")]
            for dislike in dislikes[:10]:
                if dislike:
                    self.app.memory_store.add_memory(
                        memory_type="preference",
                        content=f"User dislikes {dislike}",
                        key=f"dislikes_{dislike.lower().replace(' ', '_')}",
                        value=dislike,
                        importance=3,
                        companion_id="user_profile",
                        is_shared=True,
                    )
                    saved_count += 1

        # Save goals
        if self.goals_entry.get_text().strip():
            goals = [g.strip() for g in self.goals_entry.get_text().split(",")]
            for goal in goals[:5]:
                if goal:
                    self.app.memory_store.add_memory(
                        memory_type="goal",
                        content=f"User's goal: {goal}",
                        key=f"goal_{goal.lower().replace(' ', '_')}",
                        value=goal,
                        importance=4,
                        companion_id="user_profile",
                        is_shared=True,
                    )
                    saved_count += 1

        # Save notes
        if self.notes_entry.get_text().strip():
            self.app.memory_store.add_memory(
                memory_type="important_fact",
                content=f"About the user: {self.notes_entry.get_text().strip()}",
                importance=3,
                companion_id="user_profile",
                is_shared=True,
            )
            saved_count += 1

        return saved_count
