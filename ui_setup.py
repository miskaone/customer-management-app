import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging

from ui_components import add_tooltip

class UISetup:
    """Handles the UI setup for the Customer Manager application"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def create_widgets(self):
        """Create the main widgets for the application"""
        self.parent.notebook = ttk.Notebook(self.parent.root)
        self.parent.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self._create_tabs()
        status_frame = ttk.Frame(self.parent.root)
        status_frame.pack(fill='x', side='bottom', padx=10, pady=2)
        status_label = ttk.Label(status_frame, textvariable=self.parent.status_var)
        status_label.pack(side='left')
        self.setup_add_customer_tab()
        self.setup_manage_customers_tab()
        self.setup_case_folder_tab()
        self.setup_manage_templates_tab()
        self._setup_shutdown_button()

    def _create_tabs(self):
        """Create the main tabs for the application"""
        self.parent.add_customer_tab = ttk.Frame(self.parent.notebook)
        self.parent.manage_customers_tab = ttk.Frame(self.parent.notebook)
        self.parent.case_folder_tab = ttk.Frame(self.parent.notebook)
        self.parent.manage_templates_tab = ttk.Frame(self.parent.notebook)
        self.parent.notebook.add(self.parent.add_customer_tab, text="Add Customer")
        self.parent.notebook.add(self.parent.manage_customers_tab, text="Manage Customers")
        self.parent.notebook.add(self.parent.case_folder_tab, text="Create Case Folder")
        self.parent.notebook.add(self.parent.manage_templates_tab, text="Manage Templates")

    def setup_add_customer_tab(self):
        """Setup the Add Customer tab"""
        self._setup_add_customer_info_frame()
        self._setup_add_customer_directory_section()
        save_frame = ttk.Frame(self.parent.add_customer_tab)
        save_frame.pack(fill='x', padx=10, pady=20)
        save_btn = ttk.Button(save_frame, text="Save Customer", command=self.parent.save_customer)
        save_btn.pack(side='right')
        add_tooltip(save_btn, "Save the customer information")

    def _setup_add_customer_info_frame(self):
        """Setup the customer information frame in Add Customer tab"""
        info_frame = ttk.LabelFrame(self.parent.add_customer_tab, text="Customer Information")
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.parent.name_var = tk.StringVar()
        name_entry = ttk.Entry(info_frame, textvariable=self.parent.name_var, width=40)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w'); add_tooltip(name_entry, "Customer's name")
        ttk.Label(info_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.parent.email_var = tk.StringVar()
        email_entry = ttk.Entry(info_frame, textvariable=self.parent.email_var, width=40)
        email_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w'); add_tooltip(email_entry, "Customer's email")
        ttk.Label(info_frame, text="Phone:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.parent.phone_var = tk.StringVar()
        phone_entry = ttk.Entry(info_frame, textvariable=self.parent.phone_var, width=40)
        phone_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w'); add_tooltip(phone_entry, "Customer's phone")
        ttk.Label(info_frame, text="Address:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.parent.address_var = tk.StringVar()
        address_entry = ttk.Entry(info_frame, textvariable=self.parent.address_var, width=40)
        address_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w'); add_tooltip(address_entry, "Customer's address")
        ttk.Label(info_frame, text="Notes:").grid(row=4, column=0, padx=5, pady=5, sticky='nw')
        self.parent.notes_text = tk.Text(info_frame, width=40, height=5)
        self.parent.notes_text.grid(row=4, column=1, padx=5, pady=5, sticky='w'); add_tooltip(self.parent.notes_text, "Notes")

    def _setup_add_customer_directory_section(self):
        """Setup the directory section in the Add Customer tab"""
        dir_frame = ttk.LabelFrame(self.parent.add_customer_tab, text="Customer Directory")
        dir_frame.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.parent.dir_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.parent.dir_var, width=40)
        dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w'); add_tooltip(dir_entry, "Customer directory path")
        btn_frame = ttk.Frame(dir_frame); btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        select_btn = ttk.Button(btn_frame, text="Select Existing", command=self.parent.select_directory)
        select_btn.pack(side='left', padx=5); add_tooltip(select_btn, "Select existing directory")
        create_btn = ttk.Button(btn_frame, text="Create New", command=self.parent.create_directory)
        create_btn.pack(side='left', padx=5); add_tooltip(create_btn, "Create new directory")

    def setup_manage_customers_tab(self):
        """Setup the Manage Customers tab"""
        search_frame = ttk.Frame(self.parent.manage_customers_tab); search_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(search_frame, text="Search in:").pack(side='left', padx=5)
        search_field = ttk.Combobox(search_frame, textvariable=self.parent.search_field_var, width=10, state='readonly')
        search_field['values'] = ('all', 'name', 'email', 'phone'); search_field.pack(side='left', padx=5)
        add_tooltip(search_field, "Select field to search")
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.parent.search_var, width=30)
        search_entry.pack(side='left', padx=5); add_tooltip(search_entry, "Search customers (Ctrl+F)")
        clear_btn = ttk.Button(search_frame, text="Clear", command=self.parent.event_handler.clear_search)
        clear_btn.pack(side='left', padx=5); add_tooltip(clear_btn, "Clear search")
        self._setup_manage_customers_treeview()
        self._setup_manage_customers_buttons_frame()

    def _setup_manage_customers_treeview(self):
        """Setup the treeview for the Manage Customers tab"""
        tree_frame = ttk.Frame(self.parent.manage_customers_tab); tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        tree_scroll = ttk.Scrollbar(tree_frame); tree_scroll.pack(side='right', fill='y')
        self.parent.customer_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode='extended')
        self.parent.customer_tree.pack(fill='both', expand=True)
        tree_scroll.config(command=self.parent.customer_tree.yview)
        self._setup_treeview(self.parent.customer_tree, ('id', 'name', 'email', 'phone', 'directory', 'created'), 'id')

    def _setup_manage_customers_buttons_frame(self):
        """Setup the buttons frame for the Manage Customers tab"""
        btn_frame = ttk.Frame(self.parent.manage_customers_tab); btn_frame.pack(fill='x', padx=10, pady=10)
        action_frame = ttk.LabelFrame(btn_frame, text="Customer Actions"); action_frame.pack(side='left', padx=5, pady=5)
        open_btn = ttk.Button(action_frame, text="Open Directory", command=self.parent.open_customer_directory)
        open_btn.pack(side='left', padx=5, pady=5); add_tooltip(open_btn, "Open directory")
        rename_btn = ttk.Button(action_frame, text="Rename", command=self.parent.customer_ops.show_rename_dialog)
        rename_btn.pack(side='left', padx=5, pady=5); add_tooltip(rename_btn, "Rename customer")
        edit_btn = ttk.Button(action_frame, text="Edit Selected", command=self.parent.batch_update_customers)
        edit_btn.pack(side='left', padx=5, pady=5); add_tooltip(edit_btn, "Edit selected")
        delete_btn = ttk.Button(action_frame, text="Delete Selected", command=self.parent.delete_selected_customers)
        delete_btn.pack(side='left', padx=5, pady=5); add_tooltip(delete_btn, "Delete selected (Ctrl+D)")
        case_btn = ttk.Button(btn_frame, text="Create Case Folder", command=self.parent.event_handler.switch_to_case_folder_tab)
        case_btn.pack(side='right', padx=5); add_tooltip(case_btn, "Switch to case folder tab")
        export_frame = ttk.Frame(btn_frame); export_frame.pack(side='left', padx=5)
        import_frame = ttk.LabelFrame(export_frame, text="Import"); import_frame.pack(side='left', padx=5, pady=5)
        bulk_import_btn = ttk.Button(import_frame, text="Bulk Import", command=lambda: self.parent.bulk_ops.import_from_directory(selective=False))
        bulk_import_btn.pack(side='top', padx=5, pady=2, fill='x'); add_tooltip(bulk_import_btn, "Import all")
        selective_import_btn = ttk.Button(import_frame, text="Selective Import", command=lambda: self.parent.bulk_ops.import_from_directory(selective=True))
        selective_import_btn.pack(side='top', padx=5, pady=2, fill='x'); add_tooltip(selective_import_btn, "Select directories to import")
        export_group = ttk.LabelFrame(export_frame, text="Export"); export_group.pack(side='left', padx=5, pady=5)
        csv_btn = ttk.Button(export_group, text="CSV", command=lambda: self.parent.export_customers("csv"))
        csv_btn.pack(side='top', padx=5, pady=2, fill='x'); add_tooltip(csv_btn, "Export to CSV (Ctrl+E)")
        json_btn = ttk.Button(export_group, text="JSON", command=lambda: self.parent.export_customers("json"))
        json_btn.pack(side='top', padx=5, pady=2, fill='x'); add_tooltip(json_btn, "Export to JSON")

    def setup_case_folder_tab(self):
        """Setup the Case Folder tab"""
        top_frame = ttk.Frame(self.parent.case_folder_tab); top_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(top_frame, text="Select Customer:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.parent.customer_dropdown = ttk.Combobox(top_frame, textvariable=self.parent.selected_customer_var, width=40, state='readonly')
        self.parent.customer_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w'); add_tooltip(self.parent.customer_dropdown, "Select customer")
        self.parent.update_customer_dropdown()
        case_frame = ttk.LabelFrame(self.parent.case_folder_tab, text="Case Information"); case_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(case_frame, text="Case Number:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        case_num_entry = ttk.Entry(case_frame, textvariable=self.parent.case_number_var, width=20)
        case_num_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w'); add_tooltip(case_num_entry, "Case number (must start with MS)")
        self.parent.case_number_var.trace_add("write", self.parent.event_handler.validate_case_number)
        ms_btn = ttk.Button(case_frame, text="Add MS Prefix", command=self.parent.event_handler.add_ms_prefix)
        ms_btn.grid(row=0, column=2, padx=5, pady=5, sticky='w'); add_tooltip(ms_btn, "Add MS prefix")
        ttk.Label(case_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        description_entry = ttk.Entry(case_frame, textvariable=self.parent.case_description_var, width=40)
        description_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='w'); add_tooltip(description_entry, "Brief description")
        template_frame = ttk.LabelFrame(self.parent.case_folder_tab, text="Folder Template"); template_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(template_frame, text="Select Template:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.parent.template_dropdown = ttk.Combobox(template_frame, textvariable=self.parent.selected_template_var, width=30, state='readonly')
        self.parent.template_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w'); add_tooltip(self.parent.template_dropdown, "Select template")
        self.parent.template_dropdown.bind("<<ComboboxSelected>>", self.parent.event_handler.on_template_selected)
        self.parent.dropdown_manager.update_template_dropdown()
        description_label = ttk.Label(template_frame, textvariable=self.parent.template_desc_var, wraplength=400)
        description_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='w')
        create_btn = ttk.Button(self.parent.case_folder_tab, text="Create Case Folder", command=self.parent.create_case_folder)
        create_btn.pack(padx=10, pady=20); add_tooltip(create_btn, "Create case folder")
        self._setup_case_folder_existing_folders_section()

    def _setup_case_folder_existing_folders_section(self):
        """Setup the existing case folders section in the Case Folder tab"""
        folder_frame = ttk.LabelFrame(self.parent.case_folder_tab, text="Existing Case Folders")
        folder_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self._setup_case_folder_filter_frame(folder_frame)
        self._setup_case_folder_treeview(folder_frame)
        self._setup_case_folder_buttons_frame(folder_frame)

    def _setup_case_folder_filter_frame(self, parent_frame):
        """Setup the filter frame for case folders"""
        filter_frame = ttk.Frame(parent_frame); filter_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(filter_frame, text="Filter by:").pack(side='left', padx=5)
        case_filter_field = ttk.Combobox(filter_frame, textvariable=self.parent.case_filter_field_var, width=10, state='readonly')
        case_filter_field['values'] = ('all', 'case', 'description'); case_filter_field.pack(side='left', padx=5)
        add_tooltip(case_filter_field, "Select field to filter")
        ttk.Label(filter_frame, text="Filter:").pack(side='left', padx=5)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.parent.case_filter_var, width=30)
        filter_entry.pack(side='left', padx=5); add_tooltip(filter_entry, "Filter text")
        refresh_btn = ttk.Button(filter_frame, text="Refresh", command=self.parent.refresh_case_list)
        refresh_btn.pack(side='right', padx=5); add_tooltip(refresh_btn, "Refresh list")

    def _setup_case_folder_treeview(self, parent_frame):
        """Setup the treeview for case folders"""
        case_tree_frame = ttk.Frame(parent_frame); case_tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        case_scroll = ttk.Scrollbar(case_tree_frame); case_scroll.pack(side='right', fill='y')
        self.parent.case_tree = ttk.Treeview(case_tree_frame, yscrollcommand=case_scroll.set, selectmode='browse')
        self.parent.case_tree.pack(fill='both', expand=True)
        case_scroll.config(command=self.parent.case_tree.yview)
        self._setup_treeview(self.parent.case_tree, ('path', 'case', 'description', 'created'), 'path')

    def _setup_case_folder_buttons_frame(self, parent_frame):
        """Setup the buttons frame for case folders"""
        case_buttons_frame = ttk.Frame(parent_frame); case_buttons_frame.pack(fill='x', padx=5, pady=5)
        open_btn = ttk.Button(case_buttons_frame, text="Open Selected", command=self.parent.event_handler.open_selected_case_folder_from_context)
        open_btn.pack(side='left', padx=5); add_tooltip(open_btn, "Open selected case folder")
        move_btn = ttk.Button(case_buttons_frame, text="Move Selected", command=self.parent.move_case_folder)
        move_btn.pack(side='left', padx=5); add_tooltip(move_btn, "Move selected case folder")

    def _setup_treeview(self, treeview, columns, hidden_column):
        """Generic setup for a treeview (columns, headings, sorting)."""
        treeview['columns'] = columns
        treeview.column('#0', width=0, stretch=tk.NO)
        treeview.heading('#0', text='', anchor=tk.W)
        col_widths = {'id': 0, 'path': 0, 'name': 150, 'email': 150, 'phone': 100, 'directory': 200, 'created': 100, 'case': 150, 'description': 200, 'label': 120, 'type': 80, 'entity': 80}
        for col in columns:
            is_hidden = (col == hidden_column)
            width = 0 if is_hidden else col_widths.get(col, 120)
            stretch = tk.NO if is_hidden else tk.YES
            anchor = tk.W
            treeview.column(col, width=width, stretch=stretch, anchor=anchor)
            heading_text = col.replace('_', ' ').title() if not is_hidden else 'ID'
            treeview.heading(col, text=heading_text, anchor=anchor)
            if not is_hidden:
                 sort_command = None
                 if treeview == self.parent.customer_tree: sort_command = lambda _col=col: self.parent.treeview_manager.sort_customer_treeview(_col)
                 elif treeview == self.parent.case_tree: sort_command = lambda _col=col: self.parent.treeview_manager.sort_case_treeview(_col)
                 # Add elif for template_tree and custom_field_tree if sorting needed
                 if sort_command: treeview.heading(col, command=sort_command)

    # --- Template Management Tab Setup ---
    def setup_manage_templates_tab(self):
        """Setup the Manage Templates tab."""
        main_frame = ttk.Frame(self.parent.manage_templates_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        list_frame = ttk.LabelFrame(main_frame, text="Templates")
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        self._setup_template_treeview(list_frame)
        form_button_frame = ttk.Frame(main_frame)
        form_button_frame.pack(side='left', fill='y', padx=(5, 0))
        form_frame = ttk.LabelFrame(form_button_frame, text="Template Details")
        form_frame.pack(fill='x', pady=(0, 10))
        self._setup_template_form(form_frame)
        button_frame = ttk.Frame(form_button_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        self._setup_template_buttons(button_frame)
        # --- Custom Field Definitions Section ---
        custom_fields_frame = ttk.LabelFrame(main_frame, text="Custom Field Definitions")
        custom_fields_frame.pack(side='bottom', fill='x', expand=False, padx=(0, 5), pady=(10, 0))
        self._setup_custom_fields_definition_ui(custom_fields_frame)

    def _setup_template_treeview(self, parent_frame):
        """Setup the treeview for templates."""
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        tree_scroll = ttk.Scrollbar(tree_frame); tree_scroll.pack(side='right', fill='y')
        template_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode='browse')
        template_tree.pack(fill='both', expand=True)
        tree_scroll.config(command=template_tree.yview)
        self.parent.template_tree = template_tree
        self._setup_treeview(self.parent.template_tree, ('id', 'name', 'description'), 'id')
        self.parent.template_tree.bind('<<TreeviewSelect>>', self.parent.event_handler.on_template_tree_selected)

    def _setup_template_form(self, parent_frame):
        """Setup the form fields for adding/editing templates."""
        ttk.Label(parent_frame, text="ID:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        template_id_entry = ttk.Entry(parent_frame, textvariable=self.parent.template_form_id_var, width=35)
        template_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(template_id_entry, "Unique ID (no spaces/special chars). Cannot change after creation.")
        self.parent.template_id_entry = template_id_entry
        ttk.Label(parent_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        name_entry = ttk.Entry(parent_frame, textvariable=self.parent.template_form_name_var, width=35)
        name_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(name_entry, "Display name for the template.")
        ttk.Label(parent_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        desc_entry = ttk.Entry(parent_frame, textvariable=self.parent.template_form_desc_var, width=35)
        desc_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(desc_entry, "Brief description of the template's purpose.")
        ttk.Label(parent_frame, text="Folders:").grid(row=3, column=0, padx=5, pady=5, sticky='nw')
        template_folders_text = tk.Text(parent_frame, width=35, height=4)
        template_folders_text.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(template_folders_text, "Comma-separated list of folder names (e.g., Documents,Images,Notes).")
        self.parent.template_form_folders_text = template_folders_text

    def _setup_template_buttons(self, parent_frame):
        """Setup the Add, Update, Delete, Clear buttons for templates."""
        add_btn = ttk.Button(parent_frame, text="Add New", command=self.parent.event_handler.add_new_template)
        add_btn.grid(row=0, column=0, padx=5, pady=5, sticky='ew'); add_tooltip(add_btn, "Add new template.")
        copy_btn = ttk.Button(parent_frame, text="Copy Selected", command=self.parent.event_handler.copy_selected_template)
        copy_btn.grid(row=1, column=0, padx=5, pady=5, sticky='ew'); add_tooltip(copy_btn, "Copy selected template to form for editing.")
        update_btn = ttk.Button(parent_frame, text="Update Selected", command=self.parent.event_handler.update_selected_template)
        update_btn.grid(row=2, column=0, padx=5, pady=5, sticky='ew'); add_tooltip(update_btn, "Update selected template.")
        delete_btn = ttk.Button(parent_frame, text="Delete Selected", command=self.parent.event_handler.delete_selected_template)
        delete_btn.grid(row=3, column=0, padx=5, pady=5, sticky='ew'); add_tooltip(delete_btn, "Delete selected template.")
        clear_btn = ttk.Button(parent_frame, text="Clear Form", command=self.parent.event_handler.clear_template_form)
        clear_btn.grid(row=4, column=0, padx=5, pady=10, sticky='ew'); add_tooltip(clear_btn, "Clear form fields.")

    # --- Methods for Custom Field Definitions UI --- Correctly indented ---
    def _setup_custom_fields_definition_ui(self, parent_frame):
        """Sets up the UI for defining custom fields."""
        list_frame = ttk.LabelFrame(parent_frame, text="Defined Fields")
        list_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        self._setup_custom_fields_treeview(list_frame)
        form_button_frame = ttk.Frame(parent_frame)
        form_button_frame.pack(side='left', fill='y', padx=5, pady=5)
        form_frame = ttk.LabelFrame(form_button_frame, text="Field Details")
        form_frame.pack(fill='x', pady=(0, 10))
        self._setup_custom_field_form(form_frame)
        button_frame = ttk.Frame(form_button_frame)
        button_frame.pack(fill='x')
        self._setup_custom_field_buttons(button_frame)

    def _setup_custom_fields_treeview(self, parent_frame):
        """Setup the treeview for custom field definitions."""
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        tree_scroll = ttk.Scrollbar(tree_frame); tree_scroll.pack(side='right', fill='y')
        self.parent.custom_field_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode='browse')
        self.parent.custom_field_tree.pack(fill='both', expand=True)
        tree_scroll.config(command=self.parent.custom_field_tree.yview)
        self._setup_treeview(self.parent.custom_field_tree, ('id', 'name', 'label', 'type', 'entity'), 'id')
        self.parent.custom_field_tree.bind('<<TreeviewSelect>>', self.parent.event_handler.on_custom_field_tree_selected)

    def _setup_custom_field_form(self, parent_frame):
        """Setup the form for adding/editing custom field definitions."""
        ttk.Label(parent_frame, text="Field Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.parent.cf_name_entry = ttk.Entry(parent_frame, textvariable=self.parent.cf_form_name_var, width=30)
        self.parent.cf_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(self.parent.cf_name_entry, "Internal unique name (e.g., 'account_number', no spaces). Cannot change after creation.")
        ttk.Label(parent_frame, text="Display Label:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        cf_label_entry = ttk.Entry(parent_frame, textvariable=self.parent.cf_form_label_var, width=30)
        cf_label_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(cf_label_entry, "Label shown in the UI for this field.")
        ttk.Label(parent_frame, text="Field Type:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        cf_type_combo = ttk.Combobox(parent_frame, textvariable=self.parent.cf_form_type_var, width=28, state='readonly')
        cf_type_combo['values'] = ('TEXT', 'NUMBER', 'DATE', 'BOOLEAN')
        cf_type_combo.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(cf_type_combo, "Data type for the custom field.")
        ttk.Label(parent_frame, text="Applies To:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        cf_entity_combo = ttk.Combobox(parent_frame, textvariable=self.parent.cf_form_entity_var, width=28, state='readonly')
        cf_entity_combo['values'] = ('CUSTOMER', 'CASE')
        cf_entity_combo.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        add_tooltip(cf_entity_combo, "Where this custom field will appear (Customer or Case).")

    def _setup_custom_field_buttons(self, parent_frame):
        """Setup buttons for managing custom field definitions."""
        add_btn = ttk.Button(parent_frame, text="Add Field", command=self.parent.event_handler.add_new_custom_field)
        add_btn.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        add_tooltip(add_btn, "Add new field definition.")
        
        update_btn = ttk.Button(parent_frame, text="Update Field", command=self.parent.event_handler.update_selected_custom_field)
        update_btn.grid(row=1, column=0, padx=5, pady=5, sticky='ew')
        add_tooltip(update_btn, "Update selected field definition.")
        
        delete_btn = ttk.Button(parent_frame, text="Delete Field", command=self.parent.event_handler.delete_selected_custom_field)
        delete_btn.grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        add_tooltip(delete_btn, "Delete selected field definition.")
        
        clear_btn = ttk.Button(parent_frame, text="Clear Form", command=self.parent.event_handler.clear_custom_field_form)
        clear_btn.grid(row=3, column=0, padx=5, pady=10, sticky='ew')
        add_tooltip(clear_btn, "Clear field definition form.")

    def _setup_style(self):
        """Configure the ttk style"""
        style = ttk.Style()
        # Try setting the theme. 'clam' often allows more customization.
        try:
            style.theme_use('clam')
        except tk.TclError:
            logging.warning("Clam theme not available, using default.")
            # Fallback to default if clam is not available

        style.configure('TNotebook.Tab', padding=[10, 5])

        # Custom style for the shutdown button
        style.configure("Shutdown.TButton",
                        foreground='white',
                        background='red',
                        bordercolor='darkred',
                        relief='raised',
                        padding=[5, 5]) # Add padding for a slightly larger look
        style.map("Shutdown.TButton",
                  background=[('active', '#FF4444')], # Lighter red when active/hovered
                  relief=[('pressed', 'sunken')])

    def _setup_shutdown_button(self):
        """Add a shutdown button, potentially near the status bar or in a menu."""
        # Placing it in a frame above the status bar
        bottom_frame = ttk.Frame(self.parent.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

        # Use a power symbol (e.g., U+23FB) and apply the custom style
        shutdown_btn = ttk.Button(bottom_frame,
                                  text="⏻", # Unicode Power Symbol
                                  command=self.parent.safe_shutdown,
                                  style="Shutdown.TButton",
                                  width=2) # Limit width to make it more square/round
        shutdown_btn.pack(side=tk.RIGHT) # Place it on the right
        add_tooltip(shutdown_btn, "Closes the database connection and exits the application safely.")
