"""
Field name validation framework for the DJ Timeline application.
Ensures custom field names meet requirements and don't conflict.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set


class ValidationLevel(Enum):
    """Validation result levels."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    level: ValidationLevel
    message: str
    field_name: Optional[str] = None
    suggestion: Optional[str] = None


class FieldNameValidator:
    """Validates custom field names according to application rules."""

    # Maximum length for field names
    MAX_LENGTH = 13

    # Characters that are not allowed
    FORBIDDEN_CHARS = [' ', '\t', '\n', '\r']

    # Reserved names that cannot be used (system fields)
    RESERVED_NAMES = {
        'DAG', 'INLAGD', 'STARTDATUM', 'SLUTDATUM',
        'STARTTID', 'SLUTTID', 'HÄNDELSE'
    }

    def __init__(self):
        self.current_names: Set[str] = set()

    def validate_single_name(self, name: str, original_name: str = None, context_names: set = None) -> List[ValidationResult]:
        """Validate a single field name.

        Args:
            name: The field name to validate
            original_name: The original field name (for edit operations)
            context_names: Optional set of current field names for real-time duplicate checking
        """
        results = []

        # Empty name check
        if not name or not name.strip():
            results.append(ValidationResult(
                ValidationLevel.ERROR,
                "Fältnamn kan inte vara tomt",
                field_name=original_name
            ))
            return results

        name = name.strip()

        # Length validation
        if len(name) > self.MAX_LENGTH:
            results.append(ValidationResult(
                ValidationLevel.ERROR,
                f"Fältnamn för långt: {len(name)} tecken (max {self.MAX_LENGTH})",
                field_name=original_name,
                suggestion=name[:self.MAX_LENGTH]
            ))

        # Character validation
        forbidden_found = [char for char in self.FORBIDDEN_CHARS if char in name]
        if forbidden_found:
            char_names = []
            for char in forbidden_found:
                if char == ' ':
                    char_names.append('mellanslag')
                elif char == '\t':
                    char_names.append('tabb')
                elif char in ['\n', '\r']:
                    char_names.append('radbrytning')
                else:
                    char_names.append(f"'{char}'")

            results.append(ValidationResult(
                ValidationLevel.ERROR,
                f"Otillåtna tecken: {', '.join(char_names)}",
                field_name=original_name,
                suggestion=self._clean_name(name)
            ))

        # Reserved name validation
        if name.upper() in self.RESERVED_NAMES:
            results.append(ValidationResult(
                ValidationLevel.ERROR,
                f"Reserverat systemnamn: {name}",
                field_name=original_name,
                suggestion=f"{name}_2"
            ))

        # Duplicate validation (exclude the current field being edited)
        # Use context_names if provided (for real-time validation), otherwise use stored current_names
        names_to_check = context_names if context_names is not None else self.current_names
        if name in names_to_check and name != original_name:
            results.append(ValidationResult(
                ValidationLevel.ERROR,
                f"Fältnamn redan använt: {name}",
                field_name=original_name,
                suggestion=self._suggest_unique_name(name)
            ))

        # Success case
        if not results:
            results.append(ValidationResult(
                ValidationLevel.SUCCESS,
                "Giltigt fältnamn",
                field_name=original_name
            ))

        return results

    def validate_all_names(self, field_names: Dict[str, str]) -> List[ValidationResult]:
        """Validate all field names together for consistency."""
        results = []
        name_counts: Dict[str, int] = {}

        # Update current names for duplicate checking
        self.current_names = set(field_names.values())

        # Check each field individually
        for internal_id, display_name in field_names.items():
            field_results = self.validate_single_name(display_name, internal_id)
            results.extend(field_results)

            # Count occurrences for duplicate detection
            if display_name:
                name_counts[display_name] = name_counts.get(display_name, 0) + 1

        # Additional duplicate checking across all fields
        for name, count in name_counts.items():
            if count > 1:
                results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    f"Fältnamn '{name}' används {count} gånger",
                    suggestion="Använd unika namn för varje fält"
                ))

        return results

    def is_valid_configuration(self, field_names: Dict[str, str]) -> bool:
        """Check if the entire field configuration is valid."""
        results = self.validate_all_names(field_names)
        return all(result.level != ValidationLevel.ERROR for result in results)

    def get_validation_summary(self, field_names: Dict[str, str]) -> Dict[str, List[str]]:
        """Get a summary of validation results grouped by level."""
        results = self.validate_all_names(field_names)

        summary = {
            'errors': [],
            'warnings': [],
            'success': []
        }

        for result in results:
            message = result.message
            if result.field_name:
                message = f"{result.field_name}: {message}"

            if result.level == ValidationLevel.ERROR:
                summary['errors'].append(message)
            elif result.level == ValidationLevel.WARNING:
                summary['warnings'].append(message)
            else:
                summary['success'].append(message)

        return summary

    def suggest_corrections(self, invalid_name: str) -> List[str]:
        """Suggest corrections for an invalid field name."""
        suggestions = []

        # Clean the name
        cleaned = self._clean_name(invalid_name)
        if cleaned != invalid_name and len(cleaned) <= self.MAX_LENGTH:
            suggestions.append(cleaned)

        # Truncate if too long
        if len(invalid_name) > self.MAX_LENGTH:
            truncated = invalid_name[:self.MAX_LENGTH]
            if truncated not in suggestions:
                suggestions.append(truncated)

        # Add numbers for duplicates
        base_name = cleaned if cleaned else invalid_name[:self.MAX_LENGTH]
        for i in range(2, 10):
            numbered = f"{base_name[:-len(str(i))]}{i}" if len(base_name) + len(str(i)) > self.MAX_LENGTH else f"{base_name}{i}"
            if numbered not in self.current_names and len(numbered) <= self.MAX_LENGTH:
                suggestions.append(numbered)
                break

        return suggestions

    def _clean_name(self, name: str) -> str:
        """Clean a field name by removing forbidden characters."""
        cleaned = name
        for char in self.FORBIDDEN_CHARS:
            cleaned = cleaned.replace(char, '')
        return cleaned.strip()

    def _suggest_unique_name(self, base_name: str) -> str:
        """Suggest a unique name based on the given name."""
        # Try adding numbers
        for i in range(2, 100):
            if len(base_name) + len(str(i)) <= self.MAX_LENGTH:
                suggestion = f"{base_name}{i}"
            else:
                # Truncate and add number
                max_base_len = self.MAX_LENGTH - len(str(i))
                suggestion = f"{base_name[:max_base_len]}{i}"

            if suggestion not in self.current_names:
                return suggestion

        # Fallback - truncate and add suffix
        return f"{base_name[:10]}NEW"


class RealTimeValidator:
    """Provides real-time validation feedback for UI components."""

    def __init__(self, validator: FieldNameValidator):
        self.validator = validator

    def get_instant_feedback(self, name: str, original_name: str = None) -> Dict[str, any]:
        """Get instant validation feedback for UI styling."""
        results = self.validator.validate_single_name(name, original_name)

        has_errors = any(r.level == ValidationLevel.ERROR for r in results)
        has_warnings = any(r.level == ValidationLevel.WARNING for r in results)

        feedback = {
            'is_valid': not has_errors,
            'has_warnings': has_warnings,
            'color': 'red' if has_errors else ('orange' if has_warnings else 'green'),
            'messages': [r.message for r in results],
            'suggestions': [r.suggestion for r in results if r.suggestion],
            'char_count': len(name),
            'char_limit': FieldNameValidator.MAX_LENGTH
        }

        return feedback

    def get_instant_feedback_with_context(self, name: str, original_name: str = None,
                                        current_context: Dict[str, str] = None) -> Dict[str, any]:
        """Get instant validation feedback with real-time context for duplicate detection.

        Args:
            name: The field name to validate
            original_name: The original field name (for edit operations)
            current_context: Dict of all current field values for real-time duplicate checking
        """
        # Build context names set from current values (exclude empty values)
        context_names = set()
        if current_context:
            for field_id, field_value in current_context.items():
                if field_value and field_value.strip():
                    # Don't include the field being edited in the context
                    if field_id != original_name:
                        context_names.add(field_value.strip())

        results = self.validator.validate_single_name(name, original_name, context_names)

        has_errors = any(r.level == ValidationLevel.ERROR for r in results)
        has_warnings = any(r.level == ValidationLevel.WARNING for r in results)

        feedback = {
            'is_valid': not has_errors,
            'has_warnings': has_warnings,
            'color': 'red' if has_errors else ('orange' if has_warnings else 'green'),
            'messages': [r.message for r in results],
            'suggestions': [r.suggestion for r in results if r.suggestion],
            'char_count': len(name),
            'char_limit': FieldNameValidator.MAX_LENGTH
        }

        return feedback


# Global validator instance
field_validator = FieldNameValidator()
realtime_validator = RealTimeValidator(field_validator)
