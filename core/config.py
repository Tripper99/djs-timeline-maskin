"""
Configuration management for the DJ Timeline application
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils.constants import CONFIG_FILE, UPDATE_CHECK_DEFAULTS

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration"""

    def __init__(self):
        self.config_file = self._get_config_file_path()
        self._ensure_config_directory_exists()
        self._migrate_old_config_if_needed()
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
            "field_visibility": {},  # Store field visibility states (field_id: True/False)
            "disabled_fields": [],  # List of disabled field IDs
            "hidden_fields": [],  # Backward compatibility - aliases disabled_fields
            "active_template": "",  # Currently active template name
            "config_version": "2.6.18",  # Track config version for migrations
            # Update check configuration
            **UPDATE_CHECK_DEFAULTS
        }

    def _get_config_file_path(self) -> Path:
        """
        Get the configuration file path using platform-specific directory.
        Uses same base directory as templates for consistency.

        Returns:
            Path: Absolute path to config file
        """
        # Use APPDATA on Windows
        appdata = os.environ.get('APPDATA')
        if appdata:
            base_dir = Path(appdata) / "DJs Timeline Machine"
        else:
            # Fallback to user home directory (Linux/macOS)
            base_dir = Path.home() / ".djs_timeline_machine"

        config_path = base_dir / CONFIG_FILE
        logger.info(f"Config file path: {config_path}")
        return config_path

    def _ensure_config_directory_exists(self) -> None:
        """Ensure the config directory exists."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Config directory ensured: {self.config_file.parent}")
        except Exception as e:
            logger.error(f"Failed to create config directory: {e}")

    def _migrate_old_config_if_needed(self) -> None:
        """
        Migrate config file from old relative path location to new absolute path.
        This handles the transition for existing users.
        """
        # If new location already has config, no migration needed
        if self.config_file.exists():
            logger.info("Config file already exists at new location")
            return

        # Check for old config file in current working directory
        old_config_path = Path(CONFIG_FILE)
        if old_config_path.exists() and old_config_path.is_file():
            try:
                # Copy old config to new location
                import shutil
                shutil.copy2(old_config_path, self.config_file)
                logger.info(f"Migrated config from {old_config_path} to {self.config_file}")

                # Optionally, rename old file to indicate it's been migrated
                backup_path = old_config_path.with_suffix('.json.old')
                old_config_path.rename(backup_path)
                logger.info(f"Renamed old config to {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to migrate old config file: {e}")

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

    def save_field_state(self, disabled_fields: list) -> None:
        """Save field state configuration"""
        try:
            current_config = self.load_config()
            current_config["disabled_fields"] = disabled_fields
            # Keep both keys for backward compatibility
            current_config["hidden_fields"] = disabled_fields
            # Also update field_visibility dict for backward compatibility
            current_config["field_visibility"] = {
                field_id: field_id not in disabled_fields
                for field_id in disabled_fields
            }
            self.save_config(current_config)
            logger.info(f"Saved field state: {len(disabled_fields)} disabled fields")
        except Exception as e:
            logger.error(f"Failed to save field state: {e}")

    # Backward compatibility alias
    def save_field_visibility(self, hidden_fields: list) -> None:
        """Backward compatibility alias for save_field_state."""
        self.save_field_state(hidden_fields)

    def load_field_state(self) -> list:
        """Load field state configuration"""
        try:
            config = self.load_config()
            # Support both new and old key names for backward compatibility
            disabled_fields = config.get("disabled_fields", config.get("hidden_fields", []))
            logger.info(f"Loaded field state: {len(disabled_fields)} disabled fields")
            return disabled_fields
        except Exception as e:
            logger.error(f"Failed to load field state: {e}")
            return []

    # Backward compatibility alias
    def load_field_visibility(self) -> list:
        """Backward compatibility alias for load_field_state."""
        return self.load_field_state()

    def save_active_template(self, template_name: str) -> None:
        """Save the active template name"""
        try:
            current_config = self.load_config()
            current_config["active_template"] = template_name
            self.save_config(current_config)
            logger.info(f"Saved active template: {template_name}")
        except Exception as e:
            logger.error(f"Failed to save active template: {e}")

    def load_active_template(self) -> str:
        """Load the active template name"""
        try:
            config = self.load_config()
            return config.get("active_template", "")
        except Exception as e:
            logger.error(f"Failed to load active template: {e}")
            return ""

    def clear_config(self) -> None:
        """Clear/delete the configuration file"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
                logger.info("Configuration file deleted")
        except Exception as e:
            logger.error(f"Failed to delete config file: {e}")

    # Update check configuration methods
    def save_update_check_config(self, enabled: bool = None, skip_versions: List[str] = None,
                                 last_check: str = None) -> None:
        """Save update check configuration"""
        try:
            current_config = self.load_config()

            if enabled is not None:
                current_config["update_check_enabled"] = enabled
            if skip_versions is not None:
                current_config["skip_versions"] = skip_versions
            if last_check is not None:
                current_config["last_update_check"] = last_check

            self.save_config(current_config)
            logger.info("Saved update check configuration")
        except Exception as e:
            logger.error(f"Failed to save update check config: {e}")

    def load_update_check_config(self) -> Dict[str, Any]:
        """Load update check configuration"""
        try:
            config = self.load_config()
            return {
                "enabled": config.get("update_check_enabled", UPDATE_CHECK_DEFAULTS["update_check_enabled"]),
                "skip_versions": config.get("skip_versions", UPDATE_CHECK_DEFAULTS["skip_versions"]),
                "last_check": config.get("last_update_check", UPDATE_CHECK_DEFAULTS["last_update_check"]),
                "interval_days": config.get("auto_check_interval_days", UPDATE_CHECK_DEFAULTS["auto_check_interval_days"]),
                "timeout_seconds": config.get("github_timeout_seconds", UPDATE_CHECK_DEFAULTS["github_timeout_seconds"])
            }
        except Exception as e:
            logger.error(f"Failed to load update check config: {e}")
            return {
                "enabled": False,
                "skip_versions": [],
                "last_check": "",
                "interval_days": 7,
                "timeout_seconds": 10
            }

    def add_skipped_version(self, version: str) -> None:
        """Add a version to the skip list"""
        try:
            current_config = self.load_config()
            skip_versions = current_config.get("skip_versions", [])

            if version not in skip_versions:
                skip_versions.append(version)
                current_config["skip_versions"] = skip_versions
                self.save_config(current_config)
                logger.info(f"Added version {version} to skip list")
        except Exception as e:
            logger.error(f"Failed to add skipped version: {e}")

    def remove_skipped_version(self, version: str) -> None:
        """Remove a version from the skip list"""
        try:
            current_config = self.load_config()
            skip_versions = current_config.get("skip_versions", [])

            if version in skip_versions:
                skip_versions.remove(version)
                current_config["skip_versions"] = skip_versions
                self.save_config(current_config)
                logger.info(f"Removed version {version} from skip list")
        except Exception as e:
            logger.error(f"Failed to remove skipped version: {e}")

    def update_last_check_time(self, timestamp: str) -> None:
        """Update the timestamp of the last update check"""
        try:
            current_config = self.load_config()
            current_config["last_update_check"] = timestamp
            self.save_config(current_config)
            logger.debug(f"Updated last check time: {timestamp}")
        except Exception as e:
            logger.error(f"Failed to update last check time: {e}")

    def migrate_config(self, config: Dict) -> Dict:
        """Migrate configuration to latest version"""
        current_version = config.get("config_version", "2.2.15")

        if current_version < "2.3.0":
            # Add new fields for v2.3.0
            config.setdefault("custom_field_names", {})
            config["config_version"] = "2.3.0"
            logger.info("Migrated config to v2.3.0")

        if current_version < "2.5.0":
            # Add new fields for v2.5.0 (field visibility and templates)
            config.setdefault("field_visibility", {})
            config.setdefault("hidden_fields", [])
            config.setdefault("active_template", "")
            config["config_version"] = "2.5.0"
            logger.info("Migrated config to v2.5.0")

        if current_version < "2.5.2":
            # Add new fields for v2.5.2 (disabled fields terminology)
            # Migrate hidden_fields to disabled_fields
            hidden_fields = config.get("hidden_fields", [])
            config.setdefault("disabled_fields", hidden_fields)
            # Keep hidden_fields for backward compatibility
            config["config_version"] = "2.5.2"
            logger.info("Migrated config to v2.5.2 - added disabled fields support")

        if current_version < "2.6.17":
            # Add new fields for v2.6.17 (update check configuration)
            for key, value in UPDATE_CHECK_DEFAULTS.items():
                config.setdefault(key, value)
            config["config_version"] = "2.6.17"
            logger.info("Migrated config to v2.6.17 - added update check support")

        if current_version < "2.6.18":
            # v2.6.18: Config file now uses absolute path (Linux AppImage/Windows .exe persistence fix)
            # Migration of file location is handled by _migrate_old_config_if_needed()
            config["config_version"] = "2.6.18"
            logger.info("Migrated config to v2.6.18 - using absolute path for config file")

        return config
