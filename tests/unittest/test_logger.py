"""
Unit tests for the Logger class.
"""

from unittest import mock

from src.logger import Logger


def test_logger_initialization():
    """Test logger initialization with default settings."""
    logger = Logger()
    assert logger.logger.level == 20

    logger = Logger(verbose=False)
    assert logger.logger.level == 20

    logger = Logger(verbose=True)
    assert logger.logger.level == 10


def test_logger_handlers():
    """Test logger handlers configuration."""
    logger = Logger()

    assert logger.logger is not None

    assert len(logger.logger.handlers) == 1

    assert all(not hasattr(h, "baseFilename") for h in logger.logger.handlers)


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
    logger = Logger()
    assert logger.logger.level == 20

    logger.set_log_level("DEBUG")
    assert logger.logger.level == 10

    logger.set_log_level("ERROR")
    assert logger.logger.level == 40
