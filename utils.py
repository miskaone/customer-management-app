import os
import json # Keep json import for potential future use, though load/save removed
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import logging
import logging.handlers # For file logging

# --- Logging Setup ---
LOG_FILENAME = 'app.log'
LOG_LEVEL = logging.INFO # Default level

def setup_logging(log_to_file=True, level=LOG_LEVEL):
    """Configures logging for the application."""
    log_format = '%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    handlers = [logging.StreamHandler()] # Log to console by default

    if log_to_file:
        try:
            # Use RotatingFileHandler to limit log file size
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_FILENAME, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            handlers.append(file_handler)
            print(f"Logging to file: {os.path.abspath(LOG_FILENAME)}") # Print log file location
        except Exception as e:
            print(f"Error setting up file logging: {e}") # Print error if file logging fails

    logging.basicConfig(level=level, format=log_format, datefmt=date_format, handlers=handlers)
    logging.info("Logging configured.")

# --- Obsolete JSON Functions (Removed) ---
# def load_json_file(file_path, default_value=None): ...
# def save_json_file(file_path, data): ...

# --- Existing Utility Functions ---
def format_timestamp(timestamp=None, format_str=None):
    """Return a formatted timestamp
    
    Args:
        timestamp: Optional timestamp (datetime object or ISO string) to format (defaults to current time)
        format_str: Optional format string (defaults to ISO format)
    """
    dt = None
    if timestamp is None:
        dt = datetime.now()
    elif isinstance(timestamp, datetime):
         dt = timestamp
    elif isinstance(timestamp, str):
         try:
             dt = datetime.fromisoformat(timestamp)
         except ValueError:
             logging.warning(f"Could not parse timestamp string: {timestamp}")
             return timestamp # Return original string if parsing fails
    elif isinstance(timestamp, (int, float)):
         try:
             dt = datetime.fromtimestamp(timestamp)
         except ValueError:
              logging.warning(f"Could not convert timestamp float/int: {timestamp}")
              return str(timestamp) # Return original number as string
    else:
         logging.warning(f"Unsupported timestamp type for formatting: {type(timestamp)}")
         return str(timestamp) # Return string representation

    if dt is None: return "" # Should not happen if logic above is correct

    try:
        if format_str:
            return dt.strftime(format_str)
        return dt.isoformat() # Default to ISO format
    except Exception as e:
        logging.error(f"Error formatting datetime object {dt}: {e}")
        return str(dt) # Fallback to string representation of datetime


def open_directory(directory):
    """Open a directory in the system file explorer."""
    if not directory or not os.path.exists(directory):
         logging.error(f"Cannot open directory - path does not exist or is None: {directory}")
         messagebox.showerror("Error", f"Directory path not found:\n{directory}")
         return
         
    logging.info(f"Opening directory: {directory}")
    try:
        if os.name == 'nt':  # Windows
            os.startfile(os.path.realpath(directory)) # Use realpath for safety
        elif sys.platform == 'darwin': # macOS
             import subprocess
             subprocess.check_call(['open', directory])
        else: # Linux and other POSIX
            import subprocess
            subprocess.check_call(['xdg-open', directory])
    except FileNotFoundError:
         logging.error(f"File explorer command not found for opening directory: {directory}")
         messagebox.showerror("Error", "Could not find a suitable command to open the directory.")
    except Exception as e:
        logging.error(f"Failed to open directory '{directory}': {e}")
        messagebox.showerror("Error", f"Failed to open directory:\n{e}")

def generate_unique_filename(base_dir, base_name, extension):
    """Generate a unique filename with incrementing number if file exists."""
    # Ensure extension doesn't start with a dot if base_name already has one
    if extension.startswith('.'):
        extension = extension[1:]
        
    filename = f"{base_name}.{extension}"
    full_path = os.path.join(base_dir, filename)
    counter = 1
    
    while os.path.exists(full_path):
        filename = f"{base_name}_{counter}.{extension}"
        full_path = os.path.join(base_dir, filename)
        counter += 1
        if counter > 1000: # Safety break
             logging.error("Could not generate unique filename after 1000 attempts.")
             # Consider raising an error or returning a timestamped name
             return f"{base_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
             
    return filename

# Need sys import for platform check in open_directory
import sys
