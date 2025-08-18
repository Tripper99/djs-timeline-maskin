#!/usr/bin/env python3
"""
Main window for DJs Timeline-maskin
Contains the PDFProcessorApp class with GUI implementation
"""

# Standard library imports
import logging
import os
import platform
import subprocess
from pathlib import Path

# GUI imports
try:
    import tkinter as tk
    from tkinter import messagebox

    import customtkinter as ctk

    # Configure CustomTkinter
    ctk.set_appearance_mode("light")  # "light" or "dark"
    ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
except ImportError as e:
    print(f"Error: Required GUI library not installed. {e}")
    print("Install with: pip install customtkinter")
    exit(1)


# Local imports
from core.config import ConfigManager
from core.excel_manager import ExcelManager
from gui.dialogs import DialogManager
from gui.event_handlers import EventHandlersMixin
from gui.excel_fields import ExcelFieldManager
from gui.excel_operations import ExcelOperationsMixin
from gui.formatting_manager import FormattingManagerMixin
from gui.layout_manager import LayoutManagerMixin

# Mixin imports
from gui.pdf_operations import PDFOperationsMixin
from gui.stats_manager import StatsManagerMixin
from gui.undo_manager import UndoManagerMixin
from gui.utils import ScrollableFrame, ToolTip
from utils.constants import VERSION

# Setup logging
logger = logging.getLogger(__name__)

class PDFProcessorApp(PDFOperationsMixin, ExcelOperationsMixin, LayoutManagerMixin, EventHandlersMixin, UndoManagerMixin, FormattingManagerMixin, StatsManagerMixin):
    """Main application class"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.excel_manager = ExcelManager()
        self.dialog_manager = DialogManager(self)

        # Internal data storage
        self.current_pdf_path = ""
        self.current_pdf_pages = 0
        self.original_filename_components = {}  # Store original parsed components

        # Statistics
        self.stats = {
            'pdfs_opened': 0,
            'files_renamed': 0,
            'excel_rows_added': 0
        }

        # Load custom field names BEFORE setting up GUI
        self._load_custom_field_names()

        # Setup GUI (this creates the root window needed for tkinter variables)
        self.setup_gui()

        # Initialize lock_vars with current field display names AFTER root window exists
        self._initialize_lock_vars()

        # Create ExcelFieldManager AFTER lock_vars are initialized
        self.excel_field_manager = ExcelFieldManager(self)

        # Now create the Excel fields that were skipped during setup_gui()
        self.excel_field_manager.create_excel_fields()

        # Apply saved font size to text fields after they're created
        saved_font_size = self.config.get('text_font_size', 9)
        self.apply_text_font_size(saved_font_size)

        self.load_saved_excel_file()  # Load previously selected Excel file
        self.load_saved_output_folder()  # Load previously selected output folder

        # Load and restore locked fields after GUI is created
        self.excel_field_manager.restore_locked_fields()

    def parse_geometry(self, geometry_string):
        """
        Parse tkinter geometry string safely handling negative coordinates.

        Args:
            geometry_string (str): Format "widthxheight+x+y" or "widthxheight+x-y" etc.

        Returns:
            tuple: (width, height, x, y) or None if parsing fails
        """
        try:
            import re
            # Match pattern: widthxheight+x+y (where x,y can be negative)
            match = re.match(r'(\d+)x(\d+)([\+\-]\d+)([\+\-]\d+)', geometry_string)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                x = int(match.group(3))
                y = int(match.group(4))
                return (width, height, x, y)
            return None
        except Exception:
            return None

    def build_geometry(self, width, height, x, y):
        """
        Build tkinter geometry string from components.

        Args:
            width, height, x, y (int): Window dimensions and position

        Returns:
            str: Geometry string in format "widthxheight+x+y"
        """
        x_sign = '+' if x >= 0 else ''
        y_sign = '+' if y >= 0 else ''
        return f"{width}x{height}{x_sign}{x}{y_sign}{y}"

    def setup_gui(self):
        """Setup the main GUI"""
        # Fix Windows DPI scaling issues that can cause geometry problems
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # For Windows 10
            logger.info("DPI awareness set successfully")
        except Exception as e:
            logger.warning(f"Could not set DPI awareness: {e}")

        # Create main window with CustomTkinter
        self.root = ctk.CTk()
        self.root.title(f"DJs Timeline-maskin {VERSION}")
        self.root.geometry("1400x900")  # Initial size before responsive calculation

        # Set application icon
        try:
            icon_path = Path(__file__).parent.parent / "Agg-med-smor-v4-transperent.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
                logger.info(f"Application icon set to: {icon_path}")
            else:
                logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logger.warning(f"Could not set application icon: {e}")

        # Position window - centered horizontally but very high up vertically
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Use content-based height instead of screen percentage
        window_height = 680  # Fixed height based on actual content requirements
        logger.info(f"Screen: {screen_width}x{screen_height}, using content-based window height: {window_height}")

        # Debug actual screen measurements after DPI fix
        logger.info(f"DPI aware measurements - Screen: {self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")

        # Check if saved geometry exceeds our height limit and adjust it
        saved_geometry = self.config.get('window_geometry', '')
        if saved_geometry:
            try:
                # Parse saved geometry using safe parser
                parsed = self.parse_geometry(saved_geometry)
                if parsed:
                    saved_width, saved_height, x_pos, y_pos = parsed

                    if saved_height > window_height:
                        # Reconstruct geometry with limited height
                        limited_geometry = self.build_geometry(saved_width, window_height, x_pos, y_pos)
                        self.root.geometry(limited_geometry)
                        logger.info(f"Limited saved geometry: {saved_geometry} -> {limited_geometry}")
                    else:
                        self.root.geometry(saved_geometry)
                        logger.info(f"Using saved geometry: {saved_geometry}")
                else:
                    # Fallback to calculated geometry
                    x = 100  # Simple left positioning with reasonable margin
                    y = 50   # Small offset from top
                    self.root.geometry(f"1400x{window_height}+{x}+{y}")
            except Exception as e:
                logger.warning(f"Error parsing saved geometry {saved_geometry}: {e}")
                # Fallback to calculated geometry
                x = 100  # Simple left positioning with reasonable margin
                y = 50   # Small offset from top
                self.root.geometry(f"1400x{window_height}+{x}+{y}")
        else:
            # No saved geometry, use calculated
            x = 100  # Simple left positioning with reasonable margin
            y = 50   # Small offset from top
            self.root.geometry(f"1400x{window_height}+{x}+{y}")

        # Create menu bar
        self.create_menu_bar()

        # Setup undo functionality
        self.setup_undo_functionality()

        # Create main container that fills window
        container = ctk.CTkFrame(self.root, corner_radius=0)
        container.pack(fill="both", expand=True)

        # Create scrollable frame
        self.scrollable_frame = ScrollableFrame(container)
        self.scrollable_frame.pack(fill="both", expand=True)

        # Get interior frame for content
        content_frame = self.scrollable_frame.interior

        # Set a darker background for better section contrast
        content_frame.configure(fg_color=("gray75", "#1A1A1A"))

        # Main container - removed expand=True to ensure bottom frame remains visible
        main_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_frame.pack(fill="x", expand=False, padx=12, pady=10)

        # Variables
        self.setup_variables()

        # Create GUI groups using simple compact design with improved visual separation
        self.create_simple_section(main_frame, self.create_group1_content, ("gray90", "gray25"))  # PDF Selection - lightest
        self.create_simple_section(main_frame, self.create_parent_content, ("gray88", "gray23"))  # Filename Editing - medium
        self.create_simple_section(main_frame, self.create_group3_content, ("gray86", "gray21"))  # Excel Integration (operations now integrated under Händelse)

        # Bottom frame for statistics and version
        bottom_frame = ctk.CTkFrame(content_frame)
        bottom_frame.pack(fill="x", padx=12, pady=(0, 8))

        # Statistics label (left side) - compact format
        self.filename_stats_label = ctk.CTkLabel(bottom_frame, text=self.get_stats_text(),
                                               font=ctk.CTkFont(size=11))
        self.filename_stats_label.pack(side="left")
        ToolTip(self.filename_stats_label, "Statistik över användning: Antal PDF:er öppnade, "
                                         "filer omdöpta och Excel-rader tillagda under denna session.")

        # Version label (right side) - smaller
        version_label = ctk.CTkLabel(bottom_frame, text=VERSION, font=ctk.CTkFont(size=11))
        version_label.pack(side="right")
        ToolTip(version_label, f"Programversion {VERSION}. DJs Timeline-maskin för PDF-filhantering och Excel-integration.")

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind window configuration events to prevent saving maximized geometry
        self.root.bind('<Configure>', self.on_window_configure)


    def setup_variables(self):
        """Setup tkinter variables"""
        self.pdf_path_var = tk.StringVar(value="Ingen PDF vald")
        self.date_var = tk.StringVar()
        self.newspaper_var = tk.StringVar()
        self.pages_var = tk.StringVar()
        self.comment_var = tk.StringVar()

        self.excel_enabled_var = tk.BooleanVar(value=True)
        self.excel_path_var = tk.StringVar(value="Ingen Excel-fil vald")
        self.excel_row_saved = tk.BooleanVar(value=True)

        # Excel column variables
        self.excel_vars = {}

        # Character counters for text fields (1000 char limit for all text fields)
        self.char_counters = {}
        self.char_limit = 1000
        self.handelse_char_limit = 1000

        # Undo/Redo functionality - track widgets that support undo
        self.undo_widgets = []  # List of widgets with undo enabled

        # Custom undo system for Entry widgets
        self.entry_undo_stacks = {}  # Dictionary to store undo history for each Entry widget
        self.entry_redo_stacks = {}  # Dictionary to store redo history for each Entry widget

        # Custom undo system for Text widgets (for problematic operations)
        self.text_undo_stacks = {}  # Dictionary to store undo history for each Text widget
        self.text_redo_stacks = {}  # Dictionary to store redo history for each Text widget

        self.max_undo_levels = 20  # Maximum number of undo levels

        # Internal clipboard for format preservation
        self.internal_clipboard = None  # Stores (text, tags) tuples

        # Lock switches will be initialized dynamically after field names are loaded
        self.lock_vars = {}

        # Output folder for renamed PDFs
        self.output_folder_var = tk.StringVar(value="")
        self.output_folder_lock_var = tk.BooleanVar(value=False)
        self._actual_output_folder = ""  # Store actual path while display shows friendly text

        # Text font size for text fields (Händelse, Note1-3) - load from config
        self.text_font_size = self.config.get('text_font_size', 9)

        # Row background color selection - DEFAULT: none (white)
        self.row_color_var = tk.StringVar(value="none")

        # Initialize button variables (will be created later)
        self.save_all_btn = None
        self.new_excel_row_btn = None

        # Bind change events to track filename changes
        for var in [self.date_var, self.newspaper_var, self.pages_var, self.comment_var]:
            var.trace('w', self.on_filename_change)


    def change_theme(self, theme_name: str):
        """Change the application theme"""
        try:
            # Apply the new theme to the root window
            self.root.style.theme_use(theme_name)

            # Reapply custom button styles after theme change
            self.configure_button_styles()

            # Save the theme preference to config
            self.config['theme'] = theme_name
            self.config_manager.save_config(self.config)

            # Recreate menu bar to update visual indicators
            self.create_menu_bar()

            logger.info(f"Theme changed to: {theme_name}")

        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte ändra tema: {str(e)}")
            logger.error(f"Error changing theme to {theme_name}: {e}")

    def show_program_help(self):
        """Open Manual.rtf with external application"""
        try:
            manual_path = Path(__file__).parent.parent / "docs" / "Manual.rtf"

            if not manual_path.exists():
                messagebox.showerror("Fel", f"Manualen hittades inte: {manual_path}")
                return

            # Open RTF file with default system application
            if platform.system() == 'Windows':
                os.startfile(str(manual_path))
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(manual_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(manual_path)])

            logger.info(f"Opened manual: {manual_path}")

        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna manualen: {str(e)}")
            logger.error(f"Error opening manual: {e}")

    def _load_custom_field_names(self):
        """Load custom field names and visibility from config into field manager"""
        try:
            from core.field_definitions import field_manager
            # Debug: Check field_manager state before loading
            logger.debug(f"DEBUG: field_manager custom names BEFORE loading: {field_manager.get_custom_names()}")

            # Load custom names
            custom_names = self.config_manager.load_custom_field_names()
            logger.info(f"DEBUG: Loaded custom field names from config: {custom_names}")

            field_manager.set_custom_names(custom_names)
            logger.info(f"DEBUG: field_manager custom names AFTER setting: {field_manager.get_custom_names()}")

            # Load field visibility
            hidden_fields = self.config_manager.load_field_visibility()
            logger.info(f"Loading field visibility: {len(hidden_fields)} hidden fields")
            field_manager.set_hidden_fields(hidden_fields)

            # Verify a few display names
            if custom_names:
                for field_id in ['obs', 'kategori', 'note1']:
                    if field_id in custom_names:
                        display_name = field_manager.get_display_name(field_id)
                        logger.debug(f"DEBUG: field_id '{field_id}' → display_name '{display_name}'")

        except Exception as e:
            logger.error(f"Failed to load custom field names: {e}")

    def _initialize_lock_vars(self):
        """Initialize lock variables with current field display names"""
        try:
            from core.field_definitions import FIELD_DEFINITIONS, field_manager

            # Debug: Check field_manager state before initialization
            logger.debug(f"DEBUG: field_manager custom names at lock_vars init: {field_manager.get_custom_names()}")

            # Clear existing lock_vars
            old_keys = list(self.lock_vars.keys())
            self.lock_vars.clear()
            logger.debug(f"DEBUG: Cleared old lock_vars keys: {old_keys}")

            # Create lock variables for all lockable fields (all except 'dag' and 'inlagd')
            field_mappings = []
            for field_id, _field_def in FIELD_DEFINITIONS.items():
                # Skip fields that shouldn't have locks
                if field_id in ['dag', 'inlagd']:
                    continue

                # Get the current display name (could be custom or default)
                display_name = field_manager.get_display_name(field_id)
                field_mappings.append(f"{field_id} → {display_name}")

                # Create lock variable with display name as key
                self.lock_vars[display_name] = tk.BooleanVar()

            logger.info(f"DEBUG: Field ID mappings: {field_mappings}")
            logger.info(f"DEBUG: Initialized lock_vars with keys: {list(self.lock_vars.keys())}")
        except Exception as e:
            logger.error(f"Failed to initialize lock_vars: {e}")

    def _show_field_config_dialog(self):
        """Show the field configuration dialog"""
        try:
            from gui.field_config_dialog import show_field_config_dialog
            show_field_config_dialog(self.root, self._on_field_config_applied)
        except Exception as e:
            logger.error(f"Failed to show field config dialog: {e}")
            messagebox.showerror("Fel", f"Kunde inte öppna fältkonfiguration: {str(e)}")

    def _on_field_config_applied(self):
        """Called when field configuration changes are applied"""
        try:
            from core.field_definitions import field_manager
            logger.info("Field configuration applied - performing selective reset (preserving config)")
            logger.debug(f"DEBUG: field_manager state at START of apply: {field_manager.get_custom_names()}")

            # Show progress/info message
            messagebox.showinfo(
                "Tillämpar ändringar",
                "Fältnamn uppdateras...\nAlla data raderas och programmet ritas om."
            )

            # Step 1: Clear all field data
            self._clear_all_field_data()
            logger.debug(f"DEBUG: field_manager state after clear_all_field_data: {field_manager.get_custom_names()}")

            # Step 2: Reload configuration with saved field names and visibility (do not delete config)
            self.config = self.config_manager.load_config()
            logger.debug("DEBUG: Config reloaded, now calling _load_custom_field_names()")
            self._load_custom_field_names()  # This now loads both names and visibility
            logger.debug(f"DEBUG: field_manager state after _load_custom_field_names: {field_manager.get_custom_names()}")

            # Step 3: Reinitialize lock_vars with new field names
            self._initialize_lock_vars()

            # Step 4: Recreate Excel fields with new names
            self.excel_field_manager.create_excel_fields()

            # Step 5: Reset other UI components
            self._reset_ui_state()

            logger.info("Field configuration applied successfully")
            messagebox.showinfo("Klart", "Fältnamn har uppdaterats!\nAlla data har raderats och programmet har ritats om.")

        except Exception as e:
            logger.error(f"Failed to apply field configuration: {e}")
            messagebox.showerror("Fel", f"Kunde inte tillämpa fältkonfiguration: {str(e)}")

    def _clear_all_field_data(self):
        """Clear all field data (including locked fields)"""
        try:
            # Clear all excel_vars
            for var in self.excel_vars.values():
                if hasattr(var, 'set'):
                    var.set("")
                elif hasattr(var, 'clear'):
                    var.clear()

            # Clear PDF fields
            self.date_var.set("")
            self.newspaper_var.set("")
            self.comment_var.set("")
            self.pages_var.set("")

            # Reset output folder
            self.output_folder_var.set("")
            self._actual_output_folder = ""

            # Clear current PDF
            self.current_pdf_path = ""
            self.current_pdf_pages = 0

            # Reset row color
            self.row_color_var.set("none")

            logger.info("All field data cleared")

        except Exception as e:
            logger.error(f"Failed to clear field data: {e}")

    def _reset_ui_state(self):
        """Reset UI state to defaults"""
        try:
            # Reset font size to default
            self.text_font_size = 9
            self.apply_text_font_size(9)

            # Reset statistics
            self.stats = {
                'pdfs_opened': 0,
                'files_renamed': 0,
                'excel_rows_added': 0
            }

            # Update UI elements
            self.update_stats_display()
            self.update_filename_preview()

            logger.info("UI state reset to defaults")

        except Exception as e:
            logger.error(f"Failed to reset UI state: {e}")

    def run(self):
        """Start the application"""
        self.root.mainloop()
