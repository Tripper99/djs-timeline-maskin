#!/usr/bin/env python3
"""
Excel operations mixin for DJs Timeline-maskin
Contains Excel saving, validation, and date/time handling methods
CRITICAL: This module contains sensitive hybrid Excel operations that must not be modified
"""

import logging
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    pass

from core.filename_parser import FilenameParser

logger = logging.getLogger(__name__)


class ExcelOperationsMixin:
    """Mixin class providing Excel operations - SENSITIVE: NO MODIFICATIONS"""

    def should_save_excel_row(self) -> bool:
        """Check if Excel row should be saved - now simplified"""
        # NOTE: This method is now mainly used by other parts of the code
        # The main save logic is handled directly in save_all_and_clear()

        if not self.excel_vars:
            return False

        # Check if both Startdatum and Händelse have content
        startdatum_content = ""
        if 'Startdatum' in self.excel_vars and hasattr(self.excel_vars['Startdatum'], 'get'):
            startdatum_content = self.excel_vars['Startdatum'].get().strip()

        handelse_content = ""
        if 'Händelse' in self.excel_vars and hasattr(self.excel_vars['Händelse'], 'get'):
            if hasattr(self.excel_vars['Händelse'], 'delete'):  # Text widget
                handelse_content = self.excel_vars['Händelse'].get("1.0", tk.END).strip()
            else:  # StringVar
                handelse_content = self.excel_vars['Händelse'].get().strip()

        # Simple rule: Excel row can only be saved if BOTH required fields have content
        return startdatum_content and handelse_content

    def save_excel_row(self) -> bool:
        """Save current Excel data as new row"""
        if not self.excel_manager.worksheet:
            return False

        # Check if Excel file still exists
        if not self.excel_manager.excel_path or not Path(self.excel_manager.excel_path).exists():
            messagebox.showerror("Excel-fil saknas",
                               f"Excel-filen kunde inte hittas:\n{self.excel_manager.excel_path}\n\n" +
                               "Filen kan ha flyttats eller tagits bort. Välj Excel-filen igen.")
            return False

        excel_data = {}

        # Get data from Excel fields
        for col_name, var in self.excel_vars.items():
            if hasattr(var, 'get'):
                if hasattr(var, 'delete'):  # It's a Text widget
                    # Extract formatted text for Excel
                    formatted_text = self.get_formatted_text_for_excel(var)

                    # Clean PDF text for text fields that commonly contain pasted PDF content
                    if col_name in ['Händelse', 'Note1', 'Note2', 'Note3']:
                        # If it's a RichText object, we need to handle cleaning differently
                        if hasattr(formatted_text, '__class__') and formatted_text.__class__.__name__ == 'RichText':
                            # For RichText, we keep the formatting but clean the plain text fallback
                            excel_data[col_name] = formatted_text
                        else:
                            # Plain text, clean it
                            excel_data[col_name] = FilenameParser.clean_pdf_text(formatted_text)
                    else:
                        excel_data[col_name] = formatted_text
                else:  # It's a StringVar (Entry widget)
                    excel_data[col_name] = var.get()
            else:
                excel_data[col_name] = ""

        # Handle Inlagd - always set today's date (field is read-only)
        if 'Inlagd' in self.excel_vars:
            excel_data['Inlagd'] = datetime.now().strftime('%Y-%m-%d')

        # Get filename for special handling
        filename = excel_data.get('Källa1', '')
        if not filename:
            # Only construct filename if we have actual content from PDF filename components
            date = self.date_var.get().strip()
            newspaper = self.newspaper_var.get().strip()
            comment = self.comment_var.get().strip()
            pages = self.pages_var.get().strip()

            # Only create filename if we have at least date or newspaper (indicating PDF was loaded)
            if date or newspaper:
                filename = FilenameParser.construct_filename(date, newspaper, comment, pages)
            else:
                filename = ""  # No filename if no PDF components exist

        # Add filename components for special handling
        excel_data['date'] = self.date_var.get()

        # Try to save with retry loop for file lock handling
        while True:
            result = self.excel_manager.add_row_with_xlsxwriter(excel_data, filename, self.row_color_var.get())

            if result is True:
                # Success
                self.stats['excel_rows_added'] += 1
                self.excel_row_saved.set(True)
                self.update_stats_display()
                logger.info(f"Added Excel row with data for: {filename}")
                return True
            elif result == "file_locked":
                # Excel file is locked - show retry/cancel dialog
                choice = self.show_retry_cancel_dialog(
                    "Excel-fil låst",
                    "Excel-filen används av ett annat program. " +
                    "Stäng programmet och försök igen."
                )
                if choice == 'cancel':
                    return False
                # If choice == 'retry', loop continues to try again
            else:
                # Other error
                return False

    def validate_all_date_time_fields(self) -> bool:
        """Validate all date and time fields before saving. Returns False if validation fails."""
        try:
            date_fields = ['Startdatum', 'Slutdatum']
            time_fields = ['Starttid', 'Sluttid']

            # Validate date fields
            for field_name in date_fields:
                if field_name in self.excel_vars:
                    current_value = self.excel_vars[field_name].get().strip()
                    if current_value:  # Only validate non-empty fields
                        is_valid, formatted_date, error_msg = self.validate_date_format(current_value)
                        if not is_valid:
                            messagebox.showerror(
                                "Ogiltigt datumformat",
                                f"Fel i fältet '{field_name}':\n\n{error_msg}\n\n"
                                f"Nuvarande värde: '{current_value}'\n\n"
                                "Korrigera datumet och försök igen."
                            )
                            return False
                        else:
                            # Update field with validated format
                            self.excel_vars[field_name].set(formatted_date)

            # Validate time fields
            for field_name in time_fields:
                if field_name in self.excel_vars:
                    current_value = self.excel_vars[field_name].get().strip()
                    if current_value:  # Only validate non-empty fields
                        is_valid, formatted_time, error_msg = self.validate_time_format(current_value)
                        if not is_valid:
                            messagebox.showerror(
                                "Ogiltigt tidsformat",
                                f"Fel i fältet '{field_name}':\n\n{error_msg}\n\n"
                                f"Nuvarande värde: '{current_value}'\n\n"
                                "Korrigera tiden och försök igen."
                            )
                            return False
                        else:
                            # Update field with validated format
                            self.excel_vars[field_name].set(formatted_time)

            return True  # All validations passed

        except Exception as e:
            logger.error(f"Error during date/time validation: {e}")
            messagebox.showerror(
                "Valideringsfel",
                f"Ett oväntat fel uppstod vid validering av datum/tid:\n\n{e}\n\n"
                "Kontrollera alla datum- och tidsfält och försök igen."
            )
            return False

    def validate_excel_data_before_save(self) -> bool:
        """Validate Excel data before saving - now simplified"""
        # NOTE: This method is now mainly used for date/time validation
        # The main Startdatum/Händelse validation is handled in save_all_and_clear()

        if not self.excel_vars:
            return True  # No Excel file loaded, nothing to validate

        # Only validate date and time fields
        return self.validate_all_date_time_fields()

    def check_character_count(self, event, column_name):
        """Check character count in text fields and update counter with color coding"""
        text_widget = event.widget
        content = text_widget.get("1.0", tk.END)
        # Remove the trailing newline that tk.Text always adds
        if content.endswith('\n'):
            content = content[:-1]

        char_count = len(content)
        limit = self.handelse_char_limit if column_name == 'Händelse' else self.char_limit

        # Update counter display (now inline with field label)
        if column_name in self.char_counters:
            counter_label = self.char_counters[column_name]

            # Update inline format: "Fieldname: (count/limit)"
            counter_label.configure(text=f"{column_name}: ({char_count}/{limit})")

        # Hard limit enforcement
        if char_count > limit:
            # Truncate to exact limit
            truncated_content = content[:limit]
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", truncated_content)

            # Update counter to show limit reached
            if column_name in self.char_counters:
                self.char_counters[column_name].configure(text=f"{column_name}: ({limit}/{limit})")

    def validate_time_format(self, time_input):
        """
        Validate and format time input for HH:MM format (24-hour system).

        Args:
            time_input (str): Time input from user

        Returns:
            tuple: (is_valid, formatted_time, error_message)
        """
        try:
            import re

            # Remove whitespace
            time_input = time_input.strip()

            # Return empty for empty input
            if not time_input:
                return True, "", ""

            # Pattern for HHMM format (auto-format to HH:MM)
            hhmm_pattern = r'^(\d{4})$'
            hhmm_match = re.match(hhmm_pattern, time_input)

            if hhmm_match:
                # Convert HHMM to HH:MM
                time_digits = hhmm_match.group(1)
                hour = int(time_digits[:2])
                minute = int(time_digits[2:])

                # Validate hour and minute ranges
                if hour > 23:
                    return False, time_input, f"Ogiltig timme: {hour}. Timme måste vara 00-23."
                if minute > 59:
                    return False, time_input, f"Ogiltig minut: {minute}. Minut måste vara 00-59."

                formatted_time = f"{hour:02d}:{minute:02d}"
                return True, formatted_time, ""

            # Pattern for HH:MM format
            hhMM_pattern = r'^(\d{1,2}):(\d{1,2})$'
            hhMM_match = re.match(hhMM_pattern, time_input)

            if hhMM_match:
                hour = int(hhMM_match.group(1))
                minute = int(hhMM_match.group(2))

                # Validate hour and minute ranges
                if hour > 23:
                    return False, time_input, f"Ogiltig timme: {hour}. Timme måste vara 00-23."
                if minute > 59:
                    return False, time_input, f"Ogiltig minut: {minute}. Minut måste vara 00-59."

                formatted_time = f"{hour:02d}:{minute:02d}"
                return True, formatted_time, ""

            # Invalid format
            return False, time_input, "Ogiltigt tidsformat. Använd HH:MM eller HHMM (24-timmars format)."

        except ValueError as e:
            return False, time_input, f"Ogiltigt tidsformat: {str(e)}"
        except Exception as e:
            logger.error(f"Error validating time format: {e}")
            return False, time_input, "Fel vid validering av tidsformat."

    def validate_time_field(self, event, field_name):
        """
        Validate time field on FocusOut event.

        Args:
            event: FocusOut event
            field_name (str): Name of the time field ('Starttid' or 'Sluttid')
        """
        print(f"DEBUG: validate_time_field called for {field_name}")
        try:
            entry_widget = event.widget
            current_value = entry_widget.get()
            print(f"DEBUG: Current value in {field_name}: '{current_value}'")

            # Validate the time format
            is_valid, formatted_time, error_message = self.validate_time_format(current_value)

            if is_valid:
                # Update the field with the formatted time
                if current_value != formatted_time:
                    print(f"DEBUG: Updating {field_name} - '{current_value}' → '{formatted_time}'")
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, formatted_time)

                    # CRITICAL: Update the StringVar that Excel uses
                    if field_name in self.excel_vars:
                        self.excel_vars[field_name].set(formatted_time)
                        print(f"DEBUG: StringVar updated for {field_name}: '{formatted_time}'")

                    logger.info(f"Auto-formatted {field_name}: '{current_value}' → '{formatted_time}'")
            else:
                # Show error message
                messagebox.showerror(
                    "Ogiltigt tidsformat",
                    f"Fel i fält '{field_name}': {error_message}"
                )
                # Focus back to the field for correction
                entry_widget.focus_set()

        except Exception as e:
            logger.error(f"Error validating time field {field_name}: {e}")

    def validate_date_format(self, date_input):
        """
        Validate and format date input for YYYY-MM-DD format.

        Supported input formats:
        - YYYY-MM-DD (target format, validated and kept as-is)
        - YYYYMMDD (converted to YYYY-MM-DD format)

        Rejected formats (require century specification):
        - YY-MM-DD (ambiguous century - could be 1900s or 2000s)
        - YYMMDD (ambiguous century - could be 1900s or 2000s)

        Args:
            date_input (str): Date input from user

        Returns:
            tuple: (is_valid, formatted_date, error_message)
        """
        print(f"DEBUG: validate_date_format called with input: '{date_input}'")
        try:
            import re

            # Remove whitespace
            date_input = date_input.strip()
            print(f"DEBUG: After trim: '{date_input}'")

            # Return empty for empty input
            if not date_input:
                return True, "", ""

            # Pattern for YYYY-MM-DD format (already correct)
            yyyy_mm_dd_pattern = r'^(\d{4})-(\d{1,2})-(\d{1,2})$'
            yyyy_mm_dd_match = re.match(yyyy_mm_dd_pattern, date_input)

            if yyyy_mm_dd_match:
                year = int(yyyy_mm_dd_match.group(1))
                month = int(yyyy_mm_dd_match.group(2))
                day = int(yyyy_mm_dd_match.group(3))

                # Validate the date using datetime
                try:
                    from datetime import datetime
                    datetime.strptime(f"{year}-{month:02d}-{day:02d}", '%Y-%m-%d')
                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                    return True, formatted_date, ""
                except ValueError:
                    return False, date_input, "Ogiltigt datum. Kontrollera år, månad och dag."

            # Check for ambiguous century formats FIRST (before YYYYMMDD check)
            yy_mm_dd_pattern = r'^(\d{2})-(\d{1,2})-(\d{1,2})$'
            yymmdd_pattern = r'^(\d{6})$'

            print(f"DEBUG: Checking century patterns for: '{date_input}'")
            if re.match(yy_mm_dd_pattern, date_input) or re.match(yymmdd_pattern, date_input):
                print(f"DEBUG: Century validation triggered - rejecting '{date_input}'")
                return False, date_input, "Du måste ange århundrade"

            # Pattern for YYYYMMDD format (8 digits, convert to YYYY-MM-DD)
            yyyymmdd_pattern = r'^(\d{8})$'
            yyyymmdd_match = re.match(yyyymmdd_pattern, date_input)

            print(f"DEBUG: Checking YYYYMMDD pattern for: '{date_input}'")
            if yyyymmdd_match:
                print("DEBUG: YYYYMMDD pattern matched")
                date_digits = yyyymmdd_match.group(1)
                year = int(date_digits[:4])
                month = int(date_digits[4:6])
                day = int(date_digits[6:8])

                # Validate the date using datetime
                try:
                    from datetime import datetime
                    datetime.strptime(f"{year}-{month:02d}-{day:02d}", '%Y-%m-%d')
                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                    print(f"DEBUG: YYYYMMDD converted: '{date_input}' → '{formatted_date}'")
                    return True, formatted_date, ""
                except ValueError:
                    print("DEBUG: YYYYMMDD validation failed - invalid date")
                    return False, date_input, "Ogiltigt datum. Kontrollera år, månad och dag."

            # Invalid format
            return False, date_input, "Ogiltigt datumformat. Använd YYYY-MM-DD eller YYYYMMDD."

        except ValueError as e:
            return False, date_input, f"Ogiltigt datumformat: {str(e)}"
        except Exception as e:
            logger.error(f"Error validating date format: {e}")
            return False, date_input, "Fel vid validering av datumformat."

    def validate_date_field(self, event, field_name):
        """
        Validate date field on FocusOut event.

        Args:
            event: FocusOut event
            field_name (str): Name of the date field ('Startdatum' or 'Slutdatum')
        """
        print(f"DEBUG: validate_date_field called for {field_name}")
        try:
            entry_widget = event.widget
            current_value = entry_widget.get()
            print(f"DEBUG: Current value in {field_name}: '{current_value}'")

            # Validate the date format
            is_valid, formatted_date, error_message = self.validate_date_format(current_value)

            if is_valid:
                # Update the field with the formatted date
                if current_value != formatted_date:
                    print(f"DEBUG: Updating {field_name} - '{current_value}' → '{formatted_date}'")
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, formatted_date)

                    # CRITICAL: Update the StringVar that Excel uses
                    if field_name in self.excel_vars:
                        self.excel_vars[field_name].set(formatted_date)
                        print(f"DEBUG: StringVar updated for {field_name}: '{formatted_date}'")

                    logger.info(f"Auto-formatted {field_name}: '{current_value}' → '{formatted_date}'")
            else:
                # Show error message
                messagebox.showerror(
                    "Ogiltigt datumformat",
                    f"Fel i fält '{field_name}': {error_message}"
                )
                # Focus back to the field for correction
                entry_widget.focus_set()

        except Exception as e:
            logger.error(f"Error validating date field {field_name}: {e}")
