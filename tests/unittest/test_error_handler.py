"""
Unit tests for the ErrorHandler class.
"""

from unittest import mock

import pytest

from src.error_handler import ConfigError, ErrorHandler, RezError


@pytest.fixture
def error_handler():
    """Fixture to create an ErrorHandler instance."""
    with mock.patch("src.error_handler.get_logger"):
        return ErrorHandler()


@pytest.fixture
def mock_error_messages():
    """Fixture to create mock error messages."""
    return {
        "FileNotFoundError": {
            "message": "The specified file was not found: {error}",
            "solution": "Check if the file exists and if you have permission to access it.",
        },
        "PermissionError": {
            "message": "You don't have permission to access this file: {error}",
            "solution": "Check your file permissions or run the command with elevated privileges.",
        },
        "ConfigError": {
            "message": "Configuration error: {error}",
            "solution": "Check your configuration files for syntax errors or missing values.",
        },
        "CustomError": {
            "message": "Custom error: {error}",
            "solution": "Custom solution for custom error.",
        },
    }


def test_init(error_handler):
    """Test that ErrorHandler initializes correctly."""
    assert error_handler.logger is not None
    assert isinstance(error_handler.error_messages, dict)


def test_load_default_error_messages(error_handler):
    """Test that default error messages are loaded."""
    assert "FileNotFoundError" in error_handler.error_messages
    assert "PermissionError" in error_handler.error_messages
    assert "ConfigError" in error_handler.error_messages
    assert "RezError" in error_handler.error_messages
    assert "ValueError" in error_handler.error_messages
    assert "KeyError" in error_handler.error_messages


@mock.patch("os.path.exists", return_value=True)
@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("json.load")
def test_load_custom_error_messages(
    mock_json_load, mock_open, mock_exists, error_handler
):
    """Test that custom error messages are loaded and merged with defaults."""
    custom_messages = {
        "CustomError": {"message": "Custom message", "solution": "Custom solution"}
    }
    mock_json_load.return_value = custom_messages

    # Call _load_error_messages directly
    messages = error_handler._load_error_messages()

    mock_exists.assert_called_once()
    mock_open.assert_called_once()
    mock_json_load.assert_called_once()
    assert "CustomError" in messages
    assert "FileNotFoundError" in messages  # Default message still exists


@mock.patch("os.path.exists", return_value=True)
@mock.patch("builtins.open", side_effect=Exception("Error reading file"))
def test_load_error_messages_exception(mock_open, mock_exists, error_handler):
    """Test handling of exceptions when loading custom error messages."""
    # Call _load_error_messages directly
    messages = error_handler._load_error_messages()

    # Should still have default messages
    assert "FileNotFoundError" in messages
    assert "PermissionError" in messages


@mock.patch("builtins.print")
def test_handle_known_error(mock_print, error_handler):
    """Test handling of a known error type."""
    with mock.patch.object(error_handler, "_display_error_message") as mock_display:
        with mock.patch.object(error_handler, "_suggest_solution") as mock_suggest:
            error_handler.handle_error(FileNotFoundError("test.txt"))

            mock_display.assert_called_once_with("FileNotFoundError", mock.ANY)
            mock_suggest.assert_called_once_with("FileNotFoundError")


@mock.patch("builtins.print")
def test_handle_unknown_error(mock_print, error_handler):
    """Test handling of an unknown error type."""

    class UnknownError(Exception):
        pass

    error_handler.handle_error(UnknownError("Something unusual happened"))
    mock_print.assert_called_once_with("Error: Something unusual happened")


@mock.patch("builtins.print")
def test_display_error_message(mock_print, error_handler, mock_error_messages):
    """Test displaying error message."""
    with mock.patch.object(error_handler, "error_messages", mock_error_messages):
        error_handler._display_error_message(
            "ConfigError", ConfigError("Invalid config")
        )
        mock_print.assert_called_once_with("Error: Configuration error: Invalid config")


@mock.patch("builtins.print")
def test_suggest_solution(mock_print, error_handler, mock_error_messages):
    """Test suggesting solution."""
    with mock.patch.object(error_handler, "error_messages", mock_error_messages):
        error_handler._suggest_solution("ConfigError")
        mock_print.assert_called_once_with(
            "Suggestion: Check your configuration files for syntax errors or missing values."
        )


@mock.patch("sys.exit")
def test_handle_error_exit(mock_exit, error_handler):
    """Test handling error with exit."""
    error_handler.handle_error(ConfigError("Invalid config"), exit_program=True)
    mock_exit.assert_called_once_with(1)


def test_custom_exceptions():
    """Test custom exception classes."""
    config_error = ConfigError("Missing value")
    assert isinstance(config_error, Exception)
    assert str(config_error) == "Missing value"

    rez_error = RezError("Rez package not found")
    assert isinstance(rez_error, Exception)
    assert str(rez_error) == "Rez package not found"
