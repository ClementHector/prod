"""
Unit tests for the RezManager class.
"""

import os
import platform
import subprocess
from unittest import mock

import pytest

from src.rez_manager import RezManager
from src.errors import RezError


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
