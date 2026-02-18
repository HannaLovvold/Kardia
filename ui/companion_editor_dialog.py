"""
Dialog for creating and editing custom companions (GTK4).

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

Part of the Kardia AI Companion application.
"""
import gi
import uuid

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class CompanionEditorDialog(Adw.Window):
    """Dialog for creating/editing a companion (GTK4)."""

    def __init__(self, parent, app, companion_data=None, parent_selector=None, is_preset=False):
        """Initialize companion editor dialog.

        Args:
            parent: Parent window
            app: Application instance
            companion_data: Existing companion data to edit
            parent_selector: The companion selector widget
            is_preset: Whether the companion being edited is a preset
        """
        super().__init__()
        self.set_default_size(600, 700)
        self.set_title("Create Companion" if not companion_data else "Edit Companion")
        self.set_modal(True)
        self.set_transient_for(parent)

        self.app = app
        self.editing_id = companion_data["id"] if companion_data else None
        self.image_path = companion_data.get("image_path") if companion_data else None
        self.parent_selector = parent_selector
        self.is_preset = is_preset  # Track if editing a preset companion

        # Personality trait checkboxes storage
        self.personality_checkboxes = {}
        self.personality_traits = {
            "Emotional": ["Caring", "Empathetic", "Supportive", "Affectionate", "Protective", "Understanding"],
            "Social": ["Outgoing", "Charismatic", "Playful", "Flirty", "Charming", "Witty"],
            "Intellectual": ["Smart", "Thoughtful", "Creative", "Curious", "Philosophical", "Analytical"],
            "Character": ["Confident", "Adventurous", "Ambitious", "Loyal", "Honest", "Brave"],
            "Style": ["Calm", "Energetic", "Relaxed", "Intense", "Mysterious", "Quirky"],
            "Communication": ["Good listener", "Talkative", "Direct", "Subtle", "Sarcastic", "Sincere"],
        }

        # Store existing questionnaire data if editing
        self.existing_questionnaire_data = companion_data.get("questionnaire_data") if companion_data else None

        # Create content
        self._create_content()

        # Load existing data if editing
        if companion_data:
            self._load_companion_data(companion_data)

    def _create_content(self):
        """Create the dialog content."""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)

        # Info banner for editing presets
        self.preset_info_label = Gtk.Label()
        self.preset_info_label.set_markup(
            "<span foreground='orange'><i>Editing a preset companion will create a custom copy.</i></span>"
        )
        self.preset_info_label.set_wrap(True)
        self.preset_info_label.set_margin_bottom(10)
        self.preset_info_label.set_visible(False)  # Hidden by default
        main_box.append(self.preset_info_label)

        # Scrolled window for content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scroll.set_child(content_box)

        # Create form sections
        self._create_basic_fields(content_box)
        self._create_personality_section(content_box)
        self._create_details_section(content_box)

        main_box.append(scroll)

        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(10)
        button_box.set_halign(Gtk.Align.END)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: self.close())
        button_box.append(cancel_button)

        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self._on_save_clicked)
        button_box.append(save_button)

        main_box.append(button_box)
        self.set_content(main_box)

    def _create_basic_fields(self, parent):
        """Create basic form fields."""
        group = Adw.PreferencesGroup()
        group.set_title("Basic Information")

        # Name
        self.name_entry = Adw.EntryRow()
        self.name_entry.set_title("Name")
        group.add(self.name_entry)

        # Gender
        gender_list = Gtk.StringList()
        for gender in ["Female", "Male", "Non-Binary", "Genderfluid", "Transgender Woman", "Transgender Man", "Agender", "Bigender", "Other"]:
            gender_list.append(gender)

        self.gender_combo = Adw.ComboRow()
        self.gender_combo.set_title("Gender")
        self.gender_combo.set_model(gender_list)
        self.gender_combo.set_selected(0)
        group.add(self.gender_combo)

        # Pronouns
        self.pronouns_entry = Adw.EntryRow()
        self.pronouns_entry.set_title("Pronouns (optional)")
        group.add(self.pronouns_entry)

        parent.append(group)

    def _create_personality_section(self, parent):
        """Create personality traits section."""
        group = Adw.PreferencesGroup()
        group.set_title("Personality Traits")

        # Quick-select presets
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.personality_presets = {
            "Romantic": ["Caring", "Affectionate", "Supportive", "Charming", "Playful"],
            "Best Friend": ["Caring", "Empathetic", "Outgoing", "Witty", "Loyal", "Good listener"],
            "Mentor": ["Smart", "Thoughtful", "Supportive", "Understanding", "Good listener", "Sincere"],
            "Adventurer": ["Adventurous", "Energetic", "Confident", "Brave", "Charismatic"],
            "Artist": ["Creative", "Curious", "Quirky", "Thoughtful", "Sincere"],
            "Professional": ["Smart", "Ambitious", "Confident", "Direct", "Analytical"],
        }

        for preset_name, traits in self.personality_presets.items():
            preset_button = Gtk.Button(label=preset_name)
            preset_button.connect("clicked", self._on_preset_clicked, traits)
            preset_box.append(preset_button)

        clear_button = Gtk.Button(label="Clear All")
        clear_button.connect("clicked", self._on_clear_traits)
        preset_box.append(clear_button)

        # Add preset buttons to a row
        parent.append(preset_box)

        # Create trait categories with trait chips
        for category, traits in self.personality_traits.items():
            # Create an expander row for each category
            expander = Adw.ExpanderRow()
            expander.set_title(category)

            # Create a flow box for trait chips
            flow_box = Gtk.FlowBox()
            flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
            flow_box.set_homogeneous(True)
            flow_box.set_margin_start(10)
            flow_box.set_margin_end(10)
            flow_box.set_margin_top(5)
            flow_box.set_margin_bottom(5)

            # Add traits as toggle buttons (chips)
            for trait in traits:
                toggle_button = Gtk.ToggleButton(label=trait)
                toggle_button.add_css_class("trait-chip")
                toggle_button.connect("toggled", self._on_trait_toggled, trait)
                self.personality_checkboxes[trait] = toggle_button
                flow_box.append(toggle_button)

            expander.add_action(flow_box)
            group.add(expander)

        parent.append(group)

        # Additional personality details
        details_group = Adw.PreferencesGroup()
        details_group.set_title("Additional Details")

        # Additional personality text area
        self.personality_entry = Adw.EntryRow()
        self.personality_entry.set_title("Additional Personality Details")
        details_group.add(self.personality_entry)

        # Interests
        self.interests_entry = Adw.EntryRow()
        self.interests_entry.set_title("Interests")
        details_group.add(self.interests_entry)

        parent.append(details_group)

        # Add Personality Questionnaire button
        questionnaire_group = Adw.PreferencesGroup()
        questionnaire_group.set_title("AI Personality Profile")

        questionnaire_button = Gtk.Button(label="Generate Personality Profile")
        questionnaire_button.add_css_class("suggested-action")
        questionnaire_button.connect("clicked", self._on_questionnaire_clicked)
        questionnaire_group.add(questionnaire_button)

        self.questionnaire_status = Gtk.Label()
        self.questionnaire_status.set_markup("<small>Generate a detailed 50-question personality profile based on traits.</small>")
        self.questionnaire_status.set_wrap(True)
        questionnaire_group.add(self.questionnaire_status)

        parent.append(questionnaire_group)

    def _on_trait_toggled(self, button, trait):
        """Handle trait chip toggle - update styling."""
        if button.get_active():
            button.add_css_class("selected")
        else:
            button.remove_css_class("selected")

    def _on_preset_clicked(self, button, traits):
        """Handle preset button click - select those traits."""
        # First clear all
        self._on_clear_traits(button)

        # Then select the preset traits
        for trait in traits:
            if trait in self.personality_checkboxes:
                toggle_button = self.personality_checkboxes[trait]
                toggle_button.set_active(True)
                toggle_button.add_css_class("selected")

    def _on_clear_traits(self, button):
        """Clear all personality trait selections."""
        for toggle_button in self.personality_checkboxes.values():
            toggle_button.set_active(False)
            toggle_button.remove_css_class("selected")

    def _get_partial_companion_data(self) -> dict:
        """Get current companion data from the form (may be incomplete)."""
        # Get selected traits
        selected_traits = []
        for trait, checkbox in self.personality_checkboxes.items():
            if checkbox.get_active():
                selected_traits.append(trait.lower())

        # Get interests
        interests_text = self.interests_entry.get_text().strip()
        interests = [i.strip() for i in interests_text.split(",")] if interests_text else []

        return {
            "name": self.name_entry.get_text().strip() or "Companion",
            "gender": self.gender_combo.get_selected_item().get_string() if self.gender_combo.get_selected_item() else "Female",
            "pronouns": self.pronouns_entry.get_text().strip(),
            "personality": self.personality_entry.get_text().strip(),
            "personality_traits": selected_traits,
            "interests": interests,
            "tone": self.tone_combo.get_selected_item().get_string() if self.tone_combo.get_selected_item() else "Warm and affectionate",
            "relationship_goal": self.goal_combo.get_selected_item().get_string() if self.goal_combo.get_selected_item() else "Being a supportive friend",
            "background": self.background_entry.get_text().strip(),
            "greeting": self.greeting_entry.get_text().strip(),
        }

    def _on_questionnaire_clicked(self, button):
        """Handle questionnaire button click - open the questionnaire dialog."""
        # Get current companion data from form (may be partial)
        current_data = self._get_partial_companion_data()

        # Import here to avoid circular import
        from personality_questionnaire_dialog import PersonalityQuestionnaireDialog

        # Create and show the questionnaire dialog
        dialog = PersonalityQuestionnaireDialog(
            parent=self,
            ai_backend=self.app.ai_backend,
            companion_data=current_data,
            callback=self._on_questionnaire_complete
        )
        dialog.present()

    def _on_questionnaire_complete(self, formatted_text: str):
        """Callback when questionnaire is complete - add to personality field."""
        # Get current personality text
        current_personality = self.personality_entry.get_text().strip()

        # Append the questionnaire results
        if current_personality:
            new_personality = current_personality + "\n\n" + formatted_text
        else:
            new_personality = formatted_text

        self.personality_entry.set_text(new_personality)

        # Update status
        self.questionnaire_status.set_markup(
            "<span foreground='green'><small>✓ Personality profile generated and added!</small></span>"
        )

    def _create_details_section(self, parent):
        """Create additional details section."""
        group = Adw.PreferencesGroup()
        group.set_title("Details")

        # Greeting
        self.greeting_entry = Adw.EntryRow()
        self.greeting_entry.set_title("Greeting Message")
        group.add(self.greeting_entry)

        # Relationship goal
        goal_list = Gtk.StringList()
        for goal in ["Being a supportive friend", "Romantic relationship", "Emotional support",
                     "Casual chatting", "Deep conversations", "Life advice"]:
            goal_list.append(goal)

        self.goal_combo = Adw.ComboRow()
        self.goal_combo.set_title("Relationship Goal")
        self.goal_combo.set_model(goal_list)
        self.goal_combo.set_selected(0)
        group.add(self.goal_combo)

        # Tone
        tone_list = Gtk.StringList()
        for tone in ["Warm and affectionate", "Playful and flirty", "Calm and supportive",
                     "Energetic and enthusiastic", "Intellectual and thoughtful", "Casual and relaxed"]:
            tone_list.append(tone)

        self.tone_combo = Adw.ComboRow()
        self.tone_combo.set_title("Communication Tone")
        self.tone_combo.set_model(tone_list)
        self.tone_combo.set_selected(0)
        group.add(self.tone_combo)

        # Background
        self.background_entry = Adw.EntryRow()
        self.background_entry.set_title("Background Story")
        group.add(self.background_entry)

        parent.append(group)

    def _load_companion_data(self, data):
        """Load existing companion data for editing."""
        self.name_entry.set_text(data.get("name", ""))

        # Set gender
        gender = data.get("gender", "")
        gender_options = ["Female", "Male", "Non-Binary", "Genderfluid", "Transgender Woman",
                         "Transgender Man", "Agender", "Bigender", "Other"]
        if gender in gender_options:
            self.gender_combo.set_selected(gender_options.index(gender))

        # Pronouns
        if "pronouns" in data:
            self.pronouns_entry.set_text(data["pronouns"])

        # Personality
        if "personality" in data:
            self.personality_entry.set_text(data["personality"])

        # Interests
        if "interests" in data:
            self.interests_entry.set_text(", ".join(data["interests"]))

        # Greeting
        if "greeting" in data:
            self.greeting_entry.set_text(data["greeting"])

        # Relationship goal
        goal = data.get("relationship_goal", "")
        goal_options = ["Being a supportive friend", "Romantic relationship", "Emotional support",
                        "Casual chatting", "Deep conversations", "Life advice"]
        if goal in goal_options:
            self.goal_combo.set_selected(goal_options.index(goal))

        # Tone
        tone = data.get("tone", "")
        tone_options = ["Warm and affectionate", "Playful and flirty", "Calm and supportive",
                        "Energetic and enthusiastic", "Intellectual and thoughtful", "Casual and relaxed"]
        if tone in tone_options:
            self.tone_combo.set_selected(tone_options.index(tone))

        # Background
        if "background" in data:
            self.background_entry.set_text(data["background"])

        # Show preset info banner if editing a preset
        if self.is_preset:
            self.preset_info_label.set_visible(True)

    def _on_save_clicked(self, button):
        """Handle save button click."""
        companion_data = self.get_companion_data()

        # If editing a preset, convert it to a custom companion
        if self.is_preset:
            # Create a new custom ID
            original_id = self.editing_id
            name = self.name_entry.get_text().strip().lower().replace(" ", "_")
            companion_data["id"] = f"custom_{name}_{uuid.uuid4().hex[:8]}"
            companion_data["original_preset_id"] = original_id

            # Optionally hide the original preset
            # self.app.companion_manager._hide_preset(original_id)

        self.app.companion_manager.save_custom(companion_data)

        # Reload companions in selector
        if self.parent_selector:
            self.parent_selector._load_companions()

        # Close dialog
        self.close()

    def get_companion_data(self):
        """Get the companion data from the form."""
        # Generate ID if new
        if self.editing_id:
            companion_id = self.editing_id
        else:
            # Generate from name
            name = self.name_entry.get_text().strip().lower().replace(" ", "_")
            companion_id = f"custom_{name}_{uuid.uuid4().hex[:8]}"

        # Get interests
        interests_text = self.interests_entry.get_text().strip()
        interests = [i.strip() for i in interests_text.split(",")] if interests_text else []

        # Build personality from selected traits
        selected_traits = []
        for trait, checkbox in self.personality_checkboxes.items():
            if checkbox.get_active():
                selected_traits.append(trait.lower())

        # Get custom personality text
        custom_personality = self.personality_entry.get_text().strip()

        # Combine traits and custom text
        personality_parts = []
        if selected_traits:
            # Capitalize first letter of each trait
            traits_formatted = ", ".join([t.capitalize() for t in selected_traits])
            personality_parts.append(f"{self.name_entry.get_text().strip()} is {traits_formatted}.")
        if custom_personality:
            personality_parts.append(custom_personality)

        personality = " ".join(personality_parts) if personality_parts else "A friendly and supportive companion."

        return {
            "id": companion_id,
            "name": self.name_entry.get_text().strip(),
            "gender": self.gender_combo.get_selected_item().get_string(),
            "pronouns": self.pronouns_entry.get_text().strip(),
            "personality": personality,
            "interests": interests,
            "greeting": self.greeting_entry.get_text().strip(),
            "relationship_goal": self.goal_combo.get_selected_item().get_string(),
            "tone": self.tone_combo.get_selected_item().get_string(),
            "background": self.background_entry.get_text().strip(),
            "image_path": self.image_path,
        }
