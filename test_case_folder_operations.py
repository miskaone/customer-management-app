import pytest
import sqlite3
import os
import uuid
from datetime import datetime
import builtins # For mocking open
import json # Added import
from unittest.mock import patch, MagicMock, mock_open # For mocking filesystem/open

# Modules to test
from data_manager import DataManager
from customer_operations import CustomerOperations
from case_folder_operations import CaseFolderOperations

# --- Test Fixtures (Similar to test_customer_operations) ---

class DummyParent:
    def __init__(self, data_manager_instance, customer_ops_instance):
        self.data_manager = data_manager_instance
        self.customer_ops = customer_ops_instance # CaseFolderOps needs customer_ops
        self.root = None

@pytest.fixture
def in_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    # Create schema
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT, phone TEXT, address TEXT, notes TEXT, directory TEXT UNIQUE, created_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE templates (id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT, folders TEXT NOT NULL)")
    cursor.execute("CREATE TABLE case_folders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, case_number TEXT NOT NULL, description TEXT, path TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE)")
    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def test_data_manager(in_memory_db):
    class TestDataManager(DataManager):
        def __init__(self, parent):
            self.parent = parent
            self.db_file = ":memory:"
        def _get_db_connection(self):
            return in_memory_db # Use the fixture's connection
    dm = TestDataManager(parent=None)
    return dm

@pytest.fixture
def test_customer_ops(test_data_manager):
    # CustomerOps needs a parent with data_manager
    dummy_parent_for_cust_ops = DummyParent(test_data_manager)
    ops = CustomerOperations(parent=dummy_parent_for_cust_ops)
    return ops

@pytest.fixture
def case_folder_ops(test_data_manager, test_customer_ops):
    """Fixture to create a CaseFolderOperations instance."""
    # CaseFolderOps needs a parent with data_manager and customer_ops
    dummy_parent = DummyParent(test_data_manager, test_customer_ops)
    ops = CaseFolderOperations(parent=dummy_parent)
    return ops

@pytest.fixture
def sample_customer(test_customer_ops):
    """Fixture to add a sample customer to the DB for testing case folders."""
    customer_data = test_customer_ops.add_customer(
        name="Case Test Customer",
        email="case@test.com",
        phone="555-CASE",
        address="456 Case Ave",
        notes="Customer for case tests",
        directory="/fake/customer/case_test_customer" # Use a fake path
    )
    assert customer_data is not None
    return customer_data

@pytest.fixture
def sample_template(test_data_manager):
    """Fixture to add a sample template to the DB."""
    template_data = {
        "id": "case_test_template",
        "name": "Case Test Template",
        "description": "Template for testing cases",
        "folders": ["FolderA", "FolderB"]
    }
    # Use DataManager's add_template (or direct insert for simplicity in test)
    conn = test_data_manager._get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO templates (id, name, description, folders) VALUES (?, ?, ?, ?)",
                   (template_data['id'], template_data['name'], template_data['description'], json.dumps(template_data['folders'])))
    conn.commit()
    return template_data


# --- Test Cases ---

@patch('os.path.exists')
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open)
def test_create_case_folder_success(mock_file_open, mock_makedirs, mock_exists, case_folder_ops, sample_customer, sample_template, in_memory_db):
    """Test successful creation of a case folder."""
    customer_id = sample_customer['id']
    customer_dir = sample_customer['directory']
    case_number = "MS12345"
    description = "Test Case Description"
    expected_folder_name = f"{case_number}_{description.replace(' ', '_')}"
    expected_path = os.path.join(customer_dir, expected_folder_name)

    # Mock filesystem checks: directory exists, case folder does NOT exist initially
    mock_exists.side_effect = lambda path: path == customer_dir # Only customer dir exists

    success = case_folder_ops.create_case_folder(customer_id, case_number, description, sample_template)

    assert success is True
    # Check if os.makedirs was called correctly
    mock_makedirs.assert_any_call(expected_path) # Main folder
    mock_makedirs.assert_any_call(os.path.join(expected_path, "FolderA"), exist_ok=True) # Subfolders
    mock_makedirs.assert_any_call(os.path.join(expected_path, "FolderB"), exist_ok=True)
    # Check if case_info.txt was opened for writing
    mock_file_open.assert_called_once_with(os.path.join(expected_path, "case_info.txt"), 'w')

    # Verify DB record
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT * FROM case_folders WHERE customer_id = ? AND case_number = ?", (customer_id, case_number))
    row = cursor.fetchone()
    assert row is not None
    assert dict(row)['description'] == description
    assert dict(row)['path'] == expected_path

@patch('os.path.exists')
def test_create_case_folder_customer_dir_not_found(mock_exists, case_folder_ops, sample_customer):
    """Test creating case folder when customer directory doesn't exist."""
    customer_id = sample_customer['id']
    mock_exists.return_value = False # Simulate customer directory not existing

    success = case_folder_ops.create_case_folder(customer_id, "MS999", "Test", None)
    assert success is False

@patch('os.path.exists')
def test_create_case_folder_already_exists(mock_exists, case_folder_ops, sample_customer):
    """Test creating case folder when it already exists on filesystem."""
    customer_id = sample_customer['id']
    customer_dir = sample_customer['directory']
    case_number = "MS111"
    expected_path = os.path.join(customer_dir, case_number)

    # Simulate both customer dir AND case folder existing
    mock_exists.side_effect = lambda path: path in [customer_dir, expected_path]

    success = case_folder_ops.create_case_folder(customer_id, case_number, "", None)
    assert success is False

def test_create_case_folder_invalid_case_number(case_folder_ops, sample_customer):
    """Test creating case folder with invalid case number (no MS prefix)."""
    success = case_folder_ops.create_case_folder(sample_customer['id'], "12345", "Invalid", None)
    assert success is False

def test_get_case_folders(case_folder_ops, sample_customer, in_memory_db):
    """Test retrieving case folders for a customer."""
    customer_id = sample_customer['id']
    # Add some dummy case folders to DB
    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO case_folders (customer_id, case_number, description, path, created_at) VALUES (?, ?, ?, ?, ?)",
                   (customer_id, "MS001", "Desc 1", "/fake/cust/MS001", datetime.now().isoformat()))
    cursor.execute("INSERT INTO case_folders (customer_id, case_number, description, path, created_at) VALUES (?, ?, ?, ?, ?)",
                   (customer_id, "MS002", "Desc 2", "/fake/cust/MS002", datetime.now().isoformat()))
    in_memory_db.commit()

    folders = case_folder_ops.get_case_folders(customer_id)
    assert folders is not None
    assert len(folders) == 2
    assert isinstance(folders[0], dict)
    assert folders[0]['case_number'] in ["MS001", "MS002"] # Order might vary depending on timestamp
    assert folders[1]['description'] in ["Desc 1", "Desc 2"]

def test_get_case_folders_no_customer(case_folder_ops):
    """Test retrieving folders for a non-existent customer ID."""
    folders = case_folder_ops.get_case_folders("non-existent-id")
    assert folders == []

# Note: Need to import json for sample_template fixture
import json

@patch('os.path.exists')
@patch('shutil.move')
@patch('builtins.open', new_callable=mock_open)
def test_move_case_folder_success(mock_open_call, mock_shutil_move, mock_os_exists, case_folder_ops, test_customer_ops, sample_customer, in_memory_db):
    """Test successfully moving a case folder between customers."""
    # --- Setup ---
    # Source customer (already created by sample_customer fixture)
    source_customer_id = sample_customer['id']
    source_customer_dir = sample_customer['directory']

    # Target customer
    target_customer = test_customer_ops.add_customer("Target Cust", "", "", "", "", "/fake/target_cust")
    assert target_customer is not None
    target_customer_id = target_customer['id']
    target_customer_dir = target_customer['directory']

    # Case folder to move (add to DB first)
    case_number = "MSMOVE01"
    folder_name = f"{case_number}_MoveMe"
    source_path = os.path.join(source_customer_dir, folder_name)
    target_path = os.path.join(target_customer_dir, folder_name)
    created_at = datetime.now().isoformat()

    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO case_folders (customer_id, case_number, description, path, created_at) VALUES (?, ?, ?, ?, ?)",
                   (source_customer_id, case_number, "Move Me", source_path, created_at))
    in_memory_db.commit()
    # Get the generated ID
    case_folder_id = cursor.lastrowid

    # Mock filesystem: source customer dir, target customer dir, and source case path exist. Target case path does NOT exist.
    mock_os_exists.side_effect = lambda path: path in [source_customer_dir, target_customer_dir, source_path]

    # --- Action ---
    success = case_folder_ops.move_case_folder(case_folder_id, target_customer_id)

    # --- Assertions ---
    assert success is True
    # Check filesystem move was called
    mock_shutil_move.assert_called_once_with(source_path, target_path)
    # Check if case_info.txt was opened and potentially written to (optional check)
    # mock_open_call.assert_any_call(os.path.join(target_path, "case_info.txt"), 'r') # Check read
    # mock_open_call.assert_any_call(os.path.join(target_path, "case_info.txt"), 'w') # Check write

    # Verify DB update
    cursor.execute("SELECT customer_id, path FROM case_folders WHERE id = ?", (case_folder_id,))
    row = cursor.fetchone()
    assert row is not None
    assert dict(row)['customer_id'] == target_customer_id
    assert dict(row)['path'] == target_path

@patch('os.path.exists')
@patch('shutil.move')
def test_move_case_folder_target_exists(mock_shutil_move, mock_os_exists, case_folder_ops, test_customer_ops, sample_customer, in_memory_db):
    """Test moving a case folder when a folder with the same name exists at the target."""
    # Setup similar to success case...
    source_customer_id = sample_customer['id']
    source_customer_dir = sample_customer['directory']
    target_customer = test_customer_ops.add_customer("Target Cust 2", "", "", "", "", "/fake/target_cust2")
    target_customer_id = target_customer['id']
    target_customer_dir = target_customer['directory']
    case_number = "MSMOVE02"
    folder_name = f"{case_number}_Exists"
    source_path = os.path.join(source_customer_dir, folder_name)
    target_path = os.path.join(target_customer_dir, folder_name)
    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO case_folders (customer_id, case_number, description, path, created_at) VALUES (?, ?, ?, ?, ?)",
                   (source_customer_id, case_number, "Exists", source_path, datetime.now().isoformat()))
    in_memory_db.commit()
    case_folder_id = cursor.lastrowid

    # Mock filesystem: All relevant paths exist, including the target case path
    mock_os_exists.return_value = True

    # Action
    success = case_folder_ops.move_case_folder(case_folder_id, target_customer_id)

    # Assertions
    assert success is False
    mock_shutil_move.assert_not_called() # Should not attempt move if target exists

    # Verify DB record is unchanged
    cursor.execute("SELECT customer_id, path FROM case_folders WHERE id = ?", (case_folder_id,))
    row = cursor.fetchone()
    assert row is not None
    assert dict(row)['customer_id'] == source_customer_id # Still belongs to source
    assert dict(row)['path'] == source_path # Path unchanged

# Add test for open_case_folder (needs mocking os.path.exists and utils.open_directory)
