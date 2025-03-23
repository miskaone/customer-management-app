import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime

def load_json_file(file_path, default_value=None):
    """Load data from a JSON file"""
    if default_value is None:
        default_value = []
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            return default_value
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data from {file_path}: {str(e)}")
        return default_value

def save_json_file(file_path, data):
    """Save data to a JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save data to {file_path}: {str(e)}")
        return False

def format_timestamp(timestamp=None, format_str=None):
    """Return a formatted timestamp
    
    Args:
        timestamp: Optional timestamp to format (defaults to current time)
        format_str: Optional format string (defaults to ISO format)
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)
    
    if format_str:
        return dt.strftime(format_str)
    return dt.isoformat()

def open_directory(directory):
    """Open a directory in the system file explorer"""
    try:
        if os.name == 'nt':  # Windows
            os.startfile(directory)
        elif os.name == 'posix':  # macOS, Linux
            import subprocess
            subprocess.Popen(['open', directory])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open directory: {str(e)}")

def generate_unique_filename(base_dir, base_name, extension):
    """Generate a unique filename with incrementing number if file exists"""
    filename = f"{base_name}.{extension}"
    counter = 1
    
    while os.path.exists(os.path.join(base_dir, filename)):
        filename = f"{base_name}_{counter}.{extension}"
        counter += 1
        
    return filename
