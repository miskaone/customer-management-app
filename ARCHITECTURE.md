# Customer Management App - Architecture and Features

This document provides an overview of the architecture and features of the Customer Management application.

## 1. Architecture

The application follows a modular design, separating concerns into distinct components:

*   **UI (tkinter):** The user interface is built using the `tkinter` library and its themed widgets (`ttk`). The `UISetup` class handles the creation and layout of the main UI elements, including tabs, frames, labels, entries, and buttons. Each tab has its own setup method (e.g., `setup_add_customer_tab`, `setup_manage_customers_tab`, `setup_manage_templates_tab`, `setup_case_folder_tab`).
*   **Data Management (data_manager.py):** The `DataManager` class is responsible for all data access and persistence. It uses an SQLite database (`customer_data.db`) to store customer information, templates, case folders, and audit logs. It handles database initialization, data migration from the old JSON format, and provides methods for loading, adding, updating, and deleting data.
*   **Operational Logic (customer_operations.py, case_folder_operations.py):** These modules contain the core business logic for managing customers and case folders. They handle tasks such as validating data, creating directories, renaming customers, and moving case folders. They raise custom exceptions (e.g., `ValidationError`, `DatabaseError`, `FilesystemError`) to signal errors to the UI layer.
*   **Event Handling (event_handlers.py):** The `EventHandlers` class manages UI events, such as button clicks, dropdown selections, and treeview selections. It connects UI actions to the corresponding data management and operational logic.
*   **Treeview Management (treeview_manager.py):** The `TreeviewManager` class handles the population and sorting of data in the treeview widgets used to display customers and case folders.
*   **Form Management (form_manager.py):** The `FormManager` class assists with saving data from the forms.
*   **Dropdown Management (dropdown_manager.py):** The `DropdownManager` class assists with populating and managing the dropdowns.
*   **Bulk Operations (bulk_operations.py):** The `BulkOperations` class handles bulk actions such as importing, exporting, and deleting multiple customers.
*   **UI Components (ui_components.py):** This module contains reusable UI components, such as the `ToolTip` class for adding tooltips to widgets.

## 2. Key Features

*   **Database Migration & Refinement:** Migrated data storage to SQLite, refactored operational classes to remove UI dependencies (using exceptions), improved logging, and applied a ttk theme.
*   **Template Management:** Added a new "Manage Templates" tab with functionality to add, update, and delete case folder templates stored in the database.
*   **Advanced Search:** Enhanced the customer search to support multiple search terms (space-separated) and search across name, email, phone, address, and notes when 'all' is selected.
*   **Audit Trail:** Added an `audit_log` table to the database and integrated logging calls into customer and case folder operations (add, update, delete, rename, move) to record these actions. A UI to view the log was not implemented but the data is being recorded.
*   **Custom Fields:** The database schema and UI elements for defining custom fields (name, label, type, target entity) have been added under the "Manage Templates" tab. *Note: The functionality to display and save values for these custom fields on customer/case forms is not yet implemented.*
*   **Testing:** `pytest` is added, and initial unit tests for database operations are included.

## 3. Data Flow

1.  **User Interaction:** The user interacts with the UI (e.g., clicks a button, enters data into a form).
2.  **Event Handling:** The corresponding event handler in `event_handlers.py` is triggered.
3.  **Operational Logic:** The event handler calls a method in `customer_operations.py` or `case_folder_operations.py` to perform the requested action.
4.  **Data Management:** The operational logic interacts with the `DataManager` to access or modify data in the SQLite database.
5.  **UI Update:** The `DataManager` updates the UI (e.g., refreshes the customer list, displays a status message) to reflect the changes.

## 4. Future Enhancements

*   Implement the UI and logic for displaying and saving custom field values on customer/case forms.
*   Add a UI to view the audit log.
*   Implement selective import UI.
*   Add unit tests for more components.
*   Implement a proper form management system.
*   Implement a settings panel to configure the app.
