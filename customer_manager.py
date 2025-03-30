import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys

# Import utility modules
from utils import setup_logging
# Import custom exceptions (assuming defined in customer_operations or case_folder_operations)
try:
    from customer_operations import ValidationError, DatabaseError, FilesystemError
except ImportError:
    try:
        from case_folder_operations import ValidationError, DatabaseError, FilesystemError
    except ImportError:
        # Define locally if not found anywhere else (less ideal)
        class CustomerOpsError(Exception): pass
        class ValidationError(CustomerOpsError): pass
        class DatabaseError(CustomerOpsError): pass
        class FilesystemError(CustomerOpsError): pass


# Import operational modules
from customer_operations import CustomerOperations
from case_folder_operations import CaseFolderOperations

# Import UI and event handling modules
from ui_setup import UISetup
from event_handlers import EventHandlers
from treeview_manager import TreeviewManager

# Import data and form management modules
from data_manager import DataManager
from form_manager import FormManager
from dropdown_manager import DropdownManager
from bulk_operations import BulkOperations

class CustomerManager:
    """Main application class for customer management"""

    def __init__(self, root):
        """Initialize the customer manager with root Tk instance"""
        self.root = root
        self.root.title("Customer Directory Manager")
        self.root.geometry("900x700")

        # Apply a ttk theme for potentially better styling
        try:
            style = ttk.Style(self.root)
            available_themes = style.theme_names()
            logging.info(f"Available ttk themes: {available_themes}")
            preferred_themes = ['clam', 'alt', 'default']
            for theme in preferred_themes:
                 if theme in available_themes:
                     style.theme_use(theme)
                     logging.info(f"Applied ttk theme: {theme}")
                     break
            else:
                 logging.warning("Could not apply preferred ttk theme.")
        except tk.TclError as e:
            logging.warning(f"Failed to set ttk theme: {e}")

        # Initialize data management (now uses SQLite)
        self.data_manager = DataManager(self)
        self.customers = self.data_manager.load_customers() # Load initial data from DB
        self.templates = self.data_manager.load_templates() # Load initial data from DB

        # Initialize helper classes (passing self gives them access to data_manager etc.)
        self.customer_ops = CustomerOperations(self)
        self.case_ops = CaseFolderOperations(self)
        self.form_manager = FormManager(self)
        self.dropdown_manager = DropdownManager(self)
        self.bulk_ops = BulkOperations(self)

        # Setup variables
        self.setup_variables()

        # Setup event handlers
        self.event_handler = EventHandlers(self)

        # Create UI components
        self.ui_setup = UISetup(self)
        self.ui_setup.create_widgets()

        # Complete event handler setup
        self.event_handler.setup_events()

        # Setup treeview manager
        self.treeview_manager = TreeviewManager(self)

        # Refresh customer list (populates treeview and dropdowns)
        self.refresh_customer_list() # Initial population
        # Refresh template list (populates new treeview and dropdowns)
        self.event_handler.refresh_template_list() # Initial population for templates
        # Refresh custom field definitions list
        self.event_handler.refresh_custom_field_definitions_list() # Initial population for custom fields

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.safe_shutdown)

    def setup_variables(self):
        """Setup Tkinter variables"""
        # Form variables
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.dir_var = tk.StringVar()
        
        # Search variable
        self.search_var = tk.StringVar()
        
        # Status variable
        self.status_var = tk.StringVar()
        
        # Customer selection variables
        self.selected_customer_var = tk.StringVar()
        self.selected_customer_id_var = tk.StringVar()
        self.selected_template_var = tk.StringVar()
        self.template_desc_var = tk.StringVar()
        self.selected_case_id_var = tk.StringVar()
        self.case_number_var = tk.StringVar()
        self.case_description_var = tk.StringVar()
        self.case_filter_var = tk.StringVar()
        self.case_filter_field_var = tk.StringVar(value="all")
        self.search_field_var = tk.StringVar(value="all")

        # Template management form variables
        self.template_form_id_var = tk.StringVar()
        self.template_form_name_var = tk.StringVar()
        self.template_form_desc_var = tk.StringVar()
        # Note: Folders text widget doesn't need a StringVar, accessed directly
        
        # UI component references (initialized in UISetup)
        self.notebook = None
        self.add_customer_tab = None
        self.manage_customers_tab = None
        self.case_folder_tab = None
        self.customer_dropdown = None
        self.template_dropdown = None
        self.notes_text = None
        self.customer_tree = None
        self.case_tree = None
        self.template_tree = None # Add reference for template treeview
        self.template_form_folders_text = None
        self.template_id_entry = None

        # Custom Field definition form variables
        self.cf_form_name_var = tk.StringVar()
        self.cf_form_label_var = tk.StringVar()
        self.cf_form_type_var = tk.StringVar()
        self.cf_form_entity_var = tk.StringVar()

        # Custom Field UI component references
        self.custom_field_tree = None
        self.cf_name_entry = None # Reference to the name Entry for state control


    def refresh_customer_list(self):
        """Reload customer data from DB and refresh the UI"""
        logging.info("Refreshing customer list...")
        try:
            self.customers = self.data_manager.load_customers()
            self.treeview_manager.refresh_customer_list()
            self.dropdown_manager.update_customer_dropdown()
            logging.info("Customer list refresh complete.")
        except Exception as e:
             logging.error(f"Failed to refresh customer list: {e}", exc_info=True)
             messagebox.showerror("Error", f"Failed to load customer data:\n{e}")


    def refresh_case_list(self):
        """Refresh the case list for the selected customer"""
        customer_id = self.selected_customer_id_var.get()
        logging.info(f"Refreshing case list for customer ID: {customer_id}")
        try:
            self.treeview_manager.refresh_case_list()
            logging.info("Case list refresh complete.")
        except Exception as e:
             logging.error(f"Failed to refresh case list for customer {customer_id}: {e}", exc_info=True)
             messagebox.showerror("Error", f"Failed to load case data:\n{e}")


    def save_customer(self):
        """Save a customer using the form manager, handling exceptions."""
        try:
            # form_manager.save_customer calls customer_ops.add_customer which might raise errors
            new_customer_data = self.form_manager.save_customer()
            if new_customer_data:
                self.refresh_customer_list() # Refresh list to include the new customer
                self.data_manager.update_status(f"Customer '{new_customer_data.get('name')}' added successfully.")
                return True
            else:
                 # If save_customer returns False without raising (e.g., validation handled internally)
                 logging.warning("form_manager.save_customer returned False without raising an exception.")
                 return False
        except (ValidationError, DatabaseError, FilesystemError) as e:
             logging.error(f"Error saving customer: {e}")
             messagebox.showerror("Save Error", str(e), parent=self.root)
             return False
        except Exception as e: # Catch unexpected errors
             logging.critical("Unexpected error saving customer.", exc_info=True)
             messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}", parent=self.root)
             return False

    def clear_form(self):
        """Clear the customer form"""
        self.form_manager.clear_customer_form()

    def create_case_folder(self):
        """Create a case folder for the selected customer, handling exceptions."""
        customer_id = self.selected_customer_id_var.get()
        if not customer_id:
             messagebox.showerror("Error", "Please select a customer first.", parent=self.root)
             return

        case_number = self.case_number_var.get().strip()
        description = self.case_description_var.get().strip()
        template = self.dropdown_manager.get_selected_template()

        try:
            # Attempt to create the folder (filesystem and DB)
            success = self.case_ops.create_case_folder(
                customer_id,
                case_number,
                description,
                template
            )
            # create_case_folder now returns True or raises an exception

            if success:
                # Clear the form fields only on success
                self.case_number_var.set("")
                self.case_description_var.set("")
                # Refresh the case folder list for the currently selected customer
                self.refresh_case_list()
                # Optionally show status message
                self.data_manager.update_status(f"Case folder '{case_number}' created.")

        except (ValidationError, DatabaseError, FilesystemError) as e:
             logging.error(f"Error creating case folder: {e}")
             messagebox.showerror("Creation Error", str(e), parent=self.root)
        except Exception as e: # Catch unexpected errors
             logging.critical("Unexpected error creating case folder.", exc_info=True)
             messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}", parent=self.root)


    def load_customers(self):
        """Load customers from database via DataManager."""
        return self.data_manager.load_customers()

    def load_templates(self):
        """Load template configurations from database via DataManager."""
        return self.data_manager.load_templates()

    def update_customer_dropdown(self):
        """Update the customer dropdown with current customers."""
        self.dropdown_manager.update_customer_dropdown()

    def update_template_dropdown(self):
        """Update the template dropdown with current templates."""
        self.dropdown_manager.update_template_dropdown()

    def select_directory(self):
        """Open a dialog to select a directory for the customer form."""
        try:
            directory = self.customer_ops.select_directory()
            if directory:
                self.dir_var.set(directory)
        except Exception as e: # Catch potential errors if UI context is missing
             logging.error(f"Error selecting directory: {e}", exc_info=True)
             messagebox.showerror("Error", f"Could not open directory dialog: {e}", parent=self.root)


    def create_directory(self):
        """Create a new directory for a customer via dialog."""
        suggested_name = self.name_var.get().strip() or "new_customer"
        try:
            new_dir = self.customer_ops.create_directory(suggested_name)
            if new_dir:
                self.dir_var.set(new_dir)
                self.data_manager.update_status(f"Directory created: {new_dir}")
        except (ValidationError, FilesystemError) as e:
             logging.error(f"Error creating directory: {e}")
             messagebox.showerror("Directory Error", str(e), parent=self.root)
        except Exception as e:
             logging.critical("Unexpected error creating directory.", exc_info=True)
             messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}", parent=self.root)


    def open_customer_directory(self):
        """Open the directory for the selected customer."""
        try:
            self.bulk_ops.open_customer_directory()
        except Exception as e: # Catch errors from bulk_ops/utils
             logging.error(f"Error opening customer directory: {e}", exc_info=True)
             messagebox.showerror("Error", f"Could not open directory: {e}", parent=self.root)


    def export_customers(self, format_type):
        """Export selected customers to CSV or JSON."""
        try:
            self.bulk_ops.export_customers(format_type)
            # Success message handled by bulk_ops using status bar
        except (ValidationError, FilesystemError, DatabaseError) as e:
             logging.error(f"Error exporting customers: {e}")
             messagebox.showerror("Export Error", str(e), parent=self.root)
        except Exception as e:
             logging.critical("Unexpected error exporting customers.", exc_info=True)
             messagebox.showerror("Critical Error", f"An unexpected error occurred during export: {e}", parent=self.root)


    def batch_update_customers(self):
        """Update multiple customers at once."""
        # This method in bulk_ops handles its own dialog and error reporting
        self.bulk_ops.batch_update_customers()


    def delete_selected_customers(self):
        """Delete multiple selected customers."""
        # This method in bulk_ops handles its own confirmation and error reporting
        self.bulk_ops.delete_selected_customers()


    def move_case_folder(self):
        """Show dialog to move a case folder between customers."""
        try:
            # Get selected case folder ID from the case_tree
            selected_items = self.case_tree.selection()
            if not selected_items:
                messagebox.showerror("Error", "Please select a case folder to move.", parent=self.root)
                return
            
            case_folder_id = selected_items[0]
            
            # Fetch necessary info (might raise DatabaseError)
            case_info = self.case_ops._execute_query("SELECT customer_id, path FROM case_folders WHERE id = ?", (case_folder_id,), fetch_one=True)
            if not case_info:
                 messagebox.showerror("Error", "Could not retrieve case folder details.", parent=self.root)
                 return
            source_customer_id = case_info['customer_id']
            case_folder_name = os.path.basename(case_info['path'])

            source_customer = self.customer_ops.get_customer_by_id(source_customer_id)
            source_name = source_customer.get("name", "Unknown") if source_customer else "Unknown"

            all_customers = self.data_manager.load_customers()

        except DatabaseError as e:
             logging.error(f"Error fetching data for move dialog: {e}")
             messagebox.showerror("Database Error", f"Could not fetch data needed to move folder:\n{e}", parent=self.root)
             return
        except Exception as e:
             logging.critical("Unexpected error preparing move dialog.", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred preparing the move: {e}", parent=self.root)
             return

        # --- Create Dialog ---
        dialog = tk.Toplevel(self.root)
        dialog.title("Move Case Folder")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # Source customer display
        source_frame = ttk.Frame(dialog); source_frame.pack(fill='x', padx=20, pady=(20, 10))
        ttk.Label(source_frame, text="Source Customer:").pack(side='left', padx=(0, 10))
        ttk.Label(source_frame, text=f"{source_name} (ID: {source_customer_id})").pack(side='left')

        # Case folder display
        case_frame = ttk.Frame(dialog); case_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(case_frame, text="Case Folder:").pack(side='left', padx=(0, 10))
        ttk.Label(case_frame, text=case_folder_name).pack(side='left')

        # Target customer dropdown
        target_frame = ttk.Frame(dialog); target_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(target_frame, text="Target Customer:").pack(side='left', padx=(0, 10))
        target_var = tk.StringVar()
        target_dropdown = ttk.Combobox(target_frame, textvariable=target_var, width=40, state="readonly")
        target_dropdown.pack(side='left', fill='x', expand=True)

        # Populate target dropdown
        target_customers_map = {}
        display_names = []
        for customer in all_customers:
            cust_id = customer.get("id")
            if cust_id != source_customer_id:
                display_name = f"{customer.get('name', 'Unnamed')} (ID: {cust_id})"
                target_customers_map[display_name] = cust_id
                display_names.append(display_name)
        target_dropdown['values'] = display_names
        if display_names: target_dropdown.current(0)

        # Warning label
        warning_frame = ttk.Frame(dialog); warning_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(warning_frame, text="Warning: This physically moves the case folder directory.", foreground="darkred").pack(fill='x')

        # Buttons
        btn_frame = ttk.Frame(dialog); btn_frame.pack(fill='x', padx=20, pady=20)

        def on_move():
            selected_display_name = target_var.get()
            if not selected_display_name:
                messagebox.showerror("Error", "Please select a target customer.", parent=dialog)
                return
            target_customer_id = target_customers_map.get(selected_display_name)
            if not target_customer_id:
                 messagebox.showerror("Error", "Invalid target customer selection.", parent=dialog)
                 return

            try:
                move_successful = self.case_ops.move_case_folder(case_folder_id, target_customer_id)
                if move_successful: # Returns True on success, False if no-op, raises on error
                    dialog.destroy()
                    self.refresh_case_list()
                    self.refresh_customer_list()
                    self.data_manager.update_status(f"Case folder '{case_folder_name}' moved successfully.")
                # else: # Handle False return (no-op) if needed, e.g., show info message
                #    messagebox.showinfo("Info", "Case folder already belongs to the target customer.", parent=dialog)

            except (ValidationError, DatabaseError, FilesystemError) as e:
                 logging.error(f"Error moving case folder: {e}")
                 messagebox.showerror("Move Error", str(e), parent=dialog)
            except Exception as e:
                 logging.critical("Unexpected error moving case folder.", exc_info=True)
                 messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}", parent=dialog)

        ttk.Button(btn_frame, text="Move", command=on_move).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)

        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

    def safe_shutdown(self):
        """Handle graceful shutdown procedures."""
        logging.info("Initiating safe shutdown...")
        # Add any other necessary cleanup steps here
        # e.g., saving unsaved changes, closing network connections

        # Close the database connection
        self.data_manager.close_db()

        # Destroy the Tkinter window
        self.root.destroy()
        logging.info("Application shut down gracefully.")

    def on_closing(self):
        """Handle window closing"""
        logging.info("Closing application.")
        self.safe_shutdown()

    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.safe_shutdown)
        self.root.mainloop()

if __name__ == "__main__":
    setup_logging() # Configure logging
    logging.info("Starting Customer Management Application...")
    root = tk.Tk()
    try:
        app = CustomerManager(root)
        app.run()
    except Exception as e:
         logging.critical("Unhandled exception caused application to crash.", exc_info=True)
         # Ensure messagebox is imported if needed here
         from tkinter import messagebox
         messagebox.showerror("Critical Error", f"A critical error occurred:\n{e}\nPlease check the app.log file for details.")
         try: root.destroy()
         except: pass
    logging.info("Application closed.")
