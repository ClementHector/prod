"""
Unit tests for the environment activation function.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.production_environment import ProductionEnvironment


@pytest.fixture
def mock_environment():
    """
    Fixture to create a mock production environment.
    """
    # Patch for private methods
    mock_load = patch(
        "src.production_environment.ProductionEnvironment._load_config_paths"
    )
    mock_software = patch(
        "src.production_environment.ProductionEnvironment._parse_software_config"
    )
    mock_pipeline = patch(
        "src.production_environment.ProductionEnvironment._parse_pipeline_config"
    )
    # Patch for EnvironmentManager
    mock_env_manager = patch("src.production_environment.EnvironmentManager")
    # Start the patches
    mock_load_started = mock_load.start()

    # Configure mock return values
    mock_load_started.return_value = {"software": [], "pipeline": []}

    # Crée l'environnement de production avec les mocks
    with patch(
        "src.production_environment.ProductionEnvironment._parse_software_config",
        return_value=None
    ):
        with patch(
            "src.production_environment.ProductionEnvironment._parse_pipeline_config",
            return_value=None
        ):
            prod_env = ProductionEnvironment("test_prod")

            # Mock the pipeline_config after instantiation
            mock_pipeline_config = MagicMock()
            mock_pipeline_config.get_environment_variables.return_value = {}
            prod_env.pipeline_config = mock_pipeline_config

    # Prépare les données de test pour la liste des logiciels
    mock_software_list = [
        {"name": "maya", "version": "2024"},
        {"name": "nuke", "version": "14.0"},
        {"name": "houdini", "version": "20.0"},
    ]
    # Configure mock for get_software_list
    prod_env.get_software_list = MagicMock(return_value=mock_software_list)

    yield prod_env

    # Cleanup patches
    mock_load.stop()
    mock_software.stop()
    mock_pipeline.stop()
    mock_env_manager.stop()


def test_activate_passes_software_list_to_generate_script(mock_environment):
    """
    Test that activate() method correctly passes software list to
    generate_interactive_shell_script.
    """  # Create a MagicMock for the env_manager
    mock_environment.env_manager = MagicMock()

    # Configure mock to return a script path
    mock_environment.env_manager.generate_interactive_shell_script.return_value = (
        "/path/to/script.sh"
    )

    # Activate the environment
    mock_environment.activate()
    # Verify that generate_interactive_shell_script was called with the correct arguments
    mock_generate = mock_environment.env_manager.generate_interactive_shell_script
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
    mock_environment.env_manager.source_interactive_shell.assert_called_once()
