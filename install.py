import os
import sys
import requests
import subprocess
import shutil
import ctypes
import platform
import winreg

# Required packages
REQUIRED_PACKAGES = [
    'requests>=2.31.0',
    'configparser>=5.3.0'
]

# URLs and paths
BACKUP_SCRIPT_URL = "https://raw.githubusercontent.com/voidshaman/pyBackup/refs/heads/main/backup_service.py"
CONFIG_FILE_URL = "https://raw.githubusercontent.com/voidshaman/pyBackup/refs/heads/main/conf/conf.cfg"
INSTALL_DIR = "C:/pyBackup"
CONF_DIR = os.path.join(INSTALL_DIR, "conf")
BACKUP_SCRIPT_PATH = os.path.join(INSTALL_DIR, "backup_service.py")
CONFIG_FILE_PATH = os.path.join(CONF_DIR, "conf.cfg")
ENV_VAR_NAME = "PYBACKUP_PATH"

# Create a batch file for easy execution
BATCH_FILE_CONTENT = '''@echo off
python "%~dp0backup_service.py" %*
'''

def create_command_script():
    """Create a batch file for command line execution"""
    try:
        batch_path = os.path.join(INSTALL_DIR, "pybackup.bat")
        with open(batch_path, 'w') as f:
            f.write(BATCH_FILE_CONTENT)
        return batch_path
    except Exception as e:
        raise RuntimeError(f"Failed to create command script: {str(e)}")

def add_to_system_path(directory):
    """Add directory to system PATH"""
    try:
        # Open the registry key for the system PATH
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_ALL_ACCESS)
        
        # Get current PATH value
        current_path = winreg.QueryValueEx(key, "Path")[0]
        
        # Check if directory is already in PATH
        if directory.lower() not in [p.lower() for p in current_path.split(';')]:
            # Add new directory to PATH
            new_path = current_path + ';' + directory
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            
            # Notify the system about the change
            subprocess.run(['setx', 'PATH', new_path], capture_output=True, check=True)
            
        winreg.CloseKey(key)
        print(f"Added {directory} to system PATH")
        
    except Exception as e:
        raise RuntimeError(f"Failed to update system PATH: {str(e)}")
    

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_requirements():
    """Install required Python packages"""
    try:
        print("Installing required packages...")
        # Use system Python's pip to install packages
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        for package in REQUIRED_PACKAGES:
            print(f"Installing {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("All required packages installed successfully")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to install required packages: {str(e)}")

def check_environment():
    """Check if the environment meets all requirements"""
    if platform.system() != 'Windows':
        raise SystemError("This script only runs on Windows")
    
    if not is_admin():
        raise PermissionError("This script requires administrator privileges")
    
    # Check if Python is in PATH
    try:
        subprocess.run([sys.executable, "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise EnvironmentError("Python executable not found in PATH")

def download_file(url, dest_path):
    """Download a file with proper error handling"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {url} to {dest_path}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download {url}: {str(e)}")
    except IOError as e:
        raise RuntimeError(f"Failed to save file to {dest_path}: {str(e)}")

def setup_install_directory():
    """Set up installation directory with error handling"""
    try:
        if os.path.exists(INSTALL_DIR):
            print(f"Warning: Installation directory {INSTALL_DIR} already exists")
            if input("Would you like to remove it? (y/n): ").lower() == 'y':
                shutil.rmtree(INSTALL_DIR)
            else:
                raise RuntimeError("Installation cancelled by user")
        
        os.makedirs(CONF_DIR, exist_ok=True)
        download_file(BACKUP_SCRIPT_URL, BACKUP_SCRIPT_PATH)
    except Exception as e:
        raise RuntimeError(f"Failed to set up installation directory: {str(e)}")

def create_scheduled_task():
    """Create scheduled task with proper error handling and validation"""
    print("Please select the schedule for running the backup task:")
    print("1: Weekly\n2: Daily\n3: Monthly\n4: On Boot")
    
    schedule_types = {
        "1": ("WEEKLY", "/d MON /st 00:00"),
        "2": ("DAILY", "/st 00:00"),
        "3": ("MONTHLY", "/d 1 /st 00:00"),
        "4": ("ONSTART", "")
    }
    
    while True:
        choice = input("Enter your choice (1-4): ").strip()
        if choice in schedule_types:
            schedule_type, schedule_params = schedule_types[choice]
            break
        print("Invalid choice. Please select a valid option.")
    
    task_name = "pyBackupTask"
    python_path = f'"{sys.executable}"'  # Quote the path
    script_path = f'"{BACKUP_SCRIPT_PATH}"'  # Quote the path
    command = f'{python_path} {script_path}'
    
    try:
        # Remove existing task if it exists
        subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], 
                      capture_output=True, check=False)
        
        # Create new task
        cmd = ["schtasks", "/create", "/tn", task_name, 
               "/sc", schedule_type, "/tr", command, "/f"]
        
        if schedule_params:
            cmd.extend(schedule_params.split())
        
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"Scheduled task created for {schedule_type} schedule")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create scheduled task: {e.stderr.decode()}")

def set_env_variable():
    """Set environment variable with proper error handling"""
    try:
        # Using subprocess instead of os.system for better control
        subprocess.run(["setx", ENV_VAR_NAME, INSTALL_DIR], 
                      capture_output=True, check=True)
        print(f"Environment variable {ENV_VAR_NAME} set to {INSTALL_DIR}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to set environment variable: {e.stderr.decode()}")

def download_sample_config():
    """Download sample config with error handling"""
    try:
        download_file(CONFIG_FILE_URL, CONFIG_FILE_PATH)
    except Exception as e:
        raise RuntimeError(f"Failed to download sample config: {str(e)}")

def open_config_file():
    """Open config file with error handling"""
    try:
        os.startfile(CONFIG_FILE_PATH)
        print("Opening configuration file for editing.")
    except Exception as e:
        print(f"Warning: Could not open config file automatically: {str(e)}")
        print(f"Please open {CONFIG_FILE_PATH} manually to configure the backup settings.")

def cleanup_on_error():
    """Clean up installation files in case of failure"""
    try:
        if os.path.exists(INSTALL_DIR):
            shutil.rmtree(INSTALL_DIR)
        subprocess.run(["schtasks", "/delete", "/tn", "pyBackupTask", "/f"], 
                      capture_output=True, check=False)
    except Exception as e:
        print(f"Warning: Cleanup failed: {str(e)}")

def main():
    print("Starting installation...")
    
    try:
        # Initial environment checks
        check_environment()
        
        # Install required packages
        install_requirements()
        
        # Installation steps
        setup_install_directory()
        create_scheduled_task()
        set_env_variable()
        download_sample_config()
        
        # Create command line script and add to PATH
        batch_path = create_command_script()
        add_to_system_path(INSTALL_DIR)
        
        open_config_file()
        
        print("\nInstallation completed successfully.")
        print("\nYou can now run backups from command line using:")
        print("  pybackup")
        
    except Exception as e:
        print(f"Installation failed: {str(e)}")
        cleanup_on_error()
        sys.exit(1)

if __name__ == "__main__":
    # Restart with admin privileges if needed
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
        
    main()