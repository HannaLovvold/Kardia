"""Personality Questionnaire Dialog for Kardia AI Companion.

This module provides a GTK4 dialog for generating and viewing
personality profiles for AI companions.

Copyright (c) 2025 Hanna Lovvold
All rights reserved.
"""
import gi
import threading
from typing import Dict, Optional, Callable

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango

from personality_questionnaire import (
    PERSONALITY_QUESTIONS,
    generate_personality_prompt,
    parse_ai_response,
    format_qa_for_personality,
    get_all_questions
)


class PersonalityQuestionnaireDialog(Adw.Window):
    """Dialog for generating and viewing personality questionnaire responses."""

    def __init__(self, parent, ai_backend, companion_data: Dict, callback: Callable):
        """Initialize the questionnaire dialog.

        Args:
            parent: Parent window
            ai_backend: AI backend for generating responses
            companion_data: Dictionary with companion's basic info
            callback: Function to call with generated personality text
        """
        super().__init__()
        self.set_default_size(700, 800)
        self.set_title(f"Personality Profile - {companion_data.get('name', 'Companion')}")
        self.set_modal(True)
        self.set_transient_for(parent)

        self.ai_backend = ai_backend
        self.companion_data = companion_data
        self.callback = callback
        self.generated_answers = {}
        self.is_generating = False

        self._create_content()

    def _create_content(self):
        """Create the dialog content."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)

        # Header with description
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        title_label = Gtk.Label()
        title_label.set_markup(f"<b><big>Personality Questionnaire</big></b>")
        title_label.set_halign(Gtk.Align.START)
        header_box.append(title_label)

        desc_label = Gtk.Label()
        desc_label.set_markup(
            f"Generate a detailed personality profile for <b>{self.companion_data.get('name', 'Companion')}</b> "
            "based on their traits. The AI will answer 50 questions in character."
        )
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.set_size_request(650, -1)
        header_box.append(desc_label)

        main_box.append(header_box)

        # Scrolled window for questions/answers
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.content_box.set_margin_start(10)
        self.content_box.set_margin_end(10)
        self.content_box.set_margin_top(10)
        self.content_box.set_margin_bottom(10)
        scroll.set_child(self.content_box)

        main_box.append(scroll)

        # Progress bar (hidden initially)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("Generating personality profile...")
        self.progress_bar.set_visible(False)
        main_box.append(self.progress_bar)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_wrap(True)
        self.status_label.set_visible(False)
        main_box.append(self.status_label)

        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(10)
        button_box.set_halign(Gtk.Align.END)

        self.generate_button = Gtk.Button(label="Generate Profile")
        self.generate_button.add_css_class("suggested-action")
        self.generate_button.connect("clicked", self._on_generate_clicked)
        button_box.append(self.generate_button)

        self.apply_button = Gtk.Button(label="Apply to Personality")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.set_sensitive(False)
        self.apply_button.connect("clicked", self._on_apply_clicked)
        button_box.append(self.apply_button)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: self.close())
        button_box.append(cancel_button)

        main_box.append(button_box)
        self.set_content(main_box)

        # Show questions preview
        self._show_questions_preview()

    def _show_questions_preview(self):
        """Show preview of questions in the content area."""
        # Add a note about the questions
        info_label = Gtk.Label()
        info_label.set_markup(
            "<i>The questionnaire covers 8 categories with 50 questions total. "
            "Click 'Generate Profile' to have the AI answer these questions in character.</i>"
        )
        info_label.set_wrap(True)
        info_label.set_margin_bottom(10)
        self.content_box.append(info_label)

        # Show categories
        for category, questions in PERSONALITY_QUESTIONS.items():
            category_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

            category_label = Gtk.Label()
            category_label.set_markup(f"<b>{category}</b> ({len(questions)} questions)")
            category_label.set_halign(Gtk.Align.START)
            category_label.set_margin_top(10)
            category_box.append(category_label)

            # Show first 2 questions as preview
            for i, (num, question) in enumerate(questions[:2]):
                q_label = Gtk.Label()
                q_label.set_markup(f"  <small>{num}. {question}</small>")
                q_label.set_halign(Gtk.Align.START)
                q_label.set_ellipsize(Pango.EllipsizeMode.END)
                q_label.set_size_request(600, -1)
                category_box.append(q_label)

            if len(questions) > 2:
                more_label = Gtk.Label()
                more_label.set_markup(f"  <small><i>... and {len(questions) - 2} more questions</i></small>")
                more_label.set_halign(Gtk.Align.START)
                category_box.append(more_label)

            self.content_box.append(category_box)

    def _on_generate_clicked(self, button):
        """Handle generate button click."""
        if self.is_generating:
            return

        self.is_generating = True
        self.generate_button.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.progress_bar.pulse()
        self.status_label.set_markup("<i>Generating personality profile... This may take a moment.</i>")
        self.status_label.set_visible(True)

        # Clear content box and show loading
        for child in self.content_box:
            self.content_box.remove(child)

        loading_label = Gtk.Label()
        loading_label.set_markup("<big><b>Generating Personality Profile...</b></big>\n\nPlease wait...")
        self.content_box.append(loading_label)

        # Generate in background thread
        def generate_in_background():
            try:
                # Generate the prompt
                prompt = generate_personality_prompt(self.companion_data)

                # Call AI backend
                response = self.ai_backend.generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt="You are a creative writing assistant helping design an AI companion's personality. Answer naturally and thoughtfully in character.",
                    stream=False
                )

                # Parse response
                self.generated_answers = parse_ai_response(response)

                # Update UI on main thread
                GLib.idle_add(self._show_generated_results)

            except Exception as e:
                GLib.idle_add(self._show_error, str(e))

        thread = threading.Thread(target=generate_in_background, daemon=True)
        thread.start()

    def _show_generated_results(self):
        """Show the generated questionnaire results."""
        self.is_generating = False
        self.progress_bar.set_visible(False)
        self.status_label.set_visible(False)
        self.apply_button.set_sensitive(True)
        self.generate_button.set_sensitive(True)

        # Clear content box
        for child in self.content_box:
            self.content_box.remove(child)

        # Add header
        header_label = Gtk.Label()
        header_label.set_markup(f"<big><b>Personality Profile for {self.companion_data.get('name', 'Companion')}</b></big>")
        header_label.set_margin_bottom(15)
        self.content_box.append(header_label)

        # Create scrollable text view for the full profile
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        text_view.set_left_margin(10)
        text_view.set_right_margin(10)
        text_view.set_top_margin(10)
        text_view.set_bottom_margin(10)

        buffer = text_view.get_buffer()
        formatted_text = format_qa_for_personality(self.generated_answers, self.companion_data.get('name', 'Companion'))
        buffer.set_text(formatted_text)

        # Create a tag for bold text
        bold_tag = buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        # Create a tag for headers
        header_tag = buffer.create_tag("header", size=15 * Pango.SCALE, weight=Pango.Weight.BOLD)

        scroll.set_child(text_view)
        self.content_box.append(scroll)

    def _show_error(self, error_message: str):
        """Show error message."""
        self.is_generating = False
        self.progress_bar.set_visible(False)
        self.generate_button.set_sensitive(True)

        # Clear content box
        for child in self.content_box:
            self.content_box.remove(child)

        error_label = Gtk.Label()
        error_label.set_markup(f"<b><span foreground='red'>Error generating profile:</span></b>\n\n{error_message}")
        error_label.set_wrap(True)
        self.content_box.append(error_label)

    def _on_apply_clicked(self, button):
        """Handle apply button click - add profile to personality."""
        if not self.generated_answers:
            return

        formatted_text = format_qa_for_personality(
            self.generated_answers,
            self.companion_data.get('name', 'Companion')
        )

        # Call the callback with the formatted text
        if self.callback:
            self.callback(formatted_text)

        self.close()

    def get_answers(self) -> Dict[str, str]:
        """Get the generated Q&A pairs."""
        return self.generated_answers
