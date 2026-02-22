"""
PDF Preview Panel for DJs Timeline-maskin
Renders PDF pages using PyMuPDF and displays them in a Canvas widget.
Supports zoom in/out, click-drag panning, and keyboard shortcuts.
"""

import logging
import os
import platform
import subprocess
import tempfile
import tkinter as tk
from collections import OrderedDict
from tkinter import messagebox

import customtkinter as ctk

from gui.utils import ToolTip

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
    """Panel that renders and displays PDF pages with navigation and zoom controls."""

    MAX_CACHE_SIZE = 8

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self._pdf_doc = None
        self._current_page = 0
        self._total_pages = 0
        self._current_path = ""
        self._page_cache = OrderedDict()
        self._photo_image = None  # prevent garbage collection
        self._resize_after_id = None

        # Zoom state
        self._zoom_factor = 1.0          # Current zoom (1.0 = 100% of PDF 72 DPI)
        self._fit_to_width_zoom = 1.0    # Last computed fit-to-width zoom
        self._is_fit_to_width = True     # Auto-fit mode active?
        self._min_zoom = 0.25            # 25%
        self._max_zoom = 4.0             # 400%
        self._zoom_step = 0.10           # 10% per step
        self._max_pixmap_dim = 4096      # Max rendered pixel dimension

        # Pan state
        self._pan_start_x = None
        self._pan_start_y = None
        self._is_panning = False

        # Debounced zoom state (for smooth mousewheel zoom)
        self._zoom_after_id = None
        self._zoom_batch_start = None      # Zoom factor at start of scroll batch
        self._zoom_batch_pdf_x = None      # PDF-space anchor point X
        self._zoom_batch_pdf_y = None      # PDF-space anchor point Y
        self._zoom_batch_anchor_x = None   # Screen-space cursor X
        self._zoom_batch_anchor_y = None   # Screen-space cursor Y

        # Page intrinsic dimensions (from PDF coordinate space, 72 DPI)
        self._page_intrinsic_width = 0.0
        self._page_intrinsic_height = 0.0

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

        # Vertical scrollbar
        self._v_scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self._canvas.yview
        )
        self._v_scrollbar.grid(row=0, column=1, sticky="ns", pady=2)
        self._canvas.configure(yscrollcommand=self._v_scrollbar.set)

        # Horizontal scrollbar
        self._h_scrollbar = tk.Scrollbar(
            self, orient="horizontal", command=self._canvas.xview
        )
        self._h_scrollbar.grid(row=1, column=0, sticky="ew", padx=2)
        self._canvas.configure(xscrollcommand=self._h_scrollbar.set)

        # Navigation + zoom bar at bottom
        nav_frame = ctk.CTkFrame(self, fg_color="transparent", height=32)
        nav_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 4))

        # Page navigation (left side)
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

        # Zoom controls (center area)
        self._zoom_out_btn = ctk.CTkButton(
            nav_frame, text="\u2212", width=28, height=26,
            command=self._zoom_out, font=ctk.CTkFont(size=14),
            fg_color="#D4A017", hover_color="#B8860B"
        )
        self._zoom_out_btn.pack(side="left", padx=(8, 2))
        ToolTip(self._zoom_out_btn, "Zooma ut (\u2318-)")

        self._zoom_label = ctk.CTkLabel(
            nav_frame, text="\u2014", width=50, font=ctk.CTkFont(size=11)
        )
        self._zoom_label.pack(side="left", padx=2)
        ToolTip(self._zoom_label, "Aktuell zoomniv\u00e5")

        self._zoom_in_btn = ctk.CTkButton(
            nav_frame, text="+", width=28, height=26,
            command=self._zoom_in, font=ctk.CTkFont(size=14),
            fg_color="#D4A017", hover_color="#B8860B"
        )
        self._zoom_in_btn.pack(side="left", padx=(2, 4))
        ToolTip(self._zoom_in_btn, "Zooma in (\u2318=)")

        self._fit_width_btn = ctk.CTkButton(
            nav_frame, text="Anpassa bredd", width=110, height=26,
            command=self._fit_to_width, font=ctk.CTkFont(size=11)
        )
        self._fit_width_btn.pack(side="left", padx=(4, 8))
        ToolTip(self._fit_width_btn, "Anpassa till f\u00f6nsterbredd (\u23180)")

        # Delete page button
        self._delete_page_btn = ctk.CTkButton(
            nav_frame, text="Ta bort sida", width=105, height=26,
            command=self._delete_current_page, font=ctk.CTkFont(size=11),
            fg_color="#dc3545", hover_color="#c82333"
        )
        self._delete_page_btn.pack(side="left", padx=(4, 8))
        ToolTip(self._delete_page_btn, "Ta bort aktuell sida fr\u00e5n PDF-filen")

        # Open externally button (right side)
        self._open_btn = ctk.CTkButton(
            nav_frame, text="\u00D6ppna PDF", width=90, height=26,
            command=self._open_externally, font=ctk.CTkFont(size=11),
            fg_color="#28a745", hover_color="#218838"
        )
        self._open_btn.pack(side="right", padx=(2, 4))

        # Bind resize for debounced re-render
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mousewheel and interactions on enter/leave
        self._canvas.bind("<Enter>", self._bind_interactions)
        self._canvas.bind("<Leave>", self._unbind_interactions)

        self._update_nav_state()
        self._update_zoom_btn_state()

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

            # Reset zoom to fit-to-width for new PDF
            self._zoom_factor = 1.0
            self._is_fit_to_width = True
            self._page_intrinsic_width = 0.0
            self._page_intrinsic_height = 0.0

            logger.info(f"PDF preview loaded: {file_path} ({self._total_pages} pages)")
            self._render_current_page(page_changed=True)
            self._update_nav_state()
        except Exception as e:
            logger.error(f"Failed to load PDF for preview: {e}")
            self._show_error(f"Kunde inte ladda PDF:\n{e}")

    def clear(self):
        """Clear the current preview."""
        # Cancel pending callbacks
        if self._resize_after_id:
            try:
                self.after_cancel(self._resize_after_id)
            except Exception:
                pass
            self._resize_after_id = None

        if self._zoom_after_id:
            try:
                self.after_cancel(self._zoom_after_id)
            except Exception:
                pass
            self._zoom_after_id = None
            self._zoom_batch_start = None

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

        # Reset zoom state
        self._zoom_factor = 1.0
        self._is_fit_to_width = True
        self._page_intrinsic_width = 0.0
        self._page_intrinsic_height = 0.0

        if hasattr(self, "_canvas"):
            self._canvas.delete("all")
            self._canvas.configure(scrollregion=(0, 0, 0, 0))

        if hasattr(self, "_page_label"):
            self._page_label.configure(text="Ingen PDF")
            self._update_nav_state()

        if hasattr(self, "_zoom_label"):
            self._zoom_label.configure(text="\u2014")
            self._update_zoom_btn_state()

    # ---- Navigation ----

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_current_page(page_changed=True)
            self._update_nav_state()

    def _next_page(self):
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._render_current_page(page_changed=True)
            self._update_nav_state()

    def _update_nav_state(self):
        """Update navigation buttons and page label."""
        if not hasattr(self, "_prev_btn"):
            return

        has_pdf = self._total_pages > 0
        self._prev_btn.configure(state="normal" if has_pdf and self._current_page > 0 else "disabled")
        self._next_btn.configure(state="normal" if has_pdf and self._current_page < self._total_pages - 1 else "disabled")
        self._open_btn.configure(state="normal" if has_pdf else "disabled")
        self._delete_page_btn.configure(state="normal" if has_pdf and self._total_pages > 1 else "disabled")

        if has_pdf:
            self._page_label.configure(text=f"Sida {self._current_page + 1}/{self._total_pages}")
        else:
            self._page_label.configure(text="Ingen PDF")

    # ---- Delete page ----

    def _delete_current_page(self):
        """Delete the current page from the PDF file."""
        if not self._pdf_doc or self._total_pages <= 1:
            return

        page_num = self._current_page
        confirm = messagebox.askyesno(
            "Ta bort sida",
            f"Ta bort sida {page_num + 1} av {self._total_pages}?\n\n"
            "Denna \u00e5tg\u00e4rd kan inte \u00e5ngras.",
            icon="warning",
        )
        if not confirm:
            return

        pdf_path = self._current_path

        try:
            # Close the open document to release file lock
            self._pdf_doc.close()
            self._pdf_doc = None

            # Reopen, delete page, save to temp file, replace original
            doc = fitz.open(pdf_path)
            doc.delete_page(page_num)

            dir_name = os.path.dirname(pdf_path)
            fd, tmp_path = tempfile.mkstemp(suffix=".pdf", dir=dir_name)
            os.close(fd)

            try:
                doc.save(tmp_path)
                doc.close()
                os.replace(tmp_path, pdf_path)
            except Exception:
                doc.close()
                # Clean up temp file on failure
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise

            # Adjust current page if we deleted the last page
            new_total = self._total_pages - 1
            if page_num >= new_total:
                page_num = new_total - 1

            # Reload the saved file
            self._page_cache.clear()
            self._pdf_doc = fitz.open(pdf_path)
            self._total_pages = len(self._pdf_doc)
            self._current_page = max(0, page_num)

            logger.info(
                f"Deleted page {page_num + 1} from {pdf_path}, "
                f"{self._total_pages} pages remaining"
            )

            self._render_current_page(page_changed=True)
            self._update_nav_state()
            self._update_zoom_btn_state()

        except Exception as e:
            logger.error(f"Failed to delete page: {e}")
            messagebox.showerror(
                "Fel",
                f"Kunde inte ta bort sidan:\n{e}",
            )
            # Try to reload the original (unchanged) file
            try:
                self._pdf_doc = fitz.open(pdf_path)
                self._total_pages = len(self._pdf_doc)
                self._current_page = min(self._current_page, self._total_pages - 1)
                self._page_cache.clear()
                self._render_current_page(page_changed=True)
                self._update_nav_state()
            except Exception as reload_err:
                logger.error(f"Failed to reload PDF after delete error: {reload_err}")

    # ---- Zoom controls ----

    def _zoom_in(self, event=None):
        """Zoom in by one step, centered on viewport."""
        new_zoom = min(self._zoom_factor + self._zoom_step, self._max_zoom)
        self._set_zoom(new_zoom)

    def _zoom_out(self, event=None):
        """Zoom out by one step, centered on viewport."""
        new_zoom = max(self._zoom_factor - self._zoom_step, self._min_zoom)
        self._set_zoom(new_zoom)

    def _fit_to_width(self, event=None):
        """Reset zoom to fit canvas width."""
        self._is_fit_to_width = True
        self._page_cache.clear()  # Clear cache since fit-to-width recalculates
        self._render_current_page(page_changed=True)

    def _zoom_at_cursor(self, event):
        """Zoom in/out centered on cursor position with debounced rendering.

        Accumulates rapid scroll events and only renders once they settle (30ms).
        Uses a small multiplier per delta unit for smooth, proportional zoom.
        """
        if not self._pdf_doc or self._total_pages == 0:
            return

        # macOS physical mouse can report large deltas (10-40+ per tick)
        # while trackpad reports small deltas (1-5) across many rapid events.
        # Normalize to ±1 max so each scroll event gives at most ~6% zoom.
        if platform.system() == "Darwin":
            if event.delta > 0:
                normalized = min(event.delta / 3.0, 1.0)
            elif event.delta < 0:
                normalized = max(event.delta / 3.0, -1.0)
            else:
                return
            new_zoom = self._zoom_factor * (1.06 ** normalized)
        else:
            # Windows/Linux: delta is typically ±120 per tick
            steps = event.delta / 120
            new_zoom = self._zoom_factor * (1.1 ** steps)

        new_zoom = max(self._min_zoom, min(new_zoom, self._max_zoom))

        if abs(new_zoom - self._zoom_factor) < 0.001:
            return

        # On first event in a batch, record starting state for anchor calculation
        if self._zoom_batch_start is None:
            self._zoom_batch_start = self._zoom_factor
            self._zoom_batch_anchor_x = event.x
            self._zoom_batch_anchor_y = event.y
            # Record the PDF-space point under cursor before any zoom changes
            self._zoom_batch_pdf_x = self._canvas.canvasx(event.x) / self._zoom_factor
            self._zoom_batch_pdf_y = self._canvas.canvasy(event.y) / self._zoom_factor

        # Accumulate zoom factor immediately (no render yet)
        self._zoom_factor = new_zoom
        self._is_fit_to_width = False

        # Update label instantly for responsiveness
        self._update_zoom_label()
        self._update_zoom_btn_state()

        # Debounce the expensive render — cancel previous, schedule new
        if self._zoom_after_id:
            self.after_cancel(self._zoom_after_id)
        self._zoom_after_id = self.after(30, self._on_zoom_scroll_complete)

    def _on_zoom_scroll_complete(self):
        """Render after scroll-zoom events settle. Restores anchor position."""
        self._zoom_after_id = None

        # Retrieve batch state
        pdf_x = self._zoom_batch_pdf_x
        pdf_y = self._zoom_batch_pdf_y
        anchor_x = self._zoom_batch_anchor_x
        anchor_y = self._zoom_batch_anchor_y

        # Reset batch state
        self._zoom_batch_start = None
        self._zoom_batch_pdf_x = None
        self._zoom_batch_pdf_y = None
        self._zoom_batch_anchor_x = None
        self._zoom_batch_anchor_y = None

        # Render at the accumulated zoom level
        self._render_current_page(page_changed=False)

        # Restore scroll position so the PDF point stays under the cursor
        if pdf_x is not None and anchor_x is not None:
            sr = self._canvas.cget("scrollregion")
            if sr:
                parts = sr.split()
                sr_width = float(parts[2]) if len(parts) > 2 else 0
                sr_height = float(parts[3]) if len(parts) > 3 else 0

                if sr_width > 0 and sr_height > 0:
                    new_canvas_x = pdf_x * self._zoom_factor
                    new_canvas_y = pdf_y * self._zoom_factor
                    self._canvas.xview_moveto(max(0, (new_canvas_x - anchor_x) / sr_width))
                    self._canvas.yview_moveto(max(0, (new_canvas_y - anchor_y) / sr_height))

    def _set_zoom(self, new_zoom, anchor_canvas_x=None, anchor_canvas_y=None):
        """Apply a zoom change, optionally preserving the point under anchor coordinates."""
        new_zoom = round(max(self._min_zoom, min(new_zoom, self._max_zoom)), 2)
        old_zoom = self._zoom_factor

        if new_zoom == round(old_zoom, 2) and not self._is_fit_to_width:
            return

        # Calculate the PDF-space point under the anchor before zoom
        pdf_anchor_x = None
        pdf_anchor_y = None
        if anchor_canvas_x is not None and old_zoom > 0:
            canvas_scroll_x = self._canvas.canvasx(anchor_canvas_x)
            canvas_scroll_y = self._canvas.canvasy(anchor_canvas_y)
            pdf_anchor_x = canvas_scroll_x / old_zoom
            pdf_anchor_y = canvas_scroll_y / old_zoom

        self._is_fit_to_width = False
        self._zoom_factor = new_zoom
        self._render_current_page(page_changed=False)

        # Restore anchor position after render
        if pdf_anchor_x is not None:
            sr = self._canvas.cget("scrollregion")
            if sr:
                parts = sr.split()
                sr_width = float(parts[2]) if len(parts) > 2 else 0
                sr_height = float(parts[3]) if len(parts) > 3 else 0

                if sr_width > 0 and sr_height > 0:
                    new_canvas_x = pdf_anchor_x * new_zoom
                    new_canvas_y = pdf_anchor_y * new_zoom

                    target_xfrac = max(0, (new_canvas_x - anchor_canvas_x) / sr_width)
                    target_yfrac = max(0, (new_canvas_y - anchor_canvas_y) / sr_height)

                    self._canvas.xview_moveto(target_xfrac)
                    self._canvas.yview_moveto(target_yfrac)

        self._update_zoom_label()
        self._update_zoom_btn_state()

    def _update_zoom_label(self):
        """Update zoom percentage display."""
        if hasattr(self, "_zoom_label"):
            pct = int(self._zoom_factor * 100)
            self._zoom_label.configure(text=f"{pct}%")

    def _update_zoom_btn_state(self):
        """Enable/disable zoom buttons at limits."""
        if not hasattr(self, "_zoom_in_btn"):
            return
        has_pdf = self._total_pages > 0
        at_max = round(self._zoom_factor, 2) >= self._max_zoom
        at_min = round(self._zoom_factor, 2) <= self._min_zoom
        self._zoom_in_btn.configure(state="normal" if has_pdf and not at_max else "disabled")
        self._zoom_out_btn.configure(state="normal" if has_pdf and not at_min else "disabled")
        self._fit_width_btn.configure(state="normal" if has_pdf else "disabled")

    # ---- Rendering ----

    def _render_current_page(self, page_changed=True):
        """Render the current page to the canvas."""
        if not self._pdf_doc or self._total_pages == 0:
            return

        canvas_width = self._canvas.winfo_width()
        if canvas_width < 50:
            # Canvas not yet sized, retry shortly
            if self.winfo_exists():
                self.after(100, lambda: self._render_current_page(page_changed))
            return

        # Get page intrinsic dimensions for fit-to-width calculation
        try:
            page = self._pdf_doc[self._current_page]
            page_rect = page.rect
            self._page_intrinsic_width = page_rect.width
            self._page_intrinsic_height = page_rect.height
        except Exception:
            return

        if self._page_intrinsic_width <= 0:
            return

        # In fit-to-width mode, compute zoom from canvas width
        if self._is_fit_to_width:
            self._fit_to_width_zoom = (canvas_width - 4) / self._page_intrinsic_width
            self._zoom_factor = self._fit_to_width_zoom
            self._update_zoom_label()
            self._update_zoom_btn_state()

        zoom_rounded = round(self._zoom_factor, 2)
        cache_key = (self._current_path, self._current_page, zoom_rounded)

        if cache_key in self._page_cache:
            self._page_cache.move_to_end(cache_key)
            pil_image = self._page_cache[cache_key]
        else:
            pil_image = self._render_page_to_image(self._current_page, self._zoom_factor)
            if pil_image is None:
                return

            self._page_cache[cache_key] = pil_image
            while len(self._page_cache) > self.MAX_CACHE_SIZE:
                self._page_cache.popitem(last=False)

        # Display on canvas
        self._photo_image = ImageTk.PhotoImage(pil_image)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo_image)
        self._canvas.configure(scrollregion=(0, 0, pil_image.width, pil_image.height))

        # Only reset scroll to top on page changes, not zoom changes
        if page_changed:
            self._canvas.xview_moveto(0)
            self._canvas.yview_moveto(0)

    def _render_page_to_image(self, page_num, zoom_factor):
        """Render a PDF page to a PIL Image at the given zoom factor."""
        try:
            page = self._pdf_doc[page_num]
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height

            if page_width <= 0 or page_height <= 0:
                return None

            # Clamp zoom to prevent excessive pixmap size
            effective_zoom = zoom_factor
            max_dim = max(page_width * effective_zoom, page_height * effective_zoom)
            if max_dim > self._max_pixmap_dim:
                effective_zoom = self._max_pixmap_dim / max(page_width, page_height)
                logger.warning(
                    f"Zoom clamped from {zoom_factor:.2f} to {effective_zoom:.2f} "
                    f"to stay within {self._max_pixmap_dim}px limit"
                )

            mat = fitz.Matrix(effective_zoom, effective_zoom)
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
            if self._is_fit_to_width:
                # Recalculate fit-to-width zoom for new canvas size
                self._page_cache.clear()
                self._render_current_page(page_changed=True)
            # When manually zoomed, do nothing — scrollbars handle it

    # ---- Interaction bindings ----

    def _bind_interactions(self, event=None):
        """Bind mousewheel, keyboard shortcuts, and pan when cursor enters canvas."""
        # Mousewheel
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        if platform.system() != "Darwin":
            self._canvas.bind("<Button-4>", self._on_mousewheel)
            self._canvas.bind("<Button-5>", self._on_mousewheel)

        # Pan (click-drag)
        self._canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self._canvas.bind("<B1-Motion>", self._on_pan_motion)
        self._canvas.bind("<ButtonRelease-1>", self._on_pan_end)

        # Double-click to fit-to-width
        self._canvas.bind("<Double-Button-1>", lambda e: self._fit_to_width())

        # Keyboard zoom shortcuts (macOS: Command key)
        self._canvas.bind("<Command-equal>", self._zoom_in)
        self._canvas.bind("<Command-minus>", self._zoom_out)
        self._canvas.bind("<Command-0>", self._fit_to_width)

        # Make canvas focusable for keyboard events
        self._canvas.focus_set()

    def _unbind_interactions(self, event=None):
        """Unbind interactions when cursor leaves canvas."""
        self._canvas.unbind("<MouseWheel>")
        if platform.system() != "Darwin":
            self._canvas.unbind("<Button-4>")
            self._canvas.unbind("<Button-5>")

        self._canvas.unbind("<ButtonPress-1>")
        self._canvas.unbind("<B1-Motion>")
        self._canvas.unbind("<ButtonRelease-1>")
        self._canvas.unbind("<Double-Button-1>")
        self._canvas.unbind("<Command-equal>")
        self._canvas.unbind("<Command-minus>")
        self._canvas.unbind("<Command-0>")

        # Reset cursor if panning was interrupted
        if self._is_panning:
            self._is_panning = False
            self._canvas.configure(cursor="")

    def _on_mousewheel(self, event):
        """Handle mousewheel: Cmd+scroll = zoom, Shift+scroll = horizontal, plain = vertical."""
        if platform.system() == "Darwin":
            # macOS: Check modifier keys in event.state
            # Bit 0x8 = Command key on macOS
            if event.state & 0x8:
                self._zoom_at_cursor(event)
                return
            # Bit 0x1 = Shift key
            if event.state & 0x1:
                self._canvas.xview_scroll(int(-1 * event.delta), "units")
                return
            # Plain scroll = vertical
            self._canvas.yview_scroll(int(-1 * event.delta), "units")
        elif event.num == 4:
            self._canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(3, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---- Pan / drag ----

    def _on_pan_start(self, event):
        """Start panning on mouse press."""
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self._is_panning = True
        self._canvas.configure(cursor="fleur")

    def _on_pan_motion(self, event):
        """Pan the canvas during mouse drag using fractional moveto for smooth movement."""
        if not self._is_panning:
            return

        dx = self._pan_start_x - event.x
        dy = self._pan_start_y - event.y

        # Get scroll region dimensions for fractional calculation
        sr = self._canvas.cget("scrollregion")
        if sr:
            parts = sr.split()
            sr_width = float(parts[2]) if len(parts) > 2 else 0
            sr_height = float(parts[3]) if len(parts) > 3 else 0

            if sr_width > 0:
                current_x = self._canvas.xview()[0]
                new_x = current_x + dx / sr_width
                self._canvas.xview_moveto(max(0.0, new_x))

            if sr_height > 0:
                current_y = self._canvas.yview()[0]
                new_y = current_y + dy / sr_height
                self._canvas.yview_moveto(max(0.0, new_y))

        self._pan_start_x = event.x
        self._pan_start_y = event.y

    def _on_pan_end(self, event):
        """End panning on mouse release."""
        self._is_panning = False
        self._canvas.configure(cursor="")

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
