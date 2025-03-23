import os
from tkinter import messagebox
from datetime import datetime

from utils import load_json_file, save_json_file

class DataManager:
    """Handles all data operations including loading, saving, and auto-saving data"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
        
        # Config files
        self.config_file = "customers.json"
        self.templates_file = "templates.json"
        
        # Auto-save settings
        self.autosave_interval = 60000  # 60 seconds
        self.autosave_timer = None
    
    def load_customers(self):
        """Load customers from file"""
        return load_json_file(self.config_file, [])
    
    def load_templates(self):
        """Load template configurations from file"""
        default_templates = [{
            "id": "default",
            "name": "Default Template",
            "description": "Basic folder structure",
            "folders": ["Documents", "Images", "Notes"]
        }]
        return load_json_file(self.templates_file, default_templates)
    
    def save_customers(self):
        """Save customers to file"""
        if save_json_file(self.config_file, self.parent.customers):
            self.parent.status_var.set(f"Customers saved ({datetime.now().strftime('%H:%M:%S')})")
            self.parent.root.after(3000, lambda: self.parent.status_var.set(""))
            return True
        return False
    
    def start_autosave_timer(self):
        """Start the timer for auto-saving customer data"""
        self.auto_save()
        self.autosave_timer = self.parent.root.after(self.autosave_interval, self.start_autosave_timer)
    
    def auto_save(self):
        """Auto-save customer data"""
        if self.parent.customers:
            self.save_customers()
    
    def cancel_autosave(self):
        """Cancel the auto-save timer"""
        if self.autosave_timer:
            self.parent.root.after_cancel(self.autosave_timer)
            self.autosave_timer = None
