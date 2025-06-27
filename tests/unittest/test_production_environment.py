"""
Unit tests for the ProductionEnvironment class.
"""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

from src.production_environment import ProductionEnvironment


@patch("pathlib.Path.exists", return_value=True)
@patch("src.production_environment.ProductionEnvironment._get_settings_path", return_value=Path("mock_settings_path"))
@patch("builtins.open")
def test_load_config_paths_unix_separator(mock_file, mock_get_settings_path, mock_path_exists):
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

    # Configure mock_open with the generated content
    mock_file.side_effect = mock_open(read_data=mock_config_content)

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


@patch("pathlib.Path.exists", return_value=True)
@patch("src.production_environment.ProductionEnvironment._get_settings_path", return_value=Path("mock_settings_path"))
@patch("builtins.open", new_callable=lambda: mock_open(read_data="""
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini;C:\\path\\to\\prod\\{PROD_NAME}\\config\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\studio\\pipeline.ini;C:\\path\\to\\prod\\{PROD_NAME}\\config\\pipeline.ini
"""))
def test_load_config_paths_windows_separator(mock_file, mock_get_settings_path, mock_path_exists):
    """
    Test loading config paths with Windows separator.
    """

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


@patch("pathlib.Path.exists", return_value=True)
@patch("src.production_environment.ProductionEnvironment._get_settings_path", return_value=Path("mock_settings_path"))
@patch("builtins.open", new_callable=lambda: mock_open(read_data="""
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\pipeline.ini
"""))
def test_load_config_paths_no_separator(mock_file, mock_get_settings_path, mock_path_exists):
    """
    Test loading config paths with no separator.
    """
    prod_env = ProductionEnvironment("test_prod")

    # Access the private method directly for testing
    config_paths = prod_env.config_paths

    # Check that the single path was handled correctly
    assert len(config_paths["software"]) == 1
    assert config_paths["software"][0] == "C:\\path\\to\\software.ini"

    assert len(config_paths["pipeline"]) == 1
    assert config_paths["pipeline"][0] == "C:\\path\\to\\pipeline.ini"
