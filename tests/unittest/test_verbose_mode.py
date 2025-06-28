"""
Unit tests for verbose mode functionality.
"""

from unittest import mock
from unittest.mock import patch

import pytest

from src.environment_manager import EnvironmentManager
from src.rez_manager import RezManager


@pytest.fixture
@patch("src.rez_manager.subprocess.run")
@patch("src.rez_manager.platform.system", return_value="Windows")
@patch("src.rez_manager.get_logger")
def rez_manager(mock_logger, mock_platform, mock_run):
    """Fixture to create a RezManager instance with mocked dependencies."""
    # Mock successful rez validation
    mock_run.return_value = mock.MagicMock(returncode=0)
    manager = RezManager(verbose=True)
    # Make mock_run available to tests
    manager._mock_run = mock_run
    yield manager


@patch("src.rez_manager.subprocess.run")
@patch("src.rez_manager.platform.system", return_value="Windows")
@patch("src.rez_manager.get_logger")
def test_rez_manager_verbose_flag(mock_logger, mock_platform, mock_run):
    """Test that the verbose flag is properly set in RezManager."""
    # Mock successful rez validation
    mock_run.return_value = mock.MagicMock(returncode=0)

    # Create manager with verbose=False
    manager_non_verbose = RezManager(verbose=False)
    assert manager_non_verbose.verbose is False

    # Create manager with verbose=True
    manager_verbose = RezManager(verbose=True)
    assert manager_verbose.verbose is True


@patch("src.rez_manager.ProcessExecutor.execute")
@patch("src.rez_manager.subprocess.run")
@patch("src.rez_manager.platform.system", return_value="Windows")
@patch("src.rez_manager.get_logger")
def test_rez_manager_execute_with_verbose(mock_logger, mock_platform, mock_run, mock_execute):
    """Test that the verbose flag adds -v to rez commands."""
    # Mock successful rez validation
    mock_run.return_value = mock.MagicMock(returncode=0)
    mock_execute.return_value = (0, "Test output", "")

    # Create manager with verbose=True
    manager = RezManager(verbose=True)

    # Execute with rez
    manager.execute_with_rez("maya", "2023", [], "maya.exe")

    # Check that -v flag was included in the command
    args, _ = mock_execute.call_args
    command = args[0]
    assert "-v" in command


@patch("src.environment_manager.os.system")
@patch("src.environment_manager.platform.system", return_value="Windows")
@patch("src.environment_manager.get_logger")
def test_environment_manager_interactive_shell_verbose_windows(mock_logger, mock_platform, mock_system):
    """Test that verbose mode is correctly passed to PowerShell."""
    env_manager = EnvironmentManager()

    # Call with verbose=True
    env_manager.source_interactive_shell("script.ps1", verbose=True)

    # Check that VerbosePreference is set
    args, _ = mock_system.call_args
    cmd = args[0]
    assert "$VerbosePreference = 'Continue'" in cmd


@patch("src.environment_manager.os.system")
@patch("src.environment_manager.platform.system", return_value="Linux")
@patch("src.environment_manager.get_logger")
def test_environment_manager_interactive_shell_verbose_bash(mock_logger, mock_platform, mock_system):
    """Test that verbose mode is correctly passed to Bash."""
    env_manager = EnvironmentManager()

    # Call with verbose=True
    env_manager.source_interactive_shell("script.sh", verbose=True)

    # Check that VERBOSE=1 is set
    args, _ = mock_system.call_args
    cmd = args[0]
    assert "VERBOSE=1" in cmd


@pytest.fixture
@patch("src.production_environment.RezManager")
@patch("src.production_environment.EnvironmentManager")
@patch("src.production_environment.ProductionEnvironment._parse_pipeline_config")
@patch("src.production_environment.ProductionEnvironment._parse_software_config")
@patch("src.production_environment.ProductionEnvironment._load_config_paths", return_value={"software": [], "pipeline": []})
@patch("src.production_environment.get_logger")
def mock_production_environment(mock_logger, mock_load_config, mock_parse_software, mock_parse_pipeline, mock_env_manager, mock_rez_manager):
    """Create a mock production environment."""
    yield


@patch("src.production_environment.RezManager")
@patch("src.production_environment.EnvironmentManager")
@patch("src.production_environment.ProductionEnvironment._parse_pipeline_config")
@patch("src.production_environment.ProductionEnvironment._parse_software_config")
@patch("src.production_environment.ProductionEnvironment._load_config_paths", return_value={"software": [], "pipeline": []})
@patch("src.production_environment.get_logger")
def test_production_environment_passes_verbose_flag(mock_logger, mock_load_config, mock_parse_software, mock_parse_pipeline, mock_env_manager, mock_rez_manager):
    """Test that the ProductionEnvironment correctly passes the verbose flag."""
    # Import ProductionEnvironment after mocking RezManager
    from src.production_environment import ProductionEnvironment

    # Create instance with verbose=True
    prod_env = ProductionEnvironment("test_prod", verbose=True)

    # Verify the instance was created successfully
    assert prod_env.prod_name == "test_prod"

    # Verify that RezManager was created with verbose=True
    mock_rez_manager.assert_called_once_with(verbose=True)
