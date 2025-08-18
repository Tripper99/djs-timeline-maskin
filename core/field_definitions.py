"""
Field definitions and management for the DJ Timeline application.
Separates internal field IDs from user-configurable display names.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class FieldType(Enum):
    """Types of fields for validation and display purposes."""
    ENTRY = "entry"          # Short text input
    TEXT = "text"            # Long text input (1000 chars)
    DATE = "date"            # Date field with validation
    TIME = "time"            # Time field with validation
    AUTO = "auto"            # Auto-filled field
    FORMULA = "formula"      # Formula-calculated field


@dataclass
class FieldDefinition:
    """Definition of a field with its properties."""
    internal_id: str
    default_display_name: str
    field_type: FieldType
    column_group: str
    protected: bool = False
    max_chars: Optional[int] = None
    description: str = ""


# Core field definitions with internal IDs that never change
FIELD_DEFINITIONS: Dict[str, FieldDefinition] = {
    # Protected fields (cannot be renamed)
    'startdatum': FieldDefinition(
        internal_id='startdatum',
        default_display_name='Startdatum',
        field_type=FieldType.DATE,
        column_group='column1',
        protected=True,
        description='Startdatum för händelsen (format: YYYY-MM-DD)'
    ),
    'slutdatum': FieldDefinition(
        internal_id='slutdatum',
        default_display_name='Slutdatum',
        field_type=FieldType.DATE,
        column_group='column1',
        protected=True,
        description='Slutdatum för händelsen (format: YYYY-MM-DD)'
    ),
    'starttid': FieldDefinition(
        internal_id='starttid',
        default_display_name='Starttid',
        field_type=FieldType.TIME,
        column_group='column1',
        protected=True,
        description='Starttid för händelsen (format: HH:MM)'
    ),
    'sluttid': FieldDefinition(
        internal_id='sluttid',
        default_display_name='Sluttid',
        field_type=FieldType.TIME,
        column_group='column1',
        protected=True,
        description='Sluttid för händelsen (format: HH:MM)'
    ),
    'inlagd': FieldDefinition(
        internal_id='inlagd',
        default_display_name='Inlagd',
        field_type=FieldType.AUTO,
        column_group='column1',
        protected=True,
        description='Datum då posten lades till (automatiskt ifylld)'
    ),
    'dag': FieldDefinition(
        internal_id='dag',
        default_display_name='Dag',
        field_type=FieldType.FORMULA,
        column_group='column1',
        protected=True,
        description='Veckodag baserad på startdatum (automatiskt beräknad)'
    ),
    'handelse': FieldDefinition(
        internal_id='handelse',
        default_display_name='Händelse',
        field_type=FieldType.TEXT,
        column_group='column2',
        protected=True,
        max_chars=1000,
        description='Huvudbeskrivning av händelsen (textfält med 1000 tecken)'
    ),

    # Renamable fields
    'obs': FieldDefinition(
        internal_id='obs',
        default_display_name='OBS',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Observationer (kort textfält)'
    ),
    'kategori': FieldDefinition(
        internal_id='kategori',
        default_display_name='Kategori',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Kategori för händelsen (kort textfält)'
    ),
    'underkategori': FieldDefinition(
        internal_id='underkategori',
        default_display_name='Underkategori',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Underkategori för händelsen (kort textfält)'
    ),
    'person_sak': FieldDefinition(
        internal_id='person_sak',
        default_display_name='Person/sak',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Person eller sak relaterad till händelsen (kort textfält)'
    ),
    'special': FieldDefinition(
        internal_id='special',
        default_display_name='Special',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Specialinformation (kort textfält)'
    ),
    'kalla1': FieldDefinition(
        internal_id='kalla1',
        default_display_name='Källa',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=True,
        description='Första källreferens (kort textfält)'
    ),
    'kalla2': FieldDefinition(
        internal_id='kalla2',
        default_display_name='Källa2',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Andra källreferens (kort textfält)'
    ),
    'kalla3': FieldDefinition(
        internal_id='kalla3',
        default_display_name='Källa3',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Tredje källreferens (kort textfält)'
    ),
    'ovrigt': FieldDefinition(
        internal_id='ovrigt',
        default_display_name='Övrigt',
        field_type=FieldType.ENTRY,
        column_group='column1',
        protected=False,
        description='Övrig information (kort textfält)'
    ),
    'note1': FieldDefinition(
        internal_id='note1',
        default_display_name='Note1',
        field_type=FieldType.TEXT,
        column_group='column3',
        protected=False,
        max_chars=1000,
        description='Första anteckningsfält (textfält med 1000 tecken)'
    ),
    'note2': FieldDefinition(
        internal_id='note2',
        default_display_name='Note2',
        field_type=FieldType.TEXT,
        column_group='column3',
        protected=False,
        max_chars=1000,
        description='Andra anteckningsfält (textfält med 1000 tecken)'
    ),
    'note3': FieldDefinition(
        internal_id='note3',
        default_display_name='Note3',
        field_type=FieldType.TEXT,
        column_group='column3',
        protected=False,
        max_chars=1000,
        description='Tredje anteckningsfält (textfält med 1000 tecken)'
    ),
}

# Field order for Excel columns (maintaining compatibility with REQUIRED_EXCEL_COLUMNS)
FIELD_ORDER = [
    'obs', 'inlagd', 'kategori', 'underkategori', 'person_sak', 'special',
    'handelse', 'dag', 'startdatum', 'starttid', 'slutdatum', 'sluttid',
    'note1', 'note2', 'note3', 'kalla1', 'kalla2', 'kalla3', 'ovrigt'
]

# Two-column layout order for field configuration dialog (matching main window)
LEFT_COLUMN_ORDER = [
    'obs', 'inlagd', 'kategori', 'underkategori', 'person_sak', 'special',
    'dag', 'startdatum', 'starttid', 'slutdatum', 'sluttid'
]

RIGHT_COLUMN_ORDER = [
    'kalla1', 'kalla2', 'kalla3', 'ovrigt',
    'handelse', 'note1', 'note2', 'note3'
]

# Fields that cannot be disabled (required for basic functionality)
REQUIRED_ENABLED_FIELDS = ['startdatum', 'kalla1', 'handelse']
# Backward compatibility alias
REQUIRED_VISIBLE_FIELDS = REQUIRED_ENABLED_FIELDS


class FieldDefinitionManager:
    """Manages field definitions and custom field names."""

    def __init__(self):
        self._custom_names: Dict[str, str] = {}
        self._disabled_fields: set = set()  # Track disabled fields

    def get_display_name(self, internal_id: str) -> str:
        """Get the display name for a field (custom or default)."""
        if internal_id in self._custom_names:
            return self._custom_names[internal_id]

        if internal_id in FIELD_DEFINITIONS:
            return FIELD_DEFINITIONS[internal_id].default_display_name

        # Fallback to internal ID if not found
        return internal_id

    def get_internal_id(self, display_name: str) -> Optional[str]:
        """Get the internal ID for a display name."""
        # Check custom names first
        for internal_id, custom_name in self._custom_names.items():
            if custom_name == display_name:
                return internal_id

        # Check default names
        for internal_id, field_def in FIELD_DEFINITIONS.items():
            if field_def.default_display_name == display_name:
                return internal_id

        return None

    def is_protected(self, internal_id: str) -> bool:
        """Check if a field is protected (cannot be renamed)."""
        if internal_id in FIELD_DEFINITIONS:
            return FIELD_DEFINITIONS[internal_id].protected
        return False

    def get_renamable_fields(self) -> List[str]:
        """Get list of field IDs that can be renamed."""
        return [field_id for field_id, field_def in FIELD_DEFINITIONS.items()
                if not field_def.protected]

    def get_protected_fields(self) -> List[str]:
        """Get list of field IDs that are protected."""
        return [field_id for field_id, field_def in FIELD_DEFINITIONS.items()
                if field_def.protected]

    def set_custom_name(self, internal_id: str, display_name: str) -> bool:
        """Set a custom display name for a field."""
        if internal_id not in FIELD_DEFINITIONS:
            return False

        if FIELD_DEFINITIONS[internal_id].protected:
            return False

        self._custom_names[internal_id] = display_name
        return True

    def reset_to_default(self, internal_id: str) -> bool:
        """Reset a field to its default display name."""
        if internal_id in self._custom_names:
            del self._custom_names[internal_id]
            return True
        return False

    def reset_all_to_default(self) -> None:
        """Reset all fields to their default display names."""
        self._custom_names.clear()

    def get_custom_names(self) -> Dict[str, str]:
        """Get all custom field names."""
        return self._custom_names.copy()

    def set_custom_names(self, custom_names: Dict[str, str]) -> None:
        """Set multiple custom field names at once."""
        # Only set names for valid, non-protected fields
        self._custom_names.clear()
        for internal_id, display_name in custom_names.items():
            if (internal_id in FIELD_DEFINITIONS and
                not FIELD_DEFINITIONS[internal_id].protected):
                self._custom_names[internal_id] = display_name

    def get_all_display_names(self) -> List[str]:
        """Get all current display names in field order."""
        return [self.get_display_name(field_id) for field_id in FIELD_ORDER]

    def get_field_definition(self, internal_id: str) -> Optional[FieldDefinition]:
        """Get the field definition for an internal ID."""
        return FIELD_DEFINITIONS.get(internal_id)

    def get_fields_by_column(self, column_group: str) -> List[str]:
        """Get field IDs for a specific column group."""
        return [field_id for field_id, field_def in FIELD_DEFINITIONS.items()
                if field_def.column_group == column_group]

    def validate_display_names(self) -> List[str]:
        """Validate all current display names and return list of errors."""
        errors = []
        display_names = set()

        for field_id in FIELD_ORDER:
            display_name = self.get_display_name(field_id)

            # Check for duplicates
            if display_name in display_names:
                errors.append(f"Duplicate field name: {display_name}")
            display_names.add(display_name)

            # Validate custom names
            if field_id in self._custom_names:
                validation_errors = self._validate_custom_name(display_name)
                errors.extend(validation_errors)

        return errors

    def _validate_custom_name(self, name: str) -> List[str]:
        """Validate a custom field name."""
        errors = []

        if len(name) > 13:
            errors.append(f"Field name too long: {name} (max 13 characters)")

        if ' ' in name:
            errors.append(f"Field name contains spaces: {name}")

        if not name.strip():
            errors.append("Field name cannot be empty")

        return errors

    # Field state management methods
    def set_field_enabled(self, field_id: str, enabled: bool) -> bool:
        """Set field enabled state if allowed."""
        if not enabled and field_id in REQUIRED_ENABLED_FIELDS:
            return False  # Cannot disable required fields

        if enabled:
            self._disabled_fields.discard(field_id)
        else:
            self._disabled_fields.add(field_id)
        return True

    # Backward compatibility alias
    def set_field_visibility(self, field_id: str, visible: bool) -> bool:
        """Backward compatibility alias for set_field_enabled."""
        return self.set_field_enabled(field_id, visible)

    def is_field_enabled(self, field_id: str) -> bool:
        """Check if a field is enabled."""
        return field_id not in self._disabled_fields

    def is_field_disabled(self, field_id: str) -> bool:
        """Check if a field is disabled."""
        return field_id in self._disabled_fields

    # Backward compatibility aliases
    def is_field_visible(self, field_id: str) -> bool:
        """Backward compatibility alias for is_field_enabled."""
        return self.is_field_enabled(field_id)

    def is_field_hidden(self, field_id: str) -> bool:
        """Backward compatibility alias for is_field_disabled."""
        return self.is_field_disabled(field_id)

    def get_enabled_fields(self) -> List[str]:
        """Get list of enabled field IDs in order."""
        return [f for f in FIELD_ORDER if f not in self._disabled_fields]

    def get_enabled_display_names(self) -> List[str]:
        """Get display names for enabled fields only."""
        return [self.get_display_name(f) for f in self.get_enabled_fields()]

    def get_disabled_fields(self) -> List[str]:
        """Get list of disabled field IDs."""
        return list(self._disabled_fields)

    # Backward compatibility aliases
    def get_visible_fields(self) -> List[str]:
        """Backward compatibility alias for get_enabled_fields."""
        return self.get_enabled_fields()

    def get_visible_display_names(self) -> List[str]:
        """Backward compatibility alias for get_enabled_display_names."""
        return self.get_enabled_display_names()

    def get_hidden_fields(self) -> List[str]:
        """Backward compatibility alias for get_disabled_fields."""
        return self.get_disabled_fields()

    def set_disabled_fields(self, disabled_fields: List[str]) -> None:
        """Set disabled fields from a list."""
        self._disabled_fields = {
            f for f in disabled_fields
            if f not in REQUIRED_ENABLED_FIELDS
        }

    def can_disable_field(self, field_id: str) -> bool:
        """Check if a field can be disabled."""
        return field_id not in REQUIRED_ENABLED_FIELDS

    def reset_all_enabled(self) -> None:
        """Reset all fields to enabled."""
        self._disabled_fields.clear()

    # Backward compatibility aliases
    def set_hidden_fields(self, hidden_fields: List[str]) -> None:
        """Backward compatibility alias for set_disabled_fields."""
        self.set_disabled_fields(hidden_fields)

    def can_hide_field(self, field_id: str) -> bool:
        """Backward compatibility alias for can_disable_field."""
        return self.can_disable_field(field_id)

    def reset_visibility(self) -> None:
        """Backward compatibility alias for reset_all_enabled."""
        self.reset_all_enabled()


# Global instance for use throughout the application
field_manager = FieldDefinitionManager()
