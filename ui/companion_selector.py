"""
Companion selection screen (GTK4).

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

Part of the Kardia AI Companion application.
"""
import gi
import random

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib, Pango, GdkPixbuf

from companion_data.models import Companion


class CompanionSelector(Gtk.Box):
    """Companion selection widget (GTK4)."""

    def __init__(self, main_window):
        """Initialize companion selector."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_window = main_window

        self._create_ui()
        self._load_companions()

    def _create_ui(self):
        """Create the UI."""
        # Title
        title = Gtk.Label()
        title.set_markup("<big><b>Choose Your AI Companion</b></big>")
        title.set_margin_top(20)
        title.set_margin_bottom(10)
        title.set_halign(Gtk.Align.START)
        self.append(title)

        # Subtitle
        subtitle = Gtk.Label()
        subtitle.set_markup(
            "<small>Select a companion to start chatting. Each companion has a unique personality.</small>"
        )
        subtitle.set_margin_bottom(20)
        subtitle.set_halign(Gtk.Align.START)
        self.append(subtitle)

        # Filter buttons
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        filter_box.set_margin_bottom(10)
        self.append(filter_box)

        filters = [
            ("All", None),
            ("Girlfriends", "female"),
            ("Boyfriends", "male"),
            ("Non-Binary", "non-binary"),
            ("Transgender", "transgender"),
        ]

        for label, filter_type in filters:
            button = Gtk.Button(label=label)
            button.connect("clicked", self._on_filter_clicked, filter_type)
            filter_box.append(button)

        # Create companion button
        create_button = Gtk.Button(label="+ Create Companion")
        create_button.add_css_class("suggested-action")
        create_button.connect("clicked", self._on_create_companion)
        filter_box.append(create_button)

        # Scrolled window for companions
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        # Clamp to constrain max width
        clamp = Adw.Clamp()
        clamp.set_maximum_size(800)
        clamp.set_tightening_threshold(600)

        # Companion list
        self.companion_list = Gtk.ListBox()
        self.companion_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.companion_list.set_margin_top(10)
        self.companion_list.set_margin_bottom(10)
        self.companion_list.add_css_class("boxed-list")

        clamp.set_child(self.companion_list)
        scroll.set_child(clamp)
        self.append(scroll)

    def _load_companions(self, filter_type=None):
        """Load companions into the list."""
        # Clear existing
        child = self.companion_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.companion_list.remove(child)
            child = next_child

        # Get companions
        if filter_type:
            companions = self.main_window.app.companion_manager.filter_companions(
                gender=filter_type
            )
        else:
            companions = self.main_window.app.companion_manager.get_all_companions()

        # Add each companion
        for companion_data in companions:
            row = self._create_companion_row(companion_data)
            self.companion_list.append(row)

    def _create_companion_row(self, companion_data: dict) -> Gtk.ListBoxRow:
        """Create a row for a companion."""
        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        row.add_css_class("card")

        # Main box
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        box.set_margin_start(15)
        box.set_margin_end(15)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        # Avatar with initial or image
        avatar = self._create_companion_avatar(companion_data)
        box.append(avatar)

        # Info section
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_hexpand(True)

        # Name and gender
        name_markup = f"<b>{companion_data['name']}</b> ({companion_data['gender']})"
        name_label = Gtk.Label()
        name_label.set_markup(name_markup)
        name_label.set_halign(Gtk.Align.START)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        info_box.append(name_label)

        # Personality preview
        personality_text = companion_data["personality"][:80] + "..."
        personality_label = Gtk.Label(label=personality_text)
        personality_label.set_halign(Gtk.Align.START)
        personality_label.set_ellipsize(Pango.EllipsizeMode.END)
        personality_label.add_css_class("dim-label")
        info_box.append(personality_label)

        # Interests as tags
        interests_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        for interest in companion_data["interests"][:3]:
            tag = Gtk.Label(label=interest)
            tag.add_css_class("tag")
            interests_box.append(tag)

        info_box.append(interests_box)
        box.append(info_box)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Select button
        select_button = Gtk.Button(label="Chat")
        select_button.add_css_class("suggested-action")
        select_button.connect("clicked", self._on_companion_selected, companion_data["id"])
        button_box.append(select_button)

        # Edit button (for all companions)
        edit_button = Gtk.Button(label="Edit")
        edit_button.connect("clicked", self._on_edit_companion, companion_data["id"])
        button_box.append(edit_button)

        # Delete button (for all companions)
        delete_button = Gtk.Button(label="Delete")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", self._on_delete_companion, companion_data["id"], companion_data["name"])
        button_box.append(delete_button)

        box.append(button_box)
        row.set_child(box)

        return row

    def _create_avatar(self, name: str) -> Gtk.Image:
        """Create a colored avatar with the name's initial."""
        # Get first letter
        initial = name[0].upper() if name else "?"

        # For simplicity, use a label with colored background
        avatar = Gtk.Label()
        avatar.set_label(initial)
        avatar.set_width_chars(3)
        avatar.add_css_class("avatar")

        return avatar

    def _create_companion_avatar(self, companion_data: dict):
        """Create an avatar for a companion, using image if available."""
        # Check if companion has an image
        if "image_path" in companion_data and companion_data["image_path"]:
            try:
                # Use Gtk.Picture for better image handling
                picture = Gtk.Picture.new_for_filename(companion_data["image_path"])
                picture.set_size_request(48, 48)
                picture.set_can_shrink(False)
                picture.add_css_class("avatar-picture")
                return picture
            except Exception as e:
                print(f"Error loading companion image for {companion_data.get('name')}: {e}")

        # Fall back to text avatar
        return self._create_avatar(companion_data["name"])

    def _on_filter_clicked(self, button, filter_type):
        """Handle filter button click."""
        self._load_companions(filter_type)

    def _on_create_companion(self, button):
        """Handle create companion button click."""
        from companion_editor_dialog import CompanionEditorDialog

        dialog = CompanionEditorDialog(self.main_window, self.main_window.app, parent_selector=self)
        dialog.present()

    def _on_edit_companion(self, button, companion_id: str):
        """Handle edit companion button click."""
        from companion_editor_dialog import CompanionEditorDialog

        # Get companion data - check both custom and preset
        companion_data = self.main_window.app.companion_manager.get_custom(companion_id)
        is_preset = False

        if not companion_data:
            companion_data = self.main_window.app.companion_manager.get_preset(companion_id)
            is_preset = True

        if not companion_data:
            return

        dialog = CompanionEditorDialog(
            self.main_window,
            self.main_window.app,
            companion_data,
            parent_selector=self,
            is_preset=is_preset
        )
        dialog.present()

    def _on_delete_companion(self, button, companion_id: str, companion_name: str):
        """Handle delete companion button click."""
        # Delete the companion (works for both custom and preset)
        self.main_window.app.companion_manager.delete_companion(companion_id)

        # Reload companions
        self._load_companions()

        # Show toast notification
        toast = Adw.Toast(title=f"'{companion_name}' deleted")
        self.main_window.toast_overlay.add_toast(toast)

    def _on_companion_selected(self, button, companion_id: str):
        """Handle companion selection."""
        companion = self.main_window.app.companion_manager.create_companion(
            companion_id
        )
        if companion:
            self.main_window.on_companion_selected(companion)
