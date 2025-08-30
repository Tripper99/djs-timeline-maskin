"""
Custom exceptions for version checking functionality
"""


class UpdateCheckError(Exception):
    """Base exception for version checking operations"""
    pass


class NetworkError(UpdateCheckError):
    """Exception raised for network-related errors during version checking"""
    pass


class ValidationError(UpdateCheckError):
    """Exception raised when data validation fails"""
    pass


class RateLimitError(UpdateCheckError):
    """Exception raised when GitHub API rate limits are exceeded"""
    pass


class SecurityError(UpdateCheckError):
    """Exception raised for security-related validation failures"""
    pass
