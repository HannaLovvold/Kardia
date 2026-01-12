#!/usr/bin/env python3
"""
Kardia - AI Companion GTK4 Application

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

A modern GTK4/libadwaita AI companion application with SMS integration,
memory management, and multi-companion support.
"""
import gi
import sys
from pathlib import Path

# Require GTK4 and Adwaita before any imports
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# Add local directories to path for imports
local_ui = Path(__file__).parent / "ui"
if str(local_ui) not in sys.path:
    sys.path.insert(0, str(local_ui))

from gi.repository import Gtk, Adw, Gio, GLib, Gdk

from companion_data.models import CompanionManager, Companion
from ai_backend import OllamaBackend
from openai_backend import OpenAIBackend
from sms_integration import TwilioIntegration, MessageForwarder
from sms_webhook import SMSWebhookServer
from sms_companion_manager import SMSCompanionManager, SMSCommandParser
from storage import ConversationStorage, ConfigManager
from memory import MemoryStore
from memory_extractor import MemoryManager


class KardiaApp(Adw.Application):
    """Kardia - Main GTK4 application class."""

    def __init__(self):
        """Initialize the application."""
        super().__init__(
            application_id="com.kardia.app",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        # Get the project directory
        self.project_dir = Path(__file__).parent

        # Initialize managers
        self.companion_manager = CompanionManager(self.project_dir)
        self.storage = ConversationStorage(self.project_dir / "conversations")
        self.config = ConfigManager(self.project_dir / "config")

        # Initialize AI backends
        self.backend_type = self.config.get("ai_backend", "ollama")

        # Ollama backend
        ollama_model = self.config.get("ollama_model", "mistral")
        ollama_url = self.config.get("ollama_url", "http://localhost:11434")
        self.ollama_backend = OllamaBackend(model_name=ollama_model, base_url=ollama_url)

        # OpenAI backend
        api_key = self.config.get("api_key", "")
        api_url = self.config.get("api_url", "https://api.openai.com/v1")
        api_model = self.config.get("api_model", "gpt-3.5-turbo")
        api_params = self.config.get("api_params", "")
        self.openai_backend = OpenAIBackend(
            api_key=api_key,
            base_url=api_url,
            model=api_model,
            additional_params=api_params if api_params else None,
        ) if api_key else None

        # Set current backend
        self.ai_backend = self._get_current_backend()

        # Initialize SMS
        self.sms_integration = TwilioIntegration()
        self.message_forwarder = MessageForwarder(self.sms_integration)

        # Initialize SMS companion manager for multi-companion support
        self.sms_companion_manager = SMSCompanionManager(self.project_dir / "conversations")
        self.sms_command_parser = SMSCommandParser(
            self.sms_companion_manager,
            self.companion_manager
        )

        # Initialize SMS webhook server for incoming messages
        self.webhook_server = SMSWebhookServer(message_callback=self._on_incoming_sms)

        # Initialize Memory
        self.memory_store = MemoryStore(self.project_dir)
        self.memory_manager = MemoryManager(self.ai_backend, self.memory_store)

        # Current companion and conversation
        self.current_companion = None
        self.current_conversation = None

    def _on_incoming_sms(self, from_number: str, body: str, message_sid: str):
        """
        Handle incoming SMS message from webhook.

        This is called from a background thread, so we use GLib.idle_add
        to safely update the UI from the main thread.
        """
        print(f"📩 Processing incoming SMS from {from_number}: {body}")

        # Check if this is a command
        is_command, command_response, new_companion_id = self.sms_command_parser.parse_message(body, from_number)

        if is_command:
            # This is a command - send the response and don't process as conversation
            print(f"📋 SMS Command detected: {body}")

            # Send command response via SMS
            if command_response:
                self.sms_integration.send_message_async(command_response)

            # If it was a switch command, the mapping is already updated
            if new_companion_id:
                print(f"✅ Switched to companion: {new_companion_id}")

            return  # Don't process as regular message

        # Not a command - process as regular conversation message
        def process_sms():
            # Get the companion ID for this phone number
            companion_id = self.sms_companion_manager.get_companion_id(from_number)

            # If no mapping exists, use the current companion from the app
            if not companion_id:
                if self.current_companion:
                    companion_id = self.current_companion.id
                    # Create a mapping for future messages
                    self.sms_companion_manager.set_companion_id(
                        from_number,
                        self.current_companion.id,
                        self.current_companion.name
                    )
                    print(f"📝 Mapped {from_number} to {self.current_companion.name}")
                else:
                    # No companion available
                    error_msg = "⚠️ No companion selected. Please open the app and select a companion."
                    self.sms_integration.send_message_async(error_msg)
                    return

            # Create or get the companion
            companion = self.companion_manager.create_companion(companion_id)
            if not companion:
                error_msg = "❌ Companion not found. Text 'list' to see available companions."
                self.sms_integration.send_message_async(error_msg)
                return

            # Update last interaction time
            self.sms_companion_manager.update_last_interaction(from_number)

            # Get or create conversation for this companion
            conversation = self.storage.get_or_create_conversation(companion_id)

            # Add user message to conversation
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            conversation.add_message("user", body, timestamp)

            # Save conversation
            if self.config.get("auto_save_enabled", True):
                self.storage.save_conversation(conversation)

            # Get context and system prompt
            messages = conversation.get_context_messages()
            system_prompt = companion.get_system_prompt()

            # Add memory context
            memory_context = self.memory_store.get_context_summary()
            if memory_context and memory_context != "No information about the user yet.":
                system_prompt += f"\n\nWhat you remember about the user:\n{memory_context}\n\nUse this information to personalize your responses and show you care."

            print(f"🤖 Generating response from {companion.name}...")

            # Generate AI response
            def on_ai_response(response: str):
                # Add assistant message
                timestamp = datetime.now().isoformat()
                conversation.add_message("assistant", response, timestamp)

                # Save conversation
                if self.config.get("auto_save_enabled", True):
                    self.storage.save_conversation(conversation)

                # Extract memories
                try:
                    # Create temporary memory manager for this companion
                    from memory_extractor import MemoryManager
                    temp_memory_manager = MemoryManager(self.ai_backend, self.memory_store)
                    temp_memory_manager.process_conversation(
                        conversation.get_context_messages(),
                        companion.id,
                    )
                except Exception as e:
                    print(f"Memory extraction error: {e}")

                # Send response back via SMS
                print(f"📤 Sending SMS response to {from_number}")
                self.message_forwarder.send_companion_message_to_sms(response)

                # Update UI if this companion is currently active in the app
                def update_ui():
                    win = self.props.active_window
                    if win and hasattr(win, 'chat_view') and self.current_companion:
                        if self.current_companion.id == companion_id:
                            # Only update UI if this is the active companion
                            win.chat_view.show_user_message(body)
                            GLib.idle_add(lambda: win.chat_view.show_companion_message(response))
                            GLib.idle_add(lambda: win.chat_view._scroll_to_bottom())

                GLib.idle_add(update_ui)

            # Generate response
            self.ai_backend.generate_async(messages, system_prompt, on_ai_response)

        # Run in main thread
        GLib.idle_add(process_sms)

    def do_activate(self):
        """Activate the application (create window)."""
        win = self.props.active_window
        if not win:
            from main_window import MainWindow
            win = MainWindow(self)

        # Load CSS
        css_path = Path(__file__).parent / "style.css"
        if css_path.exists():
            css_provider = Gtk.CssProvider()
            css_provider.load_from_path(str(css_path))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        # Start SMS webhook server
        if self.sms_integration.is_configured():
            self.webhook_server.start()
            print("✅ SMS webhook server started - incoming SMS enabled")
        else:
            print("⚠️  SMS not configured - webhook server not started")

        win.present()

    def _get_current_backend(self):
        """Get the current active AI backend."""
        backend_type = self.config.get("ai_backend", "ollama")

        if backend_type == "ollama":
            return self.ollama_backend
        else:
            # Use OpenAI-compatible backend
            if not self.openai_backend:
                api_key = self.config.get("api_key", "")
                if api_key:
                    self.openai_backend = OpenAIBackend(
                        api_key=api_key,
                        base_url=self.config.get("api_url", "https://api.openai.com/v1"),
                        model=self.config.get("api_model", "gpt-3.5-turbo"),
                        additional_params=self.config.get("api_params", "") or None,
                    )
                else:
                    # No API key, fall back to Ollama
                    return self.ollama_backend
            return self.openai_backend if self.openai_backend else self.ollama_backend

    def reload_backend(self):
        """Reload the AI backend (call after settings change)."""
        # Update backend type
        self.backend_type = self.config.get("ai_backend", "ollama")

        # Reload Ollama settings
        self.ollama_backend = OllamaBackend(
            model_name=self.config.get("ollama_model", "mistral"),
            base_url=self.config.get("ollama_url", "http://localhost:11434"),
        )

        # Reload OpenAI settings
        api_key = self.config.get("api_key", "")
        if api_key:
            self.openai_backend = OpenAIBackend(
                api_key=api_key,
                base_url=self.config.get("api_url", "https://api.openai.com/v1"),
                model=self.config.get("api_model", "gpt-3.5-turbo"),
                additional_params=self.config.get("api_params", "") or None,
            )
        else:
            self.openai_backend = None

        # Update current backend
        self.ai_backend = self._get_current_backend()

        # Update memory manager
        self.memory_manager = MemoryManager(self.ai_backend, self.memory_store)

    def set_current_companion(self, companion: Companion):
        """Set the current active companion."""
        self.current_companion = companion
        self.current_conversation = self.storage.get_or_create_conversation(
            companion.id
        )
        self.config.set("last_companion", companion.id)

    def send_message(self, message: str, callback):
        """Send a message and get AI response."""
        if not self.current_companion:
            callback("Error: No companion selected")
            return

        # Add user message to conversation
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        self.current_conversation.add_message("user", message, timestamp)

        # Get context and system prompt
        messages = self.current_conversation.get_context_messages()
        system_prompt = self.current_companion.get_system_prompt()

        # Add memory context to system prompt
        memory_context = self.memory_store.get_context_summary()
        if memory_context and memory_context != "No information about the user yet.":
            system_prompt += f"\n\nWhat you remember about the user:\n{memory_context}\n\nUse this information to personalize your responses and show you care."

        # Generate response
        def on_response(response: str):
            # Add assistant message
            timestamp = datetime.now().isoformat()
            self.current_conversation.add_message("assistant", response, timestamp)

            # Save conversation
            if self.config.get("auto_save_enabled", True):
                self.storage.save_conversation(self.current_conversation)

            # Extract memories from conversation
            try:
                self.memory_manager.process_conversation(
                    self.current_conversation.get_context_messages(),
                    self.current_companion.id,
                )
            except Exception as e:
                print(f"Memory extraction error: {e}")

            # Forward to SMS if enabled
            if self.message_forwarder.should_forward_to_sms():
                self.message_forwarder.send_companion_message_to_sms(response)

            callback(response)

        self.ai_backend.generate_async(messages, system_prompt, on_response)

    def get_companion_history(self):
        """Get message history for current companion."""
        if self.current_conversation:
            return self.current_conversation.messages
        return []


def main():
    """Main entry point."""
    app = KardiaApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
