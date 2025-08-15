#!/usr/bin/env python3
"""
Layout Manager for DJs Timeline-maskin
Contains layout-related methods extracted from main_window.py
"""

# Standard library imports
import logging

# GUI imports
import tkinter as tk

import customtkinter as ctk

# Local imports
from gui.utils import ToolTip

# Setup logging
logger = logging.getLogger(__name__)


class LayoutManagerMixin:
    """Mixin class containing layout-related methods for the main window"""

    def create_menu_bar(self):
        """Create menu bar with Help menu"""
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=help_menu)
        help_menu.add_command(label="Om programmet", command=self.show_program_help)
        help_menu.add_separator()
        help_menu.add_command(label="Excel-fil krav", command=self.dialog_manager.show_excel_help)

    def create_simple_section(self, parent, content_func, section_color=None):
        """Create a simple, compact section with optional background color for visual separation"""
        # Section frame with subtle background color and increased padding for better visual separation
        section_frame = ctk.CTkFrame(parent,
                                   fg_color=section_color or ("gray90", "gray20"),
                                   corner_radius=4)
        section_frame.pack(fill="x", pady=(0, 8), padx=3)  # Increased spacing between sections

        # Content frame inside section
        content_frame = ctk.CTkFrame(section_frame,
                                   fg_color="transparent")
        content_frame.pack(fill="x", pady=3, padx=4)  # Thin internal padding

        # Call the content creation function
        content_func(content_frame)

    def create_card_section(self, parent, title, content_func):
        """Create a professional card-style section with shadow effect"""
        # Outer shadow frame (creates depth effect)
        shadow_frame = ctk.CTkFrame(parent,
                                   fg_color=("#E8E8E8", "#2B2B2B"),  # Light shadow color
                                   corner_radius=12)
        shadow_frame.pack(fill="x", pady=(0, 8), padx=2)

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
        header_frame.pack(fill="x", padx=8, pady=(8, 5))

        title_label = ctk.CTkLabel(header_frame,
                                  text=title,
                                  font=ctk.CTkFont(size=12, weight="bold"),
                                  text_color=("#1A1A1A", "#FFFFFF"))
        title_label.pack(anchor="w", padx=8, pady=4)

        # Content area
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

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
        pdf_path_frame.pack(fill="x", pady=(0, 1))

        ctk.CTkLabel(pdf_path_frame, text="Vald fil:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(3, 2))
        pdf_path_entry = ctk.CTkEntry(pdf_path_frame, textvariable=self.pdf_path_var,
                                 state="readonly", font=ctk.CTkFont(size=11), width=300, height=25)
        pdf_path_entry.pack(side="left", padx=(2, 3))
        ToolTip(pdf_path_entry, "Visar namn på den valda PDF-filen. Filen öppnas automatiskt när den väljs.")

        # Select PDF button - 40% smaller
        select_pdf_btn = ctk.CTkButton(pdf_path_frame, text="Välj PDF", width=70, height=25,
                                  command=self.select_pdf_file, font=ctk.CTkFont(size=11))
        select_pdf_btn.pack(side="left", padx=(0, 5))
        ToolTip(select_pdf_btn, "Välj en PDF-fil för bearbetning. Filen öppnas automatiskt för granskning, "
                               "filnamnet parsas till komponenter och sidantalet räknas automatiskt.")

        # Output folder selection (same row)
        ctk.CTkLabel(pdf_path_frame, text="Mapp för omdöpt pdf:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(3, 2))
        self.output_folder_entry = ctk.CTkEntry(pdf_path_frame, textvariable=self.output_folder_var,
                                           state="readonly", font=ctk.CTkFont(size=11), width=250, height=25)
        self.output_folder_entry.pack(side="left", padx=(2, 3))
        ToolTip(self.output_folder_entry, "Visar mappen där omdöpta PDF-filer ska sparas. "
                                         "Fylls automatiskt med PDF-filens mapp om inte låst.")

        # Select output folder button - 40% smaller
        self.select_output_folder_btn = ctk.CTkButton(pdf_path_frame, text="Välj mapp", width=70, height=25,
                                                 command=self.select_output_folder, font=ctk.CTkFont(size=11))
        self.select_output_folder_btn.pack(side="left", padx=(0, 3))
        ToolTip(self.select_output_folder_btn, "Välj en mapp för omdöpta PDF-filer.")

        # Lock switch for output folder - compact with lock symbol
        self.output_folder_lock_switch = ctk.CTkCheckBox(pdf_path_frame, text="🔒", width=18,
                                                       variable=self.output_folder_lock_var,
                                                       command=self.on_output_folder_lock_change,
                                                       font=ctk.CTkFont(size=12))
        self.output_folder_lock_switch.pack(side="left", padx=(2, 0))
        ToolTip(self.output_folder_lock_switch, "När låst: mappvalet ändras inte när ny PDF väljs. "
                                               "När olåst: mappvalet uppdateras automatiskt till PDF-filens mapp.")

        # Open folder button - 40% smaller
        self.open_folder_btn = ctk.CTkButton(pdf_path_frame, text="Öppna", width=50, height=25,
                                        command=self.open_output_folder, fg_color="#28a745", font=ctk.CTkFont(size=10))
        self.open_folder_btn.pack(side="left", padx=(3, 0))
        ToolTip(self.open_folder_btn, "Öppna den valda mappen i filutforskaren.")

        # Reset button - 40% smaller
        self.reset_folder_btn = ctk.CTkButton(pdf_path_frame, text="Nollställ", width=60, height=25,
                                         command=self.reset_output_folder, fg_color="#17a2b8", font=ctk.CTkFont(size=10))
        self.reset_folder_btn.pack(side="left", padx=(3, 0))
        ToolTip(self.reset_folder_btn, "Rensa mappvalet och låser upp automatisk uppdatering.")

    def create_parent_content(self, parent):
        """Group 2 Content: Filename Editing"""

        # Create grid for filename components
        components_frame = ctk.CTkFrame(parent, fg_color="transparent")
        components_frame.pack(fill="x", pady=(0, 1))

        # Date
        ctk.CTkLabel(components_frame, text="Datum:", font=ctk.CTkFont(size=11)).grid(
            row=0, column=0, sticky="w", padx=(0, 3), pady=(0, 1))
        date_entry = ctk.CTkEntry(components_frame, textvariable=self.date_var, width=100, height=25, font=ctk.CTkFont(size=11))
        date_entry.grid(row=0, column=1, sticky="w", padx=(0, 5), pady=(0, 1))
        self.enable_undo_for_widget(date_entry)

        # Newspaper
        ctk.CTkLabel(components_frame, text="Tidning:", font=ctk.CTkFont(size=11)).grid(
            row=0, column=2, sticky="w", padx=(0, 3), pady=(0, 1))
        newspaper_entry = ctk.CTkEntry(components_frame, textvariable=self.newspaper_var, width=120, height=25, font=ctk.CTkFont(size=11))
        newspaper_entry.grid(row=0, column=3, sticky="w", padx=(0, 5), pady=(0, 1))
        self.enable_undo_for_widget(newspaper_entry)

        # Pages
        ctk.CTkLabel(components_frame, text="Sidor:", font=ctk.CTkFont(size=11)).grid(
            row=0, column=4, sticky="w", padx=(0, 3), pady=(0, 1))
        pages_entry = ctk.CTkEntry(components_frame, textvariable=self.pages_var, width=50, height=25, font=ctk.CTkFont(size=11))
        pages_entry.grid(row=0, column=5, sticky="w", padx=(0, 5), pady=(0, 1))
        self.enable_undo_for_widget(pages_entry)

        # Comment
        ctk.CTkLabel(components_frame, text="Kommentar:", font=ctk.CTkFont(size=11)).grid(
            row=0, column=6, sticky="w", padx=(0, 3), pady=(0, 1))
        comment_entry = ctk.CTkEntry(components_frame, textvariable=self.comment_var, width=250, height=25, font=ctk.CTkFont(size=11))
        comment_entry.grid(row=0, column=7, sticky="w", padx=(0, 5), pady=(0, 1))
        self.enable_undo_for_widget(comment_entry)

        # Copy to Excel button with arrows - distinct color and larger to stand out
        self.copy_to_excel_btn = ctk.CTkButton(components_frame,
                                         text="↓ Kopiera ned filnamnet till Excelfältet ↓",
                                         width=220, height=30,
                                         command=self.copy_filename_to_excel,
                                         fg_color="#FF6B35", hover_color="#E55A2B",  # Orange color to stand out
                                         font=ctk.CTkFont(size=11, weight="bold"))
        self.copy_to_excel_btn.grid(row=0, column=8, sticky="w", padx=(5, 0), pady=(0, 1))
        ToolTip(self.copy_to_excel_btn, "Kopierar de parsade filnamnskomponenterna (datum, tidning, sidor, kommentar) " +
                                       "ned till Excel-fälten så du kan fortsätta redigera och lägga till mer information. " +
                                       "Detta är INTE en sparknapp - använd den för att överföra filnamnsinformation till Excel-arbetsfältet.")

    def create_group3_content(self, parent):
        """Group 3 Content: Excel Integration"""

        # Excel file selection
        excel_file_frame = ctk.CTkFrame(parent, fg_color="transparent")
        excel_file_frame.pack(fill="x", pady=(0, 1))

        ctk.CTkLabel(excel_file_frame, text="Excel-fil:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(3, 2))
        excel_path_entry = ctk.CTkEntry(excel_file_frame, textvariable=self.excel_path_var,
                                   state="readonly", font=ctk.CTkFont(size=11), width=400, height=25)
        excel_path_entry.pack(side="left", padx=(2, 3))
        ToolTip(excel_path_entry, "Visar namn på den valda Excel-filen. Programmet kommer ihåg senast använda fil.")

        # Button frame for Excel file selection and help
        excel_btn_frame = ctk.CTkFrame(excel_file_frame, fg_color="transparent")
        excel_btn_frame.pack(side="left")

        self.select_excel_btn = ctk.CTkButton(excel_btn_frame, text="Välj Excel", width=70, height=25,
                                         command=self.select_excel_file,
                                         fg_color="#17a2b8", font=ctk.CTkFont(size=11))
        self.select_excel_btn.pack(side="left", padx=(0, 2))
        ToolTip(self.select_excel_btn, "Välj Excel-fil (.xlsx) för dataintegrering. "
                                      "Du får möjlighet att skapa en säkerhetskopia att arbeta med.")

        # Open Excel button - 40% smaller
        self.open_excel_btn = ctk.CTkButton(excel_btn_frame, text="Öppna", width=60, height=25,
                                       command=self.open_excel_file,
                                       fg_color="#28a745", state="disabled", font=ctk.CTkFont(size=11))
        self.open_excel_btn.pack(side="left", padx=(0, 2))
        ToolTip(self.open_excel_btn, "Öppna den valda Excel-filen i externt program. "
                                    "Blir tillgänglig när en Excel-fil har valts.")

        # Help button - smaller
        help_btn = ctk.CTkButton(excel_btn_frame, text="?", width=25, height=25,
                           command=self.dialog_manager.show_excel_help,
                           font=ctk.CTkFont(size=11))
        help_btn.pack(side="left", padx=(0, 2))

        # Create Excel button - direct access to Excel creation from help dialog
        self.create_excel_btn = ctk.CTkButton(excel_btn_frame, text="Skapa Excel", width=80, height=25,
                                        command=self.dialog_manager.create_excel_template,
                                        fg_color="#28a745", font=ctk.CTkFont(size=10))
        self.create_excel_btn.pack(side="left")
        ToolTip(self.create_excel_btn, "Skapar en ny Excel-fil med alla nödvändiga kolumner fördefinierade. " +
                                      "Perfekt för att snabbt komma igång med nya tidslinjeprojekt.")

        # Excel column fields (scrollable, three-column layout)
        self.excel_fields_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.excel_fields_frame.pack(fill="both", expand=False, pady=(1, 0))  # Minimal padding

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
        excel_buttons_frame.pack(fill="x", pady=(0, 1))

        self.save_all_btn = ctk.CTkButton(excel_buttons_frame, text="Spara allt och rensa", width=140, height=25,
                                     command=self.save_all_and_clear,
                                     fg_color="#28a745", font=ctk.CTkFont(size=11))
        self.save_all_btn.pack(side="left", padx=(0, 3))

        self.new_excel_row_btn = ctk.CTkButton(excel_buttons_frame, text="Rensa utan spara", width=130, height=25,
                                          command=self.clear_all_without_saving,
                                          fg_color="#17a2b8", font=ctk.CTkFont(size=11))
        self.new_excel_row_btn.pack(side="left", padx=(0, 5))


        # Second row: Row color selection
        color_frame = ctk.CTkFrame(parent, fg_color="transparent")
        color_frame.pack(fill="x", pady=(1, 0))

        # Label for color selection - smaller
        color_label = ctk.CTkLabel(color_frame, text="Excelrad bakgrundsfärg:", font=ctk.CTkFont(size=10))
        color_label.pack(side="left", padx=(0, 5))

        # Colored button options for row background - 50% smaller
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
            # Create colored button with selection state - 50% smaller
            current_selection = self.row_color_var.get() if hasattr(self, 'row_color_var') else "none"
            is_selected = current_selection == value

            button = ctk.CTkButton(
                color_frame,
                text=text,
                width=40,
                height=20,  # 50% smaller
                font=ctk.CTkFont(size=9),
                fg_color=color if value != "none" else "#FFFFFF",
                hover_color=self._get_hover_color(color),
                text_color="#333333" if value != "none" else "#666666",
                border_color="#666666",
                border_width=3 if is_selected else 1,
                command=lambda v=value: self._select_row_color(v)
            )
            button.pack(side="left", padx=(0, 3))  # Reduced spacing
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
