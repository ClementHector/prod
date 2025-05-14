"""
Environment variable management for the Prod CLI tool.
"""

import os
import platform
from typing import Dict, List, Optional

from src.logger import Logger


class EnvironmentManager:
    """
    Manages environment variables for production environments.
    """

    def __init__(self, logger: Optional[Logger] = None):
        """
        Initializes the environment manager.

        Args:
            logger: Logger instance to use for logging
        """
        self.logger = logger
        self.system = platform.system()
        self.original_env = os.environ.copy()
        self.current_env = os.environ.copy()

    def set_environment_variables(self, variables: Dict[str, str]) -> None:
        """
        Sets up environment variables.

        Args:
            variables: Dictionary of environment variables to set
        """
        for key, value in variables.items():
            self._set_environment_variable(key, value)
            if self.logger:
                self.logger.debug(f"Set environment variable: {key}={value}")

    def _set_environment_variable(self, key: str, value: str) -> None:
        """
        Sets an environment variable.

        Args:
            key: Environment variable name
            value: Environment variable value
        """
        # Update the current environment
        self.current_env[key] = value

        # Set the environment variable in the process
        os.environ[key] = value

    def set_path_variables(self, path_variables: Dict[str, List[str]]) -> None:
        """
        Sets up path environment variables.

        Args:
            path_variables: Dictionary of path environment variables to set
        """
        for key, paths in path_variables.items():
            # Get the existing path
            existing_path = self.current_env.get(key, "")

            # Format paths according to the operating system
            formatted_paths = self._format_paths(paths)

            # Append the new paths to the existing path
            separator = self._get_path_separator()
            new_path = existing_path

            # Add each path if it's not already in the existing path
            for path in formatted_paths:
                # Normalize the path for comparison
                norm_path = self._normalize_path(path)

                # Check if the path is already in the existing path
                if existing_path and norm_path not in [
                    self._normalize_path(p) for p in existing_path.split(separator)
                ]:
                    new_path = f"{path}{separator}{new_path}" if new_path else path

            # Set the new path
            self._set_environment_variable(key, new_path)
            if self.logger:
                self.logger.debug(f"Set path variable: {key}={new_path}")

    def _format_paths(self, paths: List[str]) -> List[str]:
        """
        Formats paths according to the operating system.

        Args:
            paths: List of paths to format

        Returns:
            List of formatted paths
        """
        formatted_paths = []
        for path in paths:
            # Replace environment variables in the path
            path = os.path.expandvars(path)

            # Format for Windows
            if self.system == "Windows":
                path = path.replace("/", "\\")

            formatted_paths.append(path)

        return formatted_paths

    def _get_path_separator(self) -> str:
        """
        Gets the path separator for the current operating system.

        Returns:
            Path separator
        """
        return ";" if self.system == "Windows" else ":"

    def _normalize_path(self, path: str) -> str:
        """
        Normalizes a path for comparison.

        Args:
            path: Path to normalize

        Returns:
            Normalized path
        """
        return os.path.normpath(path.lower())

    def reset_environment(self) -> None:
        """
        Resets the environment to its original state.
        """
        # Clear the current environment
        os.environ.clear()

        # Set the original environment variables
        for key, value in self.original_env.items():
            os.environ[key] = value

        # Update the current environment
        self.current_env = self.original_env.copy()

        if self.logger:
            self.logger.debug("Reset environment to original state")
