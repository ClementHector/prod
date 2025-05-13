"""
Error handling for the Prod CLI tool.
"""
import json
import os
import sys
from typing import Dict, Optional

from src.logger import Logger


class ErrorHandler:
    """
    Handles errors and provides clear error messages with resolution suggestions.
    """
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initializes the error handler.
        
        Args:
            logger: Logger instance to use for logging errors
        """
        self.logger = logger
        self.error_messages = self._load_error_messages()
    
    def _load_error_messages(self) -> Dict[str, Dict[str, str]]:
        """
        Loads error messages from the error messages file.
        
        Returns:
            Dictionary of error messages
        """
        # Default error messages
        default_messages = {
            "FileNotFoundError": {
                "message": "The specified file was not found: {error}",
                "solution": "Check if the file exists and if you have permission "
                           "to access it."
            },
            "PermissionError": {
                "message": "You don't have permission to access this file: {error}",
                "solution": "Check your file permissions or run the command "
                           "with elevated privileges."
            },
            "ConfigError": {
                "message": "Configuration error: {error}",
                "solution": "Check your configuration files for syntax errors "
                           "or missing values."
            },
            "RezError": {
                "message": "Rez error: {error}",
                "solution": "Make sure Rez is installed and properly configured."
            },
            "ValueError": {
                "message": "Invalid value: {error}",
                "solution": "Check the values you provided and make sure they are valid."
            },
            "KeyError": {
                "message": "Missing key: {error}",
                "solution": "Check your configuration files for missing keys."
            }
        }
        
        # Try to load custom error messages
        error_messages_path = os.path.join(
            os.path.dirname(__file__), '../config/error_messages.json'
        )
        if os.path.exists(error_messages_path):
            try:
                with open(error_messages_path, 'r') as f:
                    custom_messages = json.load(f)
                    # Merge default and custom messages
                    default_messages.update(custom_messages)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to load custom error messages: {e}")
        
        return default_messages
    
    def handle_error(self, error: Exception, exit_program: bool = False) -> None:
        """
        Handles an error and displays an appropriate message.
        
        Args:
            error: The exception to handle
            exit_program: Whether to exit the program after handling the error
        """
        error_type = type(error).__name__
        
        if error_type in self.error_messages:
            self._display_error_message(error_type, error)
            self._suggest_solution(error_type)
        else:
            # Generic error handling
            print(f"Error: {error}")
            
        # Log the error
        if self.logger:
            self.logger.error(f"{error_type}: {str(error)}")
            
        if exit_program:
            sys.exit(1)
    
    def _display_error_message(self, error_type: str, error: Exception) -> None:
        """
        Displays an error message for the given error.
        
        Args:
            error_type: Type of the error
            error: The exception
        """
        message_template = self.error_messages[error_type]["message"]
        message = message_template.format(error=str(error))
        print(f"Error: {message}")
    
    def _suggest_solution(self, error_type: str) -> None:
        """
        Suggests a solution for the given error.
        
        Args:
            error_type: Type of the error
        """
        solution = self.error_messages[error_type]["solution"]
        print(f"Suggestion: {solution}")


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class RezError(Exception):
    """Exception raised for Rez errors."""
    pass 