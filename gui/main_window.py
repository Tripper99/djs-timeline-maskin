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
from datetime import datetime
from pathlib import Path

# GUI imports
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox

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
from core.filename_parser import FilenameParser
from core.pdf_processor import PDFProcessor
from gui.dialogs import DialogManager
from gui.excel_fields import ExcelFieldManager
from gui.utils import ScrollableFrame, ToolTip
from utils.constants import VERSION

# Setup logging
logger = logging.getLogger(__name__)

class PDFProcessorApp:
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

        # Set a subtle background color for better card contrast (commented out for testing)
        # content_frame.configure(fg_color=("#F5F5F5", "#1A1A1A"))

        # Main container - removed expand=True to ensure bottom frame remains visible
        main_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_frame.pack(fill="x", expand=False, padx=20, pady=20)

        # Variables
        self.setup_variables()

        # Create GUI groups using card-based design
        self.create_card_section(main_frame, "1. PDF-fil", self.create_group1_content)  # PDF Selection
        self.create_card_section(main_frame, "2. Filnamn komponenter", self.create_parent_content)  # Filename Editing
        self.create_card_section(main_frame, "3. Excel-integration", self.create_group3_content)  # Excel Integration
        self.create_card_section(main_frame, "4. Operationer", self.create_group4_content)  # Excel Operations Buttons

        # Bottom frame for statistics and version
        bottom_frame = ctk.CTkFrame(content_frame)
        bottom_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Statistics label (left side)
        self.filename_stats_label = ctk.CTkLabel(bottom_frame, text=self.get_stats_text(),
                                               font=ctk.CTkFont(size=14))
        self.filename_stats_label.pack(side="left")
        ToolTip(self.filename_stats_label, "Statistik över användning: Antal PDF:er öppnade, "
                                         "filer omdöpta och Excel-rader tillagda under denna session.")

        # Version label (right side)
        version_label = ctk.CTkLabel(bottom_frame, text=VERSION, font=ctk.CTkFont(size=14))
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

    def create_menu_bar(self):
        """Create menu bar with Help and Theme menus"""
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=help_menu)
        help_menu.add_command(label="Om programmet", command=self.show_program_help)
        help_menu.add_separator()
        help_menu.add_command(label="Excel-fil krav", command=self.dialog_manager.show_excel_help)

        # Theme menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tema", menu=theme_menu)

        # Light themes submenu
        light_themes_menu = tk.Menu(theme_menu, tearoff=0)
        theme_menu.add_cascade(label="Ljusa teman", menu=light_themes_menu)

        # Dark themes submenu
        dark_themes_menu = tk.Menu(theme_menu, tearoff=0)
        theme_menu.add_cascade(label="Mörka teman", menu=dark_themes_menu)

        # Define light and dark themes (verified ttkbootstrap themes)
        light_themes = [
            "cosmo", "flatly", "journal", "litera", "lumen",
            "minty", "pulse", "sandstone", "united", "yeti", "morph", "simplex",
            "cerculean"
        ]

        dark_themes = [
            "solar", "superhero", "darkly", "cyborg", "vapor"
        ]

        # Add light theme options to submenu
        current_theme = self.config.get('theme', 'simplex')
        for theme in sorted(light_themes):
            # Use bold font for current theme
            if theme == current_theme:
                light_themes_menu.add_command(
                    label=f"● {theme.capitalize()}",
                    command=lambda t=theme: self.change_theme(t),
                    font=('TkDefaultFont', 0, 'bold')
                )
            else:
                light_themes_menu.add_command(
                    label=f"  {theme.capitalize()}",
                    command=lambda t=theme: self.change_theme(t)
                )

        # Add dark theme options to submenu
        for theme in sorted(dark_themes):
            # Use bold font for current theme
            if theme == current_theme:
                dark_themes_menu.add_command(
                    label=f"● {theme.capitalize()}",
                    command=lambda t=theme: self.change_theme(t),
                    font=('TkDefaultFont', 0, 'bold')
                )
            else:
                dark_themes_menu.add_command(
                    label=f"  {theme.capitalize()}",
                    command=lambda t=theme: self.change_theme(t)
                )

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

    def create_card_section(self, parent, title, content_func):
        """Create a professional card-style section with shadow effect"""
        # Outer shadow frame (creates depth effect)
        shadow_frame = ctk.CTkFrame(parent,
                                   fg_color=("#E8E8E8", "#2B2B2B"),  # Light shadow color
                                   corner_radius=12)
        shadow_frame.pack(fill="x", pady=(0, 20), padx=2)

        # Main card frame (offset for shadow effect)
        card_frame = ctk.CTkFrame(shadow_frame,
                                 fg_color=("#FFFFFF", "#1E1E1E"),  # Clean white/dark background
                                 corner_radius=10,
                                 border_width=1,
                                 border_color=("#D0D0D0", "#404040"))
        card_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Header section with modern typography
        header_frame = ctk.CTkFrame(card_frame,
                                   fg_color=("#F8F9FA", "#2A2A2A"),
                                   corner_radius=8)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        title_label = ctk.CTkLabel(header_frame,
                                  text=title,
                                  font=ctk.CTkFont(size=18, weight="bold"),
                                  text_color=("#1A1A1A", "#FFFFFF"))
        title_label.pack(anchor="w", padx=15, pady=12)

        # Content area
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Call the content creation function
        content_func(content_frame)

    def create_modern_entry(self, parent, label_text, width=200):
        """Create a modern input field with depth"""
        container = ctk.CTkFrame(parent, fg_color="transparent")

        # Label with better typography
        label = ctk.CTkLabel(container,
                           text=label_text,
                           font=ctk.CTkFont(size=12, weight="normal"),
                           text_color=("#4A4A4A", "#B0B0B0"))
        label.pack(anchor="w", pady=(0, 4))

        # Entry with enhanced appearance
        entry = ctk.CTkEntry(container,
                           width=width,
                           height=35,
                           font=ctk.CTkFont(size=12),
                           corner_radius=8,
                           border_width=2,
                           border_color=("#E0E0E0", "#404040"),
                           fg_color=("#FFFFFF", "#2B2B2B"))
        entry.pack(anchor="w")

        return container, entry

    def create_modern_button(self, parent, text, color="#1976D2", width=150):
        """Create a modern button with enhanced styling"""
        return ctk.CTkButton(parent,
                           text=text,
                           width=width,
                           height=40,
                           font=ctk.CTkFont(size=12, weight="bold"),
                           fg_color=color,
                           corner_radius=10,
                           border_width=0)

    def create_group1_content(self, parent):
        """Group 1 Content: PDF Selection"""

        # First row: PDF path display
        pdf_path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        pdf_path_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(pdf_path_frame, text="Vald fil:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
        pdf_path_entry = ctk.CTkEntry(pdf_path_frame, textvariable=self.pdf_path_var,
                                 state="readonly", font=ctk.CTkFont(size=12), width=300)
        pdf_path_entry.pack(side="left", padx=(10, 10))
        ToolTip(pdf_path_entry, "Visar namn på den valda PDF-filen. Filen öppnas automatiskt när den väljs.")

        # Select PDF button
        select_pdf_btn = ctk.CTkButton(pdf_path_frame, text="Välj PDF",
                                  command=self.select_pdf_file, )
        select_pdf_btn.pack(side="left", padx=(0, 20))
        ToolTip(select_pdf_btn, "Välj en PDF-fil för bearbetning. Filen öppnas automatiskt för granskning, "
                               "filnamnet parsas till komponenter och sidantalet räknas automatiskt.")

        # Output folder selection (same row)
        ctk.CTkLabel(pdf_path_frame, text="Mapp för omdöpt pdf:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
        self.output_folder_entry = ctk.CTkEntry(pdf_path_frame, textvariable=self.output_folder_var,
                                           state="readonly", font=ctk.CTkFont(size=12), width=250)
        self.output_folder_entry.pack(side="left", padx=(10, 10))
        ToolTip(self.output_folder_entry, "Visar mappen där omdöpta PDF-filer ska sparas. "
                                         "Fylls automatiskt med PDF-filens mapp om inte låst.")

        # Select output folder button
        self.select_output_folder_btn = ctk.CTkButton(pdf_path_frame, text="Välj mapp",
                                                 command=self.select_output_folder, )
        self.select_output_folder_btn.pack(side="left", padx=(0, 10))
        ToolTip(self.select_output_folder_btn, "Välj en mapp för omdöpta PDF-filer.")

        # Lock switch for output folder
        self.output_folder_lock_switch = ctk.CTkCheckBox(pdf_path_frame, text="Lås",
                                                       variable=self.output_folder_lock_var,
                                                       command=self.on_output_folder_lock_change)
        self.output_folder_lock_switch.pack(side="left", padx=(5, 0))
        ToolTip(self.output_folder_lock_switch, "När låst: mappvalet ändras inte när ny PDF väljs. "
                                               "När olåst: mappvalet uppdateras automatiskt till PDF-filens mapp.")

        # Open folder button (between lock and reset)
        self.open_folder_btn = ctk.CTkButton(pdf_path_frame, text="Öppna mapp",
                                        command=self.open_output_folder, fg_color="#28a745", width=12)
        self.open_folder_btn.pack(side="left", padx=(10, 0))
        ToolTip(self.open_folder_btn, "Öppna den valda mappen i filutforskaren.")

        # Reset button (same row)
        self.reset_folder_btn = ctk.CTkButton(pdf_path_frame, text="Nollställ mapp",
                                         command=self.reset_output_folder, fg_color="#17a2b8", width=15)
        self.reset_folder_btn.pack(side="left", padx=(10, 0))
        ToolTip(self.reset_folder_btn, "Rensa mappvalet och låser upp automatisk uppdatering.")

    def create_parent_content(self, parent):
        """Group 2 Content: Filename Editing"""

        # Create grid for filename components
        components_frame = ctk.CTkFrame(parent, fg_color="transparent")
        components_frame.pack(fill="x")

        # Date
        ctk.CTkLabel(components_frame, text="Datum:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        date_entry = ctk.CTkEntry(components_frame, textvariable=self.date_var, width=120, font=ctk.CTkFont(size=12))
        date_entry.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=(0, 5))
        self.enable_undo_for_widget(date_entry)

        # Newspaper
        ctk.CTkLabel(components_frame, text="Tidning:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, sticky="w", padx=(0, 10), pady=(0, 5))
        newspaper_entry = ctk.CTkEntry(components_frame, textvariable=self.newspaper_var, width=150, font=ctk.CTkFont(size=12))
        newspaper_entry.grid(row=0, column=3, sticky="w", padx=(0, 20), pady=(0, 5))
        self.enable_undo_for_widget(newspaper_entry)

        # Pages
        ctk.CTkLabel(components_frame, text="Sidor:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=4, sticky="w", padx=(0, 10), pady=(0, 5))
        pages_entry = ctk.CTkEntry(components_frame, textvariable=self.pages_var, width=60, font=ctk.CTkFont(size=12))
        pages_entry.grid(row=0, column=5, sticky="w", padx=(0, 20), pady=(0, 5))
        self.enable_undo_for_widget(pages_entry)

        # Comment
        ctk.CTkLabel(components_frame, text="Kommentar:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=6, sticky="w", padx=(0, 10), pady=(0, 5))
        comment_entry = ctk.CTkEntry(components_frame, textvariable=self.comment_var, width=300, font=ctk.CTkFont(size=12))
        comment_entry.grid(row=0, column=7, sticky="w", padx=(0, 20), pady=(0, 5))
        self.enable_undo_for_widget(comment_entry)

        # Copy to Excel button (moved to same row, made 25% smaller)
        self.copy_to_excel_btn = ctk.CTkButton(components_frame, text="Kopiera filnamn till Excel-fältet",
                                         command=self.copy_filename_to_excel,
                                         fg_color="#17a2b8", width=26)
        self.copy_to_excel_btn.grid(row=0, column=8, sticky="w", padx=(10, 0), pady=(0, 5))

    def create_group3_content(self, parent):
        """Group 3 Content: Excel Integration"""

        # Excel file selection
        excel_file_frame = ctk.CTkFrame(parent, fg_color="transparent")
        excel_file_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(excel_file_frame, text="Excel-fil:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
        excel_path_entry = ctk.CTkEntry(excel_file_frame, textvariable=self.excel_path_var,
                                   state="readonly", font=ctk.CTkFont(size=12), width=400)
        excel_path_entry.pack(side="left", padx=(10, 10))
        ToolTip(excel_path_entry, "Visar namn på den valda Excel-filen. Programmet kommer ihåg senast använda fil.")

        # Button frame for Excel file selection and help
        excel_btn_frame = ctk.CTkFrame(excel_file_frame, fg_color="transparent")
        excel_btn_frame.pack(side="left")

        self.select_excel_btn = ctk.CTkButton(excel_btn_frame, text="Välj Excel",
                                         command=self.select_excel_file,
                                         fg_color="#17a2b8")
        self.select_excel_btn.pack(side="left", padx=(0, 5))
        ToolTip(self.select_excel_btn, "Välj Excel-fil (.xlsx) för dataintegrering. "
                                      "Du får möjlighet att skapa en säkerhetskopia att arbeta med.")

        # Open Excel button
        self.open_excel_btn = ctk.CTkButton(excel_btn_frame, text="Öppna Excel",
                                       command=self.open_excel_file,
                                       fg_color="#28a745", state="disabled")
        self.open_excel_btn.pack(side="left", padx=(0, 5))
        ToolTip(self.open_excel_btn, "Öppna den valda Excel-filen i externt program. "
                                    "Blir tillgänglig när en Excel-fil har valts.")

        # Help button (question mark)
        help_btn = ctk.CTkButton(excel_btn_frame, text="?",
                           command=self.dialog_manager.show_excel_help,
                           width=30)
        help_btn.pack(side="left")

        # Excel column fields (scrollable, three-column layout)
        self.excel_fields_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.excel_fields_frame.pack(fill="both", expand=False, pady=(5, 0))  # Reduced padding to save vertical space

        # Configure the excel_fields_frame for responsive layout
        self.excel_fields_frame.grid_columnconfigure(0, weight=1)

        self.excel_field_manager.create_excel_fields()

        # Apply saved font size to text fields after they're created
        saved_font_size = self.config.get('text_font_size', 9)
        self.apply_text_font_size(saved_font_size)

    def create_group4_content(self, parent):
        """Group 4 Content: Excel Operations Buttons"""

        # First row: Buttons for Excel operations
        excel_buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        excel_buttons_frame.pack(fill="x", pady=(0, 10))

        self.save_all_btn = ctk.CTkButton(excel_buttons_frame, text="Spara allt och rensa fälten",
                                     command=self.save_all_and_clear,
                                     fg_color="#28a745", width=30)
        self.save_all_btn.pack(side="left", padx=(0, 10))

        self.new_excel_row_btn = ctk.CTkButton(excel_buttons_frame, text="Rensa allt utan att spara",
                                          command=self.clear_all_without_saving,
                                          fg_color="#17a2b8", width=30)
        self.new_excel_row_btn.pack(side="left", padx=(0, 20))


        # Second row: Row color selection
        color_frame = ctk.CTkFrame(parent, fg_color="transparent")
        color_frame.pack(fill="x", pady=(5, 0))

        # Label for color selection
        color_label = ctk.CTkLabel(color_frame, text="Nya excelradens bakgrundsfärg:", font=ctk.CTkFont(size=10, weight="bold"))
        color_label.pack(side="left", padx=(0, 15))

        # Colored button options for row background
        color_options = [
            ("none", "Ingen", "#FFFFFF"),
            ("yellow", "Gul", "#FFF59D"),    # Light yellow
            ("green", "Grön", "#C8E6C9"),    # Light green
            ("blue", "Blå", "#BBDEFB"),      # Light blue
            ("red", "Röd", "#FFCDD2"),       # Light red
            ("pink", "Rosa", "#F8BBD9"),     # Light pink
            ("gray", "Grå", "#E0E0E0")       # Light grey
        ]

        # Store button references for selection state management
        self.color_buttons = {}

        for value, text, color in color_options:
            # Create colored button with selection state
            current_selection = self.row_color_var.get() if hasattr(self, 'row_color_var') else "none"
            is_selected = current_selection == value

            button = ctk.CTkButton(
                color_frame,
                text=text,
                width=60,
                height=30,  # Slightly taller for better proportions
                font=ctk.CTkFont(size=11),
                fg_color=color if value != "none" else "#FFFFFF",
                hover_color=self._get_hover_color(color),
                text_color="#333333" if value != "none" else "#666666",  # Better contrast
                border_color="#666666",
                border_width=3 if is_selected else 1,
                command=lambda v=value: self._select_row_color(v)
            )
            button.pack(side="left", padx=(0, 10))  # Slightly more spacing
            self.color_buttons[value] = button

    def _get_hover_color(self, base_color):
        """Generate a slightly darker hover color for buttons"""
        if base_color == "#FFFFFF":
            return "#F0F0F0"
        # Simple darkening by reducing each RGB component
        try:
            # Convert hex to RGB
            r = int(base_color[1:3], 16)
            g = int(base_color[3:5], 16)
            b = int(base_color[5:7], 16)
            # Darken by 20
            r = max(0, r - 20)
            g = max(0, g - 20)
            b = max(0, b - 20)
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return base_color

    def _select_row_color(self, selected_value):
        """Handle color button selection and update visual state"""
        # Update the variable
        self.row_color_var.set(selected_value)

        # Update button border widths to show selection
        for value, button in self.color_buttons.items():
            if value == selected_value:
                button.configure(border_width=3)  # Selected state
            else:
                button.configure(border_width=1)  # Normal state

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

    def select_pdf_file(self):
        """Select PDF file for processing"""
        initial_dir = self.config.get('last_pdf_dir', str(Path.home()))

        file_path = filedialog.askopenfilename(
            title="Välj PDF-fil",
            filetypes=[("PDF-filer", "*.pdf"), ("Alla filer", "*.*")],
            initialdir=initial_dir
        )

        if file_path:
            # Validate PDF file before proceeding
            is_valid, error_msg = PDFProcessor.validate_pdf_file(file_path)
            if not is_valid:
                messagebox.showerror("Ogiltig PDF-fil", f"Kan inte använda vald fil:\n{error_msg}")
                return

            self.current_pdf_path = file_path
            self.pdf_path_var.set(Path(file_path).name)

            # Update last directory
            self.config['last_pdf_dir'] = str(Path(file_path).parent)

            # Get page count with error handling
            try:
                self.current_pdf_pages = PDFProcessor.get_pdf_page_count(file_path)
            except ValueError as e:
                messagebox.showerror("PDF-fel", str(e))
                # Reset PDF selection
                self.current_pdf_path = ""
                self.pdf_path_var.set("Ingen PDF vald")
                return

            # Parse filename and store original components
            filename = Path(file_path).name
            components = FilenameParser.parse_filename(filename)
            self.original_filename_components = components.copy()

            # Update GUI fields
            self.date_var.set(components['date'])
            self.newspaper_var.set(components['newspaper'])
            self.comment_var.set(components['comment'])

            # Use actual page count if not in filename
            if components['pages']:
                self.pages_var.set(components['pages'])
            else:
                self.pages_var.set(str(self.current_pdf_pages))

            # Open PDF externally
            try:
                PDFProcessor.open_pdf_externally(file_path)
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte öppna PDF-fil: {str(e)}")

            # Auto-fill output folder if not locked (always when unlocked)
            if not self.output_folder_lock_var.get():
                pdf_folder = str(Path(file_path).parent)
                self._actual_output_folder = pdf_folder
                display_text = self.get_display_folder_text(pdf_folder)
                self.output_folder_var.set(display_text)
                logger.info(f"Auto-filled output folder: {pdf_folder}")

            # Update statistics
            self.stats['pdfs_opened'] += 1
            self.update_stats_display()

            logger.info(f"Loaded PDF: {filename}, Pages: {self.current_pdf_pages}")

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

    def rename_current_pdf(self) -> bool:
        """Rename the current PDF file if filename has changed"""
        if not self.current_pdf_path:
            return False

        if not self.has_filename_changed():
            return False  # No changes to save

        # Validate that PDF file still exists
        is_valid, error_msg = PDFProcessor.validate_pdf_file(self.current_pdf_path)
        if not is_valid:
            messagebox.showerror("PDF-fil saknas",
                               f"PDF-filen kunde inte hittas eller läsas:\n{error_msg}\n\n" +
                               "Filen kan ha flyttats, tagits bort eller skadats.")
            return False

        # Check if file is locked by another application - with retry loop
        while PDFProcessor.is_file_locked(self.current_pdf_path):
            choice = self.show_retry_cancel_dialog(
                "Fil låst",
                "PDF-filen används av ett annat program. " +
                "Stäng programmet och försök igen."
            )
            if choice == 'cancel':
                return False
            # If choice == 'retry', loop continues to check again

        # Construct new filename
        new_filename = FilenameParser.construct_filename(
            self.date_var.get(),
            self.newspaper_var.get(),
            self.comment_var.get(),
            self.pages_var.get()
        )

        # Validate filename
        is_valid, error_msg = FilenameParser.validate_filename(new_filename)
        if not is_valid:
            messagebox.showerror("Ogiltigt filnamn", f"Filnamnet är ogiltigt: {error_msg}")
            return False

        old_file = Path(self.current_pdf_path)

        # Determine target directory based on output folder setting
        output_folder = getattr(self, '_actual_output_folder', '') or self.output_folder_var.get()
        if output_folder and Path(output_folder).exists():
            target_dir = Path(output_folder)
        else:
            # Default to same directory as original file
            target_dir = old_file.parent

        # Check target directory permissions
        can_write, perm_error = PDFProcessor.check_directory_permissions(str(target_dir))
        if not can_write:
            messagebox.showerror("Fel", f"Kan inte skriva till mappen '{target_dir}': {perm_error}")
            return False

        new_path = target_dir / new_filename

        # Check if target file already exists
        if new_path.exists() and str(new_path) != str(old_file):
            # Check if target file is locked - with retry loop
            while PDFProcessor.is_file_locked(str(new_path)):
                choice = self.show_retry_cancel_dialog(
                    "Målfil låst",
                    f"Målfilen '{new_filename}' är låst av ett annat program. " +
                    "Stäng programmet och försök igen."
                )
                if choice == 'cancel':
                    return False
                # If choice == 'retry', loop continues to check again

            result = messagebox.askyesno("Filen finns redan",
                                       f"Filen '{new_filename}' finns redan. Vill du skriva över den?")
            if not result:
                return False
        # Attempt to rename/move
        try:
            if str(target_dir) != str(old_file.parent):
                # Move to different directory
                old_file.replace(new_path)  # replace() overwrites if target exists
                logger.info(f"Moved and renamed: {old_file.name} -> {target_dir.name}/{new_filename}")
            else:
                # Just rename in same directory
                old_file.rename(new_path)
                logger.info(f"Renamed: {old_file.name} -> {new_filename}")

            # Update internal state
            self.current_pdf_path = str(new_path)
            self.pdf_path_var.set(new_filename)
            self.original_filename_components = {
                'date': self.date_var.get(),
                'newspaper': self.newspaper_var.get(),
                'comment': self.comment_var.get(),
                'pages': self.pages_var.get()
            }

            self.stats['files_renamed'] += 1
            self.update_stats_display()

            return True

        except PermissionError:
            messagebox.showerror("Fel", "Åtkomst nekad. Kontrollera att du har behörighet att ändra filer i mappen.")
            return False
        except FileExistsError:
            messagebox.showerror("Fel", f"Filen '{new_filename}' finns redan och kunde inte skrivas över.")
            return False
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte byta namn på filen: {str(e)}")
            return False

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


    def clear_pdf_and_filename_fields(self):
        """Clear PDF selection and filename components"""
        self.current_pdf_path = ""
        self.current_pdf_pages = 0
        self.original_filename_components = {}
        self.pdf_path_var.set("Ingen PDF vald")
        self.date_var.set("")
        self.newspaper_var.set("")
        self.comment_var.set("")
        self.pages_var.set("")

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

    def check_character_count(self, event, column_name):
        """Check character count in text fields and update counter with color coding"""
        text_widget = event.widget
        content = text_widget.get("1.0", tk.END)
        # Remove the trailing newline that tk.Text always adds
        if content.endswith('\n'):
            content = content[:-1]

        char_count = len(content)
        limit = self.handelse_char_limit if column_name == 'Händelse' else self.char_limit
        remaining = limit - char_count

        # Update counter display
        if column_name in self.char_counters:
            counter_label = self.char_counters[column_name]

            # Color coding based on remaining characters
            counter_label.configure(text=f"Tecken kvar: {remaining}")

        # Hard limit enforcement
        if char_count > limit:
            # Truncate to exact limit
            truncated_content = content[:limit]
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", truncated_content)

            # Update counter to show 0
            if column_name in self.char_counters:
                self.char_counters[column_name].configure(text="Tecken kvar: 0")

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

    def verify_insertion(self, widget, field_name, expected_chunk):
        """Verify that the inserted text hasn't been corrupted by other events"""
        try:
            actual_content = widget.get("1.0", tk.END).strip()

            if actual_content != expected_chunk:
                logger.warning(f"TEXT CORRUPTION DETECTED in {field_name}!")
                logger.warning(f"Expected length: {len(expected_chunk)}, Actual length: {len(actual_content)}")
                logger.warning(f"Expected ends with: '{expected_chunk[-20:]}'")
                logger.warning(f"Actual ends with: '{actual_content[-20:]}'")

                # Fix the corruption by re-inserting the correct text
                widget.delete("1.0", tk.END)
                widget.insert("1.0", expected_chunk)
                logger.info(f"Fixed corruption in {field_name} by re-inserting correct text")
            else:
                logger.info(f"Verification OK for {field_name}: content matches expected")
        except Exception as e:
            logger.error(f"Error during verification of {field_name}: {e}")

    def handle_text_key_press_undo(self, event):
        """Handle key press in Text widget - create undo separator for character-by-character undo"""
        try:
            text_widget = event.widget
            if not isinstance(text_widget, tk.Text):
                return None

            # Skip control/modifier key combinations except for Tab
            if event.state & 0x4 and event.keysym != 'Tab':  # Control key pressed
                return None

            # Check if there's selected text that will be replaced
            has_selection = bool(text_widget.tag_ranges(tk.SEL))

            # Add separator for ANY character input or deletion
            if (len(event.char) == 1 and event.char.isprintable()) or event.keysym in ['Delete', 'BackSpace', 'Return', 'KP_Enter', 'Tab']:
                text_widget.edit_separator()

                # Log only for selections to reduce noise
                if has_selection:
                    logger.debug(f"Added undo separator before '{event.keysym}' over selection")

            # Allow the default key handling to proceed
            return None
        except (tk.TclError, AttributeError):
            # Error accessing selection or widget - let default handling proceed
            return None

    def handle_select_all_undo(self, event):
        """Handle Ctrl+A - prepare for potential undo separator if next operation modifies content"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # Mark that we just did a select all - next destructive operation should add separator
                focused_widget._select_all_pending = True
                logger.debug("Marked select-all pending for undo tracking")
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default select-all to proceed

    def handle_paste_undo(self, text_widget):
        """Handle Ctrl+V - paste with format preservation if available
        Now called directly on specific text widgets rather than globally"""
        logger.info("Direct paste handler executed")
        try:
            if isinstance(text_widget, tk.Text):
                # Add edit separator before paste
                text_widget.edit_separator()

                # Check if we have formatted content in internal clipboard
                if self.internal_clipboard:
                    text, tags_data = self.internal_clipboard

                    # Get cursor position or selection
                    try:
                        # Delete selection if exists
                        if text_widget.tag_ranges(tk.SEL):
                            text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                        insert_pos = text_widget.index(tk.INSERT)
                    except tk.TclError:
                        insert_pos = text_widget.index(tk.INSERT)

                    # Insert text
                    text_widget.insert(insert_pos, text)

                    # Apply formatting tags
                    for tag, rel_start, rel_end in tags_data:
                        tag_start = f"{insert_pos} + {rel_start}c"
                        tag_end = f"{insert_pos} + {rel_end}c"
                        text_widget.tag_add(tag, tag_start, tag_end)

                    # Add edit separator after paste
                    text_widget.edit_separator()

                    # Clear internal clipboard after use (single use)
                    self.internal_clipboard = None

                    # Trigger character count check after formatted paste
                    self.root.after_idle(lambda: self.check_character_count_for_widget(text_widget))

                    return "break"  # Prevent default paste
                else:
                    # No formatted content - perform regular paste with undo tracking
                    try:
                        # Get clipboard content
                        clipboard_content = self.root.clipboard_get()

                        # Check if there's selected text that will be replaced
                        has_selection = bool(text_widget.tag_ranges(tk.SEL))

                        # Or if we just did a select-all
                        select_all_pending = getattr(text_widget, '_select_all_pending', False)

                        if has_selection or select_all_pending:
                            # Save current content to our custom undo stack before replacing
                            current_content = text_widget.get("1.0", "end-1c")
                            self.save_text_undo_state(text_widget, current_content)

                            logger.info("Saved undo state before paste operation")

                        # Clear the select-all pending flag
                        if hasattr(text_widget, '_select_all_pending'):
                            delattr(text_widget, '_select_all_pending')

                        # Actually perform the paste operation
                        if has_selection:
                            # Delete selected text first
                            text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)

                        # Insert clipboard content at cursor position
                        insert_pos = text_widget.index(tk.INSERT)
                        text_widget.insert(insert_pos, clipboard_content)

                        # Schedule saving the post-paste content to our undo stack
                        self.root.after_idle(self.save_post_paste_state, text_widget)

                        # Add edit separator after paste
                        self.root.after_idle(lambda: text_widget.edit_separator())

                        # Trigger character count check after regular paste
                        self.root.after_idle(lambda: self.check_character_count_for_widget(text_widget))

                    except tk.TclError:
                        # No clipboard content or clipboard access failed
                        logger.debug("No clipboard content available for paste")

                # ALWAYS return "break" for Text widgets to prevent default paste
                return "break"
        except (tk.TclError, AttributeError) as e:
            logger.error(f"Error in paste handler: {e}")
        return "break"  # Always prevent default for direct widget calls

    def save_post_paste_state(self, text_widget):
        """Save the state after a paste operation completes"""
        try:
            if isinstance(text_widget, tk.Text):
                # Get the content after paste operation
                post_paste_content = text_widget.get("1.0", "end-1c")
                self.save_text_undo_state(text_widget, post_paste_content)
                logger.info("Saved post-paste content to undo stack")
        except (tk.TclError, AttributeError):
            pass

    def check_character_count_for_widget(self, text_widget):
        """Helper method to trigger character count check for a text widget after paste"""
        try:
            # Find which column this widget belongs to by checking widget references
            # This is needed because the paste handler doesn't know the column name
            for col_name, widgets in getattr(self, 'excel_widgets', {}).items():
                if hasattr(widgets, 'text_widget') and widgets.text_widget == text_widget:
                    # Create a dummy event for character count checking
                    class DummyEvent:
                        def __init__(self, widget):
                            self.widget = widget

                    self.check_character_count(DummyEvent(text_widget), col_name)
                    break
                elif widgets == text_widget:  # Direct widget reference
                    self.check_character_count(DummyEvent(text_widget), col_name)
                    break
        except (AttributeError, TypeError):
            # If we can't determine the column, skip character count check
            pass

    def handle_copy_with_format(self, event):
        """Handle Ctrl+C - copy text with formatting to internal clipboard"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                try:
                    # Get selection bounds
                    start = focused_widget.index(tk.SEL_FIRST)
                    end = focused_widget.index(tk.SEL_LAST)

                    # Get selected text
                    text = focused_widget.get(start, end)

                    # Get all formatting tags in selection
                    tags_data = []
                    for tag in ["bold", "red", "blue", "green", "default"]:
                        tag_ranges = focused_widget.tag_ranges(tag)
                        for i in range(0, len(tag_ranges), 2):
                            tag_start = tag_ranges[i]
                            tag_end = tag_ranges[i + 1]
                            # Check if tag overlaps with selection
                            if focused_widget.compare(tag_start, "<", end) and focused_widget.compare(tag_end, ">", start):
                                # Calculate relative positions within selection
                                rel_start = max(0, len(focused_widget.get(start, tag_start)))
                                rel_end = min(len(text), len(focused_widget.get(start, tag_end)))
                                tags_data.append((tag, rel_start, rel_end))

                    # Store in internal clipboard
                    self.internal_clipboard = (text, tags_data)

                    # Also copy to system clipboard (plain text)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)

                except tk.TclError:
                    # No selection
                    pass
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default handling

    def handle_cut_with_format(self, event):
        """Handle Ctrl+X - cut text with formatting to internal clipboard"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # First copy with format
                self.handle_copy_with_format(event)

                # Then delete selection with undo support
                if focused_widget.tag_ranges(tk.SEL):
                    focused_widget.edit_separator()
                    focused_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    focused_widget.edit_separator()
                    return "break"  # Prevent default cut
        except (tk.TclError, AttributeError):
            pass
        return None

    def handle_delete_with_undo(self, event):
        """Handle Delete/BackSpace - prepare undo state before deletion"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # Check if there's selected text that will be deleted
                has_selection = bool(focused_widget.tag_ranges(tk.SEL))

                # Or if we just did a select-all
                select_all_pending = getattr(focused_widget, '_select_all_pending', False)

                if has_selection or select_all_pending:
                    # Save current content to our custom undo stack
                    current_content = focused_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(focused_widget, current_content)

                    logger.info(f"Saved undo state before {event.keysym} operation")

                # Clear the select-all pending flag
                if hasattr(focused_widget, '_select_all_pending'):
                    delattr(focused_widget, '_select_all_pending')
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default delete to proceed

    def handle_delete_key_undo(self, event):
        """Handle Delete/BackSpace key press - create undo separator when deleting selection"""
        try:
            text_widget = event.widget
            if isinstance(text_widget, tk.Text):
                # Check if there's selected text that will be deleted
                if text_widget.tag_ranges(tk.SEL):
                    text_widget.edit_separator()
                    logger.info(f"Added undo separator before {event.keysym} on selection")

            # Allow the default key handling to proceed
            return None
        except (tk.TclError, AttributeError):
            # Error accessing selection or widget - let default handling proceed
            return None

    # ...existing code...

    def get_stats_text(self) -> str:
        """Get statistics text"""
        return (f"PDF:er öppnade: {self.stats['pdfs_opened']} | "
                f"Filer omdöpta: {self.stats['files_renamed']} | "
                f"Excel-rader: {self.stats['excel_rows_added']}")

    def update_stats_display(self):
        """Update statistics display"""
        self.filename_stats_label.configure(text=self.get_stats_text())

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

    def setup_undo_functionality(self):
        """Setup keyboard bindings for undo/redo"""
        # Bind global keyboard shortcuts
        self.root.bind_all('<Control-z>', self.global_undo)
        self.root.bind_all('<Control-y>', self.global_redo)
        self.root.bind_all('<Control-Shift-Z>', self.global_redo)  # Alternative redo binding

        # Add enhanced bindings for Text widgets to handle problematic operations
        self.root.bind_all('<Control-a>', self.handle_select_all_undo)
        self.root.bind_all('<Control-c>', self.handle_copy_with_format)
        self.root.bind_all('<Control-x>', self.handle_cut_with_format)
        # NOTE: Paste binding removed - now handled directly on each Text widget
        self.root.bind_all('<Delete>', self.handle_delete_with_undo)
        self.root.bind_all('<BackSpace>', self.handle_delete_with_undo)

    def global_undo(self, event=None):
        """Global undo function that works on focused widget"""
        focused_widget = self.root.focus_get()
        if focused_widget and focused_widget in self.undo_widgets:
            # For Text widgets, try custom undo first, then fallback to edit_undo
            if isinstance(focused_widget, tk.Text):
                # Try custom undo first for problematic operations
                if self.text_widget_undo(focused_widget):
                    return "break"  # Prevent default handling
                else:
                    # Fallback to built-in undo
                    try:
                        focused_widget.edit_undo()
                        return "break"  # Prevent default handling
                    except tk.TclError:
                        # No undo available
                        pass
            # For Entry widgets, use our custom undo system
            elif hasattr(focused_widget, 'get') and hasattr(focused_widget, 'delete'):
                if self.undo_entry_widget(focused_widget):
                    return "break"  # Prevent default handling
        return None

    def global_redo(self, event=None):
        """Global redo function that works on focused widget"""
        focused_widget = self.root.focus_get()
        if focused_widget and focused_widget in self.undo_widgets:
            # For Text widgets, try custom redo first, then fallback to edit_redo
            if isinstance(focused_widget, tk.Text):
                # Try custom redo first for problematic operations
                if self.text_widget_redo(focused_widget):
                    return "break"  # Prevent default handling
                else:
                    # Fallback to built-in redo
                    try:
                        focused_widget.edit_redo()
                        return "break"  # Prevent default handling
                    except tk.TclError:
                        # No redo available
                        pass
            # For Entry widgets, use our custom redo system
            elif hasattr(focused_widget, 'get') and hasattr(focused_widget, 'delete'):
                if self.redo_entry_widget(focused_widget):
                    return "break"  # Prevent default handling
        return None

    def enable_undo_for_widget(self, widget):
        """Enable undo/redo for a specific widget and add to tracking list"""
        if hasattr(widget, 'config'):
            # Only enable undo for Text widgets (Entry widgets don't reliably support undo parameter)
            if isinstance(widget, tk.Text):
                widget.configure(undo=True, maxundo=20)
            elif hasattr(widget, 'get') and hasattr(widget, 'delete'):
                # This is an Entry widget - set up custom undo tracking
                self.setup_entry_undo(widget)

            # Add to our tracking list for global undo/redo handling
            if widget not in self.undo_widgets:
                self.undo_widgets.append(widget)

    def setup_entry_undo(self, entry_widget):
        """Set up custom undo tracking for an Entry widget"""
        # Initialize undo/redo stacks for this widget
        widget_id = id(entry_widget)
        self.entry_undo_stacks[widget_id] = []
        self.entry_redo_stacks[widget_id] = []

        # Store the initial value
        initial_value = entry_widget.get()
        self.entry_undo_stacks[widget_id].append(initial_value)

        # Bind events to track changes
        entry_widget.bind('<KeyRelease>', lambda e: self.on_entry_change(entry_widget, e))
        entry_widget.bind('<FocusOut>', lambda e: self.on_entry_change(entry_widget, e))
        entry_widget.bind('<Button-1>', lambda e: self.on_entry_change(entry_widget, e))

    def on_entry_change(self, entry_widget, event=None):
        """Called when an Entry widget changes - save to undo stack"""
        widget_id = id(entry_widget)
        current_value = entry_widget.get()

        # Get the last saved value
        if widget_id in self.entry_undo_stacks and self.entry_undo_stacks[widget_id]:
            last_value = self.entry_undo_stacks[widget_id][-1]

            # Only save if the value has actually changed
            if current_value != last_value:
                # Add to undo stack
                self.entry_undo_stacks[widget_id].append(current_value)

                # Limit the undo stack size
                if len(self.entry_undo_stacks[widget_id]) > self.max_undo_levels:
                    self.entry_undo_stacks[widget_id].pop(0)

                # Clear redo stack when new change is made
                self.entry_redo_stacks[widget_id] = []

    def undo_entry_widget(self, entry_widget):
        """Perform undo on an Entry widget"""
        widget_id = id(entry_widget)

        if widget_id not in self.entry_undo_stacks:
            return False

        undo_stack = self.entry_undo_stacks[widget_id]
        redo_stack = self.entry_redo_stacks[widget_id]

        # Need at least 2 items (current + previous)
        if len(undo_stack) < 2:
            return False

        # Move current value to redo stack
        current_value = undo_stack.pop()
        redo_stack.append(current_value)

        # Get previous value and set it
        previous_value = undo_stack[-1]
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, previous_value)

        return True

    def redo_entry_widget(self, entry_widget):
        """Perform redo on an Entry widget"""
        widget_id = id(entry_widget)

        if widget_id not in self.entry_redo_stacks:
            return False

        undo_stack = self.entry_undo_stacks[widget_id]
        redo_stack = self.entry_redo_stacks[widget_id]

        # Need at least 1 item in redo stack
        if len(redo_stack) < 1:
            return False

        # Move value from redo to undo stack
        redo_value = redo_stack.pop()
        undo_stack.append(redo_value)

        # Set the redo value
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, redo_value)

        return True

    def save_text_undo_state(self, text_widget, content):
        """Save text widget state with formatting to custom undo stack"""
        widget_id = id(text_widget)

        # Initialize stacks if not exists
        if widget_id not in self.text_undo_stacks:
            self.text_undo_stacks[widget_id] = []
            self.text_redo_stacks[widget_id] = []

        # Collect all formatting tags
        tags_data = []
        for tag in ["bold", "red", "blue", "green", "default"]:
            tag_ranges = text_widget.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start_idx = str(tag_ranges[i])
                end_idx = str(tag_ranges[i + 1])
                tags_data.append((tag, start_idx, end_idx))

        # Create state tuple with content and tags
        state = (content, tags_data)

        # Don't add duplicate content to avoid double-undo issues
        if self.text_undo_stacks[widget_id] and self.text_undo_stacks[widget_id][-1][0] == content:
            return

        # Add to undo stack
        self.text_undo_stacks[widget_id].append(state)

        # Limit stack size
        if len(self.text_undo_stacks[widget_id]) > self.max_undo_levels:
            self.text_undo_stacks[widget_id].pop(0)

        # Clear redo stack when new state is saved
        self.text_redo_stacks[widget_id] = []

    def text_widget_undo(self, text_widget):
        """Perform undo on Text widget with formatting using custom stack"""
        widget_id = id(text_widget)

        if widget_id not in self.text_undo_stacks or len(self.text_undo_stacks[widget_id]) < 2:
            return False

        undo_stack = self.text_undo_stacks[widget_id]
        redo_stack = self.text_redo_stacks[widget_id]

        # Save current state to redo stack
        current_content = text_widget.get("1.0", "end-1c")
        current_tags = []
        for tag in ["bold", "red", "blue", "green", "default"]:
            tag_ranges = text_widget.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start_idx = str(tag_ranges[i])
                end_idx = str(tag_ranges[i + 1])
                current_tags.append((tag, start_idx, end_idx))
        redo_stack.append((current_content, current_tags))

        # Remove the current state from undo stack
        undo_stack.pop()

        # Get the previous state from undo stack
        if undo_stack:
            previous_content, previous_tags = undo_stack[-1]
        else:
            previous_content, previous_tags = "", []

        # Restore content
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", previous_content)

        # Restore formatting
        for tag, start_idx, end_idx in previous_tags:
            try:
                text_widget.tag_add(tag, start_idx, end_idx)
            except tk.TclError:
                # Handle invalid indices
                pass

        logger.info("Performed custom undo on Text widget with formatting")
        return True

    def text_widget_redo(self, text_widget):
        """Perform redo on Text widget with formatting using custom stack"""
        widget_id = id(text_widget)

        if widget_id not in self.text_redo_stacks or not self.text_redo_stacks[widget_id]:
            return False

        undo_stack = self.text_undo_stacks[widget_id]
        redo_stack = self.text_redo_stacks[widget_id]

        # Get next state from redo stack
        next_content, next_tags = redo_stack.pop()

        # Save current state to undo stack
        current_content = text_widget.get("1.0", "end-1c")
        current_tags = []
        for tag in ["bold", "red", "blue", "green", "default"]:
            tag_ranges = text_widget.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start_idx = str(tag_ranges[i])
                end_idx = str(tag_ranges[i + 1])
                current_tags.append((tag, start_idx, end_idx))
        undo_stack.append((current_content, current_tags))

        # Restore content
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", next_content)

        # Restore formatting
        for tag, start_idx, end_idx in next_tags:
            try:
                text_widget.tag_add(tag, start_idx, end_idx)
            except tk.TclError:
                # Handle invalid indices
                pass

        logger.info("Performed custom redo on Text widget with formatting")
        return True

    def get_theme_default_text_color(self):
        """Get the current theme's appropriate default text color"""
        try:
            # Get current style instance
            # Style removed - not needed in CustomTkinter
            # Get default text color from CustomTkinter theme
            # CustomTkinter uses appearance mode for theming
            appearance_mode = ctk.get_appearance_mode()
            if appearance_mode == "Dark":
                return '#ffffff'  # White text for dark mode
            else:
                return '#000000'  # Black text for light mode

        except Exception as e:
            logger.warning(f"Could not determine theme default color: {e}")
            # Safe fallback - dark gray that works on most backgrounds
            return '#404040'

    def setup_text_formatting_tags(self, text_widget):
        """Configure formatting tags for rich text support"""
        # Get current font size from config
        font_size = self.config.get('text_font_size', 9)

        # Get the actual default text color from the widget
        default_color = text_widget.cget('foreground')

        # Bold tag
        text_widget.tag_configure("bold", font=('Arial', font_size, 'bold'))

        # Color tags
        text_widget.tag_configure("red", foreground="red")
        text_widget.tag_configure("blue", foreground="blue")
        text_widget.tag_configure("green", foreground="green")
        text_widget.tag_configure("default", foreground=default_color)  # Use actual default color

    def update_formatting_tags(self, text_widget, font_size):
        """Update formatting tags with new font size"""
        # Update bold tag
        text_widget.tag_configure("bold", font=('Arial', font_size, 'bold'))

        # Color tags don't need font size updates

    def toggle_text_font_size(self):
        """Toggle text font size between 9pt → 12pt → 15pt → 9pt"""
        current_size = self.config.get('text_font_size', 9)

        # Cycle through font sizes
        if current_size == 9:
            new_size = 12
        elif current_size == 12:
            new_size = 15
        else:  # 15 or any other value
            new_size = 9

        # Update config
        self.config['text_font_size'] = new_size
        self.config_manager.save_config(self.config)

        # Apply new font size to all text fields
        self.apply_text_font_size(new_size)

        logger.info(f"Text font size changed from {current_size}pt to {new_size}pt")

    def apply_text_font_size(self, font_size):
        """Apply font size to all text fields (Händelse and Note1-3) and update formatting tags"""
        text_fields = ['Händelse', 'Note1', 'Note2', 'Note3']

        for field_name in text_fields:
            if field_name in self.excel_vars:
                text_widget = self.excel_vars[field_name]

                # Update main widget font (for ScrollableText, we need the actual text widget)
                if hasattr(text_widget, 'text_widget'):  # ScrollableText wrapper
                    actual_widget = text_widget.text_widget
                else:
                    actual_widget = text_widget

                # Update the main font
                actual_widget.configure(font=('Arial', font_size))

                # Update formatting tags to use new font size
                self.update_formatting_tags(actual_widget, font_size)

                logger.debug(f"Updated font size to {font_size}pt for {field_name}")

    def configure_button_styles(self):
        """Configure custom button styles with fixed colors that persist across theme changes"""
        # Style configuration not needed in CustomTkinter
        # Colors are set directly on buttons
        pass

    def create_formatting_toolbar(self, parent_frame, text_widget, col_name):
        """Create formatting toolbar with buttons and bind keyboard shortcuts"""
        # Ensure custom button styles are configured
        self.configure_button_styles()
        # Bold button - styled with bold text using Unicode
        bold_btn = ctk.CTkButton(parent_frame, text="𝐁", width=30,
                           command=lambda: self.toggle_format(text_widget, "bold"))
        bold_btn.pack(side="left", padx=(0, 2))

        # Color buttons with fixed colors (order: Red, Green, Blue)
        # Red button - fixed red color
        red_btn = ctk.CTkButton(parent_frame, text="●", width=30,
                          command=lambda: self.toggle_format(text_widget, "red"),
                          fg_color="#DC3545", hover_color="#C82333")
        red_btn.pack(side="left", padx=(0, 2))

        # Green button - fixed green color
        green_btn = ctk.CTkButton(parent_frame, text="●", width=30,
                            command=lambda: self.toggle_format(text_widget, "green"),
                            fg_color="#28A745", hover_color="#218838")
        green_btn.pack(side="left", padx=(0, 2))

        # Blue button - fixed blue color
        blue_btn = ctk.CTkButton(parent_frame, text="●", width=30,
                           command=lambda: self.toggle_format(text_widget, "blue"),
                           fg_color="#007BFF", hover_color="#0069D9")
        blue_btn.pack(side="left", padx=(0, 2))

        # Clear formatting button - removes ALL formatting and restores theme default color
        default_btn = ctk.CTkButton(parent_frame, text="T", width=30,
                              command=lambda: self.clear_all_formatting(text_widget),
                              fg_color="gray60", hover_color="gray50")
        default_btn.pack(side="left", padx=(0, 2))

        # Font size toggle button
        font_btn = ctk.CTkButton(parent_frame, text="A+", width=30,
                           command=lambda: self.toggle_text_font_size())
        font_btn.pack(side="left", padx=(2, 0))

        # Bind keyboard shortcuts for this text widget
        text_widget.bind('<Control-b>', lambda e: self.toggle_format(text_widget, "bold"))
        text_widget.bind('<Control-r>', lambda e: self.toggle_format(text_widget, "red"))
        text_widget.bind('<Control-1>', lambda e: self.toggle_format(text_widget, "blue"))
        text_widget.bind('<Control-g>', lambda e: self.toggle_format(text_widget, "green"))
        text_widget.bind('<Control-k>', lambda e: self.clear_all_formatting(text_widget))

    def toggle_format(self, text_widget, format_type):
        """Toggle formatting on selected text with undo support"""
        try:
            # Add edit separator BEFORE formatting change
            text_widget.edit_separator()

            # Get current selection
            try:
                start = text_widget.index(tk.SEL_FIRST)
                end = text_widget.index(tk.SEL_LAST)
            except tk.TclError:
                # No selection, use current cursor position for word
                cursor = text_widget.index(tk.INSERT)
                # Find word boundaries
                start = text_widget.index(f"{cursor} wordstart")
                end = text_widget.index(f"{cursor} wordend")

            # Check if the selection already has this format
            current_tags = text_widget.tag_names(start)

            if format_type in current_tags:
                # Remove the format
                text_widget.tag_remove(format_type, start, end)
            else:
                # Add the format
                text_widget.tag_add(format_type, start, end)

            # For colors, remove other color tags when applying a new one
            if format_type in ["red", "blue", "green", "default"]:
                color_tags = ["red", "blue", "green", "default"]
                for color_tag in color_tags:
                    if color_tag != format_type:
                        text_widget.tag_remove(color_tag, start, end)

            # Add edit separator AFTER formatting change
            text_widget.edit_separator()

        except tk.TclError:
            # Handle any errors silently
            pass

    def clear_all_formatting(self, text_widget):
        """Clear ALL formatting from selected text and restore theme-appropriate default color"""
        try:
            # Add edit separator BEFORE formatting change
            text_widget.edit_separator()

            # Get current selection
            try:
                start = text_widget.index(tk.SEL_FIRST)
                end = text_widget.index(tk.SEL_LAST)
            except tk.TclError:
                # No selection, use entire text
                start = "1.0"
                end = "end-1c"

            # Remove ALL formatting tags from the selection
            all_format_tags = ["bold", "red", "blue", "green", "default"]
            for tag in all_format_tags:
                text_widget.tag_remove(tag, start, end)

            # Get the text widget's actual default color (not the theme's system color)
            default_color = text_widget.cget('foreground')

            # Create a temporary tag for the theme default color
            temp_tag = "theme_default"
            text_widget.tag_configure(temp_tag, foreground=default_color)
            text_widget.tag_add(temp_tag, start, end)

            # Immediately replace the temporary tag with the permanent default tag
            text_widget.tag_remove(temp_tag, start, end)
            text_widget.tag_configure("default", foreground=default_color)
            text_widget.tag_add("default", start, end)

            # Add edit separator AFTER formatting change
            text_widget.edit_separator()

            logger.debug(f"Cleared all formatting and applied theme color {default_color}")

        except tk.TclError as e:
            logger.warning(f"Error clearing formatting: {e}")
            pass

    def get_formatted_text_for_excel(self, text_widget):
        """METHOD 2: CHARACTER-BY-CHARACTER BREAKTHROUGH ALGORITHM - Extract formatted text from Text widget"""
        try:
            from openpyxl.cell.rich_text import CellRichText, TextBlock
            from openpyxl.cell.text import InlineFont
            from openpyxl.styles.colors import Color

            # Get plain text
            plain_text = text_widget.get("1.0", "end-1c")

            # Check if there are any formatting tags
            all_tags = text_widget.tag_names()
            format_tags = [tag for tag in all_tags if tag in ["bold", "red", "blue", "green", "default"]]

            if not format_tags:
                # No formatting, return plain text
                return plain_text

            # METHOD 2: Process text character by character to maintain correct order
            rich_parts = []
            current_pos = "1.0"

            # Get all text
            text_end = text_widget.index("end-1c")

            # Iterate through text character by character
            while text_widget.compare(current_pos, "<", text_end):
                next_pos = f"{current_pos} +1c"
                char = text_widget.get(current_pos, next_pos)

                # Get tags at current position
                tags_at_pos = text_widget.tag_names(current_pos)
                format_tags_at_pos = [tag for tag in tags_at_pos if tag in ["bold", "red", "blue", "green", "default"]]

                # Build text with same formatting
                text_with_format = char
                temp_pos = next_pos

                # Continue until formatting changes
                while text_widget.compare(temp_pos, "<", text_end):
                    temp_tags = text_widget.tag_names(temp_pos)
                    temp_format_tags = [tag for tag in temp_tags if tag in ["bold", "red", "blue", "green", "default"]]

                    if set(format_tags_at_pos) != set(temp_format_tags):
                        break

                    next_char_pos = f"{temp_pos} +1c"
                    text_with_format += text_widget.get(temp_pos, next_char_pos)
                    temp_pos = next_char_pos

                # Create appropriate part
                if format_tags_at_pos:
                    font_kwargs = {}
                    for tag in format_tags_at_pos:
                        if tag == "bold":
                            font_kwargs['b'] = True
                        elif tag == "italic":
                            font_kwargs['i'] = True
                        elif tag == "red":
                            font_kwargs['color'] = Color(rgb="FF0000")
                        elif tag == "blue":
                            font_kwargs['color'] = Color(rgb="0000FF")
                        elif tag == "green":
                            font_kwargs['color'] = Color(rgb="008000")
                        elif tag == "default":
                            # For default color, we'll need to use the actual default text color
                            # For Excel export, we can use a dark gray that matches typical default text
                            font_kwargs['color'] = Color(rgb="404040")

                    if font_kwargs:
                        font = InlineFont(**font_kwargs)
                        rich_parts.append(TextBlock(font, text_with_format))
                    else:
                        rich_parts.append(text_with_format)
                else:
                    rich_parts.append(text_with_format)

                current_pos = temp_pos

            # Create CellRichText if we have formatting
            if any(isinstance(part, TextBlock) for part in rich_parts):
                result = CellRichText(*rich_parts)
                logger.info(f"METHOD 2: Created CellRichText with {len(result)} parts")
                return result
            else:
                return plain_text

        except Exception as e:
            logger.warning(f"Error extracting formatted text with Method 2: {e}")
            # Fallback to plain text
            return text_widget.get("1.0", "end-1c")

    def run(self):
        """Start the application"""
        self.root.mainloop()
