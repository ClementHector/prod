"""
Unit tests for the CLI class.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.cli import CLI
from src.logger import Logger


@pytest.fixture
def cli():
    """
    Fixture to create a CLI instance.

    Returns:
        CLI instance
    """
    return CLI()


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
    Test running the CLI with no arguments shows help.
    """
    with patch("argparse.ArgumentParser.print_help") as mock_print_help:
        result = cli.run([])

        # Check that print_help was called
        mock_print_help.assert_called_once()

        # Check the return code
        assert result == 0


def test_cli_run_list_command(cli):
    """
    Test running the CLI with the list command.
    """
    # Mock the _handle_list_command method
    with patch.object(cli, "_handle_list_command") as mock_handle_list:
        mock_handle_list.return_value = 0

        # Run the CLI with the list command
        result = cli.run(["list"])

        # Check that the list handler was called
        mock_handle_list.assert_called_once()

        # Check the return code
        assert result == 0


def test_cli_run_production_name(cli):
    """
    Test running the CLI with a production name.
    """
    # Mock the _handle_enter_command method
    with patch.object(cli, "_handle_enter_command") as mock_handle_enter:
        mock_handle_enter.return_value = 0

        # Run the CLI with a production name
        result = cli.run(["dlt"])

        # Check that the enter handler was called with the production name
        assert mock_handle_enter.call_count == 1
        args = mock_handle_enter.call_args[0][0]
        assert args.production == "dlt"

        # Check the return code
        assert result == 0


def test_handle_enter_command_activates_environment(cli):
    """
    Test that _handle_enter_command activates the production environment.
    """
    # Create a mock production environment
    mock_env = MagicMock()

    # Mock the ProductionEnvironment class
    with patch("src.cli.ProductionEnvironment", return_value=mock_env) as mock_prod_env:
        # Create mock args
        args = MagicMock()
        args.production = "test_prod"

        # Call the enter command handler
        result = cli._handle_enter_command(args)

        # Check that ProductionEnvironment was created with the production name
        mock_prod_env.assert_called_once_with("test_prod")

        # Check that activate was called
        mock_env.activate.assert_called_once()

        # Check the return code
        assert result == 0
