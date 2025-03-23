import os
import datetime
from tkinter import messagebox

from utils import open_directory, format_timestamp

class TreeviewManager:
    """Handles operations related to the treeviews for customers and case folders"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def refresh_customer_list(self):
        """Refresh the customer treeview"""
        # Clear the treeview
        for item in self.parent.customer_tree.get_children():
            self.parent.customer_tree.delete(item)
        
        # Store all customers for filtering
        self.parent.all_customers = self.parent.customers.copy()
        
        # Apply current search filter
        self.parent.event_handler.on_search_changed()
        
        # Update customer dropdown
        self.parent.update_customer_dropdown()
    
    def refresh_case_list(self):
        """Refresh the list of case folders"""
        # Get selected customer name and ID
        selected_customer_name = self.parent.selected_customer_var.get()
        selected_customer_id = self.parent.selected_customer_id_var.get()
        
        if not selected_customer_name:
            return
        
        # Clear the case treeview
        for item in self.parent.case_tree.get_children():
            self.parent.case_tree.delete(item)
        
        # Get filter text and field
        filter_text = self.parent.case_filter_var.get().lower()
        filter_field = self.parent.case_filter_field_var.get()
        
        # Use customer ID if available, otherwise find it from name
        customer_id = selected_customer_id
        if not customer_id:
            for customer in self.parent.customers:
                if customer.get("name") == selected_customer_name:
                    customer_id = customer.get("id")
                    break
                    
        if not customer_id:
            return
        
        # Get case folders using the case_ops module
        case_folders = self.parent.case_ops.get_case_folders(customer_id)
        
        # Apply filter if needed
        filtered_folders = []
        for folder in case_folders:
            case_name = folder.get("name", "").lower()
            description = folder.get("description", "").lower()
            
            if filter_text:
                if filter_field == 'all':
                    if filter_text in case_name or filter_text in description:
                        filtered_folders.append(folder)
                elif filter_field == 'case' and filter_text in case_name:
                    filtered_folders.append(folder)
                elif filter_field == 'description' and filter_text in description:
                    filtered_folders.append(folder)
            else:
                # No filter, include all
                filtered_folders.append(folder)
        
        # Add filtered folders to treeview
        for folder in filtered_folders:
            self.parent.case_tree.insert(
                '', 'end', 
                values=(
                    folder.get('path', ''),
                    folder.get('name', ''),
                    folder.get('description', ''),
                    folder.get('created_date', '')
                )
            )
        
        # Update the status bar
        if filter_text:
            self.parent.status_var.set(f"Found {len(filtered_folders)} case folders matching '{filter_text}'")
        else:
            self.parent.status_var.set(f"Loaded {len(filtered_folders)} case folders")
    
    def add_case_to_tree(self, folder):
        """Add a case folder to the treeview"""
        self.parent.case_tree.insert(
            '', 'end', 
            values=(
                folder.get('path', ''),
                folder.get('name', ''),
                folder.get('description', ''),
                folder.get('created_date', '')
            )
        )
    
    def open_selected_case(self):
        """Open the selected case folder"""
        selected_items = self.parent.case_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a case folder")
            return
        
        # Get the first selected case folder
        item = selected_items[0]
        folder_path = self.parent.case_tree.item(item, "values")[0]
        
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", "Case folder not found")
            return
        
        # Open the folder in file explorer
        open_directory(folder_path)
