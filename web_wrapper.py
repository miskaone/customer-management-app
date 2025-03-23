"""
Web Wrapper for Customer Management App
Provides a simple web interface to interact with the Customer Management App
for testing with Playwright MCP server
"""
import json
import threading
import tkinter as tk
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, List
from customer_manager import CustomerManager
import os
import sys
import importlib.util
from datetime import datetime
import asyncio
import starlette
import random

# Import the PlaywrightTester class from playwright_tests.py
try:
    # Try direct import first
    from playwright_tests import PlaywrightTester
except ImportError:
    # If direct import fails, load the module dynamically
    module_path = os.path.join(os.path.dirname(__file__), 'playwright_tests.py')
    spec = importlib.util.spec_from_file_location("playwright_tests", module_path)
    playwright_tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(playwright_tests)
    PlaywrightTester = playwright_tests.PlaywrightTester

# Models for request validation
class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    directory: Optional[str] = None
    create_directory: Optional[bool] = False

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Customer Management App - Web Interface</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1, h2 { color: #2196F3; }
        form { margin-bottom: 20px; padding: 15px; background: #f8f8f8; border-radius: 5px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 8px; margin-bottom: 10px; box-sizing: border-box; }
        button { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        tr:hover { background-color: #f5f5f5; }
        .delete-button { padding: 5px 10px; background: #f44336; color: white; border: none; cursor: pointer; }
        .error { color: #f44336; font-weight: bold; }
        .success { color: #4CAF50; font-weight: bold; }
        nav { margin-bottom: 20px; background: #f8f8f8; padding: 10px; }
        nav a { margin-right: 15px; text-decoration: none; color: #333; font-weight: bold; }
        nav a:hover { color: #2196F3; }
    </style>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/tests">Tests</a>
        <a href="/screenshots">Screenshots</a>
    </nav>

    <h1>Customer Management App - Web Interface</h1>
    
    <form id="addCustomerForm" action="/api/customers" method="post">
        <h2>Add New Customer</h2>
        <div>
            <label for="name">Customer Name:</label>
            <input type="text" id="name" name="name" required>
        </div>
        <div>
            <label for="directory">Directory:</label>
            <input type="text" id="directory" name="directory" required>
        </div>
        <button type="submit">Add Customer</button>
        <div id="formMessage"></div>
    </form>
    
    <h2>Customer List</h2>
    <table id="customerTable">
        <thead>
            <tr>
                <th>Name</th>
                <th>Directory</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="customerList">
            <!-- Customer data will be loaded here -->
        </tbody>
    </table>
    
    <script>
        // Function to fetch and display customers
        function fetchCustomers() {
            fetch('/api/customers')
                .then(response => response.json())
                .then(customers => {
                    const customerList = document.getElementById('customerList');
                    customerList.innerHTML = '';
                    
                    customers.forEach(customer => {
                        const row = document.createElement('tr');
                        
                        const nameCell = document.createElement('td');
                        nameCell.textContent = customer.name;
                        row.appendChild(nameCell);
                        
                        const directoryCell = document.createElement('td');
                        directoryCell.textContent = customer.directory;
                        row.appendChild(directoryCell);
                        
                        const actionsCell = document.createElement('td');
                        const deleteButton = document.createElement('button');
                        deleteButton.textContent = 'Delete';
                        deleteButton.className = 'delete-button';
                        deleteButton.addEventListener('click', () => {
                            if (confirm(`Are you sure you want to delete ${customer.name}?`)) {
                                deleteCustomer(customer.id);
                            }
                        });
                        actionsCell.appendChild(deleteButton);
                        row.appendChild(actionsCell);
                        
                        customerList.appendChild(row);
                    });
                })
                .catch(error => {
                    console.error('Error fetching customers:', error);
                });
        }
        
        // Function to delete a customer
        function deleteCustomer(customerId) {
            fetch(`/api/customers/${customerId}`, {
                method: 'DELETE',
            })
            .then(response => {
                if (response.ok) {
                    fetchCustomers();
                } else {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Failed to delete customer');
                    });
                }
            })
            .catch(error => {
                console.error('Error deleting customer:', error);
                alert('Error: ' + error.message);
            });
        }
        
        // Handle form submission
        document.getElementById('addCustomerForm').addEventListener('submit', function(event) {
            event.preventDefault();
            
            const name = document.getElementById('name').value;
            const directory = document.getElementById('directory').value;
            const formMessage = document.getElementById('formMessage');
            
            // Validate inputs
            if (!name) {
                formMessage.textContent = 'Error: Name is required.';
                formMessage.className = 'error';
                return;
            }
            
            if (!directory) {
                formMessage.textContent = 'Error: Directory is required.';
                formMessage.className = 'error';
                return;
            }
            
            // Submit the form data
            fetch('/api/customers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    directory: directory,
                }),
            })
            .then(response => {
                if (response.ok) {
                    document.getElementById('name').value = '';
                    document.getElementById('directory').value = '';
                    formMessage.textContent = 'Customer added successfully!';
                    formMessage.className = 'success';
                    fetchCustomers();
                    setTimeout(() => {
                        formMessage.textContent = '';
                    }, 3000);
                } else {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Failed to add customer');
                    });
                }
            })
            .catch(error => {
                console.error('Error adding customer:', error);
                formMessage.textContent = 'Error: ' + error.message;
                formMessage.className = 'error';
            });
        });
        
        // Load customers when the page loads
        document.addEventListener('DOMContentLoaded', fetchCustomers);
    </script>
</body>
</html>
"""

# HTML template for the testing page
TESTING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Customer Management App - Testing</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1, h2 { color: #2196F3; }
        nav { margin-bottom: 20px; background: #f8f8f8; padding: 10px; }
        nav a { margin-right: 15px; text-decoration: none; color: #333; font-weight: bold; }
        nav a:hover { color: #2196F3; }
        .test-controls { 
            background: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px;
            margin-bottom: 20px;
        }
        select, button { 
            padding: 8px; 
            margin: 5px 0; 
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        button { 
            background: #2196F3; 
            color: white; 
            border: none;
            cursor: pointer; 
            padding: 8px 15px;
        }
        button:hover { background: #0b7dda; }
        #output { 
            background: #f8f8f8; 
            padding: 10px; 
            border-radius: 3px; 
            border: 1px solid #ddd;
            white-space: pre-wrap;
            font-family: monospace;
            height: 300px;
            overflow-y: auto;
            margin-top: 10px;
        }
        #events {
            background: #f8f8f8; 
            padding: 10px; 
            border-radius: 3px; 
            border: 1px solid #ddd;
            white-space: pre-wrap;
            font-family: monospace;
            height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }
        .status {
            margin: 10px 0;
            padding: 10px;
            border-radius: 3px;
        }
        .success { background: #e8f5e9; color: #2e7d32; }
        .error { background: #ffebee; color: #c62828; }
        .warning { background: #fff8e1; color: #f57f17; }
        .info { background: #e3f2fd; color: #1565c0; }
        .options-group {
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .copy-container {
            position: relative;
        }
        .copy-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            padding: 5px 8px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .copy-btn:hover {
            background: #e0e0e0;
        }
    </style>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/tests">Tests</a>
        <a href="/screenshots">Screenshots</a>
    </nav>

    <h1>Interactive Testing</h1>
    
    <div class="test-controls">
        <h2>Run a Test</h2>
        <select id="testSelect">
            <option value="">Select a test...</option>
            <option value="basic_navigation">Basic Navigation</option>
            <option value="add_customer">Add Customer</option>
            <option value="edit_customer">Edit Customer</option>
            <option value="delete_customer">Delete Customer</option>
            <option value="search_customer">Search for Customer</option>
        </select>
        
        <div class="options-group">
            <div class="checkbox-container">
                <input type="checkbox" id="enableScreenshots" checked>
                <label for="enableScreenshots">Enable Screenshots</label>
            </div>
        </div>
        
        <button id="runTestBtn">Run Test</button>
    </div>
    
    <div id="statusContainer" style="display: none;" class="status"></div>
    
    <div id="eventsContainer" style="display: none;">
        <h2>Test Events</h2>
        <div class="copy-container">
            <button class="copy-btn" id="copyEventsBtn">Copy</button>
            <pre id="events"></pre>
        </div>
    </div>
    
    <div id="outputContainer">
        <h2>Test Output</h2>
        <div class="copy-container">
            <button class="copy-btn" id="copyOutputBtn">Copy</button>
            <pre id="output">Select a test and click "Run Test" to begin testing.</pre>
        </div>
    </div>
    
    <script>
        document.getElementById('copyOutputBtn').addEventListener('click', function() {
            navigator.clipboard.writeText(document.getElementById('output').textContent)
                .then(function() {
                    var originalText = this.textContent;
                    this.textContent = 'Copied!';
                    var btn = this;
                    setTimeout(function() {
                        btn.textContent = originalText;
                    }, 2000);
                }.bind(this))
                .catch(function(err) {
                    console.error('Failed to copy: ', err);
                });
        });
        
        document.getElementById('copyEventsBtn').addEventListener('click', function() {
            navigator.clipboard.writeText(document.getElementById('events').textContent)
                .then(function() {
                    var originalText = this.textContent;
                    this.textContent = 'Copied!';
                    var btn = this;
                    setTimeout(function() {
                        btn.textContent = originalText;
                    }, 2000);
                }.bind(this))
                .catch(function(err) {
                    console.error('Failed to copy: ', err);
                });
        });
        
        document.getElementById('runTestBtn').addEventListener('click', function() {
            var testName = document.getElementById('testSelect').value;
            var enableScreenshots = document.getElementById('enableScreenshots').checked;
            var statusContainer = document.getElementById('statusContainer');
            var eventsContainer = document.getElementById('eventsContainer');
            var events = document.getElementById('events');
            var output = document.getElementById('output');
            
            if (!testName) {
                alert('Please select a test to run');
                return;
            }
            
            // Clear previous test results
            events.textContent = '';
            output.textContent = 'Running test: ' + testName + '...';
            eventsContainer.style.display = 'none';
            
            // Show starting status
            statusContainer.textContent = 'Starting test: ' + testName + '...';
            statusContainer.className = 'status info';
            statusContainer.style.display = 'block';
            
            // Make the API request
            fetch('/api/run-test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    test: testName,
                    enable_screenshots: enableScreenshots
                })
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.test_id) {
                    statusContainer.textContent = 'Test started: ' + data.message;
                    
                    // Subscribe to events
                    var eventSource = new EventSource('/api/test-events/' + data.test_id);
                    
                    eventSource.onmessage = function(e) {
                        try {
                            if (e.data && e.data !== 'undefined') {
                                var eventData = JSON.parse(e.data);
                                if (eventData && eventData.message) {
                                    events.textContent += eventData.message + '\n';
                                    eventsContainer.style.display = 'block';
                                    events.scrollTop = events.scrollHeight;
                                }
                            }
                        } catch (err) {
                            console.error('Error parsing event data:', err);
                        }
                    };
                    
                    eventSource.addEventListener('complete', function(e) {
                        try {
                            if (e.data && e.data !== 'undefined') {
                                var eventData = JSON.parse(e.data);
                                statusContainer.textContent = 'Test completed: ' + (eventData.result || 'Done');
                                statusContainer.className = 'status success';
                            } else {
                                statusContainer.textContent = 'Test completed';
                                statusContainer.className = 'status success';
                            }
                        } catch (err) {
                            console.error('Error parsing complete event:', err);
                            statusContainer.textContent = 'Test completed';
                            statusContainer.className = 'status success';
                        }
                        eventSource.close();
                    });
                    
                    eventSource.addEventListener('error', function(e) {
                        try {
                            if (e.data && e.data !== 'undefined') {
                                var eventData = JSON.parse(e.data);
                                statusContainer.textContent = 'Test failed: ' + (eventData.error || 'Unknown error');
                            } else {
                                statusContainer.textContent = 'Test failed';
                            }
                        } catch (err) {
                            console.error('Error parsing error event:', err);
                            statusContainer.textContent = 'Test failed';
                        }
                        statusContainer.className = 'status error';
                        eventSource.close();
                    });
                    
                    eventSource.onerror = function(e) {
                        statusContainer.textContent = 'Error receiving test events';
                        statusContainer.className = 'status error';
                        console.error('EventSource error:', e);
                        eventSource.close();
                    };
                } else {
                    statusContainer.textContent = 'Error: ' + (data.detail || 'Unknown error');
                    statusContainer.className = 'status error';
                }
            })
            .catch(function(error) {
                statusContainer.textContent = 'Error: ' + error.message;
                statusContainer.className = 'status error';
                output.textContent = 'Error: ' + error.message;
            });
        });
    </script>
</body>
</html>
"""

# CSS for the screenshots gallery
SCREENSHOTS_CSS = """
    body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
    h1, h2 { color: #2196F3; }
    nav { margin-bottom: 20px; background: #f8f8f8; padding: 10px; }
    nav a { margin-right: 15px; text-decoration: none; color: #333; font-weight: bold; }
    nav a:hover { color: #2196F3; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
    th { background-color: #f2f2f2; }
    tr:hover { background-color: #f5f5f5; }
    .view-button { 
        padding: 5px 10px;
        background: #2196F3;
        color: white;
        text-decoration: none;
        border-radius: 3px;
    }
    .view-button:hover { background: #0b7dda; }
    .empty-gallery { 
        padding: 50px; 
        text-align: center; 
        color: #777; 
        background: #f8f8f8;
        border-radius: 5px;
        margin-top: 20px;
    }
"""

# HTML template for the screenshots gallery page (without CSS)
SCREENSHOTS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Screenshots Gallery</title>
    <style>
    {css}
    </style>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/tests">Tests</a>
        <a href="/screenshots">Screenshots</a>
    </nav>

    <h1>Test Screenshots Gallery</h1>
    
    {content}
</body>
</html>
"""

# Global app data storage
app_data = {
    'customers': {},
    'app_instance': None,
    'test_events': {},  # Store for test events by test_id
    'active_tests': {}  # Store for active test runs
}

# Initialize FastAPI
app = FastAPI(title="Customer Management App API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root API route returns the web interface
@app.get("/", response_class=HTMLResponse)
async def index():
    """Render the main page"""
    return HTML_TEMPLATE

@app.get("/tests", response_class=HTMLResponse)
async def tests_page():
    """Render the testing page"""
    return TESTING_TEMPLATE

@app.get("/screenshots")
async def screenshots_page():
    """Show the screenshot gallery page"""
    screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
    
    # Create directory if it doesn't exist
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        
    # Get list of screenshot files sorted by modification time (newest first)
    screenshot_files = []
    try:
        for file in os.listdir(screenshots_dir):
            if file.endswith('.html'):
                file_path = os.path.join(screenshots_dir, file)
                mod_time = os.path.getmtime(file_path)
                screenshot_files.append({
                    'name': file.replace('.html', ''),
                    'path': f"/screenshots/{file}",
                    'mod_time': mod_time,
                    'date': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                })
    except Exception as e:
        # If there's any error, log it and continue with empty list
        print(f"Error reading screenshots directory: {str(e)}")
    
    # Sort by modification time (newest first)
    screenshot_files.sort(key=lambda x: x['mod_time'], reverse=True)
    
    # Generate table rows for screenshots or show empty message
    if screenshot_files:
        screenshot_rows = []
        for i, s in enumerate(screenshot_files):
            screenshot_rows.append(f"""
            <tr>
                <td>{i+1}</td>
                <td>{s['name']}</td>
                <td>{s['date']}</td>
                <td><a href="{s['path']}" target="_blank" class="view-button">View</a></td>
            </tr>
            """)
        
        content_html = f"""
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Screenshot Name</th>
                    <th>Date Taken</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {"".join(screenshot_rows)}
            </tbody>
        </table>
        """
    else:
        content_html = """
        <div class="empty-gallery">
            <h2>No Screenshots Available</h2>
            <p>Run some tests to generate screenshots that will appear here.</p>
        </div>
        """
    
    # Format the full template with the content and CSS
    html_content = SCREENSHOTS_TEMPLATE.format(css=SCREENSHOTS_CSS, content=content_html)
    return HTMLResponse(html_content)

@app.get("/screenshots/{filename}")
async def serve_screenshot(filename: str):
    """Serve a screenshot file"""
    screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
    return FileResponse(os.path.join(screenshots_dir, filename))

# Test-related models
class TestRequest(BaseModel):
    test: str
    enable_screenshots: Optional[bool] = True

@app.post("/api/run-test")
async def run_test(test_request: TestRequest):
    """API endpoint to run a test"""
    test_name = test_request.test
    enable_screenshots = test_request.enable_screenshots
    
    if not test_name:
        raise HTTPException(status_code=400, detail="Missing test name")
    
    # Generate a unique test ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_id = f"test_{timestamp}_{random.randint(100, 999)}"
    
    # Initialize event queue for this test
    app_data['test_events'][test_id] = asyncio.Queue()
    
    # Start test in background task
    asyncio.create_task(run_test_background(test_id, test_name, enable_screenshots))
    
    return {
        "status": "started",
        "message": f"Test '{test_name}' started",
        "test_id": test_id
    }

async def run_test_background(test_id, test_name, enable_screenshots=True):
    """Run a test in the background and publish events"""
    queue = app_data['test_events'][test_id]
    
    try:
        # Initialize tester with screenshot preference
        tester = PlaywrightTester(mock_mode=True, enable_screenshots=enable_screenshots)
        
        # Set up event handler
        def event_callback(message):
            asyncio.create_task(queue.put({"message": message}))
        
        tester.set_callback(event_callback)
        
        # Run the test
        await queue.put({"message": f"Starting test: {test_name}"})
        await queue.put({"message": f"Screenshots {'enabled' if enable_screenshots else 'disabled'}"})
        
        if test_name == "basic_navigation":
            result = tester.test_basic_navigation()
        elif test_name == "add_customer":
            result = tester.test_add_customer()
        elif test_name == "edit_customer":
            result = tester.test_edit_customer()
        elif test_name == "delete_customer":
            result = tester.test_delete_customer()
        elif test_name == "search_customer":
            result = tester.test_search_customer()
        else:
            await queue.put({"message": f"Unknown test: {test_name}"})
            await queue.put({"type": "error", "error": f"Unknown test: {test_name}"})
            return
        
        # Report completion
        if result:
            await queue.put({"message": f"Test completed successfully"})
            await queue.put({"type": "complete", "result": "Test completed successfully"})
        else:
            await queue.put({"message": f"Test failed"})
            await queue.put({"type": "error", "error": "Test failed"})
    
    except Exception as e:
        error_message = f"Error running test: {str(e)}"
        await queue.put({"message": error_message})
        await queue.put({"type": "error", "error": error_message})
    
    finally:
        # Keep test events for a while before cleanup
        asyncio.create_task(cleanup_test_events(test_id, delay=300))

async def cleanup_test_events(test_id, delay):
    await asyncio.sleep(delay)
    if test_id in app_data['test_events']:
        del app_data['test_events'][test_id]

@app.get("/api/test-events/{test_id}")
async def test_events(test_id: str):
    """Server-sent events endpoint for test progress updates"""
    if test_id not in app_data['test_events']:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    return EventSourceResponse(event_generator(test_id))

async def event_generator(test_id: str):
    """Generate SSE events for a test run"""
    try:
        # Set up the queue reference
        queue = app_data['test_events'][test_id]
        
        # Send initial connected event
        yield "data: " + json.dumps({"message": "Connected to event stream"}) + "\n\n"
        
        # Loop to process events from the queue
        while True:
            try:
                # Wait for an event with a timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                # Ensure event is a valid dict before serializing
                if isinstance(event, dict):
                    # Send the event as an SSE message
                    yield "data: " + json.dumps(event) + "\n\n"
                    
                    # If this is the completion event, we're done
                    if event.get("type") == "complete":
                        break
                else:
                    # If event is not a dict, serialize it as a message
                    yield "data: " + json.dumps({"message": str(event)}) + "\n\n"
                    
            except asyncio.TimeoutError:
                # Keep the connection alive with a comment
                yield ": keepalive\n\n"
                
    except asyncio.CancelledError:
        # Client disconnected
        pass
    
    finally:
        # Clean up after a delay
        await asyncio.sleep(5)
        if test_id in app_data['test_events']:
            del app_data['test_events'][test_id]

# Server-sent events response class
class EventSourceResponse(starlette.responses.StreamingResponse):
    """Server-Sent Events response"""
    
    def __init__(self, content, status_code=200, headers=None):
        if headers is None:
            headers = {}
        
        # Set required headers for SSE
        headers.setdefault("Cache-Control", "no-cache")
        headers.setdefault("Connection", "keep-alive")
        headers.setdefault("X-Accel-Buffering", "no")
        
        super().__init__(
            content=content, 
            status_code=status_code, 
            headers=headers, 
            media_type="text/event-stream"
        )

@app.get("/api/customers")
async def get_customers():
    """API endpoint to get all customers"""
    # Handle both list and dictionary formats for backward compatibility
    if isinstance(app_data['customers'], dict):
        return list(app_data['customers'].values())
    return app_data['customers']

@app.post("/api/customers")
async def add_customer(customer: CustomerCreate):
    """API endpoint to add a new customer"""
    try:
        # Validate required fields
        if not customer.name:
            return {"success": False, "message": "Name is required"}
        
        if not customer.directory:
            return {"success": False, "message": "Directory is required"}
        
        # Set Tkinter variables
        if app_data['app_instance']:
            app_data['app_instance'].name_var.set(customer.name)
            app_data['app_instance'].email_var.set(customer.email or '')
            app_data['app_instance'].phone_var.set(customer.phone or '')
            app_data['app_instance'].address_var.set(customer.address or '')
            app_data['app_instance'].dir_var.set(customer.directory)
            
            # Call save method
            success = app_data['app_instance'].save_customer()
            
            if success:
                # Refresh local data
                app_data['customers'] = app_data['app_instance'].customers
                return {"success": True}
            else:
                return {"success": False, "message": "Failed to save customer"}
        
        raise HTTPException(status_code=500, detail="App instance not running")
    except Exception as e:
        import traceback
        print(f"Error in add_customer: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}"}

@app.put("/api/customers/{customer_id}")
async def update_customer(customer_id: str, customer: CustomerUpdate):
    """API endpoint to update a customer"""
    if customer_id in app_data['customers'] and app_data['app_instance']:
        # Update customer data
        if customer.name:
            app_data['customers'][customer_id]['name'] = customer.name
        if customer.email:
            app_data['customers'][customer_id]['email'] = customer.email
        if customer.phone:
            app_data['customers'][customer_id]['phone'] = customer.phone
        if customer.address:
            app_data['customers'][customer_id]['address'] = customer.address
            
        app_data['app_instance'].save_customers()
        return {"success": True}
    
    raise HTTPException(status_code=404, detail="Customer not found")

@app.delete("/api/customers/{customer_id}")
async def delete_customer(customer_id: str):
    """API endpoint to delete a customer"""
    if customer_id in app_data['customers'] and app_data['app_instance']:
        # Delete the customer
        del app_data['customers'][customer_id]
        app_data['app_instance'].save_customers()
        return {"success": True}
    
    raise HTTPException(status_code=404, detail="Customer not found")

@app.post("/api/validate-directory")
async def validate_directory(data: dict):
    """API endpoint to validate if a directory exists"""
    path = data.get("path")
    if not path:
        return {"valid": False, "message": "No path provided"}
    
    # Check if directory exists
    if os.path.isdir(path):
        return {"valid": True, "directory": path}
    else:
        return {"valid": False, "message": "Directory does not exist"}

@app.post("/api/create-directory")
async def create_directory(data: dict):
    """API endpoint to create a new directory for a customer"""
    suggested_name = data.get("suggested_name", "new_customer")
    
    if app_data['app_instance']:
        # Use the app's create_directory method
        new_dir = app_data['app_instance'].customer_ops.create_directory(suggested_name)
        
        if new_dir:
            return {"success": True, "directory": new_dir}
        else:
            return {"success": False, "message": "Failed to create directory"}
    
    return {"success": False, "message": "App instance not running"}

@app.post("/api/open-directory/{customer_id}")
async def open_customer_directory(customer_id: str):
    """API endpoint to open a customer's directory"""
    try:
        if customer_id in app_data['customers'] and app_data['app_instance']:
            # Get the customer directory
            directory = app_data['customers'][customer_id].get('directory')
            if not directory:
                return {"success": False, "message": "No directory associated with this customer"}
            
            # Check if directory exists
            if not os.path.isdir(directory):
                return {"success": False, "message": f"Directory not found: {directory}"}
            
            # Open the directory using the app's method
            app_data['app_instance'].selected_customer_id_var.set(customer_id)
            success = app_data['app_instance'].open_customer_directory()
            
            if success:
                return {"success": True}
            else:
                return {"success": False, "message": "Failed to open directory"}
        else:
            return {"success": False, "message": "Customer not found"}
    except Exception as e:
        import traceback
        print(f"Error opening directory: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}"}

def run_fastapi():
    """Run the FastAPI app in a separate thread"""
    uvicorn.run(app, host="127.0.0.1", port=5001)

def main():
    """Main function to run both the web interface and Tkinter app"""
    # Start FastAPI in a separate thread
    api_thread = threading.Thread(target=run_fastapi)
    api_thread.daemon = True
    api_thread.start()
    
    # Run Tkinter on the main thread
    root = tk.Tk()
    app_instance = CustomerManager(root)
    app_data['app_instance'] = app_instance
    
    # Load initial customers
    app_data['customers'] = app_instance.customers
    
    root.mainloop()

if __name__ == "__main__":
    main()
