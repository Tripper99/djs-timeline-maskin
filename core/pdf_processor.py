"""
PDF processing functionality for the DJ Timeline application
"""

import logging
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import PyPDF2

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF file operations"""

    @staticmethod
    def get_pdf_page_count(pdf_path: str) -> int:
        """Get number of pages in PDF file with improved error handling"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    logger.warning(f"PDF file is encrypted: {pdf_path}")
                    return 0

                # Validate that we can actually read the pages
                page_count = len(pdf_reader.pages)

                # Try to access first page to verify PDF integrity
                if page_count > 0:
                    try:
                        _ = pdf_reader.pages[0]
                    except Exception as e:
                        logger.error(f"PDF appears corrupted, cannot read first page: {e}")
                        raise ValueError("PDF-filen verkar vara skadad") from e

                return page_count

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            return 0
        except ValueError as e:
            # Re-raise ValueError with our custom message
            raise e
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            # Check if it's a known PDF corruption error
            if "xref" in str(e).lower() or "trailer" in str(e).lower() or "startxref" in str(e).lower():
                raise ValueError("PDF-filen är skadad eller korrupt") from e
            return 0

    @staticmethod
    def validate_pdf_file(pdf_path: str) -> Tuple[bool, str]:
        """Validate that PDF file exists and is readable"""
        try:
            pdf_file = Path(pdf_path)

            # Check if file exists
            if not pdf_file.exists():
                return False, "PDF-filen finns inte längre"

            # Check if it's actually a file (not a directory)
            if not pdf_file.is_file():
                return False, "Sökvägen pekar inte på en fil"

            # Check file size (empty files are suspicious)
            if pdf_file.stat().st_size == 0:
                return False, "PDF-filen är tom"

            # Check file extension
            if not pdf_file.suffix.lower() == '.pdf':
                return False, "Filen har inte .pdf-filnamnstillägg"

            # Try to read the PDF to check integrity
            try:
                PDFProcessor.get_pdf_page_count(pdf_path)
                return True, ""
            except ValueError as e:
                return False, str(e)

        except Exception as e:
            return False, f"Fel vid validering av PDF: {str(e)}"

    @staticmethod
    def check_directory_permissions(directory_path: str) -> Tuple[bool, str]:
        """Check if directory exists and is writable"""
        try:
            dir_path = Path(directory_path)

            # Check if directory exists
            if not dir_path.exists():
                return False, "Mappen finns inte"

            # Check if it's actually a directory
            if not dir_path.is_dir():
                return False, "Sökvägen är inte en mapp"

            # Check write permissions by trying to create a temporary file
            try:
                with tempfile.NamedTemporaryFile(dir=directory_path, delete=True):
                    pass
                return True, ""
            except PermissionError:
                return False, "Inga skrivrättigheter i mappen"
            except Exception as e:
                return False, f"Kan inte skriva till mappen: {str(e)}"

        except Exception as e:
            return False, f"Fel vid kontroll av mapprättigheter: {str(e)}"

    @staticmethod
    def is_file_locked(file_path: str) -> bool:
        """Check if file is locked/in use by another application"""
        try:
            # Try to open file in exclusive mode
            with open(file_path, 'r+b'):
                pass
            return False
        except (OSError, PermissionError):
            return True
        except FileNotFoundError:
            return False  # File doesn't exist, so it's not locked
        except Exception:
            return True  # Assume locked if we can't determine

    @staticmethod
    def open_pdf_externally(pdf_path: str) -> None:
        """Open PDF file with default system application"""
        try:
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path])
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path])
        except Exception as e:
            logger.error(f"Error opening PDF externally: {e}")
            raise

    @staticmethod
    def open_excel_externally(excel_path: str) -> None:
        """Open Excel file with default system application"""
        try:
            if platform.system() == 'Windows':
                os.startfile(excel_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', excel_path])
            else:  # Linux
                subprocess.run(['xdg-open', excel_path])
        except Exception as e:
            logger.error(f"Error opening Excel externally: {e}")
            raise
