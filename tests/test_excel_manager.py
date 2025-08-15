"""
Safe tests for ExcelManager module - Phase 1 Autonomous Testing
IMPORTANT: This file tests ONLY safe methods and avoids the hybrid Excel I/O system
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.excel_manager import ExcelManager


class TestExcelManagerSafe:
    """Test suite for SAFE ExcelManager functionality (avoiding hybrid methods)"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = ExcelManager()

    def test_init_without_path(self):
        """Test ExcelManager initialization without path"""
        manager = ExcelManager()
        assert manager.excel_path is None
        assert manager.workbook is None
        assert manager.worksheet is None
        assert manager.columns == {}
        assert manager.column_names == []

    def test_init_with_path(self):
        """Test ExcelManager initialization with path"""
        test_path = "test.xlsx"
        manager = ExcelManager(test_path)
        assert manager.excel_path == test_path
        assert manager.workbook is None
        assert manager.worksheet is None
        assert manager.columns == {}
        assert manager.column_names == []

    def test_get_column_names_empty(self):
        """Test get_column_names when no columns are loaded"""
        result = self.manager.get_column_names()
        assert result == []
        assert isinstance(result, list)

    def test_get_column_names_with_columns(self):
        """Test get_column_names with columns loaded (mocked)"""
        # Mock column names
        self.manager.column_names = ["Startdatum", "Händelse", "Källa1"]

        result = self.manager.get_column_names()

        assert result == ["Startdatum", "Händelse", "Källa1"]
        # Ensure it returns a copy, not the original list
        result.append("Modified")
        assert self.manager.column_names == ["Startdatum", "Händelse", "Källa1"]

    @patch('core.excel_manager.REQUIRED_EXCEL_COLUMNS', ['Col1', 'Col2', 'Col3'])
    def test_validate_excel_columns_no_file_loaded(self):
        """Test column validation when no file is loaded"""
        missing = self.manager.validate_excel_columns()
        assert missing == ['Col1', 'Col2', 'Col3']

    @patch('core.excel_manager.REQUIRED_EXCEL_COLUMNS', ['Col1', 'Col2', 'Col3'])
    def test_validate_excel_columns_all_present(self):
        """Test column validation when all required columns are present"""
        self.manager.column_names = ['Col1', 'Col2', 'Col3', 'ExtraCol']

        missing = self.manager.validate_excel_columns()
        assert missing == []

    @patch('core.excel_manager.REQUIRED_EXCEL_COLUMNS', ['Col1', 'Col2', 'Col3'])
    def test_validate_excel_columns_some_missing(self):
        """Test column validation when some required columns are missing"""
        self.manager.column_names = ['Col1', 'ExtraCol']

        missing = self.manager.validate_excel_columns()
        assert set(missing) == {'Col2', 'Col3'}

    def test_convert_color_to_hex_none(self):
        """Test color conversion with None input"""
        result = self.manager._convert_color_to_hex(None)
        assert result is None

    def test_convert_color_to_hex_empty_string(self):
        """Test color conversion with empty string"""
        result = self.manager._convert_color_to_hex("")
        assert result is None

    def test_convert_color_to_hex_valid_6_digit(self):
        """Test color conversion with valid 6-digit hex"""
        result = self.manager._convert_color_to_hex("FF0000")
        assert result == "#FF0000"

    def test_convert_color_to_hex_valid_8_digit_argb(self):
        """Test color conversion with 8-digit ARGB hex (removes alpha)"""
        result = self.manager._convert_color_to_hex("FFFF0000")
        assert result == "#FF0000"

    def test_convert_color_to_hex_with_prefix(self):
        """Test color conversion with various prefixes"""
        result = self.manager._convert_color_to_hex("0xFF0000")
        assert result == "#FF0000"

    def test_convert_color_to_hex_color_names(self):
        """Test color conversion with color names"""
        assert self.manager._convert_color_to_hex("black") == "#000000"
        assert self.manager._convert_color_to_hex("white") == "#FFFFFF"
        assert self.manager._convert_color_to_hex("red") == "#FF0000"
        assert self.manager._convert_color_to_hex("GREEN") == "#00FF00"
        assert self.manager._convert_color_to_hex("Blue") == "#0000FF"

    def test_convert_color_to_hex_invalid(self):
        """Test color conversion with invalid input"""
        result = self.manager._convert_color_to_hex("invalid_color")
        assert result is None

    def test_extract_row_color_from_format_no_color(self):
        """Test row color extraction with no fill color"""
        cell_format = {'font_bold': True, 'fill_color': None}
        result = self.manager._extract_row_color_from_format(cell_format)
        assert result is None

    def test_extract_row_color_from_format_yellow(self):
        """Test row color extraction for yellow background"""
        cell_format = {'fill_color': '#FFFF99'}
        result = self.manager._extract_row_color_from_format(cell_format)
        assert result == "yellow"

    def test_extract_row_color_from_format_green(self):
        """Test row color extraction for green background"""
        cell_format = {'fill_color': '#CCFFCC'}
        result = self.manager._extract_row_color_from_format(cell_format)
        assert result == "green"

    def test_extract_row_color_from_format_unknown_color(self):
        """Test row color extraction for unknown color"""
        cell_format = {'fill_color': '#123456'}
        result = self.manager._extract_row_color_from_format(cell_format)
        assert result is None

    def test_prepare_special_data_basic(self):
        """Test special data preparation with basic input"""
        # Mock the columns
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': 'User content',
            'Startdatum': '',
            'Källa1': '',
            'date': '2024-01-15'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        assert 'User content' in result['Händelse']
        assert 'test.pdf' in result['Händelse']
        assert result['Källa1'] == 'test.pdf'

    def test_prepare_special_data_no_filename(self):
        """Test special data preparation without filename"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': 'User content only',
            'Startdatum': '2024-01-15',
            'Källa1': ''
        }
        filename = ''

        result = self.manager._prepare_special_data(data, filename)

        assert result['Händelse'] == 'User content only'
        assert result['Startdatum'] == '2024-01-15'
        assert result['Källa1'] == ''

    def test_prepare_special_data_date_parsing(self):
        """Test special data preparation with date parsing"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': '',
            'Startdatum': '',  # Empty, should use date from filename
            'Källa1': '',
            'date': '2024-01-15'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        # Should parse date and create date object
        assert hasattr(result['Startdatum'], 'year')
        assert result['Startdatum'].year == 2024
        assert result['Startdatum'].month == 1
        assert result['Startdatum'].day == 15

    def test_prepare_special_data_invalid_date(self):
        """Test special data preparation with invalid date"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': '',
            'Startdatum': '',
            'Källa1': '',
            'date': 'invalid-date'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        # Should fall back to original string
        assert result['Startdatum'] == 'invalid-date'

    def test_prepare_special_data_user_has_startdatum(self):
        """Test special data preparation when user already provided Startdatum"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': '',
            'Startdatum': '2024-02-20',  # User provided date
            'Källa1': '',
            'date': '2024-01-15'  # Different date from filename
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        # Should keep user's date, not filename date
        assert result['Startdatum'] == '2024-02-20'

    def test_prepare_special_data_user_has_kalla1(self):
        """Test special data preparation when user already provided Källa1"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': '',
            'Startdatum': '',
            'Källa1': 'User source',  # User provided source
            'date': '2024-01-15'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        # Should keep user's source, not filename
        assert result['Källa1'] == 'User source'

    def test_prepare_special_data_filename_already_in_handelse(self):
        """Test special data preparation when filename is already in Händelse"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': 'User content with test.pdf already mentioned',
            'Startdatum': '',
            'Källa1': '',
            'date': '2024-01-15'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        # Should not duplicate filename
        assert result['Händelse'] == 'User content with test.pdf already mentioned'
        assert result['Händelse'].count('test.pdf') == 1

    def test_prepare_special_data_no_columns(self):
        """Test special data preparation when columns are not loaded"""
        # No columns loaded
        self.manager.columns = {}

        data = {
            'Händelse': 'Content',
            'date': '2024-01-15'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        # Should return data unchanged since columns don't exist
        assert result == data

    def test_prepare_special_data_empty_handelse_with_filename(self):
        """Test special data preparation with empty Händelse and filename"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': '',  # Empty
            'Startdatum': '',
            'Källa1': '',
            'date': '2024-01-15'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        # Should add filename with line breaks
        assert result['Händelse'] == '\n\ntest.pdf'

    # NOTE: We intentionally do NOT test the hybrid methods:
    # - load_excel_file() - involves actual file I/O
    # - add_row() - involves actual file I/O and complex formatting
    # - add_row_with_xlsxwriter() - the breakthrough hybrid method (untouchable)
    # - _write_rich_text_xlsxwriter() - complex rich text handling (untouchable)
    # - _repair_corrupted_cellrichtext() - critical corruption repair (untouchable)

    def test_edge_cases_special_characters(self):
        """Test special data preparation with Swedish characters"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3}

        data = {
            'Händelse': 'Innehåll med åäö',
            'Startdatum': '',
            'Källa1': '',
            'date': '2024-01-15'
        }
        filename = 'fil_med_åäö.pdf'

        result = self.manager._prepare_special_data(data, filename)

        assert 'åäö' in result['Händelse']
        assert 'fil_med_åäö.pdf' in result['Händelse']

    def test_color_conversion_case_insensitive(self):
        """Test that color name conversion is case insensitive"""
        assert self.manager._convert_color_to_hex("BLACK") == "#000000"
        assert self.manager._convert_color_to_hex("White") == "#FFFFFF"
        assert self.manager._convert_color_to_hex("rEd") == "#FF0000"

    def test_extract_row_color_case_insensitive(self):
        """Test row color extraction is case insensitive"""
        cell_format = {'fill_color': '#ffff99'}  # lowercase
        result = self.manager._extract_row_color_from_format(cell_format)
        assert result == "yellow"

    def test_prepare_special_data_preserves_other_fields(self):
        """Test that special data preparation preserves non-special fields"""
        self.manager.columns = {'Händelse': 1, 'Startdatum': 2, 'Källa1': 3, 'OtherField': 4}

        data = {
            'Händelse': '',
            'Startdatum': '',
            'Källa1': '',
            'OtherField': 'Should be preserved',
            'date': '2024-01-15'
        }
        filename = 'test.pdf'

        result = self.manager._prepare_special_data(data, filename)

        assert result['OtherField'] == 'Should be preserved'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
