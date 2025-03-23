import os
import tkinter as tk
from tkinter import ttk, messagebox

from utils import open_directory

class BulkOperations:
    """Handles bulk operations on multiple customers"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def export_customers(self, format_type):
        """Export selected customers to CSV or JSON"""
        selected_items = self.parent.customer_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select at least one customer to export")
            return
        
        # Get selected customers
        selected_customers = []
        for item in selected_items:
            customer_id = self.parent.customer_tree.item(item, "values")[0]
            for customer in self.parent.customers:
                if customer.get("id") == customer_id:
                    selected_customers.append(customer)
                    break
        
        # Export using customer_ops
        if format_type == "csv":
            result = self.parent.customer_ops.export_customers_to_csv(selected_customers)
        else:
            result = self.parent.customer_ops.export_customers_to_json(selected_customers)
        
        if result:
            messagebox.showinfo("Success", f"Exported {len(selected_customers)} customers successfully")
    
    def batch_update_customers(self):
        """Update multiple customers at once"""
        selected_items = self.parent.customer_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select at least one customer to update")
            return
        
        # Create a dialog for selecting fields to update
        dialog = tk.Toplevel(self.parent.root)
        dialog.title("Update Customers")
        dialog.geometry("400x300")
        dialog.transient(self.parent.root)
        dialog.grab_set()
        
        # Fields to update
        ttk.Label(dialog, text="Fields to update (leave blank to keep current value)").pack(pady=10)
        
        # Email field
        email_frame = ttk.Frame(dialog)
        email_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(email_frame, text="Email:").pack(side='left')
        email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=email_var, width=30).pack(side='left', padx=5)
        
        # Phone field
        phone_frame = ttk.Frame(dialog)
        phone_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(phone_frame, text="Phone:").pack(side='left')
        phone_var = tk.StringVar()
        ttk.Entry(phone_frame, textvariable=phone_var, width=30).pack(side='left', padx=5)
        
        # Address field
        address_frame = ttk.Frame(dialog)
        address_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(address_frame, text="Address:").pack(side='left')
        address_var = tk.StringVar()
        ttk.Entry(address_frame, textvariable=address_var, width=30).pack(side='left', padx=5)
        
        # Update button
        def do_update():
            # Collect fields to update
            fields = {}
            if email_var.get():
                fields['email'] = email_var.get()
            if phone_var.get():
                fields['phone'] = phone_var.get()
            if address_var.get():
                fields['address'] = address_var.get()
            
            # If no fields to update, show error
            if not fields:
                messagebox.showerror("Error", "Please enter at least one field to update")
                return
            
            # Update each selected customer
            updated_count = 0
            for item in selected_items:
                customer_id = self.parent.customer_tree.item(item, "values")[0]
                if self.parent.customer_ops.update_customer(customer_id, **fields):
                    updated_count += 1
            
            # Show success message
            messagebox.showinfo("Success", f"Updated {updated_count} customers")
            
            # Refresh the list
            self.parent.refresh_customer_list()
            
            # Close the dialog
            dialog.destroy()
        
        ttk.Button(dialog, text="Update", command=do_update).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def delete_selected_customers(self):
        """Delete selected customers"""
        selected_items = self.parent.customer_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select at least one customer to delete")
            return
        
        # Confirm deletion
        count = len(selected_items)
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {count} customer(s)?"):
            return
        
        # Delete each selected customer
        for item in selected_items:
            customer_id = self.parent.customer_tree.item(item, "values")[0]
            self.parent.customer_ops.delete_customer(customer_id)
        
        # Refresh customer list
        self.parent.refresh_customer_list()
        
        # Show success message
        messagebox.showinfo("Success", f"Deleted {count} customer(s)")
        
    def import_from_directory(self, selective=False):
        """Import customers based on directory structure"""
        from tkinter import filedialog
        import os
        import uuid
        from datetime import datetime
        
        # Ask for parent directory
        parent_dir = filedialog.askdirectory(title="Select Parent Directory Containing Customer Folders")
        if not parent_dir:
            return
            
        # Check if directory exists
        if not os.path.exists(parent_dir):
            messagebox.showerror("Error", "Selected directory does not exist")
            return
            
        # List all subdirectories (each represents a customer)
        customer_dirs = [d for d in os.listdir(parent_dir) 
                        if os.path.isdir(os.path.join(parent_dir, d))]
        
        if not customer_dirs:
            messagebox.showerror("Error", "No subdirectories found in selected directory")
            return
            
        # For selective import, let user choose which directories to import
        selected_dirs = []
        if selective:
            # Create selection dialog
            selection_dialog = tk.Toplevel(self.parent.root)
            selection_dialog.title("Select Directories to Import")
            selection_dialog.geometry("600x500")
            selection_dialog.transient(self.parent.root)
            selection_dialog.grab_set()
            
            # Instructions
            ttk.Label(selection_dialog, text="Select directories to import as customers:").pack(pady=10)
            ttk.Label(selection_dialog, text="Check the box to select a directory and edit the name if needed").pack(pady=5)
            
            # Create a frame with scrollbar for checkboxes
            frame = ttk.Frame(selection_dialog)
            frame.pack(fill='both', expand=True, padx=10, pady=5)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side='right', fill='y')
            
            # Create listbox with custom entries
            listbox_frame = ttk.Frame(frame)
            listbox_frame.pack(side='left', fill='both', expand=True)
            
            # Headers
            header_frame = ttk.Frame(listbox_frame)
            header_frame.pack(fill='x')
            ttk.Label(header_frame, text="Select", width=8).pack(side='left')
            ttk.Label(header_frame, text="Customer Name", width=25).pack(side='left')
            ttk.Label(header_frame, text="Directory Path").pack(side='left', padx=5)
            ttk.Separator(listbox_frame, orient='horizontal').pack(fill='x', pady=2)
            
            # Create a canvas for scrolling
            canvas = tk.Canvas(listbox_frame, yscrollcommand=scrollbar.set)
            scrollbar.config(command=canvas.yview)
            canvas.pack(side='left', fill='both', expand=True)
            
            # Create frame for checkbox rows inside canvas
            checkbox_frame = ttk.Frame(canvas)
            canvas_window = canvas.create_window((0, 0), window=checkbox_frame, anchor='nw')
            
            # Enable mousewheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            # Track entries for customer names
            checkbox_vars = {}
            name_entries = {}
            
            for dir_name in sorted(customer_dirs):
                var = tk.BooleanVar(value=False)
                checkbox_vars[dir_name] = var
                full_path = os.path.join(parent_dir, dir_name)
                
                # Create frame for each row
                row_frame = ttk.Frame(checkbox_frame)
                row_frame.pack(fill='x', pady=3)
                
                # Add checkbox (fixed width)
                cb = ttk.Checkbutton(row_frame, text="", variable=var, width=6)
                cb.pack(side='left')
                
                # Add name entry (fixed width)
                name_entry = ttk.Entry(row_frame, width=25)
                name_entry.insert(0, dir_name)  # Set initial value
                name_entry.pack(side='left', padx=2)
                name_entries[dir_name] = name_entry  # Store reference to entry widget
                
                # Add directory path (remaining space)
                path_label = ttk.Label(row_frame, text=full_path)
                path_label.pack(side='left', padx=5)
            
            # Update canvas scroll region after all items are added
            checkbox_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
            
            # Make sure canvas resizes with window
            def _on_frame_configure(event):
                canvas.config(scrollregion=canvas.bbox('all'))
                canvas.itemconfig(canvas_window, width=canvas.winfo_width())
            
            canvas.bind('<Configure>', _on_frame_configure)
            
            # Select/Deselect All buttons
            button_frame = ttk.Frame(selection_dialog)
            button_frame.pack(fill='x', padx=10, pady=5)
            
            def select_all():
                for var in checkbox_vars.values():
                    var.set(True)
                    
            def deselect_all():
                for var in checkbox_vars.values():
                    var.set(False)
            
            ttk.Button(button_frame, text="Select All", command=select_all).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Deselect All", command=deselect_all).pack(side='left', padx=5)
            
            # OK/Cancel buttons
            action_frame = ttk.Frame(selection_dialog)
            action_frame.pack(fill='x', padx=10, pady=10)
            
            # Variable to track if user clicked OK
            dialog_result = {'success': False}
            
            def on_ok():
                dialog_result['success'] = True
                selection_dialog.destroy()
                
            ttk.Button(action_frame, text="Import Selected", command=on_ok).pack(side='right', padx=5)
            ttk.Button(action_frame, text="Cancel", command=selection_dialog.destroy).pack(side='right', padx=5)
            
            # Wait for dialog to close
            self.parent.root.wait_window(selection_dialog)
            
            # If user clicked OK, process selections
            if dialog_result['success']:
                for dir_name, var in checkbox_vars.items():
                    if var.get():
                        # Get the name from the entry widget
                        custom_name = name_entries[dir_name].get().strip()
                        if not custom_name:  # If empty, use directory name
                            custom_name = dir_name
                        selected_dirs.append((dir_name, custom_name))
                        
                if not selected_dirs:
                    messagebox.showinfo("Info", "No directories selected for import")
                    return
            else:
                return  # User cancelled
        else:
            # For non-selective import, confirm with user
            if not messagebox.askyesno("Confirm Import", f"Found {len(customer_dirs)} potential customer directories. Import them all?"):
                return
            selected_dirs = customer_dirs
            
        # Process each selected directory as a customer
        imported_count = 0
        for item in selected_dirs:
            if selective:
                dir_name, customer_name = item
            else:
                dir_name = item
                customer_name = dir_name
                
            full_path = os.path.join(parent_dir, dir_name)
            
            # Create a new customer entry
            new_customer = {
                "id": str(uuid.uuid4()),
                "name": customer_name,
                "email": "", # Can be updated later
                "phone": "", # Can be updated later
                "directory": full_path,
                "created_at": datetime.now().isoformat()
            }
            
            # Add customer to the list
            self.parent.customers.append(new_customer)
            imported_count += 1
            
        # Save customers
        self.parent.data_manager.save_customers()
        
        # Refresh the customer list
        self.parent.refresh_customer_list()
        
        # Show success message
        messagebox.showinfo("Success", f"Imported {imported_count} customers from directories")
    
    def open_customer_directory(self):
        """Open the directory for the selected customer"""
        selected_items = self.parent.customer_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a customer")
            return
        
        # Get the first selected customer
        item = selected_items[0]
        customer_id = self.parent.customer_tree.item(item, "values")[0]
        
        # Find the customer and open their directory using customer_ops
        for customer in self.parent.customers:
            if customer.get("id") == customer_id:
                directory = customer.get("directory")
                if directory and os.path.exists(directory):
                    open_directory(directory)
                    return
                break
        
        messagebox.showerror("Error", "Customer directory not found")
