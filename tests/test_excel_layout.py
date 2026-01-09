#!/usr/bin/env python3
"""
Test script to reproduce and debug the Excel layout issue
Focuses specifically on the 3-column layout and gap above Händelse
"""

import customtkinter as ctk


class TestExcelLayout:
    def __init__(self):
        # Configure CustomTkinter
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Create main window
        self.root = ctk.CTk()
        self.root.title("Excel Layout Test")
        self.root.geometry("1200x600")

        self.create_layout()

    def create_layout(self):
        """Create the test layout"""

        # Main container frame
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="3. Excel-integration",
                                 font=ctk.CTkFont(size=12, weight="bold"))
        title_label.pack(anchor="w", pady=(0, 10))

        # Create the 3-column container
        fields_container = ctk.CTkFrame(main_frame, fg_color="lightgray")  # Gray background to see bounds
        fields_container.pack(fill="both", expand=True, pady=(5, 0))

        # Configure responsive row expansion
        fields_container.grid_rowconfigure(0, weight=1)

        # Configure column weights for 40/30/30 distribution
        fields_container.grid_columnconfigure(0, weight=4)  # Left column - 40%
        fields_container.grid_columnconfigure(1, weight=3)  # Middle column - 30%
        fields_container.grid_columnconfigure(2, weight=3)  # Right column - 30%

        # Create Column 1 (Left)
        col1_frame = ctk.CTkFrame(fields_container, fg_color="lightblue")  # Blue to identify
        col1_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 5), pady=2)
        col1_frame.grid_columnconfigure(1, weight=1)  # Entry fields expand

        # Add left column fields
        self.create_left_column_fields(col1_frame)

        # Create Column 2 (Middle) - PROBLEM COLUMN
        col2_frame = ctk.CTkFrame(fields_container, fg_color="lightcoral")  # Red to identify
        col2_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=2)
        col2_frame.grid_columnconfigure(0, weight=1)  # Content takes full width
        col2_frame.grid_rowconfigure(0, weight=1)  # Händelse expands to fill all available space

        # Add Händelse field to middle column
        self.create_handelse_field(col2_frame)

        # Create Column 3 (Right)
        col3_frame = ctk.CTkFrame(fields_container, fg_color="lightgreen")  # Green to identify
        col3_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 5), pady=2)
        col3_frame.grid_columnconfigure(0, weight=1)  # Content expands

        # Add right column fields
        self.create_right_column_fields(col3_frame)

    def create_left_column_fields(self, parent):
        """Create fields for the left column"""
        row = 0
        fields = ['Startdatum', 'Starttid', 'Slutdatum', 'Sluttid', 'OBS', 'Kategori']

        for field in fields:
            # Label
            label = ctk.CTkLabel(parent, text=f"{field}:", font=ctk.CTkFont(size=12))
            label.grid(row=row, column=0, sticky="w", padx=(10, 5), pady=(0, 5))

            # Entry
            entry = ctk.CTkEntry(parent, font=ctk.CTkFont(size=12))
            entry.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=(0, 5))

            # Lock checkbox
            lock = ctk.CTkCheckBox(parent, text="Lås")
            lock.grid(row=row, column=2, sticky="w", padx=(5, 10), pady=(0, 5))

            row += 1

    def create_handelse_field(self, parent):
        """Create the Händelse field that has the gap issue"""

        print("DEBUG: Creating Händelse field in parent with fg_color:", parent.cget("fg_color"))

        # Row 0: Header with label and lock
        header_frame = ctk.CTkFrame(parent, fg_color="yellow")  # Yellow to see header bounds
        header_frame.grid(row=0, column=0, columnspan=2, sticky="new", pady=(0, 2))
        print("DEBUG: Header frame placed at row=0, sticky='new', pady=(0, 2)")

        label = ctk.CTkLabel(header_frame, text="Händelse:", font=ctk.CTkFont(size=14))
        label.pack(side="left", padx=(10, 5))

        lock = ctk.CTkCheckBox(header_frame, text="Lås")
        lock.pack(side="right", padx=(5, 10))

        # Row 1: Toolbar
        toolbar_frame = ctk.CTkFrame(parent, fg_color="orange")  # Orange to see toolbar bounds
        toolbar_frame.grid(row=1, column=0, columnspan=2, sticky="nw", padx=(10, 5), pady=(2, 2))
        print("DEBUG: Toolbar frame placed at row=1, sticky='nw', pady=(2, 2)")

        # Add some dummy toolbar buttons
        for _i, color in enumerate(["blue", "red", "green"]):
            btn = ctk.CTkButton(toolbar_frame, text="B", width=30, height=25, fg_color=color)
            btn.pack(side="left", padx=2)

        # Row 2: Text widget
        text_frame = ctk.CTkFrame(parent, fg_color="lightpink")  # Pink to see text bounds
        text_frame.grid(row=2, column=0, columnspan=2, sticky="new", padx=(10, 10), pady=(0, 2))
        print("DEBUG: Text frame placed at row=2, sticky='new', pady=(0, 2)")

        # Configure the text widget row to expand vertically
        parent.grid_rowconfigure(2, weight=1)
        print("DEBUG: Set parent.grid_rowconfigure(2, weight=1)")

        text_widget = ctk.CTkTextbox(text_frame, height=100, font=('Arial', 9))
        text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        text_widget.insert("1.0", "This is the Händelse text field...")

        # Row 3: Character counter
        counter_label = ctk.CTkLabel(parent, text="1000", font=ctk.CTkFont(size=11))
        counter_label.grid(row=3, column=0, sticky="w", padx=(10, 5), pady=(5, 8))
        print("DEBUG: Counter placed at row=3")

    def create_right_column_fields(self, parent):
        """Create fields for the right column"""
        fields = ['Note1', 'Note2', 'Note3']

        for i, field in enumerate(fields):
            # Header
            header_frame = ctk.CTkFrame(parent, fg_color="transparent")
            header_frame.grid(row=i*3, column=0, sticky="ew", pady=(5, 2))

            label = ctk.CTkLabel(header_frame, text=f"{field}:", font=ctk.CTkFont(size=14))
            label.pack(side="left", padx=(10, 5))

            lock = ctk.CTkCheckBox(header_frame, text="Lås")
            lock.pack(side="right")

            # Text widget
            text_widget = ctk.CTkTextbox(parent, height=60, font=('Arial', 9))
            text_widget.grid(row=i*3+1, column=0, sticky="ew", padx=(10, 10), pady=(0, 2))

            # Counter
            counter = ctk.CTkLabel(parent, text="1000", font=ctk.CTkFont(size=11))
            counter.grid(row=i*3+2, column=0, sticky="w", padx=(10, 5), pady=(5, 8))

    def run(self):
        """Start the test application"""
        print("Starting Excel Layout Test...")
        print("Look for gaps above the Händelse field in the middle (red) column")
        print("Header should be yellow, toolbar orange, text area pink")
        self.root.mainloop()

if __name__ == "__main__":
    app = TestExcelLayout()
    app.run()
