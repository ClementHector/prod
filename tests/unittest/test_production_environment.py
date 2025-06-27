"""
Unit tests for the ProductionEnvironment class.
"""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

from src.production_environment import ProductionEnvironment


def test_load_config_paths_unix_separator():
    """
    Test loading config paths with Unix separator.
    """
    # Mock file content with Unix separator
    mock_config_content = """
[environment]
SOFTWARE_CONFIG=/path/to/studio/software.inisep/path/to/prod/{PROD_NAME}/config/software.ini
PIPELINE_CONFIG=/path/to/studio/pipeline.inisep/path/to/prod/{PROD_NAME}/config/pipeline.ini
"""
    mock_config_content = mock_config_content.replace("sep", os.pathsep)
    print(mock_config_content)

    # Use mock_open to simulate file reading
    with patch("builtins.open", mock_open(read_data=mock_config_content)):
        with patch(
            "src.production_environment.ProductionEnvironment._get_settings_path",
            return_value=Path("mock_settings_path"),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                # Mock the software config parsing to avoid ConfigError
                with patch(
                    "src.production_environment.ProductionEnvironment._parse_software_config",
                    return_value=None
                ):
                    with patch(
                        "src.production_environment.ProductionEnvironment._parse_pipeline_config",
                        return_value=None
                    ):
                        prod_env = ProductionEnvironment("test_prod")

                        # Access the private method directly for testing
                        config_paths = prod_env.config_paths

                        # Check that the paths were correctly split
                        assert len(config_paths["software"]) == 2
                        assert config_paths["software"][0] == "/path/to/studio/software.ini"

                assert config_paths["software"][1] == "/path/to/prod/test_prod/config/software.ini"
                assert len(config_paths["pipeline"]) == 2
                assert config_paths["pipeline"][0] == "/path/to/studio/pipeline.ini"
                assert config_paths["pipeline"][1] == "/path/to/prod/test_prod/config/pipeline.ini"


def test_load_config_paths_windows_separator():
    """
    Test loading config paths with Windows separator.
    """
    # Mock file content with Windows separator
    mock_config_content = """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini;C:\\path\\to\\prod\\{PROD_NAME}\\config\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\studio\\pipeline.ini;C:\\path\\to\\prod\\{PROD_NAME}\\config\\pipeline.ini
"""
    # Use mock_open to simulate file reading
    with patch("builtins.open", mock_open(read_data=mock_config_content)):
        with patch(
            "src.production_environment.ProductionEnvironment._get_settings_path",
            return_value=Path("mock_settings_path"),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                # Mock the software config parsing to avoid ConfigError
                with patch(
                    "src.production_environment.ProductionEnvironment._parse_software_config",
                    return_value=None
                ):
                    with patch(
                        "src.production_environment.ProductionEnvironment._parse_pipeline_config",
                        return_value=None
                    ):
                        prod_env = ProductionEnvironment("test_prod")

                        # Access the private method directly for testing
                        config_paths = prod_env.config_paths

                        # Check that the paths were correctly split
                        assert len(config_paths["software"]) == 2
                        assert config_paths["software"][0] == "C:\\path\\to\\studio\\software.ini"
                        assert config_paths["software"][1] == "C:\\path\\to\\prod\\test_prod\\config\\software.ini"

                        assert len(config_paths["pipeline"]) == 2
                        assert config_paths["pipeline"][0] == "C:\\path\\to\\studio\\pipeline.ini"
                        assert config_paths["pipeline"][1] == "C:\\path\\to\\prod\\test_prod\\config\\pipeline.ini"


def test_load_config_paths_no_separator():
    """
    Test loading config paths with no separator.
    """
    # Mock file content with no separator
    mock_config_content = """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\pipeline.ini
"""
    # Use mock_open to simulate file reading
    with patch("builtins.open", mock_open(read_data=mock_config_content)):
        with patch(
            "src.production_environment.ProductionEnvironment._get_settings_path",
            return_value=Path("mock_settings_path"),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                # Mock the software config parsing to avoid ConfigError
                with patch(
                    "src.production_environment.ProductionEnvironment._parse_software_config",
                    return_value=None
                ):
                    with patch(
                        "src.production_environment.ProductionEnvironment._parse_pipeline_config",
                        return_value=None
                    ):
                        prod_env = ProductionEnvironment("test_prod")

                        # Access the private method directly for testing
                        config_paths = prod_env.config_paths

                        # Check that the single path was handled correctly
                        assert len(config_paths["software"]) == 1
                        assert config_paths["software"][0] == "C:\\path\\to\\software.ini"

                        assert len(config_paths["pipeline"]) == 1
                        assert config_paths["pipeline"][0] == "C:\\path\\to\\pipeline.ini"
