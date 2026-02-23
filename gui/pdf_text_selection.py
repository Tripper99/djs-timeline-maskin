"""
PDF Text Selection for DJs Timeline-maskin
Allows selecting text from PDF preview canvas and copying to clipboard.
Works on PDFs with text layers (OCR'd or native text).
"""

import logging
import tkinter as tk

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFTextSelector:
    """Handles text selection on the PDF preview canvas.

    Constructor takes callback functions to access current PDF state
    from the preview panel without tight coupling.
    """

    def __init__(self, canvas, get_pdf_doc, get_current_page, get_effective_zoom):
        self._canvas = canvas
        self._get_pdf_doc = get_pdf_doc
        self._get_current_page = get_current_page
        self._get_effective_zoom = get_effective_zoom

        self._start_x = 0
        self._start_y = 0
        self._selection_rect_id = None
        self._feedback_ids = []

    def on_select_start(self, event):
        """Record start position and clear previous selection."""
        self.clear_selection()
        self._start_x = self._canvas.canvasx(event.x)
        self._start_y = self._canvas.canvasy(event.y)

    def on_select_motion(self, event):
        """Draw/update blue selection rectangle as user drags."""
        cur_x = self._canvas.canvasx(event.x)
        cur_y = self._canvas.canvasy(event.y)

        if self._selection_rect_id:
            self._canvas.delete(self._selection_rect_id)

        self._selection_rect_id = self._canvas.create_rectangle(
            self._start_x, self._start_y, cur_x, cur_y,
            outline="#4A90D9", width=2,
            fill="#4A90D9", stipple="gray25",
            tags="text_selection"
        )

    def on_select_end(self, event):
        """Extract text from selected area and copy to clipboard."""
        end_x = self._canvas.canvasx(event.x)
        end_y = self._canvas.canvasy(event.y)

        # Normalize coordinates (handle any drag direction)
        x0 = min(self._start_x, end_x)
        y0 = min(self._start_y, end_y)
        x1 = max(self._start_x, end_x)
        y1 = max(self._start_y, end_y)

        # Ignore tiny selections (likely accidental clicks)
        if (x1 - x0) < 5 or (y1 - y0) < 5:
            self.clear_selection()
            return

        # Convert canvas coords to PDF coords and extract text
        text = self._extract_text(x0, y0, x1, y1)

        if text and text.strip():
            # Copy to clipboard
            self._canvas.clipboard_clear()
            self._canvas.clipboard_append(text.strip())
            char_count = len(text.strip())
            self._show_feedback(f"Kopierat {char_count} tecken")
            logger.info(f"Text selection: copied {char_count} characters to clipboard")
        else:
            self._show_feedback("Ingen text hittad i markeringen")
            logger.info("Text selection: no text found in selection area")

    def clear_selection(self):
        """Remove selection rectangle from canvas."""
        if self._selection_rect_id:
            try:
                self._canvas.delete(self._selection_rect_id)
            except tk.TclError:
                pass
            self._selection_rect_id = None

    def reset(self):
        """Reset state when canvas is cleared (e.g. re-render)."""
        self._selection_rect_id = None

    def _extract_text(self, x0, y0, x1, y1):
        """Convert canvas coordinates to PDF space and extract text."""
        if not PYMUPDF_AVAILABLE:
            return ""

        doc = self._get_pdf_doc()
        if not doc:
            return ""

        page_num = self._get_current_page()
        zoom = self._get_effective_zoom()

        if zoom <= 0:
            return ""

        try:
            page = doc[page_num]

            # Canvas coords → PDF coords by dividing by effective zoom
            pdf_x0 = x0 / zoom
            pdf_y0 = y0 / zoom
            pdf_x1 = x1 / zoom
            pdf_y1 = y1 / zoom

            rect = fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1)
            text = page.get_text("text", clip=rect)
            return text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""

    def _show_feedback(self, message):
        """Show a temporary toast overlay on the canvas."""
        # Clear any previous feedback
        self._clear_feedback()

        # Position at top-center of visible canvas area
        visible_x = self._canvas.canvasx(self._canvas.winfo_width() / 2)
        visible_y = self._canvas.canvasy(30)

        # Background rounded rectangle (simulated with oval + rectangle)
        bg_id = self._canvas.create_rectangle(
            visible_x - 120, visible_y - 14,
            visible_x + 120, visible_y + 14,
            fill="#333333", outline="#333333",
            tags="text_feedback"
        )
        text_id = self._canvas.create_text(
            visible_x, visible_y,
            text=message,
            fill="white", font=("Arial", 11, "bold"),
            tags="text_feedback"
        )
        self._feedback_ids = [bg_id, text_id]

        # Auto-remove after 1.5 seconds
        self._canvas.after(1500, self._clear_feedback)

    def _clear_feedback(self):
        """Remove feedback toast from canvas."""
        for item_id in self._feedback_ids:
            try:
                self._canvas.delete(item_id)
            except tk.TclError:
                pass
        self._feedback_ids = []
