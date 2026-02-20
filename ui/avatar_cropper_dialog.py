"""
Avatar cropper dialog with draggable image and circular mask.

Copyright (c) 2025 Hanna Lovvold
All rights reserved.

Part of the Kardia AI Companion application.
"""
import gi
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GdkPixbuf


class AvatarCropperDialog(Adw.Window):
    """Dialog for cropping avatar images with a circular mask."""

    AVATAR_SIZE = 128  # Output size
    PREVIEW_SIZE = 200  # Size of the circular preview

    def __init__(self, parent, image_path: str, callback):
        """Initialize the avatar cropper dialog.

        Args:
            parent: Parent window
            image_path: Path to the source image
            callback: Function to call with (success, cropped_image_path)
        """
        super().__init__()
        self.set_title("Crop Avatar")
        self.set_default_size(500, 550)
        self.set_modal(True)
        self.set_transient_for(parent)

        self.callback = callback
        self.source_path = Path(image_path)
        self.original_pixbuf = None

        # Pan/offset state (image position relative to circle center)
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0

        # Drag state
        self.drag_start_offset_x = 0
        self.drag_start_offset_y = 0

        # Store the crop coordinates for final save
        self.final_crop_x = 0
        self.final_crop_y = 0
        self.final_scale = 1.0

        self._create_content()
        self._load_image()

    def _create_content(self):
        """Create the dialog content."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)

        # Title
        title = Gtk.Label()
        title.set_markup("<b>Position Your Avatar</b>")
        title.add_css_class("title-4")
        main_box.append(title)

        # Instructions
        instructions = Gtk.Label()
        instructions.set_text("Drag to position the face within the circle. Use zoom to resize.")
        instructions.add_css_class("body")
        instructions.set_wrap(True)
        instructions.add_css_class("dim-label")
        main_box.append(instructions)

        # Create a container for the cropper
        cropper_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cropper_container.set_valign(Gtk.Align.CENTER)
        cropper_container.set_halign(Gtk.Align.CENTER)

        # Use a Frame for the bordered circular preview
        self.preview_frame = Gtk.Frame()
        self.preview_frame.set_size_request(self.PREVIEW_SIZE, self.PREVIEW_SIZE)
        self.preview_frame.add_css_class("avatar-preview-frame")

        # The image (clipped to circle by CSS)
        self.cropper_image = Gtk.Image()
        self.cropper_image.set_size_request(self.PREVIEW_SIZE, self.PREVIEW_SIZE)
        self.cropper_image.add_css_class("avatar-cropper-preview")
        self.preview_frame.set_child(self.cropper_image)

        cropper_container.append(self.preview_frame)
        main_box.append(cropper_container)

        # Make the container draggable
        drag_gesture = Gtk.GestureDrag.new()
        cropper_container.add_controller(drag_gesture)
        drag_gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        drag_gesture.connect("drag-begin", self._on_drag_begin)
        drag_gesture.connect("drag-update", self._on_drag_update)
        drag_gesture.connect("drag-end", self._on_drag_end)

        # Zoom slider
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        zoom_label = Gtk.Label(label="Zoom:")
        zoom_box.append(zoom_label)

        self.zoom_adjustment = Gtk.Adjustment(value=1.0, lower=0.3, upper=3.0, step_increment=0.1)
        zoom_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.zoom_adjustment)
        zoom_slider.set_hexpand(True)
        zoom_slider.connect("value-changed", self._on_zoom_changed)
        zoom_box.append(zoom_slider)
        main_box.append(zoom_box)

        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(10)
        button_box.set_halign(Gtk.Align.END)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda _: self._on_cancel())
        button_box.append(cancel_button)

        apply_button = Gtk.Button(label="Apply")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", self._on_apply)
        button_box.append(apply_button)

        main_box.append(button_box)
        self.set_content(main_box)

    def _load_image(self):
        """Load the source image."""
        try:
            self.original_pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(self.source_path))

            # Calculate initial scale to fit the image in the preview
            img_width = self.original_pixbuf.get_width()
            img_height = self.original_pixbuf.get_height()
            max_dim = max(img_width, img_height)

            # Scale so the image fills the preview area with some room to move
            self.scale = (self.PREVIEW_SIZE * 1.2) / max_dim
            self.zoom_adjustment.set_value(self.scale)

            # Center the image initially
            self.offset_x = 0
            self.offset_y = 0

            self._update_preview()

        except Exception as e:
            print(f"Error loading image: {e}")
            import traceback
            traceback.print_exc()
            self.close()

    def _update_preview(self):
        """Update the preview image with current scale and offset."""
        if not self.original_pixbuf:
            return

        try:
            # Calculate the size needed
            img_width = self.original_pixbuf.get_width()
            img_height = self.original_pixbuf.get_height()

            # Scale the image
            scaled_width = int(img_width * self.scale)
            scaled_height = int(img_height * self.scale)

            # Don't scale if it's too small
            if scaled_width < self.PREVIEW_SIZE or scaled_height < self.PREVIEW_SIZE:
                # Image is too small at this scale, adjust scale
                min_scale = max(self.PREVIEW_SIZE / img_width, self.PREVIEW_SIZE / img_height)
                self.scale = min_scale
                self.zoom_adjustment.set_value(self.scale)
                scaled_width = int(img_width * self.scale)
                scaled_height = int(img_height * self.scale)

            scaled = self.original_pixbuf.scale_simple(
                scaled_width, scaled_height,
                GdkPixbuf.InterpType.BILINEAR
            )

            # Calculate where to place the image so the center is at the circle center
            # The offset moves the image relative to center
            center_x = scaled_width / 2
            center_y = scaled_height / 2

            # Calculate the crop rectangle (what will be visible in the circle)
            # The circle shows PREVIEW_SIZE x PREVIEW_SIZE centered on the image center + offset
            crop_x = int(center_x - self.PREVIEW_SIZE / 2 + self.offset_x)
            crop_y = int(center_y - self.PREVIEW_SIZE / 2 + self.offset_y)

            # Clamp to bounds - ensure we don't go negative or past the edge
            crop_x = max(0, min(crop_x, scaled_width - self.PREVIEW_SIZE))
            crop_y = max(0, min(crop_y, scaled_height - self.PREVIEW_SIZE))

            # Store final crop coordinates for saving
            self.final_crop_x = crop_x
            self.final_crop_y = crop_y
            self.final_scale = self.scale

            # Extract the square region that will be visible
            visible = scaled.new_subpixbuf(crop_x, crop_y, self.PREVIEW_SIZE, self.PREVIEW_SIZE)

            # Create a texture and display it
            texture = Gdk.Texture.new_for_pixbuf(visible)
            self.cropper_image.set_from_paintable(texture)

        except Exception as e:
            print(f"Error updating preview: {e}")
            import traceback
            traceback.print_exc()

    def _on_drag_begin(self, gesture, start_x, start_y):
        """Handle drag begin - store starting position."""
        self.drag_start_offset_x = self.offset_x
        self.drag_start_offset_y = self.offset_y

    def _on_drag_update(self, gesture, offset_x, offset_y):
        """Handle drag update."""
        self.offset_x = self.drag_start_offset_x + offset_x
        self.offset_y = self.drag_start_offset_y + offset_y
        self._update_preview()

    def _on_drag_end(self, gesture, offset_x, offset_y):
        """Handle drag end."""
        pass

    def _on_zoom_changed(self, slider):
        """Handle zoom slider change."""
        self.scale = self.zoom_adjustment.get_value()
        self._update_preview()

    def _on_cancel(self):
        """Handle cancel button."""
        self.callback(False, None)
        self.close()

    def _on_apply(self, button):
        """Handle apply button - crop and save the image."""
        try:
            # Get the scaled image again with current settings
            img_width = self.original_pixbuf.get_width()
            img_height = self.original_pixbuf.get_height()

            scaled_width = int(img_width * self.final_scale)
            scaled_height = int(img_height * self.final_scale)

            scaled = self.original_pixbuf.scale_simple(
                scaled_width, scaled_height,
                GdkPixbuf.InterpType.BILINEAR
            )

            # Extract the crop region
            crop = scaled.new_subpixbuf(
                int(self.final_crop_x),
                int(self.final_crop_y),
                self.PREVIEW_SIZE,
                self.PREVIEW_SIZE
            )

            # Scale to output size
            final_pixbuf = crop.scale_simple(
                self.AVATAR_SIZE, self.AVATAR_SIZE,
                GdkPixbuf.InterpType.BILINEAR
            )

            # Save to avatars directory
            avatar_dir = Path(__file__).parent.parent / "avatars"
            avatar_dir.mkdir(exist_ok=True)

            import hashlib
            file_hash = hashlib.md5(str(self.source_path).encode()).hexdigest()[:8]
            avatar_path = avatar_dir / f"avatar_{file_hash}.png"

            final_pixbuf.savev(str(avatar_path), "png", [], [])

            self.callback(True, str(avatar_path.resolve()))
            self.close()

        except Exception as e:
            print(f"Error saving cropped image: {e}")
            import traceback
            traceback.print_exc()
            self.callback(False, None)
            self.close()
