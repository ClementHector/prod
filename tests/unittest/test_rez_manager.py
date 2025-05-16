"""
Unit tests for the RezManager class.
"""

import os
import platform
import subprocess
from unittest import mock

import pytest

from src.error_handler import RezError
from src.rez_manager import RezManager


@pytest.fixture
def rez_manager():
    """Fixture to create a RezManager instance with mocked dependencies."""
    with mock.patch("src.rez_manager.get_logger"):
        with mock.patch("src.rez_manager.platform.system", return_value="Windows"):
            with mock.patch("src.rez_manager.subprocess.run") as mock_run:
                # Mock successful rez validation
                mock_run.return_value = mock.MagicMock(returncode=0)
                manager = RezManager()
                # Make mock_run available to tests
                manager._mock_run = mock_run
                yield manager


def test_validate_rez_installation_success(rez_manager):
    """Test successful validation of Rez installation."""
    # Already called during initialization, ensure it passed
    rez_manager._mock_run.assert_called_once_with(
        ["rez", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_validate_rez_installation_failure_subprocess_error():
    """Test validation failure when subprocess fails."""
    with mock.patch("src.rez_manager.get_logger"):
        with mock.patch("src.rez_manager.platform.system", return_value="Windows"):
            with mock.patch("src.rez_manager.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.SubprocessError("Command failed")

                with pytest.raises(RezError) as excinfo:
                    RezManager()

                assert "Rez is not installed or not in PATH" in str(excinfo.value)


def test_validate_rez_installation_failure_file_not_found():
    """Test validation failure when Rez is not found."""
    with mock.patch("src.rez_manager.get_logger"):
        with mock.patch("src.rez_manager.platform.system", return_value="Windows"):
            with mock.patch("src.rez_manager.subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError(
                    "No such file or directory: 'rez'"
                )

                with pytest.raises(RezError) as excinfo:
                    RezManager()

                assert "Rez is not installed or not in PATH" in str(excinfo.value)


def test_create_alias_success(rez_manager):
    """Test successful creation of Rez alias."""
    # Setup
    software_name = "maya"
    software_version = "2023"
    packages = ["usd-23.11"]

    # Reset mock to clear the initialization call
    rez_manager._mock_run.reset_mock()

    # Test
    alias_name = rez_manager.create_alias(software_name, software_version, packages)

    # Assertions
    assert alias_name == software_name
    rez_manager._mock_run.assert_called_once()
    args, kwargs = rez_manager._mock_run.call_args
    assert args[0][0:2] == ["rez-bind", "--alias"]


def test_create_alias_with_custom_name(rez_manager):
    """Test creating Rez alias with custom name."""
    # Setup
    software_name = "maya"
    software_version = "2023"
    packages = ["usd-23.11"]
    custom_alias = "maya2023"

    # Reset mock
    rez_manager._mock_run.reset_mock()

    # Test
    alias_name = rez_manager.create_alias(
        software_name, software_version, packages, alias_name=custom_alias
    )

    # Assertions
    assert alias_name == custom_alias
    rez_manager._mock_run.assert_called_once()


def test_create_alias_failure(rez_manager):
    """Test failure when creating Rez alias."""
    # Setup
    rez_manager._mock_run.side_effect = subprocess.SubprocessError("Command failed")

    # Test
    with pytest.raises(RezError) as excinfo:
        rez_manager.create_alias("maya", "2023", [])

    assert "Failed to create Rez alias" in str(excinfo.value)


@mock.patch("platform.system", return_value="Windows")
def test_generate_rez_command_windows(mock_platform, rez_manager):
    """Test generating Rez command for Windows."""
    # Test
    command = rez_manager._generate_rez_command("maya", "2023", ["usd-23.11"])

    # Verify Windows-specific command structure
    assert "rez env" in command
    assert "maya-2023" in command
    assert "usd-23.11" in command
    # Should include cmd.exe on Windows
    assert "cmd" in command


@mock.patch("platform.system", return_value="Linux")
def test_generate_rez_command_linux(mock_platform, rez_manager):
    """Test generating Rez command for Linux."""
    # Test
    command = rez_manager._generate_rez_command("maya", "2023", ["usd-23.11"])

    # Verify Linux-specific command structure
    assert "rez env" in command
    assert "maya-2023" in command
    assert "usd-23.11" in command
    # Should use bash on Linux
    assert "bash" in command


def test_launch_software_success(rez_manager):
    """Test successful software launch."""
    # Setup mock
    mock_process = mock.MagicMock()
    with mock.patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        # Test
        process = rez_manager.launch_software("maya", ["--batch"])

        # Assertions
        assert process == mock_process
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert "maya" in args[0]


def test_launch_software_failure(rez_manager):
    """Test failure when launching software."""
    # Setup mock
    with mock.patch(
        "subprocess.Popen", side_effect=subprocess.SubprocessError("Launch failed")
    ) as mock_popen:
        # Test
        with pytest.raises(RezError) as excinfo:
            rez_manager.launch_software("maya", ["--batch"])

        # Assertions
        assert "Failed to launch maya" in str(excinfo.value)
