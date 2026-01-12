"""
Settings dialog (GTK4).

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

Part of the Kardia AI Companion application.
"""
import gi
from datetime import datetime
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango


class SettingsDialog(Adw.PreferencesWindow):
    """Settings dialog (GTK4)."""

    def __init__(self, parent, app):
        """Initialize settings dialog."""
        super().__init__()
        self.set_transient_for(parent)
        self.set_default_size(700, 600)
        self.set_title("Settings")

        self.app = app

        # Create pages
        self._create_ai_backend_page()
        self._create_twilio_page()
        self._create_memory_page()

    def _create_ai_backend_page(self):
        """Create AI backend settings page."""
        page = Adw.PreferencesPage()
        page.set_title("AI Backend")
        page.set_icon_name("emblem-system-symbolic")

        # Backend type group
        group = Adw.PreferencesGroup()
        group.set_title("Backend Type")

        # Backend type dropdown
        row = Adw.ComboRow()
        row.set_title("Backend")
        backend_list = Gtk.StringList()
        for backend in ["Ollama", "OpenAI", "Groq", "DeepSeek", "Together AI", "OpenRouter", "Custom"]:
            backend_list.append(backend)
        row.set_model(backend_list)

        # Set current backend
        current_backend = self.app.config.get("ai_backend", "ollama")
        backend_map = {
            "ollama": 0, "openai": 1, "groq": 2, "deepseek": 3,
            "together": 4, "openrouter": 5, "custom": 6
        }
        row.set_selected(backend_map.get(current_backend.lower(), 0))

        row.connect("notify::selected", self._on_backend_changed)
        group.add(row)
        page.add(group)

        # Ollama settings
        self.ollama_group = Adw.PreferencesGroup()
        self.ollama_group.set_title("Ollama Settings")

        ollama_url_row = Adw.EntryRow()
        ollama_url_row.set_title("Ollama URL")
        ollama_url_row.set_text(self.app.config.get("ollama_url", "http://localhost:11434"))
        ollama_url_row.connect("changed", self._on_ollama_url_changed)
        self.ollama_group.add(ollama_url_row)

        ollama_model_row = Adw.EntryRow()
        ollama_model_row.set_title("Model")
        ollama_model_row.set_text(self.app.config.get("ollama_model", "mistral"))
        ollama_model_row.connect("changed", self._on_ollama_model_changed)
        self.ollama_group.add(ollama_model_row)

        page.add(self.ollama_group)

        # API settings
        self.api_group = Adw.PreferencesGroup()
        self.api_group.set_title("API Settings")

        # Store references to API rows
        self.api_key_row = Adw.PasswordEntryRow()
        self.api_key_row.set_title("API Key")
        self.api_key_row.set_text(self.app.config.get("api_key", ""))
        self.api_key_row.connect("changed", self._on_api_key_changed)
        self.api_group.add(self.api_key_row)

        self.api_url_row = Adw.EntryRow()
        self.api_url_row.set_title("API URL")
        self.api_url_row.set_text(self.app.config.get("api_url", "https://api.openai.com/v1"))
        self.api_url_row.connect("changed", self._on_api_url_changed)
        self.api_group.add(self.api_url_row)

        self.api_model_row = Adw.EntryRow()
        self.api_model_row.set_title("Model")
        self.api_model_row.set_text(self.app.config.get("api_model", "gpt-3.5-turbo"))
        self.api_model_row.connect("changed", self._on_api_model_changed)
        self.api_group.add(self.api_model_row)

        # Additional parameters (JSON format)
        self.api_params_row = Adw.EntryRow()
        self.api_params_row.set_title("Additional Parameters (JSON)")
        default_params = '{"thinking": {"type": "enabled", "clear_thinking": "true"}, "do_sample": "true"}'
        self.api_params_row.set_text(self.app.config.get("api_params", default_params))
        self.api_params_row.connect("changed", self._on_api_params_changed)
        self.api_group.add(self.api_params_row)

        # Info text for additional parameters
        params_info = Gtk.Label()
        params_info.set_markup(
            '<small>Optional: Add extra JSON parameters to include in the API request body.\n'
            'Example: {"temperature": 0.7, "max_tokens": 1000}</small>'
        )
        params_info.set_halign(Gtk.Align.START)
        params_info.set_margin_start(10)
        params_info.set_margin_end(10)
        params_info.add_css_class("dim-label")
        self.api_group.add(params_info)

        page.add(self.api_group)

        # Quick setup provider buttons
        quick_setup_group = Adw.PreferencesGroup()
        quick_setup_group.set_title("Quick Setup")

        # Provider buttons
        providers = [
            ("OpenAI (gpt-3.5-turbo)", "https://api.openai.com/v1", "gpt-3.5-turbo", "$"),
            ("Groq (llama-3.3-70b)", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "FREE"),
            ("DeepSeek (deepseek-chat)", "https://api.deepseek.com/v1", "deepseek-chat", "FREE"),
            ("Together (Llama 3 70B)", "https://api.together.xyz/v1", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "FREE"),
        ]

        for name, url, model, price in providers:
            provider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            name_label = Gtk.Label()
            name_label.set_markup(f"<b>{name}</b>")
            name_label.set_halign(Gtk.Align.START)
            name_label.set_hexpand(True)
            provider_box.append(name_label)

            price_label = Gtk.Label()
            price_label.set_markup(f'<span foreground="{"green" if price == "FREE" else "orange"}">{price}</span>')
            provider_box.append(price_label)

            use_button = Gtk.Button(label="Use")
            use_button.connect("clicked", self._on_use_provider, url, model)
            provider_box.append(use_button)

            # Add the box to the group
            quick_setup_group.add(provider_box)

        page.add(quick_setup_group)

        # Show/hide groups based on current backend
        self._update_backend_settings(current_backend)

        self.add(page)

    def _create_twilio_page(self):
        """Create Twilio SMS settings page."""
        page = Adw.PreferencesPage()
        page.set_title("Twilio")
        page.set_icon_name("sms-symbolic")

        # Info group
        info_group = Adw.PreferencesGroup()
        info_group.set_title("Twilio SMS Settings")

        info_label = Gtk.Label()
        info_label.set_markup(
            "<small>Configure Twilio credentials in .env file:\n"
            "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,\n"
            "TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER</small>"
        )
        info_label.set_halign(Gtk.Align.START)
        info_label.set_margin_start(10)
        info_label.set_margin_end(10)
        info_label.set_margin_top(10)
        info_label.set_margin_bottom(10)
        info_group.add(info_label)

        page.add(info_group)

        # Status group
        status_group = Adw.PreferencesGroup()
        status_group.set_title("Configuration Status")

        self.twilio_status_label = Gtk.Label()
        self.twilio_status_label.set_halign(Gtk.Align.START)
        self.twilio_status_label.set_margin_start(10)
        self.twilio_status_label.set_margin_end(10)
        self.twilio_status_label.set_margin_top(10)
        self.twilio_status_label.set_margin_bottom(10)
        status_group.add(self.twilio_status_label)

        test_button = Gtk.Button(label="Test Connection")
        test_button.connect("clicked", self._on_test_twilio)
        status_group.add(test_button)

        page.add(status_group)

        # Test message group
        test_msg_group = Adw.PreferencesGroup()
        test_msg_group.set_title("Send Test Message")

        test_entry = Gtk.Entry()
        test_entry.set_placeholder_text("Test message...")
        test_entry.set_vexpand(True)
        test_msg_group.add(test_entry)

        send_test_button = Gtk.Button(label="Send Test SMS")
        send_test_button.add_css_class("suggested-action")
        send_test_button.connect("clicked", self._on_send_test_sms, test_entry)
        test_msg_group.add(send_test_button)

        page.add(test_msg_group)

        self.add(page)

        # Check status initially
        self._on_test_twilio(None)

    def _on_test_twilio(self, button):
        """Test Twilio connection."""
        status = self.app.sms_integration.get_configuration_status()

        messages = []
        if status["account_sid_configured"]:
            messages.append('<span foreground="green">✓ Account SID configured</span>')
        else:
            messages.append('<span foreground="red">✗ Account SID not configured</span>')

        if status["auth_token_configured"]:
            messages.append('<span foreground="green">✓ Auth token configured</span>')
        else:
            messages.append('<span foreground="red">✗ Auth token not configured</span>')

        if status["twilio_number_configured"]:
            messages.append('<span foreground="green">✓ Twilio number configured</span>')
        else:
            messages.append('<span foreground="red">✗ Twilio number not configured</span>')

        if status["user_number_configured"]:
            messages.append('<span foreground="green">✓ Your number configured</span>')
        else:
            messages.append('<span foreground="red">✗ Your number not configured</span>')

        if status["fully_configured"]:
            # Test connection
            result = self.app.sms_integration.test_connection()
            if result["success"]:
                messages.append(
                    f'\n<span foreground="green">✓ Connection successful!</span>\n'
                    f'Account: {result.get("friendly_name", "N/A")}'
                )
            else:
                messages.append(
                    f'\n<span foreground="red">✗ Connection failed: {result.get("error", "Unknown error")}</span>'
                )

        self.twilio_status_label.set_markup("\n".join(messages))

    def _on_send_test_sms(self, button, entry):
        """Send test SMS message."""
        message = entry.get_text().strip()
        if not message:
            message = "Test message from AI Companion!"

        result = self.app.sms_integration.send_message(message)

        # Show result dialog
        result_dialog = Adw.Window()
        result_dialog.set_default_size(400, 200)
        result_dialog.set_title("SMS Result" if result["success"] else "SMS Failed")
        result_dialog.set_modal(True)
        result_dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        if result["success"]:
            heading = Gtk.Label()
            heading.set_markup("<b>SMS Sent!</b>")
            box.append(heading)

            label = Gtk.Label(label=f"Message SID: {result.get('message_sid', 'N/A')}")
            box.append(label)
        else:
            heading = Gtk.Label()
            heading.set_markup("<b>Failed to send SMS</b>")
            box.append(heading)

            label = Gtk.Label(label=result.get("error", "Unknown error"))
            label.set_wrap(True)
            box.append(label)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda _: result_dialog.close())
        close_button.set_halign(Gtk.Align.END)
        close_button.set_margin_top(10)
        box.append(close_button)

        result_dialog.set_content(box)
        result_dialog.present()

    def _create_memory_page(self):
        """Create memory settings page."""
        page = Adw.PreferencesPage()
        page.set_title("Memory")
        page.set_icon_name("document-open-recent-symbolic")

        # Memory stats group
        stats_group = Adw.PreferencesGroup()
        stats_group.set_title("Memory Statistics")

        self.memory_stats_label = Gtk.Label()
        self.memory_stats_label.set_halign(Gtk.Align.START)
        self.memory_stats_label.set_margin_start(10)
        self.memory_stats_label.set_margin_end(10)
        self.memory_stats_label.set_margin_top(10)
        self.memory_stats_label.set_margin_bottom(10)
        stats_group.add(self.memory_stats_label)

        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self._on_refresh_memories)
        stats_group.add(refresh_button)

        page.add(stats_group)

        # Recent memories group
        memories_group = Adw.PreferencesGroup()
        memories_group.set_title("Recent Memories")

        # Scrollable list for memories
        memories_scroll = Gtk.ScrolledWindow()
        memories_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        memories_scroll.set_min_content_height(300)

        self.memories_list = Gtk.ListBox()
        self.memories_list.set_selection_mode(Gtk.SelectionMode.NONE)
        memories_scroll.set_child(self.memories_list)

        memories_group.add(memories_scroll)
        page.add(memories_group)

        # Action buttons group
        actions_group = Adw.PreferencesGroup()
        actions_group.set_title("Memory Actions")

        # Search button
        search_button = Gtk.Button(label="Search Memories")
        search_button.connect("clicked", self._on_search_memories)
        actions_group.add(search_button)

        # Add memory button
        add_button = Gtk.Button(label="Add Memory")
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", self._on_add_memory)
        actions_group.add(add_button)

        # Export button
        export_button = Gtk.Button(label="Export Memories")
        export_button.connect("clicked", self._on_export_memories)
        actions_group.add(export_button)

        # Import button
        import_button = Gtk.Button(label="Import Memories")
        import_button.connect("clicked", self._on_import_memories)
        actions_group.add(import_button)

        # Clear all button
        clear_button = Gtk.Button(label="Clear All Memories")
        clear_button.add_css_class("destructive-action")
        clear_button.connect("clicked", self._on_clear_memories)
        actions_group.add(clear_button)

        page.add(actions_group)

        # Auto-save toggle (move to bottom)
        settings_group = Adw.PreferencesGroup()
        settings_group.set_title("Settings")

        auto_save_row = Adw.SwitchRow()
        auto_save_row.set_title("Auto-save Conversations")
        auto_save_row.set_active(self.app.config.get("auto_save_enabled", True))
        auto_save_row.connect("notify::active", self._on_auto_save_toggled)
        settings_group.add(auto_save_row)

        page.add(settings_group)

        self.add(page)

        # Load initial memories
        self._on_refresh_memories(None)

    def _update_backend_settings(self, backend_type):
        """Show/hide backend-specific settings."""
        is_ollama = backend_type.lower() == "ollama"

        if is_ollama:
            self.ollama_group.set_visible(True)
            self.api_group.set_visible(False)
        else:
            self.ollama_group.set_visible(False)
            self.api_group.set_visible(True)

    def _on_backend_changed(self, row, param):
        """Handle backend type change."""
        backends = ["ollama", "openai", "groq", "deepseek", "together", "openrouter", "custom"]
        selected = row.get_selected()
        backend = backends[selected]
        self.app.config.set("ai_backend", backend)
        self._update_backend_settings(backend)

    def _on_use_provider(self, button, url, model):
        """Use a predefined provider configuration."""
        self.api_url_row.set_text(url)
        self.api_model_row.set_text(model)

    def _on_ollama_url_changed(self, row):
        """Handle Ollama URL change."""
        self.app.config.set("ollama_url", row.get_text())

    def _on_ollama_model_changed(self, row):
        """Handle Ollama model change."""
        self.app.config.set("ollama_model", row.get_text())

    def _on_api_key_changed(self, row):
        """Handle API key change."""
        self.app.config.set("api_key", row.get_text())

    def _on_api_url_changed(self, row):
        """Handle API URL change."""
        self.app.config.set("api_url", row.get_text())

    def _on_api_model_changed(self, row):
        """Handle API model change."""
        self.app.config.set("api_model", row.get_text())

    def _on_api_params_changed(self, row):
        """Handle API additional parameters change."""
        self.app.config.set("api_params", row.get_text())

    def _on_auto_save_toggled(self, row, param):
        """Handle auto-save toggle."""
        self.app.config.set("auto_save_enabled", row.get_active())

    def _on_refresh_memories(self, button):
        """Refresh the memories list."""
        # Clear list
        child = self.memories_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.memories_list.remove(child)
            child = next_child

        # Get memories
        memories = self.app.memory_store.get_recent_memories(limit=20)

        # Update stats
        stats = self.app.memory_store.get_stats()
        shared_count = len(self.app.memory_store.get_shared_memories())
        specific_count = stats['total_memories'] - shared_count

        self.memory_stats_label.set_markup(
            f"<b>Total:</b> {stats['total_memories']} | "
            f"<b>Shared:</b> {shared_count} | "
            f"<b>Companion-specific:</b> {specific_count}\n"
            f"<b>Important (3+):</b> {stats['important_count']}"
        )

        # Add memories to list
        for memory in memories:
            row = self._create_memory_row(memory)
            self.memories_list.append(row)

    def _create_memory_row(self, memory):
        """Create a row for a memory."""
        row = Gtk.ListBoxRow()
        row.set_selectable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(5)
        box.set_margin_bottom(5)

        # Type badge
        type_label = Gtk.Label()
        type_label.set_label(memory.memory_type.replace("_", " ").title())
        type_label.add_css_class("tag")
        box.append(type_label)

        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        content_box.set_hexpand(True)

        content_label = Gtk.Label()
        content_text = memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
        content_label.set_label(content_text)
        content_label.set_halign(Gtk.Align.START)
        content_label.set_ellipsize(Pango.EllipsizeMode.END)
        content_box.append(content_label)

        # Details
        detail_parts = []
        if memory.key and memory.value:
            detail_parts.append(f"{memory.key}: {memory.value}")

        if not memory.is_shared:
            detail_parts.append(f"Companion: {memory.companion_id}")

        if detail_parts:
            detail_label = Gtk.Label()
            detail_label.set_markup(f'<small>{" | ".join(detail_parts)}</small>')
            detail_label.set_halign(Gtk.Align.START)
            detail_label.add_css_class("dim-label")
            content_box.append(detail_label)

        box.append(content_box)

        # Shared indicator
        if not memory.is_shared:
            specific_indicator = Gtk.Label()
            specific_indicator.set_label("🔒")
            specific_indicator.set_tooltip_text("Companion-specific memory")
            box.append(specific_indicator)

        # Importance indicator
        importance_label = Gtk.Label()
        importance_stars = "★" * memory.importance + "☆" * (5 - memory.importance)
        importance_label.set_label(importance_stars)
        box.append(importance_label)

        # Delete button
        delete_button = Gtk.Button()
        delete_button.set_icon_name("edit-delete-symbolic")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", self._on_delete_memory, memory.id)
        box.append(delete_button)

        row.set_child(box)
        return row

    def _on_delete_memory(self, button, memory_id):
        """Handle delete memory."""
        self.app.memory_store.delete_memory(memory_id)
        self._on_refresh_memories(None)

    def _on_search_memories(self, button):
        """Handle search memories."""
        dialog = Adw.Window()
        dialog.set_default_size(500, 200)
        dialog.set_title("Search Memories")
        dialog.set_modal(True)
        dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        entry = Gtk.Entry()
        entry.set_placeholder_text("Enter search term...")
        box.append(entry)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.END)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: dialog.close())
        button_box.append(cancel_button)

        search_button = Gtk.Button(label="Search")
        search_button.add_css_class("suggested-action")
        search_button.connect("clicked", self._on_perform_search, entry, dialog)
        button_box.append(search_button)

        box.append(button_box)
        dialog.set_content(box)
        dialog.present()

        # Also search on Enter key
        entry.connect("activate", self._on_perform_search, entry, dialog)

    def _on_perform_search(self, widget, entry, dialog):
        """Perform the search and show results."""
        query = entry.get_text().strip()
        if query:
            dialog.close()
            self._show_search_results(query)

    def _show_search_results(self, query):
        """Show memory search results."""
        memories = self.app.memory_store.search_memories(query)

        results_dialog = Adw.Window()
        results_dialog.set_default_size(600, 400)
        results_dialog.set_title(f"Search Results: {query}")
        results_dialog.set_modal(True)
        results_dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        # Scrollable results
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        results_list = Gtk.ListBox()
        results_list.set_selection_mode(Gtk.SelectionMode.NONE)

        for memory in memories:
            row = self._create_memory_row(memory)
            results_list.append(row)

        scroll.set_child(results_list)
        box.append(scroll)

        # Close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda _: results_dialog.close())
        close_button.set_halign(Gtk.Align.END)
        box.append(close_button)

        results_dialog.set_content(box)
        results_dialog.present()

    def _on_add_memory(self, button):
        """Handle add memory manually."""
        dialog = Adw.Window()
        dialog.set_default_size(500, 600)
        dialog.set_title("Add Memory")
        dialog.set_modal(True)
        dialog.set_transient_for(self)

        # Main box with scroll
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scroll.set_child(box)

        # Type selection
        type_list = Gtk.StringList()
        types = [
            "Personal Info", "Preference", "Life Event", "Emotional State",
            "Interest", "Relationship", "Goal", "Important Fact",
        ]
        for t in types:
            type_list.append(t)

        type_row = Adw.ComboRow()
        type_row.set_title("Memory Type")
        type_row.set_model(type_list)
        type_row.set_selected(0)
        box.append(type_row)

        # Content
        content_row = Adw.EntryRow()
        content_row.set_title("Description")
        content_row.set_placeholder_text("e.g., User's birthday is May 15th")
        box.append(content_row)

        # Key (optional)
        key_row = Adw.EntryRow()
        key_row.set_title("Key (optional)")
        key_row.set_placeholder_text("e.g., birthday")
        box.append(key_row)

        # Value (optional)
        value_row = Adw.EntryRow()
        value_row.set_title("Value (optional)")
        value_row.set_placeholder_text("e.g., May 15th")
        box.append(value_row)

        # Importance
        importance_row = Adw.SpinRow()
        importance_row.set_title("Importance")
        importance_row.set_adjustment(Gtk.Adjustment.new(3, 1, 5, 1, 1, 0))
        box.append(importance_row)

        # Shared checkbox
        shared_row = Adw.SwitchRow()
        shared_row.set_title("Share with all companions")
        shared_row.set_active(True)
        shared_row.set_subtitle("If checked, this memory will be available to all companions")
        box.append(shared_row)

        main_box.append(scroll)

        # Info text
        info_label = Gtk.Label()
        info_label.set_markup(
            "<small>Shared memories: Available to all companions (recommended for personal info)\n"
            "Companion-specific: Only available to this companion (private conversations)</small>"
        )
        info_label.set_halign(Gtk.Align.START)
        info_label.set_margin_bottom(10)
        main_box.append(info_label)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.END)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: dialog.close())
        button_box.append(cancel_button)

        add_button = Gtk.Button(label="Add Memory")
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", self._on_confirm_add_memory, dialog, type_row, content_row,
                          key_row, value_row, importance_row, shared_row)
        button_box.append(add_button)

        main_box.append(button_box)
        dialog.set_content(main_box)
        dialog.present()

    def _on_confirm_add_memory(self, button, dialog, type_row, content_row, key_row,
                               value_row, importance_row, shared_row):
        """Handle confirm add memory."""
        # Get type
        type_index = type_row.get_selected()
        type_item = type_row.get_model().get_string(type_index)
        memory_type = type_item.lower().replace(" ", "_")

        # Get values
        content = content_row.get_text().strip()
        key = key_row.get_text().strip() or None
        value = value_row.get_text().strip() or None
        importance = int(importance_row.get_value())
        is_shared = shared_row.get_active()

        if content:
            self.app.memory_store.add_memory(
                memory_type=memory_type,
                content=content,
                key=key,
                value=value,
                importance=importance,
                companion_id=self.app.current_companion.id if self.app.current_companion else "",
                is_shared=is_shared,
            )
            self._on_refresh_memories(None)
            dialog.close()

    def _on_export_memories(self, button):
        """Handle export memories."""
        dialog = Adw.Window()
        dialog.set_default_size(500, 300)
        dialog.set_title("Export Memories")
        dialog.set_modal(True)
        dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        # Format selection
        format_list = Gtk.StringList()
        format_list.append("JSON")
        format_list.append("Readable Text")

        format_row = Adw.ComboRow()
        format_row.set_title("Export Format")
        format_row.set_model(format_list)
        format_row.set_selected(0)
        box.append(format_row)

        # File entry
        default_name = f"ai_companion_memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        file_row = Adw.EntryRow()
        file_row.set_title("Save to file")
        file_row.set_text(default_name)
        box.append(file_row)

        # Info text
        info_label = Gtk.Label()
        info_label.set_markup(
            "<small>• JSON format: Full backup with all metadata\n"
            "• Text format: Human-readable for review\n\n"
            "Shared memories and companion-specific memories will both be exported.</small>"
        )
        info_label.set_halign(Gtk.Align.START)
        box.append(info_label)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.END)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: dialog.close())
        button_box.append(cancel_button)

        export_button = Gtk.Button(label="Export")
        export_button.add_css_class("suggested-action")
        export_button.connect("clicked", self._on_confirm_export, dialog, format_row, file_row)
        button_box.append(export_button)

        box.append(button_box)
        dialog.set_content(box)
        dialog.present()

    def _on_confirm_export(self, button, dialog, format_row, file_row):
        """Handle confirm export."""
        # Get format
        format_index = format_row.get_selected()
        format_item = format_row.get_model().get_string(format_index)
        export_format = "json" if "JSON" in format_item else "txt"

        # Get filepath
        filepath = file_row.get_text().strip()
        if not filepath.endswith(f".{export_format}"):
            filepath = filepath.rsplit(".", 1)[0] if "." in filepath else filepath
            filepath += f".{export_format}"

        # Export
        result = self.app.memory_store.export_memories(filepath, export_format)

        if result["success"]:
            # Show success toast/dialog
            success_dialog = Adw.MessageDialog()
            success_dialog.set_transient_for(dialog)
            success_dialog.set_heading("Memories Exported!")
            success_dialog.set_body(f"Exported {result['count']} memories to:\n{result['path']}")
            success_dialog.add_response("ok", "OK")
            success_dialog.connect("response", lambda d, _: d.close())
            success_dialog.present()
            dialog.close()
        else:
            # Show error
            error_dialog = Adw.MessageDialog()
            error_dialog.set_transient_for(dialog)
            error_dialog.set_heading("Export Failed")
            error_dialog.set_body(result.get("error", "Unknown error"))
            error_dialog.add_response("ok", "OK")
            error_dialog.connect("response", lambda d, _: d.close())
            error_dialog.present()

    def _on_import_memories(self, button):
        """Handle import memories."""
        # File chooser dialog (using GTK3 blocking dialog for file selection)
        file_chooser = Gtk.FileChooserDialog(
            title="Import Memories",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        file_chooser.add_button("Cancel", Gtk.ResponseType.CANCEL)
        file_chooser.add_button("Import", Gtk.ResponseType.OK)

        # Filter for JSON files
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON Files (*.json)")
        json_filter.add_pattern("*.json")
        file_chooser.add_filter(json_filter)

        # All files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        file_chooser.add_filter(all_filter)

        response = file_chooser.run()
        filepath = None
        if response == Gtk.ResponseType.OK:
            filepath = file_chooser.get_file().get_path()

        file_chooser.destroy()

        if not filepath:
            return

        # Ask about merge vs replace using dialog window
        merge_dialog = Adw.Window()
        merge_dialog.set_default_size(400, 200)
        merge_dialog.set_title("Import Memories")
        merge_dialog.set_modal(True)
        merge_dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        label = Gtk.Label()
        label.set_markup("<b>Do you want to merge with existing memories or replace all memories?</b>")
        label.set_wrap(True)
        box.append(label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(10)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: merge_dialog.close())
        button_box.append(cancel_button)

        merge_button = Gtk.Button(label="Merge")
        merge_button.add_css_class("suggested-action")
        merge_button.connect("clicked", self._on_import_merge, filepath, merge_dialog)
        button_box.append(merge_button)

        replace_button = Gtk.Button(label="Replace All")
        replace_button.add_css_class("destructive-action")
        replace_button.connect("clicked", self._on_import_replace, filepath, merge_dialog)
        button_box.append(replace_button)

        box.append(button_box)
        merge_dialog.set_content(box)
        merge_dialog.present()

    def _on_import_merge(self, button, filepath, dialog):
        """Handle import with merge."""
        dialog.close()
        self._perform_import(filepath, clear_first=False)

    def _on_import_replace(self, button, filepath, dialog):
        """Handle import with replace."""
        dialog.close()

        # Confirm replace
        confirm_dialog = Adw.Window()
        confirm_dialog.set_default_size(400, 200)
        confirm_dialog.set_title("Confirm Replace")
        confirm_dialog.set_modal(True)
        confirm_dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        label = Gtk.Label()
        label.set_markup("<b>This will delete all existing memories before importing.\nThis action cannot be undone.</b>")
        label.set_wrap(True)
        box.append(label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(10)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: confirm_dialog.close())
        button_box.append(cancel_button)

        confirm_button = Gtk.Button(label="Replace All")
        confirm_button.add_css_class("destructive-action")
        confirm_button.connect("clicked", self._on_confirm_replace, filepath, confirm_dialog)
        button_box.append(confirm_button)

        box.append(button_box)
        confirm_dialog.set_content(box)
        confirm_dialog.present()

    def _on_confirm_replace(self, button, filepath, dialog):
        """Handle confirm replace."""
        dialog.close()
        self._perform_import(filepath, clear_first=True)

    def _perform_import(self, filepath, clear_first):
        """Perform the actual import."""
        # Clear existing if needed
        if clear_first:
            memories = self.app.memory_store.get_all_memories()
            for memory in memories:
                self.app.memory_store.delete_memory(memory.id)

        # Import
        result = self.app.memory_store.import_memories(filepath, merge=True)

        # Show result dialog
        result_dialog = Adw.Window()
        result_dialog.set_default_size(400, 200)
        result_dialog.set_title("Import Result" if result["success"] else "Import Failed")
        result_dialog.set_modal(True)
        result_dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        if result["success"]:
            heading = Gtk.Label()
            heading.set_markup("<b>Import Complete!</b>")
            box.append(heading)

            summary = f"Added: {result['added']} memories\nUpdated: {result['updated']} memories"
            if result.get('skipped', 0) > 0:
                summary += f"\nSkipped: {result['skipped']} memories"

            label = Gtk.Label(label=summary)
            box.append(label)
        else:
            heading = Gtk.Label()
            heading.set_markup(f"<b>Import Failed</b>")
            box.append(heading)

            label = Gtk.Label(label=result.get("error", "Unknown error"))
            label.set_wrap(True)
            box.append(label)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self._on_import_close)
        close_button.set_halign(Gtk.Align.END)
        close_button.set_margin_top(10)
        box.append(close_button)

        result_dialog.set_content(box)
        result_dialog.present()

    def _on_import_close(self, button):
        """Close import result dialog and refresh."""
        # Find and close the dialog
        dialog = button.get_ancestor(Adw.Window)
        if dialog:
            dialog.close()
        self._on_refresh_memories(None)

    def _on_clear_memories(self, button):
        """Handle clear all memories."""
        # Confirm dialog
        confirm_dialog = Adw.Window()
        confirm_dialog.set_default_size(400, 200)
        confirm_dialog.set_title("Confirm Clear")
        confirm_dialog.set_modal(True)
        confirm_dialog.set_transient_for(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        label = Gtk.Label()
        label.set_markup("<b>This will delete all stored memories.\nYour AI companion will forget everything about you.</b>")
        label.set_wrap(True)
        box.append(label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(10)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: confirm_dialog.close())
        button_box.append(cancel_button)

        clear_button = Gtk.Button(label="Clear All")
        clear_button.add_css_class("destructive-action")
        clear_button.connect("clicked", self._on_confirm_clear, confirm_dialog)
        button_box.append(clear_button)

        box.append(button_box)
        confirm_dialog.set_content(box)
        confirm_dialog.present()

    def _on_confirm_clear(self, button, dialog):
        """Handle confirm clear memories."""
        dialog.close()

        # Delete all memories
        memories = self.app.memory_store.get_all_memories()
        for memory in memories:
            self.app.memory_store.delete_memory(memory.id)

        self._on_refresh_memories(None)
