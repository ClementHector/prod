"""
Unit tests for the Logger class.
"""

import pytest
from unittest import mock

from src.logger import Logger


@pytest.mark.parametrize("verbose,expected_level", [
    (None, 20),  # Default behavior (no verbose parameter)
    (False, 20),  # Explicit verbose=False
    (True, 10),   # Explicit verbose=True
])
def test_logger_initialization(verbose, expected_level):
    """Test logger initialization with different verbose settings."""
    if verbose is None:
        logger = Logger()  # Default initialization
    else:
        logger = Logger(verbose=verbose)
    assert logger.logger.level == expected_level


def test_logger_handlers():
    """Test logger handlers configuration."""
    logger = Logger()

    assert logger.logger is not None

    assert len(logger.logger.handlers) == 1

    assert all(not hasattr(h, "baseFilename") for h in logger.logger.handlers)


@pytest.mark.parametrize(
    "method_name,message",
    [
        ("debug", "Debug message"),
        ("info", "Info message"),
        ("warning", "Warning message"),
        ("error", "Error message"),
        ("critical", "Critical message"),
    ]
)
def test_logging_methods(method_name, message):
    """Test all logging methods with parametrized inputs."""
    logger = Logger()

    with mock.patch.object(logger.logger, method_name) as mock_method:
        getattr(logger, method_name)(message)
        mock_method.assert_called_once_with(message)


@pytest.mark.parametrize("log_level,expected_level", [
    ("DEBUG", 10),
    ("INFO", 20),
    ("WARNING", 30),
    ("ERROR", 40),
    ("CRITICAL", 50),
])
def test_set_log_level(log_level, expected_level):
    """Test setting the log level with parametrized inputs."""
    logger = Logger()
    logger.set_log_level(log_level)
    assert logger.logger.level == expected_level
