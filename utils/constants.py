"""
Constants and configuration values for the DJ Timeline application
"""

# Configuration
CONFIG_FILE = "djs_timeline_machine_config.json"
VERSION = "v2.6.17"
VERSION_TUPLE = (2, 6, 17)

# GitHub Repository Information for Updates
GITHUB_REPO_OWNER = "Tripper99"
GITHUB_REPO_NAME = "djs-timeline-maskin"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases"

# Update Check Configuration
UPDATE_CHECK_DEFAULTS = {
    "update_check_enabled": False,  # Privacy-first: disabled by default
    "skip_versions": [],            # List of versions user wants to skip
    "last_update_check": "",        # ISO timestamp of last check
    "auto_check_interval_days": 7,  # Days between automatic checks
    "github_timeout_seconds": 10,   # Network timeout for GitHub requests
    "max_response_size_kb": 50,     # Maximum size for GitHub API responses
}

# Update Check Security Limits
UPDATE_SECURITY_LIMITS = {
    "max_json_response_size": 1024 * 50,  # 50KB maximum
    "max_request_timeout": 10,            # 10 seconds maximum
    "max_version_length": 20,             # Maximum version string length
    "max_url_length": 200,                # Maximum URL length
    "max_release_notes_length": 10000,    # 10KB for release notes
}

# Required Excel columns - these must exist in the Excel file
REQUIRED_EXCEL_COLUMNS = [
    'OBS', 'Inlagd', 'Kategori', 'Underkategori',
    'Person/sak', 'Special', 'Händelse', 'Dag',
    'Startdatum', 'Starttid', 'Slutdatum', 'Sluttid', 'Note1', 'Note2', 'Note3',
    'Källa', 'Källa2', 'Källa3', 'Övrigt'
]
