"""
Template manager for field configuration templates.
Handles saving, loading, and managing field configuration templates.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages field configuration templates."""

    DEFAULT_TEMPLATE_NAME = "Standard"
    TEMPLATE_VERSION = "1.0"

    def __init__(self):
        """Initialize the template manager."""
        self.templates_dir = self._get_templates_directory()
        self._ensure_directory_exists()
        self._ensure_default_template()

    def _get_templates_directory(self) -> Path:
        """
        Get the templates directory path.

        Returns:
            Path to templates directory
        """
        # Use APPDATA on Windows
        appdata = os.environ.get('APPDATA')
        if appdata:
            base_dir = Path(appdata) / "DJs Timeline Machine"
        else:
            # Fallback to user home directory
            base_dir = Path.home() / ".djs_timeline_machine"

        templates_dir = base_dir / "templates"
        return templates_dir

    def _ensure_directory_exists(self) -> None:
        """Ensure the templates directory exists."""
        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Templates directory: {self.templates_dir}")
        except Exception as e:
            logger.error(f"Failed to create templates directory: {e}")

    def _ensure_default_template(self) -> None:
        """Ensure default template exists."""
        default_path = self.templates_dir / f"{self.DEFAULT_TEMPLATE_NAME}.json"
        if not default_path.exists():
            self._create_default_template()

    def _create_default_template(self) -> None:
        """Create the default template with standard configuration."""
        default_config = {
            "template_name": self.DEFAULT_TEMPLATE_NAME,
            "version": self.TEMPLATE_VERSION,
            "created_date": datetime.now().isoformat(),
            "description": "Standardkonfiguration för fältnamn",
            "field_config": {
                "custom_names": {},  # Empty = use default names
                "disabled_fields": [],  # All fields enabled by default
                "hidden_fields": [],  # Backward compatibility alias for disabled_fields
            }
        }

        default_path = self.templates_dir / f"{self.DEFAULT_TEMPLATE_NAME}.json"
        try:
            with open(default_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info("Created default template")
        except Exception as e:
            logger.error(f"Failed to create default template: {e}")

    def list_templates(self) -> List[str]:
        """
        Get list of available template names.

        Returns:
            List of template names (without .json extension)
        """
        try:
            templates = []
            for file_path in self.templates_dir.glob("*.json"):
                # Validate that this is actually a template file
                # by checking if it can be loaded and has the correct structure
                try:
                    with open(file_path, encoding='utf-8') as f:
                        data = json.load(f)

                    # Check if file has the expected template structure
                    # Must have field_config with the right structure
                    if self._validate_loaded_template(data):
                        templates.append(file_path.stem)
                    else:
                        logger.debug(f"Skipping invalid template file: {file_path.name}")

                except (json.JSONDecodeError, Exception) as e:
                    logger.debug(f"Skipping non-template file {file_path.name}: {e}")
                    continue

            # Ensure default is always first
            if self.DEFAULT_TEMPLATE_NAME in templates:
                templates.remove(self.DEFAULT_TEMPLATE_NAME)
                templates.insert(0, self.DEFAULT_TEMPLATE_NAME)

            return templates
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return [self.DEFAULT_TEMPLATE_NAME]

    def save_template(self, name: str, field_config: Dict, description: str = "") -> bool:
        """
        Save a field configuration as a template.

        Args:
            name: Template name
            field_config: Dictionary with custom_names and disabled_fields
            description: Optional template description

        Returns:
            True if saved successfully, False otherwise
        """
        # Validate template name
        if not self._validate_template_name(name):
            logger.error(f"Invalid template name: {name}")
            return False

        # Validate configuration
        if not self._validate_template_config(field_config):
            logger.error("Invalid template configuration")
            return False

        # Create template data with backward compatibility
        field_config_with_compat = field_config.copy()
        # Ensure both disabled_fields and hidden_fields are present for compatibility
        if "disabled_fields" in field_config_with_compat:
            field_config_with_compat["hidden_fields"] = field_config_with_compat["disabled_fields"]
        elif "hidden_fields" in field_config_with_compat:
            field_config_with_compat["disabled_fields"] = field_config_with_compat["hidden_fields"]

        template_data = {
            "template_name": name,
            "version": self.TEMPLATE_VERSION,
            "created_date": datetime.now().isoformat(),
            "description": description,
            "field_config": field_config_with_compat
        }

        # Save to file
        file_path = self.templates_dir / f"{name}.json"

        # Create backup if template exists
        if file_path.exists():
            backup_path = file_path.with_suffix('.json.bak')
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved template: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            # Restore backup if save failed
            if file_path.exists() and backup_path.exists():
                try:
                    import shutil
                    shutil.move(backup_path, file_path)
                except Exception:
                    pass
            return False

    def load_template(self, name: str) -> Optional[Dict]:
        """
        Load a template by name.

        Args:
            name: Template name

        Returns:
            Template configuration dictionary or None if not found/invalid
        """
        file_path = self.templates_dir / f"{name}.json"

        if not file_path.exists():
            logger.error(f"Template not found: {name}")
            return None

        try:
            with open(file_path, encoding='utf-8') as f:
                template_data = json.load(f)

            # Validate loaded template
            if not self._validate_loaded_template(template_data):
                logger.error(f"Invalid template data: {name}")
                return None

            # Add backward compatibility for disabled_fields
            field_config = template_data.get('field_config', {})
            if "disabled_fields" not in field_config and "hidden_fields" in field_config:
                field_config["disabled_fields"] = field_config["hidden_fields"]
            elif "hidden_fields" not in field_config and "disabled_fields" in field_config:
                field_config["hidden_fields"] = field_config["disabled_fields"]

            logger.info(f"Loaded template: {name}")
            return field_config

        except json.JSONDecodeError as e:
            logger.error(f"Template file corrupted: {name} - {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            return None

    def delete_template(self, name: str) -> bool:
        """
        Delete a template.

        Args:
            name: Template name

        Returns:
            True if deleted successfully, False otherwise
        """
        # Don't allow deleting default template
        if name == self.DEFAULT_TEMPLATE_NAME:
            logger.warning("Cannot delete default template")
            return False

        file_path = self.templates_dir / f"{name}.json"

        if not file_path.exists():
            logger.error(f"Template not found: {name}")
            return False

        try:
            # Create backup before deletion
            backup_path = file_path.with_suffix('.json.deleted')
            import shutil
            shutil.copy2(file_path, backup_path)

            # Delete the template
            file_path.unlink()
            logger.info(f"Deleted template: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False

    def get_template_info(self, name: str) -> Optional[Dict]:
        """
        Get template metadata without loading full configuration.

        Args:
            name: Template name

        Returns:
            Template metadata or None if not found
        """
        file_path = self.templates_dir / f"{name}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding='utf-8') as f:
                template_data = json.load(f)

            return {
                'name': template_data.get('template_name', name),
                'description': template_data.get('description', ''),
                'created_date': template_data.get('created_date', ''),
                'version': template_data.get('version', 'Unknown')
            }
        except Exception as e:
            logger.error(f"Failed to get template info: {e}")
            return None

    def _validate_template_name(self, name: str) -> bool:
        """
        Validate template name.

        Args:
            name: Template name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name or not name.strip():
            return False

        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in name:
                return False

        # Check length
        if len(name) > 50:
            return False

        return True

    def _validate_template_config(self, config: Dict) -> bool:
        """
        Validate template configuration structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(config, dict):
            return False

        # Check required keys - accept either disabled_fields or hidden_fields
        if 'custom_names' not in config:
            return False

        if 'disabled_fields' not in config and 'hidden_fields' not in config:
            return False

        # Validate custom_names is a dict
        if not isinstance(config['custom_names'], dict):
            return False

        # Validate field lists are lists (support both formats)
        if 'disabled_fields' in config and not isinstance(config['disabled_fields'], list):
            return False
        if 'hidden_fields' in config and not isinstance(config['hidden_fields'], list):
            return False

        # Validate custom names values are strings
        for key, value in config['custom_names'].items():
            if not isinstance(key, str) or not isinstance(value, str):
                return False

        # Validate field lists contain only strings
        for field_list_key in ['disabled_fields', 'hidden_fields']:
            if field_list_key in config:
                for field in config[field_list_key]:
                    if not isinstance(field, str):
                        return False

        return True

    def _validate_loaded_template(self, template_data: Dict) -> bool:
        """
        Validate loaded template data.

        Args:
            template_data: Full template data from file

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(template_data, dict):
            return False

        # Check for field_config
        if 'field_config' not in template_data:
            return False

        # Validate field_config structure
        return self._validate_template_config(template_data['field_config'])

    def export_template(self, name: str, export_path: Path) -> bool:
        """
        Export a template to a specific location.

        Args:
            name: Template name
            export_path: Path where to export the template

        Returns:
            True if exported successfully, False otherwise
        """
        source_path = self.templates_dir / f"{name}.json"

        if not source_path.exists():
            logger.error(f"Template not found: {name}")
            return False

        try:
            import shutil
            shutil.copy2(source_path, export_path)
            logger.info(f"Exported template {name} to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export template: {e}")
            return False

    def import_template(self, import_path: Path, new_name: Optional[str] = None) -> bool:
        """
        Import a template from a file.

        Args:
            import_path: Path to template file to import
            new_name: Optional new name for the template

        Returns:
            True if imported successfully, False otherwise
        """
        if not import_path.exists():
            logger.error(f"Import file not found: {import_path}")
            return False

        try:
            # Load and validate template
            with open(import_path, encoding='utf-8') as f:
                template_data = json.load(f)

            if not self._validate_loaded_template(template_data):
                logger.error("Invalid template file")
                return False

            # Use new name if provided
            if new_name:
                template_data['template_name'] = new_name
                name = new_name
            else:
                name = template_data.get('template_name', import_path.stem)

            # Save as new template
            return self.save_template(
                name,
                template_data['field_config'],
                template_data.get('description', '')
            )

        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return False


# Global instance for application-wide use
template_manager = TemplateManager()
