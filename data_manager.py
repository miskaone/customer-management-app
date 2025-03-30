import sqlite3
import uuid
import json
import os
from tkinter import messagebox
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    """Handles all data operations using an SQLite database."""

    def __init__(self, parent):
        """Initialize with parent CustomerManager instance and set up the database."""
        self.parent = parent
        self.db_file = "customer_data.db"
        self.templates_file = "templates.json" # Keep for initial template loading/migration
        self._initialize_database()
        self._migrate_json_data() # Attempt migration if needed

    def _get_db_connection(self):
        """Establishes and returns a database connection."""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
            conn.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints
            conn.execute("PRAGMA journal_mode=WAL;") # Enable write-ahead logging
            return conn
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            messagebox.showerror("Database Error", f"Could not connect to database: {e}")
            return None

    def _initialize_database(self):
        """Creates the database and necessary tables if they don't exist."""
        conn = self._get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            # Customers Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    notes TEXT,
                    directory TEXT UNIQUE,
                    created_at TEXT NOT NULL
                )
            """)
            # Templates Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    folders TEXT NOT NULL  -- Store folder list as JSON string
                )
            """)
            # Case Folders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS case_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id TEXT NOT NULL,
                    case_number TEXT NOT NULL,
                    description TEXT,
                    path TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
                )
            """)
            # Index for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_customer_id ON case_folders (customer_id);")
            
            # Audit Log Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user TEXT, -- Placeholder for future user tracking
                    action TEXT NOT NULL, -- e.g., 'CUSTOMER_ADD', 'CASE_MOVE'
                    target_id TEXT, -- e.g., customer_id, case_folder_id, template_id
                    details TEXT -- JSON string for additional details (e.g., changed fields)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_target_id ON audit_log (target_id);")

            # Custom Fields Definition Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_field_definitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE, -- Internal name/key
                    label TEXT NOT NULL,      -- Display name for UI
                    field_type TEXT NOT NULL CHECK(field_type IN ('TEXT', 'NUMBER', 'DATE', 'BOOLEAN')), -- Allowed types
                    target_entity TEXT NOT NULL CHECK(target_entity IN ('CUSTOMER', 'CASE')), -- Where field applies
                    created_at TEXT NOT NULL
                )
            """)

            # Custom Fields Values Table (linking fields to entities)
            cursor.execute("""
                 CREATE TABLE IF NOT EXISTS custom_field_values (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     field_definition_id INTEGER NOT NULL,
                     entity_id TEXT NOT NULL, -- e.g., customer_id or case_folder_id (use TEXT for UUIDs)
                     value TEXT,
                     FOREIGN KEY (field_definition_id) REFERENCES custom_field_definitions (id) ON DELETE CASCADE
                 )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_custom_value_entity ON custom_field_values (entity_id, field_definition_id);")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uidx_custom_value ON custom_field_values (field_definition_id, entity_id);")


            conn.commit()
            logging.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            messagebox.showerror("Database Error", f"Error initializing database: {e}")
        finally:
            if conn:
                conn.close()

    def _migrate_json_data(self):
        """Migrates data from old JSON files to the SQLite DB if necessary."""
        conn = self._get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        customer_migrated = False # Flag to track if customer migration happened

        try:
            # --- Migrate Customers ---
            cursor.execute("SELECT COUNT(*) FROM customers")
            customer_count = cursor.fetchone()[0]
            customers_json_file = "customers.json"
            migrated_customer_ids = [] # Keep track of customers added in this run

            if customer_count == 0 and os.path.exists(customers_json_file):
                logging.info(f"Migrating customer data from {customers_json_file}...")
                customer_migrated = True # Set flag
                try:
                    with open(customers_json_file, 'r') as f: customers_data = json.load(f)
                    added_count = 0
                    for customer in customers_data:
                        cust_id = customer.get('id', str(uuid.uuid4())) # Use existing ID or generate new
                        try:
                            cursor.execute("""
                                INSERT INTO customers (id, name, email, phone, address, notes, directory, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                cust_id, customer.get('name'), customer.get('email'),
                                customer.get('phone'), customer.get('address'), customer.get('notes'),
                                customer.get('directory'), customer.get('created_at', datetime.now().isoformat())
                            ))
                            migrated_customer_ids.append(cust_id) # Store ID if added
                            added_count += 1
                        except sqlite3.IntegrityError as ie: logging.warning(f"Skipping duplicate customer during migration (ID: {cust_id}, Dir: {customer.get('directory')}): {ie}")
                        except Exception as e: logging.warning(f"Skipping customer due to error during migration (ID: {cust_id}): {e}")
                    conn.commit()
                    logging.info(f"Migrated {added_count} customers from {customers_json_file}.")
                except Exception as e:
                    logging.error(f"Error migrating customers from {customers_json_file}: {e}")
                    conn.rollback()
                    customer_migrated = False # Reset flag on error

            # --- Migrate Case Folders (Only if customers were potentially migrated OR table is empty) ---
            cursor.execute("SELECT COUNT(*) FROM case_folders")
            case_folder_count = cursor.fetchone()[0]

            # Run case migration if customers were just migrated OR if case table is empty (covers initial run)
            if customer_migrated or case_folder_count == 0:
                logging.info("Attempting to migrate case folders based on customer directories...")
                migrated_case_folders = 0
                # Fetch all customers (either just migrated or existing if table wasn't empty)
                cursor.execute("SELECT id, directory FROM customers")
                all_customers_in_db = cursor.fetchall()

                for cust_row in all_customers_in_db:
                    customer_id = cust_row['id']
                    customer_dir = cust_row['directory']
                    if not customer_dir or not os.path.isdir(customer_dir):
                        logging.warning(f"Skipping case folder migration for customer {customer_id}: Directory '{customer_dir}' not found or invalid.")
                        continue

                    try:
                        for item_name in os.listdir(customer_dir):
                            item_path = os.path.join(customer_dir, item_name)
                            if os.path.isdir(item_path):
                                # Basic check: Assume directories starting with 'MS' are case folders
                                if item_name.startswith("MS"):
                                    case_number = item_name.split('_')[0]
                                    description = ""
                                    created_at_str = datetime.now().isoformat() # Default created time
                                    # Try reading case_info.txt for better details
                                    info_path = os.path.join(item_path, "case_info.txt")
                                    if os.path.exists(info_path):
                                         try:
                                             with open(info_path, 'r') as f_info:
                                                 for line in f_info:
                                                     if line.startswith("Description:"): description = line.split(":", 1)[1].strip()
                                                     elif line.startswith("Created:"): created_at_str = line.split(":", 1)[1].strip()
                                         except Exception as read_e: logging.warning(f"Could not read case_info.txt for {item_path}: {read_e}")

                                    try:
                                        cursor.execute("""
                                            INSERT INTO case_folders (customer_id, case_number, description, path, created_at)
                                            VALUES (?, ?, ?, ?, ?)
                                        """, (customer_id, case_number, description, item_path, created_at_str))
                                        migrated_case_folders += 1
                                    except sqlite3.IntegrityError: logging.warning(f"Skipping case folder migration: Path '{item_path}' likely already exists in DB.")
                                    except sqlite3.Error as db_e: logging.error(f"Database error migrating case folder '{item_path}': {db_e}")
                    except OSError as list_e: logging.error(f"Error listing directory '{customer_dir}' for case migration: {list_e}")

                if migrated_case_folders > 0:
                    conn.commit()
                    logging.info(f"Migrated {migrated_case_folders} potential case folders.")
                else:
                     logging.info("No new case folders found to migrate.")

            # --- Migrate Templates ---
            # (Template migration logic remains the same)
            cursor.execute("SELECT COUNT(*) FROM templates")
            template_count = cursor.fetchone()[0]
            if template_count == 0:
                 # ... (template migration logic as before) ...
                 pass # Placeholder

        except sqlite3.Error as e:
            logging.error(f"Database migration/check error: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def load_customers(self):
        """Load all customers from the database."""
        conn = self._get_db_connection()
        if not conn: return []
        customers = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email, phone, address, notes, directory, created_at FROM customers ORDER BY name COLLATE NOCASE")
            rows = cursor.fetchall()
            customers = [dict(row) for row in rows]
            logging.info(f"Loaded {len(customers)} customers from database.")
        except sqlite3.Error as e:
            logging.error(f"Error loading customers: {e}")
            messagebox.showerror("Database Error", f"Error loading customers: {e}")
        finally:
            if conn: conn.close()
        return customers

    def load_templates(self):
        """Load all templates from the database."""
        conn = self._get_db_connection()
        if not conn: return []
        templates = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, folders FROM templates ORDER BY name")
            rows = cursor.fetchall()
            for row in rows:
                template = dict(row)
                try: template['folders'] = json.loads(template['folders'])
                except json.JSONDecodeError: logging.error(f"Error decoding folders JSON for template ID {template['id']}."); template['folders'] = []
                templates.append(template)
            logging.info(f"Loaded {len(templates)} templates from database.")
        except sqlite3.Error as e:
            logging.error(f"Error loading templates: {e}")
            messagebox.showerror("Database Error", f"Error loading templates: {e}")
            return [] 
        finally:
            if conn: conn.close()
        if not templates:
             logging.warning("No templates found, attempting to add default.")
             default_template_data = {"id": "default", "name": "Default Template", "description": "Basic folder structure", "folders": ["Documents", "Images", "Notes"]}
             if self.add_template(default_template_data): return [default_template_data]
             else: return []
        return templates

    def add_template(self, template_data):
        """Adds a new template to the database."""
        conn = self._get_db_connection()
        if not conn: return False
        success = False
        try:
            if not template_data.get('id') or not template_data.get('name'): logging.error("Failed to add template: ID and Name required."); messagebox.showerror("Error", "Template ID and Name are required."); return False
            folders_json = json.dumps(template_data.get('folders', []))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO templates (id, name, description, folders) VALUES (?, ?, ?, ?)", (template_data['id'], template_data['name'], template_data.get('description'), folders_json))
            conn.commit()
            logging.info(f"Added template '{template_data['name']}' to database.")
            success = True
        except sqlite3.IntegrityError: logging.error(f"Failed to add template: ID '{template_data.get('id')}' or Name '{template_data.get('name')}' already exists."); messagebox.showerror("Error", f"Template ID '{template_data.get('id')}' or Name '{template_data.get('name')}' already exists.")
        except sqlite3.Error as e: logging.error(f"Database error adding template: {e}"); messagebox.showerror("Database Error", f"Error adding template: {e}"); conn.rollback()
        finally:
            if conn: conn.close()
        return success

    def update_template(self, template_id, name, description, folders):
        """Updates an existing template in the database."""
        conn = self._get_db_connection()
        if not conn: return False
        success = False
        try:
            if not template_id or not name: logging.error("Failed to update template: ID and Name required."); messagebox.showerror("Error", "Template ID and Name are required."); return False
            folders_json = json.dumps(folders)
            cursor = conn.cursor()
            cursor.execute("UPDATE templates SET name = ?, description = ?, folders = ? WHERE id = ?", (name, description, folders_json, template_id))
            conn.commit()
            success = cursor.rowcount > 0
            if success: logging.info(f"Updated template '{name}' (ID: {template_id}).")
            else: logging.warning(f"Attempted update for template ID {template_id}, but no record found.")
        except sqlite3.IntegrityError: logging.error(f"Failed to update template: Name '{name}' might already exist."); messagebox.showerror("Error", f"Template Name '{name}' might already exist.")
        except sqlite3.Error as e: logging.error(f"Database error updating template {template_id}: {e}"); messagebox.showerror("Database Error", f"Error updating template: {e}"); conn.rollback()
        finally:
            if conn: conn.close()
        return success

    def delete_template(self, template_id):
        """Deletes a template from the database."""
        if template_id == "default": logging.warning("Attempted delete default template."); messagebox.showwarning("Delete Error", "Cannot delete default template."); return False
        conn = self._get_db_connection()
        if not conn: return False
        success = False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success: logging.info(f"Deleted template ID: {template_id}")
            else: logging.warning(f"Attempted delete for template ID {template_id}, but no record found.")
        except sqlite3.Error as e: logging.error(f"Database error deleting template {template_id}: {e}"); messagebox.showerror("Database Error", f"Error deleting template: {e}"); conn.rollback()
        finally:
            if conn: conn.close()
        return success

    def log_audit_event(self, action: str, target_id: str = None, details: dict = None, user: str = "System"):
        """Logs an event to the audit_log table."""
        conn = self._get_db_connection()
        if not conn: return
        timestamp = datetime.now().isoformat()
        details_json = json.dumps(details) if details else None
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO audit_log (timestamp, user, action, target_id, details) VALUES (?, ?, ?, ?, ?)", (timestamp, user, action, target_id, details_json))
            conn.commit()
            logging.debug(f"Audit logged: Action={action}, Target={target_id}")
        except sqlite3.Error as e: logging.error(f"Failed to log audit event: {e}", exc_info=True)
        finally:
            if conn: conn.close()

    # --- Custom Field Definition Methods ---

    def load_custom_field_definitions(self):
        """Loads all custom field definitions from the database."""
        conn = self._get_db_connection()
        if not conn: return []
        definitions = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, label, field_type, target_entity, created_at FROM custom_field_definitions ORDER BY label COLLATE NOCASE")
            rows = cursor.fetchall()
            definitions = [dict(row) for row in rows]
            logging.info(f"Loaded {len(definitions)} custom field definitions.")
        except sqlite3.Error as e:
            logging.error(f"Error loading custom field definitions: {e}")
            messagebox.showerror("Database Error", f"Error loading custom field definitions: {e}")
        finally:
            if conn: conn.close()
        return definitions

    def add_custom_field_definition(self, name, label, field_type, target_entity):
        """Adds a new custom field definition to the database."""
        conn = self._get_db_connection()
        if not conn: return False
        success = False
        created_at = datetime.now().isoformat()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO custom_field_definitions (name, label, field_type, target_entity, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, label, field_type, target_entity, created_at))
            conn.commit()
            logging.info(f"Added custom field definition '{label}' (Name: {name}).")
            success = True
            self.log_audit_event(action="CUSTOM_FIELD_DEF_ADD", target_id=name, details={"label": label, "type": field_type, "entity": target_entity})
        except sqlite3.IntegrityError: logging.error(f"Failed to add custom field: Name '{name}' already exists."); messagebox.showerror("Error", f"A custom field with the name '{name}' already exists.")
        except sqlite3.Error as e: logging.error(f"Database error adding custom field definition: {e}"); messagebox.showerror("Database Error", f"Error adding custom field: {e}"); conn.rollback()
        finally:
            if conn: conn.close()
        return success

    def update_custom_field_definition(self, field_id, label, field_type, target_entity):
        """Updates an existing custom field definition (Name/ID is immutable)."""
        conn = self._get_db_connection()
        if not conn: return False
        success = False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE custom_field_definitions SET label = ?, field_type = ?, target_entity = ? WHERE id = ?", (label, field_type, target_entity, field_id))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                 logging.info(f"Updated custom field definition ID: {field_id}")
                 self.log_audit_event(action="CUSTOM_FIELD_DEF_UPDATE", target_id=str(field_id), details={"label": label, "type": field_type, "entity": target_entity})
            else: logging.warning(f"Attempted update for custom field ID {field_id}, but no record found.")
        except sqlite3.Error as e: logging.error(f"Database error updating custom field definition {field_id}: {e}"); messagebox.showerror("Database Error", f"Error updating custom field: {e}"); conn.rollback()
        finally:
            if conn: conn.close()
        return success

    def delete_custom_field_definition(self, field_id):
        """Deletes a custom field definition and all its associated values."""
        conn = self._get_db_connection()
        if not conn: return False
        success = False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM custom_field_definitions WHERE id = ?", (field_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                 logging.info(f"Deleted custom field definition ID: {field_id} and associated values.")
                 self.log_audit_event(action="CUSTOM_FIELD_DEF_DELETE", target_id=str(field_id))
            else: logging.warning(f"Attempted delete for custom field ID {field_id}, but no record found.")
        except sqlite3.Error as e: logging.error(f"Database error deleting custom field definition {field_id}: {e}"); messagebox.showerror("Database Error", f"Error deleting custom field: {e}"); conn.rollback()
        finally:
            if conn: conn.close()
        return success

    # --- Custom Field Value Methods ---

    def load_custom_field_values(self, entity_id):
        """Loads all custom field values for a specific entity (customer or case)."""
        conn = self._get_db_connection()
        if not conn: return {}
        values = {}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id as definition_id, d.name as field_name, d.label as field_label, d.field_type, v.value
                FROM custom_field_values v JOIN custom_field_definitions d ON v.field_definition_id = d.id
                WHERE v.entity_id = ?
            """, (entity_id,))
            rows = cursor.fetchall()
            for row in rows: values[row['field_name']] = {'label': row['field_label'], 'type': row['field_type'], 'value': row['value'], 'definition_id': row['definition_id']}
            logging.debug(f"Loaded {len(values)} custom field values for entity {entity_id}.")
        except sqlite3.Error as e: logging.error(f"Error loading custom field values for entity {entity_id}: {e}")
        finally:
            if conn: conn.close()
        return values

    def save_custom_field_value(self, field_definition_id, entity_id, value):
        """Saves (inserts or updates) a single custom field value."""
        conn = self._get_db_connection()
        if not conn: return False
        success = False
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO custom_field_values (field_definition_id, entity_id, value) VALUES (?, ?, ?)", (field_definition_id, entity_id, value))
            conn.commit()
            success = True
            logging.debug(f"Saved custom field value for field {field_definition_id}, entity {entity_id}.")
        except sqlite3.Error as e: logging.error(f"Database error saving custom field value (field: {field_definition_id}, entity: {entity_id}): {e}"); conn.rollback()
        finally:
            if conn: conn.close()
        return success

    # --- Status Bar Methods ---
    def clear_status_message(self):
        """Clear the status message."""
        if self.parent and hasattr(self.parent, 'status_var'): self.parent.status_var.set("")

    def update_status(self, message, duration=3000):
        """Updates the status bar message and clears it after a duration."""
        if self.parent and hasattr(self.parent, 'status_var') and hasattr(self.parent, 'root'):
             self.parent.status_var.set(f"{message} ({datetime.now().strftime('%H:%M:%S')})")
             if duration > 0 and self.parent.root: self.parent.root.after(duration, self.clear_status_message)
        else: logging.warning(f"Cannot update status, parent missing required attributes. Message: {message}")

    def close_db(self):
        """Explicitly closes the database connection if it's open."""
        # Note: In this design, connections are opened/closed per operation.
        # This method is more of a placeholder or for future use if connection
        # management changes to be persistent. For now, it doesn't do much
        # as connections aren't kept persistently open by DataManager itself.
        # However, having it allows signaling shutdown intent.
        logging.info("Database close requested (connections are typically per-operation).")
        # If a persistent connection attribute existed (e.g., self._conn),
        # you would close it here:
        # if self._conn:
        #     try:
        #         self._conn.close()
        #         logging.info("Persistent database connection closed.")
        #         self._conn = None
        #     except sqlite3.Error as e:
        #         logging.error(f"Error closing persistent database connection: {e}")
