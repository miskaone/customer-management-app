import os
import uuid
import csv
import json
import tkinter as tk # Keep for filedialog/simpledialog
from tkinter import filedialog, simpledialog, ttk, messagebox # Keep messagebox for UI dialog methods
from datetime import datetime
import sqlite3
import logging

from utils import open_directory, format_timestamp

# Define custom exception classes for specific operational errors
class CustomerOpsError(Exception):
    """Base exception for CustomerOperations errors."""
    pass

class ValidationError(CustomerOpsError):
    """Exception raised for validation errors."""
    pass

class DatabaseError(CustomerOpsError):
    """Exception raised for database errors."""
    pass

class FilesystemError(CustomerOpsError):
    """Exception raised for filesystem errors."""
    pass


class CustomerOperations:
    """Handles database operations related to customers."""

    def __init__(self, parent):
        """Initialize with parent CustomerManager instance."""
        self.parent = parent
        # Get the DataManager instance from the parent
        if parent and hasattr(parent, 'data_manager'):
             self.data_manager = parent.data_manager
        else:
             logging.warning("CustomerOperations initialized without a standard parent. Relying on parent object having 'data_manager'.")
             self.data_manager = getattr(parent, 'data_manager', None)
             if not self.data_manager:
                  raise ValueError("CustomerOperations requires a parent with a 'data_manager' attribute.")


    def _execute_query(self, query, params=(), fetch_one=False, fetch_all=False, commit=False):
        """
        Helper method to execute database queries.
        Returns fetched data, True on successful commit, or None/[] on fetch.
        Raises DatabaseError for sqlite3 errors.
        """
        conn = self.data_manager._get_db_connection()
        if not conn:
            raise DatabaseError("Failed to establish database connection.")

        result = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
                result = True # Indicate commit success
            elif fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else: # Query executed without commit/fetch (e.g., PRAGMA)
                 result = True # Indicate execution success

        except sqlite3.Error as e:
            logging.error(f"Database query error: {e}\nQuery: {query}\nParams: {params}")
            if commit:
                try: conn.rollback()
                except Exception as rb_e: logging.error(f"Rollback failed: {rb_e}")
            # Raise a custom exception instead of showing messagebox
            raise DatabaseError(f"Database error occurred: {e}") from e
        finally:
            if conn:
                conn.close()
        
        return result


    def add_customer(self, name, email, phone, address, notes, directory):
        """
        Add a new customer to the database.
        Returns: dict: The newly created customer data on success.
        Raises: ValidationError: If name or directory is missing.
                DatabaseError: If a database error occurs (e.g., duplicate directory).
        """
        if not name:
            raise ValidationError("Customer name is required.")
        if not directory:
            raise ValidationError("Customer directory is required.")

        customer_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        query = """
            INSERT INTO customers (id, name, email, phone, address, notes, directory, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (customer_id, name, email, phone, address, notes, directory, created_at)

        try:
            success = self._execute_query(query, params, commit=True)
            if success:
                logging.info(f"Added customer '{name}' with ID {customer_id}.")
                # Log audit event
                self.data_manager.log_audit_event(
                    action="CUSTOMER_ADD",
                    target_id=customer_id,
                    details={"name": name, "directory": directory, "email": email, "phone": phone}
                )
                return {
                    "id": customer_id, "name": name, "email": email, "phone": phone,
                    "address": address, "notes": notes, "directory": directory, "created_at": created_at
                }
            else:
                raise DatabaseError("Failed to add customer for an unknown reason.")
        except DatabaseError as e:
            if "UNIQUE constraint failed: customers.directory" in str(e):
                logging.warning(f"Attempted to add customer with duplicate directory: {directory}")
                raise DatabaseError(f"Directory '{directory}' is already associated with another customer.") from e
            else:
                raise e


    def update_customer(self, customer_id, **updates):
        """
        Update an existing customer in the database.
        Returns: bool: True on success.
        Raises: DatabaseError: If a database error occurs.
                ValidationError: If customer_id or updates are missing.
        """
        if not customer_id or not updates:
             raise ValidationError("Customer ID and update data are required for update.")

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        params = list(updates.values())
        params.append(customer_id)
        query = f"UPDATE customers SET {set_clause} WHERE id = ?"

        try:
            success = self._execute_query(query, tuple(params), commit=True)
            if success:
                 logging.info(f"Updated customer with ID {customer_id}.")
                 # Log audit event
                 self.data_manager.log_audit_event(
                     action="CUSTOMER_UPDATE",
                     target_id=customer_id,
                     details={"updated_fields": list(updates.keys())} # Log which fields were updated
                 )
                 return True
            logging.warning(f"Update query for customer {customer_id} reported no error but returned False.")
            return False
        except DatabaseError as e:
             raise e


    def delete_customer(self, customer_id):
        """
        Delete a customer by ID from the database.
        Returns: bool: True on success.
        Raises: DatabaseError: If a database error occurs.
                ValidationError: If customer_id is missing.
        """
        if not customer_id:
            raise ValidationError("Customer ID is required for deletion.")

        # Optional: Get customer details before deleting for audit log
        customer_details = self.get_customer_by_id(customer_id) # Might raise DB error if already gone
        details_for_log = {"name": customer_details.get("name"), "directory": customer_details.get("directory")} if customer_details else {}

        query = "DELETE FROM customers WHERE id = ?"
        params = (customer_id,)

        try:
            success = self._execute_query(query, params, commit=True)
            if success:
                logging.info(f"Deleted customer with ID {customer_id}.")
                # Log audit event
                self.data_manager.log_audit_event(
                    action="CUSTOMER_DELETE",
                    target_id=customer_id,
                    details=details_for_log
                )
                return True
            logging.warning(f"Delete query for customer {customer_id} reported no error but returned False.")
            return False
        except DatabaseError as e:
             raise e


    def delete_multiple_customers(self, customer_ids):
        """
        Delete multiple customers by their IDs from the database.
        Returns: int: The number of customers successfully deleted.
        Raises: DatabaseError: If a database error occurs during the transaction.
        """
        if not customer_ids:
            return 0

        conn = self.data_manager._get_db_connection()
        if not conn:
             raise DatabaseError("Failed to establish database connection.")

        deleted_count = 0
        try:
            cursor = conn.cursor()
            placeholders = ','.join('?' for _ in customer_ids)
            query = f"DELETE FROM customers WHERE id IN ({placeholders})"
            
            cursor.execute(query, tuple(customer_ids))
            deleted_count = cursor.rowcount
            conn.commit()
            logging.info(f"Deleted {deleted_count} customers.")
            if deleted_count > 0:
                 # Log audit event
                 self.data_manager.log_audit_event(
                     action="CUSTOMER_DELETE_MULTI",
                     details={"deleted_ids": customer_ids, "count": deleted_count}
                 )

        except sqlite3.Error as e:
            logging.error(f"Database error deleting multiple customers: {e}")
            try: conn.rollback()
            except Exception as rb_e: logging.error(f"Rollback failed: {rb_e}")
            deleted_count = 0
            raise DatabaseError(f"Error deleting customers: {e}") from e
        finally:
            if conn:
                conn.close()
        
        return deleted_count


    def rename_customer(self, customer_id, new_name):
        """
        Rename a customer by ID in the database.
        Returns: bool: True on success.
        Raises: ValidationError: If new name is empty or customer_id is missing.
                DatabaseError: If a database error occurs.
        """
        if not customer_id:
             raise ValidationError("Customer ID is required for rename.")
        if not new_name or not new_name.strip():
            raise ValidationError("Customer name cannot be empty.")

        # Get old name for audit log
        old_customer_data = self.get_customer_by_id(customer_id)
        if not old_customer_data:
             # This case should ideally be caught by the UI before calling rename
             logging.warning(f"Attempted to rename non-existent customer ID: {customer_id}")
             return False # Or raise error?

        old_name = old_customer_data.get("name", "[unknown]")
        new_name = new_name.strip()

        # Don't proceed if name hasn't changed
        if old_name == new_name:
             logging.info(f"Rename skipped for customer {customer_id}, name is already '{new_name}'.")
             return True # Considered success as the state is correct

        query = "UPDATE customers SET name = ? WHERE id = ?"
        params = (new_name, customer_id)

        try:
            success = self._execute_query(query, params, commit=True)
            if success:
                logging.info(f"Renamed customer {customer_id} from '{old_name}' to '{new_name}'.")
                # Log audit event
                self.data_manager.log_audit_event(
                    action="CUSTOMER_RENAME",
                    target_id=customer_id,
                    details={"old_name": old_name, "new_name": new_name}
                )
                return True
            logging.warning(f"Rename query for customer {customer_id} reported no error but returned False.")
            return False
        except DatabaseError as e:
             raise e


    def get_customer_by_id(self, customer_id):
         """
         Fetch a single customer by ID.
         Returns: dict: Customer data as a dictionary, or None if not found.
         Raises: DatabaseError: If a database error occurs.
         """
         if not customer_id: return None
         query = "SELECT * FROM customers WHERE id = ?"
         try:
             row = self._execute_query(query, (customer_id,), fetch_one=True)
             return dict(row) if row else None
         except DatabaseError as e:
              logging.error(f"Failed to get customer {customer_id}: {e}")
              raise e


    def show_rename_dialog(self):
        """
        Show dialog to rename a customer. (UI-dependent)
        Handles fetching data and calling rename_customer.
        Shows messageboxes for UI feedback and errors originating here or caught.
        """
        if not self.parent or not hasattr(self.parent, 'customer_tree') or not hasattr(self.parent, 'root'):
             logging.error("show_rename_dialog called without required UI components in parent.")
             return 

        selected_items = self.parent.customer_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a customer to rename", parent=self.parent.root)
            return
        if len(selected_items) > 1:
            messagebox.showerror("Error", "Please select only one customer to rename", parent=self.parent.root)
            return

        customer_id = selected_items[0]

        try:
            customer_data = self.get_customer_by_id(customer_id)
            if not customer_data:
                messagebox.showerror("Error", "Could not find customer data.", parent=self.parent.root)
                return
            current_name = customer_data.get("name", "")
        except DatabaseError as e:
             messagebox.showerror("Database Error", f"Failed to fetch customer data: {e}", parent=self.parent.root)
             return
        except Exception as e:
             logging.error(f"Unexpected error fetching customer for rename dialog: {e}", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred fetching data: {e}", parent=self.parent.root)
             return

        dialog = tk.Toplevel(self.parent.root)
        dialog.title("Rename Customer")
        dialog.geometry("400x150")
        dialog.transient(self.parent.root)
        dialog.grab_set()
        name_frame = ttk.Frame(dialog); name_frame.pack(fill='x', padx=20, pady=20)
        ttk.Label(name_frame, text="New Name:").pack(side='left', padx=(0, 10))
        name_var = tk.StringVar(value=current_name)
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side='left', fill='x', expand=True)
        name_entry.select_range(0, tk.END); name_entry.focus()
        btn_frame = ttk.Frame(dialog); btn_frame.pack(fill='x', padx=20, pady=10)

        def on_rename():
            new_name = name_var.get().strip()
            try:
                if self.rename_customer(customer_id, new_name): # This now raises exceptions
                    dialog.destroy()
                    self.parent.refresh_customer_list()
                    if hasattr(self.data_manager, 'update_status'):
                         self.data_manager.update_status(f"Customer renamed to '{new_name}'.")
            except ValidationError as ve: messagebox.showerror("Validation Error", str(ve), parent=dialog)
            except DatabaseError as dbe: messagebox.showerror("Database Error", f"Failed to rename: {dbe}", parent=dialog)
            except Exception as ex:
                 logging.error(f"Unexpected error during rename: {ex}", exc_info=True)
                 messagebox.showerror("Error", f"An unexpected error occurred: {ex}", parent=dialog)

        ttk.Button(btn_frame, text="Rename", command=on_rename).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)
        dialog.bind("<Return>", lambda e: on_rename())
        dialog.update_idletasks()
        x = self.parent.root.winfo_x() + (self.parent.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.root.winfo_y() + (self.parent.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")


    def export_customers_to_csv(self, customers, filepath=None):
        """
        Export customers (list of dicts) to CSV file.
        Returns: bool: True on success.
        Raises: FilesystemError: If file writing fails.
                ValidationError: If filepath is not provided and cannot be obtained.
        """
        if not filepath:
             if not self.parent or not self.parent.root: raise ValidationError("Filepath required for export, and UI context unavailable to ask.")
             filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], parent=self.parent.root)
             if not filepath: raise ValidationError("Export cancelled by user.")

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                headers = ["id", "name", "email", "phone", "address", "notes", "directory", "created_at"]
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(customers)
            logging.info(f"Exported {len(customers)} customers to CSV: {filepath}")
            return True
        except IOError as e:
            logging.error(f"Failed to write CSV file '{filepath}': {e}")
            raise FilesystemError(f"Failed to export to CSV: {e}") from e
        except Exception as e:
            logging.error(f"Unexpected error exporting to CSV '{filepath}': {e}", exc_info=True)
            raise FilesystemError(f"Unexpected error exporting to CSV: {e}") from e


    def export_customers_to_json(self, customers, filepath=None):
        """
        Export customers (list of dicts) to JSON file.
        Returns: bool: True on success.
        Raises: FilesystemError: If file writing fails.
                ValidationError: If filepath is not provided and cannot be obtained.
        """
        if not filepath:
             if not self.parent or not self.parent.root: raise ValidationError("Filepath required for export, and UI context unavailable to ask.")
             filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], parent=self.parent.root)
             if not filepath: raise ValidationError("Export cancelled by user.")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(customers, f, indent=4)
            logging.info(f"Exported {len(customers)} customers to JSON: {filepath}")
            return True
        except IOError as e:
            logging.error(f"Failed to write JSON file '{filepath}': {e}")
            raise FilesystemError(f"Failed to export to JSON: {e}") from e
        except Exception as e:
            logging.error(f"Unexpected error exporting to JSON '{filepath}': {e}", exc_info=True)
            raise FilesystemError(f"Unexpected error exporting to JSON: {e}") from e


    def select_directory(self):
        """Open a dialog to select a directory. (UI-dependent)"""
        if not self.parent or not self.parent.root: logging.error("select_directory called without UI context."); return None
        directory = filedialog.askdirectory(title="Select Customer Directory", parent=self.parent.root)
        return directory if directory else None

    def create_directory(self, suggested_name="new_customer"):
        """
        Create a new directory for a customer using dialogs. (UI-dependent)
        Returns: str: The path of the created directory on success.
        Raises: FilesystemError: If directory creation fails or already exists.
                ValidationError: If user cancels or provides invalid input.
        """
        if not self.parent or not self.parent.root: raise FilesystemError("Cannot create directory without UI context.")
        parent_dir = filedialog.askdirectory(title="Select Parent Directory for Customer Folders", parent=self.parent.root)
        if not parent_dir: raise ValidationError("Directory creation cancelled: No parent directory selected.")
        suggested_name = "".join(c if c.isalnum() else "_" for c in suggested_name).replace("__", "_")
        dir_name = simpledialog.askstring("Directory Name", "Enter name for the customer directory:", initialvalue=suggested_name, parent=self.parent.root)
        if not dir_name: raise ValidationError("Directory creation cancelled: No directory name entered.")
        new_dir = os.path.join(parent_dir, dir_name)
        if os.path.exists(new_dir): raise FilesystemError(f"Directory '{new_dir}' already exists.")
        try:
            os.makedirs(new_dir)
            logging.info(f"Created directory: {new_dir}")
            return new_dir
        except OSError as e:
            logging.error(f"Failed to create directory '{new_dir}': {e}")
            raise FilesystemError(f"Failed to create directory: {e}") from e
        except Exception as e:
             logging.error(f"Unexpected error creating directory '{new_dir}': {e}", exc_info=True)
             raise FilesystemError(f"Unexpected error creating directory: {e}") from e
