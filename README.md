# PyBackup

A robust automated backup solution for Windows featuring differential backups, compression, and smart backup management. Perfect for both personal and professional use.

## Features

- 🔄 Smart differential backups (only backs up changed files)
- 📊 Progress tracking with detailed status bars
- 🔒 File integrity verification
- 🗂️ Multiple backup types (Full and Differential)
- 📁 Support for multiple backup sources
- 🌲 Recursive and non-recursive folder backups
- 🗜️ ZIP compression with corruption protection
- ⏱️ Intelligent backup retention management
- 📝 Comprehensive logging system
- ⚙️ Simple configuration file
- 💻 Command-line interface

## Quick Installation

Run this command in PowerShell (Administrator):
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; Invoke-WebRequest 'https://raw.githubusercontent.com/voidshaman/pyBackup/refs/heads/main/install.py' -OutFile "$env:TEMP\install.py"; python "$env:TEMP\install.py"
```

## Requirements

- Windows OS
- Python 3.6 or higher
- Administrator privileges (for installation)
- Required packages (automatically installed):
  - tqdm (for progress bars)
  - configparser (for configuration management)

## Usage

PyBackup offers three main operations:

1. **Creating Backups**:
   ```bash
   pybackup backup
   ```

2. **Listing Available Backups**:
   ```bash
   pybackup list
   ```

3. **Restoring Backups**:
   ```bash
   pybackup restore [--backup-name BACKUP_NAME] [--folders FOLDER1 FOLDER2 ...]
   ```

## Configuration

The configuration file (`conf.cfg`) supports the following settings:

### Paths Configuration
```ini
[Paths]
backup_destination = D:/Backup    # Where your backups will be stored
```

### Backup Settings
```ini
[Backup]
type = differential               # 'full' or 'differential'
full_backup_interval = 7         # Days between full backups
max_backups = 5                  # Maximum number of backups to retain
format = zip                     # Backup format (currently only zip supported)
```

### Folder Configuration
```ini
[Folders]
folders = D:/Documents, R; C:/Projects, NR; D:/Photos, R
```

#### Folder Format Explanation:
- Paths and flags are separated by commas
- Multiple entries are separated by semicolons
- Flags:
  - `R`: Recursive (includes subfolders)
  - `NR`: Non-recursive (only top-level files)

## Backup Types

PyBackup supports two backup types:

1. **Full Backup**:
   - Complete backup of all specified folders
   - Creates a baseline for differential backups
   - Automatically performed when:
     - No previous backups exist
     - Last full backup is older than `full_backup_interval`

2. **Differential Backup**:
   - Only backs up files that have changed since last full backup
   - Much faster and space-efficient
   - Automatically skipped if no changes detected

## Restore Options

The restore command supports:

- Full system restore
- Selective folder restore
- Backup selection by name or interactive choice
- Safe restore with confirmation prompts
- Corruption detection and handling

## Directory Structure

Post-installation structure:
```
C:/pyBackup/
├── backup_service.py    # Main backup script
├── pybackup.bat        # Command-line interface
└── conf/
    └── conf.cfg        # Configuration file
```

## Logging

The system maintains a detailed log file (`backup_log.txt`) in your backup destination, tracking:
- Backup operations and their types
- File processing status
- Error reports and warnings
- Successful completions

## Troubleshooting

1. **Permission Issues**:
   - Run the backup command with administrator privileges
   - Check folder permissions in backup destination

2. **Backup Verification Failures**:
   - Check available disk space
   - Verify source files are not in use
   - Review log file for specific errors

3. **Restore Problems**:
   - Ensure you have write permissions to restore locations
   - Verify the backup chain is complete (for differential restores)
   - Check if source paths still exist

## Best Practices

1. **Backup Strategy**:
   - Keep full_backup_interval reasonable (7-30 days)
   - Store backups on a different drive than source
   - Regularly verify backup integrity

2. **Performance**:
   - Use differential backups for frequent backups
   - Adjust max_backups based on available storage
   - Consider non-recursive backups for large folders

## License

This project is licensed under the MIT License - see the LICENSE file for details.