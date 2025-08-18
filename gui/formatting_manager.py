#!/usr/bin/env python3
"""
Formatting Manager Mixin for DJs Timeline-maskin
Contains formatting-related methods extracted from main_window.py
"""

# Standard library imports
import logging
import tkinter as tk

# GUI imports
import customtkinter as ctk

# Core imports
from core.field_definitions import field_manager

# Setup logging
logger = logging.getLogger(__name__)


class FormattingManagerMixin:
    """Mixin class containing formatting-related methods"""

    def get_theme_default_text_color(self):
        """Get the current theme's appropriate default text color"""
        try:
            # Get current style instance
            # Style removed - not needed in CustomTkinter
            # Get default text color from CustomTkinter theme
            # CustomTkinter uses appearance mode for theming
            appearance_mode = ctk.get_appearance_mode()
            if appearance_mode == "Dark":
                return '#ffffff'  # White text for dark mode
            else:
                return '#000000'  # Black text for light mode

        except Exception as e:
            logger.warning(f"Could not determine theme default color: {e}")
            # Safe fallback - dark gray that works on most backgrounds
            return '#404040'

    def setup_text_formatting_tags(self, text_widget):
        """Configure formatting tags for rich text support"""
        # Get current font size from config
        font_size = self.config.get('text_font_size', 9)

        # Get the actual default text color from the widget
        default_color = text_widget.cget('foreground')

        # Bold tag
        text_widget.tag_configure("bold", font=('Arial', font_size, 'bold'))

        # Color tags
        text_widget.tag_configure("red", foreground="red")
        text_widget.tag_configure("blue", foreground="blue")
        text_widget.tag_configure("green", foreground="green")
        text_widget.tag_configure("default", foreground=default_color)  # Use actual default color

    def update_formatting_tags(self, text_widget, font_size):
        """Update formatting tags with new font size"""
        # Update bold tag
        text_widget.tag_configure("bold", font=('Arial', font_size, 'bold'))

        # Color tags don't need font size updates

    def toggle_text_font_size(self):
        """Toggle text font size between 9pt → 12pt → 15pt → 9pt"""
        current_size = self.config.get('text_font_size', 9)

        # Cycle through font sizes
        if current_size == 9:
            new_size = 12
        elif current_size == 12:
            new_size = 15
        else:  # 15 or any other value
            new_size = 9

        # Update config
        self.config['text_font_size'] = new_size
        self.config_manager.save_config(self.config)

        # Apply new font size to all text fields
        self.apply_text_font_size(new_size)

        logger.info(f"Text font size changed from {current_size}pt to {new_size}pt")

    def get_text_field_display_names(self):
        """Get current display names for all text fields that support font sizing"""
        text_field_internal_ids = ['handelse', 'note1', 'note2', 'note3']
        try:
            return [field_manager.get_display_name(field_id) for field_id in text_field_internal_ids]
        except Exception as e:
            # Fallback to hardcoded names if field_manager unavailable
            logger.warning(f"Could not get dynamic field names, using fallback: {e}")
            return ['Händelse', 'Note1', 'Note2', 'Note3']

    def apply_text_font_size(self, font_size):
        """Apply font size to all text fields dynamically and update formatting tags"""
        # Get current display names for text fields
        text_fields = self.get_text_field_display_names()

        logger.debug(f"Applying font size {font_size}pt to text fields: {text_fields}")

        for field_name in text_fields:
            if field_name in self.excel_vars:
                text_widget = self.excel_vars[field_name]

                # Update main widget font (for ScrollableText, we need the actual text widget)
                if hasattr(text_widget, 'text_widget'):  # ScrollableText wrapper
                    actual_widget = text_widget.text_widget
                else:
                    actual_widget = text_widget

                # Update the main font
                actual_widget.configure(font=('Arial', font_size))

                # Update formatting tags to use new font size
                self.update_formatting_tags(actual_widget, font_size)

                logger.debug(f"Updated font size to {font_size}pt for {field_name}")

    def configure_button_styles(self):
        """Configure custom button styles with fixed colors that persist across theme changes"""
        # Style configuration not needed in CustomTkinter
        # Colors are set directly on buttons
        pass

    def create_formatting_toolbar(self, parent_frame, text_widget, col_name, field_id=None):
        """Create formatting toolbar with buttons and bind keyboard shortcuts"""
        # Ensure custom button styles are configured
        self.configure_button_styles()
        # Bold button - styled with bold text using Unicode - 50% smaller
        bold_btn = ctk.CTkButton(parent_frame, text="𝐁", width=18, height=18,
                           command=lambda: self.toggle_format(text_widget, "bold"),
                           font=ctk.CTkFont(size=10))
        bold_btn.pack(side="left", padx=(0, 1))

        # Color buttons with fixed colors (order: Red, Green, Blue)
        # Red button - fixed red color - 50% smaller
        red_btn = ctk.CTkButton(parent_frame, text="●", width=18, height=18,
                          command=lambda: self.toggle_format(text_widget, "red"),
                          fg_color="#DC3545", hover_color="#C82333",
                          font=ctk.CTkFont(size=10))
        red_btn.pack(side="left", padx=(0, 1))

        # Green button - fixed green color - 50% smaller
        green_btn = ctk.CTkButton(parent_frame, text="●", width=18, height=18,
                            command=lambda: self.toggle_format(text_widget, "green"),
                            fg_color="#28A745", hover_color="#218838",
                            font=ctk.CTkFont(size=10))
        green_btn.pack(side="left", padx=(0, 1))

        # Blue button - fixed blue color - 50% smaller
        blue_btn = ctk.CTkButton(parent_frame, text="●", width=18, height=18,
                           command=lambda: self.toggle_format(text_widget, "blue"),
                           fg_color="#007BFF", hover_color="#0069D9",
                           font=ctk.CTkFont(size=10))
        blue_btn.pack(side="left", padx=(0, 1))

        # Clear formatting button - removes ALL formatting and restores theme default color - 50% smaller
        default_btn = ctk.CTkButton(parent_frame, text="T", width=18, height=18,
                              command=lambda: self.clear_all_formatting(text_widget),
                              fg_color="gray60", hover_color="gray50",
                              font=ctk.CTkFont(size=10))
        default_btn.pack(side="left", padx=(0, 1))

        # Font size toggle button - 50% smaller (only for Händelse field)
        if field_id == 'handelse':
            font_btn = ctk.CTkButton(parent_frame, text="A+", width=20, height=18,
                               command=lambda: self.toggle_text_font_size(),
                               font=ctk.CTkFont(size=9))
            font_btn.pack(side="left", padx=(1, 0))

        # Bind keyboard shortcuts for this text widget
        text_widget.bind('<Control-b>', lambda e: self.toggle_format(text_widget, "bold"))
        text_widget.bind('<Control-r>', lambda e: self.toggle_format(text_widget, "red"))
        text_widget.bind('<Control-1>', lambda e: self.toggle_format(text_widget, "blue"))
        text_widget.bind('<Control-g>', lambda e: self.toggle_format(text_widget, "green"))
        text_widget.bind('<Control-k>', lambda e: self.clear_all_formatting(text_widget))

    def toggle_format(self, text_widget, format_type):
        """Toggle formatting on selected text with undo support"""
        try:
            # Add edit separator BEFORE formatting change
            text_widget.edit_separator()

            # Get current selection
            try:
                start = text_widget.index(tk.SEL_FIRST)
                end = text_widget.index(tk.SEL_LAST)
            except tk.TclError:
                # No selection, use current cursor position for word
                cursor = text_widget.index(tk.INSERT)
                # Find word boundaries
                start = text_widget.index(f"{cursor} wordstart")
                end = text_widget.index(f"{cursor} wordend")

            # Check if the selection already has this format
            current_tags = text_widget.tag_names(start)

            if format_type in current_tags:
                # Remove the format
                text_widget.tag_remove(format_type, start, end)
            else:
                # Add the format
                text_widget.tag_add(format_type, start, end)

            # For colors, remove other color tags when applying a new one
            if format_type in ["red", "blue", "green", "default"]:
                color_tags = ["red", "blue", "green", "default"]
                for color_tag in color_tags:
                    if color_tag != format_type:
                        text_widget.tag_remove(color_tag, start, end)

            # Add edit separator AFTER formatting change
            text_widget.edit_separator()

        except tk.TclError:
            # Handle any errors silently
            pass

    def clear_all_formatting(self, text_widget):
        """Clear ALL formatting from selected text and restore theme-appropriate default color"""
        try:
            # Add edit separator BEFORE formatting change
            text_widget.edit_separator()

            # Get current selection
            try:
                start = text_widget.index(tk.SEL_FIRST)
                end = text_widget.index(tk.SEL_LAST)
            except tk.TclError:
                # No selection, use entire text
                start = "1.0"
                end = "end-1c"

            # Remove ALL formatting tags from the selection
            all_format_tags = ["bold", "red", "blue", "green", "default"]
            for tag in all_format_tags:
                text_widget.tag_remove(tag, start, end)

            # Get the text widget's actual default color (not the theme's system color)
            default_color = text_widget.cget('foreground')

            # Create a temporary tag for the theme default color
            temp_tag = "theme_default"
            text_widget.tag_configure(temp_tag, foreground=default_color)
            text_widget.tag_add(temp_tag, start, end)

            # Immediately replace the temporary tag with the permanent default tag
            text_widget.tag_remove(temp_tag, start, end)
            text_widget.tag_configure("default", foreground=default_color)
            text_widget.tag_add("default", start, end)

            # Add edit separator AFTER formatting change
            text_widget.edit_separator()

            logger.debug(f"Cleared all formatting and applied theme color {default_color}")

        except tk.TclError as e:
            logger.warning(f"Error clearing formatting: {e}")
            pass

    def get_formatted_text_for_excel(self, text_widget):
        """METHOD 2: CHARACTER-BY-CHARACTER BREAKTHROUGH ALGORITHM - Extract formatted text from Text widget"""
        try:
            from openpyxl.cell.rich_text import CellRichText, TextBlock
            from openpyxl.cell.text import InlineFont
            from openpyxl.styles.colors import Color

            # Get plain text
            plain_text = text_widget.get("1.0", "end-1c")

            # Check if there are any formatting tags
            all_tags = text_widget.tag_names()
            format_tags = [tag for tag in all_tags if tag in ["bold", "red", "blue", "green", "default"]]

            if not format_tags:
                # No formatting, return plain text
                return plain_text

            # METHOD 2: Process text character by character to maintain correct order
            rich_parts = []
            current_pos = "1.0"

            # Get all text
            text_end = text_widget.index("end-1c")

            # Iterate through text character by character
            while text_widget.compare(current_pos, "<", text_end):
                next_pos = f"{current_pos} +1c"
                char = text_widget.get(current_pos, next_pos)

                # Get tags at current position
                tags_at_pos = text_widget.tag_names(current_pos)
                format_tags_at_pos = [tag for tag in tags_at_pos if tag in ["bold", "red", "blue", "green", "default"]]

                # Build text with same formatting
                text_with_format = char
                temp_pos = next_pos

                # Continue until formatting changes
                while text_widget.compare(temp_pos, "<", text_end):
                    temp_tags = text_widget.tag_names(temp_pos)
                    temp_format_tags = [tag for tag in temp_tags if tag in ["bold", "red", "blue", "green", "default"]]

                    if set(format_tags_at_pos) != set(temp_format_tags):
                        break

                    next_char_pos = f"{temp_pos} +1c"
                    text_with_format += text_widget.get(temp_pos, next_char_pos)
                    temp_pos = next_char_pos

                # Create appropriate part
                if format_tags_at_pos:
                    font_kwargs = {}
                    for tag in format_tags_at_pos:
                        if tag == "bold":
                            font_kwargs['b'] = True
                        elif tag == "italic":
                            font_kwargs['i'] = True
                        elif tag == "red":
                            font_kwargs['color'] = Color(rgb="FF0000")
                        elif tag == "blue":
                            font_kwargs['color'] = Color(rgb="0000FF")
                        elif tag == "green":
                            font_kwargs['color'] = Color(rgb="008000")
                        elif tag == "default":
                            # For default color, we'll need to use the actual default text color
                            # For Excel export, we can use a dark gray that matches typical default text
                            font_kwargs['color'] = Color(rgb="404040")

                    if font_kwargs:
                        font = InlineFont(**font_kwargs)
                        rich_parts.append(TextBlock(font, text_with_format))
                    else:
                        rich_parts.append(text_with_format)
                else:
                    rich_parts.append(text_with_format)

                current_pos = temp_pos

            # Create CellRichText if we have formatting
            if any(isinstance(part, TextBlock) for part in rich_parts):
                result = CellRichText(*rich_parts)
                logger.info(f"METHOD 2: Created CellRichText with {len(result)} parts")
                return result
            else:
                return plain_text

        except Exception as e:
            logger.warning(f"Error extracting formatted text with Method 2: {e}")
            # Fallback to plain text
            return text_widget.get("1.0", "end-1c")
