"""
Unit tests for the ProductionEnvironment class.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.logger import Logger
from src.production_environment import ProductionEnvironment


@pytest.fixture
def mock_config_file():
    """
    Fixture to create a temporary config file.

    Returns:
        Tuple of (temp_dir, config_path)
    """
    temp_dir = tempfile.TemporaryDirectory()
    settings_path = os.path.join(temp_dir.name, "prod-settings.ini")

    yield temp_dir, settings_path

    temp_dir.cleanup()


@pytest.fixture
def logger():
    """
    Fixture to create a mock logger.

    Returns:
        Mock logger
    """
    return MagicMock(spec=Logger)


def test_load_config_paths_unix_separator(mock_config_file, logger):
    """
    Test loading config paths with Unix separator.
    """
    temp_dir, settings_path = mock_config_file

    # Create settings file with Unix separator
    with open(settings_path, "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=/path/to/studio/software.ini:/path/to/prod/{PROD_NAME}/config/software.ini
PIPELINE_CONFIG=/path/to/studio/pipeline.ini:/path/to/prod/{PROD_NAME}/config/pipeline.ini
"""
        )

    # Mock config loading to use our test file
    with patch("os.path.join", return_value=settings_path):
        with patch("os.path.exists", return_value=True):
            prod_env = ProductionEnvironment("test_prod")

            # Access the private method directly for testing
            config_paths = prod_env.config_paths

            # Check that the paths were correctly split
            assert len(config_paths["software"]) == 2
            assert config_paths["software"][0] == "/path/to/studio/software.ini"
            assert (
                config_paths["software"][1]
                == "/path/to/prod/test_prod/config/software.ini"
            )

            assert len(config_paths["pipeline"]) == 2
            assert config_paths["pipeline"][0] == "/path/to/studio/pipeline.ini"
            assert (
                config_paths["pipeline"][1]
                == "/path/to/prod/test_prod/config/pipeline.ini"
            )


def test_load_config_paths_windows_separator(mock_config_file, logger):
    """
    Test loading config paths with Windows separator.
    """
    temp_dir, settings_path = mock_config_file

    # Create settings file with Windows separator
    with open(settings_path, "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini;C:\\path\\to\\prod\\{PROD_NAME}\\config\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\studio\\pipeline.ini;C:\\path\\to\\prod\\{PROD_NAME}\\config\\pipeline.ini
"""
        )

    # Mock config loading to use our test file
    with patch("os.path.join", return_value=settings_path):
        with patch("os.path.exists", return_value=True):
            prod_env = ProductionEnvironment("test_prod")

            # Access the private method directly for testing
            config_paths = prod_env.config_paths

            # Check that the paths were correctly split
            assert len(config_paths["software"]) == 2
            assert config_paths["software"][0] == "C:\\path\\to\\studio\\software.ini"
            assert (
                config_paths["software"][1]
                == "C:\\path\\to\\prod\\test_prod\\config\\software.ini"
            )

            assert len(config_paths["pipeline"]) == 2
            assert config_paths["pipeline"][0] == "C:\\path\\to\\studio\\pipeline.ini"
            assert (
                config_paths["pipeline"][1]
                == "C:\\path\\to\\prod\\test_prod\\config\\pipeline.ini"
            )


def test_load_config_paths_mixed_separator(mock_config_file, logger):
    """
    Test loading config paths with mixed separators (Windows paths but Unix separator).
    """
    temp_dir, settings_path = mock_config_file

    # Create settings file with mixed separator format
    with open(settings_path, "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini:C:\\path\\to\\prod\\{PROD_NAME}\\config\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\studio\\pipeline.ini:C:\\path\\to\\prod\\{PROD_NAME}\\config\\pipeline.ini
"""
        )

    # Mock config loading to use our test file
    with patch("os.path.join", return_value=settings_path):
        with patch("os.path.exists", return_value=True):
            prod_env = ProductionEnvironment("test_prod")

            # Access the private method directly for testing
            config_paths = prod_env.config_paths

            # Check that the paths were correctly split and drive letters preserved
            assert len(config_paths["software"]) == 2
            assert config_paths["software"][0] == "C:\\path\\to\\studio\\software.ini"
            assert (
                config_paths["software"][1]
                == "C:\\path\\to\\prod\\test_prod\\config\\software.ini"
            )

            assert len(config_paths["pipeline"]) == 2
            assert config_paths["pipeline"][0] == "C:\\path\\to\\studio\\pipeline.ini"
            assert (
                config_paths["pipeline"][1]
                == "C:\\path\\to\\prod\\test_prod\\config\\pipeline.ini"
            )


def test_load_config_paths_both_separators(mock_config_file, logger):
    """
    Test loading config paths with both Windows and Unix separators in the same path.
    """
    temp_dir, settings_path = mock_config_file

    # Create settings file with mixed separators
    with open(settings_path, "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini;/unix/path/software.ini:/another/unix/path/{PROD_NAME}/software.ini
PIPELINE_CONFIG=C:\\path\\to\\studio\\pipeline.ini;/unix/path/pipeline.ini:/another/unix/path/{PROD_NAME}/pipeline.ini
"""
        )

    # Mock config loading to use our test file
    with patch("os.path.join", return_value=settings_path):
        with patch("os.path.exists", return_value=True):
            prod_env = ProductionEnvironment("test_prod")

            # Access the private method directly for testing
            config_paths = prod_env.config_paths

            # Check that the paths were correctly split using both separators
            assert len(config_paths["software"]) == 3
            assert config_paths["software"][0] == "C:\\path\\to\\studio\\software.ini"
            assert config_paths["software"][1] == "/unix/path/software.ini"
            assert (
                config_paths["software"][2]
                == "/another/unix/path/test_prod/software.ini"
            )

            assert len(config_paths["pipeline"]) == 3
            assert config_paths["pipeline"][0] == "C:\\path\\to\\studio\\pipeline.ini"
            assert config_paths["pipeline"][1] == "/unix/path/pipeline.ini"
            assert (
                config_paths["pipeline"][2]
                == "/another/unix/path/test_prod/pipeline.ini"
            )


def test_load_config_paths_no_separator(mock_config_file, logger):
    """
    Test loading config paths with no separator.
    """
    temp_dir, settings_path = mock_config_file

    # Create settings file with no separator
    with open(settings_path, "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\pipeline.ini
"""
        )

    # Mock config loading to use our test file
    with patch("os.path.join", return_value=settings_path):
        with patch("os.path.exists", return_value=True):
            prod_env = ProductionEnvironment("test_prod")

            # Access the private method directly for testing
            config_paths = prod_env.config_paths

            # Check that the single path was handled correctly
            assert len(config_paths["software"]) == 1
            assert config_paths["software"][0] == "C:\\path\\to\\software.ini"

            assert len(config_paths["pipeline"]) == 1
            assert config_paths["pipeline"][0] == "C:\\path\\to\\pipeline.ini"
