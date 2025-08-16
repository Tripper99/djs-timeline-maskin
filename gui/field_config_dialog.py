"""
Field configuration dialog for customizing Excel field names.
Allows users to rename most fields while protecting system-critical fields.
"""

import logging
from typing import Callable, Dict, Optional

import customtkinter as ctk

from core.config import ConfigManager
from core.field_definitions import FIELD_DEFINITIONS, FIELD_ORDER, field_manager
from core.field_validator import realtime_validator

logger = logging.getLogger(__name__)


class FieldConfigDialog:
    """Dialog for configuring custom field names."""

    def __init__(self, parent_app, on_apply_callback: Optional[Callable] = None):
        self.parent_app = parent_app
        self.on_apply_callback = on_apply_callback
        self.config_manager = ConfigManager()

        # Dialog window
        self.dialog = None

        # Field entry widgets
        self.field_entries: Dict[str, ctk.CTkEntry] = {}
        self.field_labels: Dict[str, ctk.CTkLabel] = {}
        self.char_count_labels: Dict[str, ctk.CTkLabel] = {}
        self.validation_icons: Dict[str, ctk.CTkLabel] = {}

        # Current field values
        self.current_values: Dict[str, str] = {}

        # Validation tracking
        self.validation_errors: Dict[str, str] = {}

        # Create dialog
        self._create_dialog()

    def _create_dialog(self):
        """Create the main dialog window."""
        self.dialog = ctk.CTkToplevel(self.parent_app)
        self.dialog.title("Konfigurera Excel-fält")
        self.dialog.geometry("900x700")
        self.dialog.transient(self.parent_app)
        self.dialog.grab_set()  # Modal dialog

        # Center on parent
        self._center_dialog()

        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(1, weight=1)

        # Create main sections
        self._create_header()
        self._create_main_content()
        self._create_footer()

        # Load current values
        self._load_current_values()

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
        dialog_width = 900
        dialog_height = 700
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)

        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def _create_header(self):
        """Create dialog header with title and instructions."""
        header_frame = ctk.CTkFrame(self.dialog)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Konfigurera Excel-fältnamn",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(15, 5))

        # Instructions
        instructions = (
            "Anpassa namnen på Excel-fälten efter dina behov. Grå fält kan inte ändras.\n"
            "Maxlängd: 13 tecken. Inga mellanslag tillåtna."
        )
        instruction_label = ctk.CTkLabel(
            header_frame,
            text=instructions,
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        instruction_label.grid(row=1, column=0, pady=(0, 15))

    def _create_main_content(self):
        """Create main content area with scrollable field sections."""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self.dialog)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_columnconfigure((0, 1), weight=1)

        # Section headers
        protected_header = ctk.CTkLabel(
            main_frame,
            text="🔒 Skyddade fält (kan ej ändras)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#888888"
        )
        protected_header.grid(row=0, column=0, pady=(10, 15), padx=10, sticky="w")

        renamable_header = ctk.CTkLabel(
            main_frame,
            text="✏️ Anpassningsbara fält",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2196F3"
        )
        renamable_header.grid(row=0, column=1, pady=(10, 15), padx=10, sticky="w")

        # Create field sections
        self._create_protected_fields(main_frame)
        self._create_renamable_fields(main_frame)

    def _create_protected_fields(self, parent):
        """Create section for protected (non-renamable) fields."""
        row = 1

        for field_id in FIELD_ORDER:
            field_def = FIELD_DEFINITIONS[field_id]
            if not field_def.protected:
                continue

            # Field container
            field_frame = ctk.CTkFrame(parent, fg_color="gray90")
            field_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
            field_frame.grid_columnconfigure(1, weight=1)

            # Lock icon
            lock_label = ctk.CTkLabel(field_frame, text="🔒", font=ctk.CTkFont(size=14))
            lock_label.grid(row=0, column=0, padx=(10, 5), pady=8)

            # Field name (disabled appearance)
            name_label = ctk.CTkLabel(
                field_frame,
                text=field_def.default_display_name,
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="gray50",
                anchor="w"
            )
            name_label.grid(row=0, column=1, sticky="w", padx=5, pady=8)

            # Help text
            help_text = self._get_field_help_text(field_def)
            help_label = ctk.CTkLabel(
                field_frame,
                text=help_text,
                font=ctk.CTkFont(size=10),
                text_color="gray40",
                anchor="w"
            )
            help_label.grid(row=0, column=2, sticky="w", padx=(10, 15), pady=8)

            row += 1

    def _create_renamable_fields(self, parent):
        """Create section for renamable fields."""
        row = 1

        for field_id in FIELD_ORDER:
            field_def = FIELD_DEFINITIONS[field_id]
            if field_def.protected:
                continue

            # Field container
            field_frame = ctk.CTkFrame(parent)
            field_frame.grid(row=row, column=1, sticky="ew", padx=10, pady=2)
            field_frame.grid_columnconfigure(1, weight=1)

            # Original name label
            original_label = ctk.CTkLabel(
                field_frame,
                text=f"{field_def.default_display_name}:",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray60",
                width=80,
                anchor="w"
            )
            original_label.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="w")

            # Entry field for custom name
            entry = ctk.CTkEntry(
                field_frame,
                placeholder_text="Ange nytt namn...",
                font=ctk.CTkFont(size=12),
                width=120
            )
            entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

            # Bind validation
            entry.bind('<KeyRelease>', lambda e, fid=field_id: self._on_field_change(fid))
            entry.bind('<FocusOut>', lambda e, fid=field_id: self._on_field_change(fid))

            self.field_entries[field_id] = entry

            # Character counter
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
            icon_label.grid(row=0, column=3, padx=(5, 10), pady=8)
            self.validation_icons[field_id] = icon_label

            # Help text row
            help_text = self._get_field_help_text(field_def)
            help_label = ctk.CTkLabel(
                field_frame,
                text=help_text,
                font=ctk.CTkFont(size=10),
                text_color="gray50",
                anchor="w"
            )
            help_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=(10, 10), pady=(0, 8))

            row += 1

    def _get_field_help_text(self, field_def) -> str:
        """Get help text for a field based on its type."""
        if field_def.field_type.value == "text":
            return "Textfält med 1000 tecken"
        elif field_def.field_type.value == "entry":
            return "Kort textfält"
        elif field_def.field_type.value == "date":
            return "Datumfält (YYYY-MM-DD)"
        elif field_def.field_type.value == "time":
            return "Tidfält (HH:MM)"
        elif field_def.field_type.value == "auto":
            return "Automatiskt ifylld"
        elif field_def.field_type.value == "formula":
            return "Beräknat fält"
        else:
            return "Systemfält"

    def _create_footer(self):
        """Create dialog footer with warning and buttons."""
        footer_frame = ctk.CTkFrame(self.dialog)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        footer_frame.grid_columnconfigure(0, weight=1)

        # Warning section
        warning_frame = ctk.CTkFrame(footer_frame, fg_color="#FFF3CD", corner_radius=8)
        warning_frame.grid(row=0, column=0, sticky="ew", pady=(15, 20), padx=15)
        warning_frame.grid_columnconfigure(1, weight=1)

        warning_icon = ctk.CTkLabel(warning_frame, text="⚠️", font=ctk.CTkFont(size=16))
        warning_icon.grid(row=0, column=0, padx=(15, 10), pady=12)

        warning_text = ctk.CTkLabel(
            warning_frame,
            text="VARNING: Alla fältdata kommer att raderas när ändringar tillämpas!",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#856404",
            anchor="w"
        )
        warning_text.grid(row=0, column=1, sticky="w", padx=(0, 15), pady=12)

        # Button section
        button_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, sticky="ew", padx=15)
        button_frame.grid_columnconfigure(1, weight=1)

        # Help button
        help_button = ctk.CTkButton(
            button_frame,
            text="Hjälp",
            width=80,
            height=35,
            fg_color="gray60",
            hover_color="gray50",
            command=self._show_help
        )
        help_button.grid(row=0, column=0, pady=10)

        # Right side buttons
        right_button_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        right_button_frame.grid(row=0, column=2, pady=10)

        # Cancel button
        cancel_button = ctk.CTkButton(
            right_button_frame,
            text="Avbryt",
            width=100,
            height=35,
            fg_color="gray60",
            hover_color="gray50",
            command=self._cancel
        )
        cancel_button.grid(row=0, column=0, padx=(0, 10))

        # Apply button
        self.apply_button = ctk.CTkButton(
            right_button_frame,
            text="Tillämpa ändringar",
            width=150,
            height=35,
            fg_color="#2196F3",
            hover_color="#1976D2",
            command=self._apply_changes
        )
        self.apply_button.grid(row=0, column=1)

    def _load_current_values(self):
        """Load current custom field names into the dialog."""
        custom_names = self.config_manager.load_custom_field_names()
        field_manager.set_custom_names(custom_names)

        for field_id, entry in self.field_entries.items():
            current_name = field_manager.get_display_name(field_id)
            field_def = FIELD_DEFINITIONS[field_id]

            # Only show custom names (not default names)
            if current_name != field_def.default_display_name:
                entry.insert(0, current_name)
                self.current_values[field_id] = current_name
            else:
                self.current_values[field_id] = ""

    def _on_field_change(self, field_id: str):
        """Handle field value changes."""
        entry = self.field_entries[field_id]
        new_value = entry.get().strip()
        self.current_values[field_id] = new_value

        # Update character counter
        char_label = self.char_count_labels[field_id]
        char_label.configure(text=f"{len(new_value)}/13")

        # Update validation
        self._update_field_validation(field_id)
        self._update_apply_button()

    def _update_field_validation(self, field_id: str):
        """Update validation display for a specific field."""
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
                fg_color="#2196F3",
                text="Tillämpa ändringar"
            )

    def _show_help(self):
        """Show help information."""
        help_text = """HJÄLP: Anpassa Excel-fältnamn

REGLER:
• Maxlängd: 13 tecken
• Inga mellanslag tillåtna
• Alla namn måste vara unika
• Skyddade fält kan inte ändras

FÄLTTYPER:
• Note1-3: Textfält med 1000 tecken för längre anteckningar
• Övriga fält: Korta textfält för snabb information

VIKTIG INFORMATION:
När du tillämpar ändringar kommer alla fältdata att raderas och konfigurationsfilen återställas. Detta säkerställer att inga gamla data orsakar problem med de nya fältnamnen.

Du kan alltid återgå till standardnamnen genom att lämna fälten tomma."""

        help_dialog = ctk.CTkToplevel(self.dialog)
        help_dialog.title("Hjälp - Fältkonfiguration")
        help_dialog.geometry("500x400")
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

    def _cancel(self):
        """Cancel dialog without saving."""
        self.dialog.destroy()

    def _apply_changes(self):
        """Apply field name changes."""
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

        # Save and apply changes
        try:
            # Save custom names to config
            self.config_manager.save_custom_field_names(custom_names)

            # Update field manager
            field_manager.set_custom_names(custom_names)

            logger.info(f"Applied custom field names: {custom_names}")

            # Call the callback to trigger application update
            if self.on_apply_callback:
                self.on_apply_callback()

            # Close dialog
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Failed to apply field name changes: {e}")
            # Show error dialog
            error_dialog = ctk.CTkToplevel(self.dialog)
            error_dialog.title("Fel")
            error_dialog.geometry("400x200")
            error_dialog.transient(self.dialog)
            error_dialog.grab_set()

            error_label = ctk.CTkLabel(
                error_dialog,
                text=f"Kunde inte spara ändringar:\n{str(e)}",
                wraplength=350
            )
            error_label.pack(expand=True, padx=20, pady=20)

            ok_button = ctk.CTkButton(
                error_dialog,
                text="OK",
                command=error_dialog.destroy
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
        x = self.dialog.winfo_rootx() + 225
        y = self.dialog.winfo_rooty() + 175
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
            text="Detta kommer att:\n\n• Radera alla fältdata\n• Ta bort konfigurationsfilen\n• Rita om användargränssnittet\n\nÄr du säker på att du vill fortsätta?",
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
            fg_color="#FF6B35",
            hover_color="#E55A2B",
            command=confirm
        )
        confirm_btn.pack(side="left")

        # Wait for dialog to close
        confirm_dialog.wait_window()

        return result["confirmed"]

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
