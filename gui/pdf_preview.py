"""
PDF Preview Panel for DJs Timeline-maskin
Renders PDF pages using PyMuPDF and displays them in a Canvas widget.
"""

import logging
import platform
import subprocess
import tkinter as tk
from collections import OrderedDict

import customtkinter as ctk

logger = logging.getLogger(__name__)

# Try importing PyMuPDF and PIL
try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not installed - PDF preview disabled")

try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed - PDF preview disabled")


class PDFPreviewPanel(ctk.CTkFrame):
    """Panel that renders and displays PDF pages with navigation controls."""

    MAX_CACHE_SIZE = 5

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self._pdf_doc = None
        self._current_page = 0
        self._total_pages = 0
        self._current_path = ""
        self._page_cache = OrderedDict()
        self._photo_image = None  # prevent garbage collection
        self._resize_after_id = None

        self._build_ui()

    def _build_ui(self):
        """Build the preview UI."""
        if not PYMUPDF_AVAILABLE or not PIL_AVAILABLE:
            self._build_fallback_ui()
            return

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Canvas for PDF page rendering
        self._canvas = tk.Canvas(
            self, bg="#E0E0E0", highlightthickness=0
        )
        self._canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Scrollbar for tall pages
        self._scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self._canvas.yview
        )
        self._scrollbar.grid(row=0, column=1, sticky="ns", pady=2)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # Navigation bar at bottom
        nav_frame = ctk.CTkFrame(self, fg_color="transparent", height=32)
        nav_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 4))

        self._prev_btn = ctk.CTkButton(
            nav_frame, text="\u25C0", width=30, height=26,
            command=self._prev_page, font=ctk.CTkFont(size=12)
        )
        self._prev_btn.pack(side="left", padx=(4, 2))

        self._page_label = ctk.CTkLabel(
            nav_frame, text="Ingen PDF", font=ctk.CTkFont(size=11)
        )
        self._page_label.pack(side="left", padx=4)

        self._next_btn = ctk.CTkButton(
            nav_frame, text="\u25B6", width=30, height=26,
            command=self._next_page, font=ctk.CTkFont(size=12)
        )
        self._next_btn.pack(side="left", padx=(2, 8))

        self._open_btn = ctk.CTkButton(
            nav_frame, text="\u00D6ppna PDF", width=90, height=26,
            command=self._open_externally, font=ctk.CTkFont(size=11),
            fg_color="#28a745", hover_color="#218838"
        )
        self._open_btn.pack(side="right", padx=(2, 4))

        # Bind resize for debounced re-render
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mousewheel to canvas scrolling
        self._canvas.bind("<Enter>", self._bind_scroll)
        self._canvas.bind("<Leave>", self._unbind_scroll)

        self._update_nav_state()

    def _build_fallback_ui(self):
        """Show message when PyMuPDF is not available."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        missing = []
        if not PYMUPDF_AVAILABLE:
            missing.append("PyMuPDF")
        if not PIL_AVAILABLE:
            missing.append("Pillow")

        label = ctk.CTkLabel(
            self,
            text=f"PDF-f\u00F6rhandsvisning ej tillg\u00E4nglig\n\n"
                 f"Installera: pip install {' '.join(missing)}",
            font=ctk.CTkFont(size=12),
            text_color="gray50",
            wraplength=200,
        )
        label.grid(row=0, column=0, padx=10, pady=20)

    # ---- Public API ----

    def load_pdf(self, file_path: str):
        """Load a PDF file for preview."""
        if not PYMUPDF_AVAILABLE or not PIL_AVAILABLE:
            return

        self.clear()

        try:
            self._pdf_doc = fitz.open(file_path)
            self._total_pages = len(self._pdf_doc)
            self._current_page = 0
            self._current_path = file_path
            logger.info(f"PDF preview loaded: {file_path} ({self._total_pages} pages)")
            self._render_current_page()
            self._update_nav_state()
        except Exception as e:
            logger.error(f"Failed to load PDF for preview: {e}")
            self._show_error(f"Kunde inte ladda PDF:\n{e}")

    def clear(self):
        """Clear the current preview."""
        # Cancel pending resize callback
        if self._resize_after_id:
            try:
                self.after_cancel(self._resize_after_id)
            except Exception:
                pass
            self._resize_after_id = None

        if self._pdf_doc:
            try:
                self._pdf_doc.close()
            except Exception:
                pass
            self._pdf_doc = None

        self._current_page = 0
        self._total_pages = 0
        self._current_path = ""
        self._page_cache.clear()
        self._photo_image = None

        if hasattr(self, "_canvas"):
            self._canvas.delete("all")
            self._canvas.configure(scrollregion=(0, 0, 0, 0))

        if hasattr(self, "_page_label"):
            self._page_label.configure(text="Ingen PDF")
            self._update_nav_state()

    # ---- Navigation ----

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_current_page()
            self._update_nav_state()

    def _next_page(self):
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._render_current_page()
            self._update_nav_state()

    def _update_nav_state(self):
        """Update navigation buttons and page label."""
        if not hasattr(self, "_prev_btn"):
            return

        has_pdf = self._total_pages > 0
        self._prev_btn.configure(state="normal" if has_pdf and self._current_page > 0 else "disabled")
        self._next_btn.configure(state="normal" if has_pdf and self._current_page < self._total_pages - 1 else "disabled")
        self._open_btn.configure(state="normal" if has_pdf else "disabled")

        if has_pdf:
            self._page_label.configure(text=f"Sida {self._current_page + 1}/{self._total_pages}")
        else:
            self._page_label.configure(text="Ingen PDF")

    # ---- Rendering ----

    def _render_current_page(self):
        """Render the current page to the canvas."""
        if not self._pdf_doc or self._total_pages == 0:
            return

        canvas_width = self._canvas.winfo_width()
        if canvas_width < 50:
            # Canvas not yet sized, retry shortly
            if self.winfo_exists():
                self.after(100, self._render_current_page)
            return

        cache_key = (self._current_path, self._current_page, canvas_width)

        if cache_key in self._page_cache:
            # Move to end (most recently used)
            self._page_cache.move_to_end(cache_key)
            pil_image = self._page_cache[cache_key]
        else:
            pil_image = self._render_page_to_image(self._current_page, canvas_width)
            if pil_image is None:
                return

            # Add to cache with LRU eviction
            self._page_cache[cache_key] = pil_image
            while len(self._page_cache) > self.MAX_CACHE_SIZE:
                self._page_cache.popitem(last=False)

        # Display on canvas
        self._photo_image = ImageTk.PhotoImage(pil_image)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo_image)
        self._canvas.configure(scrollregion=(0, 0, pil_image.width, pil_image.height))
        self._canvas.yview_moveto(0)

    def _render_page_to_image(self, page_num, target_width):
        """Render a PDF page to a PIL Image, fit to target_width."""
        try:
            page = self._pdf_doc[page_num]
            page_rect = page.rect
            page_width = page_rect.width

            if page_width <= 0:
                return None

            # Calculate zoom to fit canvas width (with small margin)
            zoom = (target_width - 4) / page_width
            mat = fitz.Matrix(zoom, zoom)

            pix = page.get_pixmap(matrix=mat, alpha=False)
            pil_image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            return pil_image

        except Exception as e:
            logger.error(f"Failed to render page {page_num}: {e}")
            return None

    # ---- Resize handling ----

    def _on_canvas_configure(self, event):
        """Debounced re-render on canvas resize."""
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(200, self._on_resize_complete)

    def _on_resize_complete(self):
        """Re-render after resize settles."""
        self._resize_after_id = None
        if self._pdf_doc and self._total_pages > 0:
            self._render_current_page()

    # ---- Scrolling ----

    def _bind_scroll(self, event=None):
        """Bind mousewheel when cursor enters canvas (widget-specific, not global)."""
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        if platform.system() != "Darwin":
            self._canvas.bind("<Button-4>", self._on_mousewheel)
            self._canvas.bind("<Button-5>", self._on_mousewheel)

    def _unbind_scroll(self, event=None):
        """Unbind mousewheel when cursor leaves canvas."""
        self._canvas.unbind("<MouseWheel>")
        if platform.system() != "Darwin":
            self._canvas.unbind("<Button-4>")
            self._canvas.unbind("<Button-5>")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        if platform.system() == "Darwin":
            self._canvas.yview_scroll(int(-1 * event.delta), "units")
        elif event.num == 4:
            self._canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(3, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---- External open ----

    def _open_externally(self):
        """Open the current PDF in the system PDF viewer."""
        if not self._current_path:
            return
        try:
            if platform.system() == "Windows":
                import os
                os.startfile(self._current_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", "--", self._current_path])
            else:
                subprocess.run(["xdg-open", "--", self._current_path])
        except Exception as e:
            logger.error(f"Failed to open PDF externally: {e}")

    # ---- Error display ----

    def _show_error(self, message):
        """Show an error message on the canvas."""
        if hasattr(self, "_canvas"):
            self._canvas.delete("all")
            self._canvas.create_text(
                10, 10, anchor="nw", text=message,
                fill="red", font=("Arial", 11), width=250
            )
