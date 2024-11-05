# PyBackup

A simple yet powerful automated backup solution for Windows, featuring scheduled backups, recursive/non-recursive folder handling, and backup retention management.

## Features

- 🔄 Automated scheduled backups (Daily, Weekly, Monthly, or On Boot)
- 📁 Support for multiple backup sources
- 🌲 Recursive and non-recursive folder backups
- 🗜️ ZIP compression
- ⏱️ Backup retention management
- 📝 Detailed logging
- ⚙️ Simple configuration file
- 💻 Command-line access from anywhere

## Quick Installation

Run this command in PowerShell (Administrator):
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/voidshaman/pyBackup/refs/heads/main/install.py')) | python
```

## Requirements

- Windows OS
- Python 3.6 or higher
- Administrator privileges (for installation)

The installer will automatically handle all Python package dependencies.

## Usage

After installation, you can run backups in three ways:

1. **Command Line**: 
- Creating a backup NOW
   ```bash
   pybackup backup
   ```
- Listing backups
   ```bash
   pybackup list
   ```
- Restoring a backup
   ```bash
   pybackup restore
   ```


2. **Scheduled Task**: Runs automatically according to your chosen schedule

3. **Manual Execution**: Run `backup_service.py` directly from the installation directory

Note: After installation, you might need to restart your terminal or refresh environment variables to use the `pybackup` command:
```powershell
# PowerShell with Chocolatey
refreshenv

# or PowerShell manual refresh
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

## Configuration

After installation, a configuration file (`conf.cfg`) will be created in the installation directory. You can customize the following settings:

### Backup Destination
```ini
[Paths]
backup_destination = D:/Backup    # Where your backups will be stored
```

### Backup Settings
```ini
[Backup]
format = zip                      # Backup format. "zip" or "folder"
max_backups = 5                   # Maximum number of backup versions to keep
session_format = zip              # Format for individual backup sessions
```

### Folder Configuration
```ini
[Folders]
folders = path/to/folder1, R; path/to/folder2, NR; path/to/folder3, R
```

#### Folder Configuration Format:
- Each folder entry consists of a path and a recursive flag
- Entries are separated by semicolons (`;`)
- For each entry:
  - `R` = Recursive backup (includes subfolders)
  - `NR` = Non-recursive backup (only top-level files)
- Example: `D:/Documents, R; C:/ImportantFiles, NR`

## Backup Process

1. The script creates a timestamped backup session
2. Each configured folder is processed according to its recursive setting
3. Files are compressed into a ZIP archive
4. Old backups are automatically removed based on `max_backups` setting
5. A detailed log is maintained in the backup destination folder

## Log File

A log file (`backup_log.txt`) is created in your backup destination folder, containing:
- Timestamp for each operation
- Folders processed
- Files added
- Any errors encountered

## Schedule Options

During installation, you can choose from these scheduling options:
1. Weekly (Runs every Monday at 00:00)
2. Daily (Runs every day at 00:00)
3. Monthly (Runs on the 1st of each month at 00:00)
4. On Boot (Runs when the system starts)

## Installation Directory Structure

After installation, you'll find these files in `C:/pyBackup`:
```
C:/pyBackup/
├── backup_service.py    # Main backup script
├── pybackup.bat        # Command-line launcher
└── conf/
    └── conf.cfg        # Configuration file
```

## Troubleshooting

1. **Installation Fails**: 
   - Ensure you're running PowerShell as Administrator
   - Check your internet connection
   - Verify Python is installed and in PATH

2. **Backup Fails**:
   - Check the log file for specific errors
   - Ensure all configured paths exist
   - Verify write permissions in the backup destination

3. **Schedule Issues**:
   - Open Task Scheduler to check the task status
   - Ensure the computer is on at scheduled times
   - Verify the Python path hasn't changed

4. **Command Not Found**:
   - Restart your terminal after installation
   - Try refreshing environment variables (see Usage section)
   - Verify installation directory is in PATH

## Support

If you encounter any issues or need assistance:
1. Check the log file for error details
2. Verify your configuration file settings
3. Create an issue on the GitHub repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.

