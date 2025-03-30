"""
Web Wrapper for Customer Management App
Provides a simple web interface and API, primarily for testing.
Interacts directly with the database via operational classes.
"""
import json
import threading
import tkinter as tk # Still needed for messagebox in ops classes (needs refactor)
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, List
import os
import importlib.util
from datetime import datetime
import asyncio
import starlette
import secrets
import logging
import sys # For platform check in open_directory

# Import operational classes and utils
from data_manager import DataManager
from customer_operations import CustomerOperations
from utils import setup_logging, open_directory

# Setup logging for the web wrapper
setup_logging()

# Import the PlaywrightTester class
try:
    from playwright_tests import PlaywrightTester
except ImportError:
    module_path = os.path.join(os.path.dirname(__file__), 'playwright_tests.py')
    spec = importlib.util.spec_from_file_location("playwright_tests", module_path)
    playwright_tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(playwright_tests)
    PlaywrightTester = playwright_tests.PlaywrightTester

# --- Pydantic Models ---
class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    directory: str

class CustomerCreateAPI(CustomerBase):
    pass

class CustomerUpdateAPI(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    directory: Optional[str] = None # Disallowing directory update via API for safety

class CustomerResponse(CustomerBase):
    id: str
    created_at: str

class TestRequest(BaseModel):
    test: str
    enable_screenshots: Optional[bool] = True
    real_mode: Optional[bool] = False

# --- HTML Templates (remain the same) ---
# (HTML_TEMPLATE, TESTING_TEMPLATE, SCREENSHOTS_CSS, SCREENSHOTS_TEMPLATE omitted for brevity)
HTML_TEMPLATE = """ ... """ # Assume previous correct template
TESTING_TEMPLATE = """ ... """ # Assume previous correct template
SCREENSHOTS_CSS = """ ... """ # Assume previous correct template
SCREENSHOTS_TEMPLATE = """ ... """ # Assume previous correct template


# --- Global App State (Test-related only) ---
app_data = {
    'test_events': {},
    'active_tests': {}
}

# --- Dependency Instantiation ---
# Create instances of operational classes for the API's lifetime.
# Workaround for Tkinter dependencies (messagebox, simpledialog) in ops classes.
try:
    _tk_root = tk.Tk()
    _tk_root.withdraw()
except tk.TclError:
    _tk_root = None
    logging.warning("Tkinter not available or failed to initialize. Messagebox/SimpleDialog in API routes might fail.")

# Define a dummy parent object that provides necessary attributes if needed by ops classes
class DummyParent:
    def __init__(self, data_manager_instance):
        self.data_manager = data_manager_instance
        # Provide the dummy root if needed by messagebox/simpledialog calls in ops classes
        # This allows ops classes expecting parent.root to function if Tkinter is available
        self.root = _tk_root 

# Instantiate DataManager (assuming it doesn't strictly need a parent)
_data_manager_instance = DataManager(parent=None) 
# Create the dummy parent with the DataManager instance
_dummy_parent = DummyParent(_data_manager_instance)
# Instantiate CustomerOperations, passing the dummy parent
_customer_ops_instance = CustomerOperations(parent=_dummy_parent) 

# --- FastAPI App Initialization ---
app = FastAPI(title="Customer Management App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def index():
    # Re-insert HTML template content here if needed, or load from file
    return """ ... HTML_TEMPLATE content ... """

@app.get("/tests", response_class=HTMLResponse)
async def tests_page():
     # Re-insert TESTING_TEMPLATE content here if needed, or load from file
    return """ ... TESTING_TEMPLATE content ... """

@app.get("/screenshots")
async def screenshots_page():
    # (Screenshot gallery logic remains the same)
    screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
    if not os.path.exists(screenshots_dir): os.makedirs(screenshots_dir)
    screenshot_files = []
    try:
        for file in os.listdir(screenshots_dir):
            if file.endswith('.html'):
                file_path = os.path.join(screenshots_dir, file)
                mod_time = os.path.getmtime(file_path)
                screenshot_files.append({'name': file.replace('.html', ''), 'path': f"/screenshots/{file}", 'mod_time': mod_time, 'date': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')})
    except Exception as e: logging.error(f"Error reading screenshots directory: {e}")
    screenshot_files.sort(key=lambda x: x['mod_time'], reverse=True)
    if screenshot_files:
        rows = [f"<tr><td>{i+1}</td><td>{s['name']}</td><td>{s['date']}</td><td><a href='{s['path']}' target='_blank' class='view-button'>View</a></td></tr>" for i, s in enumerate(screenshot_files)]
        content = f"<table><thead><tr><th>#</th><th>Name</th><th>Date</th><th>Action</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    else: content = "<div class='empty-gallery'><h2>No Screenshots Available</h2><p>Run tests to generate screenshots.</p></div>"
    # Re-insert SCREENSHOTS_TEMPLATE and SCREENSHOTS_CSS content here
    css_content = """ ... SCREENSHOTS_CSS content ... """
    html_content = """ ... SCREENSHOTS_TEMPLATE content ... """.format(css=css_content, content=content)
    return HTMLResponse(html_content)

@app.get("/screenshots/{filename}")
async def serve_screenshot(filename: str):
    screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
    file_path = os.path.join(screenshots_dir, filename)
    if os.path.exists(file_path): return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Screenshot not found")

# --- Customer API Endpoints ---

@app.get("/api/customers", response_model=List[CustomerResponse])
async def get_customers_api():
    logging.info("API: GET /api/customers")
    try:
        customers = _data_manager_instance.load_customers()
        if customers is None: raise HTTPException(status_code=500, detail="Failed to load customers.")
        return [CustomerResponse(**cust) for cust in customers]
    except Exception as e:
        logging.error(f"API Error getting customers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.post("/api/customers", response_model=dict)
async def add_customer_api(customer: CustomerCreateAPI):
    logging.info(f"API: POST /api/customers - Name: {customer.name}")
    try:
        # Use the instantiated CustomerOperations
        # Note: add_customer might show messageboxes if Tkinter is available
        new_customer_data = _customer_ops_instance.add_customer(
            name=customer.name, email=customer.email, phone=customer.phone,
            address=customer.address, notes=customer.notes, directory=customer.directory
        )
        if new_customer_data:
            return {"success": True, "message": "Customer added.", "customer_id": new_customer_data.get("id")}
        else:
            # Failure likely due to duplicate directory or DB error (logged/shown by add_customer)
            raise HTTPException(status_code=409, detail="Failed to add customer (duplicate directory or DB error).")
    except HTTPException: raise # Re-raise FastAPI exceptions
    except Exception as e:
        logging.error(f"API Error adding customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.put("/api/customers/{customer_id}", response_model=dict)
async def update_customer_api(customer_id: str, customer_update: CustomerUpdateAPI):
    logging.info(f"API: PUT /api/customers/{customer_id}")
    updates = customer_update.dict(exclude_unset=True)
    if not updates: raise HTTPException(status_code=400, detail="No update data provided.")
    if 'directory' in updates: # Disallow directory changes via API for now
        del updates['directory']
        logging.warning(f"API update attempt for customer {customer_id} ignored directory change.")
    if not updates: raise HTTPException(status_code=400, detail="Only directory update specified, which is disallowed.")

    try:
        # Check existence first
        if not _customer_ops_instance.get_customer_by_id(customer_id):
             raise HTTPException(status_code=404, detail="Customer not found.")
        
        success = _customer_ops_instance.update_customer(customer_id, **updates)
        if success:
            return {"success": True, "message": "Customer updated."}
        else:
            raise HTTPException(status_code=500, detail="Failed to update customer (database error).")
    except HTTPException: raise
    except Exception as e:
        logging.error(f"API Error updating customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.delete("/api/customers/{customer_id}", response_model=dict)
async def delete_customer_api(customer_id: str):
    logging.info(f"API: DELETE /api/customers/{customer_id}")
    try:
        if not _customer_ops_instance.get_customer_by_id(customer_id):
            raise HTTPException(status_code=404, detail="Customer not found.")
        
        success = _customer_ops_instance.delete_customer(customer_id) # Assumes cascade delete for cases is setup in DB
        if success:
            return {"success": True, "message": "Customer deleted."}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete customer (database error).")
    except HTTPException: raise
    except Exception as e:
        logging.error(f"API Error deleting customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/api/validate-directory")
async def validate_directory_api(data: dict):
    path = data.get("path")
    logging.debug(f"API: POST /api/validate-directory - Path: {path}")
    if not path: return {"valid": False, "message": "No path provided"}
    return {"valid": os.path.isdir(path), "message": "Directory exists" if os.path.isdir(path) else "Directory does not exist"}

@app.post("/api/create-directory")
async def create_directory_api(data: dict):
    # This endpoint remains problematic as create_directory uses simpledialog
    # It will only work if the API server environment has a GUI available.
    suggested_name = data.get("suggested_name", "new_customer")
    logging.info(f"API: POST /api/create-directory - Name: {suggested_name}")
    if not _tk_root: # Check if Tkinter is available
         raise HTTPException(status_code=501, detail="Directory creation via API requires GUI environment (due to dialog).")
    try:
        new_dir = _customer_ops_instance.create_directory(suggested_name)
        if new_dir: return {"success": True, "directory": new_dir}
        else: raise HTTPException(status_code=500, detail="Failed to create directory (dialog cancelled or error).")
    except Exception as e:
         logging.error(f"API Error creating directory: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/api/open-directory/{customer_id}")
async def open_customer_directory_api(customer_id: str):
    logging.info(f"API: POST /api/open-directory/{customer_id}")
    try:
        customer_data = _customer_ops_instance.get_customer_by_id(customer_id)
        if not customer_data: raise HTTPException(status_code=404, detail="Customer not found.")
        directory = customer_data.get('directory')
        if not directory: raise HTTPException(status_code=400, detail="Customer has no directory.")
        
        # Use the utility function directly - this is OS dependent
        open_directory(directory)
        return {"success": True, "message": f"Attempted to open directory: {directory}"}
    except HTTPException: raise
    except Exception as e:
        logging.error(f"API Error opening directory for {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Test Execution Endpoints (remain the same) ---
# (Helper functions, /api/run-test, run_test_background, cleanup_test_events,
# /api/test-events, event_generator, EventSourceResponse omitted for brevity - assume they are correct)
async def send_event(queue, message, event_type=None, event_data=None):
     # ... implementation ...
     pass
async def with_error_handling(queue, func, *args, **kwargs):
     # ... implementation ...
     pass
@app.post("/api/run-test")
async def run_test(test_request: TestRequest):
     # ... implementation ...
     pass
async def run_test_background(test_id, test_name, enable_screenshots=True, real_mode=False):
     # ... implementation ...
     pass
async def cleanup_test_events(test_id, delay):
     # ... implementation ...
     pass
@app.get("/api/test-events/{test_id}")
async def test_events(test_id: str):
     # ... implementation ...
     pass
async def event_generator(test_id: str):
     # ... implementation ...
     pass
class EventSourceResponse(starlette.responses.StreamingResponse):
     # ... implementation ...
     pass

# --- Main Execution ---
if __name__ == "__main__":
    logging.info("Starting FastAPI server for Customer Management API...")
    uvicorn.run("web_wrapper:app", host="127.0.0.1", port=5002, reload=True) # Use string for reload
