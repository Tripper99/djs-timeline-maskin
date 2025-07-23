"""
Filename parsing and construction for the DJ Timeline application
"""

import logging
import re
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class FilenameParser:
    """Parses and constructs PDF filenames"""

    @staticmethod
    def parse_filename(filename: str) -> Dict[str, str]:
        """Parse PDF filename into components"""
        # Remove .pdf extension
        base_name = filename.replace('.pdf', '')

        # Initialize components
        date = ""
        newspaper = ""
        comment = ""
        pages = ""

        # Extract page count from end (X sid)
        page_match = re.search(r'\((\d+)\s+sid\)$', base_name)
        if page_match:
            pages = page_match.group(1)
            base_name = base_name[:page_match.start()].strip()

        # Extract date from beginning (YYYY-MM-DD)
        date_match = re.match(r'^(\d{4}-\d{2}-\d{2})\s+', base_name)
        if date_match:
            date = date_match.group(1)
            remaining = base_name[date_match.end():].strip()

            # Split remaining text into words
            words = remaining.split()

            if words:
                # First word is always newspaper name
                newspaper_words = [words[0]]
                remaining_words = words[1:]

                # Add following ALL-CAPS words to newspaper name
                newspaper_end_index = 1  # Start after first word
                for i, word in enumerate(remaining_words):
                    if word.isupper() and len(newspaper_words) < 3:
                        newspaper_words.append(word)
                        newspaper_end_index = i + 2  # +2 because remaining_words starts from index 1
                    else:
                        break

                newspaper = ' '.join(newspaper_words)

                # Everything after newspaper name is comment
                if newspaper_end_index < len(words):
                    comment_words = words[newspaper_end_index:]
                    comment = ' '.join(comment_words)

        return {
            'date': date,
            'newspaper': newspaper,
            'comment': comment,
            'pages': pages
        }

    @staticmethod
    def construct_filename(date: str, newspaper: str, comment: str, pages: str) -> str:
        """Construct filename from components"""
        parts = [date, newspaper]

        if comment.strip():
            parts.append(comment.strip())

        if pages.strip():
            parts.append(f"({pages} sid)")

        return ' '.join(parts) + '.pdf'

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """Validate filename for Windows compatibility"""
        if not filename or not filename.strip():
            return False, "Filnamnet får inte vara tomt"

        # Check for invalid characters in Windows filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in filename:
                return False, f"Ogiltigt tecken: {char}"

        # Check length (Windows max path is 260, but we'll be conservative)
        if len(filename) > 200:
            return False, "Filnamnet är för långt"

        # Check if filename ends with .pdf
        if not filename.lower().endswith('.pdf'):
            return False, "Filnamnet måste sluta med .pdf"

        return True, ""

    @staticmethod
    def clean_pdf_text(text: str) -> str:
        """Clean text that has been copied from PDF documents by removing unwanted line breaks"""
        if not text or not isinstance(text, str):
            return text

        # Store the original for debugging
        original_text = text

        # Step 1: Normalize line endings to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Step 2: Remove hyphen + line break (word continuation)
        # Pattern: word-\n → word
        text = re.sub(r'(\w)-\n', r'\1', text)

        # Step 3: Handle line breaks after punctuation (keep these)
        # Pattern: word.\n or word. \n → keep as is (paragraph breaks)
        # This is handled by NOT modifying these patterns

        # Step 4: Remove line break after word + space
        # Pattern: word \n → word (remove just the line break)
        text = re.sub(r'(\w) \n', r'\1 ', text)

        # Step 5: Replace line break after word (no space, no punctuation)
        # Pattern: word\n → word (space)
        # But avoid cases where the line break is after sentence-ending punctuation
        text = re.sub(r'(\w)\n(?![.!?:;\n])', r'\1 ', text)

        # Step 6: Handle line breaks after punctuation that should be kept
        # Ensure colon and semicolon breaks are preserved
        # Pattern: word:\n or word;\n → keep (already preserved above)

        # Step 7: Handle commas - add space after line break
        # Pattern: word,\n → word, (space)
        text = re.sub(r'(\w),\n', r'\1, ', text)

        # Step 8: Handle line breaks after numbers/dates
        # Pattern: 123\n → 123 (space)
        text = re.sub(r'(\d)\n(?![.!?:;\n])', r'\1 ', text)

        # Step 9: Normalize multiple line breaks (max 2 for paragraph separation)
        # Pattern: \n\n\n+ → \n\n
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Step 10: Clean up excessive whitespace
        # Remove leading/trailing whitespace and normalize internal spaces
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Trim each line and normalize internal spaces
            cleaned_line = re.sub(r' +', ' ', line.strip())
            cleaned_lines.append(cleaned_line)

        # Join lines back and do final cleanup
        text = '\n'.join(cleaned_lines)

        # Final trim of the entire text
        text = text.strip()

        logger.debug(f"PDF text cleaning: '{original_text[:50]}...' → '{text[:50]}...'")
        return text
