import os
import configparser
import shutil
import zipfile
from datetime import datetime

# Load configuration
config = configparser.ConfigParser()
config.read("conf/conf.cfg")

# Read settings from the configuration
backup_destination = os.path.expandvars(config.get("Paths", "backup_destination", fallback="D:/Backup"))
backup_format = config.get("Backup", "format", fallback="zip").lower()

# Updated folder reading to process each line in the Folders section
def read_folders(config):
    """Read folder paths from configuration and process recursive flags."""
    folders = []
    if "Folders" in config.sections():
        for line in config["Folders"]:
            folder_entry = line.strip()
            if ',' in folder_entry:
                folder_path, recursive_flag = map(str.strip, folder_entry.split(','))
                recursive = recursive_flag.upper() == 'R'
                folders.append((folder_path, recursive))
            else:
                print(f"Invalid format in 'Folders' section: {folder_entry}")
    return folders

folders_to_backup = read_folders(config)

# Create backup directory with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = os.path.join(backup_destination, f"backup_{timestamp}")
os.makedirs(backup_dir, exist_ok=True)

# Logging setup
log_file = os.path.join(backup_destination, "backup_log.txt")
def log(message):
    with open(log_file, 'a') as logf:
        logf.write(f"{datetime.now()}: {message}\n")

# Perform backup for each folder
def backup_folder(folder_path, recursive, backup_type):
    try:
        folder_name = os.path.basename(folder_path.strip('/\\'))
        target_path = os.path.join(backup_dir, f"{folder_name}_{timestamp}")

        if backup_type == "zip":
            with zipfile.ZipFile(f"{target_path}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)
                    if not recursive:
                        break
            log(f"Zipped {folder_path} to {target_path}.zip")

        elif backup_type == "copy":
            if recursive:
                shutil.copytree(folder_path, target_path)
            else:
                os.makedirs(target_path, exist_ok=True)
                for item in os.listdir(folder_path):
                    s = os.path.join(folder_path, item)
                    d = os.path.join(target_path, item)
                    if os.path.isfile(s):
                        shutil.copy2(s, d)
            log(f"Copied {folder_path} to {target_path}")

    except Exception as e:
        log(f"Error backing up {folder_path}: {e}")

# Execute backup for each folder
for folder_path, is_recursive in folders_to_backup:
    if os.path.exists(folder_path):
        backup_folder(folder_path, is_recursive, backup_format)
    else:
        log(f"Folder {folder_path} does not exist, skipping.")

log("Backup operation completed.")
print("Backup operation completed. Check the log for details.")
