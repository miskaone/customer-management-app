import tkinter as tk
from tkinter import messagebox
import os
from datetime import datetime

class EventHandlers:
    """Handles various UI event handling for the Customer Manager application"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def on_search_changed(self, *args):
        """Filter customers based on search text"""
        search_text = self.parent.search_var.get().lower()
        search_field = self.parent.search_field_var.get()
        
        # Clear the treeview
        for item in self.parent.customer_tree.get_children():
            self.parent.customer_tree.delete(item)
        
        # If no search text, show all customers
        if not search_text:
            for customer in self.parent.all_customers:
                self.add_customer_to_tree(customer)
            return
        
        # Filter customers based on search field
        for customer in self.parent.all_customers:
            if search_field == 'all':
                # Search in all fields
                combined = f"{customer.get('name', '')} {customer.get('email', '')} {customer.get('phone', '')}".lower()
                if search_text in combined:
                    self.add_customer_to_tree(customer)
            elif search_field == 'name' and search_text in customer.get('name', '').lower():
                self.add_customer_to_tree(customer)
            elif search_field == 'email' and search_text in customer.get('email', '').lower():
                self.add_customer_to_tree(customer)
            elif search_field == 'phone' and search_text in customer.get('phone', '').lower():
                self.add_customer_to_tree(customer)
    
    def add_customer_to_tree(self, customer):
        """Add a customer to the treeview"""
        # Format timestamp for display
        created_at = customer.get('created_at', '')
        if created_at:
            try:
                # Convert ISO format to datetime and then to display format
                dt = datetime.fromisoformat(created_at)
                created_at = dt.strftime('%Y-%m-%d')
            except ValueError:
                # If conversion fails, use the original string
                pass
        
        # Insert into treeview
        self.parent.customer_tree.insert(
            '', 'end', 
            values=(
                customer.get('id', ''),
                customer.get('name', ''),
                customer.get('email', ''),
                customer.get('phone', ''),
                customer.get('directory', ''),
                created_at
            )
        )
    
    def on_case_filter_changed(self, *args):
        """Filter case folders based on filter text"""
        self.parent.refresh_case_list()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the application"""
        # Global shortcuts
        self.parent.root.bind('<Control-s>', lambda e: self.parent.save_customers())
        self.parent.root.bind('<Control-f>', lambda e: self.parent.focus_search())
        self.parent.root.bind('<F5>', lambda e: self.parent.refresh_customer_list())
        
        # Tab shortcuts
        self.parent.root.bind('<Control-Key-1>', lambda e: self.parent.notebook.select(self.parent.add_customer_tab))
        self.parent.root.bind('<Control-Key-2>', lambda e: self.parent.notebook.select(self.parent.manage_customers_tab))
        self.parent.root.bind('<Control-Key-3>', lambda e: self.parent.notebook.select(self.parent.case_folder_tab))
        
        # Export shortcut
        self.parent.root.bind('<Control-e>', lambda e: self.parent.export_customers("csv"))
        
        # Delete shortcut
        self.parent.root.bind('<Control-d>', lambda e: self.parent.delete_selected_customers())
    
    def focus_search(self):
        """Set focus to the search entry"""
        # First select the manage customers tab
        self.parent.notebook.select(self.parent.manage_customers_tab)
        
        # Then iterate through all children to find the Entry widget for search
        for child in self.parent.manage_customers_tab.winfo_children():
            if isinstance(child, tk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.Entry) and grandchild.cget('textvariable') == str(self.parent.search_var):
                        grandchild.focus_set()
                        return
    
    def clear_search(self):
        """Clear the search field and refresh the list"""
        self.parent.search_var.set('')
        self.parent.refresh_customer_list()
    
    def sort_treeview(self, column):
        """Sort treeview by the given column"""
        # Get all items from treeview
        item_list = [(self.parent.customer_tree.set(k, column), k) for k in self.parent.customer_tree.get_children('')]
        
        # Sort the list
        item_list.sort(reverse=self.parent.customer_tree.heading(column, 'text').startswith('▼'))
        
        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(item_list):
            self.parent.customer_tree.move(k, '', index)
        
        # Update the headings to indicate sort direction
        for col in self.parent.customer_tree['columns']:
            if col != 'id':  # Skip the ID column
                if col == column:
                    # Toggle sort direction indicator
                    if self.parent.customer_tree.heading(col, 'text').startswith('▼'):
                        self.parent.customer_tree.heading(col, text=f'▲ {col.title()}')
                    else:
                        self.parent.customer_tree.heading(col, text=f'▼ {col.title()}')
                else:
                    # Remove sort indicator from other columns
                    self.parent.customer_tree.heading(col, text=col.title())
    
    def validate_case_number(self, *args):
        """Validate that case numbers start with MS"""
        case_num = self.parent.case_number_var.get()
        if case_num and not case_num.startswith("MS"):
            self.parent.status_var.set("Case numbers should start with MS")
        else:
            self.parent.status_var.set("")
    
    def add_ms_prefix(self):
        """Add MS prefix to case number if missing"""
        case_num = self.parent.case_number_var.get()
        if case_num and not case_num.startswith("MS"):
            self.parent.case_number_var.set(f"MS{case_num}")
            self.parent.status_var.set("")
    
    def on_template_selected(self, event):
        """Update template description when a template is selected"""
        template = self.parent.dropdown_manager.get_selected_template()
        if template:
            self.parent.template_desc_var.set(template.get("description", ""))
        else:
            self.parent.template_desc_var.set("")
    
    def get_selected_template(self):
        """Get the currently selected template"""
        template_name = self.parent.selected_template_var.get()
        for template in self.parent.templates:
            if template.get("name") == template_name:
                return template
        return None
    
    def switch_to_case_folder_tab(self):
        """Switch to the Case Folder tab and set customer if selected"""
        # Get selected customer from treeview
        selected_items = self.parent.customer_tree.selection()
        if selected_items:
            item = selected_items[0]
            customer_id = self.parent.customer_tree.item(item, "values")[0]
            customer_name = self.parent.customer_tree.item(item, "values")[1]
            
            # Update dropdown selection
            self.parent.selected_customer_var.set(customer_name)
            
            # Switch to case folder tab
            self.parent.notebook.select(self.parent.case_folder_tab)
        else:
            # If no customer selected, just switch to tab
            self.parent.notebook.select(self.parent.case_folder_tab)

    def setup_customer_tree_context_menu(self):
        """Setup context menu for customer treeview"""
        # Create context menu
        self.context_menu = tk.Menu(self.parent.root, tearoff=0)
        self.context_menu.add_command(label="Open Directory", command=self.parent.open_customer_directory)
        self.context_menu.add_command(label="Rename", command=self.parent.customer_ops.show_rename_dialog)
        self.context_menu.add_command(label="Edit", command=self.parent.batch_update_customers)
        self.context_menu.add_command(label="Delete", command=self.parent.delete_selected_customers)
        
        # Bind right click to show context menu
        self.parent.customer_tree.bind("<Button-3>", self.show_customer_context_menu)
    
    def show_customer_context_menu(self, event):
        """Show context menu for customer treeview"""
        # Select row under cursor
        iid = self.parent.customer_tree.identify_row(event.y)
        if iid:
            # If the row wasn't already selected, select only this row
            if not self.parent.customer_tree.selection() or iid not in self.parent.customer_tree.selection():
                self.parent.customer_tree.selection_set(iid)
            
            # Display the context menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def setup_case_tree_context_menu(self):
        """Setup context menu for case folder treeview"""
        # Create context menu
        self.case_context_menu = tk.Menu(self.parent.root, tearoff=0)
        self.case_context_menu.add_command(label="Open Case Folder", 
                                          command=lambda: self.parent.case_ops.open_case_folder(
                                              self.parent.selected_customer_var.get(),
                                              self.parent.selected_case_var.get()
                                          ))
        self.case_context_menu.add_command(label="Move Case Folder", command=self.parent.move_case_folder)
        
        # Bind right click to show context menu
        self.parent.case_tree.bind("<Button-3>", self.show_case_context_menu)
    
    def show_case_context_menu(self, event):
        """Show context menu for case folder treeview"""
        # Select row under cursor
        iid = self.parent.case_tree.identify_row(event.y)
        if iid:
            # If the row wasn't already selected, select only this row
            if not self.parent.case_tree.selection() or iid not in self.parent.case_tree.selection():
                self.parent.case_tree.selection_set(iid)
                
            # Update selected case variable
            case_folder_name = self.parent.case_tree.item(iid, "values")[1]
            self.parent.selected_case_var.set(case_folder_name)
            
            # Display the context menu
            try:
                self.case_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.case_context_menu.grab_release()
    
    def on_customer_selected(self, event):
        """Handle customer selection in the treeview"""
        selected_items = self.parent.customer_tree.selection()
        if selected_items:
            # Get customer ID from the selected item
            customer_id = self.parent.customer_tree.item(selected_items[0], "values")[0]
            customer_name = self.parent.customer_tree.item(selected_items[0], "values")[1]
            
            # Set status message
            self.parent.status_var.set(f"Selected customer: {customer_name}")
    
    def on_case_selected(self, event):
        """Handle case folder selection in the treeview"""
        selected_items = self.parent.case_tree.selection()
        if selected_items:
            # Get case folder name from the selected item (now in the second column, index 1)
            case_folder_name = self.parent.case_tree.item(selected_items[0], "values")[1]
            
            # Set selected case variable
            self.parent.selected_case_var.set(case_folder_name)
            
            # Set status message
            self.parent.status_var.set(f"Selected case folder: {case_folder_name}")
    
    def on_customer_dropdown_selected(self, event):
        """Handle customer selection in the dropdown"""
        customer_name = self.parent.selected_customer_var.get()
        customer_id = None
        
        # Find customer ID from name
        for customer in self.parent.customers:
            if customer.get("name") == customer_name:
                customer_id = customer.get("id")
                break
        
        if customer_id:
            # Set customer ID variable (keeping the name in the dropdown)
            self.parent.selected_customer_id_var.set(customer_id)
            
            # Refresh case list for this customer
            self.parent.refresh_case_list()
            
            # Set status message
            self.parent.status_var.set(f"Loaded case folders for customer: {customer_name}")
    
    def setup_events(self):
        """Setup all event bindings"""
        # Case filter
        self.parent.case_filter_var.trace_add("write", self.on_case_filter_changed)
        
        # Customer search
        self.parent.search_var.trace_add("write", self.on_search_changed)
        
        # Treeview selections
        self.parent.customer_tree.bind('<<TreeviewSelect>>', self.on_customer_selected)
        self.parent.case_tree.bind('<<TreeviewSelect>>', self.on_case_selected)
        
        # Customer dropdown selection
        self.parent.customer_dropdown.bind("<<ComboboxSelected>>", self.on_customer_dropdown_selected)
        
        # Case number validation
        self.parent.case_number_var.trace_add("write", self.validate_case_number)
        
        # Template selection events
        if self.parent.template_dropdown:
            self.parent.template_dropdown.bind('<<ComboboxSelected>>', self.on_template_selected)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Setup context menus
        self.setup_customer_tree_context_menu()
        self.setup_case_tree_context_menu()
