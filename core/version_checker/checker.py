"""
GitHub version checker implementation
Handles secure checking for application updates
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import requests

from .exceptions import NetworkError, RateLimitError, SecurityError, ValidationError
from .models import UpdateAsset, UpdateCheckResult, UpdateInfo
from .validator import NetworkValidator

logger = logging.getLogger(__name__)


class VersionChecker:
    """Secure GitHub version checker for DJs Timeline-maskin"""

    def __init__(self, current_version: str, repo_owner: str, repo_name: str):
        """Initialize version checker with current version and repository info"""
        self.current_version = current_version.lstrip('v')  # Remove 'v' prefix if present
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.validator = NetworkValidator(repo_owner, repo_name)

        # Build API URL
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    def check_for_updates(self, skip_versions: Optional[List[str]] = None) -> UpdateCheckResult:
        """
        Check for available updates from GitHub
        
        Args:
            skip_versions: List of versions to skip (user preference)
            
        Returns:
            UpdateCheckResult with update information or error details
        """
        skip_versions = skip_versions or []

        try:
            logger.info("Starting update check for DJs Timeline-maskin")

            # Validate API URL
            self.validator.validate_api_url(self.api_url)

            # Make secure HTTP request
            update_info = self._fetch_latest_release()

            if not update_info:
                return UpdateCheckResult(
                    success=True,
                    update_available=False,
                    current_version=f"v{self.current_version}",
                    error_message="No releases found"
                )

            # Check if this version should be skipped
            if update_info.version in skip_versions or update_info.tag_name in skip_versions:
                logger.info(f"Skipping version {update_info.version} (user preference)")
                return UpdateCheckResult(
                    success=True,
                    update_available=False,
                    current_version=f"v{self.current_version}",
                    latest_version=update_info.version,
                    error_message=f"Version {update_info.version} is available but was skipped"
                )

            # Check if update is newer than current version
            is_newer = self._is_newer_version(self.current_version, update_info.version)

            result = UpdateCheckResult(
                success=True,
                update_available=is_newer,
                current_version=f"v{self.current_version}",
                latest_version=update_info.version,
                update_info=update_info if is_newer else None
            )

            if is_newer:
                logger.info(f"Update available: v{self.current_version} -> v{update_info.version}")
            else:
                logger.info(f"No update available. Current: v{self.current_version}, Latest: v{update_info.version}")

            return result

        except RateLimitError as e:
            logger.warning(f"GitHub API rate limit exceeded: {e}")
            return UpdateCheckResult(
                success=False,
                update_available=False,
                current_version=f"v{self.current_version}",
                error_message="GitHub API rate limit exceeded. Please try again later."
            )

        except NetworkError as e:
            logger.error(f"Network error during update check: {e}")
            return UpdateCheckResult(
                success=False,
                update_available=False,
                current_version=f"v{self.current_version}",
                error_message=f"Network error: {str(e)}"
            )

        except (SecurityError, ValidationError) as e:
            logger.error(f"Security/validation error during update check: {e}")
            return UpdateCheckResult(
                success=False,
                update_available=False,
                current_version=f"v{self.current_version}",
                error_message=f"Security validation failed: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error during update check: {e}")
            return UpdateCheckResult(
                success=False,
                update_available=False,
                current_version=f"v{self.current_version}",
                error_message=f"Unexpected error: {str(e)}"
            )

    def _fetch_latest_release(self) -> Optional[UpdateInfo]:
        """Fetch latest release information from GitHub API"""
        try:
            # Get secure request configuration
            config = self.validator.get_secure_request_config()

            logger.debug(f"Making request to: {self.api_url}")
            response = requests.get(self.api_url, **config)

            # Handle different HTTP status codes
            if response.status_code == 404:
                logger.warning("Repository or releases not found")
                return None

            elif response.status_code == 403:
                # Check if it's a rate limit issue
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    if remaining == '0':
                        raise RateLimitError("GitHub API rate limit exceeded")
                raise NetworkError("Access forbidden (HTTP 403)")

            elif response.status_code != 200:
                raise NetworkError(f"GitHub API returned status code: {response.status_code}")

            # Validate and parse JSON response
            release_data = self.validator.validate_json_response(response.text)

            # Convert to our data model
            return self._parse_release_data(release_data)

        except requests.exceptions.Timeout:
            raise NetworkError("Request timeout - GitHub API is not responding")

        except requests.exceptions.SSLError as e:
            raise SecurityError(f"SSL certificate validation failed: {str(e)}")

        except requests.exceptions.ConnectionError:
            raise NetworkError("Could not connect to GitHub API - check your internet connection")

        except requests.exceptions.RequestException as e:
            raise NetworkError(f"HTTP request failed: {str(e)}")

    def _parse_release_data(self, data: dict) -> UpdateInfo:
        """Parse GitHub API release data into UpdateInfo object"""
        try:
            # Extract basic information
            tag_name = data.get('tag_name', '')
            version = tag_name.lstrip('v')  # Remove 'v' prefix

            # Validate version format
            if not self.validator.validate_version_string(tag_name):
                raise ValidationError(f"Invalid version format: {tag_name}")

            # Parse published date
            published_str = data.get('published_at', '')
            try:
                published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Could not parse publish date: {published_str}")
                published_at = datetime.now(timezone.utc)

            # Validate and sanitize HTML URL
            html_url = data.get('html_url', '')
            if html_url:
                self.validator.validate_github_release_url(html_url)

            # Parse assets
            assets = self._parse_assets(data.get('assets', []))

            # Sanitize text fields
            name = self.validator.sanitize_string(data.get('name', ''), 100)
            body = self.validator.sanitize_string(data.get('body', ''), 10000)

            return UpdateInfo(
                version=version,
                tag_name=tag_name,
                name=name,
                body=body,
                published_at=published_at,
                html_url=html_url,
                assets=assets,
                is_prerelease=data.get('prerelease', False),
                is_draft=data.get('draft', False)
            )

        except (KeyError, TypeError, ValueError) as e:
            raise ValidationError(f"Invalid release data format: {str(e)}")

    def _parse_assets(self, assets_data: list) -> List[UpdateAsset]:
        """Parse GitHub release assets"""
        assets = []

        for asset_data in assets_data[:10]:  # Limit to 10 assets for safety
            try:
                if not isinstance(asset_data, dict):
                    continue

                name = self.validator.sanitize_string(asset_data.get('name', ''), 100)
                download_url = asset_data.get('browser_download_url', '')
                size = asset_data.get('size', 0)
                content_type = asset_data.get('content_type', '')

                # Validate download URL if present
                if download_url and not self.validator._is_safe_url(download_url):
                    logger.warning(f"Skipping asset with unsafe URL: {download_url}")
                    continue

                # Validate size
                if not isinstance(size, int) or size < 0:
                    size = 0

                assets.append(UpdateAsset(
                    name=name,
                    download_url=download_url,
                    size=size,
                    content_type=content_type
                ))

            except Exception as e:
                logger.warning(f"Could not parse asset: {e}")
                continue

        return assets

    def _is_newer_version(self, current: str, latest: str) -> bool:
        """Compare version strings to determine if latest is newer than current"""
        try:
            current_tuple = self._version_to_tuple(current)
            latest_tuple = self._version_to_tuple(latest)

            logger.debug(f"Version comparison: {current_tuple} vs {latest_tuple}")
            return latest_tuple > current_tuple

        except ValueError as e:
            logger.error(f"Version comparison error: {e}")
            return False

    def _version_to_tuple(self, version: str) -> Tuple[int, ...]:
        """Convert version string to tuple for comparison"""
        # Remove 'v' prefix and clean up
        clean_version = version.lstrip('v').strip()

        # Handle pre-release versions (e.g., "2.7.0-beta.1")
        if '-' in clean_version:
            base_version, pre_release = clean_version.split('-', 1)
            # Pre-release versions are considered lower than release versions
            # We'll add a small negative number to represent this
            base_tuple = tuple(map(int, base_version.split('.')))
            return base_tuple + (-1,)  # Pre-release marker
        else:
            return tuple(map(int, clean_version.split('.')))

    def get_current_version_tuple(self) -> Tuple[int, ...]:
        """Get current version as tuple for external comparison"""
        return self._version_to_tuple(self.current_version)
