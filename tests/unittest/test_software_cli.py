"""
Unit tests for the SoftwareCLI class.
"""

import os
from unittest import mock

import pytest

from src.errors import ConfigError, RezError
from src.software_cli import SoftwareCLI


@pytest.fixture
def software_cli():
    """
    Fixture to create a SoftwareCLI instance with mocked dependencies.
    """
    return SoftwareCLI("maya")


def test_initialization():
    """Test SoftwareCLI initialization."""
    cli = SoftwareCLI("maya")
    assert cli.software_name == "maya"
    assert cli.parser is not None
    assert cli.logger is None

def test_argument_parser_setup(software_cli):
    """Test argument parser setup."""
    parser = software_cli.parser

    # Check argument parser configuration
    assert parser.description == "maya launcher with Prod"

    # Check if all required arguments are defined
    args, _ = parser.parse_known_args(["--packages", "usd", "arnold"])
    assert args.packages == ["usd", "arnold"]

    args, _ = parser.parse_known_args(["--env-only"])
    assert args.env_only is True

    args, _ = parser.parse_known_args(["--verbose"])
    assert args.verbose is True

    args, _ = parser.parse_known_args(["-v"])  # Short version
    assert args.verbose is True

@mock.patch.dict(os.environ, {"PROD": "dlt"})
@mock.patch("src.software_cli.Logger")
@mock.patch("src.software_cli.ProductionEnvironment")
def test_run_success(mock_prod_env, mock_logger, software_cli):
    """Test successful run of SoftwareCLI."""
    # Setup mocks
    mock_env_instance = mock_prod_env.return_value

    # Test with default arguments (no --env-only, no --packages)
    result = software_cli.run([])

    # Verify calls
    mock_prod_env.assert_called_once_with("dlt")
    mock_env_instance.execute_software.assert_called_once_with(
        "maya", [], False, False
    )

    # Check result
    assert result == 0

@mock.patch.dict(os.environ, {"PROD": "dlt"})
@mock.patch("src.software_cli.Logger")
@mock.patch("src.software_cli.ProductionEnvironment")
def test_run_with_args(mock_prod_env, mock_logger, software_cli):
    """Test running SoftwareCLI with specific arguments."""
    # Setup mocks
    mock_env_instance = mock_prod_env.return_value

    # Test with specific arguments
    result = software_cli.run(
        ["--packages", "usd", "arnold", "--env-only", "--verbose"]
    )

    # Verify logger created with DEBUG level due to --verbose
    mock_logger.assert_called_once_with("DEBUG")

    # Verify calls to execute_software with correct arguments
    mock_env_instance.execute_software.assert_called_once_with(
        "maya", ["usd", "arnold"], True, False
    )

    # Check result
    assert result == 0

@mock.patch.dict(os.environ, {}, clear=True)  # Remove PROD from environment
def test_run_missing_prod(software_cli):
    """Test running when PROD environment variable is not set."""
    # Capture stdout to verify error message
    with mock.patch("builtins.print") as mock_print:
        result = software_cli.run([])

        # Verify error message was printed
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "No Variable PROD found" in call_args

        # Check result code
        assert result == 1

@mock.patch.dict(os.environ, {"PROD": "dlt"})
@mock.patch("src.software_cli.Logger")
@mock.patch("src.software_cli.ProductionEnvironment")
def test_run_with_config_error(mock_prod_env, mock_logger, software_cli):
    """Test handling of ConfigError."""
    # Setup mocks
    mock_env_instance = mock_prod_env.return_value
    mock_env_instance.execute_software.side_effect = ConfigError(
        "Configuration error"
    )

    # Run with the error
    result = software_cli.run([])

    # Check result code
    assert result == 1

@mock.patch.dict(os.environ, {"PROD": "dlt"})
@mock.patch("src.software_cli.Logger")
@mock.patch("src.software_cli.ProductionEnvironment")
def test_run_with_rez_error(mock_prod_env, mock_logger, software_cli):
    """Test handling of RezError."""
    # Setup mocks
    mock_env_instance = mock_prod_env.return_value
    mock_env_instance.execute_software.side_effect = RezError("Rez error")

    # Run with the error
    result = software_cli.run([])

    # Check result code
    assert result == 1
