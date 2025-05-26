"""
Logging system for the Prod CLI tool.

This module provides a centralized logging system with a singleton-based
approach to ensure consistent logging across the application.
"""

import logging

LOGGER_NAME = "prod"


class Logger:
    """
    Handles logging functionality with support for multiple verbosity levels.

    This class implements a singleton pattern to ensure only one logger instance
    exists throughout the application. It uses the standard Python logging system
    with simplified formatting.
    """

    def __init__(self, verbose: bool = False) -> None:
        """
        Initializes the logger with the specified verbosity level.

        Args:
            verbose: Whether to enable verbose logging (DEBUG level)
        """
        log_level = logging.DEBUG if verbose else logging.INFO
        self._logger = self._setup_logger(log_level)

    @property
    def logger(self) -> logging.Logger:
        """
        Access to the internal logger object.

        Returns:
            The internal logger instance
        """
        return self._logger

    def _setup_logger(self, log_level: int) -> logging.Logger:
        """
        Sets up the logging system with simplified output.

        Args:
            log_level: Logging level as an integer (e.g., logging.DEBUG)

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(LOGGER_NAME)

        if logger.handlers:
            logger.handlers.clear()

        logger.setLevel(log_level)

        formatter = logging.Formatter("%(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.propagate = False

        return logger

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        Args:
            message: Message to log
        """
        self._logger.debug(message)

    def info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message: Message to log
        """
        self._logger.info(message)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message: Message to log
        """
        self._logger.warning(message)

    def error(self, message: str) -> None:
        """
        Log an error message.

        Args:
            message: Message to log
        """
        self._logger.error(message)

    def critical(self, message: str) -> None:
        """
        Log a critical message.

        Args:
            message: Message to log
        """
        self._logger.critical(message)

    def set_log_level(self, level: str) -> None:
        """
        Set the logging level.

        Args:
            level: Logging level as string (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        """
        if hasattr(logging, level):
            self._logger.setLevel(getattr(logging, level))


def get_logger() -> logging.Logger:
    """
    Returns the singleton logger instance.

    This function ensures that only one logger instance is created
    and used throughout the application.

    Returns:
        Logger instance
    """
    return logging.getLogger(LOGGER_NAME)


def configure_logger(verbose: bool = False) -> None:
    """
    Configure the singleton logger with specified verbosity level.

    This function should be called early in the application startup
    to configure the logger before it's used elsewhere.

    Args:
        verbose: Whether to enable verbose logging (DEBUG level)
    """

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

