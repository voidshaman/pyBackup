import os
import sys
import configparser
import subprocess
import requests
import zipfile
import io
import win32serviceutil

REPO_URL = "https://github.com/voidshaman/pyBackup/archive/refs/heads/main.zip"
REPO_DIR = "pyBackup-main"

def download_and_extract_repo():
    """Download and extract the latest version of the repository from GitHub."""
    print("Downloading latest version of the repository...")
    response = requests.get(REPO_URL)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall()
        print("Repository downloaded and extracted.")
    else:
        print("Failed to download the repository. Check the URL or internet connection.")
        sys.exit(1)

def create_conf_file(config_path):
    """Create the conf.cfg file with user-provided settings."""
    config = configparser.ConfigParser()

    # Prompt user for configuration settings
    folders = input("Enter folder paths to backup, separated by commas: ").split(',')
    destination = input("Enter the backup destination path: ")
    schedule = input("Enter backup frequency (daily/weekly): ")
    format_option = input("Enter backup format (zip/copy): ")
    recursive = input("Should backup be recursive (yes/no): ").lower() == 'yes'

    # Populate configuration
    config['Paths'] = {'backup_destination': destination}
    config['Backup'] = {'schedule': schedule, 'format': format_option, 'recursive': str(recursive)}
    config['Folders'] = {f'folder{i+1}': os.path.expandvars(folder.strip()) for i, folder in enumerate(folders)}

    # Write configuration to conf.cfg
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    print("Configuration file created at", config_path)

def set_env_variable():
    """Set an environment variable for the backup service path."""
    script_dir = os.path.abspath(REPO_DIR)
    env_var = "BACKUP_SERVICE_PATH"
    os.system(f'setx {env_var} "{script_dir}"')
    print(f"Environment variable {env_var} set to {script_dir}")

def install_service():
    """Install the Windows service."""
    subprocess.run(["python", os.path.join(REPO_DIR, "backup_service.py"), "install"], check=True)
    subprocess.run(["python", os.path.join(REPO_DIR, "backup_service.py"), "start"], check=True)
    print("Backup service installed and started.")

def uninstall_service():
    """Uninstall the Windows service and remove environment variable."""
    subprocess.run(["python", os.path.join(REPO_DIR, "backup_service.py"), "stop"], check=True)
    subprocess.run(["python", os.path.join(REPO_DIR, "backup_service.py"), "remove"], check=True)
    os.system(r"reg delete HKCU\Environment /F /V BACKUP_SERVICE_PATH")
    print("Backup service uninstalled and environment variable removed.")

def main():
    config_path = os.path.join(REPO_DIR, "conf", "conf.cfg")
    action = input("Enter 'install' to setup the backup service or 'uninstall' to remove it: ").strip().lower()

    if action == 'install':
        download_and_extract_repo()
        os.makedirs(os.path.join(REPO_DIR, "conf"), exist_ok=True)
        create_conf_file(config_path)
        set_env_variable()
        install_service()
    elif action == 'uninstall':
        uninstall_service()
    else:
        print("Invalid option. Use 'install' or 'uninstall'.")

if __name__ == '__main__':
    main()