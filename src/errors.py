"""
Error handling for the Prod CLI tool.
"""


class ConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


class RezError(Exception):
    """Exception raised for Rez errors."""

    pass
