# Customer Directory Manager

A modular application for managing customers, their associated directories, and case folders.

## Features

- Add new customers with detailed information
- Manage customers with search and bulk operations
- Create case folders using customizable templates
- Search and filter capabilities for both customers and case folders
- Export customer data to CSV or JSON format
- Auto-save functionality to prevent data loss
- Tooltips for better user guidance

## Requirements

- Python 3.6 or higher
- Tkinter (included with standard Python installation)

## Usage

1. Run the application:

   ```python
   python customer_manager.py
   ```

2. Add a new customer:

   - Fill in customer details in the "Add Customer" tab
   - Select an existing directory or create a new directory
   - Click "Save Customer"

3. Manage customers:

   - View all customers in the "Manage Customers" tab
   - Search for customers using the search box
   - Select customers for bulk operations (export, update, delete)
   - Open a customer's directory

4. Create case folders:

   - Select a customer from the dropdown in the "Create Case Folder" tab
   - Enter a case number (must start with "MS")
   - Add a description and select a folder template
   - Click "Create Case Folder"
   - View and open existing case folders

## Keyboard Shortcuts

- Ctrl+S: Save customer data
- Ctrl+F: Focus on search/filter input
- F5: Refresh customer list
- Ctrl+1: Switch to Add Customer tab
- Ctrl+2: Switch to Manage Customers tab
- Ctrl+3: Switch to Create Case Folder tab
- Ctrl+E: Export selected customers to CSV
- Ctrl+D: Delete selected customers

## File Structure

- `customer_manager.py`: Main application with GUI setup
- `customer_operations.py`: Customer-related operations (add, update, delete, export)
- `case_folder_operations.py`: Case folder management operations
- `ui_components.py`: Reusable UI components like tooltips
- `utils.py`: Utility functions for file operations and general helpers
- `customers.json`: Customer data storage (created automatically)
- `templates.json`: Case folder templates (created automatically)

## Auto-Save Feature

The application automatically saves customer data every 60 seconds to prevent data loss.

## Data Validation

- Case numbers must start with "MS"
- Customer name and directory are required fields

## Note

The application automatically creates the necessary JSON files in the same directory as the script to store customer information and templates.
