import tkinter as tk
from tkinter import ttk, messagebox

# Import utility modules

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
        
        # Initialize data management        
        self.data_manager = DataManager(self)
        self.customers = self.data_manager.load_customers()
        self.templates = self.data_manager.load_templates()
        
        # Initialize helper classes
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
        
        # Refresh customer list
        self.treeview_manager.refresh_customer_list()
        
        # Configure auto-save
        self.data_manager.start_autosave_timer()
    
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
        self.selected_customer_var = tk.StringVar()  # This will store customer name for display
        self.selected_customer_id_var = tk.StringVar()  # This will store customer ID for operations
        self.selected_template_var = tk.StringVar()
        self.template_desc_var = tk.StringVar()
        self.selected_case_var = tk.StringVar()
        self.case_number_var = tk.StringVar()
        self.case_description_var = tk.StringVar()
        self.case_filter_var = tk.StringVar()
        self.case_filter_field_var = tk.StringVar(value="all")
        self.search_field_var = tk.StringVar(value="all")
        
        # UI component references
        self.notebook = None
        self.add_customer_tab = None
        self.manage_customers_tab = None
        self.case_folder_tab = None
        self.customer_dropdown = None
        self.template_dropdown = None
        self.template_description_text = None
        self.notes_text = None
        self.customer_tree = None
        self.case_tree = None
    
    def refresh_customer_list(self):
        """Refresh the customer list in UI"""
        self.treeview_manager.refresh_customer_list()
        self.dropdown_manager.update_customer_dropdown()
    
    def refresh_case_list(self):
        """Refresh the case list for the selected customer"""
        self.treeview_manager.refresh_case_list()
    
    def save_customer(self):
        """Save a customer using the form manager"""
        return self.form_manager.save_customer()
    
    def clear_form(self):
        """Clear the customer form"""
        self.form_manager.clear_customer_form()
    
    def create_case_folder(self):
        """Create a case folder for the selected customer"""
        customer_id = self.selected_customer_id_var.get()
        case_number = self.case_number_var.get().strip()
        description = self.case_description_var.get().strip()
        template = self.dropdown_manager.get_selected_template()
        
        # Create the case folder
        success = self.case_ops.create_case_folder(
            customer_id,
            case_number,
            description,
            template
        )
        
        if success:
            # Clear the form fields
            self.case_number_var.set("")
            self.case_description_var.set("")
            
            # Refresh the case folder list
            self.refresh_case_list()
    
    def save_customers(self):
        """Save customers to file"""
        return self.data_manager.save_customers()
    
    def load_customers(self):
        """Load customers from file"""
        return self.data_manager.load_customers()
    
    def load_templates(self):
        """Load template configurations from file"""
        return self.data_manager.load_templates()
    
    def update_customer_dropdown(self):
        """Update the customer dropdown with current customers"""
        self.dropdown_manager.update_customer_dropdown()
    
    def update_template_dropdown(self):
        """Update the template dropdown with current templates"""
        self.dropdown_manager.update_template_dropdown()
    
    def select_directory(self):
        """Open a dialog to select a directory"""
        directory = self.customer_ops.select_directory()
        if directory:
            self.dir_var.set(directory)
    
    def create_directory(self):
        """Create a new directory for a customer"""
        suggested_name = self.name_var.get().strip()
        if not suggested_name:
            suggested_name = "new_customer"
        
        new_dir = self.customer_ops.create_directory(suggested_name)
        if new_dir:
            self.dir_var.set(new_dir)
    
    def open_customer_directory(self):
        """Open the directory for the selected customer"""
        self.bulk_ops.open_customer_directory()
    
    def export_customers(self, format_type):
        """Export selected customers to CSV or JSON"""
        self.bulk_ops.export_customers(format_type)
    
    def batch_update_customers(self):
        """Update multiple customers at once"""
        self.bulk_ops.batch_update_customers()
    
    def delete_selected_customers(self):
        """Delete multiple selected customers"""
        self.bulk_ops.delete_selected_customers()
    
    def edit_customer(self):
        """Edit the selected customer"""
        selected_items = self.customer_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a customer to edit")
            return

        customer_id = self.customer_tree.item(selected_items[0])['values'][0]

        # Find the customer
        customer = self.customer_ops.find_customer_by_id(customer_id)
        if not customer:
            messagebox.showerror("Error", "Customer not found")
            return

        # Open the edit customer dialog
        self.customer_ops.edit_customer_dialog(customer)

        # Refresh the list
        self.refresh_customer_list()
    
    def move_case_folder(self):
        """Show dialog to move a case folder between customers"""
        # Get selected customer from the case folder tab
        source_customer_id = self.selected_customer_id_var.get()
        if not source_customer_id:
            messagebox.showerror("Error", "Please select a source customer")
            return
            
        # Get selected case folder
        selected_items = self.case_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a case folder to move")
            return
            
        case_folder_name = self.case_tree.item(selected_items[0])['values'][0]
        
        # Create dialog for moving case folder
        dialog = tk.Toplevel(self.root)
        dialog.title("Move Case Folder")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Source customer (display only)
        source_frame = ttk.Frame(dialog)
        source_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        ttk.Label(source_frame, text="Source Customer:").pack(side='left', padx=(0, 10))
        source_name = ""
        for customer in self.customers:
            if customer.get("id") == source_customer_id:
                source_name = customer.get("name", "")
                break
                
        ttk.Label(source_frame, text=source_name).pack(side='left')
        
        # Case folder (display only)
        case_frame = ttk.Frame(dialog)
        case_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(case_frame, text="Case Folder:").pack(side='left', padx=(0, 10))
        ttk.Label(case_frame, text=case_folder_name).pack(side='left')
        
        # Target customer (dropdown)
        target_frame = ttk.Frame(dialog)
        target_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(target_frame, text="Target Customer:").pack(side='left', padx=(0, 10))
        target_var = tk.StringVar()
        target_dropdown = ttk.Combobox(target_frame, textvariable=target_var, width=30)
        target_dropdown.pack(side='left', fill='x', expand=True)
        
        # Populate target dropdown
        customer_ids = []
        customer_names = []
        
        for customer in self.customers:
            # Don't include the source customer
            if customer.get("id") != source_customer_id:
                customer_ids.append(customer.get("id"))
                customer_names.append(customer.get("name", ""))
                
        target_dropdown['values'] = customer_names
        
        # Add warning label
        warning_frame = ttk.Frame(dialog)
        warning_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(
            warning_frame, 
            text="Warning: This will physically move the case folder to another customer's directory.",
            foreground="darkred"
        ).pack(fill='x')
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        def on_move():
            if not target_var.get():
                messagebox.showerror("Error", "Please select a target customer")
                return
                
            # Get target customer ID from selection
            target_idx = target_dropdown.current()
            if target_idx < 0:
                messagebox.showerror("Error", "Please select a valid target customer")
                return
                
            target_customer_id = customer_ids[target_idx]
            
            # Move the case folder
            if self.case_ops.move_case_folder(source_customer_id, case_folder_name, target_customer_id):
                dialog.destroy()
                # Refresh the case list
                self.refresh_case_list()
        
        ttk.Button(btn_frame, text="Move", command=on_move).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)
        
        # Center dialog on parent window
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def on_closing(self):
        """Handle window closing"""
        # Save data on exit
        self.save_customers()
        
        # Cancel auto-save timer
        self.data_manager.cancel_autosave()
        
        # Destroy root window
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        # Set protocol for window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the main loop
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = CustomerManager(root)
    app.run()
