"""
GUI Style Comparison: ttkbootstrap vs CustomTkinter
Shows both styles in tabs within a single window
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import customtkinter as ctk

# Configure CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class StyleComparison:
    def __init__(self):
        # Create main window with ttkbootstrap
        self.root = tb.Window(themename="simplex")
        self.root.title("GUI Style Comparison: ttkbootstrap vs CustomTkinter")
        self.root.geometry("1400x750")
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Create left and right frames
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 5))
        
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0))
        
        # Create ttkbootstrap demo on the left
        self.create_ttkbootstrap_demo(left_frame)
        
        # Create CustomTkinter demo on the right
        self.create_customtkinter_demo(right_frame)
        
    def create_ttkbootstrap_demo(self, parent):
        """Create ttkbootstrap styling demo"""
        # Title
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=X, pady=(0, 10))
        
        title = ttk.Label(title_frame, text="Current Style - ttkbootstrap", 
                         font=("Helvetica", 18, "bold"))
        title.pack()
        
        subtitle = ttk.Label(title_frame, text="(Your current implementation)", 
                           font=("Helvetica", 10))
        subtitle.pack()
        
        # Main content frame
        content = ttk.Frame(parent)
        content.pack(fill=BOTH, expand=YES)
        
        # File selection section
        file_frame = ttk.LabelFrame(content, text="PDF File Selection", padding=10)
        file_frame.pack(fill=X, pady=(0, 10))
        
        file_row = ttk.Frame(file_frame)
        file_row.pack(fill=X)
        
        ttk.Label(file_row, text="Selected file:").pack(side=LEFT, padx=(0, 5))
        file_entry = ttk.Entry(file_row, width=30)
        file_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        ttk.Button(file_row, text="Browse", style="primary.TButton").pack(side=LEFT)
        
        # Input fields section
        input_frame = ttk.LabelFrame(content, text="Filename Components", padding=10)
        input_frame.pack(fill=X, pady=(0, 10))
        
        # Date field
        date_row = ttk.Frame(input_frame)
        date_row.pack(fill=X, pady=2)
        ttk.Label(date_row, text="Datum:", width=10).pack(side=LEFT)
        ttk.Entry(date_row, width=20).pack(side=LEFT, padx=(0, 5))
        ttk.Checkbutton(date_row, text="Lock").pack(side=LEFT)
        
        # Source field
        source_row = ttk.Frame(input_frame)
        source_row.pack(fill=X, pady=2)
        ttk.Label(source_row, text="Källa:", width=10).pack(side=LEFT)
        ttk.Entry(source_row, width=20).pack(side=LEFT, padx=(0, 5))
        ttk.Checkbutton(source_row, text="Lock").pack(side=LEFT)
        
        # Excel fields section with formatting toolbar
        excel_frame = ttk.LabelFrame(content, text="Excel Fields", padding=10)
        excel_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        # Formatting toolbar
        toolbar = ttk.Frame(excel_frame)
        toolbar.pack(fill=X, pady=(0, 5))
        
        ttk.Button(toolbar, text="B", width=3, style="secondary.TButton").pack(side=LEFT, padx=1)
        ttk.Button(toolbar, text="Red", style="danger.TButton").pack(side=LEFT, padx=1)
        ttk.Button(toolbar, text="Green", style="success.TButton").pack(side=LEFT, padx=1)
        ttk.Button(toolbar, text="Blue", style="info.TButton").pack(side=LEFT, padx=1)
        ttk.Button(toolbar, text="T", width=3).pack(side=LEFT, padx=1)
        ttk.Button(toolbar, text="A+", width=3).pack(side=LEFT, padx=1)
        
        # Text area
        text_frame = ttk.Frame(excel_frame)
        text_frame.pack(fill=BOTH, expand=YES)
        
        text = tk.Text(text_frame, height=8, wrap=WORD)
        text.pack(side=LEFT, fill=BOTH, expand=YES)
        text.insert("1.0", "This is how your text fields look with ttkbootstrap styling.")
        
        scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Action buttons
        button_frame = ttk.Frame(content)
        button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Process PDF", style="success.TButton").pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Save to Excel", style="primary.TButton").pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", style="secondary.TButton").pack(side=LEFT, padx=5)
        
        # Progress bar example
        progress = ttk.Progressbar(content, style="success.Striped.TProgressbar", value=65)
        progress.pack(fill=X, pady=(10, 0))
        
        # Status bar
        status = ttk.Label(content, text="Ready - ttkbootstrap theme: simplex", 
                          relief=SUNKEN, font=("Helvetica", 9))
        status.pack(fill=X, pady=(5, 0))
        
    def create_customtkinter_demo(self, parent):
        """Create CustomTkinter styling demo"""
        # Create a frame to hold CustomTkinter widgets
        ctk_container = ctk.CTkFrame(parent, corner_radius=0, fg_color="transparent")
        ctk_container.pack(fill=BOTH, expand=YES)
        
        # Title
        title_frame = ctk.CTkFrame(ctk_container, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))
        
        title = ctk.CTkLabel(title_frame, text="Alternative Style - CustomTkinter", 
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack()
        
        subtitle = ctk.CTkLabel(title_frame, text="(Modern flat design with rounded corners)", 
                               font=ctk.CTkFont(size=12))
        subtitle.pack()
        
        # Main content frame
        content = ctk.CTkFrame(ctk_container, corner_radius=10)
        content.pack(fill="both", expand=True)
        
        # File selection section
        file_frame = ctk.CTkFrame(content)
        file_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(file_frame, text="PDF File Selection", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        file_row = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_row.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(file_row, text="Selected file:").pack(side="left", padx=(0, 10))
        file_entry = ctk.CTkEntry(file_row, width=250, placeholder_text="No file selected...")
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(file_row, text="Browse", width=80).pack(side="left")
        
        # Input fields section
        input_frame = ctk.CTkFrame(content)
        input_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(input_frame, text="Filename Components", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Date field
        date_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        date_row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(date_row, text="Datum:", width=60).pack(side="left")
        ctk.CTkEntry(date_row, width=180, placeholder_text="YYYY-MM-DD").pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(date_row, text="Lock", width=60).pack(side="left")
        
        # Source field
        source_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        source_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(source_row, text="Källa:", width=60).pack(side="left")
        ctk.CTkEntry(source_row, width=180, placeholder_text="Enter source...").pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(source_row, text="Lock", width=60).pack(side="left")
        
        # Excel fields section with formatting toolbar
        excel_frame = ctk.CTkFrame(content)
        excel_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        ctk.CTkLabel(excel_frame, text="Excel Fields", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Formatting toolbar
        toolbar = ctk.CTkFrame(excel_frame, fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkButton(toolbar, text="B", width=35, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="Red", width=45, fg_color="#dc3545", hover_color="#c82333").pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="Green", width=55, fg_color="#28a745", hover_color="#218838").pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="Blue", width=45, fg_color="#007bff", hover_color="#0069d9").pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="T", width=35, fg_color="gray60", hover_color="gray50").pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="A+", width=35).pack(side="left", padx=2)
        
        # Text area
        textbox = ctk.CTkTextbox(excel_frame, wrap="word", height=150)
        textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        textbox.insert("1.0", "This is how your text fields look with CustomTkinter styling. "
                              "Notice the modern scrollbar and rounded corners.")
        
        # Action buttons
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkButton(button_frame, text="Process PDF", 
                      fg_color="#28a745", hover_color="#218838").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Save to Excel").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Clear All", 
                      fg_color="gray60", hover_color="gray50").pack(side="left", padx=5)
        
        # Progress bar example
        progress = ctk.CTkProgressBar(content)
        progress.pack(fill="x", padx=15, pady=(10, 0))
        progress.set(0.65)
        
        # Status bar
        status = ctk.CTkLabel(content, text="Ready - CustomTkinter (rounded, modern design)", 
                             fg_color=("gray85", "gray20"), corner_radius=5, height=25)
        status.pack(fill="x", padx=15, pady=(10, 15))
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = StyleComparison()
    app.run()