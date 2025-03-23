import tkinter as tk
from tkinter import messagebox

class FormManager:
    """Handles form-related operations including validation and form clearing"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def clear_customer_form(self):
        """Clear the customer form"""
        self.parent.name_var.set("")
        self.parent.email_var.set("")
        self.parent.phone_var.set("")
        self.parent.address_var.set("")
        self.parent.notes_text.delete("1.0", tk.END)
        self.parent.dir_var.set("")
    
    def validate_customer_form(self):
        """Validate the customer form fields"""
        name = self.parent.name_var.get().strip()
        directory = self.parent.dir_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Customer name is required")
            return False
        
        if not directory:
            messagebox.showerror("Error", "Customer directory is required")
            return False
        
        return True
    
    def get_customer_form_data(self):
        """Get customer data from the form"""
        return {
            "name": self.parent.name_var.get().strip(),
            "email": self.parent.email_var.get().strip(),
            "phone": self.parent.phone_var.get().strip(),
            "address": self.parent.address_var.get().strip(),
            "notes": self.parent.notes_text.get("1.0", tk.END).strip(),
            "directory": self.parent.dir_var.set().strip()
        }
    
    def save_customer(self):
        """Save a new customer"""
        # Validate form first
        if not self.validate_customer_form():
            return False
        
        # Get values from form
        name = self.parent.name_var.get().strip()
        email = self.parent.email_var.get().strip()
        phone = self.parent.phone_var.get().strip()
        address = self.parent.address_var.get().strip()
        notes = self.parent.notes_text.get("1.0", tk.END).strip()
        directory = self.parent.dir_var.get().strip()
        
        # Use the customer_ops to add the customer
        result = self.parent.customer_ops.add_customer(
            name, email, phone, address, notes, directory
        )
        
        if result:
            # Clear the form
            self.clear_customer_form()
            
            # Switch to the manage tab
            self.parent.notebook.select(self.parent.manage_customers_tab)
            
            # Refresh customer list
            self.parent.refresh_customer_list()
            
            return True
        
        return False
