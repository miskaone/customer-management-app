import os
import uuid
import csv
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime

from utils import save_json_file, open_directory, format_timestamp

class CustomerOperations:
    """Handles operations related to customers"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def add_customer(self, name, email, phone, address, notes, directory):
        """Add a new customer to the list"""
        if not name:
            messagebox.showerror("Error", "Customer name is required")
            return False
        
        if not directory:
            messagebox.showerror("Error", "Customer directory is required")
            return False
        
        # Create customer data
        customer = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "notes": notes,
            "directory": directory,
            "created_at": format_timestamp()
        }
        
        # Add to customer list
        self.parent.customers.append(customer)
        
        # Save to file
        self.parent.save_customers()
        
        return True
    
    def update_customer(self, customer_id, **updates):
        """Update an existing customer"""
        for i, customer in enumerate(self.parent.customers):
            if customer.get("id") == customer_id:
                # Update fields
                for key, value in updates.items():
                    if key in customer:
                        customer[key] = value
                
                # Add updated timestamp
                customer["updated_at"] = format_timestamp()
                
                # Save changes
                self.parent.customers[i] = customer
                self.parent.save_customers()
                return True
        
        return False
    
    def delete_customer(self, customer_id):
        """Delete a customer by ID"""
        for i, customer in enumerate(self.parent.customers):
            if customer.get("id") == customer_id:
                del self.parent.customers[i]
                self.parent.save_customers()
                return True
        
        return False
    
    def delete_multiple_customers(self, customer_ids):
        """Delete multiple customers by their IDs"""
        count = 0
        for customer_id in customer_ids:
            if self.delete_customer(customer_id):
                count += 1
        
        return count
    
    def rename_customer(self, customer_id, new_name):
        """Rename a customer by ID"""
        # Validate new name
        if not new_name or not new_name.strip():
            messagebox.showerror("Error", "Customer name cannot be empty")
            return False
            
        # Find and update customer
        for i, customer in enumerate(self.parent.customers):
            if customer.get("id") == customer_id:
                # Update name
                customer["name"] = new_name.strip()
                
                # Add updated timestamp
                customer["updated_at"] = format_timestamp()
                
                # Save changes
                self.parent.customers[i] = customer
                self.parent.save_customers()
                return True
                
        return False
    
    def show_rename_dialog(self):
        """Show dialog to rename a customer"""
        # Get selected customer
        selected_items = self.parent.customer_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a customer to rename")
            return
            
        # Only allow one customer to be renamed at a time
        if len(selected_items) > 1:
            messagebox.showerror("Error", "Please select only one customer to rename")
            return
            
        # Get current customer data
        item = selected_items[0]
        customer_id = self.parent.customer_tree.item(item, "values")[0]
        current_name = None
        
        # Find current name
        for customer in self.parent.customers:
            if customer.get("id") == customer_id:
                current_name = customer.get("name", "")
                break
                
        if not current_name:
            messagebox.showerror("Error", "Could not find customer data")
            return
            
        # Create rename dialog
        dialog = tk.Toplevel(self.parent.root)
        dialog.title("Rename Customer")
        dialog.geometry("400x150")
        dialog.transient(self.parent.root)
        dialog.grab_set()
        
        # Name field
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(name_frame, text="New Name:").pack(side='left', padx=(0, 10))
        name_var = tk.StringVar(value=current_name)
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side='left', fill='x', expand=True)
        name_entry.select_range(0, tk.END)  # Select all text for easy editing
        name_entry.focus()  # Set focus to the entry
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        def on_rename():
            new_name = name_var.get().strip()
            if self.rename_customer(customer_id, new_name):
                dialog.destroy()
                # Refresh the customer list to show the new name
                self.parent.refresh_customer_list()
                messagebox.showinfo("Success", f"Customer renamed to '{new_name}'")
        
        ttk.Button(btn_frame, text="Rename", command=on_rename).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)
        
        # Handle Enter key
        dialog.bind("<Return>", lambda e: on_rename())
        
        # Center dialog on parent window
        dialog.update_idletasks()
        x = self.parent.root.winfo_x() + (self.parent.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.root.winfo_y() + (self.parent.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def export_customers_to_csv(self, customers, filepath=None):
        """Export customers to CSV file"""
        if not filepath:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        
        if not filepath:
            return False
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(["ID", "Name", "Email", "Phone", "Address", "Directory", "Created"])
                
                # Write data
                for customer in customers:
                    writer.writerow([
                        customer.get("id", ""),
                        customer.get("name", ""),
                        customer.get("email", ""),
                        customer.get("phone", ""),
                        customer.get("address", ""),
                        customer.get("directory", ""),
                        customer.get("created_at", "")
                    ])
            
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export to CSV: {str(e)}")
            return False
    
    def export_customers_to_json(self, customers, filepath=None):
        """Export customers to JSON file"""
        if not filepath:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        
        if not filepath:
            return False
        
        # Use save_json_file utility function instead of direct json.dump
        return save_json_file(filepath, customers)
    
    def select_directory(self):
        """Open a dialog to select a directory"""
        directory = filedialog.askdirectory(title="Select Customer Directory")
        return directory if directory else None
    
    def create_directory(self, suggested_name="new_customer"):
        """Create a new directory for a customer"""
        parent_dir = filedialog.askdirectory(title="Select Parent Directory")
        if not parent_dir:
            return None
        
        # Clean up the name for a directory
        suggested_name = "".join(c if c.isalnum() else "_" for c in suggested_name)
        
        # Create a dialog to get the directory name
        dir_name = simpledialog.askstring(
            "Directory Name", 
            "Enter name for the customer directory:",
            initialvalue=suggested_name
        )
        
        if not dir_name:
            return None
        
        new_dir = os.path.join(parent_dir, dir_name)
        try:
            os.makedirs(new_dir, exist_ok=True)
            messagebox.showinfo("Success", f"Directory created: {new_dir}")
            return new_dir
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create directory: {str(e)}")
            return None
