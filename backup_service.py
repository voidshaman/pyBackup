import os
import configparser
import shutil
import zipfile
import io
import tempfile
from datetime import datetime
import argparse
import json
from tqdm import tqdm
import hashlib
import json
from pathlib import Path
import time

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

    backup_type = config.get("Backup", "type", fallback="full").lower()  # 'full' or 'differential'
    full_backup_interval = int(config.get("Backup", "full_backup_interval", fallback="7"))  # days
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

def log(message):
    """Write a timestamped message to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp}: {message}"
    print(log_message)
    try:
        with open(log_file, 'a') as logf:
            logf.write(log_message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {str(e)}")

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

def verify_zip_content(zip_data):
    """Verify if the data is a valid zip file."""
    try:
        with io.BytesIO(zip_data) as data_stream:
            with zipfile.ZipFile(data_stream) as zf:
                return True
    except Exception as e:
        return False

# DIFFERENTIAL


def get_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_last_full_backup():
    """Find the most recent full backup and its manifest."""
    try:
        for entry in sorted(os.listdir(backup_destination), reverse=True):
            if entry.startswith("backup_full_"):
                manifest_path = os.path.join(backup_destination, entry.replace('.zip', '_manifest.json'))
                if os.path.exists(manifest_path):
                    return entry, manifest_path
        return None, None
    except Exception as e:
        log(f"Error finding last full backup: {str(e)}")
        return None, None

def should_create_full_backup():
    """Determine if a new full backup should be created."""
    last_full_backup, _ = get_last_full_backup()
    if not last_full_backup:
        return True
        
    last_full_time = os.path.getctime(os.path.join(backup_destination, last_full_backup))
    days_since_full = (time.time() - last_full_time) / (24 * 3600)
    return days_since_full >= full_backup_interval

def count_files(folder_path, recursive=True):
    """Count total files in a folder."""
    count = 0
    for root, _, files in os.walk(folder_path):
        count += len(files)
        if not recursive:
            break
    return count

def backup_folder(main_zip, folder_path, recursive, manifest=None, base_manifest=None):
    """Backup a folder with progress bar and optional differential backup."""
    if not os.path.exists(folder_path):
        log(f"Error: Folder '{folder_path}' does not exist. Skipping backup.")
        return {}, 0

    try:
        log(f"Starting backup for '{folder_path}' (Recursive: {recursive})")
        
        # Count total files for progress bar
        total_files = count_files(folder_path, recursive)
        if total_files == 0:
            log(f"No files found in {folder_path}")
            return {}, 0
            
        folder_name = os.path.basename(folder_path.strip('/\\'))
        folder_zip_filename = f"{folder_name}.zip"
        print(f"\nProcessing folder: {folder_name}")
        
        files_processed = 0
        current_manifest = {}
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_zip:
            try:
                with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as folder_zip:
                    # Add path.txt file containing the original path
                    folder_zip.writestr('path.txt', folder_path)
                    
                    # Create progress bar
                    with tqdm(total=total_files, desc=f"Backing up {folder_name}", unit="files") as pbar:
                        for root, _, files in os.walk(folder_path):
                            rel_path = os.path.relpath(root, folder_path)
                            
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, folder_path)
                                
                                try:
                                    # Calculate file hash
                                    file_hash = get_file_hash(file_path)
                                    file_time = os.path.getmtime(file_path)
                                    
                                    # For differential backup, check if file has changed
                                    if base_manifest is not None:
                                        base_info = base_manifest.get(arcname, {})
                                        if (base_info.get('hash') == file_hash and 
                                            base_info.get('time') == file_time):
                                            pbar.update(1)
                                            files_processed += 1
                                            continue
                                    
                                    # Add file to zip
                                    folder_zip.write(file_path, arcname)
                                    current_manifest[arcname] = {
                                        'hash': file_hash,
                                        'time': file_time
                                    }
                                    
                                    pbar.update(1)
                                    files_processed += 1
                                    
                                except Exception as e:
                                    log(f"Error adding file {file_path}: {str(e)}")
                            
                            if not recursive:
                                break
                
                # Verify and add to main zip
                with open(temp_zip.name, 'rb') as f:
                    zip_data = f.read()
                    if not verify_zip_content(zip_data):
                        raise Exception("Created zip file verification failed")
                    
                    if files_processed > 0:  # Only add if files were actually backed up
                        main_zip.writestr(folder_zip_filename, zip_data)
                        log(f"Added verified '{folder_zip_filename}' to main backup")
            
            finally:
                try:
                    os.unlink(temp_zip.name)
                except Exception as e:
                    log(f"Warning: Could not delete temporary file {temp_zip.name}: {str(e)}")
                    
        return current_manifest, files_processed
    
    except Exception as e:
        print(f"Error backing up '{folder_path}': {str(e)}")
        log(f"Error backing up '{folder_path}': {str(e)}")
        return {}, 0

def fix_bad_zipfile(zip_path):
    """Try to fix a corrupted zip file."""
    try:
        log(f"Attempting to fix zip file: {zip_path}")
        with open(zip_path, 'r+b') as f:
            data = f.read()
            pos = data.find(b'PK\x05\x06')  # End of central directory signature
            if pos > 0:
                log(f"Truncating file at position {pos + 22}")
                f.seek(pos + 22)   # Size of 'ZIP end of central directory record'
                f.truncate()
                return True
            else:
                log("Could not find zip file central directory")
                return False
    except Exception as e:
        log(f"Error fixing zip file: {str(e)}")
        return False

def safely_open_zip(zip_path, mode='r'):
    """Safely open a zip file, attempting to fix it if necessary."""
    try:
        return zipfile.ZipFile(zip_path, mode)
    except zipfile.BadZipFile:
        log("Bad zip file encountered, attempting to fix...")
        if fix_bad_zipfile(zip_path):
            return zipfile.ZipFile(zip_path, mode)
        raise

def list_backups():
    """List all available backups with their creation dates."""
    try:
        backups = []
        for entry in os.listdir(backup_destination):
            if entry.startswith("backup_") and entry.endswith(".zip"):
                backup_path = os.path.join(backup_destination, entry)
                creation_time = datetime.fromtimestamp(os.path.getctime(backup_path))
                backups.append((entry, creation_time))
        
        # Sort backups by creation time (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)
        
        print("\nAvailable backups:")
        print("=" * 60)
        for i, (backup_name, creation_time) in enumerate(backups, 1):
            print(f"{i}. {backup_name}")
            print(f"   Created: {creation_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
        
        return backups
    except Exception as e:
        print(f"Error listing backups: {str(e)}")
        log(f"Error listing backups: {str(e)}")
        return []

def restore_backup(backup_name, selected_folders=None):
    """Restore a backup, optionally selecting specific folders to restore."""
    backup_path = os.path.join(backup_destination, backup_name)
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    log(f"Starting restore from backup: {backup_name}")
    
    try:
        # Create a temporary directory for processing nested zips
        with tempfile.TemporaryDirectory() as temp_dir:
            with safely_open_zip(backup_path) as backup_zip:
                # List all folder zips in the backup
                folder_zips = [name for name in backup_zip.namelist() if name.endswith('.zip')]
                
                if not folder_zips:
                    log("No folder zips found in backup")
                    print("No folders found in backup to restore!")
                    return
                
                if selected_folders:
                    folder_zips = [f"{folder}.zip" for folder in selected_folders if f"{folder}.zip" in folder_zips]
                
                for folder_zip_name in folder_zips:
                    temp_zip_path = os.path.join(temp_dir, f"temp_{folder_zip_name}")
                    log(f"Processing {folder_zip_name}")
                    
                    # Extract the folder zip to the temporary directory
                    try:
                        zip_data = backup_zip.read(folder_zip_name)
                        with open(temp_zip_path, 'wb') as f:
                            f.write(zip_data)
                    except Exception as e:
                        log(f"Error extracting {folder_zip_name}: {str(e)}")
                        continue
                    
                    # Now open the extracted zip file
                    try:
                        with safely_open_zip(temp_zip_path) as folder_zip:
                            # Read the original path from path.txt
                            try:
                                original_path = folder_zip.read('path.txt').decode('utf-8').strip()
                            except KeyError:
                                log(f"Warning: path.txt not found in {folder_zip_name}, skipping...")
                                continue
                            
                            # Ask for confirmation before restoring
                            print(f"\nPreparing to restore {folder_zip_name} to {original_path}")
                            if input("Continue with restore? (y/n): ").lower() != 'y':
                                print(f"Skipping restore of {folder_zip_name}")
                                continue
                            
                            # Verify the target directory
                            if not os.path.exists(os.path.dirname(original_path)):
                                print(f"Warning: Parent directory {os.path.dirname(original_path)} doesn't exist.")
                                if input("Create parent directory? (y/n): ").lower() != 'y':
                                    print(f"Skipping restore of {folder_zip_name}")
                                    continue
                            
                            # Create the destination directory if it doesn't exist
                            os.makedirs(original_path, exist_ok=True)
                            
                            # Extract all files except path.txt
                            for file_info in folder_zip.filelist:
                                if file_info.filename != 'path.txt':
                                    target_path = os.path.join(original_path, file_info.filename)
                                    if os.path.exists(target_path):
                                        if input(f"File {file_info.filename} already exists. Overwrite? (y/n): ").lower() != 'y':
                                            log(f"Skipped existing file: {target_path}")
                                            continue
                                    
                                    # Extract the file
                                    folder_zip.extract(file_info, original_path)
                                    log(f"Restored: {os.path.join(original_path, file_info.filename)}")
                            
                            log(f"Completed restore of {folder_zip_name} to {original_path}")
                    except Exception as e:
                        log(f"Error processing folder zip {folder_zip_name}: {str(e)}")
                        print(f"Failed to restore {folder_zip_name}: {str(e)}")
                        continue
        
        log("Restore operation completed successfully")
        print("Restore completed successfully")
    
    except Exception as e:
        error_msg = f"Error during restore: {str(e)}"
        print(error_msg)
        log(error_msg)
        raise
    
def execute_backup():
    """Execute the backup operation with progress bars and differential backup support."""
    # Determine backup type
    is_full_backup = backup_type == 'full' or should_create_full_backup()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set backup name based on type
    backup_prefix = "backup_full_" if is_full_backup else "backup_diff_"
    backup_session_name = f"{backup_prefix}{timestamp}.zip"
    backup_session_path = os.path.join(backup_destination, backup_session_name)
    
    # Load base manifest for differential backup
    base_manifest = None
    if not is_full_backup:
        last_full_backup, manifest_path = get_last_full_backup()
        if manifest_path and os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    base_manifest = json.load(f)
            except Exception as e:
                log(f"Error loading base manifest, falling back to full backup: {str(e)}")
                is_full_backup = True
    
    folders_to_backup = read_folders()
    backup_type_str = "FULL" if is_full_backup else "DIFFERENTIAL"
    print(f"\nStarting {backup_type_str} backup operation...")
    
    try:
        complete_manifest = {}
        total_files_processed = 0
        
        with zipfile.ZipFile(backup_session_path, 'w', zipfile.ZIP_DEFLATED) as main_zip:
            for folder_path, is_recursive in folders_to_backup:
                folder_manifest, files_processed = backup_folder(
                    main_zip, 
                    folder_path, 
                    is_recursive,
                    complete_manifest,
                    base_manifest
                )
                complete_manifest.update(folder_manifest)
                total_files_processed += files_processed
        
        # Save manifest for this backup
        manifest_path = backup_session_path.replace('.zip', '_manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(complete_manifest, f)
        
        # If no files were processed in differential backup, clean up
        if not is_full_backup and total_files_processed == 0:
            os.remove(backup_session_path)
            os.remove(manifest_path)
            log("No changes detected, differential backup not needed")
            print("No changes detected since last backup")
            return
        
        # Verify the final backup
        log("Verifying final backup...")
        try:
            with zipfile.ZipFile(backup_session_path, 'r') as verify_zip:
                for name in verify_zip.namelist():
                    if name.endswith('.zip'):
                        zip_data = verify_zip.read(name)
                        if not verify_zip_content(zip_data):
                            raise Exception(f"Verification failed for {name}")
                        log(f"Verified {name} in backup")
            log("Backup verification completed successfully")
        except Exception as e:
            log(f"Backup verification failed: {str(e)}")
            raise
        
        enforce_backup_limit()
        log(f"{backup_type_str} backup operation completed successfully")
        print(f"{backup_type_str} backup completed. {total_files_processed} files processed.")
    
    except Exception as e:
        error_msg = f"Critical error during backup operation: {str(e)}"
        print(error_msg)
        log(error_msg)
        if os.path.exists(backup_session_path):
            try:
                os.remove(backup_session_path)
                log(f"Removed failed backup: {backup_session_path}")
            except Exception as cleanup_error:
                log(f"Could not remove failed backup: {str(cleanup_error)}")
        raise
    
def main():
    parser = argparse.ArgumentParser(description='Backup and restore utility')
    parser.add_argument('action', choices=['backup', 'restore', 'list'], help='Action to perform: backup, restore, or list backups')
    parser.add_argument('--backup-name', help='Name of the backup to restore')
    parser.add_argument('--folders', nargs='+', help='Specific folders to restore')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        execute_backup()
    elif args.action == 'list':
        list_backups()
    elif args.action == 'restore':
        if not args.backup_name:
            backups = list_backups()
            if not backups:
                print("No backups available to restore")
                return
            
            while True:
                try:
                    choice = int(input("\nEnter the number of the backup to restore: "))
                    if 1 <= choice <= len(backups):
                        args.backup_name = backups[choice-1][0]
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
        
        restore_backup(args.backup_name, args.folders)

if __name__ == "__main__":
    main()