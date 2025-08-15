#!/usr/bin/env python3
"""
Undo/Redo functionality for DJs Timeline-maskin
Contains UndoManagerMixin class with all undo/redo methods
"""

# Standard library imports
import logging

# GUI imports
import tkinter as tk

# Setup logging
logger = logging.getLogger(__name__)


class UndoManagerMixin:
    """Mixin class containing all undo/redo functionality methods"""

    def verify_insertion(self, widget, field_name, expected_chunk):
        """Verify that the inserted text hasn't been corrupted by other events"""
        try:
            actual_content = widget.get("1.0", tk.END).strip()

            if actual_content != expected_chunk:
                logger.warning(f"TEXT CORRUPTION DETECTED in {field_name}!")
                logger.warning(f"Expected length: {len(expected_chunk)}, Actual length: {len(actual_content)}")
                logger.warning(f"Expected ends with: '{expected_chunk[-20:]}'")
                logger.warning(f"Actual ends with: '{actual_content[-20:]}'")

                # Fix the corruption by re-inserting the correct text
                widget.delete("1.0", tk.END)
                widget.insert("1.0", expected_chunk)
                logger.info(f"Fixed corruption in {field_name} by re-inserting correct text")
            else:
                logger.info(f"Verification OK for {field_name}: content matches expected")
        except Exception as e:
            logger.error(f"Error during verification of {field_name}: {e}")

    def handle_text_key_press_undo(self, event):
        """Handle key press in Text widget - create undo separator for character-by-character undo"""
        try:
            text_widget = event.widget
            if not isinstance(text_widget, tk.Text):
                return None

            # Skip control/modifier key combinations except for Tab
            if event.state & 0x4 and event.keysym != 'Tab':  # Control key pressed
                return None

            # Check if there's selected text that will be replaced
            has_selection = bool(text_widget.tag_ranges(tk.SEL))

            # Add separator for ANY character input or deletion
            if (len(event.char) == 1 and event.char.isprintable()) or event.keysym in ['Delete', 'BackSpace', 'Return', 'KP_Enter', 'Tab']:
                text_widget.edit_separator()

                # Log only for selections to reduce noise
                if has_selection:
                    logger.debug(f"Added undo separator before '{event.keysym}' over selection")

            # Allow the default key handling to proceed
            return None
        except (tk.TclError, AttributeError):
            # Error accessing selection or widget - let default handling proceed
            return None

    def handle_select_all_undo(self, event):
        """Handle Ctrl+A - prepare for potential undo separator if next operation modifies content"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # Mark that we just did a select all - next destructive operation should add separator
                focused_widget._select_all_pending = True
                logger.debug("Marked select-all pending for undo tracking")
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default select-all to proceed

    def handle_paste_undo(self, text_widget):
        """Handle Ctrl+V - paste with format preservation if available
        Now called directly on specific text widgets rather than globally"""
        logger.info("Direct paste handler executed")
        try:
            if isinstance(text_widget, tk.Text):
                # Add edit separator before paste
                text_widget.edit_separator()

                # Check if we have formatted content in internal clipboard
                if self.internal_clipboard:
                    text, tags_data = self.internal_clipboard

                    # Get cursor position or selection
                    try:
                        # Delete selection if exists
                        if text_widget.tag_ranges(tk.SEL):
                            text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                        insert_pos = text_widget.index(tk.INSERT)
                    except tk.TclError:
                        insert_pos = text_widget.index(tk.INSERT)

                    # Insert text
                    text_widget.insert(insert_pos, text)

                    # Apply formatting tags
                    for tag, rel_start, rel_end in tags_data:
                        tag_start = f"{insert_pos} + {rel_start}c"
                        tag_end = f"{insert_pos} + {rel_end}c"
                        text_widget.tag_add(tag, tag_start, tag_end)

                    # Add edit separator after paste
                    text_widget.edit_separator()

                    # Clear internal clipboard after use (single use)
                    self.internal_clipboard = None

                    # Trigger character count check after formatted paste
                    self.root.after_idle(lambda: self.check_character_count_for_widget(text_widget))

                    return "break"  # Prevent default paste
                else:
                    # No formatted content - perform regular paste with undo tracking
                    try:
                        # Get clipboard content
                        clipboard_content = self.root.clipboard_get()

                        # Check if there's selected text that will be replaced
                        has_selection = bool(text_widget.tag_ranges(tk.SEL))

                        # Or if we just did a select-all
                        select_all_pending = getattr(text_widget, '_select_all_pending', False)

                        if has_selection or select_all_pending:
                            # Save current content to our custom undo stack before replacing
                            current_content = text_widget.get("1.0", "end-1c")
                            self.save_text_undo_state(text_widget, current_content)

                            logger.info("Saved undo state before paste operation")

                        # Clear the select-all pending flag
                        if hasattr(text_widget, '_select_all_pending'):
                            delattr(text_widget, '_select_all_pending')

                        # Actually perform the paste operation
                        if has_selection:
                            # Delete selected text first
                            text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)

                        # Insert clipboard content at cursor position
                        insert_pos = text_widget.index(tk.INSERT)
                        text_widget.insert(insert_pos, clipboard_content)

                        # Schedule saving the post-paste content to our undo stack
                        self.root.after_idle(self.save_post_paste_state, text_widget)

                        # Add edit separator after paste
                        self.root.after_idle(lambda: text_widget.edit_separator())

                        # Trigger character count check after regular paste
                        self.root.after_idle(lambda: self.check_character_count_for_widget(text_widget))

                    except tk.TclError:
                        # No clipboard content or clipboard access failed
                        logger.debug("No clipboard content available for paste")

                # ALWAYS return "break" for Text widgets to prevent default paste
                return "break"
        except (tk.TclError, AttributeError) as e:
            logger.error(f"Error in paste handler: {e}")
        return "break"  # Always prevent default for direct widget calls

    def save_post_paste_state(self, text_widget):
        """Save the state after a paste operation completes"""
        try:
            if isinstance(text_widget, tk.Text):
                # Get the content after paste operation
                post_paste_content = text_widget.get("1.0", "end-1c")
                self.save_text_undo_state(text_widget, post_paste_content)
                logger.info("Saved post-paste content to undo stack")
        except (tk.TclError, AttributeError):
            pass

    def check_character_count_for_widget(self, text_widget):
        """Helper method to trigger character count check for a text widget after paste"""
        try:
            # Find which column this widget belongs to by checking widget references
            # This is needed because the paste handler doesn't know the column name
            for col_name, widgets in getattr(self, 'excel_widgets', {}).items():
                if hasattr(widgets, 'text_widget') and widgets.text_widget == text_widget:
                    # Create a dummy event for character count checking
                    class DummyEvent:
                        def __init__(self, widget):
                            self.widget = widget

                    self.check_character_count(DummyEvent(text_widget), col_name)
                    break
                elif widgets == text_widget:  # Direct widget reference
                    self.check_character_count(DummyEvent(text_widget), col_name)
                    break
        except (AttributeError, TypeError):
            # If we can't determine the column, skip character count check
            pass

    def handle_copy_with_format(self, event):
        """Handle Ctrl+C - copy text with formatting to internal clipboard"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                try:
                    # Get selection bounds
                    start = focused_widget.index(tk.SEL_FIRST)
                    end = focused_widget.index(tk.SEL_LAST)

                    # Get selected text
                    text = focused_widget.get(start, end)

                    # Get all formatting tags in selection
                    tags_data = []
                    for tag in ["bold", "red", "blue", "green", "default"]:
                        tag_ranges = focused_widget.tag_ranges(tag)
                        for i in range(0, len(tag_ranges), 2):
                            tag_start = tag_ranges[i]
                            tag_end = tag_ranges[i + 1]
                            # Check if tag overlaps with selection
                            if focused_widget.compare(tag_start, "<", end) and focused_widget.compare(tag_end, ">", start):
                                # Calculate relative positions within selection
                                rel_start = max(0, len(focused_widget.get(start, tag_start)))
                                rel_end = min(len(text), len(focused_widget.get(start, tag_end)))
                                tags_data.append((tag, rel_start, rel_end))

                    # Store in internal clipboard
                    self.internal_clipboard = (text, tags_data)

                    # Also copy to system clipboard (plain text)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)

                except tk.TclError:
                    # No selection
                    pass
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default handling

    def handle_cut_with_format(self, event):
        """Handle Ctrl+X - cut text with formatting to internal clipboard"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # First copy with format
                self.handle_copy_with_format(event)

                # Then delete selection with undo support
                if focused_widget.tag_ranges(tk.SEL):
                    focused_widget.edit_separator()
                    focused_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    focused_widget.edit_separator()
                    return "break"  # Prevent default cut
        except (tk.TclError, AttributeError):
            pass
        return None

    def handle_delete_with_undo(self, event):
        """Handle Delete/BackSpace - prepare undo state before deletion"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # Check if there's selected text that will be deleted
                has_selection = bool(focused_widget.tag_ranges(tk.SEL))

                # Or if we just did a select-all
                select_all_pending = getattr(focused_widget, '_select_all_pending', False)

                if has_selection or select_all_pending:
                    # Save current content to our custom undo stack
                    current_content = focused_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(focused_widget, current_content)

                    logger.info(f"Saved undo state before {event.keysym} operation")

                # Clear the select-all pending flag
                if hasattr(focused_widget, '_select_all_pending'):
                    delattr(focused_widget, '_select_all_pending')
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default delete to proceed

    def handle_delete_key_undo(self, event):
        """Handle Delete/BackSpace key press - create undo separator when deleting selection"""
        try:
            text_widget = event.widget
            if isinstance(text_widget, tk.Text):
                # Check if there's selected text that will be deleted
                if text_widget.tag_ranges(tk.SEL):
                    text_widget.edit_separator()
                    logger.info(f"Added undo separator before {event.keysym} on selection")

            # Allow the default key handling to proceed
            return None
        except (tk.TclError, AttributeError):
            # Error accessing selection or widget - let default handling proceed
            return None

    def setup_undo_functionality(self):
        """Setup keyboard bindings for undo/redo"""
        # Bind global keyboard shortcuts
        self.root.bind_all('<Control-z>', self.global_undo)
        self.root.bind_all('<Control-y>', self.global_redo)
        self.root.bind_all('<Control-Shift-Z>', self.global_redo)  # Alternative redo binding

        # Add enhanced bindings for Text widgets to handle problematic operations
        self.root.bind_all('<Control-a>', self.handle_select_all_undo)
        self.root.bind_all('<Control-c>', self.handle_copy_with_format)
        self.root.bind_all('<Control-x>', self.handle_cut_with_format)
        # NOTE: Paste binding removed - now handled directly on each Text widget
        self.root.bind_all('<Delete>', self.handle_delete_with_undo)
        self.root.bind_all('<BackSpace>', self.handle_delete_with_undo)

    def global_undo(self, event=None):
        """Global undo function that works on focused widget"""
        focused_widget = self.root.focus_get()
        if focused_widget and focused_widget in self.undo_widgets:
            # For Text widgets, try custom undo first, then fallback to edit_undo
            if isinstance(focused_widget, tk.Text):
                # Try custom undo first for problematic operations
                if self.text_widget_undo(focused_widget):
                    return "break"  # Prevent default handling
                else:
                    # Fallback to built-in undo
                    try:
                        focused_widget.edit_undo()
                        return "break"  # Prevent default handling
                    except tk.TclError:
                        # No undo available
                        pass
            # For Entry widgets, use our custom undo system
            elif hasattr(focused_widget, 'get') and hasattr(focused_widget, 'delete'):
                if self.undo_entry_widget(focused_widget):
                    return "break"  # Prevent default handling
        return None

    def global_redo(self, event=None):
        """Global redo function that works on focused widget"""
        focused_widget = self.root.focus_get()
        if focused_widget and focused_widget in self.undo_widgets:
            # For Text widgets, try custom redo first, then fallback to edit_redo
            if isinstance(focused_widget, tk.Text):
                # Try custom redo first for problematic operations
                if self.text_widget_redo(focused_widget):
                    return "break"  # Prevent default handling
                else:
                    # Fallback to built-in redo
                    try:
                        focused_widget.edit_redo()
                        return "break"  # Prevent default handling
                    except tk.TclError:
                        # No redo available
                        pass
            # For Entry widgets, use our custom redo system
            elif hasattr(focused_widget, 'get') and hasattr(focused_widget, 'delete'):
                if self.redo_entry_widget(focused_widget):
                    return "break"  # Prevent default handling
        return None

    def enable_undo_for_widget(self, widget):
        """Enable undo/redo for a specific widget and add to tracking list"""
        if hasattr(widget, 'config'):
            # Only enable undo for Text widgets (Entry widgets don't reliably support undo parameter)
            if isinstance(widget, tk.Text):
                widget.configure(undo=True, maxundo=20)
            elif hasattr(widget, 'get') and hasattr(widget, 'delete'):
                # This is an Entry widget - set up custom undo tracking
                self.setup_entry_undo(widget)

            # Add to our tracking list for global undo/redo handling
            if widget not in self.undo_widgets:
                self.undo_widgets.append(widget)

    def setup_entry_undo(self, entry_widget):
        """Set up custom undo tracking for an Entry widget"""
        # Initialize undo/redo stacks for this widget
        widget_id = id(entry_widget)
        self.entry_undo_stacks[widget_id] = []
        self.entry_redo_stacks[widget_id] = []

        # Store the initial value
        initial_value = entry_widget.get()
        self.entry_undo_stacks[widget_id].append(initial_value)

        # Bind events to track changes
        entry_widget.bind('<KeyRelease>', lambda e: self.on_entry_change(entry_widget, e))
        entry_widget.bind('<FocusOut>', lambda e: self.on_entry_change(entry_widget, e))
        entry_widget.bind('<Button-1>', lambda e: self.on_entry_change(entry_widget, e))

    def on_entry_change(self, entry_widget, event=None):
        """Called when an Entry widget changes - save to undo stack"""
        widget_id = id(entry_widget)
        current_value = entry_widget.get()

        # Get the last saved value
        if widget_id in self.entry_undo_stacks and self.entry_undo_stacks[widget_id]:
            last_value = self.entry_undo_stacks[widget_id][-1]

            # Only save if the value has actually changed
            if current_value != last_value:
                # Add to undo stack
                self.entry_undo_stacks[widget_id].append(current_value)

                # Limit the undo stack size
                if len(self.entry_undo_stacks[widget_id]) > self.max_undo_levels:
                    self.entry_undo_stacks[widget_id].pop(0)

                # Clear redo stack when new change is made
                self.entry_redo_stacks[widget_id] = []

    def undo_entry_widget(self, entry_widget):
        """Perform undo on an Entry widget"""
        widget_id = id(entry_widget)

        if widget_id not in self.entry_undo_stacks:
            return False

        undo_stack = self.entry_undo_stacks[widget_id]
        redo_stack = self.entry_redo_stacks[widget_id]

        # Need at least 2 items (current + previous)
        if len(undo_stack) < 2:
            return False

        # Move current value to redo stack
        current_value = undo_stack.pop()
        redo_stack.append(current_value)

        # Get previous value and set it
        previous_value = undo_stack[-1]
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, previous_value)

        return True

    def redo_entry_widget(self, entry_widget):
        """Perform redo on an Entry widget"""
        widget_id = id(entry_widget)

        if widget_id not in self.entry_redo_stacks:
            return False

        undo_stack = self.entry_undo_stacks[widget_id]
        redo_stack = self.entry_redo_stacks[widget_id]

        # Need at least 1 item in redo stack
        if len(redo_stack) < 1:
            return False

        # Move value from redo to undo stack
        redo_value = redo_stack.pop()
        undo_stack.append(redo_value)

        # Set the redo value
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, redo_value)

        return True

    def save_text_undo_state(self, text_widget, content):
        """Save text widget state with formatting to custom undo stack"""
        widget_id = id(text_widget)

        # Initialize stacks if not exists
        if widget_id not in self.text_undo_stacks:
            self.text_undo_stacks[widget_id] = []
            self.text_redo_stacks[widget_id] = []

        # Collect all formatting tags
        tags_data = []
        for tag in ["bold", "red", "blue", "green", "default"]:
            tag_ranges = text_widget.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start_idx = str(tag_ranges[i])
                end_idx = str(tag_ranges[i + 1])
                tags_data.append((tag, start_idx, end_idx))

        # Create state tuple with content and tags
        state = (content, tags_data)

        # Don't add duplicate content to avoid double-undo issues
        if self.text_undo_stacks[widget_id] and self.text_undo_stacks[widget_id][-1][0] == content:
            return

        # Add to undo stack
        self.text_undo_stacks[widget_id].append(state)

        # Limit stack size
        if len(self.text_undo_stacks[widget_id]) > self.max_undo_levels:
            self.text_undo_stacks[widget_id].pop(0)

        # Clear redo stack when new state is saved
        self.text_redo_stacks[widget_id] = []

    def text_widget_undo(self, text_widget):
        """Perform undo on Text widget with formatting using custom stack"""
        widget_id = id(text_widget)

        if widget_id not in self.text_undo_stacks or len(self.text_undo_stacks[widget_id]) < 2:
            return False

        undo_stack = self.text_undo_stacks[widget_id]
        redo_stack = self.text_redo_stacks[widget_id]

        # Save current state to redo stack
        current_content = text_widget.get("1.0", "end-1c")
        current_tags = []
        for tag in ["bold", "red", "blue", "green", "default"]:
            tag_ranges = text_widget.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start_idx = str(tag_ranges[i])
                end_idx = str(tag_ranges[i + 1])
                current_tags.append((tag, start_idx, end_idx))
        redo_stack.append((current_content, current_tags))

        # Remove the current state from undo stack
        undo_stack.pop()

        # Get the previous state from undo stack
        if undo_stack:
            previous_content, previous_tags = undo_stack[-1]
        else:
            previous_content, previous_tags = "", []

        # Restore content
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", previous_content)

        # Restore formatting
        for tag, start_idx, end_idx in previous_tags:
            try:
                text_widget.tag_add(tag, start_idx, end_idx)
            except tk.TclError:
                # Handle invalid indices
                pass

        logger.info("Performed custom undo on Text widget with formatting")
        return True

    def text_widget_redo(self, text_widget):
        """Perform redo on Text widget with formatting using custom stack"""
        widget_id = id(text_widget)

        if widget_id not in self.text_redo_stacks or not self.text_redo_stacks[widget_id]:
            return False

        undo_stack = self.text_undo_stacks[widget_id]
        redo_stack = self.text_redo_stacks[widget_id]

        # Get next state from redo stack
        next_content, next_tags = redo_stack.pop()

        # Save current state to undo stack
        current_content = text_widget.get("1.0", "end-1c")
        current_tags = []
        for tag in ["bold", "red", "blue", "green", "default"]:
            tag_ranges = text_widget.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start_idx = str(tag_ranges[i])
                end_idx = str(tag_ranges[i + 1])
                current_tags.append((tag, start_idx, end_idx))
        undo_stack.append((current_content, current_tags))

        # Restore content
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", next_content)

        # Restore formatting
        for tag, start_idx, end_idx in next_tags:
            try:
                text_widget.tag_add(tag, start_idx, end_idx)
            except tk.TclError:
                # Handle invalid indices
                pass

        logger.info("Performed custom redo on Text widget with formatting")
        return True
