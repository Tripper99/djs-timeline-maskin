"""
Field configuration dialog redesigned with template support and field visibility controls.
Based on user mockup requirements with two-column layout and comprehensive template management.
"""

import logging
from tkinter import messagebox
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
        self.template_dropdown = None

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
        """Create template control row with dropdown and buttons."""
        template_frame = ctk.CTkFrame(self.dialog)
        template_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        template_frame.grid_columnconfigure(4, weight=1)  # Spacer column

        # Template dropdown
        templates = template_manager.list_templates()
        self.template_dropdown = ctk.CTkComboBox(
            template_frame,
            values=templates,
            command=self._on_template_selected,
            width=200,
            state="readonly"
        )
        self.template_dropdown.grid(row=0, column=0, padx=(15, 10), pady=15)
        self.template_dropdown.set(self.current_template)

        # Template buttons
        open_button = ctk.CTkButton(
            template_frame,
            text="Öppna template",
            width=120,
            height=32,
            command=self._open_template
        )
        open_button.grid(row=0, column=1, padx=5, pady=15)

        save_button = ctk.CTkButton(
            template_frame,
            text="Spara som",
            width=100,
            height=32,
            command=self._save_as_template
        )
        save_button.grid(row=0, column=2, padx=5, pady=15)

        delete_button = ctk.CTkButton(
            template_frame,
            text="Radera template",
            width=130,
            height=32,
            fg_color="#DC3545",
            hover_color="#C82333",
            command=self._delete_template
        )
        delete_button.grid(row=0, column=3, padx=5, pady=15)

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
        help_button.grid(row=0, column=5, padx=(10, 15), pady=15)

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
        # Column header
        left_header = ctk.CTkLabel(
            parent,
            text="VÄNSTER KOLUMN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2196F3"
        )
        left_header.grid(row=0, column=0, pady=(10, 15), padx=10, sticky="w")

        row = 1
        for field_id in LEFT_COLUMN_ORDER:
            self._create_field_row(parent, field_id, row, 0)
            row += 1

    def _create_right_column(self, parent):
        """Create right column with second set of fields."""
        # Column header
        right_header = ctk.CTkLabel(
            parent,
            text="HÖGER KOLUMN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2196F3"
        )
        right_header.grid(row=0, column=1, pady=(10, 15), padx=10, sticky="w")

        row = 1
        for field_id in RIGHT_COLUMN_ORDER:
            self._create_field_row(parent, field_id, row, 1)
            row += 1

    def _create_field_row(self, parent, field_id: str, row: int, column: int):
        """Create a single field row with all controls."""
        field_def = FIELD_DEFINITIONS[field_id]

        # Field container frame
        field_frame = ctk.CTkFrame(parent)
        field_frame.grid(row=row, column=column, sticky="ew", padx=10, pady=2)
        field_frame.grid_columnconfigure(1, weight=1)

        # Field label
        display_name = field_def.default_display_name
        label_text = f"{display_name}:"

        field_label = ctk.CTkLabel(
            field_frame,
            text=label_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            width=100,
            anchor="w"
        )
        field_label.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="w")

        # Input field or protected field display
        if field_def.protected:
            # Protected field - greyed out display
            protected_entry = ctk.CTkEntry(
                field_frame,
                placeholder_text=display_name,
                font=ctk.CTkFont(size=12),
                state="disabled",
                fg_color="gray90"
            )
            protected_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        else:
            # Editable field
            entry = ctk.CTkEntry(
                field_frame,
                placeholder_text="Ange nytt namn...",
                font=ctk.CTkFont(size=12),
                width=150
            )
            entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

            # Bind validation events
            entry.bind('<KeyRelease>', lambda e, fid=field_id: self._on_field_change(fid))
            entry.bind('<FocusOut>', lambda e, fid=field_id: self._on_field_change(fid))

            self.field_entries[field_id] = entry

            # Character counter (only for editable fields)
            char_label = ctk.CTkLabel(
                field_frame,
                text="0/13",
                font=ctk.CTkFont(size=10),
                text_color="gray50",
                width=40
            )
            char_label.grid(row=0, column=2, padx=5, pady=8)
            self.char_count_labels[field_id] = char_label

            # Validation icon
            icon_label = ctk.CTkLabel(
                field_frame,
                text="⚪",
                font=ctk.CTkFont(size=14),
                width=20
            )
            icon_label.grid(row=0, column=3, padx=5, pady=8)
            self.validation_icons[field_id] = icon_label

        # Hide checkbox (except for required fields)
        if field_id not in REQUIRED_ENABLED_FIELDS:
            hide_checkbox = ctk.CTkCheckBox(
                field_frame,
                text="Dölj",
                width=60,
                command=lambda fid=field_id: self._on_hide_checkbox_changed(fid)
            )
            hide_checkbox.grid(row=0, column=4, padx=(5, 10), pady=8)
            self.disable_checkboxes[field_id] = hide_checkbox

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
        # Load active template
        active_template = self.config_manager.load_active_template()
        if active_template and active_template in template_manager.list_templates():
            self.current_template = active_template
            self.template_dropdown.set(active_template)

        # Load current field names
        custom_names = self.config_manager.load_custom_field_names()
        field_manager.set_custom_names(custom_names)

        # Load field state
        disabled_fields = self.config_manager.load_field_state()
        field_state_manager.set_disabled_fields(disabled_fields)
        self.current_disabled_fields = set(disabled_fields)

        # Populate field entries
        for field_id, entry in self.field_entries.items():
            current_name = field_manager.get_display_name(field_id)
            field_def = FIELD_DEFINITIONS[field_id]

            # Only show custom names (not default names)
            if current_name != field_def.default_display_name:
                entry.insert(0, current_name)
                self.current_values[field_id] = current_name
            else:
                self.current_values[field_id] = ""

        # Update disable checkboxes
        for field_id, checkbox in self.disable_checkboxes.items():
            is_disabled = field_id in self.current_disabled_fields
            checkbox.select() if is_disabled else checkbox.deselect()

    def _on_template_selected(self, template_name: str):
        """Handle template selection from dropdown."""
        self.current_template = template_name
        logger.info(f"Template selected: {template_name}")

    def _open_template(self):
        """Open/load the selected template."""
        if not self.current_template:
            return

        template_config = template_manager.load_template(self.current_template)
        if not template_config:
            self._show_error("Kunde inte ladda template", f"Template '{self.current_template}' kunde inte laddas.")
            return

        # Apply template configuration
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

        logger.info(f"Loaded template: {self.current_template}")

    def _save_as_template(self):
        """Save current configuration as a new template."""
        # Get template name from user
        dialog = ctk.CTkInputDialog(
            text="Ange namn för template:",
            title="Spara template"
        )
        template_name = dialog.get_input()

        if not template_name:
            return

        # Validate template name
        if not template_manager._validate_template_name(template_name):
            self._show_error("Ogiltigt template-namn", "Template-namnet innehåller ogiltiga tecken eller är för långt.")
            return

        # Check if template exists
        if template_name in template_manager.list_templates():
            if not messagebox.askyesno("Template finns", f"Template '{template_name}' finns redan. Vill du skriva över den?"):
                return

        # Prepare configuration
        custom_names = {}
        for field_id, value in self.current_values.items():
            if value.strip():
                custom_names[field_id] = value.strip()

        config = {
            'custom_names': custom_names,
            'disabled_fields': list(self.current_disabled_fields)
        }

        # Save template
        if template_manager.save_template(template_name, config, "Sparad från konfigurationsdialog"):
            # Update dropdown
            templates = template_manager.list_templates()
            self.template_dropdown.configure(values=templates)
            self.template_dropdown.set(template_name)
            self.current_template = template_name

            messagebox.showinfo("Template sparad", f"Template '{template_name}' har sparats.")
            logger.info(f"Template saved: {template_name}")
        else:
            self._show_error("Kunde inte spara", f"Template '{template_name}' kunde inte sparas.")

    def _delete_template(self):
        """Delete the selected template."""
        if self.current_template == "Standard":
            messagebox.showwarning("Kan inte radera", "Standard-templaten kan inte raderas.")
            return

        if not messagebox.askyesno("Bekräfta radering", f"Är du säker på att du vill radera template '{self.current_template}'?"):
            return

        if template_manager.delete_template(self.current_template):
            # Update dropdown
            templates = template_manager.list_templates()
            self.template_dropdown.configure(values=templates)
            self.template_dropdown.set("Standard")
            self.current_template = "Standard"

            messagebox.showinfo("Template raderad", f"Template '{self.current_template}' har raderats.")
            logger.info(f"Template deleted: {self.current_template}")
        else:
            self._show_error("Kunde inte radera", f"Template '{self.current_template}' kunde inte raderas.")

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

    def _on_hide_checkbox_changed(self, field_id: str):
        """Handle hide checkbox changes."""
        checkbox = self.disable_checkboxes[field_id]
        is_checked = checkbox.get()

        if is_checked:
            self.current_disabled_fields.add(field_id)
        else:
            self.current_disabled_fields.discard(field_id)

        logger.debug(f"Field {field_id} visibility changed: {'hidden' if is_checked else 'visible'}")

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

        # Get validation feedback
        feedback = realtime_validator.get_instant_feedback(value, field_id)

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

            # Save active template
            self.config_manager.save_active_template(self.current_template)

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
• Spara konfigurationer som templates för framtida användning
• Växla mellan olika templates med dropdown-menyn

TEMPLATES:
• "Standard" - standardkonfiguration som alltid finns
• Skapa egna templates med "Spara som"-knappen
• Ladda befintliga templates med "Öppna template"
• Radera templates du inte längre behöver (utom Standard)

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
