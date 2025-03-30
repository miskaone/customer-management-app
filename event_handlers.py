import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
import uuid # Needed for generating template IDs
import json # Needed for parsing/dumping folders list
from datetime import datetime

# Import custom exceptions (assuming defined in customer_operations or a shared file)
try:
    from customer_operations import ValidationError, DatabaseError, FilesystemError
except ImportError:
    # Define locally if not found (less ideal)
    class CustomerOpsError(Exception): pass
    class ValidationError(CustomerOpsError): pass
    class DatabaseError(CustomerOpsError): pass
    class FilesystemError(CustomerOpsError): pass


class EventHandlers:
    """Handles various UI event handling for the Customer Manager application"""

    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
        self.context_menu = None
        self.case_context_menu = None

    # --- Customer Search and Tree ---
    def on_search_changed(self, *args):
        """Filter customers based on search text (multiple terms allowed) and populate the treeview."""
        search_input = self.parent.search_var.get().lower()
        search_terms = search_input.split() # Split by space for multiple terms
        search_field = self.parent.search_field_var.get()
        logging.debug(f"Search changed: input='{search_input}', terms={search_terms}, field='{search_field}'")

        for item in self.parent.customer_tree.get_children():
            self.parent.customer_tree.delete(item)

        count = 0
        customers_to_display = []
        if not search_terms: # If no search terms, display all
            customers_to_display = self.parent.customers
        else:
            for customer in self.parent.customers:
                 if not isinstance(customer, dict): continue
                 
                 # Check if ALL search terms are present in the selected field(s)
                 match_all_terms = True
                 for term in search_terms:
                     term_found = False
                     if search_field == 'all':
                         # Search in name, email, phone, address, notes
                         combined = f"{customer.get('name', '')} {customer.get('email', '')} {customer.get('phone', '')} {customer.get('address', '')} {customer.get('notes', '')}".lower()
                         if term in combined:
                             term_found = True
                     elif search_field == 'name' and term in customer.get('name', '').lower():
                         term_found = True
                     elif search_field == 'email' and term in customer.get('email', '').lower():
                         term_found = True
                     elif search_field == 'phone' and term in customer.get('phone', '').lower():
                         term_found = True
                     # Add elif for address, notes if specific field search is desired
                     
                     if not term_found:
                         match_all_terms = False
                         break # No need to check other terms for this customer

                 if match_all_terms:
                     customers_to_display.append(customer)

        # Populate the treeview with filtered results
        for customer in customers_to_display:
            self.add_customer_to_tree(customer)
            count += 1
            
        logging.debug(f"Populated customer treeview with {count} items after search.")
        status_msg = f"Showing {count} of {len(self.parent.customers)} customers."
        if search_terms: status_msg = f"Found {count} customers matching '{search_input}'."
        self.parent.status_var.set(status_msg)


    def add_customer_to_tree(self, customer):
        """Add a customer dictionary (from DB) to the treeview."""
        if not isinstance(customer, dict) or 'id' not in customer:
             logging.warning(f"add_customer_to_tree called with invalid data: {customer}")
             return

        created_at = customer.get('created_at', '')
        created_display = ''
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at)
                created_display = dt.strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError): created_display = str(created_at)

        try:
            self.parent.customer_tree.insert(
                '', 'end', iid=customer.get('id'),
                values=(
                    customer.get('id', ''), customer.get('name', ''), customer.get('email', ''),
                    customer.get('phone', ''), customer.get('directory', ''), created_display
                )
            )
        except tk.TclError as e: logging.error(f"Failed to insert customer {customer.get('id')} into tree: {e}")

    # --- Case Folder Filtering and Tree ---
    def on_case_filter_changed(self, *args):
        """Filter case folders based on filter text by refreshing the list."""
        self.parent.refresh_case_list()

    # --- Template Management ---
    def refresh_template_list(self):
        """Reload templates from DB and refresh the template treeview."""
        logging.info("Refreshing template list...")
        try:
            self.parent.templates = self.parent.data_manager.load_templates()
            for item in self.parent.template_tree.get_children():
                self.parent.template_tree.delete(item)
            count = 0
            for template in self.parent.templates:
                 if isinstance(template, dict):
                     self.parent.template_tree.insert(
                         '', 'end', iid=template.get('id'),
                         values=(template.get('id', ''), template.get('name', ''), template.get('description', ''))
                     )
                     count += 1
            logging.info(f"Template list refresh complete. Loaded {count} templates.")
            self.parent.dropdown_manager.update_template_dropdown()
        except Exception as e:
             logging.error(f"Failed to refresh template list: {e}", exc_info=True)
             messagebox.showerror("Error", f"Failed to load template data:\n{e}")

    def on_template_tree_selected(self, event=None):
        """Handle template selection in the treeview to populate the form."""
        selected_items = self.parent.template_tree.selection()
        if not selected_items:
            self.clear_template_form(); return
        template_id = selected_items[0]
        selected_template = next((t for t in self.parent.templates if t.get('id') == template_id), None)
        
        if selected_template:
            logging.debug(f"Template selected: {selected_template.get('name')} (ID: {template_id})")
            self.parent.template_form_id_var.set(selected_template.get('id', ''))
            self.parent.template_form_name_var.set(selected_template.get('name', ''))
            self.parent.template_form_desc_var.set(selected_template.get('description', ''))
            folders_list = selected_template.get('folders', [])
            folders_str = ", ".join(folders_list)
            self.parent.template_form_folders_text.delete('1.0', tk.END)
            self.parent.template_form_folders_text.insert('1.0', folders_str)
            self.parent.template_id_entry.config(state='readonly') # Make ID read-only for existing
        else:
            logging.warning(f"Selected template ID {template_id} not found in loaded data.")
            self.clear_template_form()

    def clear_template_form(self):
        """Clear the template editing form."""
        logging.debug("Clearing template form.")
        self.parent.template_form_id_var.set("")
        self.parent.template_form_name_var.set("")
        self.parent.template_form_desc_var.set("")
        self.parent.template_form_folders_text.delete('1.0', tk.END)
        if self.parent.template_id_entry: self.parent.template_id_entry.config(state='normal')
        if self.parent.template_tree:
             selection = self.parent.template_tree.selection()
             if selection: self.parent.template_tree.selection_remove(selection)

    def _get_template_form_data(self):
        """Helper to get data from the template form."""
        template_id = self.parent.template_form_id_var.get().strip()
        name = self.parent.template_form_name_var.get().strip()
        description = self.parent.template_form_desc_var.get().strip()
        folders_str = self.parent.template_form_folders_text.get('1.0', tk.END).strip()
        folders_list = [f.strip() for f in folders_str.split(',') if f.strip()]
        return template_id, name, description, folders_list

    def add_new_template(self):
        """Add a new template based on form data."""
        template_id, name, description, folders_list = self._get_template_form_data()
        if not template_id or not name or ' ' in template_id:
             messagebox.showerror("Error", "Template ID (no spaces) and Name are required.", parent=self.parent.root)
             return
        template_data = {"id": template_id, "name": name, "description": description, "folders": folders_list}
        try:
            if self.parent.data_manager.add_template(template_data):
                 self.parent.data_manager.update_status(f"Template '{name}' added.")
                 self.refresh_template_list()
                 self.clear_template_form()
        except Exception as e:
             logging.error(f"Unexpected error adding template: {e}", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.parent.root)

    def update_selected_template(self):
        """Update the selected template based on form data."""
        selected_items = self.parent.template_tree.selection()
        if not selected_items: messagebox.showerror("Error", "Select a template to update.", parent=self.parent.root); return
        original_template_id = selected_items[0]
        form_id, name, description, folders_list = self._get_template_form_data()
        if original_template_id != form_id: messagebox.showerror("Error", "Template ID cannot be changed.", parent=self.parent.root); return
        if not name: messagebox.showerror("Error", "Template Name is required.", parent=self.parent.root); return
        try:
            if self.parent.data_manager.update_template(original_template_id, name, description, folders_list):
                 self.parent.data_manager.update_status(f"Template '{name}' updated.")
                 self.refresh_template_list()
                 self.clear_template_form()
        except Exception as e:
             logging.error(f"Unexpected error updating template: {e}", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.parent.root)

    def delete_selected_template(self):
        """Delete the template selected in the treeview."""
        selected_items = self.parent.template_tree.selection()
        if not selected_items: messagebox.showerror("Error", "Select a template to delete.", parent=self.parent.root); return
        template_id = selected_items[0]
        template_name = self.parent.template_tree.item(template_id, "values")[1]
        if template_id == "default": messagebox.showwarning("Delete Error", "Cannot delete default template.", parent=self.parent.root); return
        if not messagebox.askyesno("Confirm Delete", f"Delete template '{template_name}' (ID: {template_id})?", parent=self.parent.root): return
        try:
            if self.parent.data_manager.delete_template(template_id):
                 self.parent.data_manager.update_status(f"Template '{template_name}' deleted.")
                 self.refresh_template_list()
                 self.clear_template_form()
        except Exception as e:
             logging.error(f"Unexpected error deleting template: {e}", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.parent.root)

    def copy_selected_template(self):
        """Copies the selected template's data to the form for editing as a new template."""
        selected_item = self.parent.template_tree.selection()
        if not selected_item:
            messagebox.showinfo("No Selection", "Please select a template to copy.")
            return
        item_iid = selected_item[0]
        # Get the ID from the first column ('#1') which holds the actual Template ID
        template_id = self.parent.template_tree.item(item_iid, 'values')[0]

        # Find the template data from the parent's loaded templates
        template_data = next((t for t in self.parent.templates if t.get('id') == template_id), None)

        if not template_data:
            messagebox.showerror("Error", f"Could not find data for selected template ID: {template_id}")
            logging.error(f"Failed to find template data for ID {template_id} during copy operation.")
            return

        # Clear the form first
        self.clear_template_form()

        # Populate form with copied data, modify name, leave ID blank
        self.parent.template_form_id_var.set("") # Clear ID field
        self.parent.template_form_name_var.set(f"{template_data.get('name', '')} (Copy)")
        self.parent.template_form_desc_var.set(template_data.get('description', ''))

        # Join folders back into string format for the Text widget
        folders_list = template_data.get('folders', [])
        folders_str = "\n".join(folders_list)
        self.parent.template_form_folders_text.delete("1.0", tk.END)
        self.parent.template_form_folders_text.insert("1.0", folders_str)

        # Ensure ID entry is enabled and set focus
        self.parent.template_id_entry.config(state='normal')
        self.parent.template_id_entry.focus_set()
        self.parent.data_manager.update_status(f"Copied template '{template_id}'. Enter a new unique ID and save.")
        logging.info(f"Copied template {template_id} data to form for creation of a new template.")

    # --- Custom Field Definition Management ---

    def refresh_custom_field_definitions_list(self):
        """Load custom field definitions and populate the treeview."""
        logging.info("Refreshing custom field definitions list...")
        try:
            definitions = self.parent.data_manager.load_custom_field_definitions()
            
            # Ensure tree exists before clearing/populating
            if not hasattr(self.parent, 'custom_field_tree') or not self.parent.custom_field_tree:
                 logging.warning("Custom field treeview not found during refresh.")
                 return

            for item in self.parent.custom_field_tree.get_children():
                self.parent.custom_field_tree.delete(item)

            count = 0
            for definition in definitions:
                 if isinstance(definition, dict):
                     self.parent.custom_field_tree.insert(
                         '', 'end', iid=definition.get('id'), # Use DB ID as item ID
                         values=(
                             definition.get('id', ''), # Hidden
                             definition.get('name', ''),
                             definition.get('label', ''),
                             definition.get('field_type', ''),
                             definition.get('target_entity', '')
                         )
                     )
                     count += 1
            logging.info(f"Loaded {count} custom field definitions into treeview.")
        except Exception as e:
             logging.error(f"Failed to refresh custom field definitions list: {e}", exc_info=True)
             messagebox.showerror("Error", f"Failed to load custom field definitions:\n{e}")

    def on_custom_field_tree_selected(self, event=None):
        """Handle selection in the custom field definitions treeview."""
        if not hasattr(self.parent, 'custom_field_tree') or not self.parent.custom_field_tree: return
        
        selected_items = self.parent.custom_field_tree.selection()
        if not selected_items:
            self.clear_custom_field_form(); return

        field_def_id = selected_items[0]
        
        # Find the selected definition data
        conn = self.parent.data_manager._get_db_connection()
        selected_definition = None
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM custom_field_definitions WHERE id = ?", (field_def_id,))
                row = cursor.fetchone()
                if row: selected_definition = dict(row)
            except Exception as e: logging.error(f"Error fetching selected custom field definition {field_def_id}: {e}")
            finally: conn.close()

        if selected_definition:
            logging.debug(f"Custom field selected: {selected_definition.get('name')}")
            self.parent.cf_form_name_var.set(selected_definition.get('name', ''))
            self.parent.cf_form_label_var.set(selected_definition.get('label', ''))
            self.parent.cf_form_type_var.set(selected_definition.get('field_type', ''))
            self.parent.cf_form_entity_var.set(selected_definition.get('target_entity', ''))
            if self.parent.cf_name_entry: self.parent.cf_name_entry.config(state='readonly') # Make Name read-only
        else:
            logging.warning(f"Selected custom field definition ID {field_def_id} not found in DB.")
            self.clear_custom_field_form()

    def clear_custom_field_form(self):
        """Clear the custom field definition form."""
        logging.debug("Clearing custom field form.")
        self.parent.cf_form_name_var.set("")
        self.parent.cf_form_label_var.set("")
        self.parent.cf_form_type_var.set("")
        self.parent.cf_form_entity_var.set("")
        if self.parent.cf_name_entry: self.parent.cf_name_entry.config(state='normal')
        if self.parent.custom_field_tree:
             selection = self.parent.custom_field_tree.selection()
             if selection: self.parent.custom_field_tree.selection_remove(selection)

    def _get_custom_field_form_data(self):
        """Helper to get data from the custom field definition form."""
        name = self.parent.cf_form_name_var.get().strip()
        label = self.parent.cf_form_label_var.get().strip()
        field_type = self.parent.cf_form_type_var.get()
        target_entity = self.parent.cf_form_entity_var.get()
        # Basic validation for internal name format (no spaces, etc.)
        if ' ' in name or not name.isidentifier():
             raise ValidationError("Field Name must be a valid identifier (letters, numbers, underscores, no spaces).")
        return name, label, field_type, target_entity

    def add_new_custom_field(self):
        """Add a new custom field definition."""
        try:
            name, label, field_type, target_entity = self._get_custom_field_form_data()
            if not name or not label or not field_type or not target_entity:
                 raise ValidationError("All fields (Name, Label, Type, Applies To) are required.")
            
            if self.parent.data_manager.add_custom_field_definition(name, label, field_type, target_entity):
                 self.parent.data_manager.update_status(f"Custom field '{label}' added.")
                 self.refresh_custom_field_definitions_list()
                 self.clear_custom_field_form()
            # else: add_custom_field_definition shows messagebox on known errors
        except ValidationError as ve:
             messagebox.showerror("Validation Error", str(ve), parent=self.parent.root)
        except Exception as e:
             logging.error(f"Unexpected error adding custom field: {e}", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.parent.root)

    def update_selected_custom_field(self):
        """Update the selected custom field definition."""
        selected_items = self.parent.custom_field_tree.selection()
        if not selected_items: messagebox.showerror("Error", "Select a field to update.", parent=self.parent.root); return
        field_def_id = selected_items[0]

        try:
            form_name, label, field_type, target_entity = self._get_custom_field_form_data()
            original_name = self.parent.custom_field_tree.item(field_def_id, "values")[1]
            if form_name != original_name:
                 raise ValidationError("Field Name (internal key) cannot be changed.")
            if not label or not field_type or not target_entity:
                 raise ValidationError("Label, Type, and Applies To fields are required.")

            if self.parent.data_manager.update_custom_field_definition(field_def_id, label, field_type, target_entity):
                 self.parent.data_manager.update_status(f"Custom field '{label}' updated.")
                 self.refresh_custom_field_definitions_list()
                 self.clear_custom_field_form()
            # else: update method shows messagebox on known errors
        except ValidationError as ve:
             messagebox.showerror("Validation Error", str(ve), parent=self.parent.root)
        except Exception as e:
             logging.error(f"Unexpected error updating custom field: {e}", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.parent.root)

    def delete_selected_custom_field(self):
        """Delete the selected custom field definition."""
        selected_items = self.parent.custom_field_tree.selection()
        if not selected_items: messagebox.showerror("Error", "Select a field to delete.", parent=self.parent.root); return
        field_def_id = selected_items[0]
        field_label = self.parent.custom_field_tree.item(field_def_id, "values")[2]

        if not messagebox.askyesno("Confirm Delete", f"Delete custom field '{field_label}'?\n\nWARNING: This deletes the definition AND all values entered for this field.", parent=self.parent.root):
            return
        try:
            if self.parent.data_manager.delete_custom_field_definition(field_def_id):
                 self.parent.data_manager.update_status(f"Custom field '{field_label}' deleted.")
                 self.refresh_custom_field_definitions_list()
                 self.clear_custom_field_form()
            # else: delete method shows messagebox on known errors
        except Exception as e:
             logging.error(f"Unexpected error deleting custom field: {e}", exc_info=True)
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.parent.root)


    # --- Keyboard Shortcuts ---
    def setup_keyboard_shortcuts(self):
        logging.debug("Setting up keyboard shortcuts.")
        self.parent.root.bind('<Control-f>', lambda e: self.focus_search())
        self.parent.root.bind('<F5>', lambda e: self.parent.refresh_customer_list())
        self.parent.root.bind('<Control-Key-1>', lambda e: self.parent.notebook.select(self.parent.add_customer_tab))
        self.parent.root.bind('<Control-Key-2>', lambda e: self.parent.notebook.select(self.parent.manage_customers_tab))
        self.parent.root.bind('<Control-Key-3>', lambda e: self.parent.notebook.select(self.parent.case_folder_tab))
        self.parent.root.bind('<Control-Key-4>', lambda e: self.parent.notebook.select(self.parent.manage_templates_tab))
        self.parent.root.bind('<Control-e>', lambda e: self.parent.export_customers("csv"))
        self.parent.root.bind('<Control-d>', lambda e: self.parent.delete_selected_customers())

    def focus_search(self):
        logging.debug("Focusing search entry.")
        self.parent.notebook.select(self.parent.manage_customers_tab)
        search_entry = None
        for widget in self.parent.manage_customers_tab.winfo_children():
             if isinstance(widget, (tk.Frame, ttk.Frame, ttk.LabelFrame)):
                 for sub_widget in widget.winfo_children():
                     if isinstance(sub_widget, ttk.Entry) and str(sub_widget.cget('textvariable')) == str(self.parent.search_var):
                         search_entry = sub_widget; break
             if search_entry: break
        if search_entry: search_entry.focus_set(); search_entry.select_range(0, tk.END); logging.debug("Search entry focused.")
        else: logging.warning("Could not find search entry widget to focus.")

    def clear_search(self):
        logging.debug("Clearing search.")
        self.parent.search_var.set('')

    # --- Case Number Validation ---
    def validate_case_number(self, *args):
        case_num = self.parent.case_number_var.get()
        is_valid, msg = self.parent.case_ops.validate_case_number(case_num)
        if not is_valid and case_num: self.parent.status_var.set(msg)
        else:
            current_status = self.parent.status_var.get()
            if msg in current_status: self.parent.status_var.set("")

    def add_ms_prefix(self):
        case_num = self.parent.case_number_var.get()
        updated_num = self.parent.case_ops.add_ms_prefix(case_num)
        if updated_num != case_num:
            self.parent.case_number_var.set(updated_num)
            is_valid, msg = self.parent.case_ops.validate_case_number(updated_num)
            current_status = self.parent.status_var.get()
            if msg in current_status: self.parent.status_var.set("")

    # --- Template Dropdown Selection (Case Folder Tab) ---
    def on_template_selected(self, event):
        template = self.parent.dropdown_manager.get_selected_template()
        self.parent.template_desc_var.set(template.get("description", "") if template else "")

    # --- Tab Switching ---
    def switch_to_case_folder_tab(self):
        logging.debug("Switching to case folder tab.")
        selected_items = self.parent.customer_tree.selection()
        if selected_items:
            customer_id = selected_items[0]
            customer_name = self.parent.customer_tree.item(customer_id, "values")[1]
            self.parent.selected_customer_var.set(customer_name)
            self.parent.selected_customer_id_var.set(customer_id)
            logging.debug(f"Customer selected for case tab: {customer_name} (ID: {customer_id})")
            self.parent.refresh_case_list()
        else:
             logging.debug("No customer selected, clearing case tab selection.")
             self.parent.selected_customer_var.set("")
             self.parent.selected_customer_id_var.set("")
             self.parent.refresh_case_list()
        self.parent.notebook.select(self.parent.case_folder_tab)

    # --- Context Menus ---
    def setup_customer_tree_context_menu(self):
        logging.debug("Setting up customer context menu.")
        self.context_menu = tk.Menu(self.parent.root, tearoff=0)
        self.context_menu.add_command(label="Open Directory", command=self.parent.open_customer_directory)
        self.context_menu.add_command(label="Rename", command=self.parent.customer_ops.show_rename_dialog)
        self.context_menu.add_command(label="Delete", command=self.parent.delete_selected_customers)
        self.parent.customer_tree.bind("<Button-3>", self.show_customer_context_menu)

    def show_customer_context_menu(self, event):
        iid = self.parent.customer_tree.identify_row(event.y)
        if iid:
            if iid not in self.parent.customer_tree.selection(): self.parent.customer_tree.selection_set(iid)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()

    def setup_case_tree_context_menu(self):
        logging.debug("Setting up case context menu.")
        self.case_context_menu = tk.Menu(self.parent.root, tearoff=0)
        self.case_context_menu.add_command(label="Open Case Folder", command=self.open_selected_case_folder_from_context)
        self.case_context_menu.add_command(label="Move Case Folder", command=self.parent.move_case_folder)
        self.parent.case_tree.bind("<Button-3>", self.show_case_context_menu)

    def show_case_context_menu(self, event):
        iid = self.parent.case_tree.identify_row(event.y)
        if iid:
            if iid not in self.parent.case_tree.selection(): self.parent.case_tree.selection_set(iid)
            self.parent.selected_case_id_var.set(iid)
            logging.debug(f"Context menu shown for case ID: {iid}")
            try: self.case_context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.case_context_menu.grab_release()

    def open_selected_case_folder_from_context(self):
         case_id = self.parent.selected_case_id_var.get()
         if case_id:
             try: self.parent.case_ops.open_case_folder(case_id)
             except (ValidationError, DatabaseError, FilesystemError) as e:
                  logging.error(f"Error opening case folder from context menu: {e}")
                  messagebox.showerror("Error", str(e), parent=self.parent.root)
             except Exception as e:
                  logging.critical("Unexpected error opening case folder.", exc_info=True)
                  messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}", parent=self.parent.root)
         else: messagebox.showwarning("Warning", "Could not determine selected case folder ID.", parent=self.parent.root)

    # --- Treeview Selection Handlers ---
    def on_customer_selected(self, event=None):
        selected_items = self.parent.customer_tree.selection()
        if selected_items:
            customer_id = selected_items[0]
            customer_name = self.parent.customer_tree.item(customer_id, "values")[1]
            self.parent.selected_customer_id_var.set(customer_id)
            self.parent.selected_customer_var.set(customer_name)
            logging.debug(f"Customer selected: {customer_name} (ID: {customer_id})")
            self.parent.status_var.set(f"Selected customer: {customer_name}")
            self.parent.refresh_case_list()
        else:
             self.parent.selected_customer_id_var.set("")
             self.parent.selected_customer_var.set("")
             self.parent.refresh_case_list()
             logging.debug("Customer selection cleared.")

    def on_case_selected(self, event=None):
        selected_items = self.parent.case_tree.selection()
        if selected_items:
            case_id = selected_items[0]
            case_number = self.parent.case_tree.item(case_id, "values")[1]
            self.parent.selected_case_id_var.set(case_id)
            logging.debug(f"Case selected: {case_number} (ID: {case_id})")
            self.parent.status_var.set(f"Selected case folder: {case_number}")
        else:
             self.parent.selected_case_id_var.set("")
             logging.debug("Case selection cleared.")

    # --- Dropdown Selection Handler ---
    def on_customer_dropdown_selected(self, event):
        customer_name = self.parent.selected_customer_var.get()
        customer_id = None
        logging.debug(f"Customer dropdown selected: '{customer_name}'")
        for customer in self.parent.customers:
            if customer.get("name") == customer_name: customer_id = customer.get("id"); break
        if customer_id:
            self.parent.selected_customer_id_var.set(customer_id)
            logging.debug(f"Found customer ID: {customer_id}")
            self.parent.refresh_case_list()
            self.parent.status_var.set(f"Loaded cases for: {customer_name}")
        else:
             logging.warning(f"Could not find ID for customer name: '{customer_name}'")
             self.parent.selected_customer_id_var.set("")
             self.parent.refresh_case_list()

    # --- Main Event Setup ---
    def setup_events(self):
        """Setup all event bindings."""
        logging.info("Setting up UI event bindings.")
        # Traces
        self.parent.case_filter_var.trace_add("write", self.on_case_filter_changed)
        self.parent.case_filter_field_var.trace_add("write", self.on_case_filter_changed)
        self.parent.search_var.trace_add("write", self.on_search_changed)
        self.parent.search_field_var.trace_add("write", self.on_search_changed)
        self.parent.case_number_var.trace_add("write", self.validate_case_number)
        
        # Treeview selections
        self.parent.customer_tree.bind('<<TreeviewSelect>>', self.on_customer_selected)
        self.parent.case_tree.bind('<<TreeviewSelect>>', self.on_case_selected)
        # Add binding for template tree selection
        if hasattr(self.parent, 'template_tree') and self.parent.template_tree:
             self.parent.template_tree.bind('<<TreeviewSelect>>', self.on_template_tree_selected)
        # Add binding for custom field definition tree selection
        if hasattr(self.parent, 'custom_field_tree') and self.parent.custom_field_tree:
             self.parent.custom_field_tree.bind('<<TreeviewSelect>>', self.on_custom_field_tree_selected)


        # Dropdown selections
        self.parent.customer_dropdown.bind("<<ComboboxSelected>>", self.on_customer_dropdown_selected)
        if self.parent.template_dropdown:
            self.parent.template_dropdown.bind('<<ComboboxSelected>>', self.on_template_selected)

        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Context menus
        self.setup_customer_tree_context_menu()
        self.setup_case_tree_context_menu()
        
        logging.info("Event bindings setup complete.")
