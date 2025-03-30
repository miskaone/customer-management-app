import pytest
import sqlite3
import os
import uuid
from datetime import datetime

# Modules to test
from data_manager import DataManager
from customer_operations import CustomerOperations

# --- Test Fixtures ---

# Dummy Parent class to satisfy dependencies
class DummyParent:
    def __init__(self, data_manager_instance):
        self.data_manager = data_manager_instance
        # Add other attributes if CustomerOperations starts depending on them
        self.root = None # No real Tk root needed for these tests

@pytest.fixture
def in_memory_db():
    """Fixture to create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    yield conn
    conn.close()

@pytest.fixture
def test_data_manager(in_memory_db, monkeypatch):
    """Fixture to create a DataManager instance using the in-memory DB."""
    # Create a dummy DataManager that uses the in-memory connection
    class TestDataManager(DataManager):
        def __init__(self, parent):
            # Skip regular init, especially migration
            self.parent = parent
            self.db_file = ":memory:" # Indicate in-memory
            # Don't call _initialize_database or _migrate_json_data here
            # The schema will be created by the fixture below

        def _get_db_connection(self):
            # Return the already connected in-memory DB from the fixture
            # This is a simplification; real scenarios might need more robust connection management
            return in_memory_db

    # Initialize the schema in the in-memory DB
    cursor = in_memory_db.cursor()
    # Customers Table
    cursor.execute("""
        CREATE TABLE customers (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT, phone TEXT,
            address TEXT, notes TEXT, directory TEXT UNIQUE, created_at TEXT NOT NULL
        )
    """)
    # Templates Table (needed if ops classes reference it indirectly)
    cursor.execute("""
        CREATE TABLE templates (
            id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT, folders TEXT NOT NULL
        )
    """)
     # Case Folders Table (needed for foreign key constraints)
    cursor.execute("""
        CREATE TABLE case_folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, case_number TEXT NOT NULL,
            description TEXT, path TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
        )
    """)
    in_memory_db.commit()

    # Instantiate the TestDataManager
    dm = TestDataManager(parent=None) # Parent not strictly needed for DM itself
    return dm


@pytest.fixture
def customer_ops(test_data_manager):
    """Fixture to create a CustomerOperations instance with the test DataManager."""
    dummy_parent = DummyParent(test_data_manager)
    ops = CustomerOperations(parent=dummy_parent)
    return ops

# --- Test Cases ---

def test_add_customer_success(customer_ops, in_memory_db):
    """Test adding a valid customer."""
    name = "Test Customer"
    email = "test@example.com"
    phone = "1234567890"
    address = "123 Test St"
    notes = "Some notes"
    directory = "/test/customer/dir"
    
    result = customer_ops.add_customer(name, email, phone, address, notes, directory)

    assert result is not None
    assert isinstance(result, dict)
    assert result["name"] == name
    assert result["directory"] == directory
    new_id = result["id"]

    # Verify in DB
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    assert row is not None
    assert dict(row)["name"] == name
    assert dict(row)["email"] == email
    assert dict(row)["phone"] == phone
    assert dict(row)["address"] == address
    assert dict(row)["notes"] == notes
    assert dict(row)["directory"] == directory
    assert dict(row)["id"] == new_id

def test_add_customer_missing_name(customer_ops):
    """Test adding a customer with a missing name."""
    # Expect add_customer to handle messagebox and return None/False
    # We can't easily test the messagebox call itself without more complex mocking
    result = customer_ops.add_customer("", "test@example.com", "123", "addr", "notes", "/dir")
    assert result is False # Should fail validation

def test_add_customer_missing_directory(customer_ops):
    """Test adding a customer with a missing directory."""
    result = customer_ops.add_customer("Test Name", "test@example.com", "123", "addr", "notes", "")
    assert result is False # Should fail validation

def test_add_customer_duplicate_directory(customer_ops, in_memory_db):
    """Test adding a customer with a directory that already exists."""
    dir_path = "/unique/customer/path"
    # Add first customer
    customer_ops.add_customer("Customer One", "", "", "", "", dir_path)
    
    # Try adding second customer with the same directory
    # Expect add_customer to handle the IntegrityError and return None
    result = customer_ops.add_customer("Customer Two", "", "", "", "", dir_path)
    assert result is None # Indicates failure, specifically UNIQUE constraint likely

    # Verify only one customer with that directory exists
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers WHERE directory = ?", (dir_path,))
    count = cursor.fetchone()[0]
    assert count == 1

def test_get_customer_by_id_found(customer_ops):
    """Test retrieving an existing customer by ID."""
    added_customer = customer_ops.add_customer("Find Me", "find@me.com", "", "", "", "/find/me")
    assert added_customer is not None
    customer_id = added_customer["id"]

    retrieved_customer = customer_ops.get_customer_by_id(customer_id)
    assert retrieved_customer is not None
    assert isinstance(retrieved_customer, dict)
    assert retrieved_customer["id"] == customer_id
    assert retrieved_customer["name"] == "Find Me"
    assert retrieved_customer["email"] == "find@me.com"

def test_get_customer_by_id_not_found(customer_ops):
    """Test retrieving a non-existent customer ID."""
    non_existent_id = str(uuid.uuid4())
    retrieved_customer = customer_ops.get_customer_by_id(non_existent_id)
    assert retrieved_customer is None

def test_update_customer_success(customer_ops, in_memory_db):
    """Test successfully updating an existing customer."""
    added_customer = customer_ops.add_customer("Update Me", "update@me.com", "111", "Addr", "Notes", "/update/me")
    customer_id = added_customer["id"]

    updates = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "phone": "9998887777"
    }
    success = customer_ops.update_customer(customer_id, **updates)
    assert success is True

    # Verify in DB
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT name, email, phone FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    assert row is not None
    assert dict(row)["name"] == "Updated Name"
    assert dict(row)["email"] == "updated@example.com"
    assert dict(row)["phone"] == "9998887777"

def test_update_customer_not_found(customer_ops):
    """Test updating a non-existent customer ID."""
    non_existent_id = str(uuid.uuid4())
    updates = {"name": "Won't Update"}
    success = customer_ops.update_customer(non_existent_id, **updates)
    assert success is False

def test_delete_customer_success(customer_ops, in_memory_db):
    """Test successfully deleting a customer."""
    added_customer = customer_ops.add_customer("Delete Me", "", "", "", "", "/delete/me")
    customer_id = added_customer["id"]

    success = customer_ops.delete_customer(customer_id)
    assert success is True

    # Verify deletion in DB
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers WHERE id = ?", (customer_id,))
    count = cursor.fetchone()[0]
    assert count == 0

def test_delete_customer_not_found(customer_ops):
    """Test deleting a non-existent customer ID."""
    non_existent_id = str(uuid.uuid4())
    success = customer_ops.delete_customer(non_existent_id)
    assert success is False

def test_delete_multiple_customers(customer_ops, in_memory_db):
    """Test deleting multiple customers."""
    cust1 = customer_ops.add_customer("Del Multi 1", "", "", "", "", "/del/multi1")
    cust2 = customer_ops.add_customer("Del Multi 2", "", "", "", "", "/del/multi2")
    cust3 = customer_ops.add_customer("Keep Me", "", "", "", "", "/keep/me")
    ids_to_delete = [cust1["id"], cust2["id"]]

    deleted_count = customer_ops.delete_multiple_customers(ids_to_delete)
    assert deleted_count == 2

    # Verify deletion in DB
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers WHERE id IN (?, ?)", tuple(ids_to_delete))
    count_deleted = cursor.fetchone()[0]
    assert count_deleted == 0

    cursor.execute("SELECT COUNT(*) FROM customers WHERE id = ?", (cust3["id"],))
    count_kept = cursor.fetchone()[0]
    assert count_kept == 1

def test_rename_customer_success(customer_ops, in_memory_db):
    """Test successfully renaming a customer."""
    added_customer = customer_ops.add_customer("Rename Me", "", "", "", "", "/rename/me")
    customer_id = added_customer["id"]
    new_name = "Successfully Renamed"

    success = customer_ops.rename_customer(customer_id, new_name)
    assert success is True

    # Verify in DB
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    assert row is not None
    assert dict(row)["name"] == new_name

def test_rename_customer_not_found(customer_ops):
    """Test renaming a non-existent customer."""
    non_existent_id = str(uuid.uuid4())
    success = customer_ops.rename_customer(non_existent_id, "New Name")
    assert success is False

def test_rename_customer_empty_name(customer_ops):
    """Test renaming a customer to an empty name."""
    added_customer = customer_ops.add_customer("Original Name", "", "", "", "", "/orig/name")
    customer_id = added_customer["id"]
    
    # Expect rename_customer to handle messagebox and return False
    success = customer_ops.rename_customer(customer_id, "  ") # Empty after strip
    assert success is False
