"""
Unit tests for the environment activation function.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.production_environment import ProductionEnvironment


@pytest.fixture
def mock_software_list():
    """
    Fixture for mock software list data.
    """
    return [
        {"name": "maya", "version": "2024"},
        {"name": "nuke", "version": "14.0"},
        {"name": "houdini", "version": "20.0"},
    ]


@patch("src.production_environment.EnvironmentManager")
@patch("src.production_environment.ProductionEnvironment._parse_pipeline_config", return_value=None)
@patch("src.production_environment.ProductionEnvironment._parse_software_config", return_value=None)
@patch("src.production_environment.ProductionEnvironment._load_config_paths", return_value={"software": [], "pipeline": []})
def test_activate_passes_software_list_to_generate_script(
    mock_load_config, mock_parse_software, mock_parse_pipeline, mock_env_manager, mock_software_list
):
    """
    Test that activate() method correctly passes software list to
    generate_interactive_shell_script.
    """
    # Crée l'environnement de production avec les mocks
    prod_env = ProductionEnvironment("test_prod")

    # Mock the pipeline_config after instantiation
    mock_pipeline_config = MagicMock()
    mock_pipeline_config.get_environment_variables.return_value = {}
    prod_env.pipeline_config = mock_pipeline_config

    # Configure mock for get_software_list
    prod_env.get_software_list = MagicMock(return_value=mock_software_list)

    # Create a MagicMock for the env_manager
    prod_env.env_manager = MagicMock()

    # Configure mock to return a script path
    prod_env.env_manager.generate_interactive_shell_script.return_value = "/path/to/script.sh"

    # Activate the environment
    prod_env.activate()

    # Verify that generate_interactive_shell_script was called with the correct arguments
    mock_generate = prod_env.env_manager.generate_interactive_shell_script
    assert mock_generate.called, "generate_interactive_shell_script was not called"

    call_args = mock_generate.call_args

    # Verify the first argument (production name)
    assert call_args[0][0] == "test_prod"

    # Verify the second argument (software list)
    assert len(call_args[0]) > 1, "Software list was not passed"
    software_list = call_args[0][1]
    assert isinstance(software_list, list)
    assert "maya:2024" in software_list
    assert "nuke:14.0" in software_list
    assert "houdini:20.0" in software_list

    # Verify that source_interactive_shell was called
    prod_env.env_manager.source_interactive_shell.assert_called_once()
