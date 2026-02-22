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

    # Known PDF viewer app bundles — maps executable names or bundle
    # path fragments to friendly display names.
    KNOWN_PDF_APPS: dict[str, str] = {
        'PDF Studio 2024.app': 'PDF Studio 2024',
        'PDF Studio 2023.app': 'PDF Studio 2023',
        'PDF Studio 2022.app': 'PDF Studio 2022',
        'PDF Studio.app': 'PDF Studio',
        'Adobe Acrobat': 'Adobe Acrobat',
        'Acrobat Reader': 'Adobe Acrobat Reader',
        'Skim.app': 'Skim',
        'PDF Expert.app': 'PDF Expert',
    }

    @staticmethod
    def check_accessibility_permission() -> bool:
        """Test if we have macOS Accessibility permission for System Events.

        Tests actual window reading (not just process names), because reading
        window properties is what requires Accessibility permission.
        Returns True if permission is granted, False otherwise.
        """
        if platform.system() != 'Darwin':
            return True

        try:
            # Read window names of Finder — this requires Accessibility
            # permission, unlike reading process names which works without it.
            result = subprocess.run(
                ['osascript', '-e',
                 'tell application "System Events" to get name of every '
                 'window of process "Finder"'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                logger.info("Accessibility permission check: granted")
                return True
            else:
                logger.warning(
                    f"Accessibility permission check failed: "
                    f"{result.stderr.strip()}"
                )
                return False
        except subprocess.TimeoutExpired:
            logger.warning("Accessibility permission check timed out")
            return False
        except (FileNotFoundError, OSError) as e:
            logger.debug(f"Accessibility permission check error: {e}")
            return False

    @staticmethod
    def _get_running_pdf_apps() -> list[str]:
        """Check if any known PDF viewer applications are running.

        Uses 'ps aux' to find running processes matching known PDF app paths.
        Returns list of friendly app names that are currently running.
        """
        running_apps: list[str] = []
        try:
            result = subprocess.run(
                ['ps', 'aux'], capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return []

            for line in result.stdout.splitlines():
                for bundle_fragment, friendly_name in (
                    PDFProcessor.KNOWN_PDF_APPS.items()
                ):
                    if (
                        bundle_fragment in line
                        and friendly_name not in running_apps
                    ):
                        running_apps.append(friendly_name)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug(f"ps aux check failed: {e}")

        return running_apps

    @staticmethod
    def is_file_open_by_other_process(file_path: str) -> tuple[bool, list[str]]:
        """Check if file is open by another process on macOS.

        Uses three complementary methods:
        1. CGWindowListCopyWindowInfo — checks window titles for the filename.
           Catches apps whose window titles are visible (requires Screen Recording
           permission for other apps' window names).
        2. lsof — checks open file descriptors. Catches apps like Preview/QuickLook
           that keep the file handle open.
        3. Process list (ps aux) — checks if known PDF viewer apps are running.
           Can't verify which file is open, but warns the user. Catches Java
           apps (PDF Studio) that close file handles and don't expose window
           titles without special permissions.

        Returns:
            (is_open, process_names): Whether file is open and list of app names using it.
        """
        if platform.system() != 'Darwin':
            return (False, [])

        process_names: list[str] = []
        own_pid = os.getpid()
        filename = Path(file_path).name
        stem = Path(file_path).stem

        # Apps to exclude from window-title matching (not PDF editors)
        ignored_window_owners = {'Finder', 'Python', 'python3'}

        # Method 1: Check window titles via CoreGraphics
        try:
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGNullWindowID,
                kCGWindowListOptionAll,
            )
            windows = CGWindowListCopyWindowInfo(
                kCGWindowListOptionAll, kCGNullWindowID,
            )
            for w in windows:
                win_name = w.get('kCGWindowName', '') or ''
                owner = w.get('kCGWindowOwnerName', '') or ''
                owner_pid = w.get('kCGWindowOwnerPID', 0)
                if (
                    owner_pid != own_pid
                    and owner not in ignored_window_owners
                    and (filename in win_name or stem in win_name)
                    and owner not in process_names
                ):
                    process_names.append(owner)
        except Exception as e:
            logger.debug(f"CGWindowList check unavailable: {e}")

        # Method 2: Check open file descriptors via lsof
        try:
            result = subprocess.run(
                ['lsof', '--', file_path],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                for line in lines[1:]:
                    columns = line.split()
                    if len(columns) >= 2:
                        proc_name = columns[0]
                        proc_pid = columns[1]
                        if (
                            proc_pid != str(own_pid)
                            and proc_name not in process_names
                        ):
                            process_names.append(proc_name)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug(f"lsof check failed: {e}")

        # Method 3: AppleScript System Events — query window names via
        # Accessibility permission. Precise: identifies which file is open.
        if not process_names:
            try:
                escaped_filename = filename.replace('\\', '\\\\').replace('"', '\\"')
                escaped_stem = stem.replace('\\', '\\\\').replace('"', '\\"')

                applescript = f'''
                    set matchedApps to {{}}
                    tell application "System Events"
                        set appProcesses to every process whose background only is false
                        repeat with proc in appProcesses
                            set procName to name of proc
                            try
                                set winList to name of every window of proc
                                repeat with winTitle in winList
                                    if winTitle contains "{escaped_filename}" or winTitle contains "{escaped_stem}" then
                                        if procName is not in matchedApps then
                                            set end of matchedApps to procName
                                        end if
                                    end if
                                end repeat
                            end try
                        end repeat
                    end tell
                    set AppleScript's text item delimiters to linefeed
                    return matchedApps as text
                '''

                result = subprocess.run(
                    ['osascript', '-e', applescript],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    for app_name in result.stdout.strip().splitlines():
                        app_name = app_name.strip()
                        if (
                            app_name
                            and app_name not in ignored_window_owners
                            and app_name not in process_names
                        ):
                            process_names.append(app_name)
            except subprocess.TimeoutExpired:
                logger.warning("AppleScript System Events timed out")
            except (FileNotFoundError, OSError) as e:
                logger.debug(f"AppleScript System Events check failed: {e}")

        # Method 4: Check running PDF apps via process list (ps aux).
        # Fallback when Methods 1-3 found nothing. Can't identify which
        # file is open, but detects that a PDF viewer is running.
        if not process_names:
            running_pdf_apps = PDFProcessor._get_running_pdf_apps()
            if running_pdf_apps:
                process_names.extend(running_pdf_apps)
                logger.info(
                    f"PDF apps detected via process list: {running_pdf_apps}"
                )

        if process_names:
            return (True, process_names)
        return (False, [])

    @staticmethod
    def open_pdf_externally(pdf_path: str) -> None:
        """Open PDF file with default system application"""
        try:
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', '--', pdf_path])
            else:  # Linux
                subprocess.run(['xdg-open', '--', pdf_path])
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
                subprocess.run(['open', '--', excel_path])
            else:  # Linux
                subprocess.run(['xdg-open', '--', excel_path])
        except Exception as e:
            logger.error(f"Error opening Excel externally: {e}")
            raise
