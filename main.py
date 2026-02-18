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
from api_server import APIServer
from proactive_messenger import ProactiveMessageScheduler
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

        # Initialize API Server
        self.api_server = APIServer(self)

        # Initialize Proactive Message Scheduler
        self.proactive_scheduler = ProactiveMessageScheduler(self)

        # Initialize Memory
        self.memory_store = MemoryStore(self.project_dir)
        self.memory_manager = MemoryManager(self.ai_backend, self.memory_store)

        # Current companion and conversation
        self.current_companion = None
        self.current_conversation = None

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

        # Start API server
        self.api_server.start()

        # Start proactive message scheduler
        self.proactive_scheduler.start()

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
        from datetime import datetime
        current_dt = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        system_prompt = self.current_companion.get_system_prompt(current_dt)

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
