import os
import configparser
import shutil
import zipfile
import io  # Import BytesIO for in-memory zip creation
from datetime import datetime

# Load configuration
config = configparser.ConfigParser()
config_file_path = "conf/conf.cfg"
config.read(config_file_path)

# Parse Paths and Backup settings
backup_destination = os.path.expandvars(config.get("Paths", "backup_destination", fallback="D:/Backup"))
backup_format = config.get("Backup", "format", fallback="zip").lower()
max_backups = int(config.get("Backup", "max_backups", fallback="5"))
session_format = config.get("Backup", "session_format", fallback="zip").lower()  # New setting for session format

# Ensure the main backup destination exists
os.makedirs(backup_destination, exist_ok=True)

# Define the log file location within the backup destination
log_file = os.path.join(backup_destination, "backup_log.txt")

# Logging function
def log(message):
    with open(log_file, 'a') as logf:
        logf.write(f"{datetime.now()}: {message}\n")
    print(message)  # Also print to console for immediate feedback

# Function to enforce backup retention limit
def enforce_backup_limit():
    """Ensure that only the latest 'max_backups' number of backups are retained."""
    backups = sorted(
        (entry for entry in os.listdir(backup_destination) if entry.startswith("backup_") and entry.endswith(".zip")),
        key=lambda entry: os.path.getmtime(os.path.join(backup_destination, entry))
    )
    if len(backups) > max_backups:
        excess_backups = len(backups) - max_backups
        for old_backup in backups[:excess_backups]:
            backup_path = os.path.join(backup_destination, old_backup)
            os.remove(backup_path)
            log(f"Removed old backup: {backup_path}")

# Parse folder list from config
def read_folders():
    """Parse the folder list from the config file."""
    folders = []
    try:
        folder_list = config.get("Folders", "folders")
        # Split by semicolon and process each entry
        folder_entries = folder_list.split(";")
        for entry in folder_entries:
            entry = entry.strip()
            if entry:
                folder_path, recursive_flag = map(str.strip, entry.rsplit(',', 1))
                recursive = recursive_flag.upper() == 'R'
                folders.append((folder_path, recursive))
                log(f"Loaded folder '{folder_path}' with recursive setting '{recursive_flag}'")
    except (ValueError, configparser.NoOptionError) as e:
        log(f"Error reading folders: {e}")
    return folders

folders_to_backup = read_folders()

# Create a timestamped backup session name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_session_name = f"backup_{timestamp}.zip"
backup_session_path = os.path.join(backup_destination, backup_session_name)

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
        
        # Use BytesIO for in-memory zip
        folder_zip_bytes = io.BytesIO()
        with zipfile.ZipFile(folder_zip_bytes, 'w', zipfile.ZIP_DEFLATED) as folder_zip:
            for root, dirs, files in os.walk(folder_path):
                log(f"Zipping folder '{root}'")  # Log each folder being zipped
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    folder_zip.write(file_path, arcname)
                    log(f"Added '{file_path}' to zip as '{arcname}'")  # Log each file added to the zip
                if not recursive:
                    break
            
            # Write the in-memory folder zip to the main session zip
            folder_zip_bytes.seek(0)  # Reset pointer to the beginning of the BytesIO buffer
            zipf.writestr(folder_zip_filename, folder_zip_bytes.read())
            log(f"Added '{folder_zip_filename}' to main backup zip")

    except Exception as e:
        log(f"Error backing up '{folder_path}': {e}")

# Execute backup operation
log("Starting backup operation...")

# Create a single zip file for the backup session
with zipfile.ZipFile(backup_session_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for folder_path, is_recursive in folders_to_backup:
        log(f"Processing folder '{folder_path}' (Recursive: {is_recursive})")
        backup_folder(zipf, folder_path, is_recursive)

# Enforce the backup retention limit after creating the backup
enforce_backup_limit()

log("Backup operation completed.")
print("Backup operation completed. Check the log for details.")
