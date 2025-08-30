"""
Network security validator for GitHub API interactions
Implements comprehensive security measures for version checking
"""

import json
import logging
import re
import ssl
from typing import Any, Dict
from urllib.parse import urlparse

from .exceptions import SecurityError, ValidationError

logger = logging.getLogger(__name__)

# Security configuration constants
MAX_JSON_RESPONSE_SIZE = 1024 * 50  # 50KB maximum for GitHub API responses
MAX_REQUEST_TIMEOUT = 10  # 10 seconds maximum timeout
MAX_VERSION_LENGTH = 20   # Maximum length for version strings
MAX_URL_LENGTH = 200      # Maximum length for URLs


class NetworkValidator:
    """Secure network operations validator for GitHub API interactions"""

    def __init__(self, repo_owner: str, repo_name: str):
        """Initialize validator with repository information"""
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.valid_github_domains = {'api.github.com', 'github.com'}

        # Compiled regex patterns for performance
        self.version_pattern = re.compile(r'^v?\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+(?:\.\d+)?)?$')
        self.github_release_path_pattern = re.compile(
            r'^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/releases(?:/tag/v?\d+\.\d+\.\d+.*)?$'
        )

    def validate_api_url(self, url: str) -> bool:
        """Validate that URL is a legitimate GitHub API URL"""
        try:
            if len(url) > MAX_URL_LENGTH:
                raise SecurityError(f"URL too long: {len(url)} characters")

            if not url.startswith("https://"):
                raise SecurityError("Only HTTPS URLs are allowed")

            parsed = urlparse(url)

            # Validate domain
            if parsed.netloc not in self.valid_github_domains:
                raise SecurityError(f"Invalid domain: {parsed.netloc}")

            # Validate API endpoint path
            expected_path = f"/repos/{self.repo_owner}/{self.repo_name}/releases"
            if parsed.netloc == 'api.github.com':
                if not parsed.path.startswith(expected_path):
                    raise SecurityError(f"Invalid API path: {parsed.path}")

            return True

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            logger.error(f"URL validation error: {e}")
            raise SecurityError(f"URL validation failed: {str(e)}")

    def validate_github_release_url(self, url: str) -> bool:
        """Validate GitHub release page URL for browser opening"""
        try:
            if len(url) > MAX_URL_LENGTH:
                raise SecurityError(f"URL too long: {len(url)} characters")

            if not url.startswith("https://github.com"):
                raise SecurityError("Only GitHub release URLs are allowed")

            parsed = urlparse(url)

            # Validate domain
            if parsed.netloc != 'github.com':
                raise SecurityError(f"Invalid domain for release URL: {parsed.netloc}")

            # Validate path format
            if not self.github_release_path_pattern.match(parsed.path):
                raise SecurityError(f"Invalid GitHub release path format: {parsed.path}")

            # Ensure it's for the correct repository
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                if path_parts[0] != self.repo_owner or path_parts[1] != self.repo_name:
                    raise SecurityError("URL is not for the expected repository")

            return True

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            logger.error(f"Release URL validation error: {e}")
            raise SecurityError(f"Release URL validation failed: {str(e)}")

    def get_secure_request_config(self) -> Dict[str, Any]:
        """Get secure configuration for HTTP requests"""
        return {
            'timeout': MAX_REQUEST_TIMEOUT,
            'verify': True,  # Always verify SSL certificates
            'allow_redirects': False,  # No automatic redirects for security
            'stream': False,  # Don't stream to control response size
            'headers': {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'DJs-Timeline-Machine-UpdateChecker/1.0',
                'Accept-Encoding': 'gzip, deflate'
            }
        }

    def validate_json_response(self, response_text: str) -> Dict[str, Any]:
        """Safely parse and validate JSON response from GitHub API"""
        try:
            # Check response size
            if len(response_text) > MAX_JSON_RESPONSE_SIZE:
                raise SecurityError(
                    f"Response too large: {len(response_text)} bytes (max: {MAX_JSON_RESPONSE_SIZE})"
                )

            # Parse JSON safely
            data = json.loads(response_text)

            # Validate JSON structure for GitHub release API response
            if not isinstance(data, dict):
                raise ValidationError("Response must be a JSON object")

            # Check for required fields in release data
            required_fields = ['tag_name', 'name', 'html_url', 'published_at']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(f"Missing required fields: {missing_fields}")

            # Validate individual fields
            self._validate_release_fields(data)

            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValidationError(f"Invalid JSON response: {str(e)}")
        except (SecurityError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in JSON validation: {e}")
            raise ValidationError(f"JSON validation failed: {str(e)}")

    def _validate_release_fields(self, data: Dict[str, Any]) -> None:
        """Validate individual fields in GitHub release data"""
        # Validate tag_name (version)
        tag_name = data.get('tag_name', '')
        if not self.validate_version_string(tag_name):
            raise ValidationError(f"Invalid version format in tag_name: {tag_name}")

        # Validate HTML URL
        html_url = data.get('html_url', '')
        if html_url and not self._is_safe_url(html_url):
            raise ValidationError(f"Unsafe HTML URL: {html_url}")

        # Validate name field
        name = data.get('name', '')
        if len(name) > 100:  # Reasonable limit for release names
            raise ValidationError("Release name too long")

        # Validate body (release notes) length
        body = data.get('body', '')
        if len(body) > 10000:  # 10KB limit for release notes
            raise ValidationError("Release notes too long")

        # Validate assets if present
        assets = data.get('assets', [])
        if isinstance(assets, list):
            for asset in assets:
                self._validate_asset_fields(asset)

    def _validate_asset_fields(self, asset: Dict[str, Any]) -> None:
        """Validate GitHub release asset fields"""
        if not isinstance(asset, dict):
            raise ValidationError("Asset must be an object")

        # Validate asset name
        name = asset.get('name', '')
        if len(name) > 100:
            raise ValidationError("Asset name too long")

        # Validate download URL
        download_url = asset.get('browser_download_url', '')
        if download_url and not self._is_safe_url(download_url):
            raise ValidationError(f"Unsafe asset download URL: {download_url}")

        # Validate size (should be reasonable)
        size = asset.get('size', 0)
        if not isinstance(size, int) or size < 0:
            raise ValidationError("Invalid asset size")

    def _is_safe_url(self, url: str) -> bool:
        """Check if URL is safe (GitHub domain only)"""
        try:
            if not url.startswith('https://'):
                return False
            parsed = urlparse(url)
            return parsed.netloc in {'github.com', 'objects.githubusercontent.com'}
        except Exception:
            return False

    def validate_version_string(self, version: str) -> bool:
        """Validate version string format and safety"""
        if not version or len(version) > MAX_VERSION_LENGTH:
            return False

        # Check for dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '|', ';', '`', '$', '\\', '/']
        if any(char in version for char in dangerous_chars):
            logger.warning(f"Dangerous characters in version string: {version}")
            return False

        # Validate against regex pattern
        return bool(self.version_pattern.match(version))

    def sanitize_string(self, text: str, max_length: int = 1000) -> str:
        """Sanitize string for safe display in UI"""
        if not text:
            return ""

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Remove potentially dangerous characters
        # Keep only printable ASCII and common Unicode characters
        safe_chars = []
        for char in text:
            if ord(char) >= 32 and ord(char) <= 126:  # Printable ASCII
                safe_chars.append(char)
            elif char in '\n\r\t':  # Common whitespace
                safe_chars.append(char)
            elif ord(char) > 127:  # Unicode characters (for Swedish text)
                safe_chars.append(char)

        return ''.join(safe_chars).strip()

    def create_ssl_context(self) -> ssl.SSLContext:
        """Create secure SSL context for HTTPS requests"""
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        # Additional security settings
        context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA')

        return context
