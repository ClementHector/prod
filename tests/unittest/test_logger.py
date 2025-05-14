"""
Tests unitaires pour la classe Logger.
"""

import os
import tempfile
import time
from unittest import mock

import pytest

from src.logger import Logger


@pytest.fixture
def temp_log_file():
    """Create a temporary log file."""
    temp_dir = tempfile.TemporaryDirectory()
    log_file = os.path.join(temp_dir.name, "test.log")

    yield log_file

    # Cleanup - ignore errors as Windows may have file locks
    try:
        temp_dir.cleanup()
    except PermissionError:
        # On Windows, the file might still be locked
        pass


def test_logger_initialization():
    """Test logger initialization with default settings."""
    logger = Logger()
    assert logger.logger.level == 20  # INFO level

    # Test with DEBUG level
    logger = Logger(log_level="DEBUG")
    assert logger.logger.level == 10  # DEBUG level


def test_logger_with_file(temp_log_file):
    """Test logger with a log file."""
    logger = Logger(log_level="INFO", log_file=temp_log_file)

    # Log a message
    test_message = "Test log message"
    logger.info(test_message)

    # Explicitly close all handlers to release the file lock
    for handler in logger.logger.handlers:
        handler.flush()
        handler.close()

    # Clear handlers to ensure they're not used again
    logger.logger.handlers.clear()

    # Give the OS a moment to release the file lock
    time.sleep(0.1)

    # Check that the message was written to the file
    with open(temp_log_file, "r") as f:
        content = f.read()
        assert test_message in content


def test_logging_methods():
    """Test all logging methods."""
    logger = Logger()

    with mock.patch.object(logger.logger, "debug") as mock_debug:
        logger.debug("Debug message")
        mock_debug.assert_called_once_with("Debug message")

    with mock.patch.object(logger.logger, "info") as mock_info:
        logger.info("Info message")
        mock_info.assert_called_once_with("Info message")

    with mock.patch.object(logger.logger, "warning") as mock_warning:
        logger.warning("Warning message")
        mock_warning.assert_called_once_with("Warning message")

    with mock.patch.object(logger.logger, "error") as mock_error:
        logger.error("Error message")
        mock_error.assert_called_once_with("Error message")

    with mock.patch.object(logger.logger, "critical") as mock_critical:
        logger.critical("Critical message")
        mock_critical.assert_called_once_with("Critical message")


def test_set_log_level():
    """Test setting the log level."""
    logger = Logger(log_level="INFO")
    assert logger.logger.level == 20  # INFO level

    logger.set_log_level("DEBUG")
    assert logger.logger.level == 10  # DEBUG level

    logger.set_log_level("ERROR")
    assert logger.logger.level == 40  # ERROR level


def test_get_log_file_path():
    """Test getting a log file path."""
    # Test with no production
    log_path = Logger.get_log_file_path()
    norm_log_path = os.path.normpath(log_path)
    assert (
        os.path.normpath(".prod/logs/prod_") in norm_log_path
        or os.path.normpath(".prod\\logs\\prod_") in norm_log_path
    )

    # Test with production
    log_path = Logger.get_log_file_path(production="test_prod")
    norm_log_path = os.path.normpath(log_path)
    assert (
        os.path.normpath(".prod/logs/test_prod/prod_") in norm_log_path
        or os.path.normpath(".prod\\logs\\test_prod\\prod_") in norm_log_path
    )
