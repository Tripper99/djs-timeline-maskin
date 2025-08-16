"""
Configuration management for the DJ Timeline application
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

from utils.constants import CONFIG_FILE

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration"""

    def __init__(self):
        self.config_file = Path(CONFIG_FILE)
        self.default_config = {
            "excel_file": "",
            "last_pdf_dir": "",
            "window_geometry": "1400x680",
            "theme": "simplex",
            "output_folder": "",  # Store output folder path for renamed PDFs
            "output_folder_locked": False,  # Store if output folder selection is locked
            "text_font_size": 9,  # Store text font size for Händelse and Note fields
            "locked_fields": {},  # Store which fields are locked (field_name: True/False)
            "locked_field_contents": {},  # Store content of locked fields (field_name: content)
            "locked_field_formats": {},  # Store rich text formatting of locked fields (field_name: format_data)
            "custom_field_names": {},  # Store custom field names (internal_id: display_name)
            "config_version": "2.3.0"  # Track config version for migrations
        }

    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults and migrate if needed
                    config = {**self.default_config, **config}
                    config = self.migrate_config(config)
                    return config
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load config: {e}")
        return self.default_config.copy()

    def save_config(self, config: Dict) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Failed to save config: {e}")

    def save_locked_fields(self, locked_states: Dict[str, bool], locked_contents: Dict[str, str], locked_formats: Dict[str, Any] = None) -> None:
        """Save locked field states, their contents, and rich text formatting"""
        try:
            # Load current config
            current_config = self.load_config()

            # Update locked fields data
            current_config["locked_fields"] = locked_states
            current_config["locked_field_contents"] = locked_contents

            # Update locked field formats if provided
            if locked_formats is not None:
                current_config["locked_field_formats"] = locked_formats

            # Save updated config
            self.save_config(current_config)
            logger.info(f"Saved locked fields: {list(locked_states.keys())}")
            if locked_formats:
                logger.info(f"Saved rich text formats for: {list(locked_formats.keys())}")

        except Exception as e:
            logger.error(f"Failed to save locked fields: {e}")

    def load_locked_fields(self) -> Tuple[Dict[str, bool], Dict[str, str], Dict[str, Any]]:
        """Load locked field states, their contents, and rich text formatting"""
        try:
            config = self.load_config()
            locked_states = config.get("locked_fields", {})
            locked_contents = config.get("locked_field_contents", {})
            locked_formats = config.get("locked_field_formats", {})

            logger.info(f"Loaded locked fields: {list(locked_states.keys())}")
            if locked_formats:
                logger.info(f"Loaded rich text formats for: {list(locked_formats.keys())}")
            return locked_states, locked_contents, locked_formats

        except Exception as e:
            logger.error(f"Failed to load locked fields: {e}")
            return {}, {}, {}

    def save_custom_field_names(self, custom_names: Dict[str, str]) -> None:
        """Save custom field names"""
        try:
            current_config = self.load_config()
            current_config["custom_field_names"] = custom_names
            self.save_config(current_config)
            logger.info(f"Saved custom field names: {custom_names}")
        except Exception as e:
            logger.error(f"Failed to save custom field names: {e}")

    def load_custom_field_names(self) -> Dict[str, str]:
        """Load custom field names"""
        try:
            config = self.load_config()
            custom_names = config.get("custom_field_names", {})
            logger.info(f"Loaded custom field names: {custom_names}")
            return custom_names
        except Exception as e:
            logger.error(f"Failed to load custom field names: {e}")
            return {}

    def clear_config(self) -> None:
        """Clear/delete the configuration file"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
                logger.info("Configuration file deleted")
        except Exception as e:
            logger.error(f"Failed to delete config file: {e}")

    def migrate_config(self, config: Dict) -> Dict:
        """Migrate configuration to latest version"""
        current_version = config.get("config_version", "2.2.15")

        if current_version < "2.3.0":
            # Add new fields for v2.3.0
            config.setdefault("custom_field_names", {})
            config["config_version"] = "2.3.0"
            logger.info("Migrated config to v2.3.0")

        return config
