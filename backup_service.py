import os
import configparser
import shutil
import zipfile
import io  # Import BytesIO for in-memory zip creation
from datetime import datetime

print("Script starting...")
print(f"Current working directory: {os.getcwd()}")

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"Script directory: {SCRIPT_DIR}")

# Load configuration
config = configparser.ConfigParser()
config_file_path = os.path.join(SCRIPT_DIR, "conf", "conf.cfg")
print(f"Looking for config file at: {config_file_path}")

if not os.path.exists(config_file_path):
    print(f"ERROR: Config file not found at: {config_file_path}")
    raise FileNotFoundError(f"Config file not found at: {config_file_path}")

print(f"Reading config file...")
try:
    with open(config_file_path, 'r', encoding='utf-8') as f:
        print("Raw config content:")
        raw_content = f.read()
        print(raw_content)
except Exception as e:
    print(f"Error reading config file: {str(e)}")
    raise

print("Parsing config file...")
read_files = config.read(config_file_path, encoding='utf-8')
print(f"Files read by ConfigParser: {read_files}")
print(f"Available sections: {config.sections()}")

try:
    # Parse Paths and Backup settings
    print("\nReading configuration values:")
    backup_destination = os.path.expandvars(config.get("Paths", "backup_destination", fallback="D:/Backup"))
    print(f"Backup destination: {backup_destination}")
    
    backup_format = config.get("Backup", "format", fallback="zip").lower()
    print(f"Backup format: {backup_format}")
    
    max_backups = int(config.get("Backup", "max_backups", fallback="5"))
    print(f"Max backups: {max_backups}")
    
    session_format = config.get("Backup", "session_format", fallback="zip").lower()
    print(f"Session format: {session_format}")
except Exception as e:
    print(f"Error parsing configuration values: {str(e)}")
    raise

# Ensure the main backup destination exists
try:
    os.makedirs(backup_destination, exist_ok=True)
    print(f"Backup destination directory ensured: {backup_destination}")
except Exception as e:
    print(f"Error creating backup destination: {str(e)}")
    raise

# Define the log file location within the backup destination
log_file = os.path.join(backup_destination, "backup_log.txt")
print(f"Log file path: {log_file}")

# Logging function
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp}: {message}"
    print(log_message)
    try:
        with open(log_file, 'a') as logf:
            logf.write(log_message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {str(e)}")

# Function to enforce backup retention limit
def enforce_backup_limit():
    """Ensure that only the latest 'max_backups' number of backups are retained."""
    try:
        backups = sorted(
            (entry for entry in os.listdir(backup_destination) 
             if entry.startswith("backup_") and entry.endswith(".zip")),
            key=lambda entry: os.path.getmtime(os.path.join(backup_destination, entry))
        )
        print(f"Found {len(backups)} existing backups")
        
        if len(backups) > max_backups:
            excess_backups = len(backups) - max_backups
            for old_backup in backups[:excess_backups]:
                backup_path = os.path.join(backup_destination, old_backup)
                os.remove(backup_path)
                log(f"Removed old backup: {backup_path}")
    except Exception as e:
        print(f"Error in enforce_backup_limit: {str(e)}")
        log(f"Error in enforce_backup_limit: {str(e)}")

# Parse folder list from config
def read_folders():
    """Parse the folder list from the config file."""
    print("\nReading folders configuration:")
    folders = []
    try:
        print(f"Available sections: {config.sections()}")
        print("Attempting to read 'folders' from 'Folders' section")
        
        if 'Folders' not in config.sections():
            print("ERROR: 'Folders' section not found in config!")
            raise configparser.NoSectionError('Folders')
            
        folder_list = config.get("Folders", "folders")
        print(f"Raw folder list: {folder_list}")
        
        # Split by semicolon and process each entry
        folder_entries = folder_list.split(";")
        for entry in folder_entries:
            entry = entry.strip()
            if entry:
                print(f"Processing entry: {entry}")
                folder_path, recursive_flag = map(str.strip, entry.rsplit(',', 1))
                recursive = recursive_flag.upper() == 'R'
                folders.append((folder_path, recursive))
                log(f"Loaded folder '{folder_path}' with recursive setting '{recursive_flag}'")
    except Exception as e:
        print(f"Error reading folders: {str(e)}")
        log(f"Error reading folders: {str(e)}")
    
    print(f"Final folders list: {folders}")
    return folders

print("\nStarting folder reading...")
folders_to_backup = read_folders()
print(f"Folders to backup: {folders_to_backup}")

# Create a timestamped backup session name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_session_name = f"backup_{timestamp}.zip"
backup_session_path = os.path.join(backup_destination, backup_session_name)
print(f"Backup session path: {backup_session_path}")

# Perform backup
def backup_folder(zipf, folder_path, recursive):
    if not os.path.exists(folder_path):
        log(f"Error: Folder '{folder_path}' does not exist. Skipping backup.")
        return

    try:
        log(f"Starting backup for '{folder_path}' (Recursive: {recursive})")

        # Create an in-memory zip for the individual folder
        folder_name = os.path.basename(folder_path.strip('/\\'))
        folder_zip_filename = f"{folder_name}.zip"
        print(f"Processing folder: {folder_name}")
        
        # Use BytesIO for in-memory zip
        folder_zip_bytes = io.BytesIO()
        with zipfile.ZipFile(folder_zip_bytes, 'w', zipfile.ZIP_DEFLATED) as folder_zip:
            for root, dirs, files in os.walk(folder_path):
                log(f"Zipping folder '{root}'")
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    folder_zip.write(file_path, arcname)
                    log(f"Added '{file_path}' to zip as '{arcname}'")
                if not recursive:
                    break
            
            # Write the in-memory folder zip to the main session zip
            folder_zip_bytes.seek(0)
            zipf.writestr(folder_zip_filename, folder_zip_bytes.read())
            log(f"Added '{folder_zip_filename}' to main backup zip")

    except Exception as e:
        print(f"Error backing up '{folder_path}': {str(e)}")
        log(f"Error backing up '{folder_path}': {str(e)}")

# Execute backup operation
log("Starting backup operation...")

try:
    # Create a single zip file for the backup session
    with zipfile.ZipFile(backup_session_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder_path, is_recursive in folders_to_backup:
            log(f"Processing folder '{folder_path}' (Recursive: {is_recursive})")
            backup_folder(zipf, folder_path, is_recursive)

    # Enforce the backup retention limit after creating the backup
    enforce_backup_limit()

    log("Backup operation completed.")
    print("Backup operation completed. Check the log for details.")
    
except Exception as e:
    error_msg = f"Critical error during backup operation: {str(e)}"
    print(error_msg)
    log(error_msg)
    raise