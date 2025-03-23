import tkinter as tk
from tkinter import ttk

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)
    
    def enter(self, event=None):
        self.schedule()
        
    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
        
    def motion(self, event=None):
        self.x, self.y = event.x, event.y
        
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)
        
    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
            
    def showtip(self):
        if self.tip_window:
            return
            
        # Get screen position
        x = self.widget.winfo_rootx() + self.x + 20
        y = self.widget.winfo_rooty() + self.y + 20
        
        # Create a toplevel window
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Display text in tooltip
        label = ttk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         wraplength=250)
        label.pack(padx=2, pady=2)
        
    def hidetip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def add_tooltip(widget, text):
    """Helper function to add tooltip to a widget"""
    return ToolTip(widget, text)
