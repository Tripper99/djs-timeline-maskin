#!/usr/bin/env python3
"""
Test app for debugging rich text formatting issues.
Isolates tkinter Text widget → Excel rich text conversion problems.
Contains Method 2: Character-by-character processing - the BREAKTHROUGH algorithm
"""

import logging
import sys
import tkinter as tk
from tkinter import ttk

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.cell.rich_text import CellRichText, TextBlock
    from openpyxl.cell.text import InlineFont
    from openpyxl.styles.colors import Color
except ImportError as e:
    logger.error(f"Required module not found: {e}")
    sys.exit(1)

class RichTextTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rich Text Testing App v1.0")
        self.root.geometry("800x600")

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Rich Text Testing App",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Formatting buttons frame
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10))

        ttk.Label(format_frame, text="Formatting:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Formatting buttons
        self.bold_btn = tk.Button(format_frame, text="B", font=('Arial', 9, 'bold'),
                                 command=self.toggle_bold, width=3)
        self.bold_btn.grid(row=1, column=0, padx=(0, 5))

        self.italic_btn = tk.Button(format_frame, text="I", font=('Arial', 9, 'italic'),
                                   command=self.toggle_italic, width=3)
        self.italic_btn.grid(row=1, column=1, padx=(0, 5))

        self.red_btn = tk.Button(format_frame, text="R", fg="red",
                                command=self.toggle_red, width=3)
        self.red_btn.grid(row=2, column=0, padx=(0, 5), pady=(5, 0))

        self.blue_btn = tk.Button(format_frame, text="B", fg="blue",
                                 command=self.toggle_blue, width=3)
        self.blue_btn.grid(row=2, column=1, padx=(0, 5), pady=(5, 0))

        self.green_btn = tk.Button(format_frame, text="G", fg="green",
                                  command=self.toggle_green, width=3)
        self.green_btn.grid(row=2, column=2, pady=(5, 0))

        # Test buttons
        ttk.Separator(format_frame, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)

        ttk.Label(format_frame, text="Tests:", font=('Arial', 10, 'bold')).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        self.test1_btn = ttk.Button(format_frame, text="Test Method 1\n(Current)",
                                   command=self.test_method1)
        self.test1_btn.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))

        self.test2_btn = ttk.Button(format_frame, text="Test Method 2\n(Pure openpyxl)",
                                   command=self.test_method2)
        self.test2_btn.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))

        self.test3_btn = ttk.Button(format_frame, text="Test Method 3\n(Alternative)",
                                   command=self.test_method3)
        self.test3_btn.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))

        self.clear_btn = ttk.Button(format_frame, text="Clear Text",
                                   command=self.clear_text)
        self.clear_btn.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        # Text widget
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        ttk.Label(text_frame, text="Rich Text Editor:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # Create text widget with scrollbar
        text_container = ttk.Frame(text_frame)
        text_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        self.text_widget = tk.Text(text_container, wrap=tk.WORD, width=50, height=20,
                                  font=('Arial', 10))
        self.text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.text_widget.config(yscrollcommand=scrollbar.set)

        # Configure text formatting tags
        self.setup_text_tags()

        # Add sample text
        self.add_sample_text()

        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to test rich text formatting",
                                     foreground="green")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    def setup_text_tags(self):
        """Configure formatting tags for the text widget"""
        self.text_widget.tag_configure("bold", font=('Arial', 10, 'bold'))
        self.text_widget.tag_configure("italic", font=('Arial', 10, 'italic'))
        self.text_widget.tag_configure("red", foreground="red")
        self.text_widget.tag_configure("blue", foreground="blue")
        self.text_widget.tag_configure("green", foreground="green")

    def add_sample_text(self):
        """Add sample formatted text for testing - using problematic long text"""
        # Use the exact long text that causes problems
        self.text_widget.insert("1.0", "Text som är oformaterad. \n\n")

        # Blue text
        start_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.insert(tk.INSERT, "Blå text. Röd text som kommer direkt efter den blå utan radbrytning.  \n\n")
        # Apply blue to only "Blå text."
        blue_end = f"{start_pos} +9c"
        self.text_widget.tag_add("blue", start_pos, blue_end)
        # Apply red to "Röd text som kommer direkt efter den blå utan radbrytning."
        red_start = f"{start_pos} +10c"
        red_end = f"{start_pos} +71c"
        self.text_widget.tag_add("red", red_start, red_end)

        # Green text (two parts)
        start_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.insert(tk.INSERT, "Grön text som kommer en blankrad ned. Och här är lite mer grön text. \n\n")
        self.text_widget.tag_add("green", start_pos, f"{start_pos} +68c")

        # Plain text
        self.text_widget.insert(tk.INSERT, "Den här texten är också plain text. \n\n")

        # Blue bold text
        start_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.insert(tk.INSERT, "Blå fet text Bergwall dömdes för åtta mord.\n\n")
        self.text_widget.tag_add("blue", start_pos, f"{start_pos} +40c")
        self.text_widget.tag_add("bold", start_pos, f"{start_pos} +40c")

        # Green italic text
        start_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.insert(tk.INSERT, "Grön kursiv text. \n\n")
        self.text_widget.tag_add("green", start_pos, f"{start_pos} +17c")
        self.text_widget.tag_add("italic", start_pos, f"{start_pos} +17c")

        # Final plain text
        self.text_widget.insert(tk.INSERT, "Och här kommer ännu en text som saknar formattering.")

    def get_selected_range(self):
        """Get the currently selected text range"""
        try:
            return self.text_widget.tag_ranges(tk.SEL)
        except tk.TclError:
            # No selection, use insertion cursor
            pos = self.text_widget.index(tk.INSERT)
            return (pos, pos)

    def toggle_bold(self):
        """Toggle bold formatting for selected text"""
        try:
            sel_start, sel_end = self.text_widget.tag_ranges(tk.SEL)
            current_tags = self.text_widget.tag_names(sel_start)

            if "bold" in current_tags:
                self.text_widget.tag_remove("bold", sel_start, sel_end)
            else:
                self.text_widget.tag_add("bold", sel_start, sel_end)
        except ValueError:
            self.status_label.config(text="Please select text to format", foreground="orange")

    def toggle_italic(self):
        """Toggle italic formatting for selected text"""
        try:
            sel_start, sel_end = self.text_widget.tag_ranges(tk.SEL)
            current_tags = self.text_widget.tag_names(sel_start)

            if "italic" in current_tags:
                self.text_widget.tag_remove("italic", sel_start, sel_end)
            else:
                self.text_widget.tag_add("italic", sel_start, sel_end)
        except ValueError:
            self.status_label.config(text="Please select text to format", foreground="orange")

    def toggle_red(self):
        """Toggle red color for selected text"""
        try:
            sel_start, sel_end = self.text_widget.tag_ranges(tk.SEL)
            # Remove other colors first
            for color in ["red", "blue", "green"]:
                self.text_widget.tag_remove(color, sel_start, sel_end)
            self.text_widget.tag_add("red", sel_start, sel_end)
        except ValueError:
            self.status_label.config(text="Please select text to format", foreground="orange")

    def toggle_blue(self):
        """Toggle blue color for selected text"""
        try:
            sel_start, sel_end = self.text_widget.tag_ranges(tk.SEL)
            # Remove other colors first
            for color in ["red", "blue", "green"]:
                self.text_widget.tag_remove(color, sel_start, sel_end)
            self.text_widget.tag_add("blue", sel_start, sel_end)
        except ValueError:
            self.status_label.config(text="Please select text to format", foreground="orange")

    def toggle_green(self):
        """Toggle green color for selected text"""
        try:
            sel_start, sel_end = self.text_widget.tag_ranges(tk.SEL)
            # Remove other colors first
            for color in ["red", "blue", "green"]:
                self.text_widget.tag_remove(color, sel_start, sel_end)
            self.text_widget.tag_add("green", sel_start, sel_end)
        except ValueError:
            self.status_label.config(text="Please select text to format", foreground="orange")

    def clear_text(self):
        """Clear all text from the widget"""
        self.text_widget.delete("1.0", tk.END)
        self.status_label.config(text="Text cleared", foreground="blue")

    def test_method1(self):
        """Test Method 1: Current approach from main app"""
        logger.info("=== Testing Method 1: Current approach ===")
        self.status_label.config(text="Testing Method 1...", foreground="blue")

        try:
            rich_text = self.get_formatted_text_method1()
            success = self.write_to_excel(rich_text, "test_method1.xlsx")

            if success:
                self.status_label.config(text="Method 1: SUCCESS - Check test_method1.xlsx",
                                       foreground="green")
            else:
                self.status_label.config(text="Method 1: FAILED - See console",
                                       foreground="red")

        except Exception as e:
            logger.error(f"Method 1 failed: {e}")
            self.status_label.config(text=f"Method 1: ERROR - {str(e)[:50]}...",
                                   foreground="red")

    def test_method2(self):
        """Test Method 2: BREAKTHROUGH Character-by-character algorithm"""
        logger.info("=== Testing Method 2: CHARACTER-BY-CHARACTER (BREAKTHROUGH) ===")
        self.status_label.config(text="Testing Method 2...", foreground="blue")

        try:
            rich_text = self.get_formatted_text_method2()
            success = self.write_to_excel_pure(rich_text, "test_method2.xlsx")

            if success:
                self.status_label.config(text="Method 2: SUCCESS - Check test_method2.xlsx",
                                       foreground="green")
            else:
                self.status_label.config(text="Method 2: FAILED - See console",
                                       foreground="red")

        except Exception as e:
            logger.error(f"Method 2 failed: {e}")
            self.status_label.config(text=f"Method 2: ERROR - {str(e)[:50]}...",
                                   foreground="red")

    def test_method3(self):
        """Test Method 3: Alternative approach"""
        logger.info("=== Testing Method 3: Alternative approach ===")
        self.status_label.config(text="Testing Method 3...", foreground="blue")

        try:
            rich_text = self.get_formatted_text_method3()
            success = self.write_to_excel_pure(rich_text, "test_method3.xlsx")

            if success:
                self.status_label.config(text="Method 3: SUCCESS - Check test_method3.xlsx",
                                       foreground="green")
            else:
                self.status_label.config(text="Method 3: FAILED - See console",
                                       foreground="red")

        except Exception as e:
            logger.error(f"Method 3 failed: {e}")
            self.status_label.config(text=f"Method 3: ERROR - {str(e)[:50]}...",
                                   foreground="red")

    def get_formatted_text_method1(self):
        """Method 1: Current approach from main app (similar to _rebuild_richtext_from_widget)"""
        # Get plain text
        plain_text = self.text_widget.get("1.0", "end-1c")
        logger.info(f"Plain text: '{plain_text}'")

        # Check if there are any formatting tags
        all_tags = self.text_widget.tag_names()
        format_tags = [tag for tag in all_tags if tag in ["bold", "italic", "red", "blue", "green", "black"]]

        logger.info(f"Format tags found: {format_tags}")

        if not format_tags:
            logger.info("No formatting, returning plain text")
            return plain_text

        # Build CellRichText structure
        rich_text_parts = []

        # Collect all format change positions
        format_positions = set(["1.0"])
        for tag in format_tags:
            tag_ranges = self.text_widget.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start_idx = str(tag_ranges[i])
                end_idx = str(tag_ranges[i + 1])
                format_positions.add(start_idx)
                format_positions.add(end_idx)

        # Add end position
        format_positions.add("end-1c")

        # Sort positions
        sorted_positions = sorted(format_positions, key=lambda pos: self.text_widget.index(pos))
        logger.info(f"Format positions: {sorted_positions}")

        # Process each segment
        for i in range(len(sorted_positions) - 1):
            start_pos = sorted_positions[i]
            end_pos = sorted_positions[i + 1]

            # Skip empty segments
            if self.text_widget.compare(start_pos, "==", end_pos):
                continue

            # Get text for this segment
            segment_text = self.text_widget.get(start_pos, end_pos)
            if not segment_text:
                continue

            # Find active tags at start of segment
            active_tags = []
            for tag in format_tags:
                tag_ranges = self.text_widget.tag_ranges(tag)
                for j in range(0, len(tag_ranges), 2):
                    tag_start = tag_ranges[j]
                    tag_end = tag_ranges[j + 1]
                    if (self.text_widget.compare(start_pos, ">=", tag_start) and
                        self.text_widget.compare(start_pos, "<", tag_end)):
                        active_tags.append(tag)
                        break

            logger.info(f"Segment '{segment_text[:30]}...' has tags: {active_tags}")

            if active_tags:
                # Create TextBlock with formatting
                font_kwargs = {}
                for tag in active_tags:
                    if tag == "bold":
                        font_kwargs['b'] = True
                    elif tag == "italic":
                        font_kwargs['i'] = True
                    elif tag == "red":
                        font_kwargs['color'] = Color(rgb="FF0000")
                    elif tag == "blue":
                        font_kwargs['color'] = Color(rgb="0000FF")
                    elif tag == "green":
                        font_kwargs['color'] = Color(rgb="008000")

                font = InlineFont(**font_kwargs)
                textblock = TextBlock(font, segment_text)
                rich_text_parts.append(textblock)
                logger.info(f"Added TextBlock: '{segment_text[:30]}...' with {font_kwargs}")
            else:
                # Plain text segment
                rich_text_parts.append(segment_text)
                logger.info(f"Added plain text: '{segment_text[:30]}...'")

        if rich_text_parts:
            result = CellRichText(*rich_text_parts)
            logger.info(f"Created CellRichText with {len(result)} parts")

            # Debug: log the structure
            for i, part in enumerate(result):
                if hasattr(part, 'text'):
                    logger.info(f"Part {i}: TextBlock '{part.text[:30]}...'")
                else:
                    logger.info(f"Part {i}: String '{str(part)[:30]}...'")

            return result
        else:
            return plain_text

    def get_formatted_text_method2(self):
        """Method 2: CHARACTER-BY-CHARACTER BREAKTHROUGH ALGORITHM - processes text sequentially"""
        plain_text = self.text_widget.get("1.0", "end-1c")
        logger.info(f"Method 2 - Plain text: '{plain_text}'")

        # Simple approach: process text sequentially
        rich_parts = []
        current_pos = "1.0"

        # Get all text
        text_end = self.text_widget.index("end-1c")

        # Iterate through text character by character
        while self.text_widget.compare(current_pos, "<", text_end):
            next_pos = f"{current_pos} +1c"
            char = self.text_widget.get(current_pos, next_pos)

            # Get tags at current position
            tags_at_pos = self.text_widget.tag_names(current_pos)
            format_tags = [tag for tag in tags_at_pos if tag in ["bold", "italic", "red", "blue", "green"]]

            # Build text with same formatting
            text_with_format = char
            temp_pos = next_pos

            # Continue until formatting changes
            while self.text_widget.compare(temp_pos, "<", text_end):
                temp_tags = self.text_widget.tag_names(temp_pos)
                temp_format_tags = [tag for tag in temp_tags if tag in ["bold", "italic", "red", "blue", "green"]]

                if set(format_tags) != set(temp_format_tags):
                    break

                next_char_pos = f"{temp_pos} +1c"
                text_with_format += self.text_widget.get(temp_pos, next_char_pos)
                temp_pos = next_char_pos

            # Create appropriate part
            if format_tags:
                font_kwargs = {}
                for tag in format_tags:
                    if tag == "bold":
                        font_kwargs['b'] = True
                    elif tag == "italic":
                        font_kwargs['i'] = True
                    elif tag == "red":
                        font_kwargs['color'] = Color(rgb="FF0000")
                    elif tag == "blue":
                        font_kwargs['color'] = Color(rgb="0000FF")
                    elif tag == "green":
                        font_kwargs['color'] = Color(rgb="008000")

                if font_kwargs:
                    font = InlineFont(**font_kwargs)
                    rich_parts.append(TextBlock(font, text_with_format))
                    logger.info(f"Method 2 - Added TextBlock: '{text_with_format[:30]}...' with {font_kwargs}")
                else:
                    rich_parts.append(text_with_format)
                    logger.info(f"Method 2 - Added plain: '{text_with_format[:30]}...'")
            else:
                rich_parts.append(text_with_format)
                logger.info(f"Method 2 - Added plain: '{text_with_format[:30]}...'")

            current_pos = temp_pos

        if any(isinstance(part, TextBlock) for part in rich_parts):
            result = CellRichText(*rich_parts)
            logger.info(f"Method 2 - Created CellRichText with {len(result)} parts")
            return result
        else:
            return plain_text

    def get_formatted_text_method3(self):
        """Method 3: Alternative approach - build from text runs"""
        plain_text = self.text_widget.get("1.0", "end-1c")
        logger.info(f"Method 3 - Plain text: '{plain_text}'")

        # Get all format tags and their ranges
        format_tags = ["bold", "italic", "red", "blue", "green"]
        tag_info = {}

        for tag in format_tags:
            ranges = self.text_widget.tag_ranges(tag)
            if ranges:
                tag_info[tag] = [(str(ranges[i]), str(ranges[i+1])) for i in range(0, len(ranges), 2)]
                logger.info(f"Method 3 - Tag '{tag}' ranges: {tag_info[tag]}")

        # If no formatting, return plain text
        if not tag_info:
            return plain_text

        # Create segments based on all format boundaries
        boundaries = set(["1.0", "end-1c"])
        for tag_ranges in tag_info.values():
            for start, end in tag_ranges:
                boundaries.add(start)
                boundaries.add(end)

        sorted_boundaries = sorted(boundaries, key=lambda pos: self.text_widget.index(pos))
        logger.info(f"Method 3 - Boundaries: {sorted_boundaries}")

        rich_parts = []
        for i in range(len(sorted_boundaries) - 1):
            start = sorted_boundaries[i]
            end = sorted_boundaries[i + 1]

            if self.text_widget.compare(start, "==", end):
                continue

            segment_text = self.text_widget.get(start, end)
            if not segment_text:
                continue

            # Find which tags apply to this segment
            active_tags = []
            mid_point = f"{start} +1c"  # Test point within segment

            for tag, ranges in tag_info.items():
                for range_start, range_end in ranges:
                    if (self.text_widget.compare(mid_point, ">=", range_start) and
                        self.text_widget.compare(mid_point, "<=", range_end)):
                        active_tags.append(tag)
                        break

            logger.info(f"Method 3 - Segment '{segment_text[:30]}...' tags: {active_tags}")

            if active_tags:
                font_kwargs = {}
                for tag in active_tags:
                    if tag == "bold":
                        font_kwargs['b'] = True
                    elif tag == "italic":
                        font_kwargs['i'] = True
                    elif tag == "red":
                        font_kwargs['color'] = Color(rgb="FF0000")
                    elif tag == "blue":
                        font_kwargs['color'] = Color(rgb="0000FF")
                    elif tag == "green":
                        font_kwargs['color'] = Color(rgb="008000")

                if font_kwargs:
                    font = InlineFont(**font_kwargs)
                    rich_parts.append(TextBlock(font, segment_text))
                else:
                    rich_parts.append(segment_text)
            else:
                rich_parts.append(segment_text)

        if any(isinstance(part, TextBlock) for part in rich_parts):
            result = CellRichText(*rich_parts)
            logger.info(f"Method 3 - Created CellRichText with {len(result)} parts")

            # Debug structure
            for i, part in enumerate(result):
                if hasattr(part, 'text'):
                    logger.info(f"Method 3 - Part {i}: TextBlock '{part.text[:30]}...'")
                else:
                    logger.info(f"Method 3 - Part {i}: String '{str(part)[:30]}...'")

            return result
        else:
            return plain_text

    def write_to_excel(self, rich_text, filename):
        """Write rich text to Excel using current app approach (hybrid)"""
        try:
            # This simulates the current app's approach but simplified
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Rich Text Test"

            # Write to cell A1
            worksheet['A1'] = rich_text

            # Save
            workbook.save(filename)
            logger.info(f"Saved to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to write to Excel: {e}")
            return False

    def write_to_excel_pure(self, rich_text, filename):
        """Write rich text to Excel using pure openpyxl"""
        try:
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Rich Text Test"

            # Set cell value
            cell = worksheet['A1']
            cell.value = rich_text

            # Save
            workbook.save(filename)
            logger.info(f"Saved to {filename} using pure openpyxl")
            return True

        except Exception as e:
            logger.error(f"Failed to write to Excel with pure openpyxl: {e}")
            return False

    def run(self):
        """Start the test application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = RichTextTester()
    app.run()
