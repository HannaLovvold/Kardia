"""
Main GTK4 application window for Kardia.

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

Part of the Kardia AI Companion application.
"""
import gi
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

from companion_data.models import Companion
from companion_selector import CompanionSelector
from chat_view import ChatView
from settings_dialog import SettingsDialog
from user_profile_dialog import UserProfileDialog


class MainWindow(Adw.ApplicationWindow):
    """Main GTK4 application window for Kardia."""

    def __init__(self, app):
        """Initialize the main window."""
        super().__init__(application=app)

        self.set_title("Kardia")
        self.set_default_size(1000, 700)

        self.app = app

        # Create toast overlay
        self.toast_overlay = Adw.ToastOverlay()

        # Create header bar widget (but don't set it as titlebar)
        self.header_bar = Adw.HeaderBar()
        self._setup_header_bar()

        # Create view stack
        self.stack = Adw.ViewStack()
        # Note: ViewStack transitions are handled differently than Gtk.Stack

        # Create companion selector view
        self.companion_selector = CompanionSelector(self)
        self.stack.add_titled(
            self.companion_selector,
            "companion-selection",
            "Select Companion",
        )

        # Create chat view
        self.chat_view = ChatView(self)
        self.stack.add_titled(self.chat_view, "chat", "Chat")

        # Create switcher for navigation
        self.switcher = Adw.ViewSwitcher()
        self.switcher.set_stack(self.stack)
        self.switcher.set_policy(Adw.ViewSwitcherPolicy.NARROW)

        # Main box
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(self.header_bar)
        box.append(self.switcher)
        box.append(self.stack)

        # Set toast overlay content
        self.toast_overlay.set_child(box)
        self.set_content(self.toast_overlay)

        # Load last companion if available
        self._load_last_companion()

    def _setup_header_bar(self):
        """Set up the header bar."""
        # User profile button
        profile_button = Gtk.Button(label="Your Profile")
        profile_button.set_icon_name("avatar-default-symbolic")
        profile_button.connect("clicked", self._on_profile_clicked)

        self.header_bar.pack_end(profile_button)

        # Settings button
        settings_button = Gtk.Button()
        settings_button.set_icon_name("emblem-system-symbolic")
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self._on_settings_clicked)

        self.header_bar.pack_end(settings_button)

    def _on_settings_clicked(self, button):
        """Handle settings button click."""
        from settings_dialog import SettingsDialog
        dialog = SettingsDialog(self, self.app)
        dialog.present()

        # Reload AI backend after settings change
        self.app.reload_backend()

    def _on_profile_clicked(self, button):
        """Handle user profile button click."""
        from user_profile_dialog import UserProfileDialog
        dialog = UserProfileDialog(self, self.app)
        dialog.present()

    def _load_last_companion(self):
        """Load the last used companion."""
        last_id = self.app.config.get("last_companion")
        if last_id:
            preset = self.app.companion_manager.get_preset(last_id)
            if preset:
                companion = self.app.companion_manager.create_companion(last_id)
                if companion:
                    self._start_chat(companion)

    def on_companion_selected(self, companion: Companion):
        """Handle companion selection."""
        self.app.set_current_companion(companion)
        self._start_chat(companion)

    def _start_chat(self, companion: Companion):
        """Start chat with a companion."""
        self.chat_view.set_companion(companion)

        # Load conversation history
        messages = self.app.get_companion_history()
        self.chat_view.load_messages(messages)

        # Switch to chat view
        self.stack.set_visible_child_name("chat")

    def go_to_companion_selection(self):
        """Go back to companion selection."""
        self.stack.set_visible_child_name("companion-selection")

    def send_message(self, message: str):
        """Send a message through the app."""
        self.chat_view.show_user_message(message)

        # Get AI response
        def on_response(response: str):
            GLib.idle_add(self.chat_view.show_companion_message, response)

        self.app.send_message(message, on_response)
