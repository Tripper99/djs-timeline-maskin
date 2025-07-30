"""
GUI Style Comparison: ttkbootstrap vs CustomTkinter
Shows how DJs Timeline-maskin UI elements would look with different styling
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Try to import customtkinter - will need to be installed
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("light")  # or "dark"
    ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("CustomTkinter not installed. Run: pip install customtkinter")

def create_ttkbootstrap_demo():
    """Create a window showing ttkbootstrap styling (current)"""
    root = tb.Window(themename="simplex")
    root.title("Current Style - ttkbootstrap")
    root.geometry("600x700")
    
    # Main frame
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=BOTH, expand=YES)
    
    # Title
    title = ttk.Label(main_frame, text="DJs Timeline-maskin", 
                     font=("Helvetica", 16, "bold"))
    title.pack(pady=(0, 20))
    
    # File selection section
    file_frame = ttk.LabelFrame(main_frame, text="PDF File Selection", padding=10)
    file_frame.pack(fill=X, pady=(0, 10))
    
    ttk.Label(file_frame, text="Selected file:").pack(anchor=W)
    file_entry = ttk.Entry(file_frame, width=50)
    file_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
    ttk.Button(file_frame, text="Browse", style="primary.TButton").pack(side=LEFT)
    
    # Input fields section
    input_frame = ttk.LabelFrame(main_frame, text="Filename Components", padding=10)
    input_frame.pack(fill=X, pady=(0, 10))
    
    # Date field
    date_row = ttk.Frame(input_frame)
    date_row.pack(fill=X, pady=2)
    ttk.Label(date_row, text="Datum:", width=15).pack(side=LEFT)
    ttk.Entry(date_row, width=30).pack(side=LEFT, padx=(0, 5))
    ttk.Checkbutton(date_row, text="Lock").pack(side=LEFT)
    
    # Source field
    source_row = ttk.Frame(input_frame)
    source_row.pack(fill=X, pady=2)
    ttk.Label(source_row, text="Källa:", width=15).pack(side=LEFT)
    ttk.Entry(source_row, width=30).pack(side=LEFT, padx=(0, 5))
    ttk.Checkbutton(source_row, text="Lock").pack(side=LEFT)
    
    # Excel fields section with formatting toolbar
    excel_frame = ttk.LabelFrame(main_frame, text="Excel Fields", padding=10)
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
    
    text = tk.Text(text_frame, height=6, wrap=WORD)
    text.pack(side=LEFT, fill=BOTH, expand=YES)
    
    scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=text.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    text.config(yscrollcommand=scrollbar.set)
    
    # Action buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=X)
    
    ttk.Button(button_frame, text="Process PDF", style="success.TButton").pack(side=LEFT, padx=5)
    ttk.Button(button_frame, text="Save to Excel", style="primary.TButton").pack(side=LEFT, padx=5)
    ttk.Button(button_frame, text="Clear All", style="secondary.TButton").pack(side=LEFT, padx=5)
    
    # Status bar
    status = ttk.Label(main_frame, text="Ready", relief=SUNKEN)
    status.pack(fill=X, side=BOTTOM, pady=(10, 0))
    
    return root

def create_customtkinter_demo():
    """Create a window showing CustomTkinter styling (alternative)"""
    if not CTK_AVAILABLE:
        return None
        
    root = ctk.CTk()
    root.title("Alternative Style - CustomTkinter")
    root.geometry("600x700")
    
    # Main frame
    main_frame = ctk.CTkFrame(root, corner_radius=0)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title = ctk.CTkLabel(main_frame, text="DJs Timeline-maskin", 
                        font=ctk.CTkFont(size=20, weight="bold"))
    title.pack(pady=(10, 20))
    
    # File selection section
    file_frame = ctk.CTkFrame(main_frame)
    file_frame.pack(fill="x", padx=10, pady=(0, 10))
    
    ctk.CTkLabel(file_frame, text="PDF File Selection", 
                font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
    
    file_row = ctk.CTkFrame(file_frame)
    file_row.pack(fill="x", padx=10, pady=(0, 10))
    
    ctk.CTkLabel(file_row, text="Selected file:").pack(side="left", padx=(0, 10))
    file_entry = ctk.CTkEntry(file_row, width=300)
    file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    ctk.CTkButton(file_row, text="Browse", width=80).pack(side="left")
    
    # Input fields section
    input_frame = ctk.CTkFrame(main_frame)
    input_frame.pack(fill="x", padx=10, pady=(0, 10))
    
    ctk.CTkLabel(input_frame, text="Filename Components", 
                font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
    
    # Date field
    date_row = ctk.CTkFrame(input_frame)
    date_row.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(date_row, text="Datum:", width=100).pack(side="left")
    ctk.CTkEntry(date_row, width=200).pack(side="left", padx=(0, 10))
    ctk.CTkCheckBox(date_row, text="Lock", width=60).pack(side="left")
    
    # Source field
    source_row = ctk.CTkFrame(input_frame)
    source_row.pack(fill="x", padx=10, pady=(0, 10))
    ctk.CTkLabel(source_row, text="Källa:", width=100).pack(side="left")
    ctk.CTkEntry(source_row, width=200).pack(side="left", padx=(0, 10))
    ctk.CTkCheckBox(source_row, text="Lock", width=60).pack(side="left")
    
    # Excel fields section with formatting toolbar
    excel_frame = ctk.CTkFrame(main_frame)
    excel_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    ctk.CTkLabel(excel_frame, text="Excel Fields", 
                font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
    
    # Formatting toolbar
    toolbar = ctk.CTkFrame(excel_frame)
    toolbar.pack(fill="x", padx=10, pady=(0, 5))
    
    ctk.CTkButton(toolbar, text="B", width=40, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)
    ctk.CTkButton(toolbar, text="Red", width=50, fg_color="#dc3545").pack(side="left", padx=2)
    ctk.CTkButton(toolbar, text="Green", width=60, fg_color="#28a745").pack(side="left", padx=2)
    ctk.CTkButton(toolbar, text="Blue", width=50, fg_color="#007bff").pack(side="left", padx=2)
    ctk.CTkButton(toolbar, text="T", width=40).pack(side="left", padx=2)
    ctk.CTkButton(toolbar, text="A+", width=40).pack(side="left", padx=2)
    
    # Text area
    text_frame = ctk.CTkFrame(excel_frame)
    text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    textbox = ctk.CTkTextbox(text_frame, wrap="word")
    textbox.pack(fill="both", expand=True)
    
    # Action buttons
    button_frame = ctk.CTkFrame(main_frame)
    button_frame.pack(fill="x", padx=10, pady=(0, 10))
    
    ctk.CTkButton(button_frame, text="Process PDF", 
                  fg_color="#28a745").pack(side="left", padx=5)
    ctk.CTkButton(button_frame, text="Save to Excel").pack(side="left", padx=5)
    ctk.CTkButton(button_frame, text="Clear All", 
                  fg_color="gray").pack(side="left", padx=5)
    
    # Status bar
    status = ctk.CTkLabel(main_frame, text="Ready", 
                         fg_color=("gray80", "gray20"), corner_radius=5)
    status.pack(fill="x", padx=10, pady=(0, 10))
    
    return root

def main():
    """Run both demos side by side"""
    # Create ttkbootstrap window
    ttk_window = create_ttkbootstrap_demo()
    ttk_window.geometry("600x700+100+50")
    
    # Create CustomTkinter window if available
    if CTK_AVAILABLE:
        ctk_window = create_customtkinter_demo()
        if ctk_window:
            ctk_window.geometry("600x700+750+50")
    
    # Start the main loop
    ttk_window.mainloop()
    if CTK_AVAILABLE and ctk_window:
        ctk_window.mainloop()

if __name__ == "__main__":
    main()