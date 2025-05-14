"""
Tests unitaires pour la fonction d'activation de l'environnement.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.logger import Logger
from src.production_environment import ProductionEnvironment


@pytest.fixture
def mock_environment():
    """
    Fixture pour créer un environnement de production mock.
    """
    # Patch pour les méthodes privées
    mock_load = patch("src.production_environment.ProductionEnvironment._load_config_paths")
    mock_software = patch("src.production_environment.ProductionEnvironment._parse_software_config")
    mock_pipeline = patch("src.production_environment.ProductionEnvironment._parse_pipeline_config")
    # Patch pour EnvironmentManager
    mock_env_manager = patch("src.production_environment.EnvironmentManager")
    
    # Démarre les patches
    mock_load_started = mock_load.start()
    mock_software_started = mock_software.start()
    mock_pipeline_started = mock_pipeline.start()
    mock_env_manager_started = mock_env_manager.start()
    
    # Configure les retours de mock
    mock_load_started.return_value = {"software": [], "pipeline": []}
    
    # Crée l'environnement de production avec les mocks
    logger = MagicMock(spec=Logger)
    prod_env = ProductionEnvironment("test_prod", logger)
    
    # Prépare les données de test pour la liste des logiciels
    mock_software_list = [
        {"name": "maya", "version": "2024"},
        {"name": "nuke", "version": "14.0"},
        {"name": "houdini", "version": "20.0"}
    ]
    
    # Configure le mock pour get_software_list
    prod_env.get_software_list = MagicMock(return_value=mock_software_list)
    
    yield prod_env
    
    # Nettoyage des patches
    mock_load.stop()
    mock_software.stop()
    mock_pipeline.stop()
    mock_env_manager.stop()


def test_activate_passes_software_list_to_generate_script(mock_environment):
    """
    Test que la méthode activate() passe correctement la liste des logiciels
    à generate_interactive_shell_script.
    """
    # Configure le mock pour renvoyer un chemin de script
    mock_environment.env_manager.generate_interactive_shell_script.return_value = "/path/to/script.sh"
    
    # Configure source_interactive_shell pour ne rien faire
    mock_environment.env_manager.source_interactive_shell = MagicMock()
    
    # Active l'environnement
    mock_environment.activate()
    
    # Vérifie que generate_interactive_shell_script a été appelée avec les bons arguments
    mock_generate = mock_environment.env_manager.generate_interactive_shell_script
    assert mock_generate.called, "generate_interactive_shell_script n'a pas été appelée"
    
    call_args = mock_generate.call_args
    
    # Vérifie le premier argument (nom de la production)
    assert call_args[0][0] == "test_prod"
    
    # Vérifie le deuxième argument (liste des logiciels)
    assert len(call_args[0]) > 1, "La liste des logiciels n'a pas été passée"
    software_list = call_args[0][1]
    assert isinstance(software_list, list)
    assert "maya:2024" in software_list
    assert "nuke:14.0" in software_list
    assert "houdini:20.0" in software_list
    
    # Vérifie que source_interactive_shell a été appelée
    mock_environment.env_manager.source_interactive_shell.assert_called_once()
