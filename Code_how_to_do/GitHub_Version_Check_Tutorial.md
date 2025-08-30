# How to Add GitHub Version Checking to Your Python App

This guide explains how to add automatic version checking functionality to any Python application using GitHub Releases. It's written for beginners who want to implement similar functionality in their own projects.

## What This System Does

The version checking system allows your Python application to:
- Check GitHub for newer versions automatically
- Show users when updates are available
- Display release notes and downloadable files
- Open the browser to download updates
- Work without requiring users to have GitHub accounts

## Overview - How It Works

1. **Your app knows its current version** (stored in a file)
2. **It calls GitHub's API** to check for the latest release
3. **It compares versions** (current vs. latest)
4. **If newer version exists**, it shows a dialog to the user
5. **User can download the update** by opening GitHub in their browser

## Required Dependencies

Add these to your `requirements.txt` or install with pip:

```bash
pip install requests
```

That's it! The system uses only standard Python libraries plus `requests`.

## File Structure

Create these files in your project:

```
your_project/
├── src/
│   ├── version.py                    # Stores current version
│   ├── config.py                     # Configuration management
│   ├── security/
│   │   └── network_validator.py      # Security for API calls
│   └── update/
│       ├── __init__.py
│       ├── models.py                 # Data structures
│       ├── version_checker.py        # Main logic
│       └── update_dialog.py          # User interface
└── your_main_app.py
```

## Step 1: Version Management (`src/version.py`)

First, create a simple version file:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version management for your application
"""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
__release_date__ = "2025-01-01"

def get_version():
    """Return the current version string"""
    return __version__

def get_version_info():
    """Return version as tuple (major, minor, patch)"""
    return __version_info__
```

**Why this matters**: Your app needs to know what version it is before it can check if there's a newer one.

## Step 2: Configuration (`src/config.py`)

Add GitHub repository info to your config:

```python
def load_config():
    """Load application configuration"""
    default_config = {
        # Your existing settings here...
        "update_settings": {
            "github_repo_owner": "YourUsername",    # Change this!
            "github_repo_name": "YourRepository",   # Change this!
            "check_on_startup": False,
            "auto_check_enabled": False
        }
    }
    
    # Load from JSON file if it exists, otherwise use defaults
    # (implementation depends on how your app handles config)
    
    return default_config
```

**Important**: Replace "YourUsername" and "YourRepository" with your actual GitHub info!

## Step 3: Data Models (`src/update/models.py`)

Create simple data structures to hold update information:

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class UpdateAsset:
    """Represents a downloadable file from GitHub release"""
    name: str           # File name (e.g., "MyApp_v1.2.0.exe")
    download_url: str   # Direct download link
    size_mb: float      # File size in megabytes

@dataclass
class UpdateInfo:
    """Information about an available update"""
    version: str                    # New version (e.g., "1.2.0")
    release_notes: str             # Description of changes
    release_date: datetime         # When it was published
    assets: List[UpdateAsset]      # List of files to download
    html_url: str                  # GitHub page URL
    
    @property
    def version_tuple(self) -> tuple:
        """Convert version string to tuple for comparison"""
        # Remove 'v' prefix if present and split by dots
        clean_version = self.version.lstrip('v')
        return tuple(map(int, clean_version.split('.')))

@dataclass
class UpdateCheckResult:
    """Result of checking for updates"""
    update_available: bool
    current_version: str
    update_info: Optional[UpdateInfo] = None
    error_message: Optional[str] = None
```

**What this does**: These are like containers that hold all the information about updates in an organized way.

## Step 4: Security Layer (`src/security/network_validator.py`)

**Important**: Never skip security! This protects your app from malicious responses:

```python
import re
import json
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Security limits
MAX_JSON_RESPONSE_SIZE = 1024 * 1024  # 1MB
MAX_REQUEST_TIMEOUT = 10  # seconds

class NetworkSecurityError(Exception):
    """Base exception for network security violations"""
    pass

class NetworkValidator:
    """Secure network operations validator"""
    
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
    def validate_api_url(self, url: str) -> bool:
        """Make sure the URL is a valid GitHub API URL"""
        if not url.startswith("https://api.github.com/repos/"):
            raise NetworkSecurityError("Only GitHub API URLs allowed")
            
        expected = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases"
        if not url.startswith(expected):
            raise NetworkSecurityError("URL doesn't match expected repository")
            
        return True
        
    def get_secure_request_config(self) -> dict:
        """Get secure settings for HTTP requests"""
        return {
            'timeout': MAX_REQUEST_TIMEOUT,
            'verify': True,  # Always verify SSL certificates
            'allow_redirects': False,  # No automatic redirects
            'headers': {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'YourAppName-UpdateChecker/1.0'  # Change this!
            }
        }
        
    def validate_json_response(self, response_text: str) -> dict:
        """Safely parse JSON response"""
        # Check size
        if len(response_text) > MAX_JSON_RESPONSE_SIZE:
            raise NetworkSecurityError(f"Response too large: {len(response_text)} bytes")
            
        # Parse JSON safely
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise NetworkSecurityError(f"Invalid JSON response: {e}")
            
        return data
```

**Why security matters**: Without validation, malicious responses could crash your app or worse.

## Step 5: Main Logic (`src/update/version_checker.py`)

This is the heart of the system:

```python
import logging
import requests
from datetime import datetime
from typing import Optional

from ..version import get_version_info
from ..security.network_validator import NetworkValidator, NetworkSecurityError
from .models import UpdateCheckResult, UpdateInfo, UpdateAsset

logger = logging.getLogger(__name__)

class VersionChecker:
    """Handles checking for updates from GitHub"""
    
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.validator = NetworkValidator(repo_owner, repo_name)
        
    def check_for_updates(self) -> UpdateCheckResult:
        """Check if a newer version is available"""
        current_version = get_version_info()  # e.g., (1, 0, 0)
        
        try:
            # Build GitHub API URL
            api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            
            # Validate URL for security
            self.validator.validate_api_url(api_url)
            
            # Make secure HTTP request
            config = self.validator.get_secure_request_config()
            response = requests.get(api_url, **config)
            
            if response.status_code == 404:
                return UpdateCheckResult(
                    update_available=False,
                    current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                    error_message="No releases found in repository"
                )
                
            response.raise_for_status()  # Raise error for bad status codes
            
            # Parse and validate JSON response
            release_data = self.validator.validate_json_response(response.text)
            
            # Extract version info
            latest_version = release_data.get('tag_name', '').lstrip('v')
            if not latest_version:
                return UpdateCheckResult(
                    update_available=False,
                    current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                    error_message="Could not find version information"
                )
            
            # Compare versions
            try:
                latest_tuple = tuple(map(int, latest_version.split('.')))
                update_available = latest_tuple > current_version
                
                if update_available:
                    # Create update info
                    assets = []
                    for asset in release_data.get('assets', []):
                        assets.append(UpdateAsset(
                            name=asset.get('name', ''),
                            download_url=asset.get('browser_download_url', ''),
                            size_mb=round(asset.get('size', 0) / (1024 * 1024), 1)
                        ))
                    
                    update_info = UpdateInfo(
                        version=latest_version,
                        release_notes=release_data.get('body', ''),
                        release_date=datetime.fromisoformat(release_data.get('published_at', '').replace('Z', '+00:00')),
                        assets=assets,
                        html_url=release_data.get('html_url', '')
                    )
                    
                    return UpdateCheckResult(
                        update_available=True,
                        current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                        update_info=update_info
                    )
                else:
                    return UpdateCheckResult(
                        update_available=False,
                        current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}"
                    )
                    
            except ValueError:
                return UpdateCheckResult(
                    update_available=False,
                    current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                    error_message=f"Invalid version format: {latest_version}"
                )
                
        except NetworkSecurityError as e:
            logger.error(f"Security error during update check: {e}")
            return UpdateCheckResult(
                update_available=False,
                current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                error_message=f"Security error: {str(e)}"
            )
        except requests.RequestException as e:
            logger.error(f"Network error during update check: {e}")
            return UpdateCheckResult(
                update_available=False,
                current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                error_message=f"Network error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during update check: {e}")
            return UpdateCheckResult(
                update_available=False,
                current_version=f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                error_message=f"Unexpected error: {str(e)}"
            )
```

**What this does**: This is the "brain" that actually talks to GitHub and figures out if there's an update.

## Step 6: User Interface (`src/update/update_dialog.py`)

Create a simple dialog to show users when updates are available:

```python
import tkinter as tk
from tkinter import messagebox
import webbrowser
import logging

from .models import UpdateInfo

logger = logging.getLogger(__name__)

class UpdateDialog:
    """Dialog to show available updates to user"""
    
    def __init__(self, parent, update_info: UpdateInfo):
        self.parent = parent
        self.update_info = update_info
        self.result = None
        
    def show_update_available(self) -> str:
        """Show dialog for available update"""
        # Create a simple dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Update Available")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        dialog.grab_set()  # Make it modal
        
        # Center on parent window
        dialog.transient(self.parent)
        
        # Main frame
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text=f"New Version Available: v{self.update_info.version}",
                              font=("TkDefaultFont", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Release notes
        if self.update_info.release_notes.strip():
            notes_label = tk.Label(main_frame, text="Release Notes:", 
                                 font=("TkDefaultFont", 10, "bold"))
            notes_label.pack(anchor="w")
            
            notes_text = tk.Text(main_frame, height=8, wrap=tk.WORD)
            notes_text.pack(fill="both", expand=True, pady=(5, 10))
            notes_text.insert(tk.END, self.update_info.release_notes)
            notes_text.config(state="disabled")  # Read-only
        
        # Available files
        if self.update_info.assets:
            files_label = tk.Label(main_frame, text="Available Files:", 
                                 font=("TkDefaultFont", 10, "bold"))
            files_label.pack(anchor="w", pady=(0, 5))
            
            for asset in self.update_info.assets:
                file_text = f"• {asset.name} ({asset.size_mb} MB)"
                file_label = tk.Label(main_frame, text=file_text, 
                                    font=("TkDefaultFont", 9))
                file_label.pack(anchor="w", padx=(20, 0))
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Download button
        download_btn = tk.Button(button_frame, text="Download Update",
                               command=lambda: self._handle_download(dialog))
        download_btn.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Later",
                              command=lambda: self._handle_cancel(dialog))
        cancel_btn.pack(side="right")
        
        # Wait for user choice
        dialog.wait_window()
        return self.result or "cancel"
        
    def _handle_download(self, dialog):
        """Handle download button click"""
        try:
            webbrowser.open(self.update_info.html_url)
            self.result = "download"
            dialog.destroy()
        except Exception as e:
            logger.error(f"Could not open browser: {e}")
            messagebox.showerror("Error", "Could not open web browser")
            
    def _handle_cancel(self, dialog):
        """Handle cancel button click"""
        self.result = "cancel"
        dialog.destroy()
```

## Step 7: Integration with Your Main App

In your main application file, add a menu item or button to check for updates:

```python
from src.config import load_config
from src.update.version_checker import VersionChecker
from src.update.update_dialog import UpdateDialog

def check_for_updates(parent_window):
    """Check for updates and show dialog if needed"""
    config = load_config()
    update_settings = config.get("update_settings", {})
    
    repo_owner = update_settings.get("github_repo_owner", "")
    repo_name = update_settings.get("github_repo_name", "")
    
    if not repo_owner or not repo_name:
        messagebox.showwarning("Configuration Error", 
                              "GitHub repository not configured")
        return
    
    # Check for updates
    checker = VersionChecker(repo_owner, repo_name)
    result = checker.check_for_updates()
    
    if result.error_message:
        messagebox.showerror("Update Check Failed", result.error_message)
    elif result.update_available:
        # Show update dialog
        dialog = UpdateDialog(parent_window, result.update_info)
        action = dialog.show_update_available()
        print(f"User chose: {action}")
    else:
        messagebox.showinfo("No Updates", "You are using the latest version!")

# Example: Add to your GUI menu
def create_help_menu(menubar, parent_window):
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Check for Updates...", 
                         command=lambda: check_for_updates(parent_window))
```

## Step 8: Testing Your Implementation

1. **Test with no internet**: Make sure it doesn't crash
2. **Test with wrong repository name**: Should show error message
3. **Test with current version**: Should say "no updates available"
4. **Create a test release on GitHub**: Make version higher than your current version
5. **Test with newer version available**: Should show update dialog

## Step 9: Customization

### Change the Language
Replace English text with your preferred language in the dialog:

```python
# English
title_text = "New Version Available"
download_button = "Download Update"

# Swedish (example)
title_text = "Ny version tillgänglig"
download_button = "Ladda ned uppdatering"

# German (example)
title_text = "Neue Version verfügbar"
download_button = "Update herunterladen"
```

### Add Automatic Checking
You can check for updates when your app starts:

```python
def on_app_startup():
    config = load_config()
    if config.get("update_settings", {}).get("check_on_startup", False):
        # Run in background thread to not block startup
        import threading
        update_thread = threading.Thread(target=lambda: check_for_updates(main_window))
        update_thread.daemon = True
        update_thread.start()
```

### Add "Skip This Version" Feature
Users can choose to ignore a specific version:

```python
def _handle_skip_version(self, dialog):
    """Handle skip version button click"""
    # Save skipped version to config
    config = load_config()
    config["update_settings"]["skip_version"] = self.update_info.version
    save_config(config)
    
    self.result = "skip"
    dialog.destroy()
```

## Security Best Practices

1. **Always validate URLs** before making requests
2. **Set timeouts** for network requests
3. **Limit response sizes** to prevent memory issues
4. **Verify SSL certificates** (never disable verification)
5. **Don't auto-download files** - let users choose
6. **Log security events** for debugging

## Common Problems and Solutions

### "No releases found"
- Make sure your repository is public
- Create at least one release on GitHub
- Check the repository name spelling

### "Permission denied" errors
- Make sure your repository is public
- Don't use authentication tokens for public repos

### Version comparison not working
- Make sure your versions follow format "1.2.3"
- Remove "v" prefix from version tags

### Dialog doesn't show
- Check that your GUI framework is properly initialized
- Make sure you're calling the dialog from the main thread

## Final Notes

This system is designed to be:
- **Safe**: Won't automatically download or install anything
- **User-friendly**: Clear dialogs and messages
- **Secure**: Validates all network responses
- **Simple**: Easy to integrate into existing apps

Remember to:
1. Replace placeholder text with your actual repository information
2. Test thoroughly before deploying
3. Keep your version numbers consistent
4. Create meaningful release notes for your users

Good luck with your implementation!