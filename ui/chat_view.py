"""
Chat view for messaging (GTK4).

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

Part of the Kardia AI Companion application.
"""
import gi
from datetime import datetime

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib, Pango, GdkPixbuf

from companion_data.models import Message


class ChatView(Gtk.Box):
    """Chat view widget (GTK4)."""

    def __init__(self, main_window):
        """Initialize chat view."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_window = main_window
        self.companion = None

        self._create_ui()

    def _create_ui(self):
        """Create the UI."""
        # Back button
        self.back_button = Gtk.Button()
        back_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        back_image = Gtk.Image.new_from_icon_name("go-previous-symbolic")
        back_label = Gtk.Label(label="Change Companion")
        back_box.append(back_image)
        back_box.append(back_label)
        self.back_button.set_child(back_box)
        self.back_button.connect("clicked", self._on_back_clicked)
        self.back_button.set_margin_start(10)
        self.back_button.set_margin_top(10)

        # Companion info bar
        self.info_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.info_bar.set_margin_start(10)
        self.info_bar.set_margin_end(10)
        self.info_bar.set_margin_top(5)
        self.info_bar.set_margin_bottom(5)
        self.info_bar.add_css_class("info-bar")

        # Info label (will be updated when companion is set)
        self.info_label = Gtk.Label()
        self.info_bar.append(self.info_label)

        # Spacer to push delete button to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.info_bar.append(spacer)

        # Delete chat button
        delete_button = Gtk.Button()
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.set_tooltip_text("Delete chat and start fresh")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", self._on_delete_chat)
        self.info_bar.append(delete_button)

        # Messages scroll view
        messages_scroll = Gtk.ScrolledWindow()
        messages_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        messages_scroll.set_vexpand(True)

        # Messages list box
        self.messages_list = Gtk.ListBox()
        self.messages_list.set_selection_mode(Gtk.SelectionMode.NONE)
        messages_scroll.set_child(self.messages_list)

        # Message entry area
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_box.add_css_class("chat-input-area")

        self.message_entry = Gtk.Entry()
        self.message_entry.set_placeholder_text("Type your message...")
        self.message_entry.connect("activate", self._on_send_message)
        self.message_entry.set_hexpand(True)
        self.message_entry.add_css_class("chat-entry")

        send_button = Gtk.Button(label="Send")
        send_button.add_css_class("suggested-action")
        send_button.add_css_class("send-button")
        send_button.set_icon_name("send-to-symbolic")
        send_button.connect("clicked", self._on_send_message)

        entry_box.append(self.message_entry)
        entry_box.append(send_button)

        # SMS toggle
        self.sms_button = Gtk.ToggleButton(label="SMS")
        self.sms_button.set_tooltip_text("Forward messages to your phone")
        self.sms_button.connect("toggled", self._on_sms_toggled)
        entry_box.append(self.sms_button)

        # Pack everything
        self.append(self.back_button)
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self.append(self.info_bar)
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self.append(messages_scroll)
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self.append(entry_box)

    def set_companion(self, companion):
        """Set the current companion."""
        self.companion = companion

        # Update info label
        name_markup = f"<b>{companion.display_name}</b> - {companion.gender}"
        self.info_label.set_markup(name_markup)

        # Load SMS state
        sms_enabled = self.main_window.app.config.get("sms_forwarding_enabled", False)
        self.sms_button.set_active(sms_enabled)

    def load_messages(self, messages):
        """Load conversation messages."""
        # Clear existing
        child = self.messages_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.messages_list.remove(child)
            child = next_child

        # Add messages
        for msg in messages:
            if msg.role == "user":
                self._add_user_message(msg.content)
            else:
                self._add_companion_message(msg.content)

        # Scroll to bottom
        GLib.idle_add(self._scroll_to_bottom)

    def show_user_message(self, content: str):
        """Display a user message."""
        self._add_user_message(content)
        GLib.idle_add(self._scroll_to_bottom)

    def show_companion_message(self, content: str):
        """Display a companion message."""
        self._add_companion_message(content)
        GLib.idle_add(self._scroll_to_bottom)

    def _add_user_message(self, content: str):
        """Add a user message to the chat."""
        row = Gtk.ListBoxRow()
        row.set_selectable(False)

        # Main container that fills the width
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_hexpand(True)

        # Spacer to push message to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        main_box.append(spacer)

        # Message bubble
        frame = Gtk.Frame()
        frame.add_css_class("user-message")
        frame.add_css_class("message-bubble")
        frame.set_valign(Gtk.Align.START)

        label = Gtk.Label(label=content)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(60)
        label.set_xalign(0)

        frame.set_child(label)
        main_box.append(frame)

        # Right margin
        margin = Gtk.Box()
        margin.set_size_request(10, 0)
        main_box.append(margin)

        row.set_child(main_box)
        self.messages_list.append(row)

    def _add_companion_message(self, content: str):
        """Add a companion message to the chat."""
        row = Gtk.ListBoxRow()
        row.set_selectable(False)

        # Main container that fills the width
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_hexpand(True)

        # Left margin
        margin = Gtk.Box()
        margin.set_size_request(10, 0)
        main_box.append(margin)

        # Avatar
        avatar = self._create_companion_avatar()
        avatar.set_valign(Gtk.Align.START)
        main_box.append(avatar)

        # Spacing between avatar and message
        spacing = Gtk.Box()
        spacing.set_size_request(10, 0)
        main_box.append(spacing)

        # Message bubble
        frame = Gtk.Frame()
        frame.add_css_class("companion-message")
        frame.add_css_class("message-bubble")
        frame.set_valign(Gtk.Align.START)

        label = Gtk.Label(label=content)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(60)
        label.set_xalign(0)

        frame.set_child(label)
        main_box.append(frame)

        # Spacer to push remaining content to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        main_box.append(spacer)

        row.set_child(main_box)
        self.messages_list.append(row)

    def _create_companion_avatar(self) -> Gtk.Widget:
        """Create an avatar for the companion, using image if available."""
        # Check if companion has an image
        if self.companion and self.companion.image_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    self.companion.image_path, 32, 32
                )
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                image = Gtk.Image()
                image.set_from_paintable(texture)
                image.set_size_request(32, 32)
                return image
            except Exception as e:
                print(f"Error loading companion image: {e}")

        # Fall back to text avatar
        avatar = Gtk.Label()
        avatar.set_label(self.companion.display_name[0] if self.companion else "?")
        avatar.add_css_class("avatar-small")
        return avatar

    def _scroll_to_bottom(self):
        """Scroll messages view to bottom."""
        adj = self.messages_list.get_adjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def _on_send_message(self, widget):
        """Handle send message button."""
        message = self.message_entry.get_text().strip()
        if not message:
            return

        # Clear entry
        self.message_entry.set_text("")

        # Show message immediately
        self.show_user_message(message)

        # Send through main window
        self.main_window.send_message(message)

    def _on_back_clicked(self, button):
        """Handle back button click."""
        self.main_window.go_to_companion_selection()

    def _on_sms_toggled(self, button):
        """Handle SMS toggle."""
        enabled = button.get_active()
        self.main_window.app.message_forwarder.toggle_sms_forwarding(enabled)
        self.main_window.app.config.set("sms_forwarding_enabled", enabled)

    def _on_delete_chat(self, button):
        """Handle delete chat button click."""
        # Create confirmation dialog
        confirm_dialog = Adw.Window()
        confirm_dialog.set_default_size(400, 200)
        confirm_dialog.set_title("Delete Chat?")
        confirm_dialog.set_modal(True)
        confirm_dialog.set_transient_for(self.get_root())

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        label = Gtk.Label()
        label.set_markup("<b>This will delete all messages in this conversation.\nYou will start fresh with this companion.</b>")
        label.set_wrap(True)
        box.append(label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(10)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: confirm_dialog.close())
        button_box.append(cancel_button)

        delete_button = Gtk.Button(label="Delete Chat")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", self._confirm_delete_chat, confirm_dialog)
        button_box.append(delete_button)

        box.append(button_box)
        confirm_dialog.set_content(box)
        confirm_dialog.present()

    def _confirm_delete_chat(self, button, dialog):
        """Confirm and delete the chat."""
        dialog.close()

        # Delete the conversation
        if self.main_window.app.current_conversation:
            self.main_window.app.storage.delete_conversation(
                self.main_window.app.current_conversation.companion_id
            )

        # Create new conversation
        if self.main_window.app.current_companion:
            self.main_window.app.set_current_companion(self.main_window.app.current_companion)

        # Clear messages from view
        child = self.messages_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.messages_list.remove(child)
            child = next_child

        # Show toast notification
        toast = Adw.Toast(title="Chat deleted - Starting fresh")
        self.main_window.toast_overlay.add_toast(toast)
