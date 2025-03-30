import os
import tkinter as tk # Keep for messagebox dependency in ops classes (needs refactor)
# from tkinter import messagebox # REMOVE messagebox dependency
from datetime import datetime
import sqlite3
import logging
import shutil
import json # Needed for audit log details

from utils import open_directory, format_timestamp
# Import custom exceptions (assuming they are defined in customer_operations or a shared file)
# If not shared, define them here or move to utils.py
try:
    from customer_operations import ValidationError, DatabaseError, FilesystemError, CustomerOpsError
except ImportError:
    # Define locally if not found (less ideal)
    class CustomerOpsError(Exception): pass
    class ValidationError(CustomerOpsError): pass
    class DatabaseError(CustomerOpsError): pass
    class FilesystemError(CustomerOpsError): pass


class CaseFolderOperations:
    """Handles database and filesystem operations related to case folders."""

    def __init__(self, parent):
        """Initialize with parent CustomerManager instance."""
        self.parent = parent
        # Ensure parent provides necessary dependencies
        if not (parent and hasattr(parent, 'data_manager') and hasattr(parent, 'customer_ops')):
             raise ValueError("CaseFolderOperations requires a parent with 'data_manager' and 'customer_ops'.")
        self.data_manager = parent.data_manager
        self.customer_ops = parent.customer_ops

    def _execute_query(self, query, params=(), fetch_one=False, fetch_all=False, commit=False):
        """
        Helper method to execute database queries.
        Relies on the implementation in customer_ops for consistency.
        Raises DatabaseError for sqlite3 errors.
        """
        # Delegate to customer_ops's helper for consistency, assuming it's accessible
        # If direct access isn't desired, duplicate the helper here.
        # For now, assume delegation is okay.
        if hasattr(self.customer_ops, '_execute_query'):
             # Note: This creates a slight dependency, refactoring _execute_query to utils
             # or DataManager might be better long-term.
             return self.customer_ops._execute_query(query, params, fetch_one, fetch_all, commit)
        else:
             # Fallback if delegation isn't possible (e.g., testing setup)
             logging.error("Cannot delegate _execute_query to customer_ops. Using local implementation (may differ).")
             # Duplicate the logic from customer_ops._execute_query here if needed
             raise NotImplementedError("Local _execute_query implementation needed if delegation fails.")


    def create_case_folder(self, customer_id, case_number, description, template):
        """
        Create a case folder on filesystem and record it in the database.
        Returns: bool: True on success.
        Raises: ValidationError, DatabaseError, FilesystemError on failure.
        """
        # --- Validation ---
        if not customer_id:
             raise ValidationError("No customer selected.")
        if not case_number:
            raise ValidationError("Case number is required.")
        is_valid, msg = self.validate_case_number(case_number)
        if not is_valid:
            raise ValidationError(msg)

        # --- Get Customer Info ---
        try:
            customer = self.customer_ops.get_customer_by_id(customer_id)
        except DatabaseError as e:
             raise DatabaseError(f"Failed to retrieve customer data: {e}") from e

        if not customer:
            raise ValidationError("Selected customer not found in database.")
        customer_dir = customer.get("directory")
        customer_name = customer.get("name") # Used for case_info.txt

        if not customer_dir:
             raise ValidationError(f"Customer '{customer_name}' has no directory path associated.")
        if not os.path.exists(customer_dir):
            # Raise FilesystemError instead of showing messagebox
            raise FilesystemError(f"Customer directory not found or inaccessible: {customer_dir}")

        # --- Prepare Folder Name ---
        invalid_chars = r'<>:"/\|?*'
        safe_case_number = ''.join(c if c not in invalid_chars else '_' for c in case_number)
        if safe_case_number != case_number:
             logging.warning(f"Invalid characters in case number '{case_number}' replaced: '{safe_case_number}'")
             case_number = safe_case_number # Use the sanitized version

        folder_name_suffix = ""
        if description:
            original_desc = description
            safe_desc = ''.join(c if c not in invalid_chars and c.isascii() else '_' for c in description).strip()
            while '__' in safe_desc: safe_desc = safe_desc.replace('__', '_')
            if safe_desc != original_desc:
                 logging.info(f"Description sanitized for folder name. Original: '{original_desc}', Sanitized: '{safe_desc}'")
            if safe_desc:
                folder_name_suffix = f"_{safe_desc}"

        folder_name = f"{case_number}{folder_name_suffix}"
        case_path = os.path.join(customer_dir, folder_name)

        # --- Filesystem Operations ---
        try:
            if os.path.exists(case_path):
                raise FilesystemError(f"Case folder already exists: {folder_name}")
            
            os.makedirs(case_path)
            logging.info(f"Created directory: {case_path}")

            if template and "folders" in template:
                for subfolder in template["folders"]:
                    try: os.makedirs(os.path.join(case_path, subfolder), exist_ok=True)
                    except Exception as sub_e: logging.warning(f"Could not create subfolder '{subfolder}': {sub_e}")

            try: # Create info file (best effort)
                with open(os.path.join(case_path, "case_info.txt"), 'w') as f:
                    f.write(f"Case Number: {case_number}\nDescription: {description}\n")
                    f.write(f"Customer ID: {customer_id}\nCustomer Name: {customer_name}\n")
                    f.write(f"Created: {datetime.now().isoformat()}\n")
                    f.write(f"Template: {template.get('name', 'None') if template else 'None'}\n")
            except Exception as info_e: logging.warning(f"Could not create case_info.txt: {info_e}")

        except OSError as e:
            logging.error(f"Filesystem error creating case folder structure for '{case_path}': {e}")
            if os.path.exists(case_path) and not os.listdir(case_path):
                 try: os.rmdir(case_path)
                 except Exception as rm_e: logging.error(f"Cleanup failed for {case_path}: {rm_e}")
            raise FilesystemError(f"Failed to create case folder structure: {e}") from e
        except Exception as e:
             logging.error(f"Unexpected error during case folder filesystem operations: {e}", exc_info=True)
             raise FilesystemError(f"Unexpected error creating folder: {e}") from e

        # --- Database Operation ---
        query = """
            INSERT INTO case_folders (customer_id, case_number, description, path, created_at)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (customer_id, case_number, description, case_path, datetime.now().isoformat())
        inserted_id = None # To store the ID for audit log

        try:
            conn = self.data_manager._get_db_connection()
            if not conn: raise DatabaseError("Failed to get DB connection for case insert.")
            cursor = conn.cursor()
            cursor.execute(query, params)
            inserted_id = cursor.lastrowid # Get the ID of the inserted row
            conn.commit()
            success = True
        except sqlite3.Error as e:
             logging.error(f"Database error inserting case folder record: {e}")
             if conn: conn.rollback()
             success = False
             # Raise specific error for unique path constraint
             if "UNIQUE constraint failed: case_folders.path" in str(e):
                  raise DatabaseError(f"A case folder record with path '{case_path}' already exists.") from e
             else:
                  raise DatabaseError(f"Failed to record case folder in database: {e}") from e
        finally:
             if conn: conn.close()

        if success:
            logging.info(f"Recorded case folder '{folder_name}' (ID: {inserted_id}) for customer {customer_id}.")
            # Log audit event
            self.data_manager.log_audit_event(
                action="CASE_ADD",
                target_id=str(inserted_id), # Log against the case folder ID
                details={"customer_id": customer_id, "case_number": case_number, "path": case_path, "description": description}
            )
            return True
        else:
            # If DB insert fails after filesystem success, attempt cleanup
            logging.error(f"Failed to record case folder '{folder_name}' in database after creating directory. Attempting cleanup.")
            try:
                if os.path.exists(case_path):
                    shutil.rmtree(case_path)
                    logging.info(f"Cleaned up created folder due to DB error: {case_path}")
            except Exception as cleanup_e:
                logging.error(f"Filesystem cleanup failed for {case_path}: {cleanup_e}")
                # Raise a more specific error indicating inconsistent state
                raise FilesystemError(f"DB insert failed AND filesystem cleanup failed. Path: {case_path}. Cleanup error: {cleanup_e}")
            # If cleanup succeeded, still indicate failure
            return False


    def get_case_folders(self, customer_id):
        """
        Get list of case folders for a customer from the database.
        Returns: list[dict]: List of case folder dictionaries. Returns empty list if none found or error.
        Raises: DatabaseError: If a database error occurs.
        """
        if not customer_id: return []
        query = "SELECT id, customer_id, case_number, description, path, created_at FROM case_folders WHERE customer_id = ? ORDER BY created_at DESC"
        params = (customer_id,)
        try:
            rows = self._execute_query(query, params, fetch_all=True)
            if rows is None: return []
            return [dict(row) for row in rows]
        except DatabaseError as e:
             logging.error(f"Failed to get case folders for customer {customer_id}: {e}")
             raise e


    def open_case_folder(self, case_folder_id):
        """
        Open a case folder using its database ID.
        Returns: bool: True on success.
        Raises: ValidationError, DatabaseError, FilesystemError.
        """
        if not case_folder_id: raise ValidationError("Case folder ID is required.")
        query = "SELECT path FROM case_folders WHERE id = ?"
        params = (case_folder_id,)
        try:
            result = self._execute_query(query, params, fetch_one=True)
        except DatabaseError as e:
             raise DatabaseError(f"Failed to query case folder path for ID {case_folder_id}: {e}") from e
        if result and result['path']:
            case_path = result['path']
            try:
                open_directory(case_path) # Raises FilesystemError on failure
                return True
            except FilesystemError as fse: raise fse
            except Exception as e:
                 logging.error(f"Unexpected error opening directory '{case_path}': {e}", exc_info=True)
                 raise FilesystemError(f"Unexpected error opening directory: {e}") from e
        else:
            raise DatabaseError(f"Case folder record not found for ID: {case_folder_id}")


    def add_ms_prefix(self, case_number):
        """Add MS prefix to case number if it doesn't have one."""
        if case_number and not case_number.startswith("MS"): return f"MS{case_number}"
        return case_number

    def validate_case_number(self, case_number):
        """Validate that case number starts with MS."""
        if case_number and not case_number.startswith("MS"): return False, "Case numbers should start with MS"
        return True, ""


    def move_case_folder(self, case_folder_id, target_customer_id):
        """
        Move a case folder (filesystem and DB record) to another customer.
        Returns: bool: True on success.
        Raises: ValidationError, DatabaseError, FilesystemError on failure.
        """
        if not case_folder_id or not target_customer_id:
            raise ValidationError("Case folder ID and target customer ID are required.")

        # --- Get Target Customer Info ---
        try:
            target_customer = self.customer_ops.get_customer_by_id(target_customer_id)
            if not target_customer: raise ValidationError("Target customer not found.")
        except DatabaseError as e: raise DatabaseError(f"Failed to retrieve target customer data: {e}") from e
        target_customer_dir = target_customer.get("directory")
        target_customer_name = target_customer.get("name")
        if not target_customer_dir: raise ValidationError(f"Target customer '{target_customer_name}' has no directory path.")
        if not os.path.exists(target_customer_dir): raise FilesystemError(f"Target customer directory not found: {target_customer_dir}")

        # --- Get Current Case Folder Info ---
        query_case = "SELECT path, customer_id, case_number FROM case_folders WHERE id = ?" # Get case_number too
        try:
            case_info = self._execute_query(query_case, (case_folder_id,), fetch_one=True)
            if not case_info: raise DatabaseError("Case folder record not found in database.")
        except DatabaseError as e: raise DatabaseError(f"Failed to retrieve case folder data: {e}") from e
        source_case_path = case_info['path']
        source_customer_id = case_info['customer_id']
        case_number = case_info['case_number'] # For logging

        if source_customer_id == target_customer_id:
             logging.info("Move cancelled: Case folder already belongs to the target customer.")
             return False
        if not os.path.exists(source_case_path): raise FilesystemError(f"Source case folder path not found: {source_case_path}")

        # --- Prepare Target Path ---
        case_folder_name = os.path.basename(source_case_path)
        target_case_path = os.path.join(target_customer_dir, case_folder_name)
        if os.path.exists(target_case_path): raise FilesystemError(f"A folder named '{case_folder_name}' already exists in the target directory.")

        # --- Filesystem Move ---
        try:
            shutil.move(source_case_path, target_case_path)
            logging.info(f"Moved folder from {source_case_path} to {target_case_path}")
        except Exception as e:
            logging.error(f"Failed to move case folder '{case_folder_name}': {e}")
            raise FilesystemError(f"Failed to move case folder: {e}") from e

        # --- Database Update ---
        query_update = "UPDATE case_folders SET customer_id = ?, path = ? WHERE id = ?"
        params_update = (target_customer_id, target_case_path, case_folder_id)
        try:
            success = self._execute_query(query_update, params_update, commit=True)
            if not success: raise DatabaseError("Failed to update case folder record for unknown reason.")

            logging.info(f"Updated case folder DB record {case_folder_id}.")
            # Log audit event for successful move
            self.data_manager.log_audit_event(
                action="CASE_MOVE",
                target_id=str(case_folder_id),
                details={
                    "case_number": case_number,
                    "source_customer_id": source_customer_id,
                    "target_customer_id": target_customer_id,
                    "old_path": source_case_path,
                    "new_path": target_case_path
                }
            )

            # --- Update case_info.txt (Best effort) ---
            try:
                case_info_path = os.path.join(target_case_path, "case_info.txt")
                if os.path.exists(case_info_path):
                    with open(case_info_path, 'r') as f: lines = f.readlines()
                    updated_lines = []
                    found_id, found_name = False, False
                    for line in lines:
                        if line.startswith("Customer ID:"): updated_lines.append(f"Customer ID: {target_customer_id}\n"); found_id = True
                        elif line.startswith("Customer Name:"): updated_lines.append(f"Customer Name: {target_customer_name}\n"); found_name = True
                        else: updated_lines.append(line)
                    if not found_id: updated_lines.insert(2, f"Customer ID: {target_customer_id}\n")
                    if not found_name: updated_lines.insert(3, f"Customer Name: {target_customer_name}\n")
                    source_customer = self.customer_ops.get_customer_by_id(source_customer_id)
                    source_name = source_customer.get('name', 'Unknown') if source_customer else 'Unknown'
                    updated_lines.append(f"\nMoved from: {source_name} (ID: {source_customer_id}) on {datetime.now().isoformat()}\n")
                    with open(case_info_path, 'w') as f: f.writelines(updated_lines)
            except Exception as info_e: logging.warning(f"Could not update case_info.txt after move: {info_e}")

            return True # Overall success

        except DatabaseError as e:
            logging.error(f"Failed to update case folder record {case_folder_id} after move. Attempting rollback.")
            try:
                shutil.move(target_case_path, source_case_path)
                logging.info(f"Moved folder back to {source_case_path} due to DB error.")
            except Exception as rollback_e:
                logging.error(f"Failed to move folder back during rollback: {rollback_e}")
                raise FilesystemError(f"DB update failed AND filesystem rollback failed: {e}; Rollback error: {rollback_e}") from e
            raise e # Re-raise original DB error after successful rollback
