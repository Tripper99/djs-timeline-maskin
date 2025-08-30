"""
Data models for version checking functionality
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class UpdateAsset:
    """Represents a downloadable file from GitHub release"""
    name: str           # File name (e.g., "DJs_Timeline_Machine_v2.7.0.exe")
    download_url: str   # Direct download link
    size: int          # File size in bytes
    content_type: str  # MIME type of the file

    @property
    def size_mb(self) -> float:
        """Return file size in megabytes"""
        return round(self.size / (1024 * 1024), 1)


@dataclass
class UpdateInfo:
    """Information about an available update"""
    version: str                    # New version (e.g., "2.7.0")
    tag_name: str                  # GitHub tag name (e.g., "v2.7.0")
    name: str                      # Release name
    body: str                      # Release notes/description
    published_at: datetime         # When it was published
    html_url: str                  # GitHub release page URL
    assets: List[UpdateAsset]      # List of files to download
    is_prerelease: bool           # Whether this is a pre-release
    is_draft: bool                # Whether this is a draft release

    @property
    def version_tuple(self) -> Tuple[int, ...]:
        """Convert version string to tuple for comparison"""
        # Remove 'v' prefix if present and split by dots
        clean_version = self.version.lstrip('v')
        try:
            return tuple(map(int, clean_version.split('.')))
        except ValueError:
            # Fallback for non-standard version formats
            return (0, 0, 0)

    @property
    def release_date_str(self) -> str:
        """Return formatted release date string in Swedish format"""
        return self.published_at.strftime('%Y-%m-%d')


@dataclass
class UpdateCheckResult:
    """Result of checking for updates"""
    success: bool                                   # Whether the check was successful
    update_available: bool                         # Whether an update is available
    current_version: str                          # Current application version
    latest_version: Optional[str] = None          # Latest version if available
    update_info: Optional[UpdateInfo] = None      # Detailed update information
    error_message: Optional[str] = None           # Error message if check failed

    @property
    def is_newer_version_available(self) -> bool:
        """Check if a newer version is actually available"""
        if not self.success or not self.update_info:
            return False
        return self.update_available and self.update_info.version_tuple > self._current_version_tuple

    @property
    def _current_version_tuple(self) -> Tuple[int, ...]:
        """Convert current version to tuple for comparison"""
        clean_version = self.current_version.lstrip('v')
        try:
            return tuple(map(int, clean_version.split('.')))
        except ValueError:
            return (0, 0, 0)
