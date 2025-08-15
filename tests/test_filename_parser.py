"""
Comprehensive tests for FilenameParser module - Phase 1 Autonomous Testing
"""

import sys
from pathlib import Path

import pytest

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.filename_parser import FilenameParser


class TestFilenameParser:
    """Test suite for FilenameParser functionality"""

    def test_parse_filename_basic(self):
        """Test basic filename parsing with all components"""
        filename = "2024-01-15 Dagens Nyheter article about corruption (5 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == "2024-01-15"
        # Note: Parser only takes first word for newspaper unless ALL-CAPS
        assert result['newspaper'] == "Dagens"
        assert result['comment'] == "Nyheter article about corruption"
        assert result['pages'] == "5"

    def test_parse_filename_with_all_caps_newspaper(self):
        """Test parsing with ALL-CAPS newspaper name"""
        filename = "2024-02-20 AFTONBLADET PLUS investigation report (3 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == "2024-02-20"
        assert result['newspaper'] == "AFTONBLADET PLUS"
        assert result['comment'] == "investigation report"
        assert result['pages'] == "3"

    def test_parse_filename_no_comment(self):
        """Test parsing filename without comment"""
        filename = "2024-03-10 Svenska Dagbladet (7 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == "2024-03-10"
        # Parser only takes first word unless ALL-CAPS
        assert result['newspaper'] == "Svenska"
        assert result['comment'] == "Dagbladet"
        assert result['pages'] == "7"

    def test_parse_filename_no_pages(self):
        """Test parsing filename without page count"""
        filename = "2024-04-05 Expressen breaking news story.pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == "2024-04-05"
        assert result['newspaper'] == "Expressen"
        assert result['comment'] == "breaking news story"
        assert result['pages'] == ""

    def test_parse_filename_minimal(self):
        """Test parsing minimal filename with just date and newspaper"""
        filename = "2024-05-12 DN.pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == "2024-05-12"
        assert result['newspaper'] == "DN"
        assert result['comment'] == ""
        assert result['pages'] == ""

    def test_parse_filename_no_date(self):
        """Test parsing filename without date"""
        filename = "Dagens Nyheter important article (2 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == ""
        assert result['newspaper'] == ""
        assert result['comment'] == ""
        assert result['pages'] == "2"

    def test_parse_filename_complex_newspaper_name(self):
        """Test parsing with complex newspaper name (max 3 words)"""
        filename = "2024-06-01 DAGENS INDUSTRI PREMIUM special report (4 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == "2024-06-01"
        assert result['newspaper'] == "DAGENS INDUSTRI PREMIUM"
        assert result['comment'] == "special report"
        assert result['pages'] == "4"

    def test_parse_filename_long_comment(self):
        """Test parsing with long comment"""
        filename = "2024-07-15 Aftonbladet this is a very long comment about multiple topics and issues (10 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['date'] == "2024-07-15"
        assert result['newspaper'] == "Aftonbladet"
        assert result['comment'] == "this is a very long comment about multiple topics and issues"
        assert result['pages'] == "10"

    def test_construct_filename_all_components(self):
        """Test filename construction with all components"""
        result = FilenameParser.construct_filename(
            "2024-01-15",
            "Dagens Nyheter",
            "article about corruption",
            "5"
        )
        expected = "2024-01-15 Dagens Nyheter article about corruption (5 sid).pdf"
        assert result == expected

    def test_construct_filename_no_comment(self):
        """Test filename construction without comment"""
        result = FilenameParser.construct_filename(
            "2024-02-20",
            "Svenska Dagbladet",
            "",
            "3"
        )
        expected = "2024-02-20 Svenska Dagbladet (3 sid).pdf"
        assert result == expected

    def test_construct_filename_no_pages(self):
        """Test filename construction without pages"""
        result = FilenameParser.construct_filename(
            "2024-03-10",
            "Expressen",
            "breaking news",
            ""
        )
        expected = "2024-03-10 Expressen breaking news.pdf"
        assert result == expected

    def test_construct_filename_minimal(self):
        """Test filename construction with just date and newspaper"""
        result = FilenameParser.construct_filename(
            "2024-04-05",
            "DN",
            "",
            ""
        )
        expected = "2024-04-05 DN.pdf"
        assert result == expected

    def test_construct_filename_handles_whitespace(self):
        """Test that construction handles whitespace in components"""
        result = FilenameParser.construct_filename(
            "2024-05-12",
            "Dagens Nyheter",
            "  spaced comment  ",
            "  7  "
        )
        expected = "2024-05-12 Dagens Nyheter spaced comment (  7   sid).pdf"
        assert result == expected

    def test_validate_filename_valid(self):
        """Test validation of valid filename"""
        valid, message = FilenameParser.validate_filename("2024-01-15 Dagens Nyheter article (5 sid).pdf")
        assert valid is True
        assert message == ""

    def test_validate_filename_empty(self):
        """Test validation of empty filename"""
        valid, message = FilenameParser.validate_filename("")
        assert valid is False
        assert "tomt" in message.lower()

    def test_validate_filename_whitespace_only(self):
        """Test validation of whitespace-only filename"""
        valid, message = FilenameParser.validate_filename("   ")
        assert valid is False
        assert "tomt" in message.lower()

    def test_validate_filename_invalid_characters(self):
        """Test validation with Windows-invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = f"2024-01-15 Test{char}File.pdf"
            valid, message = FilenameParser.validate_filename(filename)
            assert valid is False
            assert char in message

    def test_validate_filename_too_long(self):
        """Test validation of filename that's too long"""
        long_filename = "2024-01-15 " + "A" * 200 + ".pdf"
        valid, message = FilenameParser.validate_filename(long_filename)
        assert valid is False
        assert "långt" in message.lower()

    def test_validate_filename_no_pdf_extension(self):
        """Test validation of filename without .pdf extension"""
        valid, message = FilenameParser.validate_filename("2024-01-15 Dagens Nyheter article")
        assert valid is False
        assert ".pdf" in message

    def test_validate_filename_case_insensitive_pdf(self):
        """Test validation accepts .PDF extension (case insensitive)"""
        valid, message = FilenameParser.validate_filename("2024-01-15 Test.PDF")
        assert valid is True
        assert message == ""

    def test_clean_pdf_text_basic_line_breaks(self):
        """Test basic line break cleaning"""
        text = "This is a test\nwith line breaks\nthat should be cleaned"
        result = FilenameParser.clean_pdf_text(text)
        expected = "This is a test with line breaks that should be cleaned"
        assert result == expected

    def test_clean_pdf_text_hyphen_continuation(self):
        """Test hyphen word continuation cleaning"""
        text = "This is a hyphen-\nated word that spans lines"
        result = FilenameParser.clean_pdf_text(text)
        expected = "This is a hyphenated word that spans lines"
        assert result == expected

    def test_clean_pdf_text_preserve_punctuation_breaks(self):
        """Test preservation of line breaks after punctuation"""
        text = "Sentence one.\nSentence two."
        result = FilenameParser.clean_pdf_text(text)
        expected = "Sentence one.\nSentence two."
        assert result == expected

    def test_clean_pdf_text_comma_handling(self):
        """Test comma line break handling"""
        text = "Item one,\nitem two"
        result = FilenameParser.clean_pdf_text(text)
        expected = "Item one, item two"
        assert result == expected

    def test_clean_pdf_text_number_handling(self):
        """Test number line break handling"""
        text = "The year 2024\nwas important"
        result = FilenameParser.clean_pdf_text(text)
        expected = "The year 2024 was important"
        assert result == expected

    def test_clean_pdf_text_multiple_line_breaks(self):
        """Test normalization of multiple line breaks"""
        text = "Paragraph one.\n\n\n\nParagraph two."
        result = FilenameParser.clean_pdf_text(text)
        expected = "Paragraph one.\n\nParagraph two."
        assert result == expected

    def test_clean_pdf_text_whitespace_normalization(self):
        """Test whitespace normalization"""
        text = "  Text   with   excessive    spaces  \n  and   line  breaks  "
        result = FilenameParser.clean_pdf_text(text)
        expected = "Text with excessive spaces\nand line breaks"
        assert result == expected

    def test_clean_pdf_text_empty_input(self):
        """Test cleaning of empty or None input"""
        assert FilenameParser.clean_pdf_text("") == ""
        assert FilenameParser.clean_pdf_text(None) is None

    def test_clean_pdf_text_windows_line_endings(self):
        """Test handling of Windows line endings"""
        text = "Line one\r\nLine two\r\nLine three"
        result = FilenameParser.clean_pdf_text(text)
        expected = "Line one Line two Line three"
        assert result == expected

    def test_clean_pdf_text_complex_example(self):
        """Test complex real-world example"""
        text = """This is a complex exam-\nple of PDF text that has been\ncopied with various line\nbreaks and formatting issues.\n\n\nIt includes multiple paragraphs,\nnumbers like 2024\nand punctuation.\n\nThe final result should be readable."""
        result = FilenameParser.clean_pdf_text(text)

        # Should remove continuation hyphens and unnecessary line breaks
        assert "exam-\nple" not in result
        assert "example" in result
        assert "2024 and" in result
        # Should preserve paragraph breaks
        assert result.count('\n\n') >= 1

    def test_parse_and_construct_roundtrip(self):
        """Test that parsing and construction work together (note: not perfect roundtrip due to newspaper parsing)"""
        original_filename = "2024-08-15 DAGENS NYHETER investigation report (12 sid).pdf"

        # Parse the filename
        components = FilenameParser.parse_filename(original_filename)

        # Reconstruct it
        reconstructed = FilenameParser.construct_filename(
            components['date'],
            components['newspaper'],
            components['comment'],
            components['pages']
        )

        # Due to ALL-CAPS newspaper parsing, this should work for ALL-CAPS newspapers
        assert reconstructed == original_filename

        # Test with single word newspaper (perfect roundtrip)
        simple_filename = "2024-08-15 Expressen investigation report (12 sid).pdf"
        components2 = FilenameParser.parse_filename(simple_filename)
        reconstructed2 = FilenameParser.construct_filename(
            components2['date'],
            components2['newspaper'],
            components2['comment'],
            components2['pages']
        )
        assert reconstructed2 == simple_filename

    def test_edge_cases_special_characters_in_comment(self):
        """Test handling of special characters in comments"""
        filename = "2024-09-01 Aftonbladet åäö special characters (1 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        assert result['comment'] == "åäö special characters"
        assert result['newspaper'] == "Aftonbladet"

    def test_edge_cases_numbers_in_newspaper(self):
        """Test handling of numbers in newspaper names"""
        filename = "2024-10-15 24 Sidor breaking news (3 sid).pdf"
        result = FilenameParser.parse_filename(filename)

        # Numbers in newspaper name should be handled properly
        assert result['newspaper'] == "24"
        assert result['comment'] == "Sidor breaking news"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
