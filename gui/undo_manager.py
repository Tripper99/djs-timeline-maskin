#!/usr/bin/env python3
"""
Undo/Redo functionality for DJs Timeline-maskin
Contains UndoManagerMixin class with all undo/redo methods

Single custom snapshot-based undo system for Text widgets.
Tk's built-in undo is disabled to prevent interference.
Debounced typing snapshots (500ms) provide phrase-level undo.
"""

# Standard library imports
import logging
import time

# GUI imports
import tkinter as tk

# Setup logging
logger = logging.getLogger(__name__)

# Debounce interval for typing snapshots (seconds)
TYPING_SNAPSHOT_DELAY_MS = 500
# Maximum time between forced snapshots (seconds)
MAX_SNAPSHOT_INTERVAL = 3.0


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

    # ── Debounce timer management ──────────────────────────────────

    def _schedule_undo_snapshot(self, text_widget):
        """Cancel pending timer, schedule new snapshot after 500ms pause.
        Also force-save if >3 seconds since last snapshot."""
        widget_id = id(text_widget)

        # Cancel any existing timer
        self._cancel_undo_timer(text_widget)

        # Check if we need a forced save (>3 seconds since last snapshot)
        last_save_time = getattr(self, '_last_snapshot_time', {}).get(widget_id, 0)
        now = time.time()
        if now - last_save_time > MAX_SNAPSHOT_INTERVAL and last_save_time > 0:
            self._save_typing_snapshot(text_widget)
            # Schedule a new timer for the next pause
            timer_id = self.root.after(
                TYPING_SNAPSHOT_DELAY_MS,
                lambda: self._save_typing_snapshot(text_widget)
            )
            if not hasattr(self, '_undo_timers'):
                self._undo_timers = {}
            self._undo_timers[widget_id] = timer_id
            return

        # Schedule a new timer
        timer_id = self.root.after(
            TYPING_SNAPSHOT_DELAY_MS,
            lambda: self._save_typing_snapshot(text_widget)
        )
        if not hasattr(self, '_undo_timers'):
            self._undo_timers = {}
        self._undo_timers[widget_id] = timer_id

    def _save_typing_snapshot(self, text_widget):
        """Save current content+formatting to undo stack (debounce callback)."""
        widget_id = id(text_widget)

        # Clear the timer reference
        if hasattr(self, '_undo_timers') and widget_id in self._undo_timers:
            self._undo_timers[widget_id] = None

        try:
            content = text_widget.get("1.0", "end-1c")
            self.save_text_undo_state(text_widget, content)

            # Update last snapshot time
            if not hasattr(self, '_last_snapshot_time'):
                self._last_snapshot_time = {}
            self._last_snapshot_time[widget_id] = time.time()

            logger.debug(f"Saved typing snapshot for widget {widget_id}")
        except tk.TclError:
            pass

    def _cancel_undo_timer(self, text_widget):
        """Cancel pending debounce timer without saving."""
        widget_id = id(text_widget)
        if hasattr(self, '_undo_timers') and widget_id in self._undo_timers:
            timer_id = self._undo_timers[widget_id]
            if timer_id is not None:
                self.root.after_cancel(timer_id)
                self._undo_timers[widget_id] = None

    def _flush_undo_timer(self, text_widget):
        """Cancel timer AND immediately save if one was pending."""
        widget_id = id(text_widget)
        if hasattr(self, '_undo_timers') and widget_id in self._undo_timers:
            timer_id = self._undo_timers[widget_id]
            if timer_id is not None:
                self.root.after_cancel(timer_id)
                self._undo_timers[widget_id] = None
                # Save the snapshot now
                self._save_typing_snapshot(text_widget)

    # ── Key press handlers ─────────────────────────────────────────

    def handle_text_key_press_undo(self, event):
        """Handle key press in Text widget - schedule debounced undo snapshot"""
        try:
            text_widget = event.widget
            if not isinstance(text_widget, tk.Text):
                return None

            # Skip control/modifier key combinations except for Tab
            if event.state & 0x4 and event.keysym != 'Tab':  # Control key pressed
                return None

            # Printable char, Return, or Tab → schedule debounced snapshot
            if (len(event.char) == 1 and event.char.isprintable()) or event.keysym in ['Return', 'KP_Enter', 'Tab']:
                # If there's a selection that will be replaced, save state first
                if text_widget.tag_ranges(tk.SEL):
                    self._flush_undo_timer(text_widget)
                    content = text_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(text_widget, content)
                else:
                    self._schedule_undo_snapshot(text_widget)
                return None

            # Delete/BackSpace with selection → save pre-delete state immediately
            if event.keysym in ['Delete', 'BackSpace']:
                if text_widget.tag_ranges(tk.SEL):
                    self._flush_undo_timer(text_widget)
                    content = text_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(text_widget, content)
                else:
                    self._schedule_undo_snapshot(text_widget)
                return None

            # Allow the default key handling to proceed
            return None
        except (tk.TclError, AttributeError):
            return None

    def handle_select_all_undo(self, event):
        """Handle Ctrl+A - prepare for potential undo separator if next operation modifies content"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, tk.Text):
                # Mark that we just did a select all - next destructive operation should save state
                focused_widget._select_all_pending = True
                logger.debug("Marked select-all pending for undo tracking")
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default select-all to proceed

    def handle_paste_undo(self, text_widget):
        """Handle Ctrl+V - paste with format preservation if available.
        Synchronous state management — no after_idle for critical saves."""
        logger.info("Direct paste handler executed")
        try:
            if isinstance(text_widget, tk.Text):
                # Flush any pending typing snapshot
                self._flush_undo_timer(text_widget)

                # Save pre-paste state
                pre_paste_content = text_widget.get("1.0", "end-1c")
                self.save_text_undo_state(text_widget, pre_paste_content)

                # Check if we have formatted content in internal clipboard
                # Verify system clipboard still matches — if not, newer content
                # was copied (e.g. from PDF text selection) and internal is stale
                if self.internal_clipboard:
                    text, tags_data = self.internal_clipboard
                    try:
                        system_clip = self.root.clipboard_get()
                        if system_clip != text:
                            self.internal_clipboard = None
                    except tk.TclError:
                        self.internal_clipboard = None

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

                    # Save post-paste state synchronously
                    post_paste_content = text_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(text_widget, post_paste_content)

                    # Trigger character count check after formatted paste
                    self.root.after_idle(lambda: self.check_character_count_for_widget(text_widget))

                    return "break"  # Prevent default paste
                else:
                    # No formatted content - perform regular paste with undo tracking
                    try:
                        # Get clipboard content
                        clipboard_content = self.root.clipboard_get()

                        # Delete selection if exists
                        if text_widget.tag_ranges(tk.SEL):
                            text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)

                        # Clear the select-all pending flag
                        if hasattr(text_widget, '_select_all_pending'):
                            delattr(text_widget, '_select_all_pending')

                        # Insert clipboard content at cursor position
                        insert_pos = text_widget.index(tk.INSERT)
                        text_widget.insert(insert_pos, clipboard_content)

                        # Save post-paste state synchronously
                        post_paste_content = text_widget.get("1.0", "end-1c")
                        self.save_text_undo_state(text_widget, post_paste_content)

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

    def check_character_count_for_widget(self, text_widget):
        """Helper method to trigger character count check for a text widget after paste"""
        try:
            # Find which column this widget belongs to by checking widget references
            for col_name, widgets in getattr(self, 'excel_widgets', {}).items():
                if hasattr(widgets, 'text_widget') and widgets.text_widget == text_widget:
                    class DummyEvent:
                        def __init__(self, widget):
                            self.widget = widget

                    self.check_character_count(DummyEvent(text_widget), col_name)
                    break
                elif widgets == text_widget:  # Direct widget reference
                    class DummyEvent:
                        def __init__(self, widget):
                            self.widget = widget

                    self.check_character_count(DummyEvent(text_widget), col_name)
                    break
        except (AttributeError, TypeError):
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
                                # Calculate relative positions using count() for Unicode safety
                                count_start = focused_widget.count(start, tag_start, "chars")
                                rel_start = max(0, count_start[0] if count_start else 0)
                                count_end = focused_widget.count(start, tag_end, "chars")
                                rel_end = min(len(text), count_end[0] if count_end else len(text))
                                tags_data.append((tag, rel_start, rel_end))

                    # Only store in internal clipboard if there's actual formatting
                    if tags_data:
                        self.internal_clipboard = (text, tags_data)
                        logger.debug(f"Stored formatted content with {len(tags_data)} tags")

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
                    # Flush timer and save pre-cut state
                    self._flush_undo_timer(focused_widget)
                    content = focused_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(focused_widget, content)

                    focused_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)

                    # Save post-cut state
                    post_cut_content = focused_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(focused_widget, post_cut_content)

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
                    # Flush timer and save current content to undo stack
                    self._flush_undo_timer(focused_widget)
                    current_content = focused_widget.get("1.0", "end-1c")
                    self.save_text_undo_state(focused_widget, current_content)

                    logger.info(f"Saved undo state before {event.keysym} operation")

                # Clear the select-all pending flag
                if hasattr(focused_widget, '_select_all_pending'):
                    delattr(focused_widget, '_select_all_pending')
        except (tk.TclError, AttributeError):
            pass
        return None  # Allow default delete to proceed

    def setup_undo_functionality(self):
        """Setup keyboard bindings for undo/redo"""
        # Bind global keyboard shortcuts (Command for macOS, Control for Windows/Linux)
        self.root.bind_all('<Command-z>', self.global_undo)
        self.root.bind_all('<Control-z>', self.global_undo)
        self.root.bind_all('<Command-y>', self.global_redo)
        self.root.bind_all('<Control-y>', self.global_redo)
        self.root.bind_all('<Control-Y>', self.global_redo)
        self.root.bind_all('<Command-Shift-z>', self.global_redo)
        self.root.bind_all('<Command-Shift-Z>', self.global_redo)
        self.root.bind_all('<Control-Shift-z>', self.global_redo)
        self.root.bind_all('<Control-Shift-Z>', self.global_redo)
        logger.info("Undo/redo bindings set up: Cmd/Ctrl+Z (undo), Cmd/Ctrl+Y/Shift+Z (redo)")

        # Add enhanced bindings for Text widgets (Command for macOS, Control for Windows/Linux)
        self.root.bind_all('<Command-a>', self.handle_select_all_undo)
        self.root.bind_all('<Control-a>', self.handle_select_all_undo)
        self.root.bind_all('<Command-c>', self.handle_copy_with_format)
        self.root.bind_all('<Control-c>', self.handle_copy_with_format)
        self.root.bind_all('<Command-x>', self.handle_cut_with_format)
        self.root.bind_all('<Control-x>', self.handle_cut_with_format)
        # NOTE: Paste binding removed - now handled directly on each Text widget
        self.root.bind_all('<Delete>', self.handle_delete_with_undo)
        self.root.bind_all('<BackSpace>', self.handle_delete_with_undo)

    def global_undo(self, event=None):
        """Global undo function that works on focused widget"""
        focused_widget = self.root.focus_get()
        if focused_widget and focused_widget in self.undo_widgets:
            if isinstance(focused_widget, tk.Text):
                # Flush any pending typing snapshot before undoing
                self._flush_undo_timer(focused_widget)
                if self.text_widget_undo(focused_widget):
                    # Cancel timer to prevent stale saves during undo sequence
                    self._cancel_undo_timer(focused_widget)
                    return "break"
            # For Entry widgets, use our custom undo system
            elif hasattr(focused_widget, 'get') and hasattr(focused_widget, 'delete'):
                if self.undo_entry_widget(focused_widget):
                    return "break"
        return None

    def global_redo(self, event=None):
        """Global redo function that works on focused widget"""
        focused_widget = self.root.focus_get()
        if focused_widget and focused_widget in self.undo_widgets:
            if isinstance(focused_widget, tk.Text):
                # Cancel any pending timer
                self._cancel_undo_timer(focused_widget)
                if self.text_widget_redo(focused_widget):
                    return "break"
            # For Entry widgets, use our custom redo system
            elif hasattr(focused_widget, 'get') and hasattr(focused_widget, 'delete'):
                if self.redo_entry_widget(focused_widget):
                    return "break"
        return None

    def enable_undo_for_widget(self, widget):
        """Enable undo/redo for a specific widget and add to tracking list"""
        if hasattr(widget, 'config'):
            if isinstance(widget, tk.Text):
                # Disable Tk's built-in undo — we use our own snapshot system
                widget.configure(undo=False)

                # Save initial empty state to custom stack
                widget_id = id(widget)
                if widget_id not in self.text_undo_stacks:
                    self.text_undo_stacks[widget_id] = []
                    self.text_redo_stacks[widget_id] = []
                content = widget.get("1.0", "end-1c")
                self.text_undo_stacks[widget_id].append((content, []))

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

        # Don't add duplicate state: check both content AND tags
        if self.text_undo_stacks[widget_id]:
            prev_content, prev_tags = self.text_undo_stacks[widget_id][-1]
            if prev_content == content and prev_tags == tags_data:
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
