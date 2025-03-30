import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog # Added filedialog explicitly
import logging
import uuid # Needed for import
from datetime import datetime # Needed for import

from utils import open_directory
# Import custom exceptions (defined in customer_operations)
from customer_operations import ValidationError, DatabaseError, FilesystemError, CustomerOpsError


class BulkOperations:
    """Handles bulk operations on multiple customers using the database."""

    def __init__(self, parent):
        """Initialize with parent CustomerManager instance."""
        self.parent = parent
        # Get operational classes from parent
        self.customer_ops = self.parent.customer_ops
        self.data_manager = self.parent.data_manager

    def _get_selected_customer_ids(self):
        """Returns a list of selected customer IDs from the treeview."""
        selected_items = self.parent.customer_tree.selection()
        # The item ID ('iid') is the customer's database ID
        return list(selected_items)

    def export_customers(self, format_type):
        """Export selected customers to CSV or JSON."""
        selected_ids = self._get_selected_customer_ids()
        if not selected_ids:
            messagebox.showerror("Error", "Please select at least one customer to export.")
            return

        logging.info(f"Exporting {len(selected_ids)} customers as {format_type}...")

        # Fetch data for selected customers from the database
        selected_customers_data = []
        conn = self.data_manager._get_db_connection()
        if not conn: return # Error handled in _get_db_connection

        try:
            cursor = conn.cursor()
            placeholders = ','.join('?' for _ in selected_ids)
            query = f"SELECT * FROM customers WHERE id IN ({placeholders})"
            cursor.execute(query, tuple(selected_ids))
            rows = cursor.fetchall()
            selected_customers_data = [dict(row) for row in rows]
        except Exception as e:
             logging.error(f"Error fetching customer data for export: {e}")
             messagebox.showerror("Database Error", f"Could not fetch customer data for export: {e}")
             return
        finally:
             if conn: conn.close()

        if not selected_customers_data:
             messagebox.showwarning("Export Warning", "No data found for selected customers.")
             return

        # Ask for filepath (common logic)
        default_extension = f".{format_type}"
        filetypes = [(f"{format_type.upper()} files", f"*.{format_type}"), ("All files", "*.*")]
        filepath = filedialog.asksaveasfilename(
            defaultextension=default_extension,
            filetypes=filetypes,
            title=f"Export Selected Customers to {format_type.upper()}"
        )
        if not filepath:
            logging.info("Export cancelled by user.")
            return # User cancelled

        # Export using customer_ops methods (which now handle file writing)
        success = False
        if format_type == "csv":
            success = self.customer_ops.export_customers_to_csv(selected_customers_data, filepath)
        elif format_type == "json":
            success = self.customer_ops.export_customers_to_json(selected_customers_data, filepath)
        else:
             logging.error(f"Unsupported export format: {format_type}")
             messagebox.showerror("Error", f"Unsupported export format: {format_type}")
             return

        # No need for separate success message here, export methods handle it via status bar/logs
        # if success:
        #     messagebox.showinfo("Success", f"Exported {len(selected_customers_data)} customers successfully to {filepath}")


    def batch_update_customers(self):
        """Update multiple selected customers at once."""
        selected_ids = self._get_selected_customer_ids()
        if not selected_ids:
            messagebox.showerror("Error", "Please select at least one customer to update.")
            return

        logging.info(f"Initiating batch update for {len(selected_ids)} customers.")

        # --- Dialog for selecting fields (remains mostly the same) ---
        dialog = tk.Toplevel(self.parent.root)
        dialog.title(f"Batch Update {len(selected_ids)} Customers")
        dialog.geometry("400x300")
        dialog.transient(self.parent.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter new values (leave blank to keep current)").pack(pady=10)

        fields_to_update = {}
        entry_vars = {}

        # Define fields that can be batch updated
        updatable_fields = ["email", "phone", "address"] # Add 'notes' if desired, but needs Text widget

        for field in updatable_fields:
            frame = ttk.Frame(dialog)
            frame.pack(fill='x', padx=20, pady=5)
            ttk.Label(frame, text=f"{field.capitalize()}:", width=8, anchor='w').pack(side='left')
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=35)
            entry.pack(side='left', fill='x', expand=True, padx=5)
            entry_vars[field] = var

        # Update button action
        def do_update():
            updates = {}
            for field, var in entry_vars.items():
                value = var.get().strip()
                if value: # Only include fields with entered values
                    updates[field] = value

            if not updates:
                messagebox.showerror("Error", "Please enter a value for at least one field to update.", parent=dialog)
                return

            confirm_msg = f"Update {len(selected_ids)} customers with these values?\n\n"
            for field, value in updates.items():
                confirm_msg += f"- {field.capitalize()}: {value}\n"

            if not messagebox.askyesno("Confirm Batch Update", confirm_msg, parent=dialog):
                return

            updated_count = 0
            failed_ids = []
            for customer_id in selected_ids:
                try:
                    # update_customer now raises exceptions on failure
                    if self.customer_ops.update_customer(customer_id, **updates):
                        updated_count += 1
                    # else case removed as failure is now an exception
                except (ValidationError, DatabaseError) as e:
                     failed_ids.append(customer_id)
                     logging.warning(f"Failed to update customer ID {customer_id}: {e}")
                except Exception as e: # Catch unexpected errors per customer
                     failed_ids.append(customer_id)
                     logging.error(f"Unexpected error updating customer ID {customer_id}: {e}", exc_info=True)


            # Show summary message via status bar or warning dialog
            summary_msg = f"Batch update complete. Updated: {updated_count}."
            if failed_ids:
                summary_msg += f" Failed: {len(failed_ids)} (see logs)."
                messagebox.showwarning("Batch Update Result", summary_msg) # Keep warning for failures - Corrected Indent
            else:
                self.data_manager.update_status(summary_msg) # Use status bar for success - Corrected Indent

            # Refresh the list and close dialog (should happen regardless of failures) - Corrected Indent
            self.parent.refresh_customer_list()
            dialog.destroy()

        # Dialog buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Update Selected Customers", command=do_update).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=10)

        # Center dialog
        dialog.update_idletasks()
        x = self.parent.root.winfo_x() + (self.parent.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.root.winfo_y() + (self.parent.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")


    def delete_selected_customers(self):
        """Delete selected customers from the database."""
        selected_ids = self._get_selected_customer_ids()
        if not selected_ids:
            messagebox.showerror("Error", "Please select at least one customer to delete.")
            return

        count = len(selected_ids)
        confirm_msg = f"Are you sure you want to permanently delete {count} customer(s)?\n\nThis will also delete all associated case folders from the database (but not the folders on disk)."
        if not messagebox.askyesno("Confirm Delete", confirm_msg):
            logging.info("Customer deletion cancelled by user.")
            return

        logging.info(f"Attempting to delete {count} customers: {selected_ids}")
        # Use the optimized multi-delete method (now raises DatabaseError on failure)
        deleted_count = 0
        try:
            deleted_count = self.customer_ops.delete_multiple_customers(selected_ids)
            # Status update handled within delete_multiple_customers logging, UI shows result below
        except DatabaseError as e:
             logging.error(f"Database error during bulk delete: {e}")
             messagebox.showerror("Delete Error", f"Failed to delete customers:\n{e}", parent=self.parent.root)
             # Keep deleted_count as 0
        except Exception as e:
             logging.critical("Unexpected error during bulk delete.", exc_info=True)
             messagebox.showerror("Critical Error", f"An unexpected error occurred during deletion:\n{e}", parent=self.parent.root)
             deleted_count = 0


        # Refresh customer list regardless of errors to show current state
        self.parent.refresh_customer_list()

        # Show result message (status bar update is handled in delete_multiple_customers for success)
        # Only show a message box if there was an issue.
        if deleted_count != count:
             messagebox.showwarning("Deletion Issue", f"Attempted to delete {count}, but only {deleted_count} were deleted. Check logs for details.")
        # Success message is handled by status bar update within delete_multiple_customers


    def import_from_directory(self, selective=False):
        """
        TEMPORARILY MODIFIED: Import customers directly from customers.json.
        Ignores 'selective' flag for this temporary purpose.
        """
        import json # Need json for this temporary function
        json_file_path = "customers.json"
        
        if not os.path.exists(json_file_path):
            messagebox.showerror("Error", f"{json_file_path} not found. Cannot restore data.")
            return

        if not messagebox.askyesno("Confirm Restore", f"Restore customer data from {json_file_path}? This will attempt to add customers from the file into the database, skipping duplicates based on directory path."):
            return

        customers_data = []
        try:
            with open(json_file_path, 'r') as f:
                customers_data = json.load(f)
            if not isinstance(customers_data, list):
                 raise ValueError("Invalid format in customers.json")
        except Exception as e:
             logging.error(f"Error reading or parsing {json_file_path}: {e}", exc_info=True)
             messagebox.showerror("Error", f"Could not read or parse {json_file_path}:\n{e}")
             return

        if not customers_data:
            messagebox.showinfo("Info", f"{json_file_path} is empty. No data to restore.")
            return

        # --- Process Imports from JSON data ---
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        
        for customer in customers_data:
            if not isinstance(customer, dict):
                 logging.warning(f"Skipping invalid entry in JSON: {customer}")
                 failed_count += 1
                 continue

            name = customer.get("name")
            directory = customer.get("directory")
            customer_id_from_json = customer.get("id") # Try to keep original ID if possible

            if not name or not directory:
                 logging.warning(f"Skipping customer due to missing name or directory: {customer}")
                 failed_count += 1
                 continue

            logging.info(f"Attempting to import customer '{name}' from JSON (Dir: {directory})")
            
            try:
                # Attempt to add customer using data from JSON
                # Note: add_customer generates a new UUID, we aren't using the one from JSON here
                # If preserving original IDs is critical, add_customer logic would need modification
                new_customer_data = self.customer_ops.add_customer(
                    name=name,
                    email=customer.get("email", ""),
                    phone=customer.get("phone", ""),
                    address=customer.get("address", ""),
                    notes=customer.get("notes", ""),
                    directory=directory
                    # created_at is handled by add_customer
                )
                if new_customer_data:
                    imported_count += 1
                # else case removed as failure is an exception
            except DatabaseError as e:
                 # Specifically catch duplicate directory errors and count as skipped
                 if "UNIQUE constraint failed: customers.directory" in str(e):
                      logging.warning(f"Skipping import for '{name}': Directory '{directory}' likely already exists in DB.")
                      skipped_count += 1
                 else:
                      logging.error(f"Database error importing customer '{name}': {e}")
                      failed_count += 1
            except ValidationError as e:
                 logging.error(f"Validation error importing customer '{name}': {e}")
                 failed_count += 1
            except Exception as e:
                 logging.error(f"Unexpected error importing customer '{name}': {e}", exc_info=True)
                 failed_count += 1

        # Refresh the customer list after all imports attempted
        self.parent.refresh_customer_list()

        # Show summary message
        summary_msg = f"Restore from JSON finished.\n\nSuccessfully added: {imported_count}"
        if skipped_count > 0:
             summary_msg += f"\nSkipped (already exist): {skipped_count}"
        if failed_count > 0:
             summary_msg += f"\nFailed: {failed_count} (see logs for details)"
        
        if failed_count > 0 or skipped_count > 0:
             messagebox.showwarning("Restore Result", summary_msg)
        else:
             self.data_manager.update_status(summary_msg)


    def open_customer_directory(self):
        """Open the directory for the selected customer."""
        selected_ids = self._get_selected_customer_ids()
        if not selected_ids:
            messagebox.showerror("Error", "Please select a customer.")
            return
        if len(selected_ids) > 1:
             messagebox.showwarning("Info", "Please select only one customer to open their directory.")
             return

        customer_id = selected_ids[0]
        logging.debug(f"Attempting to open directory for customer ID: {customer_id}")

        # Fetch customer data from DB to get the directory path
        customer_data = self.customer_ops.get_customer_by_id(customer_id)

        if customer_data and customer_data.get('directory'):
            directory = customer_data['directory']
            if os.path.exists(directory):
                try:
                    open_directory(directory)
                    logging.info(f"Opened directory: {directory}")
                except Exception as e:
                     logging.error(f"Failed to open directory '{directory}': {e}")
                     messagebox.showerror("Error", f"Could not open directory:\n{e}")
            else:
                logging.warning(f"Directory path not found for customer {customer_id}: {directory}")
                messagebox.showerror("Error", f"Directory path not found:\n{directory}")
        else:
            logging.warning(f"Could not find directory information for customer ID: {customer_id}")
            messagebox.showerror("Error", "Could not find directory information for the selected customer.")
