"""Custom exceptions for the referral network platform."""


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class DomainNotFoundError(Exception):
    """Raised when a requested domain is not found or not enabled."""
    pass


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found in any enabled domain."""
    pass


class DependencyError(Exception):
    """Raised when domain dependencies cannot be resolved."""
    pass
