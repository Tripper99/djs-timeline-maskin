"""
PDF Merge Dialog for DJs Timeline-maskin
Allows merging multiple PDF files into one, with source files moved to a subfolder.
"""

import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFMergeDialog(ctk.CTkToplevel):
    """Modal dialog for merging PDF files."""

    SUBFOLDER_NAME = "Sammanslagna filer - kastas"

    def __init__(self, parent, folder_path, file_list, on_complete=None,
                 on_clear_preview=None):
        """Initialize merge dialog.

        Args:
            parent: Parent window.
            folder_path: Path to the folder containing PDF files.
            file_list: List of PDF file paths currently shown in file list.
            on_complete: Callback when merge is done (to refresh file list).
            on_clear_preview: Callback to clear PDF preview if needed.
        """
        super().__init__(parent)

        self._folder_path = folder_path
        self._file_list = file_list
        self._on_complete = on_complete
        self._on_clear_preview = on_clear_preview

        self.title("Slå samman PDF-filer")
        self.geometry("900x550")
        self.resizable(True, True)
        self.minsize(700, 400)

        self.transient(parent)

        self._build_ui()

        # Center on parent (allow negative coords for external monitors)
        self.update_idletasks()
        parent.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

        # Make modal after window is positioned and visible
        self.after(100, self._make_modal)

        # Release grab on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _make_modal(self):
        """Set grab after window is fully visible."""
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def _on_close(self):
        """Release grab and destroy."""
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def _build_ui(self):
        """Build the dialog UI."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            header_frame, text="Slå samman PDF-filer",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")

        # Folder display
        folder_display = str(self._folder_path)
        if len(folder_display) > 80:
            folder_display = "..." + folder_display[-77:]
        ctk.CTkLabel(
            header_frame, text=f"Mapp: {folder_display}",
            font=ctk.CTkFont(size=11), text_color="gray50"
        ).pack(anchor="w", pady=(2, 0))

        # Main content: two lists with buttons between
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=16, pady=(8, 4))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        # Left list label
        ctk.CTkLabel(
            content_frame, text="Tillgängliga filer:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        # Right list label (with count)
        self._right_label = ctk.CTkLabel(
            content_frame, text="Sammanfogningsordning: (0)",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self._right_label.grid(row=0, column=2, sticky="w", pady=(0, 4))

        # Left list frame
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        self._left_listbox = tk.Listbox(
            left_frame, font=("Arial", 10), selectmode=tk.EXTENDED,
            activestyle="none", relief="flat", bd=1,
            highlightthickness=1, highlightcolor="#2196F3",
            highlightbackground="#E0E0E0",
            selectbackground="#BBDEFB", selectforeground="#000000",
        )
        self._left_listbox.grid(row=0, column=0, sticky="nsew")

        left_scroll = tk.Scrollbar(
            left_frame, orient="vertical", command=self._left_listbox.yview
        )
        left_scroll.grid(row=0, column=1, sticky="ns")
        self._left_listbox.configure(yscrollcommand=left_scroll.set)

        # Center buttons
        btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=1, padx=8)

        btn_style = {"width": 60, "height": 28, "font": ctk.CTkFont(size=12)}

        ctk.CTkButton(
            btn_frame, text=">>", command=self._add_selected, **btn_style
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            btn_frame, text="<<", command=self._remove_selected, **btn_style
        ).pack(pady=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Alla >>", command=self._add_all,
            width=60, height=28, font=ctk.CTkFont(size=11)
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            btn_frame, text="<< Alla", command=self._remove_all,
            width=60, height=28, font=ctk.CTkFont(size=11)
        ).pack()

        # Right list frame with order buttons
        right_outer = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_outer.grid(row=1, column=2, sticky="nsew", padx=(4, 0))
        right_outer.grid_rowconfigure(0, weight=1)
        right_outer.grid_columnconfigure(0, weight=1)

        self._right_listbox = tk.Listbox(
            right_outer, font=("Arial", 10), selectmode=tk.SINGLE,
            activestyle="none", relief="flat", bd=1,
            highlightthickness=1, highlightcolor="#6C63FF",
            highlightbackground="#E0E0E0",
            selectbackground="#D1C4E9", selectforeground="#000000",
        )
        self._right_listbox.grid(row=0, column=0, sticky="nsew")

        right_scroll = tk.Scrollbar(
            right_outer, orient="vertical", command=self._right_listbox.yview
        )
        right_scroll.grid(row=0, column=1, sticky="ns")
        self._right_listbox.configure(yscrollcommand=right_scroll.set)

        # Up/down buttons
        order_frame = ctk.CTkFrame(right_outer, fg_color="transparent")
        order_frame.grid(row=0, column=2, padx=(4, 0))

        ctk.CTkButton(
            order_frame, text="\u25B2", width=30, height=28,
            command=self._move_up, font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            order_frame, text="\u25BC", width=30, height=28,
            command=self._move_down, font=ctk.CTkFont(size=14)
        ).pack()

        # Bottom: filename + action buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=16, pady=(8, 16))

        # Filename row
        name_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            name_frame, text="Filnamn:", font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 8))

        self._filename_var = ctk.StringVar()
        self._filename_var.trace_add("write", self._on_state_changed)

        self._filename_entry = ctk.CTkEntry(
            name_frame, textvariable=self._filename_var,
            width=400, height=30, font=ctk.CTkFont(size=12),
            placeholder_text="Ange filnamn för sammanfogad PDF..."
        )
        self._filename_entry.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            name_frame, text=".pdf", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        # Action buttons
        btn_action_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_action_frame.pack(fill="x")

        self._merge_btn = ctk.CTkButton(
            btn_action_frame, text="Slå samman",
            width=140, height=34,
            command=self._perform_merge,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#28a745", hover_color="#218838",
            state="disabled"
        )
        self._merge_btn.pack(side="left")

        ctk.CTkButton(
            btn_action_frame, text="Avbryt",
            width=100, height=34,
            command=self._on_close,
            font=ctk.CTkFont(size=12),
            fg_color="#6c757d", hover_color="#5a6268"
        ).pack(side="right")

        # Populate left list
        self._file_paths = {}  # filename -> full path
        self._merge_files = []  # ordered list of full paths for merge
        self._populate_left_list()

        # Bind listbox changes
        self._right_listbox.bind("<<ListboxSelect>>", lambda e: None)

    def _populate_left_list(self):
        """Fill left listbox with available files."""
        self._left_listbox.delete(0, tk.END)
        self._file_paths.clear()

        for file_path in self._file_list:
            filename = Path(file_path).name
            self._file_paths[filename] = file_path
            self._left_listbox.insert(tk.END, filename)

    def _add_selected(self):
        """Move selected files from left to right list."""
        selection = list(self._left_listbox.curselection())
        if not selection:
            return

        # Get filenames to move (reverse order to avoid index shift)
        filenames = [self._left_listbox.get(i) for i in selection]

        for idx in sorted(selection, reverse=True):
            self._left_listbox.delete(idx)

        for filename in filenames:
            self._right_listbox.insert(tk.END, filename)
            if filename in self._file_paths:
                self._merge_files.append(self._file_paths[filename])

        self._on_state_changed()

    def _remove_selected(self):
        """Move selected file from right back to left list."""
        selection = self._right_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        filename = self._right_listbox.get(idx)
        self._right_listbox.delete(idx)

        # Remove from merge list
        if filename in self._file_paths:
            path = self._file_paths[filename]
            if path in self._merge_files:
                self._merge_files.remove(path)

        # Add back to left list
        self._left_listbox.insert(tk.END, filename)

        self._on_state_changed()

    def _add_all(self):
        """Move all files from left to right."""
        while self._left_listbox.size() > 0:
            filename = self._left_listbox.get(0)
            self._left_listbox.delete(0)
            self._right_listbox.insert(tk.END, filename)
            if filename in self._file_paths:
                self._merge_files.append(self._file_paths[filename])

        self._on_state_changed()

    def _remove_all(self):
        """Move all files from right back to left."""
        self._right_listbox.delete(0, tk.END)
        self._merge_files.clear()
        self._populate_left_list()
        self._on_state_changed()

    def _move_up(self):
        """Move selected item up in the right list."""
        selection = self._right_listbox.curselection()
        if not selection or selection[0] == 0:
            return

        idx = selection[0]
        filename = self._right_listbox.get(idx)
        self._right_listbox.delete(idx)
        self._right_listbox.insert(idx - 1, filename)
        self._right_listbox.selection_set(idx - 1)
        self._right_listbox.see(idx - 1)

        # Update merge order
        if idx < len(self._merge_files):
            item = self._merge_files.pop(idx)
            self._merge_files.insert(idx - 1, item)

    def _move_down(self):
        """Move selected item down in the right list."""
        selection = self._right_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx >= self._right_listbox.size() - 1:
            return

        filename = self._right_listbox.get(idx)
        self._right_listbox.delete(idx)
        self._right_listbox.insert(idx + 1, filename)
        self._right_listbox.selection_set(idx + 1)
        self._right_listbox.see(idx + 1)

        # Update merge order
        if idx < len(self._merge_files):
            item = self._merge_files.pop(idx)
            self._merge_files.insert(idx + 1, item)

    def _on_state_changed(self, *_args):
        """Update merge button state and right list count label."""
        count = self._right_listbox.size()
        self._right_label.configure(text=f"Sammanfogningsordning: ({count})")

        filename = self._filename_var.get().strip()
        can_merge = count >= 2 and len(filename) > 0
        self._merge_btn.configure(state="normal" if can_merge else "disabled")

    def _perform_merge(self):
        """Execute the PDF merge operation."""
        if not PYMUPDF_AVAILABLE:
            messagebox.showerror("Fel", "PyMuPDF krävs för att slå samman PDF-filer.")
            return

        # Build output filename
        filename = self._filename_var.get().strip()
        if not filename:
            return
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        output_path = Path(self._folder_path) / filename

        # Check if output file already exists
        if output_path.exists():
            overwrite = messagebox.askyesno(
                "Fil finns redan",
                f"Filen '{filename}' finns redan.\n\nVill du skriva över den?",
                icon="warning"
            )
            if not overwrite:
                return

        # Validate all source files still exist
        missing = [p for p in self._merge_files if not Path(p).exists()]
        if missing:
            names = "\n".join(Path(p).name for p in missing)
            messagebox.showerror(
                "Filer saknas",
                f"Följande filer hittades inte:\n\n{names}"
            )
            return

        # Build file list for confirmation
        file_names = [Path(p).name for p in self._merge_files]
        file_list_text = "\n".join(f"  {i+1}. {name}" for i, name in enumerate(file_names))

        confirm = messagebox.askyesno(
            "Bekräfta sammanslagning",
            f"Slå samman {len(self._merge_files)} filer i denna ordning:\n\n"
            f"{file_list_text}\n\n"
            f"Sparas som: {filename}\n\n"
            f"Originalfilerna flyttas till undermappen\n"
            f"'{self.SUBFOLDER_NAME}'.",
            icon="question"
        )
        if not confirm:
            return

        # Clear preview if any source file is currently previewed
        if self._on_clear_preview:
            self._on_clear_preview(self._merge_files)

        # Perform the merge
        try:
            output_doc = fitz.open()
            for file_path in self._merge_files:
                input_doc = fitz.open(file_path)
                output_doc.insert_pdf(input_doc)
                input_doc.close()
            output_doc.save(str(output_path))
            output_doc.close()

            logger.info(f"PDF merge successful: {len(self._merge_files)} files → {output_path}")

        except Exception as e:
            logger.error(f"PDF merge failed: {e}")
            messagebox.showerror(
                "Sammanslagning misslyckades",
                f"Kunde inte slå samman PDF-filerna:\n\n{e}"
            )
            return

        # Move source files to subfolder
        moved, failed = self._move_source_files()

        # Report result
        if failed:
            failed_names = "\n".join(Path(p).name for p in failed)
            messagebox.showwarning(
                "Delvis klart",
                f"PDF-filen '{filename}' skapades.\n\n"
                f"{moved} av {len(self._merge_files)} originalfiler flyttades.\n\n"
                f"Kunde inte flytta:\n{failed_names}"
            )
        else:
            messagebox.showinfo(
                "Klart",
                f"PDF-filen '{filename}' skapades.\n\n"
                f"Alla {moved} originalfiler flyttades till\n"
                f"'{self.SUBFOLDER_NAME}'."
            )

        # Notify parent to refresh
        if self._on_complete:
            self._on_complete()

        self._on_close()

    def _move_source_files(self):
        """Move source files to subfolder. Returns (moved_count, failed_paths)."""
        subfolder = Path(self._folder_path) / self.SUBFOLDER_NAME
        subfolder.mkdir(exist_ok=True)

        moved = 0
        failed = []

        for file_path in self._merge_files:
            src = Path(file_path)
            dest = subfolder / src.name

            # Handle filename conflicts
            if dest.exists():
                stem = src.stem
                suffix = src.suffix
                counter = 1
                while dest.exists():
                    dest = subfolder / f"{stem}_{counter}{suffix}"
                    counter += 1

            try:
                src.rename(dest)
                moved += 1
                logger.info(f"Moved source file: {src.name} → {dest}")
            except Exception as e:
                logger.error(f"Failed to move {src.name}: {e}")
                failed.append(file_path)

        return moved, failed
