"""
Tests unitaires pour la classe EnvironmentManager.
"""

import os
import platform
import tempfile
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


def test_generate_powershell_script(env_manager):
    """
    Test de génération d'un script PowerShell.
    """
    # Configuration de l'environnement de test
    with patch("platform.system", return_value="Windows"):
        # Définir des variables d'environnement
        env_manager.set_environment_variables(
            {"PROD": "dlt", "PROD_ROOT": "/s/prods/dlt", "PROD_TYPE": "vfx"}
        )

        # Générer le script
        script_path = env_manager.generate_shell_script("dlt")

        # Vérifier que le fichier existe
        assert os.path.exists(script_path)
        assert script_path.endswith(".ps1")

        # Vérifier le contenu du script
        with open(script_path, "r") as f:
            content = f.read()
            assert "$env:PROD = 'dlt'" in content
            assert "$env:PROD_ROOT = '/s/prods/dlt'" in content
            assert "$env:PROD_TYPE = 'vfx'" in content
            assert "Set-ProdEnvironment" in content


def test_generate_bash_script(env_manager):
    """
    Test de génération d'un script Bash.
    """
    # Configuration de l'environnement de test
    with patch("platform.system", return_value="Linux"):
        # Définir des variables d'environnement
        env_manager.set_environment_variables(
            {"PROD": "dlt", "PROD_ROOT": "/s/prods/dlt", "PROD_TYPE": "vfx"}
        )

        # Générer le script
        script_path = env_manager.generate_shell_script("dlt")

        # Vérifier que le fichier existe
        assert os.path.exists(script_path)
        assert script_path.endswith(".sh")

        # Vérifier le contenu du script
        with open(script_path, "r") as f:
            content = f.read()
            assert "export PROD='dlt'" in content
            assert "export PROD_ROOT='/s/prods/dlt'" in content
            assert "export PROD_TYPE='vfx'" in content
            assert "#!/bin/bash" in content


def test_apply_environment_to_parent_shell(env_manager):
    """
    Test de l'application des variables d'environnement au shell parent.
    Ceci est principalement un test de la fonction plutôt que de son effet,
    car il n'est pas réellement possible de modifier l'environnement du shell parent.
    """
    # Créer un fichier temporaire pour simuler un script shell
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        suffix=".ps1" if platform.system() == "Windows" else ".sh",
    ) as tmp:
        tmp.write("# Test script\n")
        tmp_path = tmp.name

    try:
        # Mock subprocess.run pour éviter l'exécution réelle
        with patch("subprocess.run") as mock_run:
            # Appeler la méthode
            env_manager.apply_environment_to_parent_shell(tmp_path)

            # Vérifier que subprocess.run a été appelé
            mock_run.assert_called_once()
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
