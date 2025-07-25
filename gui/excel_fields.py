"""
Excel field management for DJs Timeline-maskin
Contains all Excel field creation and management methods extracted from main_window.py
"""

# Standard library imports
import logging
import tkinter as tk
from typing import Dict, Tuple, Any, List

# Third-party GUI imports
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Local imports
from utils.constants import REQUIRED_EXCEL_COLUMNS

logger = logging.getLogger(__name__)


class ExcelFieldManager:
    """Manages Excel field creation, layout, and state management"""

    def __init__(self, parent_app):
        """Initialize Excel field manager with reference to parent application"""
        self.parent = parent_app
        
        # Text fields that support rich text formatting
        self.text_fields = {'Note1', 'Note2', 'Note3', 'Händelse'}

    def serialize_text_widget_formatting(self, text_widget) -> List[Dict[str, Any]]:
        """Serialize tkinter Text widget formatting to JSON-compatible format"""
        try:
            # Get all text content
            text_content = text_widget.get("1.0", "end-1c")
            if not text_content:
                return []
            
            # Get all tag ranges in the widget
            tag_ranges = []
            available_tags = ['bold', 'italic', 'red', 'blue', 'green', 'black']
            
            for tag in available_tags:
                ranges = text_widget.tag_ranges(tag)
                # tag_ranges returns pairs: (start1, end1, start2, end2, ...)
                for i in range(0, len(ranges), 2):
                    start_idx = ranges[i]
                    end_idx = ranges[i + 1]
                    
                    # Convert tkinter indices to character positions
                    start_pos = text_widget.index(start_idx)
                    end_pos = text_widget.index(end_idx)
                    
                    tag_ranges.append({
                        'tag': tag,
                        'start': start_pos,
                        'end': end_pos
                    })
            
            return tag_ranges
            
        except Exception as e:
            logger.error(f"Error serializing text widget formatting: {e}")
            return []

    def restore_text_widget_formatting(self, text_widget, format_data: List[Dict[str, Any]]) -> None:
        """Restore tkinter Text widget formatting from serialized format"""
        try:
            if not format_data:
                return
            
            # Apply each tag range
            for tag_info in format_data:
                tag = tag_info.get('tag')
                start = tag_info.get('start')
                end = tag_info.get('end')
                
                if tag and start and end:
                    try:
                        text_widget.tag_add(tag, start, end)
                    except tk.TclError as e:
                        logger.warning(f"Could not apply tag {tag} from {start} to {end}: {e}")
                        
        except Exception as e:
            logger.error(f"Error restoring text widget formatting: {e}")

    def collect_locked_field_data(self) -> Tuple[Dict[str, bool], Dict[str, str], Dict[str, Any]]:
        """Collect current locked field states, their contents, and rich text formatting"""
        try:
            locked_states = {}
            locked_contents = {}
            locked_formats = {}

            # Collect lock states
            for field_name, lock_var in self.parent.lock_vars.items():
                locked_states[field_name] = lock_var.get()

            # Collect field contents and formatting for locked fields
            for field_name in self.parent.lock_vars.keys():
                if locked_states.get(field_name, False):  # Only collect if locked
                    if field_name in self.parent.excel_vars:
                        var = self.parent.excel_vars[field_name]

                        # Handle different widget types
                        if hasattr(var, 'get') and hasattr(var, 'delete'):  # Text widget
                            content = var.get("1.0", "end-1c")  # Get all text except final newline
                            
                            # Collect rich text formatting for text fields
                            if field_name in self.text_fields and content.strip():
                                format_data = self.serialize_text_widget_formatting(var)
                                if format_data:
                                    locked_formats[field_name] = format_data
                                    logger.debug(f"Collected {len(format_data)} format tags for {field_name}")
                                    
                        elif hasattr(var, 'get'):  # StringVar or Entry
                            content = var.get()
                        else:
                            content = ""

                        if content.strip():  # Only save non-empty content
                            locked_contents[field_name] = content

            logger.info(f"Collected {len(locked_contents)} locked fields with content")
            logger.info(f"Collected {len(locked_formats)} fields with rich text formatting")
            return locked_states, locked_contents, locked_formats

        except Exception as e:
            logger.error(f"Error collecting locked field data: {e}")
            return {}, {}, {}

    def restore_locked_fields(self) -> None:
        """Restore locked field states, contents, and rich text formatting from saved configuration"""
        try:
            # Load saved locked fields data
            locked_states, locked_contents, locked_formats = self.parent.config_manager.load_locked_fields()

            if not locked_states and not locked_contents:
                logger.info("No saved locked fields to restore")
                return

            # Restore lock states
            for field_name, is_locked in locked_states.items():
                if field_name in self.parent.lock_vars:
                    self.parent.lock_vars[field_name].set(is_locked)
                    logger.debug(f"Restored lock state for {field_name}: {is_locked}")

            # Restore field contents for locked fields
            for field_name, content in locked_contents.items():
                if field_name in self.parent.excel_vars and locked_states.get(field_name, False):
                    var = self.parent.excel_vars[field_name]

                    # Handle different widget types
                    if hasattr(var, 'delete') and hasattr(var, 'insert'):  # Text widget
                        var.delete("1.0", tk.END)
                        var.insert("1.0", content)
                        
                        # Restore rich text formatting for text fields
                        if field_name in self.text_fields and field_name in locked_formats:
                            format_data = locked_formats[field_name]
                            self.restore_text_widget_formatting(var, format_data)
                            logger.debug(f"Restored {len(format_data)} format tags for {field_name}")
                            
                    elif hasattr(var, 'set'):  # StringVar
                        var.set(content)

                    logger.debug(f"Restored content for locked field {field_name}: {content[:50]}...")

            logger.info(f"Restored {len(locked_states)} lock states and {len(locked_contents)} field contents")
            if locked_formats:
                logger.info(f"Restored rich text formatting for {len(locked_formats)} fields")

        except Exception as e:
            logger.error(f"Error restoring locked fields: {e}")

    def save_locked_fields_on_exit(self) -> None:
        """Save current locked field states, contents, and rich text formatting before exit"""
        try:
            locked_states, locked_contents, locked_formats = self.collect_locked_field_data()

            if locked_states or locked_contents:
                self.parent.config_manager.save_locked_fields(locked_states, locked_contents, locked_formats)
                logger.info("Saved locked fields before exit")
                if locked_formats:
                    logger.info(f"Saved rich text formatting for {len(locked_formats)} fields")
            else:
                logger.info("No locked fields to save")

        except Exception as e:
            logger.error(f"Error saving locked fields on exit: {e}")

    def clear_excel_fields(self):
        """Clear Excel fields except locked ones and Inlagd"""
        for col_name, var in self.parent.excel_vars.items():
            # Skip locked fields
            if col_name in self.parent.lock_vars and self.parent.lock_vars[col_name].get():
                continue
            # Skip Inlagd - it should always maintain today's date
            if col_name == 'Inlagd':
                continue

            if hasattr(var, 'delete'):  # Text widget
                var.delete("1.0", tk.END)
                # Reset character counter for text fields
                if col_name in self.parent.char_counters:
                    limit = self.parent.handelse_char_limit if col_name == 'Händelse' else self.parent.char_limit
                    self.parent.char_counters[col_name].config(text=f"Tecken kvar: {limit}", bootstyle="success")
            else:  # StringVar
                var.set("")

    def create_excel_fields(self):
        """Create input fields for Excel columns in three-column layout"""
        # Clear existing fields
        for widget in self.parent.excel_fields_frame.winfo_children():
            widget.destroy()

        # Use static list of required columns instead of reading from Excel
        column_names = REQUIRED_EXCEL_COLUMNS

        # Clear and recreate excel_vars for all required columns
        self.parent.excel_vars.clear()
        for col_name in column_names:
            # Don't create variables for automatically calculated fields
            if col_name != 'Dag':
                self.parent.excel_vars[col_name] = tk.StringVar()

        # Auto-fill today's date in "Inlagd" field
        if 'Inlagd' in self.parent.excel_vars:
            from datetime import datetime
            today_date = datetime.now().strftime('%Y-%m-%d')
            self.parent.excel_vars['Inlagd'].set(today_date)

        # Create frame for Excel fields (responsive grid layout)
        fields_container = tb.Frame(self.parent.excel_fields_frame)
        fields_container.pack(fill="both", expand=True, pady=(5, 0))

        # Configure responsive row expansion
        fields_container.grid_rowconfigure(0, weight=1)

        # Define column groupings (updated with new field name)
        column1_fields = ['OBS', 'Inlagd', 'Kategori', 'Underkategori', 'Person/sak',
                         'Special', 'Dag', 'Källa1', 'Källa2', 'Källa3', 'Övrigt']
        column2_fields = ['Startdatum', 'Starttid', 'Slutdatum', 'Sluttid', 'Händelse']
        column3_fields = ['Note1', 'Note2', 'Note3']

        # Configure column weights for equal spacing - each column gets exactly 1/3 of available width
        # Use uniform to force exactly equal column distribution
        fields_container.grid_columnconfigure(0, weight=1, uniform="col")  # Left column - 1/3 of width
        fields_container.grid_columnconfigure(1, weight=1, uniform="col")  # Middle column - 1/3 of width
        fields_container.grid_columnconfigure(2, weight=1, uniform="col")  # Right column - 1/3 of width

        # Create Column 1
        col1_frame = tb.LabelFrame(fields_container, text="", padding=2)
        col1_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        col1_frame.grid_columnconfigure(0, weight=0)  # Field labels - fixed width
        col1_frame.grid_columnconfigure(1, weight=1)  # Entry fields - expand to fill space
        col1_frame.grid_columnconfigure(2, weight=0)  # Lock switches - fixed width
        # Configure rows to expand and use available vertical space
        for i in range(len(column1_fields)):
            col1_frame.grid_rowconfigure(i, weight=1)

        row = 0
        for col_name in column1_fields:
            rows_used = self.create_field_in_frame(col1_frame, col_name, row, column_type="column1")
            row += rows_used

        # Create Column 2
        col2_frame = tb.LabelFrame(fields_container, text="", padding=2)
        col2_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        col2_frame.grid_columnconfigure(0, weight=0)  # Field labels - fixed width
        col2_frame.grid_columnconfigure(1, weight=1)  # Entry fields - expand to fill space
        col2_frame.grid_columnconfigure(2, weight=0)  # Lock switches - fixed width

        row = 0
        for col_name in column2_fields:
            rows_used = self.create_field_in_frame(col2_frame, col_name, row, column_type="column2")
            # If this is Händelse, make its text widget row expandable
            if col_name == 'Händelse':
                col2_frame.grid_rowconfigure(row+2, weight=1)  # Text widget is at row+2
            row += rows_used

        # Create Column 3
        col3_frame = tb.LabelFrame(fields_container, text="", padding=(2, 2, 10, 2))  # Extra bottom padding for character counters
        col3_frame.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        col3_frame.grid_columnconfigure(0, weight=1)  # Make all content expand full width

        row = 0
        for col_name in column3_fields:
            rows_used = self.create_field_in_frame(col3_frame, col_name, row, column_type="column3")
            row += rows_used

    def create_field_in_frame(self, parent_frame, col_name, row, column_type="column1"):
        """Create a single field in the specified frame with layout optimized per column type"""
        # Check if this field should have a lock switch (all except Dag and Inlagd)
        has_lock = col_name in self.parent.lock_vars

        # Special handling for Dag column - make it read-only with explanation
        if col_name == 'Dag':
            # Standard horizontal layout for Dag field
            tb.Label(parent_frame, text=f"{col_name}:",
                    font=('Arial', 10)).grid(row=row, column=0, sticky="w", pady=(0, 5))

            dag_var = tk.StringVar(value="Formel läggs till automatiskt")
            entry = tb.Entry(parent_frame,
                           textvariable=dag_var,
                           state="readonly",
                           font=('Arial', 9, 'italic'))
            entry.grid(row=row, column=1, sticky="ew", pady=(0, 5))

            # Return 1 row used for Dag field
            return 1

        # Special handling for Inlagd - read-only, always today's date
        elif col_name == 'Inlagd':
            # Standard horizontal layout for Inlagd field
            tb.Label(parent_frame, text=f"{col_name}:",
                    font=('Arial', 10)).grid(row=row, column=0, sticky="w", pady=(0, 5))

            entry = tb.Entry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                           state="readonly",
                           font=('Arial', 9))
            entry.grid(row=row, column=1, sticky="ew", pady=(0, 5))

            # Return 1 row used for Inlagd field
            return 1

        # Special vertical layout for text fields with character counters (Händelse, Note1-3)
        elif col_name.startswith('Note') or col_name == 'Händelse':
            # Row 1: Field name and lock switch (if applicable)
            header_frame = tb.Frame(parent_frame)
            header_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))

            tb.Label(header_frame, text=f"{col_name}:",
                    font=('Arial', 10)).pack(side="left")

            # Add lock switch for text fields that should have one
            if has_lock:
                lock_switch = tb.Checkbutton(header_frame,
                                           text="Lås",
                                           variable=self.parent.lock_vars[col_name],
                                           bootstyle="success-round-toggle")
                lock_switch.pack(side="right")

            # Row 2: Text widget (full width)
            if col_name == 'Händelse':
                height = 22  # Match combined height of Note1-3 (8+8+6=22)
            elif col_name in ['Note1', 'Note2']:
                height = 8  # Increased from 6 to make character counters visible
            else:
                height = 6  # Increased from 4 (Note3 and other text fields)

            text_widget = tk.Text(parent_frame, height=height,
                                wrap=tk.WORD, font=('Arial', 9),
                                undo=True, maxundo=20)

            # Enable undo functionality for text widget
            self.parent.enable_undo_for_widget(text_widget)

            # Bind character count checking and paste handling
            text_widget.bind('<KeyRelease>',
                           lambda e, col=col_name: self.parent.check_character_count(e, col))
            text_widget.bind('<Button-1>',
                           lambda e, col=col_name: self.parent.root.after(1, lambda: self.parent.check_character_count(e, col)))
            text_widget.bind('<Control-v>',
                           lambda e, col=col_name: self.parent.dialog_manager.handle_paste_event(e, col))
            text_widget.bind('<<Paste>>',
                           lambda e, col=col_name: self.parent.dialog_manager.handle_paste_event(e, col))

            # Add improved undo handling for key presses that replace selected text
            text_widget.bind('<KeyPress>',
                           lambda e: self.parent.handle_text_key_press_undo(e))

            # Specific binding for Delete key to handle selection deletion
            text_widget.bind('<Delete>',
                           lambda e: self.parent.handle_delete_key_undo(e))
            text_widget.bind('<BackSpace>',
                           lambda e: self.parent.handle_delete_key_undo(e))

            # Configure formatting tags for rich text
            self.parent.setup_text_formatting_tags(text_widget)

            # Row 2.5: Formatting toolbar (compact)
            toolbar_frame = tb.Frame(parent_frame)
            toolbar_frame.grid(row=row+1, column=0, columnspan=2, sticky="w", pady=(2, 2))
            self.parent.create_formatting_toolbar(toolbar_frame, text_widget, col_name)

            # Move text widget to row+2 to make room for toolbar
            # Make Händelse expand vertically to fill available space
            if col_name == 'Händelse':
                text_widget.grid(row=row+2, column=0, columnspan=2, sticky="nsew", pady=(0, 2))
                # Configure the text widget row to expand vertically
                parent_frame.grid_rowconfigure(row+2, weight=1)
            else:
                text_widget.grid(row=row+2, column=0, columnspan=2, sticky="ew", pady=(0, 2))

            # Row 4: Character counter (left aligned, compact)
            limit = self.parent.handelse_char_limit if col_name == 'Händelse' else self.parent.char_limit
            counter_label = tb.Label(parent_frame, text=f"{limit}",
                                   font=('Arial', 8), bootstyle="success")
            counter_label.grid(row=row+3, column=0, sticky="w", pady=(5, 8))
            self.parent.char_counters[col_name] = counter_label

            # Store reference to text widget
            self.parent.excel_vars[col_name] = text_widget

            # Return the number of rows used (4 rows for text fields: header, toolbar, text, counter)
            return 4

        # Layout depends on column type and field type
        elif column_type == "column1" or (column_type == "column2" and col_name in ['Startdatum', 'Starttid', 'Slutdatum', 'Sluttid']):
            # Horizontal layout for column 1 and date fields in column 2 - saves vertical space
            tb.Label(parent_frame, text=f"{col_name}:",
                    font=('Arial', 10)).grid(row=row, column=0, sticky="w", pady=(0, 5))

            # Set appropriate width based on field type
            if col_name in ['Startdatum', 'Slutdatum']:
                # Date fields: 2025-07-25 (10 chars + padding)
                entry = tb.Entry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                               font=('Arial', 9), width=12)
                entry.grid(row=row, column=1, sticky="w", pady=(0, 5))
            elif col_name in ['Starttid', 'Sluttid']:
                # Time fields: 18:45 (5 chars + padding)
                entry = tb.Entry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                               font=('Arial', 9), width=7)
                entry.grid(row=row, column=1, sticky="w", pady=(0, 5))
            else:
                # Other fields: expand to fill available space
                entry = tb.Entry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                               font=('Arial', 9))
                entry.grid(row=row, column=1, sticky="ew", pady=(0, 5))

            # Enable undo tracking for Entry widget
            self.parent.enable_undo_for_widget(entry)

            # Add time validation for time fields
            if col_name in ['Starttid', 'Sluttid']:
                entry.bind('<FocusOut>', lambda e, field=col_name: self.parent.validate_time_field(e, field))

            # Add lock switch for fields that should have one (in column 2)
            if has_lock:
                lock_switch = tb.Checkbutton(parent_frame,
                                           text="Lås",
                                           variable=self.parent.lock_vars[col_name],
                                           bootstyle="success-round-toggle")
                lock_switch.grid(row=row, column=2, sticky="w", padx=(5, 0), pady=(0, 5))

            # Return 1 row used for horizontal layout
            return 1

        else:
            # Vertical layout for columns 2&3 - maximizes input field width
            # Row 1: Field name and lock switch
            header_frame = tb.Frame(parent_frame)
            header_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))

            tb.Label(header_frame, text=f"{col_name}:",
                    font=('Arial', 10)).pack(side="left")

            # Add lock switch for fields that should have one
            if has_lock:
                lock_switch = tb.Checkbutton(header_frame,
                                           text="Lås",
                                           variable=self.parent.lock_vars[col_name],
                                           bootstyle="success-round-toggle")
                lock_switch.pack(side="right")

            # Row 2: Entry field (full width)
            entry = tb.Entry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                           font=('Arial', 9))
            entry.grid(row=row+1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

            # Enable undo tracking for Entry widget
            self.parent.enable_undo_for_widget(entry)

            # Return 2 rows used for vertical layout
            return 2

        # Configure column weight for proper resizing (for all field types)
        parent_frame.grid_columnconfigure(0, weight=1)
        if parent_frame.grid_size()[0] > 1:  # If there are multiple columns
            parent_frame.grid_columnconfigure(1, weight=1)
