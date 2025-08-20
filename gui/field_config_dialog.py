"""
Field configuration dialog redesigned with template support and field visibility controls.
Based on user mockup requirements with two-column layout and comprehensive template management.
"""

import logging
import os
from datetime import datetime
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


class SavePromptChoice:
    """Constants for save prompt dialog return values"""
    SAVE_FIRST = "save_first"
    CONTINUE_WITHOUT_SAVING = "continue_without_saving"
    CANCEL = "cancel"


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
        self.save_template_button = None  # Reference to direct save button for state management
        self.is_template_modified = False
        self._loading_template = False  # Flag to prevent race conditions during template loading
        self._last_button_update = 0  # Throttling mechanism for button state updates

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
        template_frame.grid_columnconfigure(3, weight=1)  # Spacer column (updated for 3 buttons)

        # Load template button
        load_button = ctk.CTkButton(
            template_frame,
            text="Ladda mall...",
            width=140,
            height=32,
            command=self._load_template_from_file
        )
        load_button.grid(row=0, column=0, padx=(15, 10), pady=15)

        # Direct save template button (new)
        self.save_template_button = ctk.CTkButton(
            template_frame,
            text="Spara mall",
            width=120,
            height=32,
            command=self._save_current_template,
            state="disabled"  # Initially disabled
        )
        self.save_template_button.grid(row=0, column=1, padx=5, pady=15)

        # Save template as button (renamed from "Spara mall...")
        save_as_button = ctk.CTkButton(
            template_frame,
            text="Spara mall som...",
            width=140,
            height=32,
            command=self._save_template_to_file
        )
        save_as_button.grid(row=0, column=2, padx=5, pady=15)

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
        self.template_name_label.grid(row=0, column=3, padx=15, pady=15)

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
        help_button.grid(row=0, column=4, padx=(10, 15), pady=15)

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
        # Note: Checkbox availability is independent of field protection status
        can_be_disabled = field_id not in REQUIRED_ENABLED_FIELDS

        if field_def.protected:
            self._create_protected_field_components(containers, field_id, field_def, can_be_disabled)
        else:
            self._create_editable_field_components(containers, field_id, field_def, can_be_disabled)

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

    def _create_protected_field_components(self, containers, field_id: str, field_def, can_be_disabled: bool = False):
        """Create components for protected fields (label + disabled entry + optional checkbox)."""
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

        # Add invisible spacers for unused columns - widget-specific for proper alignment
        self._add_counter_spacer(containers['counter'])
        self._add_icon_spacer(containers['icon'])

        # Add checkbox if field can be disabled, otherwise add checkbox spacer
        if can_be_disabled:
            self._create_disable_checkbox(containers['checkbox'], field_id)
        else:
            self._add_checkbox_spacer(containers['checkbox'])


    def _create_editable_field_components(self, containers, field_id: str, field_def, can_be_disabled: bool = True):
        """Create components for fully editable fields (all components + optional checkbox)."""
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

        # Add checkbox if field can be disabled, otherwise add checkbox spacer
        if can_be_disabled:
            self._create_disable_checkbox(containers['checkbox'], field_id)
        else:
            self._add_checkbox_spacer(containers['checkbox'])

    def _create_disable_checkbox(self, container, field_id: str):
        """Create a disable checkbox for the specified field."""
        hide_checkbox = ctk.CTkCheckBox(
            container,
            text="Dölj",
            command=lambda fid=field_id: self._on_hide_checkbox_changed(fid)
        )
        hide_checkbox.pack(padx=(5, 10), pady=8, anchor="center")
        self.disable_checkboxes[field_id] = hide_checkbox

    def _add_counter_spacer(self, container):
        """Add invisible character counter spacer to match real counter dimensions."""
        spacer = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=10),
            fg_color="transparent"
        )
        spacer.pack(padx=5, pady=8, anchor="center")

    def _add_icon_spacer(self, container):
        """Add invisible validation icon spacer to match real icon dimensions."""
        spacer = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=14),
            fg_color="transparent"
        )
        spacer.pack(padx=5, pady=8, anchor="center")

    def _add_checkbox_spacer(self, container):
        """Add invisible checkbox spacer to match real checkbox dimensions."""
        spacer = ctk.CTkFrame(
            container,
            fg_color="transparent",
            width=85,
            height=24
        )
        spacer.pack(padx=(5, 10), pady=8, anchor="center")

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
        # Load active template name (fallback to "Standard")
        self.current_template = self.config_manager.load_active_template() or "Standard"

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
        # Note: _update_template_buttons_state() is called by _update_template_name_display()

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

            # Note: Template state is already handled in _apply_template_config()
            # No need to duplicate the state setting here

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

    def _save_current_template(self):
        """Save changes directly to the currently active template."""
        # Safety checks
        if not self._can_save_current_template():
            logger.warning("Attempted to save current template when not allowed")
            return

        # Additional validation: ensure current template name is valid
        if not self.current_template or not self.current_template.strip():
            logger.error("Cannot save: current template name is invalid")
            self._show_save_error("Mallnamnet är ogiltigt. Kan inte spara.")
            return

        try:
            # Extract current configuration
            field_config = self._get_current_field_config()

            # Create descriptive save message
            description = f"Mall uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # Attempt save using template manager
            success = template_manager.save_template(
                self.current_template,
                field_config,
                description
            )

            if success:
                # Save successful - update state and provide feedback
                self.is_template_modified = False
                self._show_save_success()
                logger.info(f"Successfully saved template: {self.current_template}")
            else:
                # Save failed - keep modified state and show error
                self._show_save_error("Kunde inte spara mallen. Kontrollera att du har skrivrättigheter.")
                logger.error(f"Failed to save template: {self.current_template}")

        except Exception as e:
            # Unexpected error - handle gracefully
            self._show_save_error(f"Ett oväntat fel uppstod: {str(e)}")
            logger.error(f"Unexpected error saving template {self.current_template}: {e}")

        finally:
            # Always update button state and display (regardless of success/failure)
            self._update_template_buttons_state()
            self._update_template_name_display()

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

            # Reset template state after successful save
            self.current_template = template_name
            self.is_template_modified = False
            self._update_template_name_display()

            logger.info(f"Saved template to file: {file_path}")

        except Exception as e:
            logger.error(f"Error saving template to file: {e}")
            messagebox.showerror(
                "Fel vid sparande",
                f"Kunde inte spara mallen: {str(e)}"
            )

    def _apply_template_config(self, template_config: dict, template_name: str):
        """Apply loaded template configuration to the dialog."""
        # Set flag to prevent race conditions during template loading
        self._loading_template = True
        logger.info(f"🔄 TEMPLATE LOADING START: {template_name} (_loading_template=True)")
        logger.debug(f"Starting template loading for: {template_name}, _loading_template=True")

        try:
            custom_names = template_config.get('custom_names', {})
            disabled_fields = template_config.get('disabled_fields', template_config.get('hidden_fields', []))

            # Clear current entries
            for entry in self.field_entries.values():
                entry.delete(0, 'end')
            self.current_values.clear()

            # Apply custom names
            for field_id, custom_name in custom_names.items():
                if field_id in self.field_entries:
                    logger.debug(f"Inserting custom name for {field_id}: {custom_name}")
                    self.field_entries[field_id].insert(0, custom_name)
                    self.current_values[field_id] = custom_name

            # Apply field state
            self.current_disabled_fields = set(disabled_fields)
            for field_id, checkbox in self.disable_checkboxes.items():
                is_disabled = field_id in self.current_disabled_fields
                checkbox.select() if is_disabled else checkbox.deselect()

            # Update validation
            self._update_validation()

            # Update current template name for reference - this must be done after validation
            self.current_template = template_name
            self.is_template_modified = False
            logger.info(f"✅ TEMPLATE STATE RESET: {template_name} (is_modified=False)")
            self._update_template_name_display()
            # Note: _update_template_buttons_state() is called by _update_template_name_display()

            logger.debug("Template config applied, scheduling flag clear with timeout protection")
            # Schedule flag clearing AFTER 150ms timeout for robust event protection
            self.dialog.after(150, self._clear_loading_flag)

        except Exception as e:
            # Clear flag immediately on error
            logger.error(f"Error applying template config: {e}")
            self._loading_template = False
            raise

    def _clear_loading_flag(self):
        """Clear the template loading flag after timeout protection period."""
        logger.info(f"🏁 TEMPLATE LOADING END: Timeout protection complete (_loading_template={self._loading_template} → False)")
        logger.debug(f"Clearing template loading flag after timeout protection (was {self._loading_template}, now False)")
        self._loading_template = False
        logger.debug("Template loading complete - timeout protection ended")

    def _can_save_current_template(self) -> bool:
        """
        Determine if current template can be saved directly.

        Returns:
            True if template can be saved, False otherwise
        """
        # Always disabled for Standard template - cannot be overwritten
        if self.current_template == "Standard":
            return False

        # Always disabled when loading template (race condition protection)
        if self._loading_template:
            return False

        # Only enabled when there are modifications to save
        return self.is_template_modified

    def _update_template_buttons_state(self):
        """Update the state and text of template save buttons."""
        if not self.save_template_button:
            return  # Button not created yet

        # Simple throttling: avoid excessive updates (max once per 50ms)
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - self._last_button_update < 50:
            return  # Too soon since last update
        self._last_button_update = current_time

        can_save = self._can_save_current_template()

        # Update button state
        button_state = "normal" if can_save else "disabled"
        self.save_template_button.configure(state=button_state)

        # Update button text dynamically
        if can_save:
            button_text = f"Spara mall: {self.current_template}"
        else:
            button_text = "Spara mall"

        # Update button text (truncate if too long to fit button width)
        max_length = 16  # Approximate max characters that fit in button width
        if len(button_text) > max_length:
            truncated_template = self.current_template[:max_length-12] + "..."
            button_text = f"Spara mall: {truncated_template}"

        self.save_template_button.configure(text=button_text)

    def _get_current_field_config(self) -> Dict:
        """
        Extract current field configuration for template saving.

        Returns:
            Dictionary with 'custom_names' and 'disabled_fields' keys
        """
        # Validate that we have current values to work with
        if not hasattr(self, 'current_values') or self.current_values is None:
            logger.warning("current_values not initialized, returning empty config")
            return {'custom_names': {}, 'disabled_fields': []}

        if not hasattr(self, 'current_disabled_fields') or self.current_disabled_fields is None:
            logger.warning("current_disabled_fields not initialized, using empty set")
            self.current_disabled_fields = set()

        # Extract custom names (only include non-empty, valid values)
        custom_names = {}
        for field_id, value in self.current_values.items():
            if isinstance(value, str) and value.strip():  # Only include valid, non-empty custom names
                # Additional validation: check field_id is valid
                if field_id in FIELD_DEFINITIONS:
                    custom_names[field_id] = value.strip()
                else:
                    logger.warning(f"Ignoring invalid field_id during config extraction: {field_id}")

        # Validate disabled fields list
        disabled_fields_list = []
        for field_id in self.current_disabled_fields:
            if isinstance(field_id, str) and field_id in FIELD_DEFINITIONS:
                disabled_fields_list.append(field_id)
            else:
                logger.warning(f"Ignoring invalid disabled field_id: {field_id}")

        # Create field configuration dictionary
        field_config = {
            'custom_names': custom_names,
            'disabled_fields': disabled_fields_list
        }

        return field_config

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

        # Update button state when template name display changes
        self._update_template_buttons_state()

    def _on_field_change(self, field_id: str):
        """Handle field value changes."""
        logger.debug(f"Field change event for {field_id}, _loading_template={self._loading_template}")

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

        # Mark template as modified (only if not currently loading a template)
        if not self._loading_template:
            logger.info(f"📝 TEMPLATE MODIFIED by field change in {field_id}")
            logger.debug(f"Marking template as modified due to field change in {field_id}")
            self.is_template_modified = True
            self._update_template_name_display()
            # Note: _update_template_buttons_state() is called by _update_template_name_display()
        else:
            logger.debug(f"Ignoring field change during template loading for {field_id}")

    def _on_hide_checkbox_changed(self, field_id: str):
        """Handle hide checkbox changes."""
        checkbox = self.disable_checkboxes[field_id]
        is_checked = checkbox.get()

        if is_checked:
            self.current_disabled_fields.add(field_id)
        else:
            self.current_disabled_fields.discard(field_id)

        logger.debug(f"Field {field_id} visibility changed: {'hidden' if is_checked else 'visible'}")

        # Mark template as modified (only if not currently loading a template)
        if not self._loading_template:
            logger.info(f"📝 TEMPLATE MODIFIED by checkbox change in {field_id}")
            logger.debug(f"Marking template as modified due to checkbox change in {field_id}")
            self.is_template_modified = True
            self._update_template_name_display()
            # Note: _update_template_buttons_state() is called by _update_template_name_display()
        else:
            logger.debug(f"Ignoring checkbox change during template loading for {field_id}")

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

        # Reset template state to Standard
        self.current_template = "Standard"
        self.is_template_modified = False
        self._update_template_name_display()
        # Note: _update_template_buttons_state() is called by _update_template_name_display()

        # Update validation
        self._update_validation()

        logger.info("Configuration reset to defaults with template state updated")

    def _apply_changes(self):
        """Apply field name changes and visibility settings."""
        if self.validation_errors:
            return  # Should not happen if button is properly disabled

        # Check if template has been modified and show save prompt
        if self.is_template_modified:
            save_choice = self._show_save_prompt()

            if save_choice == SavePromptChoice.CANCEL:
                return  # User cancelled, keep dialog open
            elif save_choice == SavePromptChoice.SAVE_FIRST:
                # Attempt to save template first
                save_success = self._save_template_with_feedback()
                if not save_success:
                    # Save failed or was cancelled, ask user what to do
                    if not self._handle_save_failure():
                        return  # User chose to cancel after save failure
                    # If user chose to continue, proceed with apply

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

            # Save active template name for persistence
            self.config_manager.save_active_template(self.current_template)

            # Call the callback to trigger application update
            if self.on_apply_callback:
                self.on_apply_callback()

            # Close dialog
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Failed to apply configuration: {e}")
            self._show_error("Kunde inte tillämpa ändringar", f"Ett fel uppstod: {str(e)}")

    def _show_save_prompt(self) -> str:
        """Show save prompt dialog when template has modifications."""
        save_dialog = ctk.CTkToplevel(self.dialog)
        save_dialog.title("Spara ändringar?")
        save_dialog.geometry("500x300")
        save_dialog.transient(self.dialog)
        save_dialog.grab_set()

        # Center on parent dialog
        self.dialog.update_idletasks()
        x = self.dialog.winfo_rootx() + 200
        y = self.dialog.winfo_rooty() + 200
        save_dialog.geometry(f"500x300+{x}+{y}")

        result = {"choice": SavePromptChoice.CANCEL}

        # Warning icon and title
        warning_label = ctk.CTkLabel(
            save_dialog,
            text="💾 SPARA ÄNDRINGAR?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF8C00"
        )
        warning_label.pack(pady=(20, 15))

        # Main message
        message_label = ctk.CTkLabel(
            save_dialog,
            text=f"Du har gjort ändringar i mallen '{self.current_template}'.\n\nVad vill du göra innan ändringarna tillämpas?",
            font=ctk.CTkFont(size=12),
            justify="center",
            wraplength=400
        )
        message_label.pack(pady=(0, 20))

        # Buttons frame
        button_frame = ctk.CTkFrame(save_dialog)
        button_frame.pack(pady=20, padx=20, fill="x")

        def on_save_first():
            result["choice"] = SavePromptChoice.SAVE_FIRST
            save_dialog.destroy()

        def on_continue_without_saving():
            result["choice"] = SavePromptChoice.CONTINUE_WITHOUT_SAVING
            save_dialog.destroy()

        def on_cancel():
            result["choice"] = SavePromptChoice.CANCEL
            save_dialog.destroy()

        # Save first button (orange - primary action)
        save_button = ctk.CTkButton(
            button_frame,
            text="💾 Spara mall först",
            command=on_save_first,
            width=140,
            height=40,
            fg_color="#FF8C00",
            hover_color="#FF7F00"
        )
        save_button.pack(side="left", padx=(10, 5))

        # Continue without saving (blue - secondary action)
        continue_button = ctk.CTkButton(
            button_frame,
            text="➤ Fortsätt utan att spara",
            command=on_continue_without_saving,
            width=160,
            height=40,
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        continue_button.pack(side="left", padx=5)

        # Cancel button (gray - cancel action)
        cancel_button = ctk.CTkButton(
            button_frame,
            text="✕ Avbryt",
            command=on_cancel,
            width=100,
            height=40,
            fg_color="#666666",
            hover_color="#555555"
        )
        cancel_button.pack(side="right", padx=(5, 10))

        # Wait for user response
        save_dialog.wait_window()
        return result["choice"]

    def _save_template_with_feedback(self) -> bool:
        """Save template with feedback and return success status."""
        try:
            # Call existing save method
            self._save_template_to_file()
            # Check if template was actually saved (not cancelled)
            return not self.is_template_modified  # If save was successful, is_template_modified should be False
        except Exception as e:
            logger.error(f"Save template failed: {e}")
            return False

    def _handle_save_failure(self) -> bool:
        """Handle save failure scenario - return True to continue, False to cancel."""
        failure_dialog = ctk.CTkToplevel(self.dialog)
        failure_dialog.title("Kunde inte spara")
        failure_dialog.geometry("400x200")
        failure_dialog.transient(self.dialog)
        failure_dialog.grab_set()

        # Center on parent dialog
        self.dialog.update_idletasks()
        x = self.dialog.winfo_rootx() + 250
        y = self.dialog.winfo_rooty() + 250
        failure_dialog.geometry(f"400x200+{x}+{y}")

        result = {"continue": False}

        # Error message
        error_label = ctk.CTkLabel(
            failure_dialog,
            text="⚠️ Kunde inte spara mallen",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FF6B35"
        )
        error_label.pack(pady=(20, 10))

        message_label = ctk.CTkLabel(
            failure_dialog,
            text="Mallen kunde inte sparas.\nVill du fortsätta ändå utan att spara?",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        message_label.pack(pady=(0, 20))

        # Buttons frame
        button_frame = ctk.CTkFrame(failure_dialog)
        button_frame.pack(pady=10, fill="x")

        def on_continue():
            result["continue"] = True
            failure_dialog.destroy()

        def on_cancel():
            result["continue"] = False
            failure_dialog.destroy()

        # Continue button
        continue_button = ctk.CTkButton(
            button_frame,
            text="➤ Fortsätt utan att spara",
            command=on_continue,
            width=150,
            height=35,
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        continue_button.pack(side="left", padx=(20, 10))

        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="✕ Avbryt",
            command=on_cancel,
            width=100,
            height=35,
            fg_color="#666666",
            hover_color="#555555"
        )
        cancel_button.pack(side="right", padx=(10, 20))

        # Wait for user response
        failure_dialog.wait_window()
        return result["continue"]

    def _show_save_success(self):
        """Show success feedback when template is saved."""
        success_dialog = ctk.CTkToplevel(self.dialog)
        success_dialog.title("Mall sparad")
        success_dialog.geometry("350x150")
        success_dialog.transient(self.dialog)
        success_dialog.grab_set()

        # Center on parent dialog
        self.dialog.update_idletasks()
        x = self.dialog.winfo_rootx() + 300
        y = self.dialog.winfo_rooty() + 300
        success_dialog.geometry(f"350x150+{x}+{y}")

        # Success message
        success_label = ctk.CTkLabel(
            success_dialog,
            text="✅ Mall sparad!",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#28A745"
        )
        success_label.pack(pady=(20, 10))

        detail_label = ctk.CTkLabel(
            success_dialog,
            text=f"Mallen '{self.current_template}' har uppdaterats.",
            font=ctk.CTkFont(size=12)
        )
        detail_label.pack(pady=(0, 20))

        # OK button
        ok_button = ctk.CTkButton(
            success_dialog,
            text="OK",
            width=80,
            height=30,
            command=success_dialog.destroy,
            fg_color="#28A745",
            hover_color="#218838"
        )
        ok_button.pack(pady=(0, 20))

        # Auto-close after 2 seconds
        success_dialog.after(2000, success_dialog.destroy)

    def _show_save_error(self, error_message: str):
        """Show error feedback when template save fails."""
        error_dialog = ctk.CTkToplevel(self.dialog)
        error_dialog.title("Kunde inte spara")
        error_dialog.geometry("400x200")
        error_dialog.transient(self.dialog)
        error_dialog.grab_set()

        # Center on parent dialog
        self.dialog.update_idletasks()
        x = self.dialog.winfo_rootx() + 250
        y = self.dialog.winfo_rooty() + 250
        error_dialog.geometry(f"400x200+{x}+{y}")

        # Error message
        error_label = ctk.CTkLabel(
            error_dialog,
            text="❌ Kunde inte spara mall",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#DC3545"
        )
        error_label.pack(pady=(20, 10))

        detail_label = ctk.CTkLabel(
            error_dialog,
            text=error_message,
            font=ctk.CTkFont(size=12),
            wraplength=350,
            justify="center"
        )
        detail_label.pack(pady=(0, 20), padx=20)

        # OK button
        ok_button = ctk.CTkButton(
            error_dialog,
            text="OK",
            width=80,
            height=30,
            command=error_dialog.destroy,
            fg_color="#DC3545",
            hover_color="#C82333"
        )
        ok_button.pack(pady=(0, 20))

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
