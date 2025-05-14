"""
Tests unitaires pour les fonctions interactives de EnvironmentManager.
"""

import os
import platform
from unittest.mock import MagicMock, patch

import pytest

from src.environment_manager import EnvironmentManager
from src.logger import Logger


@pytest.fixture
def env_manager():
    """
    Fixture pour créer un gestionnaire d'environnement.

    Returns:
        EnvironmentManager
    """
    logger = MagicMock(spec=Logger)
    return EnvironmentManager(logger)


def test_generate_interactive_shell_script_with_software_list(env_manager):
    """
    Test de génération d'un script interactif avec une liste de logiciels fournie directement.
    """
    # Configuration de l'environnement de test
    with patch("platform.system", return_value="Windows"):
        # Définir des variables d'environnement
        env_manager.set_environment_variables(
            {"PROD": "dlt", "PROD_ROOT": "/s/prods/dlt", "PROD_TYPE": "vfx"}
        )

        # Préparer une liste de logiciels
        software_list = ["maya:2024", "houdini:20.0", "nuke:14.0"]

        # Générer le script
        script_path = env_manager.generate_interactive_shell_script("dlt", software_list)

        # Vérifier que le fichier existe
        assert os.path.exists(script_path)
        assert script_path.endswith(".ps1")  # PowerShell sur Windows

        # Vérifier le contenu du script
        with open(script_path, "r") as f:
            content = f.read()
            assert "$env:PROD = 'dlt'" in content
            assert "function global:maya {" in content
            assert "function global:houdini {" in content
            assert "function global:nuke {" in content
            assert "rez env maya-2024 -- maya" in content
            assert "rez env houdini-20.0 -- houdini" in content
            assert "rez env nuke-14.0 -- nuke" in content
            assert "* maya (version 2024)" in content
            assert "* houdini (version 20.0)" in content
            assert "* nuke (version 14.0)" in content

    # Maintenant testons avec Linux
    with patch("platform.system", return_value="Linux"):
        # Générer le script
        script_path = env_manager.generate_interactive_shell_script("dlt", software_list)

        # Vérifier que le fichier existe
        assert os.path.exists(script_path)
        assert script_path.endswith(".sh")  # Bash sur Linux

        # Vérifier le contenu du script
        with open(script_path, "r") as f:
            content = f.read()
            assert "export PROD='dlt'" in content
            assert "function maya() {" in content
            assert "function houdini() {" in content
            assert "function nuke() {" in content
            assert "rez env maya-2024 -- maya" in content
            assert "rez env houdini-20.0 -- houdini" in content
            assert "rez env nuke-14.0 -- nuke" in content
            assert "* maya (version 2024)" in content
            assert "* houdini (version 20.0)" in content
            assert "* nuke (version 14.0)" in content
