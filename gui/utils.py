"""
GUI utility classes for the DJ Timeline application
"""

import platform
import tkinter as tk

import ttkbootstrap as tb


class ToolTip:
    """Create a tooltip for a given widget"""

    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)

    def on_enter(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        # Create tooltip label with styling
        label = tk.Label(tw, text=self.text, justify='left',
                        background="#ffffe0", relief='solid', borderwidth=1,
                        font=("tahoma", 8, "normal"), wraplength=300)
        label.pack(ipadx=1)

    def on_leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ScrollableText(tb.Frame):
    """A Text widget with vertical scrollbar"""
    
    def __init__(self, parent, **text_options):
        super().__init__(parent)
        
        # Create text widget with all provided options
        self.text_widget = tk.Text(self, **text_options)
        
        # Create scrollbar (always visible for consistent behavior)
        self.scrollbar = tb.Scrollbar(self, orient="vertical", 
                                     command=self.text_widget.yview)
        
        # Configure text widget scrolling
        self.text_widget.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout widgets - use grid for better control
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the text widget"""
        return getattr(self.text_widget, name)


class ScrollableFrame(tb.Frame):
    """
    A scrollable frame widget that provides vertical scrolling capability
    while preserving ttkbootstrap theming.
    """

    def __init__(self, parent, *args, **kwargs):
        """
        Initialize scrollable frame with:
        - Canvas for content rendering
        - Vertical scrollbar
        - Interior frame for actual content
        """
        super().__init__(parent, *args, **kwargs)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = tb.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tb.Frame(self.canvas)

        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window inside canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind canvas resize to frame resize
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        # Bind mousewheel events
        self.bind_mouse_wheel()

    def on_canvas_configure(self, event):
        """Reset the canvas window to encompass inner frame when canvas size changes"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def bind_mouse_wheel(self):
        """Bind mouse wheel events for scrolling"""
        # Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        # Linux
        self.canvas.bind_all("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self.on_mouse_wheel)

    def unbind_mouse_wheel(self):
        """Unbind mouse wheel events"""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling with platform-specific logic"""
        # Check if the mouse is over a text widget (which might have its own scrolling)
        widget_under_mouse = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget_under_mouse and isinstance(widget_under_mouse, (tk.Text, tk.Listbox)):
            return

        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:  # Linux/Mac
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    @property
    def interior(self):
        """Return the interior frame where content should be placed"""
        return self.scrollable_frame

    def scroll_to_top(self):
        """Scroll to the top of the canvas"""
        self.canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """Scroll to the bottom of the canvas"""
        self.canvas.yview_moveto(1)
