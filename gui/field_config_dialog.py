"""
Field configuration dialog redesigned with template support and field visibility controls.
Based on user mockup requirements with two-column layout and comprehensive template management.
"""

import logging
import os
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Dict, Optional

import customtkinter as ctk

from core.config import ConfigManager
from core.field_definitions import (
    FIELD_DEFINITIONS,
    LEFT_COLUMN_ORDER,
    REQUIRED_ENABLED_FIELDS,
    RIGHT_COLUMN_ORDER,
    field_manager,
)
from core.field_state_manager import field_state_manager
from core.field_validator import realtime_validator
from core.template_manager import template_manager

logger = logging.getLogger(__name__)


class FieldConfigDialog:
    """Redesigned field configuration dialog with template support and field visibility."""

    def __init__(self, parent_app, on_apply_callback: Optional[Callable] = None):
        self.parent_app = parent_app
        self.on_apply_callback = on_apply_callback
        self.config_manager = ConfigManager()

        # Dialog window
        self.dialog = None

        # Template management
        self.current_template = "Standard"
        self.template_name_label = None
        self.is_template_modified = False

        # Field widgets storage
        self.field_entries: Dict[str, ctk.CTkEntry] = {}
        self.char_count_labels: Dict[str, ctk.CTkLabel] = {}
        self.validation_icons: Dict[str, ctk.CTkLabel] = {}
        self.disable_checkboxes: Dict[str, ctk.CTkCheckBox] = {}  # Internal: disabled fields

        # Current field values and states
        self.current_values: Dict[str, str] = {}
        self.current_disabled_fields: set = set()  # Internal: disabled fields
        self.validation_errors: Dict[str, str] = {}

        # Create dialog
        self._create_dialog()

    def _create_dialog(self):
        """Create the main dialog window."""
        self.dialog = ctk.CTkToplevel(self.parent_app)
        self.dialog.title("Konfigurera Excel-fält")
        self.dialog.geometry("1000x800")
        self.dialog.transient(self.parent_app)
        self.dialog.grab_set()  # Modal dialog

        # Center on parent
        self._center_dialog()

        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(2, weight=1)

        # Create main sections
        self._create_header()
        self._create_template_controls()
        self._create_main_content()
        self._create_footer()

        # Load current values
        self._load_current_configuration()

        # Start validation
        self._update_validation()

    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = self.parent_app.winfo_rootx()
        parent_y = self.parent_app.winfo_rooty()
        parent_width = self.parent_app.winfo_width()
        parent_height = self.parent_app.winfo_height()

        # Calculate center position
        dialog_width = 1000
        dialog_height = 800
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)

        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def _create_header(self):
        """Create dialog header with title and instructions."""
        header_frame = ctk.CTkFrame(self.dialog)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        # Main title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Gör dina egna Excel-fältnamn",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(15, 5))

        # Instructions
        instructions = (
            "Anpassa namnen på Excel-fälten efter dina behov och välj vilka fält som ska visas.\n"
            "Grå fält kan inte ändras. Använd templates för att spara olika konfigurationer."
        )
        instruction_label = ctk.CTkLabel(
            header_frame,
            text=instructions,
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        instruction_label.grid(row=1, column=0, pady=(0, 15))

    def _create_template_controls(self):
        """Create template file dialog controls for loading and saving templates."""
        template_frame = ctk.CTkFrame(self.dialog)
        template_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        template_frame.grid_columnconfigure(2, weight=1)  # Spacer column

        # Load template button
        load_button = ctk.CTkButton(
            template_frame,
            text="Ladda mall...",
            width=140,
            height=32,
            command=self._load_template_from_file
        )
        load_button.grid(row=0, column=0, padx=(15, 10), pady=15)

        # Save template button
        save_button = ctk.CTkButton(
            template_frame,
            text="Spara mall...",
            width=140,
            height=32,
            command=self._save_template_to_file
        )
        save_button.grid(row=0, column=1, padx=10, pady=15)

        # Template name display
        self.template_name_label = ctk.CTkLabel(
            template_frame,
            text="Aktuell mall: Standard",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
            fg_color="#FF8C00",  # Orange background
            corner_radius=6,
            padx=12,
            pady=6
        )
        self.template_name_label.grid(row=0, column=2, padx=15, pady=15)

        # Help button on right side
        help_button = ctk.CTkButton(
            template_frame,
            text="Hjälp",
            width=80,
            height=32,
            fg_color="gray60",
            hover_color="gray50",
            command=self._show_help
        )
        help_button.grid(row=0, column=3, padx=(10, 15), pady=15)

    def _create_main_content(self):
        """Create main content area with two-column field layout."""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self.dialog)
        main_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_columnconfigure((0, 1), weight=1, uniform="column")

        # Create two columns
        self._create_left_column(main_frame)
        self._create_right_column(main_frame)

    def _create_left_column(self, parent):
        """Create left column with first set of fields."""
        row = 0
        for field_id in LEFT_COLUMN_ORDER:
            self._create_field_row(parent, field_id, row, 0)
            row += 1

    def _create_right_column(self, parent):
        """Create right column with second set of fields."""
        row = 0
        for field_id in RIGHT_COLUMN_ORDER:
            self._create_field_row(parent, field_id, row, 1)
            row += 1

    def _create_field_row(self, parent, field_id: str, row: int, column: int):
        """Create a single field row with fixed-width container architecture for uniform alignment."""
        field_def = FIELD_DEFINITIONS[field_id]

        # Main field container frame - don't use grid_propagate(False) on the main container
        field_frame = ctk.CTkFrame(parent)
        field_frame.grid(row=row, column=column, sticky="ew", padx=10, pady=2)

        # Create fixed-width container frames for each column
        containers = self._create_fixed_width_containers(field_frame)

        # Determine field type and create appropriate components
        if field_def.protected:
            self._create_protected_field_components(containers, field_id, field_def)
        elif field_id in REQUIRED_ENABLED_FIELDS:
            self._create_required_field_components(containers, field_id, field_def)
        else:
            self._create_editable_field_components(containers, field_id, field_def)

    def _create_fixed_width_containers(self, parent_frame):
        """Create fixed-width container frames for uniform column alignment."""
        containers = {}

        # Configure parent frame columns with fixed widths and no expansion
        parent_frame.grid_columnconfigure(0, weight=0, minsize=140)  # Label
        parent_frame.grid_columnconfigure(1, weight=0, minsize=250)  # Entry
        parent_frame.grid_columnconfigure(2, weight=0, minsize=55)   # Counter
        parent_frame.grid_columnconfigure(3, weight=0, minsize=35)   # Icon
        parent_frame.grid_columnconfigure(4, weight=0, minsize=85)   # Checkbox

        # Column 0: Label container (140px)
        label_container = ctk.CTkFrame(parent_frame, fg_color="transparent", width=140, height=40)
        label_container.grid(row=0, column=0, sticky="w", padx=0, pady=0)
        label_container.grid_propagate(False)
        containers['label'] = label_container

        # Column 1: Entry container (250px)
        entry_container = ctk.CTkFrame(parent_frame, fg_color="transparent", width=250, height=40)
        entry_container.grid(row=0, column=1, sticky="w", padx=0, pady=0)
        entry_container.grid_propagate(False)
        containers['entry'] = entry_container

        # Column 2: Counter container (55px)
        counter_container = ctk.CTkFrame(parent_frame, fg_color="transparent", width=55, height=40)
        counter_container.grid(row=0, column=2, sticky="w", padx=0, pady=0)
        counter_container.grid_propagate(False)
        containers['counter'] = counter_container

        # Column 3: Icon container (35px)
        icon_container = ctk.CTkFrame(parent_frame, fg_color="transparent", width=35, height=40)
        icon_container.grid(row=0, column=3, sticky="w", padx=0, pady=0)
        icon_container.grid_propagate(False)
        containers['icon'] = icon_container

        # Column 4: Checkbox container (85px)
        checkbox_container = ctk.CTkFrame(parent_frame, fg_color="transparent", width=85, height=40)
        checkbox_container.grid(row=0, column=4, sticky="w", padx=0, pady=0)
        checkbox_container.grid_propagate(False)
        containers['checkbox'] = checkbox_container

        return containers

    def _create_protected_field_components(self, containers, field_id: str, field_def):
        """Create components for protected fields (label + disabled entry only)."""
        display_name = field_def.default_display_name

        # Field label in label container
        label_text = f"{display_name}:"
        field_label = ctk.CTkLabel(
            containers['label'],
            text=label_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        field_label.pack(side="left", padx=(10, 5), pady=8, fill="y")

        # Protected entry in entry container
        protected_entry = ctk.CTkEntry(
            containers['entry'],
            placeholder_text=display_name,
            font=ctk.CTkFont(size=12),
            state="disabled",
            fg_color="gray90"
        )
        protected_entry.pack(fill="both", expand=True, padx=5, pady=6)

        # Add invisible spacer frames for unused columns to maintain layout consistency
        self._add_spacer_frame(containers['counter'])
        self._add_spacer_frame(containers['icon'])
        self._add_spacer_frame(containers['checkbox'])

    def _create_required_field_components(self, containers, field_id: str, field_def):
        """Create components for required editable fields (no checkbox)."""
        display_name = field_def.default_display_name

        # Field label in label container
        label_text = f"{display_name}:"
        field_label = ctk.CTkLabel(
            containers['label'],
            text=label_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        field_label.pack(side="left", padx=(10, 5), pady=8, fill="y")

        # Editable entry in entry container
        entry = ctk.CTkEntry(
            containers['entry'],
            placeholder_text="Ange nytt namn...",
            font=ctk.CTkFont(size=12)
        )
        entry.pack(fill="both", expand=True, padx=5, pady=6)

        # Bind validation events
        entry.bind('<KeyRelease>', lambda e, fid=field_id: self._on_field_change(fid))
        entry.bind('<FocusOut>', lambda e, fid=field_id: self._on_field_change(fid))
        self.field_entries[field_id] = entry

        # Character counter in counter container
        char_label = ctk.CTkLabel(
            containers['counter'],
            text="0/13",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        char_label.pack(padx=5, pady=8, anchor="center")
        self.char_count_labels[field_id] = char_label

        # Validation icon in icon container
        icon_label = ctk.CTkLabel(
            containers['icon'],
            text="⚪",
            font=ctk.CTkFont(size=14)
        )
        icon_label.pack(padx=5, pady=8, anchor="center")
        self.validation_icons[field_id] = icon_label

        # Add invisible spacer frame for checkbox column
        self._add_spacer_frame(containers['checkbox'])

    def _create_editable_field_components(self, containers, field_id: str, field_def):
        """Create components for fully editable fields (all components)."""
        display_name = field_def.default_display_name

        # Field label in label container
        label_text = f"{display_name}:"
        field_label = ctk.CTkLabel(
            containers['label'],
            text=label_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        field_label.pack(side="left", padx=(10, 5), pady=8, fill="y")

        # Editable entry in entry container
        entry = ctk.CTkEntry(
            containers['entry'],
            placeholder_text="Ange nytt namn...",
            font=ctk.CTkFont(size=12)
        )
        entry.pack(fill="both", expand=True, padx=5, pady=6)

        # Bind validation events
        entry.bind('<KeyRelease>', lambda e, fid=field_id: self._on_field_change(fid))
        entry.bind('<FocusOut>', lambda e, fid=field_id: self._on_field_change(fid))
        self.field_entries[field_id] = entry

        # Character counter in counter container
        char_label = ctk.CTkLabel(
            containers['counter'],
            text="0/13",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        char_label.pack(padx=5, pady=8, anchor="center")
        self.char_count_labels[field_id] = char_label

        # Validation icon in icon container
        icon_label = ctk.CTkLabel(
            containers['icon'],
            text="⚪",
            font=ctk.CTkFont(size=14)
        )
        icon_label.pack(padx=5, pady=8, anchor="center")
        self.validation_icons[field_id] = icon_label

        # Hide checkbox in checkbox container
        hide_checkbox = ctk.CTkCheckBox(
            containers['checkbox'],
            text="Dölj",
            command=lambda fid=field_id: self._on_hide_checkbox_changed(fid)
        )
        hide_checkbox.pack(padx=(5, 10), pady=8, anchor="center")
        self.disable_checkboxes[field_id] = hide_checkbox

    def _add_spacer_frame(self, container):
        """Add invisible spacer frame to maintain layout consistency."""
        spacer = ctk.CTkFrame(container, fg_color="transparent", width=1, height=1)
        spacer.pack(fill="both", expand=True)

    def _create_footer(self):
        """Create dialog footer with action buttons."""
        footer_frame = ctk.CTkFrame(self.dialog)
        footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        footer_frame.grid_columnconfigure(1, weight=1)

        # Left side buttons
        left_button_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        left_button_frame.grid(row=0, column=0, padx=15, pady=15)

        cancel_button = ctk.CTkButton(
            left_button_frame,
            text="Avbryt",
            width=100,
            height=40,
            fg_color="gray60",
            hover_color="gray50",
            command=self._cancel
        )
        cancel_button.pack(side="left", padx=(0, 10))

        # Right side buttons
        right_button_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        right_button_frame.grid(row=0, column=2, padx=15, pady=15)

        reset_button = ctk.CTkButton(
            right_button_frame,
            text="Återställ till standard",
            width=180,
            height=40,
            fg_color="#FF6B35",
            hover_color="#E55A2B",
            command=self._reset_to_defaults
        )
        reset_button.pack(side="left", padx=(0, 10))

        # Apply button
        self.apply_button = ctk.CTkButton(
            right_button_frame,
            text="Använd dessa namn",
            width=160,
            height=40,
            fg_color="#28A745",
            hover_color="#218838",
            command=self._apply_changes
        )
        self.apply_button.pack(side="left")

    def _load_current_configuration(self):
        """Load current field configuration and template."""
        # Initialize with default template
        self.current_template = "Standard"

        # Load current field names
        custom_names = self.config_manager.load_custom_field_names()
        logger.info(f"Loading custom names: {custom_names}")
        field_manager.set_custom_names(custom_names)

        # Load field state
        disabled_fields = self.config_manager.load_field_state()
        logger.info(f"Loading disabled fields: {disabled_fields}")
        field_state_manager.set_disabled_fields(disabled_fields)
        self.current_disabled_fields = set(disabled_fields)

        # Populate field entries
        for field_id, entry in self.field_entries.items():
            current_name = field_manager.get_display_name(field_id)
            field_def = FIELD_DEFINITIONS[field_id]

            # Clear any existing content first
            entry.delete(0, 'end')

            # Only show custom names (not default names)
            if current_name != field_def.default_display_name:
                entry.insert(0, current_name)
                self.current_values[field_id] = current_name
                logger.debug(f"Set custom name for {field_id}: '{current_name}'")
            else:
                self.current_values[field_id] = ""

        # Update disable checkboxes
        for field_id, checkbox in self.disable_checkboxes.items():
            is_disabled = field_id in self.current_disabled_fields
            if is_disabled:
                checkbox.select()
                logger.debug(f"Set checkbox for {field_id} to disabled")
            else:
                checkbox.deselect()

        logger.info(f"Config loading complete: {len(custom_names)} custom names, {len(disabled_fields)} disabled fields")

        # Update template name display
        self.is_template_modified = False  # Initial load is not a modification
        self._update_template_name_display()

    def _load_template_from_file(self):
        """Load template configuration from a file dialog."""
        # Open file dialog for template selection
        file_path = filedialog.askopenfilename(
            title="Ladda fältmall",
            filetypes=[("Template files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
            initialdir=os.getcwd()
        )

        if not file_path:
            return

        try:
            # Use existing import_template method from template_manager
            template_path = Path(file_path)
            success = template_manager.import_template(template_path)

            if not success:
                messagebox.showerror(
                    "Kunde inte ladda mall",
                    "Mallens format är ogiltigt eller så inträffade ett fel vid laddning."
                )
                return

            # Load the imported template (it gets the filename as template name)
            template_name = template_path.stem
            template_config = template_manager.load_template(template_name)

            if not template_config:
                messagebox.showerror(
                    "Kunde inte ladda mall",
                    f"Mall '{template_name}' kunde inte laddas efter import."
                )
                return

            # Apply template configuration to dialog
            self._apply_template_config(template_config, template_name)

            messagebox.showinfo(
                "Mall laddad",
                f"Mall '{template_name}' har laddats från {template_path.name}"
            )

            logger.info(f"Loaded template from file: {file_path}")

        except Exception as e:
            logger.error(f"Error loading template from file: {e}")
            messagebox.showerror(
                "Fel vid laddning",
                f"Kunde inte ladda mallen: {str(e)}"
            )

    def _save_template_to_file(self):
        """Save current configuration to a file via file dialog."""
        # Suggest filename based on first non-empty custom name or use "Fältmall"
        suggested_name = "Fältmall"
        for _field_id, value in self.current_values.items():
            if value.strip():
                # Use first few words of first custom field as suggestion
                suggested_name = value.strip()[:20].replace(" ", "_")
                break

        # Open save file dialog
        file_path = filedialog.asksaveasfilename(
            title="Spara fältmall",
            filetypes=[("Template files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
            initialdir=os.getcwd(),
            initialfile=f"{suggested_name}.json"
        )

        if not file_path:
            return

        try:
            # Prepare template configuration
            custom_names = {}
            for field_id, value in self.current_values.items():
                if value.strip():
                    custom_names[field_id] = value.strip()

            field_config = {
                'custom_names': custom_names,
                'disabled_fields': list(self.current_disabled_fields)
            }

            # Get template name from filename
            template_path = Path(file_path)
            template_name = template_path.stem

            # Save template internally first
            success = template_manager.save_template(
                template_name,
                field_config,
                f"Mall sparad till fil: {template_path.name}"
            )

            if not success:
                messagebox.showerror(
                    "Kunde inte spara mall",
                    "Ett fel inträffade vid sparande av mallen."
                )
                return

            # Export to chosen file location
            export_success = template_manager.export_template(template_name, template_path)

            if not export_success:
                messagebox.showerror(
                    "Kunde inte exportera mall",
                    f"Kunde inte spara mallen till {file_path}"
                )
                return

            messagebox.showinfo(
                "Mall sparad",
                f"Mall har sparats till {template_path.name}"
            )

            logger.info(f"Saved template to file: {file_path}")

        except Exception as e:
            logger.error(f"Error saving template to file: {e}")
            messagebox.showerror(
                "Fel vid sparande",
                f"Kunde inte spara mallen: {str(e)}"
            )

    def _apply_template_config(self, template_config: dict, template_name: str):
        """Apply loaded template configuration to the dialog."""
        custom_names = template_config.get('custom_names', {})
        disabled_fields = template_config.get('disabled_fields', template_config.get('hidden_fields', []))

        # Clear current entries
        for entry in self.field_entries.values():
            entry.delete(0, 'end')
        self.current_values.clear()

        # Apply custom names
        for field_id, custom_name in custom_names.items():
            if field_id in self.field_entries:
                self.field_entries[field_id].insert(0, custom_name)
                self.current_values[field_id] = custom_name

        # Apply field state
        self.current_disabled_fields = set(disabled_fields)
        for field_id, checkbox in self.disable_checkboxes.items():
            is_disabled = field_id in self.current_disabled_fields
            checkbox.select() if is_disabled else checkbox.deselect()

        # Update validation
        self._update_validation()

        # Update current template name for reference
        self.current_template = template_name
        self.is_template_modified = False
        self._update_template_name_display()

    def _update_template_name_display(self):
        """Update the template name display label."""
        if not self.template_name_label:
            return

        base_text = f"Aktuell mall: {self.current_template}"

        if self.is_template_modified:
            display_text = f"{base_text} (ändrad)"
            text_color = "white"
            bg_color = "#DC3545"  # Red background to indicate modification
        else:
            display_text = base_text
            text_color = "white"
            bg_color = "#FF8C00"  # Orange background for normal state

        self.template_name_label.configure(text=display_text, text_color=text_color, fg_color=bg_color)

    def _on_field_change(self, field_id: str):
        """Handle field value changes."""
        entry = self.field_entries[field_id]
        new_value = entry.get().strip()
        self.current_values[field_id] = new_value

        # Update character counter
        if field_id in self.char_count_labels:
            char_label = self.char_count_labels[field_id]
            char_label.configure(text=f"{len(new_value)}/13")

        # Update validation
        self._update_field_validation(field_id)
        self._update_apply_button()

        # Mark template as modified
        self.is_template_modified = True
        self._update_template_name_display()

    def _on_hide_checkbox_changed(self, field_id: str):
        """Handle hide checkbox changes."""
        checkbox = self.disable_checkboxes[field_id]
        is_checked = checkbox.get()

        if is_checked:
            self.current_disabled_fields.add(field_id)
        else:
            self.current_disabled_fields.discard(field_id)

        logger.debug(f"Field {field_id} visibility changed: {'hidden' if is_checked else 'visible'}")

        # Mark template as modified
        self.is_template_modified = True
        self._update_template_name_display()

    def _update_field_validation(self, field_id: str):
        """Update validation display for a specific field."""
        if field_id not in self.field_entries:
            return

        entry = self.field_entries[field_id]
        icon_label = self.validation_icons[field_id]
        char_label = self.char_count_labels[field_id]

        value = self.current_values.get(field_id, "")

        if not value:
            # Empty field - neutral state
            icon_label.configure(text="⚪", text_color="gray50")
            char_label.configure(text_color="gray50")
            entry.configure(border_color="gray70")
            self.validation_errors.pop(field_id, None)
            return

        # Get validation feedback with live context for real-time duplicate detection
        feedback = realtime_validator.get_instant_feedback_with_context(
            name=value,
            original_name=field_id,
            current_context=self.current_values
        )

        # Update icon and colors
        if feedback['is_valid']:
            icon_label.configure(text="✅", text_color="green")
            char_label.configure(text_color="green")
            entry.configure(border_color="green")
            self.validation_errors.pop(field_id, None)
        else:
            icon_label.configure(text="❌", text_color="red")
            char_label.configure(text_color="red")
            entry.configure(border_color="red")
            self.validation_errors[field_id] = feedback['messages'][0] if feedback['messages'] else "Ogiltigt namn"

        # Update character count color based on length
        if len(value) > 13:
            char_label.configure(text_color="red")
        elif len(value) > 10:
            char_label.configure(text_color="orange")

    def _update_validation(self):
        """Update validation for all fields."""
        for field_id in self.field_entries.keys():
            self._update_field_validation(field_id)
        self._update_apply_button()

    def _update_apply_button(self):
        """Enable/disable apply button based on validation."""
        has_errors = bool(self.validation_errors)

        if has_errors:
            self.apply_button.configure(
                state="disabled",
                fg_color="gray50",
                text=f"Åtgärda {len(self.validation_errors)} fel först"
            )
        else:
            self.apply_button.configure(
                state="normal",
                fg_color="#28A745",
                text="Använd dessa namn"
            )

    def _reset_to_defaults(self):
        """Reset all fields to default values."""
        if not messagebox.askyesno("Återställ till standard", "Vill du återställa alla fält till standardvärden?"):
            return

        # Clear all entries
        for entry in self.field_entries.values():
            entry.delete(0, 'end')

        self.current_values.clear()

        # Reset visibility checkboxes
        for checkbox in self.disable_checkboxes.values():
            checkbox.deselect()

        self.current_disabled_fields.clear()

        # Update validation
        self._update_validation()

        logger.info("Configuration reset to defaults")

    def _apply_changes(self):
        """Apply field name changes and visibility settings."""
        if self.validation_errors:
            return  # Should not happen if button is properly disabled

        # Show final confirmation
        if not self._confirm_apply():
            return

        # Prepare custom names (only include non-empty values)
        custom_names = {}
        for field_id, value in self.current_values.items():
            if value.strip():
                custom_names[field_id] = value.strip()

        # Apply changes
        try:
            # Save custom names
            self.config_manager.save_custom_field_names(custom_names)

            # Save field visibility
            self.config_manager.save_field_state(list(self.current_disabled_fields))

            # Update field manager
            field_manager.set_custom_names(custom_names)
            field_manager.set_disabled_fields(list(self.current_disabled_fields))
            field_state_manager.set_disabled_fields(list(self.current_disabled_fields))

            logger.info(f"Applied configuration: {len(custom_names)} custom names, {len(self.current_disabled_fields)} disabled fields")

            # Call the callback to trigger application update
            if self.on_apply_callback:
                self.on_apply_callback()

            # Close dialog
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Failed to apply configuration: {e}")
            self._show_error("Kunde inte tillämpa ändringar", f"Ett fel uppstod: {str(e)}")

    def _confirm_apply(self) -> bool:
        """Show confirmation dialog for applying changes."""
        confirm_dialog = ctk.CTkToplevel(self.dialog)
        confirm_dialog.title("Bekräfta ändringar")
        confirm_dialog.geometry("450x250")
        confirm_dialog.transient(self.dialog)
        confirm_dialog.grab_set()

        # Center on parent dialog
        self.dialog.update_idletasks()
        x = self.dialog.winfo_rootx() + 275
        y = self.dialog.winfo_rooty() + 275
        confirm_dialog.geometry(f"450x250+{x}+{y}")

        result = {"confirmed": False}

        # Warning text
        warning_label = ctk.CTkLabel(
            confirm_dialog,
            text="⚠️ BEKRÄFTA ÄNDRINGAR",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF6B35"
        )
        warning_label.pack(pady=(20, 10))

        message_label = ctk.CTkLabel(
            confirm_dialog,
            text="Detta kommer att tillämpa de nya fältnamnen och synlighetsinställningarna.\n\nKlicka 'Tillämpa' för att fortsätta eller 'Avbryt' för att återgå.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        message_label.pack(pady=10, padx=20)

        # Buttons
        button_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        button_frame.pack(pady=20)

        def confirm():
            result["confirmed"] = True
            confirm_dialog.destroy()

        def cancel():
            result["confirmed"] = False
            confirm_dialog.destroy()

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Avbryt",
            width=100,
            fg_color="gray60",
            hover_color="gray50",
            command=cancel
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        confirm_btn = ctk.CTkButton(
            button_frame,
            text="Tillämpa",
            width=100,
            fg_color="#28A745",
            hover_color="#218838",
            command=confirm
        )
        confirm_btn.pack(side="left")

        # Wait for dialog to close
        confirm_dialog.wait_window()

        return result["confirmed"]

    def _show_help(self):
        """Show help information."""
        help_text = """HJÄLP: Konfigurera Excel-fältnamn och synlighet

FUNKTIONER:
• Anpassa namnen på Excel-fälten (max 13 tecken, inga mellanslag)
• Dölj fält som inte behövs (vissa fält kan inte döljas)
• Spara konfigurationer som mallfiler för framtida användning och delning

TEMPLATES:
• "Ladda mall..." - öppna mallkonfiguration från din dator
• "Spara mall..." - spara nuvarande konfiguration till fil
• Mallar sparas som JSON-filer som du kan organisera och dela
• Standardplats: Dokumentmappen (men du kan välja var som helst)

FÄLTREGLER:
• Grå fält kan inte ändras (systemfält)
• Vita fält kan anpassas fritt
• Maxlängd: 13 tecken per fältnamn
• Inga mellanslag eller specialtecken tillåtna
• Alla namn måste vara unika

SYNLIGHET:
• Markera "Dölj" för att dölja fält från huvudgränssnittet
• Vissa fält (Startdatum, Källa1, Händelse) kan aldrig döljas
• Dolda fält sparas i templates

Klicka "Använd dessa namn" när du är klar."""

        help_dialog = ctk.CTkToplevel(self.dialog)
        help_dialog.title("Hjälp - Fältkonfiguration")
        help_dialog.geometry("600x500")
        help_dialog.transient(self.dialog)
        help_dialog.grab_set()

        text_widget = ctk.CTkTextbox(help_dialog, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)
        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")

        close_button = ctk.CTkButton(
            help_dialog,
            text="Stäng",
            command=help_dialog.destroy
        )
        close_button.pack(pady=(0, 20))

    def _show_error(self, title: str, message: str):
        """Show error dialog."""
        error_dialog = ctk.CTkToplevel(self.dialog)
        error_dialog.title(title)
        error_dialog.geometry("400x200")
        error_dialog.transient(self.dialog)
        error_dialog.grab_set()

        error_label = ctk.CTkLabel(
            error_dialog,
            text=message,
            wraplength=350,
            font=ctk.CTkFont(size=12)
        )
        error_label.pack(expand=True, padx=20, pady=20)

        ok_button = ctk.CTkButton(
            error_dialog,
            text="OK",
            command=error_dialog.destroy
        )
        ok_button.pack(pady=(0, 20))

    def _cancel(self):
        """Cancel dialog without saving."""
        self.dialog.destroy()

    def show(self):
        """Show the dialog."""
        if self.dialog:
            self.dialog.focus()
            self.dialog.lift()


def show_field_config_dialog(parent_app, on_apply_callback=None):
    """Convenience function to show the field configuration dialog."""
    dialog = FieldConfigDialog(parent_app, on_apply_callback)
    dialog.show()
    return dialog
