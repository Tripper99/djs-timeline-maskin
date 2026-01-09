"""
Field state manager for handling field state and data preservation.
Manages which fields are disabled/enabled and preserves data when fields are disabled.
"""

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class FieldStateManager:
    """Manages field states and data preservation."""

    # Fields that cannot be disabled (required for basic functionality)
    REQUIRED_ENABLED_FIELDS = {'startdatum', 'kalla1', 'handelse'}
    # Backward compatibility alias
    REQUIRED_VISIBLE_FIELDS = REQUIRED_ENABLED_FIELDS

    def __init__(self):
        """Initialize the field state manager."""
        self._disabled_fields: Set[str] = set()
        self._preserved_data: Dict[str, str] = {}
        self._preserved_formats: Dict[str, any] = {}  # For rich text fields

    def can_disable_field(self, field_id: str) -> bool:
        """
        Check if a field can be disabled.

        Args:
            field_id: Internal field identifier

        Returns:
            True if field can be disabled, False otherwise
        """
        return field_id not in self.REQUIRED_ENABLED_FIELDS

    # Backward compatibility alias
    def can_hide_field(self, field_id: str) -> bool:
        """Backward compatibility alias for can_disable_field."""
        return self.can_disable_field(field_id)

    def disable_field(self, field_id: str, current_value: str = "", current_format: any = None) -> bool:
        """
        Disable a field while preserving its data.

        Args:
            field_id: Internal field identifier
            current_value: Current field value to preserve
            current_format: Current format data (for rich text fields)

        Returns:
            True if field was disabled, False if field cannot be disabled
        """
        if not self.can_disable_field(field_id):
            logger.warning(f"Cannot disable required field: {field_id}")
            return False

        self._disabled_fields.add(field_id)

        # Preserve data if provided
        if current_value:
            self._preserved_data[field_id] = current_value
            logger.debug(f"Preserved data for disabled field {field_id}: {len(current_value)} chars")

        if current_format:
            self._preserved_formats[field_id] = current_format
            logger.debug(f"Preserved format for disabled field {field_id}")

        logger.info(f"Field disabled: {field_id}")
        return True

    # Backward compatibility alias
    def hide_field(self, field_id: str, current_value: str = "", current_format: any = None) -> bool:
        """Backward compatibility alias for disable_field."""
        return self.disable_field(field_id, current_value, current_format)

    def enable_field(self, field_id: str) -> tuple[str, any]:
        """
        Enable a field and return any preserved data.

        Args:
            field_id: Internal field identifier

        Returns:
            Tuple of (preserved_value, preserved_format) or ("", None) if no data
        """
        self._disabled_fields.discard(field_id)

        # Return preserved data if available
        value = self._preserved_data.pop(field_id, "")
        format_data = self._preserved_formats.pop(field_id, None)

        if value:
            logger.debug(f"Restored data for enabled field {field_id}: {len(value)} chars")

        logger.info(f"Field enabled: {field_id}")
        return value, format_data

    # Backward compatibility alias
    def show_field(self, field_id: str) -> tuple[str, any]:
        """Backward compatibility alias for enable_field."""
        return self.enable_field(field_id)

    def is_field_disabled(self, field_id: str) -> bool:
        """
        Check if a field is currently disabled.

        Args:
            field_id: Internal field identifier

        Returns:
            True if field is disabled, False otherwise
        """
        return field_id in self._disabled_fields

    # Backward compatibility alias
    def is_field_hidden(self, field_id: str) -> bool:
        """Backward compatibility alias for is_field_disabled."""
        return self.is_field_disabled(field_id)

    def is_field_enabled(self, field_id: str) -> bool:
        """
        Check if a field is currently enabled.

        Args:
            field_id: Internal field identifier

        Returns:
            True if field is enabled, False otherwise
        """
        return field_id not in self._disabled_fields

    # Backward compatibility alias
    def is_field_visible(self, field_id: str) -> bool:
        """Backward compatibility alias for is_field_enabled."""
        return self.is_field_enabled(field_id)

    def get_disabled_fields(self) -> List[str]:
        """
        Get list of currently disabled field IDs.

        Returns:
            List of disabled field IDs
        """
        return list(self._disabled_fields)

    # Backward compatibility alias
    def get_hidden_fields(self) -> List[str]:
        """Backward compatibility alias for get_disabled_fields."""
        return self.get_disabled_fields()

    def get_enabled_fields(self, all_fields: List[str]) -> List[str]:
        """
        Get list of enabled field IDs from a list of all fields.

        Args:
            all_fields: List of all field IDs in order

        Returns:
            List of enabled field IDs maintaining original order
        """
        return [f for f in all_fields if f not in self._disabled_fields]

    # Backward compatibility alias
    def get_visible_fields(self, all_fields: List[str]) -> List[str]:
        """Backward compatibility alias for get_enabled_fields."""
        return self.get_enabled_fields(all_fields)

    def set_disabled_fields(self, disabled_fields: List[str]) -> None:
        """
        Set the disabled fields from a list (e.g., from config or template).

        Args:
            disabled_fields: List of field IDs to disable
        """
        # Only disable fields that can be disabled
        self._disabled_fields = {
            f for f in disabled_fields
            if self.can_disable_field(f)
        }

        # Log any fields that couldn't be disabled
        invalid = [f for f in disabled_fields if not self.can_disable_field(f)]
        if invalid:
            logger.warning(f"Cannot disable required fields: {invalid}")

    # Backward compatibility alias
    def set_hidden_fields(self, hidden_fields: List[str]) -> None:
        """Backward compatibility alias for set_disabled_fields."""
        self.set_disabled_fields(hidden_fields)

    def get_preserved_data(self, field_id: str) -> Optional[str]:
        """
        Get preserved data for a disabled field without enabling it.

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

    def reset_all_enabled(self) -> None:
        """Reset all fields to enabled state."""
        self._disabled_fields.clear()
        logger.info("All fields reset to enabled")

    # Backward compatibility alias
    def reset_visibility(self) -> None:
        """Backward compatibility alias for reset_all_enabled."""
        self.reset_all_enabled()

    def get_state_dict(self) -> Dict:
        """
        Get current state as dictionary for saving.

        Returns:
            Dictionary containing disabled fields and preserved data
        """
        return {
            'disabled_fields': list(self._disabled_fields),
            # Keep both keys for backward compatibility
            'hidden_fields': list(self._disabled_fields),
            'preserved_data': self._preserved_data.copy(),
            'preserved_formats': self._preserved_formats.copy()
        }

    def load_state_dict(self, state: Dict) -> None:
        """
        Load state from dictionary.

        Args:
            state: Dictionary containing disabled fields and preserved data
        """
        # Support both new and old key names for backward compatibility
        disabled_fields = state.get('disabled_fields', state.get('hidden_fields', []))
        self.set_disabled_fields(disabled_fields)
        self._preserved_data = state.get('preserved_data', {}).copy()
        self._preserved_formats = state.get('preserved_formats', {}).copy()
        logger.info(f"Loaded field state: {len(self._disabled_fields)} disabled fields")


# Global instance for application-wide use
field_state_manager = FieldStateManager()
