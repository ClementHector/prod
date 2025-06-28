"""
Unit tests for the RezManager class.
"""

import subprocess
from unittest import mock

import pytest

from src.exceptions import RezError
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
        check=False,
        text=True,
    )


@mock.patch("src.rez_manager.get_logger")
@mock.patch("src.rez_manager.platform.system", return_value="Windows")
@mock.patch("src.rez_manager.subprocess.run")
def test_validate_rez_installation_failure_subprocess_error(mock_run, mock_system, mock_logger):
    """Test validation failure when subprocess fails."""
    # Instead of raising exception directly, return an error result
    mock_result = mock.MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Command failed"
    mock_run.return_value = mock_result

    with pytest.raises(RezError) as excinfo:
        RezManager()

    assert "Rez installation check failed" in str(excinfo.value)


@mock.patch("src.rez_manager.get_logger")
@mock.patch("src.rez_manager.platform.system", return_value="Windows")
@mock.patch("src.rez_manager.subprocess.run")
def test_validate_rez_installation_failure_file_not_found(mock_run, mock_system, mock_logger):
    """Test validation failure when Rez is not found."""
    mock_run.side_effect = FileNotFoundError(
        "No such file or directory: 'rez'"
    )

    with pytest.raises(RezError) as excinfo:
        RezManager()

    assert "Rez is not installed or not in PATH" in str(excinfo.value)
