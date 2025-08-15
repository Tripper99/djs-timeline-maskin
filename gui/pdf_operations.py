#!/usr/bin/env python3
"""
PDF operations mixin for DJs Timeline-maskin
Contains PDF file selection, renaming, and clearing methods
"""

import logging
from pathlib import Path
from tkinter import filedialog, messagebox

from core.filename_parser import FilenameParser
from core.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)


class PDFOperationsMixin:
    """Mixin class providing PDF file operations"""

    def select_pdf_file(self):
        """Select PDF file for processing"""
        initial_dir = self.config.get('last_pdf_dir', str(Path.home()))

        file_path = filedialog.askopenfilename(
            title="Välj PDF-fil",
            filetypes=[("PDF-filer", "*.pdf"), ("Alla filer", "*.*")],
            initialdir=initial_dir
        )

        if file_path:
            # Validate PDF file before proceeding
            is_valid, error_msg = PDFProcessor.validate_pdf_file(file_path)
            if not is_valid:
                messagebox.showerror("Ogiltig PDF-fil", f"Kan inte använda vald fil:\n{error_msg}")
                return

            self.current_pdf_path = file_path
            self.pdf_path_var.set(Path(file_path).name)

            # Update last directory
            self.config['last_pdf_dir'] = str(Path(file_path).parent)

            # Get page count with error handling
            try:
                self.current_pdf_pages = PDFProcessor.get_pdf_page_count(file_path)
            except ValueError as e:
                messagebox.showerror("PDF-fel", str(e))
                # Reset PDF selection
                self.current_pdf_path = ""
                self.pdf_path_var.set("Ingen PDF vald")
                return

            # Parse filename and store original components
            filename = Path(file_path).name
            components = FilenameParser.parse_filename(filename)
            self.original_filename_components = components.copy()

            # Update GUI fields
            self.date_var.set(components['date'])
            self.newspaper_var.set(components['newspaper'])
            self.comment_var.set(components['comment'])

            # Use actual page count if not in filename
            if components['pages']:
                self.pages_var.set(components['pages'])
            else:
                self.pages_var.set(str(self.current_pdf_pages))

            # Open PDF externally
            try:
                PDFProcessor.open_pdf_externally(file_path)
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte öppna PDF-fil: {str(e)}")

            # Auto-fill output folder if not locked (always when unlocked)
            if not self.output_folder_lock_var.get():
                pdf_folder = str(Path(file_path).parent)
                self._actual_output_folder = pdf_folder
                display_text = self.get_display_folder_text(pdf_folder)
                self.output_folder_var.set(display_text)
                logger.info(f"Auto-filled output folder: {pdf_folder}")

            # Update statistics
            self.stats['pdfs_opened'] += 1
            self.update_stats_display()

            logger.info(f"Loaded PDF: {filename}, Pages: {self.current_pdf_pages}")

    def rename_current_pdf(self) -> bool:
        """Rename the current PDF file if filename has changed"""
        if not self.current_pdf_path:
            return False

        if not self.has_filename_changed():
            return False  # No changes to save

        # Validate that PDF file still exists
        is_valid, error_msg = PDFProcessor.validate_pdf_file(self.current_pdf_path)
        if not is_valid:
            messagebox.showerror("PDF-fil saknas",
                               f"PDF-filen kunde inte hittas eller läsas:\n{error_msg}\n\n" +
                               "Filen kan ha flyttats, tagits bort eller skadats.")
            return False

        # Check if file is locked by another application - with retry loop
        while PDFProcessor.is_file_locked(self.current_pdf_path):
            choice = self.show_retry_cancel_dialog(
                "Fil låst",
                "PDF-filen används av ett annat program. " +
                "Stäng programmet och försök igen."
            )
            if choice == 'cancel':
                return False
            # If choice == 'retry', loop continues to check again

        # Construct new filename
        new_filename = FilenameParser.construct_filename(
            self.date_var.get(),
            self.newspaper_var.get(),
            self.comment_var.get(),
            self.pages_var.get()
        )

        # Validate filename
        is_valid, error_msg = FilenameParser.validate_filename(new_filename)
        if not is_valid:
            messagebox.showerror("Ogiltigt filnamn", f"Filnamnet är ogiltigt: {error_msg}")
            return False

        old_file = Path(self.current_pdf_path)

        # Determine target directory based on output folder setting
        output_folder = getattr(self, '_actual_output_folder', '') or self.output_folder_var.get()
        if output_folder and Path(output_folder).exists():
            target_dir = Path(output_folder)
        else:
            # Default to same directory as original file
            target_dir = old_file.parent

        # Check target directory permissions
        can_write, perm_error = PDFProcessor.check_directory_permissions(str(target_dir))
        if not can_write:
            messagebox.showerror("Fel", f"Kan inte skriva till mappen '{target_dir}': {perm_error}")
            return False

        new_path = target_dir / new_filename

        # Check if target file already exists
        if new_path.exists() and str(new_path) != str(old_file):
            # Check if target file is locked - with retry loop
            while PDFProcessor.is_file_locked(str(new_path)):
                choice = self.show_retry_cancel_dialog(
                    "Målfil låst",
                    f"Målfilen '{new_filename}' är låst av ett annat program. " +
                    "Stäng programmet och försök igen."
                )
                if choice == 'cancel':
                    return False
                # If choice == 'retry', loop continues to check again

            result = messagebox.askyesno("Filen finns redan",
                                       f"Filen '{new_filename}' finns redan. Vill du skriva över den?")
            if not result:
                return False
        # Attempt to rename/move
        try:
            if str(target_dir) != str(old_file.parent):
                # Move to different directory
                old_file.replace(new_path)  # replace() overwrites if target exists
                logger.info(f"Moved and renamed: {old_file.name} -> {target_dir.name}/{new_filename}")
            else:
                # Just rename in same directory
                old_file.rename(new_path)
                logger.info(f"Renamed: {old_file.name} -> {new_filename}")

            # Update internal state
            self.current_pdf_path = str(new_path)
            self.pdf_path_var.set(new_filename)
            self.original_filename_components = {
                'date': self.date_var.get(),
                'newspaper': self.newspaper_var.get(),
                'comment': self.comment_var.get(),
                'pages': self.pages_var.get()
            }

            self.stats['files_renamed'] += 1
            self.update_stats_display()

            return True

        except PermissionError:
            messagebox.showerror("Fel", "Åtkomst nekad. Kontrollera att du har behörighet att ändra filer i mappen.")
            return False
        except FileExistsError:
            messagebox.showerror("Fel", f"Filen '{new_filename}' finns redan och kunde inte skrivas över.")
            return False
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte byta namn på filen: {str(e)}")
            return False

    def clear_pdf_and_filename_fields(self):
        """Clear PDF selection and filename components"""
        self.current_pdf_path = ""
        self.current_pdf_pages = 0
        self.original_filename_components = {}
        self.pdf_path_var.set("Ingen PDF vald")
        self.date_var.set("")
        self.newspaper_var.set("")
        self.comment_var.set("")
        self.pages_var.set("")
