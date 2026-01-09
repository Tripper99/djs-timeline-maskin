"""
Excel field management for DJs Timeline-maskin
Contains all Excel field creation and management methods extracted from main_window.py
"""

# Standard library imports
import logging
import tkinter as tk
from typing import Any, Dict, List, Tuple

# Third-party GUI imports
import customtkinter as ctk

from core.field_definitions import field_manager
from core.field_state_manager import field_state_manager
from gui.field_styling import apply_field_state
from gui.utils import ScrollableText

# Local imports

logger = logging.getLogger(__name__)


class ExcelFieldManager:
    """Manages Excel field creation, layout, and state management"""

    def __init__(self, parent_app):
        """Initialize Excel field manager with reference to parent application"""
        self.parent = parent_app

        # Text fields that support rich text formatting (using internal IDs)
        self.text_field_ids = {'note1', 'note2', 'note3', 'handelse'}

    def _is_text_field(self, field_id: str) -> bool:
        """Check if a field is a text field that supports rich text formatting"""
        return field_id in self.text_field_ids

    def _get_field_id_from_display_name(self, display_name: str) -> str:
        """Get internal field ID from display name"""
        internal_id = field_manager.get_internal_id(display_name)
        return internal_id if internal_id else display_name.lower()

    def _connect_entry_to_stringvar(self, entry_widget, string_var):
        """Manually connect Entry widget to StringVar while preserving placeholder text"""
        # Set initial value from StringVar if it has content
        initial_value = string_var.get()
        if initial_value:
            entry_widget.insert(0, initial_value)

        # Bind Entry changes to update StringVar
        def on_entry_change(*args):
            string_var.set(entry_widget.get())

        # Bind StringVar changes to update Entry
        def on_var_change(*args):
            current_entry_value = entry_widget.get()
            new_var_value = string_var.get()
            if current_entry_value != new_var_value:
                entry_widget.delete(0, 'end')
                if new_var_value:  # Only insert if not empty (preserve placeholder)
                    entry_widget.insert(0, new_var_value)

        # Bind events
        entry_widget.bind('<KeyRelease>', on_entry_change)
        entry_widget.bind('<FocusOut>', on_entry_change)
        string_var.trace('w', on_var_change)

    def _setup_date_field_focus(self, entry_widget, field_name):
        """Setup enhanced focus behavior for date fields with click-to-clear"""
        # Enhanced focus behavior
        entry_widget.bind('<FocusIn>', lambda e: self._on_date_focus_in(entry_widget))
        entry_widget.bind('<FocusOut>', lambda e: self._on_date_focus_out(entry_widget), add='+')

        # Click-to-clear behavior (only clear on first click if field has focus)
        def on_click(event):
            # If the widget is already focused and has content, offer to clear
            if entry_widget.focus_get() == entry_widget:
                current_value = entry_widget.get()
                if current_value.strip():
                    # Clear the field on click when focused
                    entry_widget.delete(0, 'end')

        entry_widget.bind('<Button-1>', on_click, add='+')

    def _on_date_focus_in(self, entry_widget):
        """Enhanced focus in behavior for date fields"""
        entry_widget.configure(border_color="#2196F3", border_width=2)

    def _on_date_focus_out(self, entry_widget):
        """Enhanced focus out behavior for date fields"""
        entry_widget.configure(border_color="#E0E0E0", border_width=1)

    def _setup_time_field_focus(self, entry_widget, field_name):
        """Setup enhanced focus behavior for time fields with click-to-clear"""
        # Enhanced focus behavior (same as date fields)
        entry_widget.bind('<FocusIn>', lambda e: self._on_time_focus_in(entry_widget))
        entry_widget.bind('<FocusOut>', lambda e: self._on_time_focus_out(entry_widget), add='+')

        # Click-to-clear behavior (only clear on first click if field has focus)
        def on_click(event):
            # If the widget is already focused and has content, offer to clear
            if entry_widget.focus_get() == entry_widget:
                current_value = entry_widget.get()
                if current_value.strip():
                    # Clear the field on click when focused
                    entry_widget.delete(0, 'end')

        entry_widget.bind('<Button-1>', on_click, add='+')

    def _on_time_focus_in(self, entry_widget):
        """Enhanced focus in behavior for time fields"""
        entry_widget.configure(border_color="#2196F3", border_width=2)

    def _on_time_focus_out(self, entry_widget):
        """Enhanced focus out behavior for time fields"""
        entry_widget.configure(border_color="#E0E0E0", border_width=1)

    def _setup_left_column_field_focus(self, entry_widget, field_name):
        """Setup enhanced focus behavior for left column fields"""
        # Enhanced focus behavior
        entry_widget.bind('<FocusIn>', lambda e: self._on_left_column_focus_in(entry_widget))
        entry_widget.bind('<FocusOut>', lambda e: self._on_left_column_focus_out(entry_widget), add='+')

    def _on_left_column_focus_in(self, entry_widget):
        """Enhanced focus in behavior for left column fields"""
        entry_widget.configure(border_color="#2196F3", border_width=2)

    def _on_left_column_focus_out(self, entry_widget):
        """Enhanced focus out behavior for left column fields"""
        entry_widget.configure(border_color="#E0E0E0", border_width=1)

    def serialize_text_widget_formatting(self, text_widget) -> List[Dict[str, Any]]:
        """Serialize tkinter Text widget formatting to JSON-compatible format"""
        try:
            # Get all text content
            text_content = text_widget.get("1.0", "end-1c")
            if not text_content:
                return []

            # Get all tag ranges in the widget
            tag_ranges = []
            available_tags = ['bold', 'red', 'blue', 'green', 'black']

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
                # Reset character counter for text fields (now inline format)
                if col_name in self.parent.char_counters:
                    limit = self.parent.handelse_char_limit if col_name == 'Händelse' else self.parent.char_limit
                    self.parent.char_counters[col_name].configure(text=f"{col_name}: (0/{limit})")
            else:  # StringVar
                var.set("")

    def create_excel_fields(self):
        """Create input fields for Excel columns in three-column layout"""
        # Clear existing fields
        for widget in self.parent.excel_fields_frame.winfo_children():
            widget.destroy()

        # Get ALL fields from field manager - we now show all fields, just disabled
        from core.field_definitions import FIELD_ORDER
        all_field_ids = FIELD_ORDER
        disabled_field_ids = field_state_manager.get_disabled_fields()
        enabled_field_ids = [f for f in all_field_ids if f not in disabled_field_ids]

        logger.info(f"Creating Excel fields for {len(all_field_ids)} total fields")
        logger.info(f"Disabled fields: {disabled_field_ids}")
        logger.info(f"Enabled fields: {enabled_field_ids}")

        # Clear and recreate excel_vars for ALL columns
        self.parent.excel_vars.clear()
        for field_id in all_field_ids:
            display_name = field_manager.get_display_name(field_id)
            # Don't create variables for automatically calculated fields
            if field_id != 'dag':
                self.parent.excel_vars[display_name] = tk.StringVar()

        # Auto-fill today's date in "Inlagd" field
        inlagd_display_name = field_manager.get_display_name('inlagd')
        if inlagd_display_name in self.parent.excel_vars:
            from datetime import datetime
            today_date = datetime.now().strftime('%Y-%m-%d')
            self.parent.excel_vars[inlagd_display_name].set(today_date)

        # Create resizable PanedWindow for Excel fields
        fields_container = tk.PanedWindow(self.parent.excel_fields_frame, orient="horizontal")
        fields_container.pack(fill="both", expand=True, pady=(5, 0))

        # Define column groupings using field manager to get current display names
        # Get field IDs for each column and convert to display names
        logger.debug(f"DEBUG: field_manager custom names at UI creation: {field_manager.get_custom_names()}")

        column1_field_ids = field_manager.get_fields_by_column('column1')
        # Include ALL fields in the column, both enabled and disabled
        column1_fields = [field_manager.get_display_name(field_id) for field_id in all_field_ids
                         if field_id in column1_field_ids]
        logger.debug(f"DEBUG: Column1 field IDs: {column1_field_ids}")
        logger.debug(f"DEBUG: Column1 display names (all): {column1_fields}")

        column3_field_ids = field_manager.get_fields_by_column('column3')
        # Include ALL fields in the column, both enabled and disabled
        column3_fields = [field_manager.get_display_name(field_id) for field_id in all_field_ids
                         if field_id in column3_field_ids]
        logger.debug(f"DEBUG: Column3 field IDs: {column3_field_ids}")
        logger.debug(f"DEBUG: Column3 display names (all): {column3_fields}")

        # Create Column 1 (Left)
        col1_frame = ctk.CTkFrame(fields_container)
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

        # Add Column 1 to PanedWindow
        fields_container.add(col1_frame, minsize=300)  # Minimum width to prevent over-compression

        # Create Column 2 (Middle) - Exclusively for Händelse
        col2_frame = ctk.CTkFrame(fields_container)
        col2_frame.grid_columnconfigure(0, weight=1)  # Content takes full width
        col2_frame.grid_rowconfigure(2, weight=1)  # Text widget row expands to fill available space

        # Create Händelse field directly in the column (using current display name)
        handelse_display_name = field_manager.get_display_name('handelse')
        self.create_field_in_frame(col2_frame, handelse_display_name, 0, column_type="column2")

        # Add operations box under Händelse field
        self.create_operations_box(col2_frame)

        # Add Column 2 to PanedWindow
        fields_container.add(col2_frame, minsize=200)  # Minimum width for Händelse

        # Create Column 3 (Right)
        col3_frame = ctk.CTkFrame(fields_container)
        col3_frame.grid_columnconfigure(0, weight=1)  # Make all content expand full width

        row = 0
        for col_name in column3_fields:
            rows_used = self.create_field_in_frame(col3_frame, col_name, row, column_type="column3")
            row += rows_used

        # Add Column 3 to PanedWindow
        fields_container.add(col3_frame, minsize=200)  # Minimum width for Note fields

        # Store reference to PanedWindow for position saving/restoring
        self.parent.excel_fields_paned_window = fields_container

        # Set initial sash positions for approximately 30/35/35 distribution
        # Schedule this for after the window is displayed and has a known width
        # Use multiple attempts with increasing delays to ensure proper width
        self.parent.root.after(500, lambda: self._set_initial_sash_positions_with_retry(fields_container, attempt=1))

    def _set_initial_sash_positions_with_retry(self, panedwindow, attempt=1, max_attempts=5):
        """Set initial sash positions with retry logic for proper width detection"""
        try:
            # Get the current width of the panedwindow
            panedwindow.update_idletasks()
            total_width = panedwindow.winfo_width()
            min_required_width = 800  # Minimum reasonable width for 3 columns

            logger.info(f"SASH RETRY {attempt}: Panedwindow width: {total_width} (min required: {min_required_width})")

            if total_width >= min_required_width:
                # Width is good, proceed with positioning
                logger.info(f"SASH RETRY {attempt}: Width sufficient, setting positions")
                self._set_initial_sash_positions(panedwindow)
            elif attempt < max_attempts:
                # Width too small, retry with longer delay
                retry_delay = 300 * attempt  # Increasing delay: 300ms, 600ms, 900ms, etc.
                logger.info(f"SASH RETRY {attempt}: Width too small ({total_width}), retrying in {retry_delay}ms")
                self.parent.root.after(retry_delay, lambda: self._set_initial_sash_positions_with_retry(panedwindow, attempt + 1, max_attempts))
            else:
                # All attempts failed, use whatever width we have
                logger.warning(f"SASH RETRY {attempt}: All attempts failed, using width {total_width}")
                self._set_initial_sash_positions(panedwindow)

        except Exception as e:
            logger.error(f"Error in sash positioning retry {attempt}: {e}")

    def _set_initial_sash_positions(self, panedwindow):
        """Set initial sash positions - restore saved positions or use 40/30/30 distribution"""
        try:
            # Get the current width of the panedwindow
            panedwindow.update_idletasks()
            total_width = panedwindow.winfo_width()
            min_reasonable_width = 800  # Minimum width for 3 columns with proper proportions
            logger.info(f"SASH DEBUG: Panedwindow total width: {total_width} (min reasonable: {min_reasonable_width})")

            if total_width >= min_reasonable_width:  # Only set if we have a reasonable width
                # Try to restore saved sash positions
                saved_positions = self.parent.config.get('excel_sash_positions', None)
                logger.info(f"SASH DEBUG: Saved positions from config: {saved_positions}")

                if saved_positions and len(saved_positions) == 2:
                    # Restore saved positions (scaled to current width if needed)
                    saved_width = self.parent.config.get('excel_sash_total_width', total_width)
                    logger.info(f"SASH DEBUG: Saved width: {saved_width}, current width: {total_width}")
                    if saved_width > 0:
                        # Scale positions proportionally to current width
                        scale_factor = total_width / saved_width
                        pos1 = min(int(saved_positions[0] * scale_factor), total_width - 400)  # Leave space for other columns
                        pos2 = min(int(saved_positions[1] * scale_factor), total_width - 200)  # Leave space for right column

                        # Ensure logical ordering
                        if pos1 >= pos2:
                            pos2 = pos1 + 200

                        panedwindow.sash_place(0, pos1, 0)
                        panedwindow.sash_place(1, pos2, 0)
                        logger.info(f"Restored sash positions: {pos1}, {pos2} (scaled from {saved_positions})")
                    else:
                        # Fallback to default if saved width is invalid
                        self._set_default_sash_positions(panedwindow, total_width)
                else:
                    # No saved positions, use default 30/35/35 distribution
                    logger.info("SASH DEBUG: No saved positions found, using default 30/35/35")
                    self._set_default_sash_positions(panedwindow, total_width)
            else:
                logger.warning(f"SASH DEBUG: Total width too small ({total_width} < {min_reasonable_width}), skipping sash positioning")

        except Exception as e:
            logger.error(f"Error setting sash positions: {e}")

    def _set_default_sash_positions(self, panedwindow, total_width):
        """Set default 30/35/35 sash positions"""
        try:
            # Calculate positions for 30/35/35 split
            pos1 = int(total_width * 0.3)  # 30% for left column
            pos2 = int(total_width * 0.65)  # 65% for left+middle columns

            # Validate positions make sense
            min_col_width = 200  # Minimum column width
            if pos1 < min_col_width:
                pos1 = min_col_width
            if pos2 < pos1 + min_col_width:
                pos2 = pos1 + min_col_width
            if total_width - pos2 < min_col_width:
                pos2 = total_width - min_col_width

            # Set sash positions
            panedwindow.sash_place(0, pos1, 0)  # First sash at 40%
            panedwindow.sash_place(1, pos2, 0)  # Second sash at 70%

            # Calculate actual proportions for verification
            col1_pct = (pos1 / total_width) * 100
            col2_pct = ((pos2 - pos1) / total_width) * 100
            col3_pct = ((total_width - pos2) / total_width) * 100

            logger.info(f"Set default sash positions - Width: {total_width}, Pos1: {pos1}, Pos2: {pos2}")
            logger.info(f"Actual proportions: {col1_pct:.1f}% / {col2_pct:.1f}% / {col3_pct:.1f}%")
        except Exception as e:
            logger.error(f"Error setting default sash positions: {e}")

    def create_field_in_frame(self, parent_frame, col_name, row, column_type="column1"):
        """Create a single field in the specified frame with layout optimized per column type"""
        # Get internal field ID for this display name
        field_id = self._get_field_id_from_display_name(col_name)

        # Check if this field is disabled
        is_field_disabled = field_state_manager.is_field_disabled(field_id)
        logger.debug(f"DEBUG: Field '{col_name}' (field_id: {field_id}) is_disabled: {is_field_disabled}")

        # Check if this field should have a lock switch (all except Dag and Inlagd)
        has_lock = col_name in self.parent.lock_vars
        logger.debug(f"DEBUG: Creating field '{col_name}' (field_id: {field_id})")
        logger.debug(f"DEBUG: Available lock_vars keys: {list(self.parent.lock_vars.keys())}")
        logger.debug(f"DEBUG: Field '{col_name}' has_lock: {has_lock}")

        # Special handling for Dag column - make it read-only with explanation
        if field_id == 'dag':
            # Standard horizontal layout for Dag field
            dag_label = ctk.CTkLabel(parent_frame, text=f"{col_name}:",
                    font=ctk.CTkFont(size=12))
            dag_label.grid(row=row, column=0, sticky="w", padx=(3, 2), pady=(0, 1))

            dag_var = tk.StringVar(value="Formel läggs till automatiskt")
            entry = ctk.CTkEntry(parent_frame,
                           textvariable=dag_var,
                           state="readonly",
                           font=ctk.CTkFont(size=12, slant='italic'))
            entry.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=(0, 5))

            # Apply disabled styling if field is disabled
            if is_field_disabled:
                field_widgets = {'label': dag_label, 'input': entry}
                apply_field_state(field_widgets, field_id, is_field_disabled)

            # Return 1 row used for Dag field
            return 1

        # Special handling for Inlagd - read-only, always today's date
        elif field_id == 'inlagd':
            # Standard horizontal layout for Inlagd field
            inlagd_label = ctk.CTkLabel(parent_frame, text=f"{col_name}:",
                    font=ctk.CTkFont(size=12))
            inlagd_label.grid(row=row, column=0, sticky="w", padx=(3, 2), pady=(0, 1))

            entry = ctk.CTkEntry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                           state="readonly",
                           font=ctk.CTkFont(size=12))
            entry.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=(0, 5))

            # Apply disabled styling if field is disabled
            if is_field_disabled:
                field_widgets = {'label': inlagd_label, 'input': entry}
                apply_field_state(field_widgets, field_id, is_field_disabled)

            # Return 1 row used for Inlagd field
            return 1

        # Special vertical layout for text fields with character counters (Händelse, Note1-3)
        elif self._is_text_field(field_id):
            # Row 1: Field name with inline character counter and lock switch (if applicable)
            header_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
            header_frame.grid(row=row, column=0, columnspan=2, sticky="new", pady=(0, 2))

            # Create label with inline character counter
            limit = self.parent.handelse_char_limit if field_id == 'handelse' else self.parent.char_limit
            label_text = f"{col_name}: (0/{limit})"
            field_label = ctk.CTkLabel(header_frame, text=label_text, font=ctk.CTkFont(size=12))
            field_label.pack(side="left", padx=(3, 2))
            # Store reference for counter updates
            self.parent.char_counters[col_name] = field_label

            # Add lock switch for text fields that should have one - compact with lock symbol
            if has_lock:
                lock_switch = ctk.CTkCheckBox(header_frame,
                                           text="🔒",
                                           width=18,
                                           variable=self.parent.lock_vars[col_name],
                                           font=ctk.CTkFont(size=12))
                lock_switch.pack(side="right")

            # Row 2: Text widget (full width)
            if field_id == 'handelse':
                height = 22  # Match combined height of Note1-3 (8+8+6=22)
            elif field_id in ['note1', 'note2']:
                height = 8  # Increased from 6 to make character counters visible
            else:
                height = 6  # Increased from 4 (Note3 and other text fields)

            # Create scrollable text widget container
            scrollable_text = ScrollableText(parent_frame, height=height,
                                           wrap=tk.WORD, font=('Arial', 9),
                                           undo=True, maxundo=20)

            # Get reference to the actual text widget for bindings
            text_widget = scrollable_text.text_widget

            # Enable undo functionality for text widget
            self.parent.enable_undo_for_widget(text_widget)

            # NUCLEAR OPTION: Direct paste binding to bypass all tkinter hierarchy issues
            # This binds directly to the actual Text widget, not the ScrollableText wrapper
            text_widget.bind('<Control-v>', lambda e: self.parent.handle_paste_undo(text_widget))
            text_widget.bind('<<Paste>>', lambda e: 'break')  # Disable built-in paste

            # Bind character count checking
            text_widget.bind('<KeyRelease>',
                           lambda e, col=col_name: self.parent.check_character_count(e, col))
            text_widget.bind('<Button-1>',
                           lambda e, col=col_name: self.parent.root.after(1, lambda: self.parent.check_character_count(e, col)))

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
            toolbar_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
            toolbar_frame.grid(row=row+1, column=0, columnspan=2, sticky="nw", padx=(10, 5), pady=(2, 2))
            self.parent.create_formatting_toolbar(toolbar_frame, text_widget, col_name, field_id)

            # Move scrollable text container to row+2 to make room for toolbar
            # Make Händelse expand vertically to fill available space
            if field_id == 'handelse':
                scrollable_text.grid(row=row+2, column=0, columnspan=2, sticky="new", padx=(3, 3), pady=(0, 1))
                # Configure the text widget row to expand vertically
                parent_frame.grid_rowconfigure(row+2, weight=1)
            else:
                scrollable_text.grid(row=row+2, column=0, columnspan=2, sticky="ew", padx=(3, 3), pady=(0, 1))
                # FIX: Configure Note field rows to maintain fixed physical size regardless of font size
                # This prevents the fields from growing when font size increases
                if field_id in ['note1', 'note2', 'note3']:
                    parent_frame.grid_rowconfigure(row+2, weight=1)

            # Store reference to scrollable text container (delegation will handle method calls)
            self.parent.excel_vars[col_name] = scrollable_text

            # Apply disabled styling if field is disabled
            if is_field_disabled:
                field_widgets = {'label': field_label, 'input': text_widget}
                if has_lock:
                    field_widgets['checkbox'] = lock_switch
                apply_field_state(field_widgets, field_id, is_field_disabled)

            # Return the number of rows used (3 rows for text fields: header, toolbar, text - counter is now inline)
            return 3

        # Layout depends on column type and field type
        elif column_type == "column1":
            # Horizontal layout for column 1 and date fields in column 2 - saves vertical space
            field_label = ctk.CTkLabel(parent_frame, text=f"{col_name}:",
                    font=ctk.CTkFont(size=12))
            field_label.grid(row=row, column=0, sticky="w", padx=(3, 2), pady=(0, 1))

            # Set appropriate width based on field type - reduced height
            if field_id in ['startdatum', 'slutdatum']:
                # Date fields: 2025-07-25 (10 chars + padding) with placeholder
                entry = ctk.CTkEntry(parent_frame,
                               font=ctk.CTkFont(size=11), width=120, height=22,
                               placeholder_text="YYYY-MM-DD")
                entry.grid(row=row, column=1, sticky="w", padx=(2, 3), pady=(0, 1))
                # Manual connection to StringVar while preserving placeholder
                self._connect_entry_to_stringvar(entry, self.parent.excel_vars[col_name])
            elif field_id in ['starttid', 'sluttid']:
                # Time fields: 18:45 (5 chars + padding) with placeholder
                entry = ctk.CTkEntry(parent_frame,
                               font=ctk.CTkFont(size=11), width=80, height=22,
                               placeholder_text="HH:MM")
                entry.grid(row=row, column=1, sticky="w", padx=(2, 3), pady=(0, 1))
                # Manual connection to StringVar while preserving placeholder
                self._connect_entry_to_stringvar(entry, self.parent.excel_vars[col_name])
            else:
                # Other fields: expand to fill available space with enhanced focus styling
                entry = ctk.CTkEntry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                               font=ctk.CTkFont(size=11), height=22,
                               border_color="#E0E0E0", border_width=1, fg_color="#F8F8F8")
                entry.grid(row=row, column=1, sticky="ew", padx=(2, 3), pady=(0, 1))

            # Enable undo tracking for Entry widget
            self.parent.enable_undo_for_widget(entry)

            # Add enhanced focus behavior for left column fields (excluding date/time fields)
            if col_name not in ['Startdatum', 'Slutdatum', 'Starttid', 'Sluttid']:
                self._setup_left_column_field_focus(entry, col_name)

            # Note: Time field validation removed to match date field behavior
            # Time validation will still occur during save operations

            # Add lock switch for fields that should have one (in column 2) - compact with lock symbol
            lock_switch = None
            if has_lock:
                lock_switch = ctk.CTkCheckBox(parent_frame,
                                           text="🔒",
                                           width=18,
                                           variable=self.parent.lock_vars[col_name],
                                           font=ctk.CTkFont(size=12))
                lock_switch.grid(row=row, column=2, sticky="w", padx=(2, 3), pady=(0, 1))

            # Apply disabled styling if field is disabled
            if is_field_disabled:
                field_widgets = {'label': field_label, 'input': entry}
                if lock_switch:
                    field_widgets['checkbox'] = lock_switch
                apply_field_state(field_widgets, field_id, is_field_disabled)

            # Return 1 row used for horizontal layout
            return 1

        else:
            # Vertical layout for columns 2&3 - maximizes input field width
            # Row 1: Field name and lock switch
            header_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
            header_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))

            field_label = ctk.CTkLabel(header_frame, text=f"{col_name}:",
                    font=ctk.CTkFont(size=12))
            field_label.pack(side="left", padx=(3, 2))

            # Add lock switch for fields that should have one - compact with lock symbol
            lock_switch = None
            if has_lock:
                lock_switch = ctk.CTkCheckBox(header_frame,
                                           text="🔒",
                                           width=18,
                                           variable=self.parent.lock_vars[col_name],
                                           font=ctk.CTkFont(size=12))
                lock_switch.pack(side="right")

            # Row 2: Entry field (full width)
            entry = ctk.CTkEntry(parent_frame, textvariable=self.parent.excel_vars[col_name],
                           font=ctk.CTkFont(size=12))
            entry.grid(row=row+1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

            # Enable undo tracking for Entry widget
            self.parent.enable_undo_for_widget(entry)

            # Apply disabled styling if field is disabled
            if is_field_disabled:
                field_widgets = {'label': field_label, 'input': entry}
                if lock_switch:
                    field_widgets['checkbox'] = lock_switch
                apply_field_state(field_widgets, field_id, is_field_disabled)

            # Return 2 rows used for vertical layout
            return 2

        # Configure column weight for proper resizing (for all field types)
        parent_frame.grid_columnconfigure(0, weight=1)
        if parent_frame.grid_size()[0] > 1:  # If there are multiple columns
            parent_frame.grid_columnconfigure(1, weight=1)

    def _create_datetime_fields_in_subframe(self, datetime_frame):
        """Create date/time fields in a simple 2x2 grid layout"""
        # Configure grid layout: 2 columns, 2 rows
        datetime_frame.grid_columnconfigure(0, weight=1)  # Left column
        datetime_frame.grid_columnconfigure(1, weight=1)  # Right column

        # Create date fields in first row
        self._create_single_datetime_field(datetime_frame, 'Startdatum', 0, 0)
        self._create_single_datetime_field(datetime_frame, 'Slutdatum', 0, 1)

        # Create time fields in second row
        self._create_single_datetime_field(datetime_frame, 'Starttid', 1, 0)
        self._create_single_datetime_field(datetime_frame, 'Sluttid', 1, 1)

    def _create_single_datetime_field(self, parent, field_name, row, col):
        """Create a single date/time field with label, entry, and lock switch"""
        # Create container frame for this field
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.grid(row=row, column=col, sticky="ew", padx=5, pady=2)

        # Configure internal layout
        field_frame.grid_columnconfigure(1, weight=1)  # Entry expands

        # Create label
        ctk.CTkLabel(field_frame, text=f"{field_name}:",
                font=ctk.CTkFont(size=14)).grid(row=0, column=0, sticky="w", padx=(5, 5))

        # Create entry field
        entry = ctk.CTkEntry(field_frame, textvariable=self.parent.excel_vars[field_name],
                        font=ctk.CTkFont(size=12),
                        border_color="#E0E0E0", border_width=1)
        entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))

        # Create lock switch
        lock_switch = ctk.CTkCheckBox(field_frame,
                                    text="Lås",
                                    variable=self.parent.lock_vars[field_name])
        lock_switch.grid(row=0, column=2, sticky="w", padx=(5, 5))

        # Add validation bindings
        if 'datum' in field_name.lower():
            entry.bind('<FocusOut>', lambda e: self.parent.validate_date_field(e, field_name))
            entry.bind('<Return>', lambda e: self.parent.validate_date_field(e, field_name))
            entry.bind('<Tab>', lambda e: self.parent.validate_date_field(e, field_name))
            entry.bind('<Button-1>', lambda e: self.parent.root.after(10, lambda: self.parent.validate_date_field(e, field_name)))
            self._setup_date_field_focus(entry, field_name)
        else:  # time fields
            entry.bind('<FocusOut>', lambda e: self.parent.validate_time_field(e, field_name))
            entry.bind('<Return>', lambda e: self.parent.validate_time_field(e, field_name))
            entry.bind('<Tab>', lambda e: self.parent.validate_time_field(e, field_name))
            entry.bind('<Button-1>', lambda e: self.parent.root.after(10, lambda: self.parent.validate_time_field(e, field_name)))
            self._setup_time_field_focus(entry, field_name)

        # Enable undo tracking
        self.parent.enable_undo_for_widget(entry)
        print(f"DEBUG: Validation bindings added for {field_name}")

    def create_operations_box(self, parent_frame):
        """Create reorganized operations box under Händelse field with separate containers"""

        # First box: Color selection in light grey container (positioned above buttons)
        color_box = ctk.CTkFrame(parent_frame, fg_color=("gray92", "gray18"), corner_radius=4)
        color_box.grid(row=10, column=0, columnspan=2, sticky="ew", padx=3, pady=(5, 2))

        # Color selection frame with centered content
        color_frame = ctk.CTkFrame(color_box, fg_color="transparent")
        color_frame.pack(expand=True, pady=4)

        # Label for color selection - centered
        color_label = ctk.CTkLabel(color_frame, text="Bakgrundsfärg på nya excel-raden:", font=ctk.CTkFont(size=10, weight="bold"))
        color_label.pack(pady=(0, 3))

        # Container for color buttons - centered
        color_buttons_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        color_buttons_frame.pack()

        # Colored button options - enlarged for better usability
        color_options = [
            ("none", "Ingen", "#FFFFFF"),
            ("yellow", "Gul", "#FFF59D"),
            ("green", "Grön", "#C8E6C9"),
            ("blue", "Blå", "#BBDEFB"),
            ("red", "Röd", "#FFCDD2"),
            ("pink", "Rosa", "#F8BBD9"),
            ("gray", "Grå", "#E0E0E0")
        ]

        # Store button references for selection state management
        self.parent.color_buttons = {}

        for value, text, color in color_options:
            current_selection = self.parent.row_color_var.get() if hasattr(self.parent, 'row_color_var') else "none"
            is_selected = current_selection == value

            button = ctk.CTkButton(
                color_buttons_frame,
                text=text,
                width=45,
                height=22,  # Enlarged for better touch/click usability
                font=ctk.CTkFont(size=9),
                fg_color=color if value != "none" else "#FFFFFF",
                hover_color=self.parent._get_hover_color(color),
                text_color="#333333" if value != "none" else "#666666",
                border_color="#666666",
                border_width=2 if is_selected else 1,
                command=lambda v=value: self.parent._select_row_color(v)
            )
            button.pack(side="left", padx=2)
            self.parent.color_buttons[value] = button

        # Second box: Operation buttons in separate light grey container (positioned below with more spacing)
        buttons_box = ctk.CTkFrame(parent_frame, fg_color=("gray92", "gray18"), corner_radius=4)
        buttons_box.grid(row=11, column=0, columnspan=2, sticky="ew", padx=3, pady=(8, 3))

        # Buttons frame with centered content
        buttons_frame = ctk.CTkFrame(buttons_box, fg_color="transparent")
        buttons_frame.pack(expand=True, pady=4)

        # Container for buttons - centered
        buttons_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        buttons_container.pack()

        self.parent.save_all_btn = ctk.CTkButton(buttons_container, text="Spara allt och rensa", width=200, height=40,
                                     command=self.parent.save_all_and_clear,
                                     fg_color="#28a745", hover_color="#218838",
                                     font=ctk.CTkFont(size=13, weight="bold"))
        self.parent.save_all_btn.pack(side="left", padx=(0, 5))

        self.parent.new_excel_row_btn = ctk.CTkButton(buttons_container, text="Rensa utan spara", width=180, height=40,
                                          command=self.parent.clear_all_without_saving,
                                          fg_color="#17a2b8", hover_color="#117a8b",
                                          font=ctk.CTkFont(size=13, weight="bold"))
        self.parent.new_excel_row_btn.pack(side="left", padx=(5, 0))

    def refresh_field_styling(self):
        """
        Refresh the styling of existing fields based on current disabled state.
        This is more efficient than recreating all fields.
        """
        try:
            from core.field_definitions import FIELD_ORDER
            disabled_field_ids = field_state_manager.get_disabled_fields()

            logger.info(f"Refreshing field styling for {len(disabled_field_ids)} disabled fields")

            # Iterate through all created fields and update their styling
            for field_id in FIELD_ORDER:
                is_field_disabled = field_id in disabled_field_ids
                display_name = field_manager.get_display_name(field_id)

                # Find the field widgets in parent's attributes
                # Field entries are stored with display names as keys
                if hasattr(self.parent, 'entries') and display_name in self.parent.entries:
                    entry_widget = self.parent.entries[display_name]

                    # Find associated label and checkbox
                    field_widgets = {'input': entry_widget}

                    # Look for label with matching text
                    for child in self.parent.excel_fields_frame.winfo_children():
                        if hasattr(child, 'winfo_children'):
                            for grandchild in child.winfo_children():
                                if (hasattr(grandchild, 'cget') and
                                    hasattr(grandchild, 'configure') and
                                    hasattr(grandchild, '_text')):  # CTkLabel
                                    try:
                                        label_text = grandchild.cget('text')
                                        if label_text.rstrip(':') == display_name:
                                            field_widgets['label'] = grandchild
                                            break
                                    except (AttributeError, TypeError):
                                        pass

                    # Look for associated checkbox (lock switch)
                    if hasattr(self.parent, 'lock_vars') and display_name in self.parent.lock_vars:
                        # Find checkbox widget associated with this lock_var
                        for child in self.parent.excel_fields_frame.winfo_children():
                            if hasattr(child, 'winfo_children'):
                                for grandchild in child.winfo_children():
                                    if (hasattr(grandchild, 'cget') and
                                        hasattr(grandchild, 'configure') and
                                        hasattr(grandchild, '_variable')):  # CTkCheckBox
                                        try:
                                            if grandchild.cget('variable') == self.parent.lock_vars[display_name]:
                                                field_widgets['checkbox'] = grandchild
                                                break
                                        except (AttributeError, TypeError):
                                            pass

                    # Apply the appropriate styling
                    apply_field_state(field_widgets, field_id, is_field_disabled)

            logger.info("Field styling refresh completed")

        except Exception as e:
            logger.error(f"Failed to refresh field styling: {e}")
            # Fall back to recreating fields if refresh fails
            logger.info("Falling back to recreating Excel fields")
            self.create_excel_fields()
