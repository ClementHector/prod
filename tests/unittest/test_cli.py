"""
Unit tests for the CLI class.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.cli import PRODUCTIONCLI
from src.logger import Logger


@pytest.fixture
def cli():
    """
    Fixture to create a CLI instance.

    Returns:
        CLI instance
    """
    return PRODUCTIONCLI()


@pytest.fixture
def logger():
    """
    Fixture to create a mock logger.

    Returns:
        Mock logger
    """
    return MagicMock(spec=Logger)


def test_cli_run_no_args(cli):
    """
    Test running the CLI with no arguments shows error.
    """
    # Since the new CLI requires a production argument or --list flag
    # we expect it to return 1 (error) when no arguments are provided
    result = cli.run([])

    # Check the return code (should be 1 for error)
    assert result == 1


@patch.object(PRODUCTIONCLI, "_handle_list_command")
def test_cli_run_list_command(mock_handle_list, cli):
    """
    Test running the CLI with the list command.
    """
    mock_handle_list.return_value = 0

    # Run the CLI with the --list flag
    result = cli.run(["--list"])

    # Check that the list handler was called
    mock_handle_list.assert_called_once()

    # Check the return code
    assert result == 0


@patch("src.cli.list_prod_names")
@patch.object(PRODUCTIONCLI, "_handle_enter_command")
def test_cli_run_production_name(mock_handle_enter, mock_list_prod_names, cli):
    """
    Test running the CLI with a production name.
    """
    mock_handle_enter.return_value = 0
    mock_list_prod_names.return_value = ["dlt", "tld"]

    # Run the CLI with a production name
    result = cli.run(["dlt"])

    # Check that the enter handler was called with the production name and verbose flag
    mock_handle_enter.assert_called_once_with("dlt", False)

    # Check the return code
    assert result == 0


@patch("src.cli.ProductionEnvironment")
def test_handle_enter_command_activates_environment(mock_prod_env, cli):
    """
    Test that _handle_enter_command activates the production environment.
    """
    # Create a mock production environment
    mock_env = MagicMock()
    mock_prod_env.return_value = mock_env

    # Call the enter command handler with the new signature
    result = cli._handle_enter_command("test_prod", False)

    # Check that ProductionEnvironment was created with the production name and verbose flag
    mock_prod_env.assert_called_once_with("test_prod", verbose=False)

    # Check that activate was called
    mock_env.activate.assert_called_once()

    # Check the return code
    assert result == 0
