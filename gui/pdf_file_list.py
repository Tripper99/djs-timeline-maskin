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

SORT_OPTIONS = [
    "Namn (A-Ö)",
    "Namn (Ö-A)",
    "Datum (nyast)",
    "Datum (äldst)",
    "Storlek (störst)",
    "Storlek (minst)",
]


class PDFFileListPanel(ctk.CTkFrame):
    """Panel showing PDF files from a selected folder with click-to-select."""

    def __init__(self, parent, on_file_selected=None, config_manager=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._on_file_selected = on_file_selected
        self._config_manager = config_manager
        self._folder_path = ""
        self._all_pdf_files = []  # list of (path_str, filename, mtime, size) tuples
        self._pdf_files = []      # list of path_str — currently displayed subset
        self._current_highlight = None  # path of currently highlighted file

        self._build_ui()

    def _build_ui(self):
        """Build the file list UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # file list row shifted to 2

        # Row 0: Top bar — folder selection + sort + info
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

        # Sort dropdown
        saved_sort = self._load_sort_preference()
        self._sort_var = ctk.StringVar(value=saved_sort)
        self._sort_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self._sort_var,
            values=SORT_OPTIONS,
            width=120,
            height=26,
            font=ctk.CTkFont(size=10),
            dropdown_font=ctk.CTkFont(size=10),
            command=self._on_sort_changed,
        )
        self._sort_menu.grid(row=0, column=3, padx=(2, 2))
        ToolTip(self._sort_menu, "Sortera fillistan.")

        self._refresh_btn = ctk.CTkButton(
            top_frame, text="\u21BB", width=30, height=26,
            command=self._refresh_list,
            font=ctk.CTkFont(size=14)
        )
        self._refresh_btn.grid(row=0, column=4, padx=(2, 0))
        ToolTip(self._refresh_btn, "Uppdatera fillistan.")

        # Row 1: Search bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(2, 2))
        search_frame.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)

        self._search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="Sök bland PDF-filer...",
            height=26,
            font=ctk.CTkFont(size=11),
        )
        self._search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        self._clear_btn = ctk.CTkButton(
            search_frame, text="✕", width=26, height=26,
            command=self._clear_search,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=("gray85", "gray30"),
            text_color=("gray40", "gray60"),
        )
        self._clear_btn.grid(row=0, column=1, padx=(0, 0))
        self._clear_btn.grid_remove()  # hidden until text is entered

        # Row 2: File list using tk.Listbox for performance and native scrolling
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=(2, 4))
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
        """Scan the current folder for PDF files and populate metadata."""
        self._all_pdf_files = []

        if not self._folder_path or not Path(self._folder_path).is_dir():
            self._pdf_files = []
            self._listbox.delete(0, tk.END)
            self._count_label.configure(text="")
            return

        try:
            folder = Path(self._folder_path)
            for f in folder.iterdir():
                if f.suffix.lower() == ".pdf" and f.is_file():
                    try:
                        stat = f.stat()
                        self._all_pdf_files.append(
                            (str(f), f.name, stat.st_mtime, stat.st_size)
                        )
                    except OSError:
                        # File may have been deleted between iterdir and stat
                        pass

            logger.info(
                f"PDF file list: found {len(self._all_pdf_files)} files in {self._folder_path}"
            )
            self._apply_filter_and_sort()

        except PermissionError:
            logger.warning(f"Permission denied reading folder: {self._folder_path}")
            self._count_label.configure(text="\u00C5tkomst nekad")
        except Exception as e:
            logger.error(f"Error scanning folder: {e}")
            self._count_label.configure(text="Fel vid l\u00E4sning")

    def _apply_filter_and_sort(self):
        """Filter by search text and sort by selected criterion, then repopulate listbox."""
        # 1. Filter
        search_text = self._search_var.get().strip().lower()
        if search_text:
            filtered = [
                entry for entry in self._all_pdf_files
                if search_text in entry[1].lower()  # entry[1] = filename
            ]
        else:
            filtered = list(self._all_pdf_files)

        # 2. Sort
        sort_choice = self._sort_var.get()
        if sort_choice == "Namn (A-Ö)":
            filtered.sort(key=lambda e: e[1].lower())
        elif sort_choice == "Namn (Ö-A)":
            filtered.sort(key=lambda e: e[1].lower(), reverse=True)
        elif sort_choice == "Datum (nyast)":
            filtered.sort(key=lambda e: e[2], reverse=True)
        elif sort_choice == "Datum (äldst)":
            filtered.sort(key=lambda e: e[2])
        elif sort_choice == "Storlek (störst)":
            filtered.sort(key=lambda e: e[3], reverse=True)
        elif sort_choice == "Storlek (minst)":
            filtered.sort(key=lambda e: e[3])

        # 3. Update displayed list
        self._pdf_files = [entry[0] for entry in filtered]  # path strings

        self._listbox.delete(0, tk.END)
        for entry in filtered:
            self._listbox.insert(tk.END, entry[1])  # filename

        # 4. Update count label
        total = len(self._all_pdf_files)
        shown = len(filtered)
        if search_text:
            self._count_label.configure(text=f"{shown}/{total} PDF-filer")
        else:
            self._count_label.configure(text=f"{total} PDF-filer")

        # 5. Re-apply highlight if set
        if self._current_highlight:
            self.highlight_file(self._current_highlight)

    def _refresh_list(self):
        """Refresh button handler."""
        self._scan_folder()

    # ---- Search handling ----

    def _on_search_changed(self, *_args):
        """Handle search text changes — filter in real time."""
        text = self._search_var.get()
        if text:
            self._clear_btn.grid()
        else:
            self._clear_btn.grid_remove()

        if self._all_pdf_files:
            self._apply_filter_and_sort()

    def _clear_search(self):
        """Clear the search field."""
        self._search_var.set("")
        self._search_entry.focus_set()

    # ---- Sort handling ----

    def _on_sort_changed(self, _choice):
        """Handle sort dropdown change."""
        self._save_sort_preference()
        if self._all_pdf_files:
            self._apply_filter_and_sort()

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

    def _save_sort_preference(self):
        """Save the current sort order to config."""
        if self._config_manager:
            try:
                config = self._config_manager.load_config()
                config["pdf_sort_order"] = self._sort_var.get()
                self._config_manager.save_config(config)
            except Exception as e:
                logger.error(f"Failed to save sort preference: {e}")

    def _load_sort_preference(self) -> str:
        """Load sort preference from config, defaulting to 'Namn (A-Ö)'."""
        if self._config_manager:
            try:
                config = self._config_manager.load_config()
                saved = config.get("pdf_sort_order", "")
                if saved in SORT_OPTIONS:
                    return saved
            except Exception as e:
                logger.error(f"Failed to load sort preference: {e}")
        return "Namn (A-Ö)"

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
