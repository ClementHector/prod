"""
Logging system for the Prod CLI tool.
"""

import logging
from typing import Optional

LoggerName = "prod"


def get_logger() -> logging.Logger:
    """
    Returns the logger instance.

    Returns:
        Logger instance
    """
    return logging.getLogger(LoggerName)


class Logger:
    """
    Handles logging functionality with support for multiple verbosity levels.
    Uses the default Python logging system with simplified format.
    """

    def __init__(self, verbose: Optional[bool] = False):
        """
        Initializes the logger with the specified verbosity level.

        Args:
            verbose: Whether to enable verbose logging.

        """
        log_level = "DEBUG" if verbose else "INFO"
        self._logger = self._setup_logger(log_level)

    @property
    def logger(self):
        """
        Access to the internal logger object.

        Returns:
            Internal logger instance
        """
        return self._logger

    def _setup_logger(self, log_level: str):
        """
        Sets up the logging system with simplified output.

        Args:
            log_level: Logging level

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(LoggerName)

        if logger.handlers:
            logger.handlers.clear()

        logger.setLevel(getattr(logging, log_level))

        formatter = logging.Formatter("%(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

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

    def set_log_level(self, log_level: str) -> None:
        """
        Set the log level.

        Args:
            log_level: New log level
        """
        self._logger.setLevel(getattr(logging, log_level))
