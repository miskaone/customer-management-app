import tkinter as tk
from tkinter import ttk

from ui_components import add_tooltip

def setup_add_customer_tab(parent):
    """Setup the Add Customer tab"""
    _setup_add_customer_info_frame(parent)
    _setup_add_customer_directory_section(parent)

    # Save button
    save_frame = ttk.Frame(parent.add_customer_tab)
    save_frame.pack(fill='x', padx=10, pady=20)
    save_btn = ttk.Button(save_frame, text="Save Customer", command=parent.save_customer)
    save_btn.pack(side='right')
    add_tooltip(save_btn, "Save the customer information")

def _setup_add_customer_info_frame(parent):
    """Setup the customer information frame in Add Customer tab"""
    info_frame = ttk.LabelFrame(parent.add_customer_tab, text="Customer Information")
    info_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Customer Name
    ttk.Label(info_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
    parent.name_var = tk.StringVar()
    name_entry = ttk.Entry(info_frame, textvariable=parent.name_var, width=40)
    name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    add_tooltip(name_entry, "Customer's full name or company name")
    
    # Email
    ttk.Label(info_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
    parent.email_var = tk.StringVar()
    email_entry = ttk.Entry(info_frame, textvariable=parent.email_var, width=40)
    email_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
    add_tooltip(email_entry, "Customer's email address")
    
    # Phone
    ttk.Label(info_frame, text="Phone:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
    parent.phone_var = tk.StringVar()
    phone_entry = ttk.Entry(info_frame, textvariable=parent.phone_var, width=40)
    phone_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
    add_tooltip(phone_entry, "Customer's phone number")
    
    # Address
    ttk.Label(info_frame, text="Address:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
    parent.address_var = tk.StringVar()
    address_entry = ttk.Entry(info_frame, textvariable=parent.address_var, width=40)
    address_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
    add_tooltip(address_entry, "Customer's physical address")
    
    # Notes
    ttk.Label(info_frame, text="Notes:").grid(row=4, column=0, padx=5, pady=5, sticky='nw')
    parent.notes_text = tk.Text(info_frame, width=40, height=5)
    parent.notes_text.grid(row=4, column=1, padx=5, pady=5, sticky='w')
    add_tooltip(parent.notes_text, "Additional notes about the customer")

def _setup_add_customer_directory_section(parent):
    """Setup the directory section in the Add Customer tab"""
    dir_frame = ttk.LabelFrame(parent.add_customer_tab, text="Customer Directory")
    dir_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Directory path
    ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
    parent.dir_var = tk.StringVar()
    dir_entry = ttk.Entry(dir_frame, textvariable=parent.dir_var, width=40)
    dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    add_tooltip(dir_entry, "Path to the customer's directory for storing case folders")
    
    # Directory buttons
    btn_frame = ttk.Frame(dir_frame)
    btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
    
    select_btn = ttk.Button(btn_frame, text="Select Existing", command=parent.select_directory)
    select_btn.pack(side='left', padx=5)
    add_tooltip(select_btn, "Select an existing directory")
    
    create_btn = ttk.Button(btn_frame, text="Create New", command=parent.create_directory)
    create_btn.pack(side='left', padx=5)
    add_tooltip(create_btn, "Create a new directory for this customer")
