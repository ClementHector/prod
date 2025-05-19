"""
Error handling for the Prod CLI tool.

This module provides custom exception classes to handle different types of errors
in the application, making error handling more specific and informative.
"""


class ProdError(Exception):
    """Base exception class for all Prod CLI tool errors."""

    def __init__(self, message: str = "An error occurred in the Prod CLI tool") -> None:
        self.message = message
        super().__init__(self.message)


class ConfigError(ProdError):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str = "Configuration error") -> None:
        super().__init__(message)


class RezError(ProdError):
    """Exception raised for Rez-related errors."""

    def __init__(self, message: str = "Rez operation failed") -> None:
        super().__init__(message)


class EnvironmentError(ProdError):
    """Exception raised for environment-related errors."""

    def __init__(self, message: str = "Environment operation failed") -> None:
        super().__init__(message)


class ValidationError(ProdError):
    """Exception raised for input validation errors."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message)
