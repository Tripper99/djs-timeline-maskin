#!/usr/bin/env python3
"""
Main window for DJs Timeline-maskin
Contains the PDFProcessorApp class with GUI implementation
"""

# Standard library imports
import os
import re
import json
import shutil
import tempfile
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# GUI imports
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext
except ImportError:
    print("Error: ttkbootstrap not installed. Install with: pip install ttkbootstrap")
    exit(1)

# PDF processing
try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 not installed. Install with: pip install PyPDF2")
    exit(1)

# Excel processing
try:
    import openpyxl
    from openpyxl.styles import NamedStyle
except ImportError:
    print("Error: openpyxl not installed. Install with: pip install openpyxl")
    exit(1)

# Local imports
from core.config import ConfigManager
from core.pdf_processor import PDFProcessor
from core.filename_parser import FilenameParser
from core.excel_manager import ExcelManager
from gui.utils import ToolTip
from utils.constants import VERSION

# Setup logging
logger = logging.getLogger(__name__)

class PDFProcessorApp:
    """Main application class"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.excel_manager = ExcelManager()
        
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
        self.load_saved_excel_file()
        
        # Load and restore locked fields after GUI is created
        self.restore_locked_fields()
    
    def collect_locked_field_data(self) -> Tuple[Dict[str, bool], Dict[str, str]]:
        """Collect current locked field states and their contents"""
        try:
            locked_states = {}
            locked_contents = {}
            
            # Collect lock states
            for field_name, lock_var in self.lock_vars.items():
                locked_states[field_name] = lock_var.get()
            
            # Collect field contents for locked fields
            for field_name in self.lock_vars.keys():
                if locked_states.get(field_name, False):  # Only collect if locked
                    if field_name in self.excel_vars:
                        var = self.excel_vars[field_name]
                        
                        # Handle different widget types
                        if hasattr(var, 'get') and hasattr(var, 'delete'):  # Text widget
                            content = var.get("1.0", "end-1c")  # Get all text except final newline
                        elif hasattr(var, 'get'):  # StringVar or Entry
                            content = var.get()
                        else:
                            content = ""
                        
                        if content.strip():  # Only save non-empty content
                            locked_contents[field_name] = content
            
            logger.info(f"Collected {len(locked_contents)} locked fields with content")
            return locked_states, locked_contents
            
        except Exception as e:
            logger.error(f"Error collecting locked field data: {e}")
            return {}, {}
    
    def restore_locked_fields(self) -> None:
        """Restore locked field states and contents from saved configuration"""
        try:
            # Load saved locked fields data
            locked_states, locked_contents = self.config_manager.load_locked_fields()
            
            if not locked_states and not locked_contents:
                logger.info("No saved locked fields to restore")
                return
            
            # Restore lock states
            for field_name, is_locked in locked_states.items():
                if field_name in self.lock_vars:
                    self.lock_vars[field_name].set(is_locked)
                    logger.debug(f"Restored lock state for {field_name}: {is_locked}")
            
            # Restore field contents for locked fields
            for field_name, content in locked_contents.items():
                if field_name in self.excel_vars and locked_states.get(field_name, False):
                    var = self.excel_vars[field_name]
                    
                    # Handle different widget types
                    if hasattr(var, 'delete') and hasattr(var, 'insert'):  # Text widget
                        var.delete("1.0", tk.END)
                        var.insert("1.0", content)
                    elif hasattr(var, 'set'):  # StringVar
                        var.set(content)
                    
                    logger.debug(f"Restored content for locked field {field_name}: {content[:50]}...")
            
            logger.info(f"Restored {len(locked_states)} lock states and {len(locked_contents)} field contents")
            
        except Exception as e:
            logger.error(f"Error restoring locked fields: {e}")
    
    def save_locked_fields_on_exit(self) -> None:
        """Save current locked field states and contents before exit"""
        try:
            locked_states, locked_contents = self.collect_locked_field_data()
            
            if locked_states or locked_contents:
                self.config_manager.save_locked_fields(locked_states, locked_contents)
                logger.info("Saved locked fields before exit")
            else:
                logger.info("No locked fields to save")
                
        except Exception as e:
            logger.error(f"Error saving locked fields on exit: {e}")
    
    def setup_gui(self):
        """Setup the main GUI"""
        # Get saved theme or use default
        current_theme = self.config.get('theme', 'simplex')
        self.root = tb.Window(themename=current_theme)
        self.root.title(f"DJs Timeline-maskin {VERSION}")
        self.root.geometry("2000x1400")  # Optimal size - wide enough and sufficient height
        
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
        x = (screen_width // 2) - (2000 // 2)  # Center horizontally
        y = 0  # Position at the very top of screen
        self.root.geometry(f"2000x1400+{x}+{y}")  # Final size and position
        
        # Create menu bar
        self.create_menu_bar()
        
        # Setup undo functionality
        self.setup_undo_functionality()
        
        # Main container
        main_frame = tb.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Variables
        self.setup_variables()
        
        # Create GUI groups
        self.create_group1(main_frame)  # PDF Selection
        self.create_group2(main_frame)  # Filename Editing
        self.create_group3(main_frame)  # Excel Integration
        self.create_group4(main_frame)  # Excel Operations Buttons
        
        # Bottom frame for statistics and version
        bottom_frame = tb.Frame(self.root)
        bottom_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Statistics label (left side)
        self.filename_stats_label = tb.Label(bottom_frame, text=self.get_stats_text(), 
                                           font=('Arial', 9))
        self.filename_stats_label.pack(side="left")
        ToolTip(self.filename_stats_label, "Statistik över användning: Antal PDF:er öppnade, "
                                         "filer omdöpta och Excel-rader tillagda under denna session.")
        
        # Version label (right side)
        version_label = tb.Label(bottom_frame, text=VERSION, font=('Arial', 8))
        version_label.pack(side="right")
        ToolTip(version_label, f"Programversion {VERSION}. DJs Timeline-maskin för PDF-filhantering och Excel-integration.")
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        
        # Character counters for text fields (1000 char limit)
        self.char_counters = {}
        self.char_limit = 1000;
        
        # Undo/Redo functionality - track widgets that support undo
        self.undo_widgets = []  # List of widgets with undo enabled
        
        # Custom undo system for Entry widgets
        self.entry_undo_stacks = {}  # Dictionary to store undo history for each Entry widget
        self.entry_redo_stacks = {}  # Dictionary to store redo history for each Entry widget
        
        # Custom undo system for Text widgets (for problematic operations)
        self.text_undo_stacks = {}  # Dictionary to store undo history for each Text widget
        self.text_redo_stacks = {}  # Dictionary to store redo history for each Text widget
        
        self.max_undo_levels = 20  # Maximum number of undo levels
        
        # Lock switches for ALL fields except Dag, Händelse and Inlagd datum (which is read-only)
        self.lock_vars = {
            'OBS': tk.BooleanVar(),
            'Kategori': tk.BooleanVar(),
            'Underkategori': tk.BooleanVar(), 
            'Person/sak': tk.BooleanVar(),
            'Egen grupp': tk.BooleanVar(),
            'Tid start': tk.BooleanVar(),
            'Tid slut': tk.BooleanVar(),
            'Note1': tk.BooleanVar(),
            'Note2': tk.BooleanVar(),
            'Note3': tk.BooleanVar(),
            'Källa1': tk.BooleanVar(),
            'Källa2': tk.BooleanVar(),
            'Källa3': tk.BooleanVar(),
            'Historiskt': tk.BooleanVar()  # Updated from "Korrelerande historisk händelse"
        }
        
        # Move to subfolder switch - DEFAULT ON
        self.move_to_subfolder_var = tk.BooleanVar(value=True)
        
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
        self.root.config(menu=menubar)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=help_menu)
        help_menu.add_command(label="Om programmet", command=self.show_program_help)
        help_menu.add_separator()
        help_menu.add_command(label="Excel-fil krav", command=self.show_excel_help)
        
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
        """Show comprehensive help about what the program does"""
        help_win = tb.Toplevel()
        help_win.title("Om APP DJs Timeline-verktyg")
        help_win.geometry("700x600")
        help_win.transient(self.root)
        help_win.grab_set()
        
        # Center dialog
        help_win.update_idletasks()
        x = (help_win.winfo_screenwidth() // 2) - (700 // 2)
        y = (help_win.winfo_screenheight() // 2) - (600 // 2)
        help_win.geometry(f"700x600+{x}+{y}")
        
        # Main frame
        main_frame = tb.Frame(help_win)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        tb.Label(main_frame, text=f"DJs Timeline-maskin {VERSION}", 
                font=('Arial', 16, 'bold')).pack(pady=(0, 15))
        
        # Help text
        help_text = """HUVUDFUNKTIONER:

📄 PDF-FILHANTERING:
• Välj PDF-filer för bearbetning
• Programmet öppnar PDF:en automatiskt för visning
• Parsning av filnamn till komponenter (datum, tidning, kommentar, sidor)
• Automatisk räkning av sidantal från PDF-filen

🏷️ FILNAMNÄNDRING:
• Redigera filnamnskomponenter: Datum, Tidning, Kommentar, Sidor
• Validering av filnamn för Windows-kompatibilitet
• Omdöpning av PDF-filer med nytt konstruerat namn
• Alternativ att flytta omdöpta filer till undermapp "Omdöpta filer"

📊 EXCEL-INTEGRATION:
• Stöd för Excel-filer (.xlsx) med fördefinierade kolumner
• Alternativ att skapa säkerhetskopia av Excel-fil innan bearbetning
• Automatisk mall-skapare med rätt kolumnnamn och formatering
• Låsfunktion för viktiga fält (alla fält utom Dag, Händelse och Inlagd datum)

📝 TEXTBEARBETNING:
• Kopiering av filnamnsdata till Excel-fält
• Automatisk rensning av PDF-text (tar bort onödiga radbrytningar)
• Teckengräns på 1000 tecken per textfält (Händelse, Note1-3)
• Realtidsräknare som visar återstående tecken med färgkodning
• Smart inklistring med automatisk textuppdelning över flera fält
• Word wrap för bättre läsbarhet i långa textfält

🗓️ AUTOMATISK DATAHANTERING:
• "Dag"-kolumn fylls automatiskt med Excel-formel =SUM(Tid_start)
• Formateras som DDD (mån, tis, ons, etc.)
• Automatisk datum-formatering för datum-kolumner
• Automatisk ifyllning av dagens datum i "Inlagd datum"

💾 SPARFUNKTIONER:
• "Spara allt och rensa fälten" - genomför alla operationer på en gång
• Villkorlig sparning: PDF döps om OM filnamnet ändrats
• Villkorlig Excel-rad: sparas OM "Tid start" OCH "Händelse" har innehåll
• Automatisk rensning av alla fält efter sparning (utom låsta)
• Färgkodning av rader - välj bakgrundsfärg för visuell kategorisering

⚙️ ÖVRIGA FUNKTIONER:
• Minneshantering av Excel-fil mellan sessioner
• Statistik över öppnade PDF:er, omdöpta filer och Excel-rader
• Validering av alla inställningar innan bearbetning
• Säker filhantering med felkontroll och återställningsmöjligheter
• Radbackgrundsfärger för enkel kategorisering (gul, grön, blå, rosa, grå)

ARBETSFLÖDE:
1. Välj Excel-fil (skapa kopia rekommenderas)
2. Välj PDF-fil (öppnas automatiskt)
3. Justera filnamnskomponenter vid behov
4. Kopiera filnamn till Excel-fält
5. Fyll i ytterligare Excel-information
6. Klicka "Spara allt och rensa fälten"
7. Upprepa för nästa PDF

Programmet är designat för effektiv bearbetning av många PDF-filer med konsekvent dokumentation i Excel."""
        
        # Scrollable text area
        text_frame = tb.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                            font=('Arial', 10), height=20)
        text_area.pack(fill="both", expand=True)
        text_area.insert("1.0", help_text)
        text_area.config(state=tk.DISABLED)
        
        # Close button
        tb.Button(main_frame, text="Stäng",
                 command=help_win.destroy,
                 bootstyle=PRIMARY, width=15).pack(pady=(10, 0))
    
    def create_group1(self, parent):
        """Group 1: PDF Selection"""
        group1 = tb.LabelFrame(parent, text="1. PDF-fil", padding=15)
        group1.pack(fill="x", pady=(0, 15))
        
        # PDF path display
        pdf_path_frame = tb.Frame(group1)
        pdf_path_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(pdf_path_frame, text="Vald fil:", font=('Arial', 10)).pack(side="left")
        pdf_path_entry = tb.Entry(pdf_path_frame, textvariable=self.pdf_path_var, 
                                 state="readonly", font=('Arial', 9), width=60)
        pdf_path_entry.pack(side="left", padx=(10, 10))
        ToolTip(pdf_path_entry, "Visar namn på den valda PDF-filen. Filen öppnas automatiskt när den väljs.")
        
        # Select PDF button
        select_pdf_btn = tb.Button(pdf_path_frame, text="Välj PDF", 
                                  command=self.select_pdf_file, bootstyle=PRIMARY)
        select_pdf_btn.pack(side="left")
        ToolTip(select_pdf_btn, "Välj en PDF-fil för bearbetning. Filen öppnas automatiskt för granskning, "
                               "filnamnet parsas till komponenter och sidantalet räknas automatiskt.")
    
    def create_group2(self, parent):
        """Group 2: Filename Editing"""
        group2 = tb.LabelFrame(parent, text="2. Filnamn komponenter", padding=15)
        group2.pack(fill="x", pady=(0, 15))
        
        # Create grid for filename components
        components_frame = tb.Frame(group2)
        components_frame.pack(fill="x")
        
        # Date
        tb.Label(components_frame, text="Datum:", font=('Arial', 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        date_entry = tb.Entry(components_frame, textvariable=self.date_var, width=15)
        date_entry.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=(0, 5))
        self.enable_undo_for_widget(date_entry)
        
        # Newspaper
        tb.Label(components_frame, text="Tidning:", font=('Arial', 10)).grid(
            row=0, column=2, sticky="w", padx=(0, 10), pady=(0, 5))
        newspaper_entry = tb.Entry(components_frame, textvariable=self.newspaper_var, width=20)
        newspaper_entry.grid(row=0, column=3, sticky="w", padx=(0, 20), pady=(0, 5))
        self.enable_undo_for_widget(newspaper_entry)
        
        # Pages
        tb.Label(components_frame, text="Sidor:", font=('Arial', 10)).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        pages_entry = tb.Entry(components_frame, textvariable=self.pages_var, width=5)
        pages_entry.grid(row=1, column=1, sticky="w", padx=(0, 20), pady=(0, 5))
        self.enable_undo_for_widget(pages_entry)
        
        # Comment
        tb.Label(components_frame, text="Kommentar:", font=('Arial', 10)).grid(
            row=1, column=2, sticky="w", padx=(0, 10), pady=(0, 5))
        comment_entry = tb.Entry(components_frame, textvariable=self.comment_var, width=48)
        comment_entry.grid(row=1, column=3, sticky="w", pady=(0, 5))
        self.enable_undo_for_widget(comment_entry)
        
        # Button frame
        button_frame = tb.Frame(components_frame)
        button_frame.grid(row=2, column=1, columnspan=3, pady=(10, 5))
        
        # Copy to Excel button
        self.copy_to_excel_btn = tb.Button(button_frame, text="Kopiera filnamn till Excel-fältet",
                                         command=self.copy_filename_to_excel,
                                         bootstyle=INFO, width=35)
        self.copy_to_excel_btn.pack(side="left")
    
    def create_group3(self, parent):
        """Group 3: Excel Integration"""
        group3 = tb.LabelFrame(parent, text="3. Excel-integration", padding=15)
        group3.pack(fill="x", pady=(0, 15))
        
        # Excel file selection
        excel_file_frame = tb.Frame(group3)
        excel_file_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(excel_file_frame, text="Excel-fil:", font=('Arial', 10)).pack(side="left")
        excel_path_entry = tb.Entry(excel_file_frame, textvariable=self.excel_path_var,
                                   state="readonly", font=('Arial', 9), width=60)
        excel_path_entry.pack(side="left", padx=(10, 10))
        ToolTip(excel_path_entry, "Visar namn på den valda Excel-filen. Programmet kommer ihåg senast använda fil.")
        
        # Button frame for Excel file selection and help
        excel_btn_frame = tb.Frame(excel_file_frame)
        excel_btn_frame.pack(side="left")
        
        self.select_excel_btn = tb.Button(excel_btn_frame, text="Välj Excel", 
                                         command=self.select_excel_file, 
                                         bootstyle=INFO)
        self.select_excel_btn.pack(side="left", padx=(0, 5))
        ToolTip(self.select_excel_btn, "Välj Excel-fil (.xlsx) för dataintegrering. "
                                      "Du får möjlighet att skapa en säkerhetskopia att arbeta med.")
        
        # Open Excel button
        self.open_excel_btn = tb.Button(excel_btn_frame, text="Öppna Excel", 
                                       command=self.open_excel_file, 
                                       bootstyle=SUCCESS, state="disabled")
        self.open_excel_btn.pack(side="left", padx=(0, 5))
        ToolTip(self.open_excel_btn, "Öppna den valda Excel-filen i externt program. "
                                    "Blir tillgänglig när en Excel-fil har valts.")
        
        # Help button (question mark)
        help_btn = tb.Button(excel_btn_frame, text="?", 
                           command=self.show_excel_help,
                           bootstyle=SECONDARY, width=3)
        help_btn.pack(side="left")
        
        # Excel column fields (scrollable, three-column layout)
        self.excel_fields_frame = tb.Frame(group3)
        self.excel_fields_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Configure the excel_fields_frame for responsive layout
        self.excel_fields_frame.grid_columnconfigure(0, weight=1)
        
        self.create_excel_fields()
    
    def create_group4(self, parent):
        """Group 4: Excel Operations Buttons"""
        group4 = tb.LabelFrame(parent, text="4. Excel-operationer", padding=15)
        group4.pack(fill="x", pady=(0, 15))
        
        # First row: Buttons for Excel operations
        excel_buttons_frame = tb.Frame(group4)
        excel_buttons_frame.pack(fill="x", pady=(0, 10))
        
        self.save_all_btn = tb.Button(excel_buttons_frame, text="Spara allt och rensa fälten",
                                     command=self.save_all_and_clear,
                                     bootstyle=SUCCESS, width=30)
        self.save_all_btn.pack(side="left", padx=(0, 10))
        
        self.new_excel_row_btn = tb.Button(excel_buttons_frame, text="Rensa allt utan att spara",
                                          command=self.clear_all_without_saving,
                                          bootstyle=INFO, width=30)
        self.new_excel_row_btn.pack(side="left", padx=(0, 20))
        
        # Move to subfolder switch
        self.move_switch = tb.Checkbutton(excel_buttons_frame, 
                                        text='Flytta omdöpt PDF till undermapp "Omdöpta filer"',
                                        variable=self.move_to_subfolder_var,
                                        bootstyle="info-round-toggle")
        self.move_switch.pack(side="left")
        ToolTip(self.move_switch, "När aktiverad: omdöpta PDF-filer flyttas till undermappen 'Omdöpta filer'. "
                                 "När inaktiverad: PDF-filer döps om på samma plats. Standard: PÅ.")
        
        # Second row: Row color selection
        color_frame = tb.Frame(group4)
        color_frame.pack(fill="x", pady=(5, 0))
        
        # Label for color selection
        color_label = tb.Label(color_frame, text="Nya radens färg:", font=('Arial', 10, 'bold'))
        color_label.pack(side="left", padx=(0, 15))
        
        # Color options with visual indicators
        color_options = [
            ("none", "Ingen", "#FFFFFF"),
            ("yellow", "Gul", "#FFFF99"),
            ("green", "Grön", "#CCFFCC"),
            ("blue", "Ljusblå", "#CCE5FF"),
            ("pink", "Ljusrosa", "#FFCCEE"),
            ("gray", "Ljusgrå", "#E6E6E6")
        ]
        
        for value, text, color in color_options:
            # Create frame for each radio button with color sample
            radio_frame = tb.Frame(color_frame)
            # Add consistent spacing between all options for better visual separation
            radio_frame.pack(side="left", padx=(0, 20))
            
            # Radio button
            radio = tb.Radiobutton(radio_frame, text=text, value=value, 
                                 variable=self.row_color_var, bootstyle="info")
            radio.pack(side="left")
            
            # Color sample using Canvas widget - skip for "none" option
            if value != "none":
                color_sample = tk.Canvas(radio_frame, width=20, height=15, highlightthickness=1,
                                       highlightbackground="black", highlightcolor="black")
                color_sample.pack(side="left", padx=(5, 0))
                color_sample.create_rectangle(0, 0, 20, 15, fill=color, outline="black")
    
    def load_saved_excel_file(self):
        """Load previously saved Excel file if it exists"""
        excel_path = self.config.get('excel_file', '')
        if excel_path and Path(excel_path).exists():
            if self.excel_manager.load_excel_file(excel_path):
                self.excel_path_var.set(Path(excel_path).name)
                self.create_excel_fields()
                # Enable the "Open Excel" button for previously loaded file
                self.open_excel_btn.config(state="normal")
                logger.info(f"Loaded saved Excel file: {excel_path}")
    
    def create_excel_fields(self):
        """Create input fields for Excel columns in three-column layout"""
        # Clear existing fields
        for widget in self.excel_fields_frame.winfo_children():
            widget.destroy()
        
        # Get column names from loaded Excel file
        column_names = self.excel_manager.get_column_names()
        if not column_names:
            tb.Label(self.excel_fields_frame, text="Välj en Excel-fil först", 
                    font=('Arial', 10)).pack(pady=20)
            return
        
        # Clear and recreate excel_vars for current columns
        self.excel_vars.clear()
        for col_name in column_names:
            # Don't create variables for automatically calculated fields
            if col_name != 'Dag':
                self.excel_vars[col_name] = tk.StringVar()
        
        # Auto-fill today's date in "Inlagd datum" field
        if 'Inlagd datum' in self.excel_vars:
            from datetime import datetime
            today_date = datetime.now().strftime('%Y-%m-%d')
            self.excel_vars['Inlagd datum'].set(today_date)
        
        # Create frame for Excel fields (responsive grid layout)
        fields_container = tb.Frame(self.excel_fields_frame)
        fields_container.pack(fill="both", expand=True, pady=(10, 0))
        
        # Configure responsive row expansion
        fields_container.grid_rowconfigure(0, weight=1)
        
        # Define column groupings (updated with new field name)
        column1_fields = ['OBS', 'Inlagd datum', 'Kategori', 'Underkategori', 'Person/sak', 
                         'Egen grupp', 'Dag', 'Tid start', 'Tid slut', 'Händelse']
        column2_fields = ['Note1', 'Note2', 'Note3']
        column3_fields = ['Källa1', 'Källa2', 'Källa3', 'Historiskt']  # Updated from "Korrelerande historisk händelse"
        
        # Add remaining columns to column 3
        for col_name in column_names:
            if col_name not in column1_fields and col_name not in column2_fields and col_name not in column3_fields:
                column3_fields.append(col_name)
        
        # Configure column weights for equal spacing - each column gets exactly 1/3 of available width
        # Use uniform to force exactly equal column distribution
        fields_container.grid_columnconfigure(0, weight=1, uniform="col")  # Left column - 1/3 of width
        fields_container.grid_columnconfigure(1, weight=1, uniform="col")  # Middle column - 1/3 of width  
        fields_container.grid_columnconfigure(2, weight=1, uniform="col")  # Right column - 1/3 of width
        
        # Create Column 1
        if any(col in column_names for col in column1_fields):
            col1_frame = tb.LabelFrame(fields_container, text="Grundläggande information", padding=5)
            col1_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            col1_frame.grid_columnconfigure(0, weight=0)  # Field labels - fixed width
            col1_frame.grid_columnconfigure(1, weight=1)  # Entry fields - expand to fill space
            col1_frame.grid_columnconfigure(2, weight=0)  # Lock switches - fixed width
            
            row = 0
            for col_name in column1_fields:
                if col_name in column_names:
                    rows_used = self.create_field_in_frame(col1_frame, col_name, row, column_type="column1")
                    row += rows_used
        
        # Create Column 2
        if any(col in column_names for col in column2_fields):
            col2_frame = tb.LabelFrame(fields_container, text="Anteckningar", padding=5)
            col2_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
            col2_frame.grid_columnconfigure(0, weight=1)  # Make all content expand full width
            
            row = 0
            for col_name in column2_fields:
                if col_name in column_names:
                    rows_used = self.create_field_in_frame(col2_frame, col_name, row, column_type="column2")
                    row += rows_used
        
        # Create Column 3
        if column3_fields:
            col3_frame = tb.LabelFrame(fields_container, text="Källor och övrigt", padding=5)
            col3_frame.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
            col3_frame.grid_columnconfigure(0, weight=1)  # Make all content expand full width
            
            row = 0
            for col_name in column3_fields:
                if col_name in column_names:
                    rows_used = self.create_field_in_frame(col3_frame, col_name, row, column_type="column3")
                    row += rows_used
    
    def create_field_in_frame(self, parent_frame, col_name, row, column_type="column1"):
        """Create a single field in the specified frame with layout optimized per column type"""
        # Check if this field should have a lock switch (all except Dag, Händelse and Inlagd datum)
        has_lock = col_name in self.lock_vars
        
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
            
        # Special handling for Inlagd datum - read-only, always today's date
        elif col_name == 'Inlagd datum':
            # Standard horizontal layout for Inlagd datum field
            tb.Label(parent_frame, text=f"{col_name}:", 
                    font=('Arial', 10)).grid(row=row, column=0, sticky="w", pady=(0, 5))
            
            entry = tb.Entry(parent_frame, textvariable=self.excel_vars[col_name], 
                           state="readonly", 
                           font=('Arial', 9))
            entry.grid(row=row, column=1, sticky="ew", pady=(0, 5))
            
            # Return 1 row used for Inlagd datum field
            return 1
            
        # Special vertical layout for text fields with character counters (Händelse, Note1-3)
        elif col_name.startswith('Note') or col_name == 'Händelse':
            # Row 1: Field name and lock switch (if applicable)
            header_frame = tb.Frame(parent_frame)
            header_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))
            
            tb.Label(header_frame, text=f"{col_name}:", 
                    font=('Arial', 10)).pack(side="left")
            
            # Add lock switch for text fields that should have one
            if has_lock and col_name != 'Händelse':
                lock_switch = tb.Checkbutton(header_frame, 
                                           text="Lås", 
                                           variable=self.lock_vars[col_name],
                                           bootstyle="success-round-toggle")
                lock_switch.pack(side="right")
            
            # Row 2: Text widget (full width)
            if col_name == 'Händelse':
                height = 8
            elif col_name in ['Note1', 'Note2']:
                height = 6
            else:
                height = 4
            
            text_widget = tk.Text(parent_frame, height=height, 
                                wrap=tk.WORD, font=('Arial', 9),
                                undo=True, maxundo=20)
            text_widget.grid(row=row+1, column=0, columnspan=2, sticky="ew", pady=(0, 2))
            
            # Enable undo functionality for text widget
            self.enable_undo_for_widget(text_widget)
            
            # Bind character count checking and paste handling
            text_widget.bind('<KeyRelease>', 
                           lambda e, col=col_name: self.check_character_count(e, col))
            text_widget.bind('<Button-1>', 
                           lambda e, col=col_name: self.root.after(1, lambda: self.check_character_count(e, col)))
            text_widget.bind('<Control-v>', 
                           lambda e, col=col_name: self.handle_paste_event(e, col))
            text_widget.bind('<<Paste>>', 
                           lambda e, col=col_name: self.handle_paste_event(e, col))
            
            # Add improved undo handling for key presses that replace selected text
            text_widget.bind('<KeyPress>', 
                           lambda e: self.handle_text_key_press_undo(e))
            
            # Specific binding for Delete key to handle selection deletion
            text_widget.bind('<Delete>', 
                           lambda e: self.handle_delete_key_undo(e))
            text_widget.bind('<BackSpace>', 
                           lambda e: self.handle_delete_key_undo(e))
            

            
            # Row 3: Character counter (left aligned, compact)
            counter_label = tb.Label(parent_frame, text=f"{self.char_limit}", 
                                   font=('Arial', 8), bootstyle="success")
            counter_label.grid(row=row+2, column=0, sticky="w", pady=(0, 5))
            self.char_counters[col_name] = counter_label
            
            # Store reference to text widget
            self.excel_vars[col_name] = text_widget
            
            # Return the number of rows used (3 rows for text fields)
            return 3
            
        # Layout depends on column type
        elif column_type == "column1":
            # Horizontal layout for column 1 - saves vertical space
            tb.Label(parent_frame, text=f"{col_name}:", 
                    font=('Arial', 10)).grid(row=row, column=0, sticky="w", pady=(0, 5))
            
            entry = tb.Entry(parent_frame, textvariable=self.excel_vars[col_name], 
                           font=('Arial', 9))
            entry.grid(row=row, column=1, sticky="ew", pady=(0, 5))
            
            # Enable undo tracking for Entry widget
            self.enable_undo_for_widget(entry)
            
            # Add lock switch for fields that should have one (in column 2)
            if has_lock:
                lock_switch = tb.Checkbutton(parent_frame, 
                                           text="Lås", 
                                           variable=self.lock_vars[col_name],
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
                                           variable=self.lock_vars[col_name],
                                           bootstyle="success-round-toggle")
                lock_switch.pack(side="right")
            
            # Row 2: Entry field (full width)
            entry = tb.Entry(parent_frame, textvariable=self.excel_vars[col_name], 
                           font=('Arial', 9))
            entry.grid(row=row+1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
            
            # Enable undo tracking for Entry widget
            self.enable_undo_for_widget(entry)
            
            # Return 2 rows used for vertical layout
            return 2
        
        # Configure column weight for proper resizing (for all field types)
        parent_frame.grid_columnconfigure(0, weight=1)
        if parent_frame.grid_size()[0] > 1:  # If there are multiple columns
            parent_frame.grid_columnconfigure(1, weight=1)
    
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
            
            # Update statistics
            self.stats['pdfs_opened'] += 1
            self.update_stats_display()
            
            logger.info(f"Loaded PDF: {filename}, Pages: {self.current_pdf_pages}")
    
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
                self.config['excel_file'] = working_path
                self.create_excel_fields()
                # Enable the "Open Excel" button after successful load
                self.open_excel_btn.config(state="normal")
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
            self.open_excel_btn.config(state="disabled")
            return
        
        try:
            PDFProcessor.open_excel_externally(self.excel_manager.excel_path)
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna Excel-fil: {str(e)}")
    
    def show_excel_help(self):
        """Show help dialog for Excel file requirements"""
        help_win = tb.Toplevel()
        help_win.title("Excel-fil hjälp")
        help_win.geometry("600x600")  # Increased from 500 to 600 (20% increase)
        help_win.transient(self.root)
        help_win.grab_set()
        
        # Center dialog
        help_win.update_idletasks()
        x = (help_win.winfo_screenwidth() // 2) - (600 // 2)
        y = (help_win.winfo_screenheight() // 2) - (600 // 2)  # Updated for new height
        help_win.geometry(f"600x600+{x}+{y}")
        
        # Main frame
        main_frame = tb.Frame(help_win)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        tb.Label(main_frame, text="Excel-fil krav", 
                font=('Arial', 14, 'bold')).pack(pady=(0, 15))
        
        # Requirements text (updated with new field name)
        req_text = """För att applikationen ska fungera korrekt måste Excel-filen innehålla följande kolumnnamn (exakt stavning krävs):

OBLIGATORISKA KOLUMNER:
• OBS
• Inlagd datum
• Kategori  
• Underkategori
• Person/sak
• Egen grupp
• Händelse
• Dag
• Tid start
• Tid slut
• Note1
• Note2
• Note3
• Källa1
• Källa2
• Källa3
• Historiskt

VIKTIGT:
- Kolumnnamnen måste vara exakt som ovan (inklusive stora/små bokstäver)
- Kolumnnamnen ska finnas på första raden i Excel-filen
- Ordningen på kolumnerna spelar ingen roll
- Du kan ha ytterligare kolumner, de ignoreras av applikationen

Applikationen kommer automatiskt att fylla i vissa fält baserat på PDF-filnamnet."""
        
        # Scrollable text area
        text_frame = tb.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                            font=('Arial', 10), height=15)
        text_area.pack(fill="both", expand=True)
        text_area.insert("1.0", req_text)
        text_area.config(state=tk.DISABLED)
        
        # Buttons frame
        buttons_frame = tb.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Create template button
        template_btn = tb.Button(buttons_frame, text="Skapa mall-Excel med rätt kolumner",
                               command=lambda: self.create_excel_template(help_win),
                               bootstyle=SUCCESS, width=35)
        template_btn.pack(side="left", padx=(0, 10))
        ToolTip(template_btn, "Skapar en ny Excel-fil med alla nödvändiga kolumner fördefinierade. " +
                             "Filerna får rätt formatering och några exempel-formler för Dag-kolumnen.")
        
        # Close button
        close_btn = tb.Button(buttons_frame, text="Stäng",
                            command=help_win.destroy,
                            bootstyle=SECONDARY, width=15)
        close_btn.pack(side="right")
    
    def create_excel_template(self, parent_window=None):
        """Create a new Excel file with the correct column headers"""
        try:
            # Ask user where to save the template
            template_path = filedialog.asksaveasfilename(
                title="Spara Excel-mall som...",
                defaultextension=".xlsx",
                filetypes=[("Excel-filer", "*.xlsx")],
                initialfile="Timeline_mall.xlsx"
            )
            
            if not template_path:
                return
            
            # Create new workbook
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Timeline"
            
            # Define column headers in the specified order (updated with new field name)
            headers = [
                "OBS", "Inlagd datum", "Kategori", "Underkategori", "Person/sak", 
                "Egen grupp", "Händelse", "Dag", "Tid start", "Tid slut",
                "Note1", "Note2", "Note3", "Källa1", "Källa2", "Källa3",
                "Historiskt"  # Updated from "Korrelerande historisk händelse"
            ]
            
            # Add headers to first row
            for col_idx, header in enumerate(headers, 1):
                ws.cell(row=1, column=col_idx, value=header)
            
            # Style the header row and set up column formatting
            from openpyxl.styles import Font, PatternFill, Alignment
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.font = header_font
                cell.fill = header_fill
                
                # Set up column-specific formatting for the entire column
                column_letter = cell.column_letter
                
                if header == 'OBS':
                    # Text format for OBS column - ensure it's formatted as text
                    pass  # Formatting will be applied when data is added
                elif header in ['Tid start', 'Tid slut']:
                    # Date format for date columns - don't pre-format empty rows
                    pass  # Formatting will be applied when data is added
                elif header == 'Dag':
                    # Day format for Dag column - formula will be added when data is added
                    pass  # Formatting will be applied when data is added
                elif header.startswith('Note') or header == 'Händelse':
                    # Text wrapping for text fields - don't pre-format empty rows
                    pass  # Formatting will be applied when data is added
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Max width 50
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Save the workbook
            wb.save(template_path)
            
            # Success message with option to open the created file
            result = messagebox.askyesno(
                "Mall skapad",
                f"Excel-mallen har skapats:\n{Path(template_path).name}\n\n" +
                "Vill du öppna mallen direkt i applikationen?"
            )
            
            if result:
                # Close help window if it exists
                if parent_window:
                    parent_window.destroy()
                
                # Load the created template
                if self.excel_manager.load_excel_file(template_path):
                    self.excel_path_var.set(Path(template_path).name)
                    self.config['excel_file'] = template_path
                    self.create_excel_fields()
                    # Enable the "Open Excel" button for newly created template
                    self.open_excel_btn.config(state="normal")
                    logger.info(f"Loaded created template: {template_path}")
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte skapa Excel-mall: {str(e)}")
            logger.error(f"Error creating Excel template: {e}")
    
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
            # Skip automatically calculated fields and Inlagd datum (will be preserved)
            if col_name == 'Dag' or col_name == 'Inlagd datum':
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
        
        # Clear all Excel fields first (except locked ones and Inlagd datum)
        for col_name, var in self.excel_vars.items():
            # Skip locked fields and automatically calculated fields
            if col_name in self.lock_vars and self.lock_vars[col_name].get():
                continue
            if col_name == 'Dag':  # Skip automatically calculated fields
                continue
            if col_name == 'Inlagd datum':  # Skip Inlagd datum to preserve today's date
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
        
        if 'Tid start' in self.excel_vars and date:
            # Only set if not locked
            if not (self.lock_vars.get('Tid start', tk.BooleanVar()).get()):
                self.excel_vars['Tid start'].set(date)
        
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
        
        # Check if file is locked by another application
        if PDFProcessor.is_file_locked(self.current_pdf_path):
            messagebox.showerror("Fil låst", 
                               "PDF-filen används av ett annat program. " +
                               "Stäng programmet och försök igen.")
            return False
        
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
        
        # Determine target directory and check permissions
        if self.move_to_subfolder_var.get():
            subfolder_path = old_file.parent / "Omdöpta filer"
            
            # Check parent directory permissions first
            can_write, perm_error = PDFProcessor.check_directory_permissions(str(old_file.parent))
            if not can_write:
                messagebox.showerror("Fel", f"Kan inte skapa undermapp: {perm_error}")
                return False
            
            try:
                subfolder_path.mkdir(exist_ok=True)
                logger.info(f"Created/verified subfolder: {subfolder_path}")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte skapa underkatalog: {str(e)}")
                return False
            
            # Check subfolder permissions
            can_write, perm_error = PDFProcessor.check_directory_permissions(str(subfolder_path))
            if not can_write:
                messagebox.showerror("Fel", f"Kan inte skriva till undermapp: {perm_error}")
                return False
            
            new_path = subfolder_path / new_filename
        else:
            # Check current directory permissions
            can_write, perm_error = PDFProcessor.check_directory_permissions(str(old_file.parent))
            if not can_write:
                messagebox.showerror("Fel", f"Kan inte skriva till mappen: {perm_error}")
                return False
            
            new_path = old_file.parent / new_filename
        
        # Check if target file already exists
        if new_path.exists() and str(new_path) != str(old_file):
            # Check if target file is locked
            if PDFProcessor.is_file_locked(str(new_path)):
                messagebox.showerror("Fel", 
                                   f"Målfilen '{new_filename}' är låst av ett annat program. " +
                                   "Stäng programmet och försök igen.")
                return False
            
            result = messagebox.askyesno("Filen finns redan", 
                                       f"Filen '{new_filename}' finns redan. Vill du skriva över den?")
            if not result:
                return False        
        # Attempt to rename/move
        try:
            if self.move_to_subfolder_var.get():
                # Move to subfolder
                old_file.replace(new_path)  # replace() overwrites if target exists
                logger.info(f"Moved and renamed: {old_file.name} -> Omdöpta filer/{new_filename}")
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
        """Check if Excel row should be saved based on any significant content"""
        if not self.excel_vars:
            return False
        
        # Check if any important field has content
        important_fields = ['Tid start', 'Händelse', 'OBS', 'Kategori', 'Underkategori', 
                           'Person/sak', 'Egen grupp', 'Tid slut', 'Note1', 'Note2', 'Note3',
                           'Källa1', 'Källa2', 'Källa3', 'Historiskt']
        
        for field_name in important_fields:
            if field_name in self.excel_vars:
                var = self.excel_vars[field_name]
                if hasattr(var, 'get'):
                    content = ""
                    if hasattr(var, 'delete'):  # Text widget
                        content = var.get("1.0", tk.END).strip()
                    else:  # StringVar or Entry
                        content = var.get().strip()
                    
                    if content:  # If any field has content, save the row
                        return True
        
        return False
    
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
                    raw_text = var.get("1.0", tk.END).strip()
                    # Clean PDF text for text fields that commonly contain pasted PDF content
                    if col_name in ['Händelse', 'Note1', 'Note2', 'Note3']:
                        excel_data[col_name] = FilenameParser.clean_pdf_text(raw_text)
                    else:
                        excel_data[col_name] = raw_text
                else:  # It's a StringVar (Entry widget)
                    excel_data[col_name] = var.get()
            else:
                excel_data[col_name] = ""
        
        # Handle Inlagd datum - always set today's date (field is read-only)
        if 'Inlagd datum' in self.excel_vars:
            excel_data['Inlagd datum'] = datetime.now().strftime('%Y-%m-%d')
        
        # Get filename for special handling
        filename = excel_data.get('Källa1', '')
        if not filename:
            # Only construct filename if we have actual content from PDF filename components
            date = self.date_var.get().strip()
            newspaper = self.newspaper_var.get().strip()
            comment = self.comment_var.get().strip()
            pages = self.pages_var.get().strip();
            
            # Only create filename if we have at least date or newspaper (indicating PDF was loaded)
            if date or newspaper:
                filename = FilenameParser.construct_filename(date, newspaper, comment, pages)
            else:
                filename = ""  # No filename if no PDF components exist
        
        # Add filename components for special handling
        excel_data['date'] = self.date_var.get()
        
        if self.excel_manager.add_row(excel_data, filename, self.row_color_var.get()):
            self.stats['excel_rows_added'] += 1
            self.excel_row_saved.set(True)
            self.update_stats_display()
            logger.info(f"Added Excel row with data for: {filename}")
            return True
        else:
            return False
    
    def clear_excel_fields(self):
        """Clear Excel fields except locked ones and Inlagd datum"""
        for col_name, var in self.excel_vars.items():
            # Skip locked fields
            if col_name in self.lock_vars and self.lock_vars[col_name].get():
                continue
            # Skip Inlagd datum - it should always maintain today's date
            if col_name == 'Inlagd datum':
                continue
                
            if hasattr(var, 'delete'):  # Text widget
                var.delete("1.0", tk.END)
                # Reset character counter for text fields
                if col_name in self.char_counters:
                    self.char_counters[col_name].config(text=f"Tecken kvar: {self.char_limit}", bootstyle="success")
            else:  # StringVar
                var.set("")
    
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
        # Check for potential missing date when user has entered event info
        if not self.validate_excel_data_before_save():
            return  # User chose to cancel and fix the issue
        
        # Check if Excel file exists before proceeding
        if self.excel_manager.excel_path and not Path(self.excel_manager.excel_path).exists():
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
            # If result is False (No), continue without Excel saving
        
        operations_performed = []
        
        # 1. Rename PDF file if filename has changed
        if self.current_pdf_path and self.has_filename_changed():
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
                        result = messagebox.askyesno("Filnamnändring misslyckades", 
                                                   "PDF-filen kunde inte döpas om. " +
                                                   "Vill du ändå fortsätta med att spara Excel-raden?")
                        if not result:
                            return
                else:  # Yes - continue without rename
                    pass  # Skip rename, continue with Excel
            else:
                # File exists, proceed with rename
                if self.rename_current_pdf():
                    operations_performed.append("PDF-filen har döpts om")
                else:
                    # If rename failed, ask user if they want to continue with Excel save
                    result = messagebox.askyesno("Filnamnändring misslyckades", 
                                               "PDF-filen kunde inte döpas om. " +
                                               "Vill du ändå fortsätta med att spara Excel-raden?")
                    if not result:
                        return
        
        # 2. Save Excel row if required data exists AND Excel file is available
        if self.should_save_excel_row():
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
        
        # 3. Clear Excel fields
        self.clear_excel_fields()
        
        # 4. Clear PDF and filename fields
        self.clear_pdf_and_filename_fields()
        
        # 5. Reset row color to default
        self.row_color_var.set("none")
        
        operations_performed.append("alla fält har rensats (utom låsta)")
        
        # Show result message
        if operations_performed:
            message = "Följande operationer genomfördes:\n• " + "\n• ".join(operations_performed)
            messagebox.showinfo("Sparat", message)
        else:
            messagebox.showinfo("Inget att spara", 
                              "Inga ändringar att spara (alla fält var tomma eller oförändrade). " +
                              "Alla fält har rensats.")
    
    def validate_excel_data_before_save(self) -> bool:
        """Validate Excel data before saving and warn user of potential issues"""
        if not self.excel_vars:
            return True  # No Excel file loaded, nothing to validate
        
        # Check if Händelse has content
        handelse_content = ""
        if 'Händelse' in self.excel_vars:
            if hasattr(self.excel_vars['Händelse'], 'get'):
                if hasattr(self.excel_vars['Händelse'], 'delete'):  # Text widget
                    handelse_content = self.excel_vars['Händelse'].get("1.0", tk.END).strip()
                else:  # StringVar
                    handelse_content = self.excel_vars['Händelse'].get().strip()
        
        # Check if Tid start has content
        tid_start_content = ""
        if 'Tid start' in self.excel_vars:
            if hasattr(self.excel_vars['Tid start'], 'get'):
                tid_start_content = self.excel_vars['Tid start'].get().strip()
        
        # Warning if Händelse has content but Tid start is missing
        if handelse_content and not tid_start_content:
            result = messagebox.askyesno(
                "Saknas datum?",
                "Du har fyllt i 'Händelse' men inte 'Tid start' (datum).\n\n" +
                "Excel-raden kommer att sparas, men utan datum blir det svårt att sortera och hitta händelsen senare.\n\n" +
                "Vill du:\n" +
                "• JA - Fortsätta och spara utan datum\n" +
                "• NEJ - Avbryta så du kan fylla i datum"
            )
            
            if result is False:  # No - let user add date
                # Focus on Tid start field if possible
                if 'Tid start' in self.excel_vars and hasattr(self.excel_vars['Tid start'], 'focus'):
                    self.excel_vars['Tid start'].focus()
                return False
            # If result is True (Yes), continue and save row even without date
        
        return True  # Validation passed or user chose to continue
    
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
        self.clear_excel_fields()
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
        remaining = self.char_limit - char_count
        
        # Update counter display
        if column_name in self.char_counters:
            counter_label = self.char_counters[column_name]
            
            # Color coding based on remaining characters
            if remaining >= 200:
                color = "green"
                style = "success"
            elif remaining >= 50:
                color = "orange"
                style = "warning"
            else:
                color = "red"
                style = "danger"
            
            counter_label.config(text=f"Tecken kvar: {remaining}", bootstyle=style)
        
        # Hard limit enforcement
        if char_count > self.char_limit:
            # Truncate to exact limit
            truncated_content = content[:self.char_limit]
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", truncated_content)
            
            # Update counter to show 0
            if column_name in self.char_counters:
                self.char_counters[column_name].config(text="Tecken kvar: 0", bootstyle="danger")
    
    def handle_paste_event(self, event, column_name):
        """Handle paste events with length checking and smart splitting"""
        try:
            # Get the text widget
            text_widget = event.widget
            
            # Create undo separator BEFORE any paste operation for Text widgets
            if isinstance(text_widget, tk.Text):
                try:
                    text_widget.edit_separator()
                    logger.info(f"Added undo separator before paste in {column_name}")
                except tk.TclError:
                    pass
            
            # Get clipboard content
            clipboard_content = self.root.clipboard_get()
            
            # Check if clipboard content exceeds limit
            if len(clipboard_content) <= self.char_limit:
                # Normal paste - let it proceed but ensure undo separator was added
                logger.info(f"Normal paste in {column_name}: {len(clipboard_content)} chars")
                return False  # Don't block the event
            
            # Content is too long - offer options
            dialog_win = tb.Toplevel()
            dialog_win.title("Text för lång")
            dialog_win.geometry("650x325")
            dialog_win.transient(self.root)
            dialog_win.grab_set()
            
            # Center dialog
            dialog_win.update_idletasks()
            x = (dialog_win.winfo_screenwidth() // 2) - (650 // 2)
            y = (dialog_win.winfo_screenheight() // 2) - (325 // 2)
            dialog_win.geometry(f"650x325+{x}+{y}")
            
            # Dialog result variable
            dialog_result = [None]  # Use list to allow modification in nested functions
            
            # Main frame
            main_frame = tb.Frame(dialog_win)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Message
            message_text = (f"Den inklistrade texten är {len(clipboard_content)} tecken lång, "
                          f"vilket överstiger gränsen på {self.char_limit} tecken.\n\n"
                          f"Vad vill du göra?")
            tb.Label(main_frame, text=message_text, font=('Arial', 10), 
                    wraplength=580, justify="left").pack(pady=(0, 20))
            
            # Button frame
            button_frame = tb.Frame(main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            def on_truncate():
                dialog_result[0] = 'truncate'
                dialog_win.destroy()
            
            def on_split():
                dialog_result[0] = 'split'
                dialog_win.destroy()
            
            def on_cancel():
                dialog_result[0] = 'cancel'
                dialog_win.destroy()
            
            # Buttons with clear labels
            tb.Button(button_frame, text="Klipp av texten (första 1000 tecken)",
                     command=on_truncate, bootstyle=WARNING, width=35).pack(pady=(0, 5))
            
            tb.Button(button_frame, text="Dela upp på flera fält",
                     command=on_split, bootstyle=INFO, width=35).pack(pady=(0, 5))
            
            tb.Button(button_frame, text="Avbryt inklistring",
                     command=on_cancel, bootstyle=SECONDARY, width=35).pack(pady=(0, 5))
            
            # Wait for dialog to close
            dialog_win.wait_window()
            result = dialog_result[0]
            
            if result == 'cancel':  # Cancel
                return True  # Block the paste
            elif result == 'truncate':  # Truncate - paste first 1000 characters
                truncated_content = clipboard_content[:self.char_limit]
                text_widget = event.widget
                
                # Add undo separator before making changes
                if isinstance(text_widget, tk.Text):
                    try:
                        text_widget.edit_separator()
                    except tk.TclError:
                        pass
                
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", truncated_content)
                
                # Add undo separator after making changes
                if isinstance(text_widget, tk.Text):
                    try:
                        text_widget.edit_separator()
                    except tk.TclError:
                        pass
                
                self.check_character_count(event, column_name)
                return True  # Block the original paste
            elif result == 'split':  # Split - try to split across fields
                return self.handle_text_splitting(clipboard_content, column_name)
            else:  # No dialog result (dialog was closed)
                return True  # Block the paste
                
        except tk.TclError:
            # No clipboard content
            return False
    
    def handle_text_splitting(self, text_content, start_column):
        """Handle splitting long text across multiple text fields"""
        # Define the text fields in order for splitting
        text_fields_order = ['Händelse', 'Note1', 'Note2', 'Note3']
        
        # Find starting position
        try:
            start_idx = text_fields_order.index(start_column)
        except ValueError:
            messagebox.showerror("Fel", "Texdelning stöds endast för Händelse, Note1, Note2 och Note3")
            return True  # Block paste
        
        # Get available fields from start position onwards
        available_fields = text_fields_order[start_idx:]
        
        # Check if any target fields have content and warn user
        fields_with_content = []
        for field_name in available_fields:
            if field_name in self.excel_vars:
                widget = self.excel_vars[field_name]
                if hasattr(widget, 'get'):
                    content = widget.get("1.0", tk.END).strip()
                    if content:
                        fields_with_content.append(field_name)
        
        # Warn about overwriting existing content
        if fields_with_content:
            overwrite_warning = f"Följande fält innehåller redan text som kommer att skrivas över:\n• " + "\n• ".join(fields_with_content)
            confirm_overwrite = messagebox.askyesno(
                "Skriva över befintlig text?",
                f"{overwrite_warning}\n\nVill du fortsätta med texdelningen?"
            )
            if not confirm_overwrite:
                return True  # Block paste
        
        # Split text into chunks
        chunks = []
        remaining_text = text_content
        
        # Debug logging
        logger.info(f"Starting text splitting with {len(remaining_text)} characters")
        logger.info(f"First 50 chars: '{remaining_text[:50]}'")
        
        for field_name in available_fields:
            if len(remaining_text) == 0:
                break
                
            if len(remaining_text) <= self.char_limit:
                # Remaining text fits in this field
                chunks.append((field_name, remaining_text))
                logger.info(f"Final chunk for {field_name}: {len(remaining_text)} chars")
                remaining_text = ""  # Clear remaining text
                break
            else:
                # Find a good break point (try to break at word boundary)
                # Try to break at last space, newline, or punctuation within last 100 chars
                break_point = self.char_limit
                for i in range(min(100, self.char_limit)):
                    char_idx = self.char_limit - 1 - i
                    if char_idx < 0:
                        break
                    if char_idx < len(remaining_text):
                        char = remaining_text[char_idx]
                        if char in [' ', '\n', '.', '!', '?', ';', ':']:
                            # For punctuation, include it in current chunk
                            # For space/newline, don't include it in current chunk
                            if char in [' ', '\n']:
                                break_point = char_idx  # Don't include the space/newline
                            else:
                                break_point = char_idx + 1  # Include the punctuation
                            break
                
                chunk = remaining_text[:break_point].rstrip()  # Remove trailing whitespace
                chunks.append((field_name, chunk))
                
                # Debug logging
                logger.info(f"Chunk for {field_name}: {len(chunk)} chars, break_point: {break_point}")
                logger.info(f"Chunk ends with: '{chunk[-20:]}'")
                
                # Calculate actual chunk length after rstrip to avoid losing characters
                actual_chunk_length = len(chunk)
                remaining_text = remaining_text[actual_chunk_length:].lstrip() # Use actual chunk length, not break_point
                
                # More debug logging
                logger.info(f"Actual chunk length after rstrip: {actual_chunk_length}")
                logger.info(f"Remaining text starts with: '{remaining_text[:20]}'")
                logger.info(f"Remaining text length: {len(remaining_text)}")
        
        # Log final chunks summary
        for i, (field_name, chunk) in enumerate(chunks):
            logger.info(f"Final chunk {i+1} ({field_name}): {len(chunk)} chars, starts with: '{chunk[:20]}', ends with: '{chunk[-20:]}'")
        
        # Only show warning if text actually won't fit
        if remaining_text:
            # Create custom warning dialog
            warning_win = tb.Toplevel()
            warning_win.title("Text för lång")
            warning_win.geometry("650x200")
            warning_win.transient(self.root)
            warning_win.grab_set()
            
            # Center dialog
            warning_win.update_idletasks()
            x = (warning_win.winfo_screenwidth() // 2) - (650 // 2)
            y = (warning_win.winfo_screenheight() // 2) - (200 // 2)
            warning_win.geometry(f"650x200+{x}+{y}")
            
            # Main frame
            main_frame = tb.Frame(warning_win)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Warning message
            warning_text = (f"Texten är för lång för att passa i tillgängliga fält. " +
                          f"Cirka {len(remaining_text)} tecken kommer att klippas bort från slutet.")
            tb.Label(main_frame, text=warning_text, font=('Arial', 10), 
                    wraplength=580, justify="left").pack(pady=(0, 20))
            
            # OK button
            tb.Button(main_frame, text="OK",
                     command=warning_win.destroy,
                     bootstyle=PRIMARY, width=15).pack()
            
            # Wait for dialog to close
            warning_win.wait_window()
        
        # Show preview of how text will be split with meaningful excerpts
        preview_text = "Texten kommer att delas upp så här:\n\n"
        for field_name, chunk in chunks:
            # Show first and last few words to give better context
            words = chunk.split()
            if len(words) <= 10:
                preview = chunk
            else:
                first_words = ' '.join(words[:5])
                last_words = ' '.join(words[-5:])
                preview = f"{first_words} ... {last_words}"
            preview_text += f"• {field_name}: \"{preview}\" ({len(chunk)} tecken)\n"
        
        # Create custom dialog for split confirmation
        dialog_win = tb.Toplevel()
        dialog_win.title("Bekräfta textuppdelning")
        dialog_win.geometry("650x400")
        dialog_win.transient(self.root)
        dialog_win.grab_set()
        
        # Center dialog
        dialog_win.update_idletasks()
        x = (dialog_win.winfo_screenwidth() // 2) - (650 // 2)
        y = (dialog_win.winfo_screenheight() // 2) - (400 // 2)
        dialog_win.geometry(f"650x400+{x}+{y}")
        
        # Dialog result variable
        confirm_result = [False]
        
        # Main frame
        main_frame = tb.Frame(dialog_win)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Message with scrollable text area
        text_frame = tb.Frame(main_frame)
        text_frame.pack(fill="x", pady=(0, 15))
        
        import tkinter.scrolledtext as scrolledtext
        text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                            font=('Arial', 10), height=10, width=70)
        text_area.pack(fill="both")
        text_area.insert("1.0", preview_text + "\nFortsätt med denna uppdelning?")
        text_area.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        def on_yes():
            confirm_result[0] = True
            dialog_win.destroy()
        
        def on_no():
            confirm_result[0] = False
            dialog_win.destroy()
        
        tb.Button(button_frame, text="Ja, fortsätt med uppdelning",
                 command=on_yes, bootstyle=SUCCESS, width=25).pack(side="left", padx=(0, 10))
        
        tb.Button(button_frame, text="Nej, avbryt",
                 command=on_no, bootstyle=SECONDARY, width=15).pack(side="left")
        
        # Wait for dialog to close
        dialog_win.wait_window()
        confirm_split = confirm_result[0]
        
        if confirm_split:
            # Apply the split text to fields
            for field_name, chunk in chunks:
                if field_name in self.excel_vars:
                    widget = self.excel_vars[field_name]
                    if hasattr(widget, 'delete'):
                        # Add undo separator before making changes (for Text widgets)
                        if isinstance(widget, tk.Text):
                            try:
                                widget.edit_separator()
                            except tk.TclError:
                                pass
                
                        # Temporarily unbind paste events to prevent conflicts
                        old_ctrl_v_binding = widget.bind('<Control-v>')
                        old_paste_binding = widget.bind('<<Paste>>')
                        widget.unbind('<Control-v>')
                        widget.unbind('<<Paste>>')
                        
                        # Force widget to update and clear any pending events
                        widget.delete("1.0", tk.END)
                        widget.update_idletasks()  # Process any pending GUI events
                        
                        # Insert the chunk
                        widget.insert("1.0", chunk)
                        widget.update_idletasks()  # Process insertion
                        
                        # Add undo separator after making changes (for Text widgets)
                        if isinstance(widget, tk.Text):
                            try:
                                widget.edit_separator()
                            except tk.TclError:
                                pass
                        
                        # Restore paste event bindings
                        if old_ctrl_v_binding:
                            widget.bind('<Control-v>', lambda e, col=field_name: self.handle_paste_event(e, col))
                        if old_paste_binding:
                            widget.bind('<<Paste>>', lambda e, col=field_name: self.handle_paste_event(e, col))
                        
                        # Debug logging to verify what was actually inserted
                        actual_content = widget.get("1.0", tk.END).strip()
                        logger.info(f"Inserted into {field_name}: {len(actual_content)} chars")
                        logger.info(f"Actual content starts with: '{actual_content[:20]}'")
                        logger.info(f"Actual content ends with: '{actual_content[-20:]}'")
                        
                        # Update character counter
                        fake_event = type('FakeEvent', (), {'widget': widget})()
                        self.check_character_count(fake_event, field_name)
                        
                        # Schedule a delayed verification to catch any interference
                        self.root.after(100, lambda w=widget, fn=field_name, c=chunk: self.verify_insertion(w, fn, c))
        
        return True  # Block the original paste
    
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
        """Handle key press in Text widget - create undo separator when replacing selection"""
        try:
            text_widget = event.widget
            if not isinstance(text_widget, tk.Text):
                return None
            
            # Check if there's selected text that will be replaced
            has_selection = bool(text_widget.tag_ranges(tk.SEL))
            
            # Handle different key scenarios that replace text
            if has_selection:
                # Case 1: Regular printable character - replaces selection
                if (len(event.char) == 1 and event.char.isprintable()):
                    text_widget.edit_separator()
                    logger.info(f"Added undo separator before typing '{event.char}' over selection")
                
                # Case 2: Delete key - deletes selection
                elif event.keysym in ['Delete', 'BackSpace']:
                    text_widget.edit_separator()
                    logger.info(f"Added undo separator before {event.keysym} on selection")
                
                # Case 3: Enter/Return key - replaces selection with newline
                elif event.keysym in ['Return', 'KP_Enter']:
                    text_widget.edit_separator()
                    logger.info(f"Added undo separator before Enter over selection")
                
                # Case 4: Tab key - replaces selection with tab
                elif event.keysym == 'Tab':
                    text_widget.edit_separator()
                    logger.info(f"Added undo separator before Tab over selection")
            
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
    
    def handle_paste_undo(self, event):
        """Handle Ctrl+V - save current content before paste operation"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # Check if there's selected text that will be replaced
                has_selection = bool(focused_widget.tag_ranges(tk.SEL))
                
                # Or if we just did a select-all
                select_all_pending = getattr(focused_widget, '_select_all_pending', False)
                
                if has_selection or select_all_pending:
                    # Save current content to our custom undo stack
                    current_content = focused_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(focused_widget, current_content)
                    
                    logger.info("Saved undo state before paste operation")
                
                # Clear the select-all pending flag
                if hasattr(focused_widget, '_select_all_pending'):
                    delattr(focused_widget, '_select_all_pending')
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default paste to proceed
    
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
        self.filename_stats_label.config(text=self.get_stats_text())
    
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
                if col_name in ['Dag', 'Inlagd datum']:
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
        
        # Save current window geometry and locked fields before exit
        self.config['window_geometry'] = self.root.geometry()
        self.config_manager.save_config(self.config)
        
        # Save locked fields data
        self.save_locked_fields_on_exit()
        
        self.root.destroy()
    
    def setup_undo_functionality(self):
        """Setup keyboard bindings for undo/redo"""
        # Bind global keyboard shortcuts
        self.root.bind_all('<Control-z>', self.global_undo)
        self.root.bind_all('<Control-y>', self.global_redo)
        self.root.bind_all('<Control-Shift-Z>', self.global_redo)  # Alternative redo binding
        
        # Add enhanced bindings for Text widgets to handle problematic operations
        self.root.bind_all('<Control-a>', self.handle_select_all_undo)
        self.root.bind_all('<Control-v>', self.handle_paste_undo)
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
                widget.config(undo=True, maxundo=20)
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
        """Save text widget state to custom undo stack"""
        widget_id = id(text_widget)
        
        # Initialize stacks if not exists
        if widget_id not in self.text_undo_stacks:
            self.text_undo_stacks[widget_id] = []
            self.text_redo_stacks[widget_id] = []
        
        # Add to undo stack
        self.text_undo_stacks[widget_id].append(content)
        
        # Limit stack size
        if len(self.text_undo_stacks[widget_id]) > self.max_undo_levels:
            self.text_undo_stacks[widget_id].pop(0)
        
        # Clear redo stack when new state is saved
        self.text_redo_stacks[widget_id] = []
    
    def text_widget_undo(self, text_widget):
        """Perform undo on Text widget using custom stack"""
        widget_id = id(text_widget)
        
        if widget_id not in self.text_undo_stacks or len(self.text_undo_stacks[widget_id]) < 2:
            return False
        
        undo_stack = self.text_undo_stacks[widget_id]
        redo_stack = self.text_redo_stacks[widget_id]
        
        # Save current content to redo stack (this is the state after the operation)
        current_content = text_widget.get("1.0", "end-1c")
        redo_stack.append(current_content)
        
        # Remove the current state from undo stack (this was just saved by the operation)
        undo_stack.pop()
        
        # Get the actual previous content from undo stack
        previous_content = undo_stack[-1] if undo_stack else ""
        
        # Restore content
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", previous_content)
        
        logger.info("Performed custom undo on Text widget")
        return True
    
    def text_widget_redo(self, text_widget):
        """Perform redo on Text widget using custom stack"""
        widget_id = id(text_widget)
        
        if widget_id not in self.text_redo_stacks or not self.text_redo_stacks[widget_id]:
            return False
        
        undo_stack = self.text_undo_stacks[widget_id]
        redo_stack = self.text_redo_stacks[widget_id]
        
        # Get next content from redo stack
        next_content = redo_stack.pop()
        
        # Save current content to undo stack
        current_content = text_widget.get("1.0", "end-1c")
        undo_stack.append(current_content)
        
        # Restore content
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", next_content)
        
        logger.info("Performed custom redo on Text widget")
        return True
    
    def run(self):
        """Start the application"""
        self.root.mainloop()