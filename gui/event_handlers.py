#!/usr/bin/env python3
"""
Event handler methods for DJs Timeline-maskin
Contains event handler mixin class extracted from main_window.py
"""

# Standard library imports
import logging
import os
import platform
import subprocess

# GUI imports
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

# Local imports
from core.filename_parser import FilenameParser
from core.pdf_processor import PDFProcessor

# Setup logging
logger = logging.getLogger(__name__)


class EventHandlersMixin:
    """Mixin class containing event handler methods"""

    def load_saved_excel_file(self):
        """Load previously saved Excel file if it exists"""
        excel_path = self.config.get('excel_file', '')
        if excel_path and Path(excel_path).exists():
            if self.excel_manager.load_excel_file(excel_path):
                self.excel_path_var.set(Path(excel_path).name)
                # No need to create fields - they're already created in setup_gui
                # Enable the "Open Excel" button for previously loaded file
                self.open_excel_btn.configure(state="normal")
                logger.info(f"Loaded saved Excel file: {excel_path}")

    def load_saved_output_folder(self):
        """Load previously saved output folder settings if they exist"""
        output_folder = self.config.get('output_folder', '')
        output_folder_locked = self.config.get('output_folder_locked', False)

        if output_folder and Path(output_folder).exists():
            # Store actual path and update display
            display_text = self.get_display_folder_text(output_folder)
            self.output_folder_var.set(display_text)
            self._actual_output_folder = output_folder
            logger.info(f"Loaded saved output folder: {output_folder}")
        else:
            self._actual_output_folder = ""

        # Load saved lock state
        self.output_folder_lock_var.set(output_folder_locked)
        logger.info(f"Loaded output folder lock state: {output_folder_locked}")

    def show_retry_cancel_dialog(self, title: str, message: str) -> str:
        """
        Show a custom dialog with 'Försök igen' and 'Avbryt' buttons

        Returns:
            'retry' if user clicks retry button
            'cancel' if user clicks cancel button
        """
        import tkinter as tk

        # Create custom dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"500x200+{x}+{y}")

        result = {'choice': 'cancel'}  # Default to cancel

        # Message frame
        msg_frame = tk.Frame(dialog)
        msg_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Message label
        msg_label = tk.Label(msg_frame, text=message, wraplength=450, justify="left", font=('Arial', 10))
        msg_label.pack(expand=True)

        # Button frame
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def on_retry():
            result['choice'] = 'retry'
            dialog.destroy()

        def on_cancel():
            result['choice'] = 'cancel'
            dialog.destroy()

        # Buttons
        cancel_btn = tk.Button(btn_frame, text="Avbryt", command=on_cancel,
                              font=('Arial', 10), width=12, bg='#f44336', fg='white')
        cancel_btn.pack(side="right", padx=(10, 0))

        retry_btn = tk.Button(btn_frame, text="Försök igen", command=on_retry,
                             font=('Arial', 10), width=12, bg='#4CAF50', fg='white')
        retry_btn.pack(side="right")

        # Handle window close button (X) as cancel
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

        # Wait for user response
        dialog.wait_window()

        return result['choice']

    def select_output_folder(self):
        """Select output folder for renamed PDF files"""
        current_folder = self.output_folder_var.get()
        initial_dir = current_folder if current_folder and Path(current_folder).exists() else str(Path.home())

        folder_path = filedialog.askdirectory(
            title="Välj mapp för omdöpta PDF-filer",
            initialdir=initial_dir
        )

        if folder_path:
            # Store actual path and update display (save folder but not lock state)
            self.config['output_folder'] = folder_path
            # Don't save lock state - it's session-only behavior
            self.config_manager.save_config(self.config)

            # Update display with friendly text
            display_text = self.get_display_folder_text(folder_path)
            self.output_folder_var.set(display_text)
            self._actual_output_folder = folder_path

            logger.info(f"Selected output folder: {folder_path}")

    def reset_output_folder(self):
        """Reset output folder selection and unlock auto-fill"""
        self.output_folder_var.set("")
        self.output_folder_lock_var.set(False)
        self._actual_output_folder = ""
        # Save folder reset to config (but not lock state - it's session-only)
        self.config['output_folder'] = ""
        self.config_manager.save_config(self.config)
        logger.info("Reset output folder selection")

    def open_output_folder(self):
        """Open the selected output folder in file explorer"""
        actual_folder = getattr(self, '_actual_output_folder', '')

        if not actual_folder:
            messagebox.showerror("Fel", "Ingen mapp är vald att öppna.")
            return

        if not Path(actual_folder).exists():
            messagebox.showerror("Fel", f"Mappen finns inte längre:\n{actual_folder}")
            return

        try:
            if platform.system() == 'Windows':
                os.startfile(actual_folder)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', actual_folder])
            else:  # Linux
                subprocess.run(['xdg-open', actual_folder])
            logger.info(f"Opened output folder: {actual_folder}")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna mappen: {str(e)}")
            logger.error(f"Error opening output folder: {e}")

    def get_display_folder_text(self, folder_path):
        """Get display text for output folder - show 'Samma mapp som pdf-filen' for PDF's parent directory"""
        if not folder_path:
            return ""

        # If we have a current PDF and the folder matches its parent directory
        if self.current_pdf_path:
            pdf_parent = str(Path(self.current_pdf_path).parent)
            if str(folder_path) == pdf_parent:
                return "Samma mapp som pdf-filen"

        return folder_path

    def update_output_folder_display(self):
        """Update the display text in the output folder entry"""
        current_folder = self.output_folder_var.get()
        display_text = self.get_display_folder_text(current_folder)
        # Store the actual path but display the user-friendly text
        self._actual_output_folder = current_folder
        self.output_folder_var.set(display_text)

    def on_output_folder_lock_change(self):
        """Handle output folder lock state changes and save to config"""
        # Check if trying to lock with empty folder
        if self.output_folder_lock_var.get():
            actual_folder = getattr(self, '_actual_output_folder', '')
            if not actual_folder:
                # Revert the switch and show error
                self.output_folder_lock_var.set(False)
                messagebox.showerror("Fel", "Du måste välja en mapp innan du kan låsa mappvalet.")
                return

        # Save lock state to config
        self.config['output_folder_locked'] = self.output_folder_lock_var.get()
        self.config_manager.save_config(self.config)

        if self.output_folder_lock_var.get():
            logger.info("Output folder lock enabled and saved to config")
        else:
            logger.info("Output folder lock disabled and saved to config")

    def select_excel_file(self):
        """Select Excel file for integration"""
        file_path = filedialog.askopenfilename(
            title="Välj Excel-fil",
            filetypes=[("Excel-filer", "*.xlsx"), ("Alla filer", "*.*")]
        )

        if file_path:
            # Ask if user wants to work with a copy
            result = messagebox.askyesnocancel(
                "Arbeta med kopia?",
                "Vill du skapa en kopia av Excel-filen att arbeta med?\n\n" +
                "Ja = Skapa kopia (rekommenderas)\n" +
                "Nej = Arbeta direkt med originalfilen\n" +
                "Avbryt = Avbryt filval"
            )

            if result is None:  # User clicked Cancel
                return
            elif result:  # User clicked Yes - create copy
                try:
                    # Ask user where to save the copy using "Save As" dialog
                    original_path = Path(file_path)
                    default_name = f"{original_path.stem}_kopia.xlsx"

                    copy_path = filedialog.asksaveasfilename(
                        title="Spara kopia som...",
                        defaultextension=".xlsx",
                        filetypes=[("Excel-filer", "*.xlsx"), ("Alla filer", "*.*")],
                        initialfile=default_name,
                        initialdir=str(original_path.parent)
                    )

                    if not copy_path:
                        return  # User cancelled the save dialog

                    # Create the copy
                    import shutil
                    shutil.copy2(file_path, copy_path)

                    # Use the copy
                    working_path = copy_path
                    self.excel_path_var.set(f"{Path(copy_path).name} (kopia)")

                    messagebox.showinfo("Kopia skapad",
                                      f"En kopia har skapats:\n{Path(copy_path).name}\n\n" +
                                      "Applikationen arbetar nu med kopian.")

                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte skapa kopia: {str(e)}")
                    return
            else:  # User clicked No - use original
                working_path = file_path
                self.excel_path_var.set(Path(file_path).name)

            # Load the Excel file (original or copy)
            if self.excel_manager.load_excel_file(working_path):
                # Validate that all required columns exist
                missing_columns = self.excel_manager.validate_excel_columns()
                if missing_columns:
                    error_msg = (
                        "Excel-filen saknar följande obligatoriska kolumner:\n\n" +
                        "• " + "\n• ".join(missing_columns) + "\n\n" +
                        "Vill du skapa en ny Excel-mall med alla rätta kolumner?"
                    )

                    if messagebox.askyesno("Kolumner saknas", error_msg):
                        # User wants to create template
                        self.dialog_manager.create_excel_template()
                        return
                    else:
                        # User doesn't want template, clear the selection
                        self.excel_path_var.set("")
                        self.excel_manager.excel_path = None
                        return

                # Save Excel file path to config for persistence
                self.config['excel_file'] = working_path
                self.config_manager.save_config(self.config)
                # Enable the "Open Excel" button after successful load
                self.open_excel_btn.configure(state="normal")
                logger.info(f"Selected Excel file: {working_path}")
            else:
                messagebox.showerror("Fel", "Kunde inte läsa Excel-filen")

    def open_excel_file(self):
        """Open the selected Excel file in external application"""
        if not self.excel_manager.excel_path:
            messagebox.showwarning("Varning", "Ingen Excel-fil vald")
            return

        # Check if file still exists
        if not Path(self.excel_manager.excel_path).exists():
            messagebox.showerror("Fil saknas",
                               f"Excel-filen kunde inte hittas:\n{Path(self.excel_manager.excel_path).name}\n\n" +
                               "Filen kan ha flyttats eller tagits bort.")
            # Disable the button since file is missing
            self.open_excel_btn.configure(state="disabled")
            return

        try:
            PDFProcessor.open_excel_externally(self.excel_manager.excel_path)
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna Excel-fil: {str(e)}")



    def on_filename_change(self, *args):
        """Called when filename components change - just for tracking"""
        # No UI changes needed, just track that changes were made
        pass

    def has_filename_changed(self) -> bool:
        """Check if current filename components differ from original"""
        if not self.current_pdf_path or not self.original_filename_components:
            return False

        current_components = {
            'date': self.date_var.get(),
            'newspaper': self.newspaper_var.get(),
            'comment': self.comment_var.get(),
            'pages': self.pages_var.get()
        }

        return current_components != self.original_filename_components

    def copy_filename_to_excel(self):
        """Kopiera filnamnskomponenter till Excel-fält"""
        if not self.excel_vars:
            messagebox.showwarning("Varning", "Ingen Excel-fil vald")
            return

        # Check if there are unsaved changes in Excel fields
        has_content = False
        for col_name, var in self.excel_vars.items():
            # Skip locked fields when checking for content
            if col_name in self.lock_vars and self.lock_vars[col_name].get():
                continue
            # Skip automatically calculated fields and Inlagd (will be preserved)
            if col_name == 'Dag' or col_name == 'Inlagd':
                continue

            if hasattr(var, 'get'):
                if hasattr(var, 'delete'):  # Text widget
                    content = var.get("1.0", tk.END).strip()
                    if content:
                        has_content = True
                        break
                else:  # StringVar
                    if var.get().strip():
                        has_content = True
                        break

        if has_content:
            result = messagebox.askyesno("Osparade ändringar",
                                       "Det finns innehåll i Excel-fälten som kommer att skrivas över. " +
                                       "Vill du fortsätta?")
            if not result:
                return

        # Get current filename components
        date = self.date_var.get()
        newspaper = self.newspaper_var.get()
        comment = self.comment_var.get()
        pages = self.pages_var.get()

        # Construct the new filename
        new_filename = FilenameParser.construct_filename(date, newspaper, comment, pages)

        # Clear all Excel fields first (except locked ones and Inlagd)
        for col_name, var in self.excel_vars.items():
            # Skip locked fields and automatically calculated fields
            if col_name in self.lock_vars and self.lock_vars[col_name].get():
                continue
            if col_name == 'Dag':  # Skip automatically calculated fields
                continue
            if col_name == 'Inlagd':  # Skip Inlagd to preserve today's date
                continue

            if hasattr(var, 'delete'):  # Text widget
                var.delete("1.0", tk.END)
            else:  # StringVar
                var.set("")

        # Update specific fields based on filename components
        if 'Händelse' in self.excel_vars:
            # Build content: comment + blankline + filename
            content_parts = []
            if comment.strip():
                content_parts.append(comment.strip())
            content_parts.append("")  # This creates the blank line
            content_parts.append(new_filename)

            content = "\n".join(content_parts)

            if hasattr(self.excel_vars['Händelse'], 'insert'):
                self.excel_vars['Händelse'].insert("1.0", content)
            else:
                self.excel_vars['Händelse'].set(content)

        if 'Startdatum' in self.excel_vars and date:
            # Only set if not locked
            if not (self.lock_vars.get('Startdatum', tk.BooleanVar()).get()):
                self.excel_vars['Startdatum'].set(date)

        if 'Källa1' in self.excel_vars:
            # Only set if not locked
            if not (self.lock_vars.get('Källa1', tk.BooleanVar()).get()):
                self.excel_vars['Källa1'].set(new_filename)

        self.excel_row_saved.set(False)

    def save_all_and_clear(self):
        """Main save function - rename file if changed and save Excel row if data exists"""

        # STEP 1: Determine what operations are needed
        needs_pdf_rename = self.current_pdf_path and self.has_filename_changed()

        # Check if Startdatum and Händelse both have content for Excel row
        startdatum_content = ""
        handelse_content = ""

        if self.excel_vars:
            if 'Startdatum' in self.excel_vars and hasattr(self.excel_vars['Startdatum'], 'get'):
                startdatum_content = self.excel_vars['Startdatum'].get().strip()

            if 'Händelse' in self.excel_vars and hasattr(self.excel_vars['Händelse'], 'get'):
                if hasattr(self.excel_vars['Händelse'], 'delete'):  # Text widget
                    handelse_content = self.excel_vars['Händelse'].get("1.0", tk.END).strip()
                else:  # StringVar
                    handelse_content = self.excel_vars['Händelse'].get().strip()

        needs_excel_row = startdatum_content and handelse_content

        # STEP 2: Handle different scenarios

        # Nothing to do at all
        if not needs_pdf_rename and not needs_excel_row:
            messagebox.showwarning(
                "Inget att göra",
                "Jag har inget att göra.\n\n" +
                "Välj en pdf att namnändra och/eller fyll i datum i Startdatum " +
                "och en beskrivning i Händelse-fältet."
            )
            return

        # Excel row needed but validation fails
        if needs_excel_row:
            # First validate all date and time fields
            if not self.validate_all_date_time_fields():
                return  # Date/time validation failed

        # If Excel row needed but one of the required fields is missing
        # (This shouldn't happen due to needs_excel_row check, but as safety)
        if (startdatum_content or handelse_content) and not (startdatum_content and handelse_content):
            messagebox.showwarning(
                "Obligatoriska fält saknas",
                "Både Startdatum och Händelse måste vara ifyllda för att en ny excelrad ska kunna skrivas.\n\n" +
                "Om du bara vill byta namn på en pdf så se till så att fälten Startdatum och Händelse är tomma."
            )
            # Focus on the empty field
            if not startdatum_content and 'Startdatum' in self.excel_vars:
                if hasattr(self.excel_vars['Startdatum'], 'focus'):
                    self.excel_vars['Startdatum'].focus()
            elif not handelse_content and 'Händelse' in self.excel_vars:
                if hasattr(self.excel_vars['Händelse'], 'focus'):
                    self.excel_vars['Händelse'].focus()
            return

        # STEP 3: Check if Excel file exists before proceeding (if Excel row needed)
        if needs_excel_row and self.excel_manager.excel_path and not Path(self.excel_manager.excel_path).exists():
            result = messagebox.askyesnocancel(
                "Excel-fil saknas",
                f"Excel-filen kunde inte hittas:\n{Path(self.excel_manager.excel_path).name}\n\n" +
                "Filen kan ha flyttats eller tagits bort.\n\n" +
                "Vill du:\n" +
                "• JA - Välj en ny Excel-fil\n" +
                "• NEJ - Fortsätt utan Excel-sparning (endast PDF-namnändring)\n" +
                "• AVBRYT - Avbryt hela operationen"
            )

            if result is None:  # Cancel
                return
            elif result:  # Yes - select new Excel file
                self.select_excel_file()
                if not self.excel_manager.excel_path or not Path(self.excel_manager.excel_path).exists():
                    return  # User didn't select a valid file
            else:  # No - continue without Excel saving
                needs_excel_row = False

        # STEP 4: Perform operations
        operations_performed = []

        # 4A. Rename PDF file if needed
        if needs_pdf_rename:
            # Check that PDF file still exists before attempting rename
            is_valid, error_msg = PDFProcessor.validate_pdf_file(self.current_pdf_path)
            if not is_valid:
                result = messagebox.askyesnocancel(
                    "PDF-fil saknas",
                    f"PDF-filen kunde inte hittas eller läsas:\n{error_msg}\n\n" +
                    "Vill du:\n" +
                    "• JA - Fortsätta med Excel-sparning (hoppa över filnamnändring)\n" +
                    "• NEJ - Välj en ny PDF-fil\n" +
                    "• AVBRYT - Avbryt hela operationen"
                )

                if result is None:  # Cancel
                    return
                elif result is False:  # No - select new PDF file
                    self.select_pdf_file()
                    if not self.current_pdf_path:
                        return  # User didn't select a file
                    # Try rename again with new file
                    if not self.rename_current_pdf():
                        return  # Rename failed, stop operation
                else:  # Yes - continue without rename
                    needs_pdf_rename = False  # Skip PDF rename
            else:
                # File exists, proceed with rename
                if self.rename_current_pdf():
                    operations_performed.append("PDF-filen har döpts om")
                else:
                    return  # Rename failed, stop operation

        # 4B. Save Excel row if needed
        if needs_excel_row:
            if not self.excel_manager.worksheet:
                messagebox.showwarning("Varning", "Ingen Excel-fil vald")
                return

            # Double-check file exists (in case it was moved after the initial check)
            if not self.excel_manager.excel_path or not Path(self.excel_manager.excel_path).exists():
                messagebox.showwarning("Varning", "Excel-filen är inte tillgänglig. Excel-raden sparas inte.")
            else:
                if self.save_excel_row():
                    operations_performed.append("Excel-rad har sparats")
                else:
                    messagebox.showerror("Fel", "Kunde inte spara Excel-raden")
                    return

        # STEP 5: Clear fields
        self.excel_field_manager.clear_excel_fields()
        self.clear_pdf_and_filename_fields()
        self.row_color_var.set("none")

        # STEP 6: Show appropriate status message
        pdf_renamed = "PDF-filen har döpts om" in operations_performed
        excel_saved = "Excel-rad har sparats" in operations_performed

        if pdf_renamed and excel_saved:
            # Both operations performed
            message = "Följande operationer genomfördes:\n• " + "\n• ".join(operations_performed)
            message += "\n• Alla fält har rensats (utom låsta och automatiska fält)"
            messagebox.showinfo("Sparat", message)
        elif pdf_renamed and not excel_saved:
            # Only PDF renamed
            messagebox.showinfo(
                "PDF namnändrad",
                "Pdf-filen har fått sitt nya namn.\n\n" +
                "Alla fält har rensats (utom låsta och automatiska fält)."
            )
        elif excel_saved and not pdf_renamed:
            # Only Excel row saved
            messagebox.showinfo(
                "Excel-rad skapad",
                "Den nya excelraden har skapats.\n" +
                "Alla fält har rensats (utom låsta och automatiska fält).\n\n" +
                "Grattis! Din timeline växer."
            )
        else:
            # This should never happen, but as fallback
            messagebox.showinfo("Klart", "Alla fält har rensats.")

    def clear_all_without_saving(self):
        """Clear all fields without saving anything"""
        # Check if there are unsaved changes
        unsaved_filename = self.current_pdf_path and self.has_filename_changed()
        unsaved_excel = not self.excel_row_saved.get()

        if unsaved_filename or unsaved_excel:
            changes = []
            if unsaved_filename:
                changes.append("osparade filnamnsändringar")
            if unsaved_excel:
                changes.append("osparade Excel-data")

            result = messagebox.askyesno("Osparade ändringar",
                                       f"Du har {' och '.join(changes)}. " +
                                       "Dessa kommer att gå förlorade. Vill du fortsätta?")
            if not result:
                return

        # Clear everything
        self.excel_field_manager.clear_excel_fields()
        self.clear_pdf_and_filename_fields()
        self.excel_row_saved.set(True)

        # Reset row color to default
        self.row_color_var.set("none")

        messagebox.showinfo("Rensat", "Alla fält har rensats (utom låsta och automatiska)")

    def on_closing(self):
        """Handle application closing"""
        # Check if there are unsaved changes
        unsaved_filename = self.current_pdf_path and self.has_filename_changed()
        unsaved_excel = not self.excel_row_saved.get()

        # Check for text in unlocked Excel fields (excluding automatic fields)
        unlocked_fields_with_content = []
        if self.excel_vars:
            for col_name, var in self.excel_vars.items():
                # Skip locked fields
                if col_name in self.lock_vars and self.lock_vars[col_name].get():
                    continue
                # Skip automatic fields that should be ignored
                if col_name in ['Dag', 'Inlagd']:
                    continue

                # Check if field has content
                content = ""
                if hasattr(var, 'get'):
                    if hasattr(var, 'delete'):  # Text widget
                        content = var.get("1.0", tk.END).strip()
                    else:  # StringVar
                        content = var.get().strip()

                if content:
                    unlocked_fields_with_content.append(col_name)

        # Show warning if there are unsaved changes or content in unlocked fields
        if unsaved_filename or unsaved_excel or unlocked_fields_with_content:
            changes = []
            if unsaved_filename:
                changes.append("osparade filnamnsändringar")
            if unsaved_excel:
                changes.append("osparade Excel-data")
            if unlocked_fields_with_content:
                changes.append(f"text i {len(unlocked_fields_with_content)} olåsta fält")

            result = messagebox.askyesno("Osparade ändringar",
                                       f"Du har {' och '.join(changes)}. " +
                                       "Dessa kommer att gå förlorade. Vill du avsluta ändå?")
            if not result:
                return

        # Save current window geometry with height limit enforcement
        current_geometry = self.root.geometry()
        try:
            # Calculate maximum allowed height for this screen
            screen_height = self.root.winfo_screenheight()
            try:
                available_height = self.root.winfo_height() if hasattr(self.root, 'winfo_height') else screen_height - 80
            except Exception:
                available_height = screen_height - 80
            max_height = min(max(int(available_height * 0.75), 700), 800)

            # Parse and limit geometry if needed using safe parser
            parsed = self.parse_geometry(current_geometry)
            if parsed:
                width, height, x_pos, y_pos = parsed

                if height > max_height:
                    # Save with limited height
                    limited_geometry = self.build_geometry(width, max_height, x_pos, y_pos)
                    self.config['window_geometry'] = limited_geometry
                    logger.info(f"Saved geometry with height limit: {current_geometry} -> {limited_geometry}")
                else:
                    self.config['window_geometry'] = current_geometry
                    logger.info(f"Saved geometry: {current_geometry}")
            else:
                self.config['window_geometry'] = current_geometry
        except Exception as e:
            logger.warning(f"Error limiting geometry on save: {e}")
            self.config['window_geometry'] = current_geometry

        # Save current output folder lock state
        self.config['output_folder_locked'] = self.output_folder_lock_var.get()

        self.config_manager.save_config(self.config)

        # Save locked fields data
        self.excel_field_manager.save_locked_fields_on_exit()

        self.root.destroy()

    def on_window_configure(self, event=None):
        """Handle window configuration changes"""
        # Only process events for the main window
        if event and event.widget != self.root:
            return

        # Skip processing for a few seconds after startup to avoid interfering with initial setup
        if not hasattr(self, '_startup_time'):
            import time
            self._startup_time = time.time()
            return

        import time
        if time.time() - self._startup_time < 3:  # Skip first 3 seconds
            return

        # DISABLED: Aggressive height limiting that prevented manual resizing
        # This was causing the window to jump back to 800px height on every resize attempt
        # Initial height limiting is still enforced during startup in setup_gui()

        # try:
        #     # Check if window height exceeds our limit
        #     current_geometry = self.root.geometry()
        #     parsed = self.parse_geometry(current_geometry)
        #     if parsed:
        #         width, height, x_pos, y_pos = parsed
        #
        #         # Calculate max allowed height
        #         screen_height = self.root.winfo_screenheight()
        #         available_height = screen_height - 80  # Conservative estimate
        #         max_height = min(max(int(available_height * 0.75), 700), 800)
        #
        #         if height > max_height:
        #             # Resize to max height
        #             limited_geometry = self.build_geometry(width, max_height, x_pos, y_pos)
        #             self.root.after_idle(lambda: self.root.geometry(limited_geometry))
        #             logger.info(f"Limited window height during configure: {height} -> {max_height}")
        #
        # except Exception as e:
        #     logger.warning(f"Error in window configure handler: {e}")

        pass  # Allow free resizing by user
