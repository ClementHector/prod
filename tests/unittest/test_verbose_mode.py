"""
Unit tests for verbose mode functionality.
"""

from unittest import mock

import pytest

from src.environment_manager import EnvironmentManager
from src.rez_manager import RezManager


@pytest.fixture
def rez_manager():
    """Fixture to create a RezManager instance with mocked dependencies."""
    with mock.patch("src.rez_manager.get_logger"):
        with mock.patch("src.rez_manager.platform.system", return_value="Windows"):
            with mock.patch("src.rez_manager.subprocess.run") as mock_run:
                # Mock successful rez validation
                mock_run.return_value = mock.MagicMock(returncode=0)
                manager = RezManager(verbose=True)
                # Make mock_run available to tests
                manager._mock_run = mock_run
                yield manager


def test_rez_manager_verbose_flag():
    """Test that the verbose flag is properly set in RezManager."""
    with mock.patch("src.rez_manager.get_logger"):
        with mock.patch("src.rez_manager.platform.system", return_value="Windows"):
            with mock.patch("src.rez_manager.subprocess.run") as mock_run:
                # Mock successful rez validation
                mock_run.return_value = mock.MagicMock(returncode=0)

                # Create manager with verbose=False
                manager_non_verbose = RezManager(verbose=False)
                assert manager_non_verbose.verbose is False

                # Create manager with verbose=True
                manager_verbose = RezManager(verbose=True)
                assert manager_verbose.verbose is True


def test_rez_manager_execute_with_verbose():
    """Test that the verbose flag adds -v to rez commands."""
    with mock.patch("src.rez_manager.get_logger"):
        with mock.patch("src.rez_manager.platform.system", return_value="Windows"):
            with mock.patch("src.rez_manager.subprocess.run") as mock_run:
                # Mock successful rez validation
                mock_run.return_value = mock.MagicMock(returncode=0)

                # Mock the ProcessExecutor.execute method to capture the command
                with mock.patch("src.rez_manager.ProcessExecutor.execute") as mock_execute:
                    mock_execute.return_value = (0, "Test output", "")

                    # Create manager with verbose=True
                    manager = RezManager(verbose=True)

                    # Execute with rez
                    manager.execute_with_rez("maya", "2023", [], "maya.exe")

                    # Check that -v flag was included in the command
                    args, _ = mock_execute.call_args
                    command = args[0]
                    assert "-v" in command


def test_environment_manager_interactive_shell_verbose_windows():
    """Test that verbose mode is correctly passed to PowerShell."""
    with mock.patch("src.environment_manager.get_logger"):
        with mock.patch(
            "src.environment_manager.platform.system", return_value="Windows"
        ):
            with mock.patch("src.environment_manager.os.system") as mock_system:
                env_manager = EnvironmentManager()

                # Call with verbose=True
                env_manager.source_interactive_shell("script.ps1", verbose=True)

                # Check that VerbosePreference is set
                args, _ = mock_system.call_args
                cmd = args[0]
                assert "$VerbosePreference = 'Continue'" in cmd


def test_environment_manager_interactive_shell_verbose_bash():
    """Test that verbose mode is correctly passed to Bash."""
    with mock.patch("src.environment_manager.get_logger"):
        with mock.patch(
            "src.environment_manager.platform.system", return_value="Linux"
        ):
            with mock.patch("src.environment_manager.os.system") as mock_system:
                env_manager = EnvironmentManager()

                # Call with verbose=True
                env_manager.source_interactive_shell("script.sh", verbose=True)

                # Check that VERBOSE=1 is set
                args, _ = mock_system.call_args
                cmd = args[0]
                assert "VERBOSE=1" in cmd


@pytest.fixture
def mock_production_environment():
    """Create a mock production environment."""
    with mock.patch("src.production_environment.get_logger"):
        with mock.patch(
            "src.production_environment.ProductionEnvironment._load_config_paths",
            return_value={"software": [], "pipeline": []},
        ):
            with mock.patch(
                "src.production_environment.ProductionEnvironment._parse_software_config"
            ):
                with mock.patch(
                    "src.production_environment.ProductionEnvironment._parse_pipeline_config"
                ):
                    with mock.patch("src.production_environment.EnvironmentManager"):
                        with mock.patch("src.production_environment.RezManager"):
                            yield


def test_production_environment_passes_verbose_flag():
    """Test that the ProductionEnvironment correctly passes the verbose flag."""
    with mock.patch("src.production_environment.get_logger"):
        with mock.patch(
            "src.production_environment.ProductionEnvironment._load_config_paths",
            return_value={"software": [], "pipeline": []},
        ):
            with mock.patch(
                "src.production_environment.ProductionEnvironment._parse_software_config"
            ):
                with mock.patch(
                    "src.production_environment.ProductionEnvironment._parse_pipeline_config"
                ):
                    with mock.patch("src.production_environment.EnvironmentManager"):
                        with mock.patch(
                            "src.production_environment.RezManager"
                        ) as mock_rez_manager:
                            # Import ProductionEnvironment after mocking RezManager
                            from src.production_environment import ProductionEnvironment

                            # Create instance with verbose=True
                            prod_env = ProductionEnvironment("test_prod", verbose=True)

                            # Verify the instance was created successfully
                            assert prod_env.prod_name == "test_prod"

                            # Verify that RezManager was created with verbose=True
                            mock_rez_manager.assert_called_once_with(verbose=True)
