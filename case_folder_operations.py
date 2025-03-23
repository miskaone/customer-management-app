import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from utils import open_directory, format_timestamp

class CaseFolderOperations:
    """Handles operations related to case folders"""
    
    def __init__(self, parent):
        """Initialize with parent CustomerManager instance"""
        self.parent = parent
    
    def create_case_folder(self, customer_id, case_number, description, template):
        """Create a case folder for a customer"""
        # Find customer with this ID
        customer_dir = None
        customer_name = None
        
        for customer in self.parent.customers:
            if customer.get("id") == customer_id:
                customer_dir = customer.get("directory")
                customer_name = customer.get("name")
                break
        
        if not customer_dir or not os.path.exists(customer_dir):
            messagebox.showerror("Error", "Customer directory not found")
            return False
        
        # Validate case number
        if not case_number:
            messagebox.showerror("Error", "Case number is required")
            return False
        
        if not case_number.startswith("MS"):
            messagebox.showerror("Error", "Case numbers should start with MS")
            return False
        
        # Sanitize case number (just in case)
        invalid_chars = r'<>:"/\|?*'
        if any(c in invalid_chars for c in case_number):
            original_case = case_number
            case_number = ''.join(c if c not in invalid_chars else '_' for c in case_number)
            messagebox.showwarning("Warning", f"Invalid characters in case number have been replaced with underscores.\nOriginal: {original_case}\nSanitized: {case_number}")
        
        # Create folder name from case number and description
        folder_name = case_number
        
        if description:
            # Store original description for comparison
            original_desc = description
            
            # Replace invalid characters in description (more comprehensive)
            # These characters are typically invalid in most file systems: < > : " / \ | ? *
            safe_desc = ''.join(c if c not in invalid_chars and c.isascii() else '_' for c in description)
            
            # Remove leading/trailing spaces from the sanitized description
            safe_desc = safe_desc.strip()
            
            # Collapse multiple underscores
            while '__' in safe_desc:
                safe_desc = safe_desc.replace('__', '_')
            
            # Notify user if description was modified
            if safe_desc != original_desc:
                messagebox.showinfo("Information", 
                    f"Special characters in your description have been replaced with underscores for folder name compatibility.\n\n"
                    f"Original: {original_desc}\n"
                    f"Modified: {safe_desc}")
            
            folder_name = f"{folder_name}_{safe_desc}" if safe_desc else folder_name
        
        # Create the case folder
        case_path = os.path.join(customer_dir, folder_name)
        try:
            # Check if the folder already exists
            if os.path.exists(case_path):
                messagebox.showerror("Error", f"Case folder already exists: {folder_name}")
                return False
            
            # Create the folder
            os.makedirs(case_path)
            
            # Create subfolders from template
            if template and "folders" in template:
                for subfolder in template["folders"]:
                    os.makedirs(os.path.join(case_path, subfolder), exist_ok=True)
            
            # Create a case info file
            with open(os.path.join(case_path, "case_info.txt"), 'w') as f:
                f.write(f"Case Number: {case_number}\n")
                f.write(f"Description: {description}\n")
                f.write(f"Customer: {customer_name}\n")
                f.write(f"Created: {format_timestamp()}\n")
                f.write(f"Template: {template.get('name', 'None') if template else 'None'}\n")
            
            # Show success message
            messagebox.showinfo("Success", f"Case folder created: {folder_name}")
            
            # Open the folder
            open_directory(case_path)
            
            return True
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create case folder: {str(e)}")
            return False
    
    def get_case_folders(self, customer_id):
        """Get list of case folders for a customer"""
        # Find customer with this ID
        customer_dir = None
        
        for customer in self.parent.customers:
            if customer.get("id") == customer_id:
                customer_dir = customer.get("directory")
                break
        
        if not customer_dir or not os.path.exists(customer_dir):
            return []
        
        # Get list of case folders
        case_folders = []
        for item in os.listdir(customer_dir):
            item_path = os.path.join(customer_dir, item)
            if os.path.isdir(item_path):
                # Try to get info from case_info.txt
                info_path = os.path.join(item_path, "case_info.txt")
                description = ""
                created_date = ""
                
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r') as f:
                            lines = f.readlines()
                            for line in lines:
                                if line.startswith("Description:"):
                                    description = line.split(":", 1)[1].strip()
                                elif line.startswith("Created:"):
                                    created_date = line.split(":", 1)[1].strip()
                    except:
                        pass
                
                case_folders.append({
                    "name": item,
                    "path": item_path,
                    "description": description,
                    "created_date": created_date
                })
        
        return case_folders
    
    def open_case_folder(self, customer_id, case_folder_name):
        """Open a case folder for a customer"""
        # Find customer with this ID
        customer_dir = None
        
        for customer in self.parent.customers:
            if customer.get("id") == customer_id:
                customer_dir = customer.get("directory")
                break
        
        if not customer_dir:
            messagebox.showerror("Error", "Customer directory not found")
            return False
        
        # Open the case folder
        case_path = os.path.join(customer_dir, case_folder_name)
        if not os.path.exists(case_path):
            messagebox.showerror("Error", f"Case folder does not exist: {case_folder_name}")
            return False
        
        open_directory(case_path)
        return True
        
    def add_ms_prefix(self, case_number):
        """Add MS prefix to case number if it doesn't have one"""
        if case_number and not case_number.startswith("MS"):
            return f"MS{case_number}"
        return case_number
    
    def validate_case_number(self, case_number):
        """Validate that case number starts with MS"""
        if case_number and not case_number.startswith("MS"):
            return False, "Case numbers should start with MS"
        return True, ""
        
    def move_case_folder(self, source_customer_id, case_folder_name, target_customer_id):
        """Move a case folder from one customer to another"""
        import shutil
        
        # Find source customer directory
        source_customer_dir = None
        source_customer_name = None
        for customer in self.parent.customers:
            if customer.get("id") == source_customer_id:
                source_customer_dir = customer.get("directory")
                source_customer_name = customer.get("name")
                break
                
        if not source_customer_dir or not os.path.exists(source_customer_dir):
            messagebox.showerror("Error", "Source customer directory not found")
            return False
            
        # Find target customer directory
        target_customer_dir = None
        target_customer_name = None
        for customer in self.parent.customers:
            if customer.get("id") == target_customer_id:
                target_customer_dir = customer.get("directory")
                target_customer_name = customer.get("name")
                break
                
        if not target_customer_dir or not os.path.exists(target_customer_dir):
            messagebox.showerror("Error", "Target customer directory not found")
            return False
            
        # Check if the case folder exists in source
        source_case_path = os.path.join(source_customer_dir, case_folder_name)
        if not os.path.exists(source_case_path):
            messagebox.showerror("Error", f"Case folder not found: {case_folder_name}")
            return False
            
        # Check if a case folder with the same name exists in target
        target_case_path = os.path.join(target_customer_dir, case_folder_name)
        if os.path.exists(target_case_path):
            messagebox.showerror("Error", f"A case folder with the same name already exists for the target customer")
            return False
            
        try:
            # Move the folder
            shutil.move(source_case_path, target_case_path)
            
            # Update the case_info.txt file with new customer info
            case_info_path = os.path.join(target_case_path, "case_info.txt")
            if os.path.exists(case_info_path):
                # Read existing case info
                with open(case_info_path, 'r') as f:
                    lines = f.readlines()
                    
                # Update customer line
                updated_lines = []
                for line in lines:
                    if line.startswith("Customer:"):
                        updated_lines.append(f"Customer: {target_customer_name}\n")
                    else:
                        updated_lines.append(line)
                        
                # Add a note about the move
                updated_lines.append(f"Moved from: {source_customer_name} on {format_timestamp()}\n")
                
                # Write updated info
                with open(case_info_path, 'w') as f:
                    f.writelines(updated_lines)
            
            messagebox.showinfo("Success", f"Case folder '{case_folder_name}' successfully moved from '{source_customer_name}' to '{target_customer_name}'")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move case folder: {str(e)}")
            return False
