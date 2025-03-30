import os
import datetime
import logging
import tkinter as tk
from tkinter import messagebox, ttk

from utils import open_directory

class TreeviewManager:
    """Handles operations related to the treeviews for customers and case folders"""

    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
        self.customer_sort_column = "name"
        self.customer_sort_reverse = False
        self.case_sort_column = "created_at"
        self.case_sort_reverse = True # Default sort newest first

    def refresh_customer_list(self):
        """Refresh the customer treeview using data from self.parent.customers"""
        logging.debug("Refreshing customer treeview...")
        for item in self.parent.customer_tree.get_children():
            self.parent.customer_tree.delete(item)
        self.parent.event_handler.on_search_changed() 
        logging.debug("Customer treeview refresh triggered (population depends on search handler).")

    def refresh_case_list(self):
        """Refresh the list of case folders from the database"""
        logging.debug("Refreshing case treeview...")
        selected_customer_id = self.parent.selected_customer_id_var.get()

        # Clear the case treeview
        for item in self.parent.case_tree.get_children():
            self.parent.case_tree.delete(item)

        if not selected_customer_id:
            logging.debug("No customer selected, case list cleared.")
            self.parent.status_var.set("Select a customer to view case folders.")
            return # Nothing to load

        # Get filter text and field
        filter_text = self.parent.case_filter_var.get().lower()
        filter_field = self.parent.case_filter_field_var.get()

        # Get case folders from the database via case_ops
        case_folders = self.parent.case_ops.get_case_folders(selected_customer_id)
        logging.debug(f"Retrieved {len(case_folders)} case folders from DB for customer {selected_customer_id}.")

        # Apply filter if needed
        filtered_folders = []
        if not case_folders: # Handle case where DB query fails or returns empty
             pass
        else:
            for folder in case_folders:
                # Ensure folder is a dictionary before proceeding
                if not isinstance(folder, dict):
                    logging.warning(f"Skipping invalid folder data: {folder}")
                    continue

                case_number = folder.get("case_number", "").lower() # Use case_number from DB
                description = folder.get("description", "").lower()

                include = False
                if not filter_text:
                    include = True
                elif filter_field == 'all':
                    if filter_text in case_number or filter_text in description:
                        include = True
                elif filter_field == 'case' and filter_text in case_number:
                    include = True
                elif filter_field == 'description' and filter_text in description:
                    include = True
                
                if include:
                    filtered_folders.append(folder)

        # Add filtered folders to treeview
        # The columns defined in ui_setup are ('path', 'case', 'description', 'created')
        # DB returns: id, customer_id, case_number, description, path, created_at
        # We need to map DB fields to the *displayed* columns in the values tuple.
        # Use the DB 'id' as the treeview item ID ('iid').
        for folder in filtered_folders:
             # Format created_at for display (optional)
             created_at = folder.get('created_at', '')
             created_display = created_at
             if created_at:
                try:
                    dt_obj = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
                    created_display = dt_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    try:
                        dt_obj = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S")
                        created_display = dt_obj.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        logging.warning(f"Invalid date format: {created_at}")
                        created_display = created_at

             self.parent.case_tree.insert(
                '', 'end',
                iid=folder.get('id'), # Use DB ID as item ID
                values=(
                    folder.get('path', ''), # Hidden column 0
                    folder.get('case_number', ''), # Displayed column 1 ('case')
                    folder.get('description', ''), # Displayed column 2 ('description')
                    created_display # Displayed column 3 ('created')
                )
            )
        logging.debug(f"Populated case treeview with {len(filtered_folders)} items.")

        # Update the status bar
        status_msg = f"Loaded {len(filtered_folders)} case folders."
        if filter_text:
            status_msg = f"Found {len(filtered_folders)} case folders matching '{filter_text}'."
        self.parent.status_var.set(status_msg)


    def add_case_to_tree(self, folder):
        """Add a single case folder (dict from DB) to the treeview.
           Note: Calling refresh_case_list might be simpler."""
        if not isinstance(folder, dict) or 'id' not in folder:
             logging.warning("add_case_to_tree called with invalid data.")
             return

        logging.debug(f"Adding single case folder to tree: ID {folder.get('id')}")
        created_display = folder.get('created_at', '')
        try:
            dt_obj = datetime.datetime.strptime(created_display, "%Y-%m-%d %H:%M")
            created_display = dt_obj.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            pass

        try:
            self.parent.case_tree.insert(
                '', 'end',
                iid=folder.get('id'), # Use DB ID as item ID
                values=(
                    folder.get('path', ''),
                    folder.get('case_number', ''),
                    folder.get('description', ''),
                    created_display
                )
            )
        except tk.TclError as e:
             # Handle potential error if item with same ID already exists
             logging.error(f"Failed to insert case folder {folder.get('id')} into tree: {e}")


    def open_selected_case(self):
        """Open the selected case folder using its DB ID."""
        selected_items = self.parent.case_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a case folder to open.")
            return

        # The item ID ('iid') is now the database ID
        case_folder_id = selected_items[0]
        logging.debug(f"Attempting to open case folder with DB ID: {case_folder_id}")

        # Call the updated case_ops method
        if not self.parent.case_ops.open_case_folder(case_folder_id):
             # Error message is handled within open_case_folder
             pass

    def sort_treeview(self, tree, col, reverse):
        """Sort treeview items by column."""
        # Basic implementation for in-memory sorting (might need adjustment for DB)
        # This assumes data is already loaded into the treeview
        try:
            data_list = [(tree.set(item_id, col), item_id) for item_id in tree.get_children('')]
            
            # Attempt numeric sort if possible, otherwise string sort
            try:
                # Try converting to float for sorting numeric-like columns
                data_list.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError:
                # Fallback to case-insensitive string sort
                data_list.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

            for index, (val, item_id) in enumerate(data_list):
                tree.move(item_id, '', index)

            # Update arrow indicator
            for c in tree['columns']:
                 tree.heading(c, text=c) # Reset text first
            arrow = ' ▲' if reverse else ' ▼'
            tree.heading(col, text=col + arrow)

            # Remember last sort
            if tree == self.parent.customer_tree:
                 self.customer_sort_column = col
                 self.customer_sort_reverse = reverse
            elif tree == self.parent.case_tree:
                 self.case_sort_column = col
                 self.case_sort_reverse = reverse
                 
        except Exception as e:
            logging.error(f"Error sorting treeview column '{col}': {e}")
            messagebox.showerror("Sort Error", f"Could not sort column '{col}'.")

    # Wrapper methods called by column headers
    def sort_customer_treeview(self, col):
        """Sort customer treeview by the clicked column header."""
        reverse = False
        if col == self.customer_sort_column:
            reverse = not self.customer_sort_reverse # Toggle direction
        self.sort_treeview(self.parent.customer_tree, col, reverse)

    def sort_case_treeview(self, col):
        """Sort case treeview by the clicked column header."""
        reverse = False
        if col == self.case_sort_column:
            reverse = not self.case_sort_reverse # Toggle direction
        self.sort_treeview(self.parent.case_tree, col, reverse)
