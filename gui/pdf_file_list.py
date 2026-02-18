"""
PDF File List Panel for DJs Timeline-maskin
Shows a browsable list of PDF files from a selected folder.
"""

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from gui.utils import ToolTip

logger = logging.getLogger(__name__)


class PDFFileListPanel(ctk.CTkFrame):
    """Panel showing PDF files from a selected folder with click-to-select."""

    def __init__(self, parent, on_file_selected=None, config_manager=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._on_file_selected = on_file_selected
        self._config_manager = config_manager
        self._folder_path = ""
        self._pdf_files = []
        self._current_highlight = None  # path of currently highlighted file

        self._build_ui()

    def _build_ui(self):
        """Build the file list UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top bar: folder selection + info
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        top_frame.grid_columnconfigure(1, weight=1)

        self._folder_btn = ctk.CTkButton(
            top_frame, text="V\u00E4lj mapp", width=80, height=26,
            command=self._select_folder,
            font=ctk.CTkFont(size=11)
        )
        self._folder_btn.grid(row=0, column=0, padx=(0, 4))
        ToolTip(self._folder_btn, "V\u00E4lj en mapp med PDF-filer att visa i listan.")

        self._folder_label = ctk.CTkLabel(
            top_frame, text="Ingen mapp vald",
            font=ctk.CTkFont(size=10), text_color="gray50",
            anchor="w"
        )
        self._folder_label.grid(row=0, column=1, sticky="ew", padx=2)
        self._folder_tooltip = ToolTip(self._folder_label, "S\u00F6kv\u00E4g till den valda mappen.")

        self._count_label = ctk.CTkLabel(
            top_frame, text="", font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        self._count_label.grid(row=0, column=2, padx=(4, 2))

        self._refresh_btn = ctk.CTkButton(
            top_frame, text="\u21BB", width=30, height=26,
            command=self._refresh_list,
            font=ctk.CTkFont(size=14)
        )
        self._refresh_btn.grid(row=0, column=3, padx=(2, 0))
        ToolTip(self._refresh_btn, "Uppdatera fillistan.")

        # File list using tk.Listbox for performance and native scrolling
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self._listbox = tk.Listbox(
            list_frame,
            font=("Arial", 10),
            selectmode=tk.SINGLE,
            activestyle="none",
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightcolor="#2196F3",
            highlightbackground="#E0E0E0",
            selectbackground="#BBDEFB",
            selectforeground="#000000",
        )
        self._listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(
            list_frame, orient="vertical", command=self._listbox.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._listbox.configure(yscrollcommand=scrollbar.set)

        # Bind click events
        self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

    # ---- Public API ----

    def set_folder(self, folder_path: str):
        """Set the folder to display PDFs from."""
        if not folder_path or not Path(folder_path).is_dir():
            return

        self._folder_path = folder_path
        self._update_folder_display()
        self._scan_folder()

    def get_folder(self) -> str:
        """Return current folder path."""
        return self._folder_path

    def highlight_file(self, file_path: str):
        """Highlight a specific file in the list."""
        self._current_highlight = file_path
        if not file_path:
            self._listbox.selection_clear(0, tk.END)
            return

        filename = Path(file_path).name
        for i in range(self._listbox.size()):
            if self._listbox.get(i) == filename:
                self._listbox.selection_clear(0, tk.END)
                self._listbox.selection_set(i)
                self._listbox.see(i)
                return

    def refresh(self):
        """Refresh the file list from the current folder."""
        self._scan_folder()

    # ---- Folder operations ----

    def _select_folder(self):
        """Open folder selection dialog."""
        initial_dir = self._folder_path if self._folder_path else str(Path.home())

        folder = filedialog.askdirectory(
            title="V\u00E4lj mapp med PDF-filer",
            initialdir=initial_dir
        )

        if folder:
            self._folder_path = folder
            self._update_folder_display()
            self._scan_folder()
            self._save_folder_to_config()

    def _update_folder_display(self):
        """Update the folder path label with truncation."""
        if not self._folder_path:
            self._folder_label.configure(text="Ingen mapp vald", text_color="gray50")
            return

        path = self._folder_path
        # Truncate long paths for display
        max_display = 60
        if len(path) > max_display:
            display = "..." + path[-(max_display - 3):]
        else:
            display = path

        self._folder_label.configure(text=display, text_color=("gray20", "gray80"))
        # Update existing tooltip text (don't recreate)
        self._folder_tooltip.update_text(self._folder_path)

    def _scan_folder(self):
        """Scan the current folder for PDF files."""
        self._listbox.delete(0, tk.END)
        self._pdf_files = []

        if not self._folder_path or not Path(self._folder_path).is_dir():
            self._count_label.configure(text="")
            return

        try:
            folder = Path(self._folder_path)
            pdf_files = sorted(
                [f for f in folder.iterdir() if f.suffix.lower() == ".pdf" and f.is_file()],
                key=lambda f: f.name.lower()
            )
            self._pdf_files = [str(f) for f in pdf_files]

            for f in pdf_files:
                self._listbox.insert(tk.END, f.name)

            count = len(pdf_files)
            self._count_label.configure(text=f"{count} PDF-filer")
            logger.info(f"PDF file list: found {count} files in {self._folder_path}")

            # Re-apply highlight if set
            if self._current_highlight:
                self.highlight_file(self._current_highlight)

        except PermissionError:
            logger.warning(f"Permission denied reading folder: {self._folder_path}")
            self._count_label.configure(text="\u00C5tkomst nekad")
        except Exception as e:
            logger.error(f"Error scanning folder: {e}")
            self._count_label.configure(text="Fel vid l\u00E4sning")

    def _refresh_list(self):
        """Refresh button handler."""
        self._scan_folder()

    # ---- Selection handling ----

    def _on_listbox_select(self, event):
        """Handle listbox selection."""
        selection = self._listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self._pdf_files):
            file_path = self._pdf_files[index]
            self._current_highlight = file_path
            if self._on_file_selected:
                self._on_file_selected(file_path)

    # ---- Config persistence ----

    def _save_folder_to_config(self):
        """Save the selected folder to config."""
        if self._config_manager:
            try:
                config = self._config_manager.load_config()
                config["pdf_browse_folder"] = self._folder_path
                self._config_manager.save_config(config)
                logger.info(f"Saved PDF browse folder: {self._folder_path}")
            except Exception as e:
                logger.error(f"Failed to save PDF browse folder: {e}")

    def load_folder_from_config(self):
        """Load folder from config and populate list."""
        if self._config_manager:
            try:
                config = self._config_manager.load_config()
                folder = config.get("pdf_browse_folder", "")
                if folder and Path(folder).is_dir():
                    self._folder_path = folder
                    self._update_folder_display()
                    self._scan_folder()
            except Exception as e:
                logger.error(f"Failed to load PDF browse folder: {e}")
