"""
Comprehensive tests for ConfigManager module - Phase 1 Autonomous Testing
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_file = os.path.join(self.temp_dir, "test_config.json")

    def teardown_method(self):
        """Cleanup test fixtures"""
        try:
            if os.path.exists(self.temp_config_file):
                os.unlink(self.temp_config_file)
            os.rmdir(self.temp_dir)
        except (FileNotFoundError, OSError):
            pass

    @patch('core.config.CONFIG_FILE', 'test_config.json')
    def test_init(self):
        """Test ConfigManager initialization"""
        manager = ConfigManager()
        assert str(manager.config_file) == 'test_config.json'
        assert manager.default_config is not None
        assert isinstance(manager.default_config, dict)

    def test_default_config_structure(self):
        """Test that default config has all required keys"""
        manager = ConfigManager()
        expected_keys = {
            "excel_file", "last_pdf_dir", "window_geometry", "theme",
            "output_folder", "output_folder_locked", "text_font_size",
            "locked_fields", "locked_field_contents", "locked_field_formats"
        }
        assert set(manager.default_config.keys()) == expected_keys

    def test_default_config_values(self):
        """Test default config values"""
        manager = ConfigManager()
        config = manager.default_config

        assert config["excel_file"] == ""
        assert config["last_pdf_dir"] == ""
        assert config["window_geometry"] == "1800x1400"
        assert config["theme"] == "simplex"
        assert config["output_folder"] == ""
        assert config["output_folder_locked"] is False
        assert config["text_font_size"] == 9
        assert config["locked_fields"] == {}
        assert config["locked_field_contents"] == {}
        assert config["locked_field_formats"] == {}

    @patch.object(Path, 'exists')
    def test_load_config_file_not_exists(self, mock_exists):
        """Test loading config when file doesn't exist"""
        mock_exists.return_value = False

        manager = ConfigManager()
        config = manager.load_config()

        assert config == manager.default_config

    @patch('builtins.open', new_callable=mock_open, read_data='{"excel_file": "test.xlsx", "theme": "custom"}')
    @patch.object(Path, 'exists')
    def test_load_config_file_exists(self, mock_exists, mock_file):
        """Test loading config from existing file"""
        mock_exists.return_value = True

        manager = ConfigManager()
        config = manager.load_config()

        # Should merge with default config
        assert config["excel_file"] == "test.xlsx"
        assert config["theme"] == "custom"
        # Default values should still be present
        assert config["last_pdf_dir"] == ""
        assert config["text_font_size"] == 9

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch.object(Path, 'exists')
    def test_load_config_invalid_json(self, mock_exists, mock_file):
        """Test loading config with invalid JSON"""
        mock_exists.return_value = True

        manager = ConfigManager()
        config = manager.load_config()

        # Should return default config
        assert config == manager.default_config

    @patch('builtins.open', side_effect=OSError("Permission denied"))
    @patch.object(Path, 'exists')
    def test_load_config_file_error(self, mock_exists, mock_file):
        """Test loading config with file read error"""
        mock_exists.return_value = True

        manager = ConfigManager()
        config = manager.load_config()

        # Should return default config
        assert config == manager.default_config

    @patch('builtins.open', new_callable=mock_open)
    def test_save_config_success(self, mock_file):
        """Test successful config saving"""
        manager = ConfigManager()
        test_config = {"excel_file": "test.xlsx", "theme": "dark"}

        manager.save_config(test_config)

        mock_file.assert_called_once()
        # Verify JSON was written (we can't easily check exact content due to formatting)
        mock_file().write.assert_called()

    @patch('builtins.open', side_effect=OSError("Disk full"))
    def test_save_config_error(self, mock_file):
        """Test config saving with file write error"""
        manager = ConfigManager()
        test_config = {"excel_file": "test.xlsx"}

        # Should not raise exception
        manager.save_config(test_config)

    def test_save_config_with_real_file(self):
        """Test config saving with real file"""
        # Use a real temporary file for this test
        manager = ConfigManager()
        manager.config_file = Path(self.temp_config_file)  # Set instance attribute directly

        test_config = {
            "excel_file": "real_test.xlsx",
            "theme": "bootstrap",
            "text_font_size": 12,
            "locked_fields": {"field1": True}
        }

        manager.save_config(test_config)

        # Verify file was written
        assert os.path.exists(self.temp_config_file)

        # Load and verify content
        with open(self.temp_config_file, encoding='utf-8') as f:
            saved_config = json.load(f)

        assert saved_config["excel_file"] == "real_test.xlsx"
        assert saved_config["theme"] == "bootstrap"
        assert saved_config["text_font_size"] == 12
        assert saved_config["locked_fields"]["field1"] is True

    def test_load_config_with_real_file(self):
        """Test config loading with real file"""
        # Create a test config file
        test_config = {
            "excel_file": "loaded_test.xlsx",
            "window_geometry": "1600x1200",
            "locked_fields": {"field1": True, "field2": False}
        }

        with open(self.temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2)

        # Load with real file
        manager = ConfigManager()
        manager.config_file = Path(self.temp_config_file)  # Set instance attribute directly

        loaded_config = manager.load_config()

        # Should merge with defaults
        assert loaded_config["excel_file"] == "loaded_test.xlsx"
        assert loaded_config["window_geometry"] == "1600x1200"
        assert loaded_config["locked_fields"]["field1"] is True
        assert loaded_config["locked_fields"]["field2"] is False
        # Default values should be present
        assert loaded_config["theme"] == "simplex"
        assert loaded_config["text_font_size"] == 9

    @patch.object(ConfigManager, 'load_config')
    @patch.object(ConfigManager, 'save_config')
    def test_save_locked_fields_success(self, mock_save, mock_load):
        """Test successful locked fields saving"""
        mock_load.return_value = {"excel_file": "test.xlsx"}

        manager = ConfigManager()
        locked_states = {"field1": True, "field2": False}
        locked_contents = {"field1": "content1", "field2": "content2"}
        locked_formats = {"field1": {"bold": True}}

        manager.save_locked_fields(locked_states, locked_contents, locked_formats)

        # Verify save_config was called with updated data
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0][0]  # First argument to save_config
        assert call_args["locked_fields"] == locked_states
        assert call_args["locked_field_contents"] == locked_contents
        assert call_args["locked_field_formats"] == locked_formats
        # Original config should be preserved
        assert call_args["excel_file"] == "test.xlsx"

    @patch.object(ConfigManager, 'load_config')
    @patch.object(ConfigManager, 'save_config')
    def test_save_locked_fields_without_formats(self, mock_save, mock_load):
        """Test locked fields saving without formats"""
        mock_load.return_value = {"theme": "dark"}

        manager = ConfigManager()
        locked_states = {"field1": True}
        locked_contents = {"field1": "content1"}

        manager.save_locked_fields(locked_states, locked_contents)

        mock_save.assert_called_once()
        call_args = mock_save.call_args[0][0]
        assert call_args["locked_fields"] == locked_states
        assert call_args["locked_field_contents"] == locked_contents
        # locked_field_formats should not be updated when None
        assert "locked_field_formats" not in call_args or call_args["locked_field_formats"] == {}

    @patch.object(ConfigManager, 'load_config', side_effect=Exception("Load error"))
    def test_save_locked_fields_error(self, mock_load):
        """Test locked fields saving with error"""
        manager = ConfigManager()
        locked_states = {"field1": True}
        locked_contents = {"field1": "content1"}

        # Should not raise exception
        manager.save_locked_fields(locked_states, locked_contents)

    @patch.object(ConfigManager, 'load_config')
    def test_load_locked_fields_success(self, mock_load):
        """Test successful locked fields loading"""
        mock_config = {
            "locked_fields": {"field1": True, "field2": False},
            "locked_field_contents": {"field1": "content1", "field2": "content2"},
            "locked_field_formats": {"field1": {"bold": True}},
            "theme": "bootstrap"
        }
        mock_load.return_value = mock_config

        manager = ConfigManager()
        states, contents, formats = manager.load_locked_fields()

        assert states == {"field1": True, "field2": False}
        assert contents == {"field1": "content1", "field2": "content2"}
        assert formats == {"field1": {"bold": True}}

    @patch.object(ConfigManager, 'load_config')
    def test_load_locked_fields_missing_keys(self, mock_load):
        """Test locked fields loading with missing keys"""
        mock_config = {"theme": "bootstrap"}  # No locked field keys
        mock_load.return_value = mock_config

        manager = ConfigManager()
        states, contents, formats = manager.load_locked_fields()

        assert states == {}
        assert contents == {}
        assert formats == {}

    @patch.object(ConfigManager, 'load_config', side_effect=Exception("Load error"))
    def test_load_locked_fields_error(self, mock_load):
        """Test locked fields loading with error"""
        manager = ConfigManager()
        states, contents, formats = manager.load_locked_fields()

        # Should return empty dicts
        assert states == {}
        assert contents == {}
        assert formats == {}

    def test_config_encoding_utf8(self):
        """Test that config files are saved/loaded with UTF-8 encoding"""
        # Create config with Swedish characters
        test_config = {
            "excel_file": "test_åäö.xlsx",
            "locked_field_contents": {"Händelse": "Innehåll med åäö"}
        }

        manager = ConfigManager()
        manager.config_file = Path(self.temp_config_file)
        manager.save_config(test_config)

        # Load and verify Swedish characters are preserved
        loaded_config = manager.load_config()

        assert loaded_config["excel_file"] == "test_åäö.xlsx"
        assert loaded_config["locked_field_contents"]["Händelse"] == "Innehåll med åäö"

    def test_locked_fields_integration(self):
        """Test complete integration of locked fields saving and loading"""
        manager = ConfigManager()
        manager.config_file = Path(self.temp_config_file)

        # Save locked fields data
        locked_states = {"Händelse": True, "Note1": False}
        locked_contents = {"Händelse": "Låst innehåll", "Note1": ""}
        locked_formats = {"Händelse": {"font_size": 12, "bold": True}}

        manager.save_locked_fields(locked_states, locked_contents, locked_formats)

        # Create new manager instance to test loading
        manager2 = ConfigManager()
        manager2.config_file = Path(self.temp_config_file)

        states, contents, formats = manager2.load_locked_fields()

        assert states == locked_states
        assert contents == locked_contents
        assert formats == locked_formats

    def test_config_file_path_handling(self):
        """Test that config file path is handled correctly"""
        with patch('core.config.CONFIG_FILE', 'custom_config.json'):
            manager = ConfigManager()
            assert str(manager.config_file) == 'custom_config.json'
            assert isinstance(manager.config_file, Path)

    def test_large_config_data(self):
        """Test handling of large configuration data"""
        manager = ConfigManager()
        manager.config_file = Path(self.temp_config_file)

        # Create large config data
        large_content = "x" * 10000  # 10KB string
        test_config = {
            "excel_file": "test.xlsx",
            "locked_field_contents": {"large_field": large_content}
        }

        manager.save_config(test_config)
        loaded_config = manager.load_config()

        assert loaded_config["locked_field_contents"]["large_field"] == large_content
        assert len(loaded_config["locked_field_contents"]["large_field"]) == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
