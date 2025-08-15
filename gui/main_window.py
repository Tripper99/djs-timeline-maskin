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
        self.excel_field_manager = ExcelFieldManager(self)

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

        # Setup GUI
        self.setup_gui()
        self.load_saved_excel_file()  # Load previously selected Excel file
        self.load_saved_output_folder()  # Load previously selected output folder

        # Load and restore locked fields after GUI is created
        self.excel_field_manager.restore_locked_fields()

        # Apply saved font size to text fields
        saved_font_size = self.config.get('text_font_size', 9)
        self.apply_text_font_size(saved_font_size)

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
        self.root.geometry("1800x1000")  # Initial size before responsive calculation

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

        # Get actual available screen area (excludes taskbar)
        try:
            # Try to get the actual working area height
            work_area_height = self.root.winfo_vrootheight()
            if work_area_height > 0:
                available_height = work_area_height
            else:
                available_height = screen_height - 80  # Fallback: assume larger taskbar
        except Exception:
            available_height = screen_height - 80  # Fallback

        window_height = min(max(int(available_height * 0.75), 700), 800)  # Much more aggressive height reduction for laptops
        logger.info(f"Screen: {screen_width}x{screen_height}, work area: {available_height}, calculated window height: {window_height}")

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
                    x = (screen_width // 2) - (1800 // 2)
                    y = 0
                    self.root.geometry(f"1800x{window_height}+{x}+{y}")
            except Exception as e:
                logger.warning(f"Error parsing saved geometry {saved_geometry}: {e}")
                # Fallback to calculated geometry
                x = (screen_width // 2) - (1800 // 2)
                y = 0
                self.root.geometry(f"1800x{window_height}+{x}+{y}")
        else:
            # No saved geometry, use calculated
            x = (screen_width // 2) - (1800 // 2)
            y = 0
            self.root.geometry(f"1800x{window_height}+{x}+{y}")

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

        # Lock switches for ALL fields except Dag and Inlagd (which is read-only)
        self.lock_vars = {
            'OBS': tk.BooleanVar(),
            'Kategori': tk.BooleanVar(),
            'Underkategori': tk.BooleanVar(),
            'Person/sak': tk.BooleanVar(),
            'Special': tk.BooleanVar(),
            'Händelse': tk.BooleanVar(),
            'Startdatum': tk.BooleanVar(),
            'Starttid': tk.BooleanVar(),
            'Slutdatum': tk.BooleanVar(),
            'Sluttid': tk.BooleanVar(),
            'Note1': tk.BooleanVar(),
            'Note2': tk.BooleanVar(),
            'Note3': tk.BooleanVar(),
            'Källa1': tk.BooleanVar(),
            'Källa2': tk.BooleanVar(),
            'Källa3': tk.BooleanVar(),
            'Övrigt': tk.BooleanVar()  # Updated from "Korrelerande historisk händelse"
        }

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
            manual_path = Path(__file__).parent.parent / "Manual.rtf"

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

    def run(self):
        """Start the application"""
        self.root.mainloop()
