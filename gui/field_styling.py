"""
Centralized field styling system for disabled field appearance.
Provides consistent styling for disabled fields across the application.
"""

import logging
import tkinter as tk
from typing import Any, Dict

import customtkinter as ctk

logger = logging.getLogger(__name__)


class FieldStyling:
    """Centralized field styling manager for disabled fields."""

    # Disabled field color scheme - Enhanced for better visibility
    DISABLED_COLORS = {
        'entry_bg': '#E8E8E8',           # More noticeable gray background for entries
        'text_bg': '#E8E8E8',            # More noticeable gray background for text fields
        'text_color': '#666666',         # Darker dimmed text color for better contrast
        'border': '#CCCCCC',             # More visible muted border color
        'checkbox_bg': '#E8E8E8',        # Darker disabled checkbox background
        'label_color': '#666666',        # Darker dimmed label color
    }

    # Enabled field colors (for reference and restoration)
    ENABLED_COLORS = {
        'entry_bg': '#F8F8F8',           # Standard entry background
        'text_bg': 'white',              # Standard text background
        'text_color': 'black',           # Standard text color
        'border': '#E0E0E0',             # Standard border color
        'checkbox_bg': 'white',          # Standard checkbox background
        'label_color': 'black',          # Standard label color
    }

    @classmethod
    def get_disabled_entry_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for disabled CTkEntry widgets.
        Enhanced for better CustomTkinter compatibility.

        Returns:
            Dictionary of styling parameters for CTkEntry
        """
        return {
            'state': 'disabled',
            'fg_color': cls.DISABLED_COLORS['entry_bg'],
            'text_color': cls.DISABLED_COLORS['text_color'],
            'border_color': cls.DISABLED_COLORS['border'],
            'border_width': 2,  # Slightly thicker border for disabled fields
            'corner_radius': 6,
            # Add explicit disabled color parameters for CustomTkinter
            'placeholder_text_color': cls.DISABLED_COLORS['text_color']
        }

    @classmethod
    def get_enabled_entry_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for enabled CTkEntry widgets.

        Returns:
            Dictionary of styling parameters for CTkEntry
        """
        return {
            'state': 'normal',
            'fg_color': cls.ENABLED_COLORS['entry_bg'],
            'text_color': cls.ENABLED_COLORS['text_color'],
            'border_color': cls.ENABLED_COLORS['border'],
            'border_width': 1,
            'corner_radius': 6
        }

    @classmethod
    def get_disabled_text_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for disabled text widgets (ScrollableText).

        Returns:
            Dictionary of styling parameters for text widgets
        """
        return {
            'state': 'disabled',
            'bg': cls.DISABLED_COLORS['text_bg'],
            'fg': cls.DISABLED_COLORS['text_color'],
            'highlightcolor': cls.DISABLED_COLORS['border'],
            'highlightbackground': cls.DISABLED_COLORS['border'],
            'highlightthickness': 1,
            'wrap': 'word'
        }

    @classmethod
    def get_enabled_text_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for enabled text widgets (ScrollableText).

        Returns:
            Dictionary of styling parameters for text widgets
        """
        return {
            'state': 'normal',
            'bg': cls.ENABLED_COLORS['text_bg'],
            'fg': cls.ENABLED_COLORS['text_color'],
            'highlightcolor': '#2196F3',  # Blue focus highlight
            'highlightbackground': cls.ENABLED_COLORS['border'],
            'highlightthickness': 1,
            'wrap': 'word'
        }

    @classmethod
    def get_disabled_checkbox_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for disabled CTkCheckBox widgets.

        Returns:
            Dictionary of styling parameters for CTkCheckBox
        """
        return {
            'state': 'disabled',
            'fg_color': cls.DISABLED_COLORS['checkbox_bg'],
            'border_color': cls.DISABLED_COLORS['border'],
            'text_color': cls.DISABLED_COLORS['text_color'],
            'hover_color': cls.DISABLED_COLORS['checkbox_bg']
        }

    @classmethod
    def get_enabled_checkbox_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for enabled CTkCheckBox widgets.

        Returns:
            Dictionary of styling parameters for CTkCheckBox
        """
        return {
            'state': 'normal',
            'fg_color': cls.ENABLED_COLORS['checkbox_bg'],
            'border_color': cls.ENABLED_COLORS['border'],
            'text_color': cls.ENABLED_COLORS['text_color']
        }

    @classmethod
    def get_disabled_label_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for disabled CTkLabel widgets.

        Returns:
            Dictionary of styling parameters for CTkLabel
        """
        return {
            'text_color': cls.DISABLED_COLORS['label_color'],
            'font': ctk.CTkFont(size=12, slant='italic')  # Italic for disabled appearance
        }

    @classmethod
    def get_enabled_label_style(cls) -> Dict[str, Any]:
        """
        Get styling configuration for enabled CTkLabel widgets.

        Returns:
            Dictionary of styling parameters for CTkLabel
        """
        return {
            'text_color': cls.ENABLED_COLORS['label_color'],
            'font': ctk.CTkFont(size=12)  # Normal font for enabled
        }

    @classmethod
    def apply_disabled_style(cls, widget: Any, widget_type: str) -> bool:
        """
        Apply disabled styling to a widget.

        Args:
            widget: The widget to style
            widget_type: Type of widget ('entry', 'text', 'checkbox', 'label')

        Returns:
            True if styling was applied successfully, False otherwise
        """
        try:
            if widget_type == 'entry':
                style = cls.get_disabled_entry_style()
            elif widget_type == 'text':
                style = cls.get_disabled_text_style()
            elif widget_type == 'checkbox':
                style = cls.get_disabled_checkbox_style()
            elif widget_type == 'label':
                style = cls.get_disabled_label_style()
            else:
                logger.warning(f"Unknown widget type for styling: {widget_type}")
                return False

            # Log the widget class and styling being applied for debugging
            widget_class = widget.__class__.__name__
            logger.info(f"Applying disabled styling to {widget_class} ({widget_type}): {style}")

            widget.configure(**style)
            logger.info(f"Successfully applied disabled styling to {widget_type} widget ({widget_class})")
            return True

        except Exception as e:
            widget_class = widget.__class__.__name__ if widget else "Unknown"
            logger.error(f"Failed to apply disabled styling to {widget_type} ({widget_class}): {e}")
            logger.error(f"Style attempted: {style if 'style' in locals() else 'N/A'}")
            return False

    @classmethod
    def apply_enabled_style(cls, widget: Any, widget_type: str) -> bool:
        """
        Apply enabled styling to a widget.

        Args:
            widget: The widget to style
            widget_type: Type of widget ('entry', 'text', 'checkbox', 'label')

        Returns:
            True if styling was applied successfully, False otherwise
        """
        try:
            if widget_type == 'entry':
                style = cls.get_enabled_entry_style()
            elif widget_type == 'text':
                style = cls.get_enabled_text_style()
            elif widget_type == 'checkbox':
                style = cls.get_enabled_checkbox_style()
            elif widget_type == 'label':
                style = cls.get_enabled_label_style()
            else:
                logger.warning(f"Unknown widget type for styling: {widget_type}")
                return False

            widget.configure(**style)
            logger.debug(f"Applied enabled styling to {widget_type} widget")
            return True

        except Exception as e:
            logger.error(f"Failed to apply enabled styling to {widget_type}: {e}")
            return False

    @classmethod
    def style_field_group(cls, field_widgets: Dict[str, Any], enabled: bool) -> None:
        """
        Apply styling to a complete field group (label, input, checkbox).

        Args:
            field_widgets: Dictionary containing field widgets
                          {'label': widget, 'input': widget, 'checkbox': widget}
            enabled: True for enabled styling, False for disabled styling
        """
        style_function = cls.apply_enabled_style if enabled else cls.apply_disabled_style

        # Style label if present
        if 'label' in field_widgets and field_widgets['label']:
            style_function(field_widgets['label'], 'label')

        # Style input widget if present
        if 'input' in field_widgets and field_widgets['input']:
            # Determine input widget type using isinstance checks
            widget = field_widgets['input']

            # Check for CTkEntry first (most specific)
            if isinstance(widget, ctk.CTkEntry):
                widget_type = 'entry'
            # Check for Text widget (including ScrollableText.text_widget)
            elif isinstance(widget, tk.Text):
                widget_type = 'text'
            # Check for ScrollableText wrapper (access the text_widget inside)
            elif hasattr(widget, 'text_widget') and isinstance(widget.text_widget, tk.Text):
                widget = widget.text_widget  # Use the actual Text widget for styling
                widget_type = 'text'
            else:
                # Fallback for other widget types
                logger.warning(f'Unknown input widget type: {widget.__class__.__name__}')
                widget_type = 'entry'  # Default to entry styling

            style_function(widget, widget_type)

        # Style checkbox if present
        if 'checkbox' in field_widgets and field_widgets['checkbox']:
            style_function(field_widgets['checkbox'], 'checkbox')

        logger.debug(f"Styled field group: {'enabled' if enabled else 'disabled'}")

    @classmethod
    def create_disabled_field_container(cls, parent: Any) -> ctk.CTkFrame:
        """
        Create a container frame with disabled field styling.

        Args:
            parent: Parent widget

        Returns:
            Styled container frame
        """
        container = ctk.CTkFrame(
            parent,
            fg_color=cls.DISABLED_COLORS['entry_bg'],
            border_color=cls.DISABLED_COLORS['border'],
            border_width=1,
            corner_radius=6
        )
        return container

    @classmethod
    def get_focus_style_override(cls) -> Dict[str, Any]:
        """
        Get focus style override for disabled fields.
        Disabled fields should not show focus styling.

        Returns:
            Dictionary of focus style parameters
        """
        return {
            'highlightcolor': cls.DISABLED_COLORS['border'],
            'highlightbackground': cls.DISABLED_COLORS['border'],
            'highlightthickness': 1
        }


# Convenience functions for common styling operations

def disable_field(field_widgets: Dict[str, Any]) -> None:
    """
    Convenience function to disable a complete field.

    Args:
        field_widgets: Dictionary containing field widgets
    """
    FieldStyling.style_field_group(field_widgets, enabled=False)


def enable_field(field_widgets: Dict[str, Any]) -> None:
    """
    Convenience function to enable a complete field.

    Args:
        field_widgets: Dictionary containing field widgets
    """
    FieldStyling.style_field_group(field_widgets, enabled=True)


def apply_field_state(field_widgets: Dict[str, Any], field_id: str,
                     is_disabled: bool) -> None:
    """
    Apply field state based on disabled status.

    Args:
        field_widgets: Dictionary containing field widgets
        field_id: Field identifier for logging
        is_disabled: True if field should be disabled, False if enabled
    """
    if is_disabled:
        disable_field(field_widgets)
        logger.debug(f"Applied disabled styling to field: {field_id}")
    else:
        enable_field(field_widgets)
        logger.debug(f"Applied enabled styling to field: {field_id}")
