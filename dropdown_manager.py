class DropdownManager:
    """Handles dropdown-related operations for customer and template selection"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def update_customer_dropdown(self):
        """Update the customer dropdown with current customers"""
        # Clear current values
        if self.parent.customer_dropdown:
            self.parent.customer_dropdown['values'] = []
        
        # Get customer names
        customer_names = [customer.get("name") for customer in self.parent.customers]
        
        # Set new values
        if self.parent.customer_dropdown:
            self.parent.customer_dropdown['values'] = customer_names
    
    def update_template_dropdown(self):
        """Update the template dropdown with current templates"""
        # Clear current values
        if self.parent.template_dropdown:
            self.parent.template_dropdown['values'] = []
        
        # Get template names
        template_names = [template.get("name") for template in self.parent.templates]
        
        # Set new values
        if self.parent.template_dropdown:
            self.parent.template_dropdown['values'] = template_names
            
            # Select the first template by default
            if template_names and not self.parent.selected_template_var.get():
                self.parent.selected_template_var.set(template_names[0])
                
                # Update the description directly
                first_template = self.get_selected_template()
                if first_template:
                    self.parent.template_desc_var.set(first_template.get("description", ""))
                else:
                    self.parent.template_desc_var.set("")
    
    def get_selected_template(self):
        """Get the currently selected template object"""
        selected_name = self.parent.selected_template_var.get()
        for template in self.parent.templates:
            if template.get("name") == selected_name:
                return template
        return None
