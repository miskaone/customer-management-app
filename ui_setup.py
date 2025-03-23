import tkinter as tk
from tkinter import ttk, messagebox
import os

from ui_components import add_tooltip

class UISetup:
    """Handles the UI setup for the Customer Manager application"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def create_widgets(self):
        """Create the main widgets for the application"""
        # Main notebook to hold tabs
        self.parent.notebook = ttk.Notebook(self.parent.root)
        self.parent.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.parent.add_customer_tab = ttk.Frame(self.parent.notebook)
        self.parent.manage_customers_tab = ttk.Frame(self.parent.notebook)
        self.parent.case_folder_tab = ttk.Frame(self.parent.notebook)
        
        # Add tabs to notebook
        self.parent.notebook.add(self.parent.add_customer_tab, text="Add Customer")
        self.parent.notebook.add(self.parent.manage_customers_tab, text="Manage Customers")
        self.parent.notebook.add(self.parent.case_folder_tab, text="Create Case Folder")
        
        # Status bar
        status_frame = ttk.Frame(self.parent.root)
        status_frame.pack(fill='x', side='bottom', padx=10, pady=2)
        
        # Status message
        status_label = ttk.Label(status_frame, textvariable=self.parent.status_var)
        status_label.pack(side='left')
        
        # Auto-save indicator
        autosave_label = ttk.Label(status_frame, text="Auto-saving enabled")
        autosave_label.pack(side='right')
        
        # Setup tab content
        self.setup_add_customer_tab()
        self.setup_manage_customers_tab()
        self.setup_case_folder_tab()
    
    def setup_add_customer_tab(self):
        """Setup the Add Customer tab"""
        # Basic information
        info_frame = ttk.LabelFrame(self.parent.add_customer_tab, text="Customer Information")
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Customer Name
        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.parent.name_var = tk.StringVar()
        name_entry = ttk.Entry(info_frame, textvariable=self.parent.name_var, width=40)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(name_entry, "Customer's full name or company name")
        
        # Email
        ttk.Label(info_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.parent.email_var = tk.StringVar()
        email_entry = ttk.Entry(info_frame, textvariable=self.parent.email_var, width=40)
        email_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(email_entry, "Customer's email address")
        
        # Phone
        ttk.Label(info_frame, text="Phone:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.parent.phone_var = tk.StringVar()
        phone_entry = ttk.Entry(info_frame, textvariable=self.parent.phone_var, width=40)
        phone_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(phone_entry, "Customer's phone number")
        
        # Address
        ttk.Label(info_frame, text="Address:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.parent.address_var = tk.StringVar()
        address_entry = ttk.Entry(info_frame, textvariable=self.parent.address_var, width=40)
        address_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(address_entry, "Customer's physical address")
        
        # Notes
        ttk.Label(info_frame, text="Notes:").grid(row=4, column=0, padx=5, pady=5, sticky='nw')
        self.parent.notes_text = tk.Text(info_frame, width=40, height=5)
        self.parent.notes_text.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(self.parent.notes_text, "Additional notes about the customer")
        
        # Directory section
        dir_frame = ttk.LabelFrame(self.parent.add_customer_tab, text="Customer Directory")
        dir_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Directory path
        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.parent.dir_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.parent.dir_var, width=40)
        dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(dir_entry, "Path to the customer's directory for storing case folders")
        
        # Directory buttons
        btn_frame = ttk.Frame(dir_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        select_btn = ttk.Button(btn_frame, text="Select Existing", command=self.parent.select_directory)
        select_btn.pack(side='left', padx=5)
        add_tooltip(select_btn, "Select an existing directory")
        
        create_btn = ttk.Button(btn_frame, text="Create New", command=self.parent.create_directory)
        create_btn.pack(side='left', padx=5)
        add_tooltip(create_btn, "Create a new directory for this customer")
        
        # Save button
        save_frame = ttk.Frame(self.parent.add_customer_tab)
        save_frame.pack(fill='x', padx=10, pady=20)
        save_btn = ttk.Button(save_frame, text="Save Customer", command=self.parent.save_customer)
        save_btn.pack(side='right')
        add_tooltip(save_btn, "Save the customer information")
    
    def setup_manage_customers_tab(self):
        """Setup the Manage Customers tab"""
        # Search and filter frame
        search_frame = ttk.Frame(self.parent.manage_customers_tab)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        # Search field dropdown
        ttk.Label(search_frame, text="Search in:").pack(side='left', padx=5)
        search_field = ttk.Combobox(search_frame, textvariable=self.parent.search_field_var, width=10)
        search_field['values'] = ('all', 'name', 'email', 'phone')
        search_field.pack(side='left', padx=5)
        add_tooltip(search_field, "Select which field to search in")
        
        # Search entry
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.parent.search_var, width=30)
        search_entry.pack(side='left', padx=5)
        add_tooltip(search_entry, "Search for customers (Ctrl+F)")
        
        # Clear search button
        clear_btn = ttk.Button(search_frame, text="Clear", command=self.parent.event_handler.clear_search)
        clear_btn.pack(side='left', padx=5)
        add_tooltip(clear_btn, "Clear search and show all customers")
        
        # Treeview for displaying customers
        tree_frame = ttk.Frame(self.parent.manage_customers_tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create treeview with scrollbars
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side='right', fill='y')
        
        self.parent.customer_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode='extended')
        self.parent.customer_tree.pack(fill='both', expand=True)
        tree_scroll.config(command=self.parent.customer_tree.yview)
        
        # Define columns
        self.parent.customer_tree['columns'] = ('id', 'name', 'email', 'phone', 'directory', 'created')
        
        # Format columns
        self.parent.customer_tree.column('#0', width=0, stretch=tk.NO)
        self.parent.customer_tree.column('id', width=0, stretch=tk.NO)  # Hidden ID column
        self.parent.customer_tree.column('name', width=150, anchor=tk.W)
        self.parent.customer_tree.column('email', width=150, anchor=tk.W)
        self.parent.customer_tree.column('phone', width=100, anchor=tk.W)
        self.parent.customer_tree.column('directory', width=200, anchor=tk.W)
        self.parent.customer_tree.column('created', width=100, anchor=tk.W)
        
        # Create headings
        self.parent.customer_tree.heading('#0', text='', anchor=tk.W)
        self.parent.customer_tree.heading('id', text='ID', anchor=tk.W)
        self.parent.customer_tree.heading('name', text='Name', anchor=tk.W)
        self.parent.customer_tree.heading('email', text='Email', anchor=tk.W)
        self.parent.customer_tree.heading('phone', text='Phone', anchor=tk.W)
        self.parent.customer_tree.heading('directory', text='Directory', anchor=tk.W)
        self.parent.customer_tree.heading('created', text='Created', anchor=tk.W)
        
        # Add onClick sorting
        for col in self.parent.customer_tree['columns']:
            if col != 'id':  # Skip the ID column
                self.parent.customer_tree.heading(col, command=lambda _col=col: self.parent.treeview_manager.sort_treeview(_col))
        
        # Buttons frame
        btn_frame = ttk.Frame(self.parent.manage_customers_tab)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        # Customer actions group
        action_frame = ttk.LabelFrame(btn_frame, text="Customer Actions")
        action_frame.pack(side='left', padx=5, pady=5)
        
        # Open directory button
        open_btn = ttk.Button(action_frame, text="Open Directory", command=self.parent.open_customer_directory)
        open_btn.pack(side='left', padx=5, pady=5)
        add_tooltip(open_btn, "Open the selected customer's directory")
        
        # Rename button
        rename_btn = ttk.Button(action_frame, text="Rename", command=self.parent.customer_ops.show_rename_dialog)
        rename_btn.pack(side='left', padx=5, pady=5)
        add_tooltip(rename_btn, "Rename selected customer")
        
        # Edit button
        edit_btn = ttk.Button(action_frame, text="Edit Selected", command=self.parent.batch_update_customers)
        edit_btn.pack(side='left', padx=5, pady=5)
        add_tooltip(edit_btn, "Edit the selected customers")
        
        # Delete button
        delete_btn = ttk.Button(action_frame, text="Delete Selected", command=self.parent.delete_selected_customers)
        delete_btn.pack(side='left', padx=5, pady=5)
        add_tooltip(delete_btn, "Delete the selected customers (Ctrl+D)")
        
        # Create case button
        case_btn = ttk.Button(btn_frame, text="Create Case Folder", command=self.parent.event_handler.switch_to_case_folder_tab)
        case_btn.pack(side='right', padx=5)
        add_tooltip(case_btn, "Switch to case folder creation tab")
        
        # Export buttons
        export_frame = ttk.Frame(btn_frame)
        export_frame.pack(side='left', padx=5)
        
        # Import directories button group
        import_frame = ttk.LabelFrame(export_frame, text="Import")
        import_frame.pack(side='left', padx=5, pady=5)
        
        # Bulk import button
        bulk_import_btn = ttk.Button(import_frame, text="Bulk Import", 
                                     command=lambda: self.parent.bulk_ops.import_from_directory(selective=False))
        bulk_import_btn.pack(side='top', padx=5, pady=2, fill='x')
        add_tooltip(bulk_import_btn, "Import all customers from directories")
        
        # Selective import button
        selective_import_btn = ttk.Button(import_frame, text="Selective Import", 
                                          command=lambda: self.parent.bulk_ops.import_from_directory(selective=True))
        selective_import_btn.pack(side='top', padx=5, pady=2, fill='x')
        add_tooltip(selective_import_btn, "Select which directories to import as customers")
        
        # Export group
        export_group = ttk.LabelFrame(export_frame, text="Export")
        export_group.pack(side='left', padx=5, pady=5)
        
        # Export to CSV button
        csv_btn = ttk.Button(export_group, text="CSV", command=lambda: self.parent.bulk_ops.export_customers("csv"))
        csv_btn.pack(side='top', padx=5, pady=2, fill='x')
        add_tooltip(csv_btn, "Export selected customers to CSV file (Ctrl+E)")
        
        # JSON export
        json_btn = ttk.Button(export_group, text="JSON", 
                            command=lambda: self.parent.bulk_ops.export_customers("json"))
        json_btn.pack(side='top', padx=5, pady=2, fill='x')
        add_tooltip(json_btn, "Export selected customers to JSON file")
    
    def setup_case_folder_tab(self):
        """Setup the Case Folder tab"""
        # Top frame for customer selection
        top_frame = ttk.Frame(self.parent.case_folder_tab)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        # Customer selection
        ttk.Label(top_frame, text="Select Customer:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.parent.customer_dropdown = ttk.Combobox(top_frame, textvariable=self.parent.selected_customer_var, width=40)
        self.parent.customer_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(self.parent.customer_dropdown, "Select the customer to create a case folder for")
        
        # Initialize dropdown with customers
        self.parent.update_customer_dropdown()
        
        # Case information
        case_frame = ttk.LabelFrame(self.parent.case_folder_tab, text="Case Information")
        case_frame.pack(fill='x', padx=10, pady=10)
        
        # Case number
        ttk.Label(case_frame, text="Case Number:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        case_num_entry = ttk.Entry(case_frame, textvariable=self.parent.case_number_var, width=20)
        case_num_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(case_num_entry, "Case number (must start with MS)")
        
        # Add validation for case number
        self.parent.case_number_var.trace_add("write", self.parent.event_handler.validate_case_number)
        
        # MS prefix button
        ms_btn = ttk.Button(case_frame, text="Add MS Prefix", command=self.parent.event_handler.add_ms_prefix)
        ms_btn.grid(row=0, column=2, padx=5, pady=5, sticky='w')
        add_tooltip(ms_btn, "Add MS prefix to case number if missing")
        
        # Description
        ttk.Label(case_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        description_entry = ttk.Entry(case_frame, textvariable=self.parent.case_description_var, width=40)
        description_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='w')
        add_tooltip(description_entry, "Brief description of the case")
        
        # Template selection
        template_frame = ttk.LabelFrame(self.parent.case_folder_tab, text="Folder Template")
        template_frame.pack(fill='x', padx=10, pady=10)
        
        # Template dropdown
        ttk.Label(template_frame, text="Select Template:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.parent.template_dropdown = ttk.Combobox(template_frame, textvariable=self.parent.selected_template_var, width=30)
        self.parent.template_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        add_tooltip(self.parent.template_dropdown, "Select a folder template to use")
        
        # Bind template selection event
        self.parent.template_dropdown.bind("<<ComboboxSelected>>", self.parent.event_handler.on_template_selected)
        
        # Initialize dropdown with templates
        self.parent.dropdown_manager.update_template_dropdown()
        
        # Template description
        description_label = ttk.Label(template_frame, textvariable=self.parent.template_desc_var, wraplength=400)
        description_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='w')
        
        # Create button
        create_btn = ttk.Button(self.parent.case_folder_tab, text="Create Case Folder", command=self.parent.create_case_folder)
        create_btn.pack(padx=10, pady=20)
        add_tooltip(create_btn, "Create a case folder based on selected template")
        
        # Existing case folders section
        folder_frame = ttk.LabelFrame(self.parent.case_folder_tab, text="Existing Case Folders")
        folder_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Search and filter for case folders
        filter_frame = ttk.Frame(folder_frame)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        # Filter field dropdown
        ttk.Label(filter_frame, text="Filter by:").pack(side='left', padx=5)
        case_filter_field = ttk.Combobox(filter_frame, textvariable=self.parent.case_filter_field_var, width=10)
        case_filter_field['values'] = ('all', 'case', 'description')
        case_filter_field.pack(side='left', padx=5)
        add_tooltip(case_filter_field, "Select which field to filter by")
        
        # Filter entry
        ttk.Label(filter_frame, text="Filter:").pack(side='left', padx=5)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.parent.case_filter_var, width=30)
        filter_entry.pack(side='left', padx=5)
        add_tooltip(filter_entry, "Filter case folders")
        
        # Refresh button
        refresh_btn = ttk.Button(filter_frame, text="Refresh", command=self.parent.refresh_case_list)
        refresh_btn.pack(side='right', padx=5)
        add_tooltip(refresh_btn, "Refresh the list of case folders")
        
        # Treeview for case folders
        case_tree_frame = ttk.Frame(folder_frame)
        case_tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar
        case_scroll = ttk.Scrollbar(case_tree_frame)
        case_scroll.pack(side='right', fill='y')
        
        # Create treeview
        self.parent.case_tree = ttk.Treeview(case_tree_frame, yscrollcommand=case_scroll.set)
        self.parent.case_tree.pack(fill='both', expand=True)
        case_scroll.config(command=self.parent.case_tree.yview)
        
        # Define columns
        self.parent.case_tree['columns'] = ('path', 'case', 'description', 'created')
        
        # Format columns
        self.parent.case_tree.column('#0', width=0, stretch=tk.NO)
        self.parent.case_tree.column('path', width=0, stretch=tk.NO)  # Hidden path column
        self.parent.case_tree.column('case', width=150, anchor=tk.W)
        self.parent.case_tree.column('description', width=200, anchor=tk.W)
        self.parent.case_tree.column('created', width=100, anchor=tk.W)
        
        # Create headings
        self.parent.case_tree.heading('#0', text='', anchor=tk.W)
        self.parent.case_tree.heading('path', text='Path', anchor=tk.W)
        self.parent.case_tree.heading('case', text='Case #', anchor=tk.W)
        self.parent.case_tree.heading('description', text='Description', anchor=tk.W)
        self.parent.case_tree.heading('created', text='Created', anchor=tk.W)
        
        # Add onClick sorting for case folders
        cols = self.parent.case_tree['columns']
        for col in cols:
            if col != 'path':  # Skip the hidden path column
                self.parent.case_tree.heading(col, text=col)
                self.parent.case_tree.heading(col, command=lambda _col=col: self.parent.treeview_manager.sort_treeview(_col))
        
        # Create a frame for buttons
        case_buttons_frame = ttk.Frame(folder_frame)
        case_buttons_frame.pack(fill='x', padx=5, pady=5)
        
        # Open case folder button
        open_case_btn = ttk.Button(case_buttons_frame, text="Open Selected Case Folder", 
                                   command=lambda: self.parent.case_ops.open_case_folder(
                                       self.parent.selected_customer_var.get(),
                                       self.parent.selected_case_var.get()
                                   ))
        open_case_btn.pack(side='left', padx=5)
        add_tooltip(open_case_btn, "Open the selected case folder")
        
        # Add Move Case Folder button
        move_case_btn = ttk.Button(case_buttons_frame, text="Move Case Folder", 
                                   command=self.parent.move_case_folder)
        move_case_btn.pack(side='left', padx=5)
        add_tooltip(move_case_btn, "Move the selected case folder to another customer")
