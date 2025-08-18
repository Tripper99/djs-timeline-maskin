"""
Field state manager for handling field visibility and data preservation.
Manages which fields are hidden/shown and preserves data when fields are hidden.
"""

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class FieldStateManager:
    """Manages field visibility states and data preservation."""

    # Fields that cannot be hidden (required for basic functionality)
    REQUIRED_VISIBLE_FIELDS = {'startdatum', 'kalla1', 'handelse'}

    def __init__(self):
        """Initialize the field state manager."""
        self._hidden_fields: Set[str] = set()
        self._preserved_data: Dict[str, str] = {}
        self._preserved_formats: Dict[str, any] = {}  # For rich text fields

    def can_hide_field(self, field_id: str) -> bool:
        """
        Check if a field can be hidden.

        Args:
            field_id: Internal field identifier

        Returns:
            True if field can be hidden, False otherwise
        """
        return field_id not in self.REQUIRED_VISIBLE_FIELDS

    def hide_field(self, field_id: str, current_value: str = "", current_format: any = None) -> bool:
        """
        Hide a field while preserving its data.

        Args:
            field_id: Internal field identifier
            current_value: Current field value to preserve
            current_format: Current format data (for rich text fields)

        Returns:
            True if field was hidden, False if field cannot be hidden
        """
        if not self.can_hide_field(field_id):
            logger.warning(f"Cannot hide required field: {field_id}")
            return False

        self._hidden_fields.add(field_id)

        # Preserve data if provided
        if current_value:
            self._preserved_data[field_id] = current_value
            logger.debug(f"Preserved data for hidden field {field_id}: {len(current_value)} chars")

        if current_format:
            self._preserved_formats[field_id] = current_format
            logger.debug(f"Preserved format for hidden field {field_id}")

        logger.info(f"Field hidden: {field_id}")
        return True

    def show_field(self, field_id: str) -> tuple[str, any]:
        """
        Show a field and return any preserved data.

        Args:
            field_id: Internal field identifier

        Returns:
            Tuple of (preserved_value, preserved_format) or ("", None) if no data
        """
        self._hidden_fields.discard(field_id)

        # Return preserved data if available
        value = self._preserved_data.pop(field_id, "")
        format_data = self._preserved_formats.pop(field_id, None)

        if value:
            logger.debug(f"Restored data for shown field {field_id}: {len(value)} chars")

        logger.info(f"Field shown: {field_id}")
        return value, format_data

    def is_field_hidden(self, field_id: str) -> bool:
        """
        Check if a field is currently hidden.

        Args:
            field_id: Internal field identifier

        Returns:
            True if field is hidden, False otherwise
        """
        return field_id in self._hidden_fields

    def is_field_visible(self, field_id: str) -> bool:
        """
        Check if a field is currently visible.

        Args:
            field_id: Internal field identifier

        Returns:
            True if field is visible, False otherwise
        """
        return field_id not in self._hidden_fields

    def get_hidden_fields(self) -> List[str]:
        """
        Get list of currently hidden field IDs.

        Returns:
            List of hidden field IDs
        """
        return list(self._hidden_fields)

    def get_visible_fields(self, all_fields: List[str]) -> List[str]:
        """
        Get list of visible field IDs from a list of all fields.

        Args:
            all_fields: List of all field IDs in order

        Returns:
            List of visible field IDs maintaining original order
        """
        return [f for f in all_fields if f not in self._hidden_fields]

    def set_hidden_fields(self, hidden_fields: List[str]) -> None:
        """
        Set the hidden fields from a list (e.g., from config or template).

        Args:
            hidden_fields: List of field IDs to hide
        """
        # Only hide fields that can be hidden
        self._hidden_fields = {
            f for f in hidden_fields
            if self.can_hide_field(f)
        }

        # Log any fields that couldn't be hidden
        invalid = [f for f in hidden_fields if not self.can_hide_field(f)]
        if invalid:
            logger.warning(f"Cannot hide required fields: {invalid}")

    def get_preserved_data(self, field_id: str) -> Optional[str]:
        """
        Get preserved data for a hidden field without showing it.

        Args:
            field_id: Internal field identifier

        Returns:
            Preserved value or None if no data preserved
        """
        return self._preserved_data.get(field_id)

    def clear_preserved_data(self, field_id: str = None) -> None:
        """
        Clear preserved data for a field or all fields.

        Args:
            field_id: Specific field to clear, or None to clear all
        """
        if field_id:
            self._preserved_data.pop(field_id, None)
            self._preserved_formats.pop(field_id, None)
            logger.debug(f"Cleared preserved data for field: {field_id}")
        else:
            self._preserved_data.clear()
            self._preserved_formats.clear()
            logger.debug("Cleared all preserved field data")

    def reset_visibility(self) -> None:
        """Reset all fields to visible state."""
        self._hidden_fields.clear()
        logger.info("All fields reset to visible")

    def get_state_dict(self) -> Dict:
        """
        Get current state as dictionary for saving.

        Returns:
            Dictionary containing hidden fields and preserved data
        """
        return {
            'hidden_fields': list(self._hidden_fields),
            'preserved_data': self._preserved_data.copy(),
            'preserved_formats': self._preserved_formats.copy()
        }

    def load_state_dict(self, state: Dict) -> None:
        """
        Load state from dictionary.

        Args:
            state: Dictionary containing hidden fields and preserved data
        """
        self.set_hidden_fields(state.get('hidden_fields', []))
        self._preserved_data = state.get('preserved_data', {}).copy()
        self._preserved_formats = state.get('preserved_formats', {}).copy()
        logger.info(f"Loaded field state: {len(self._hidden_fields)} hidden fields")


# Global instance for application-wide use
field_state_manager = FieldStateManager()
