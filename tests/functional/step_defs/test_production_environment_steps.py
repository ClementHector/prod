"""
Step definitions pour les tests fonctionnels de gestion des environnements de production.
"""

import os
import tempfile
from unittest import mock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from src.logger import Logger
from src.production_environment import ProductionEnvironment

# Importer tous les scénarios du fichier feature
scenarios("../features/production_environment.feature")


@pytest.fixture
def prod_env_context():
    """Fixture pour le contexte des tests d'environnement de production."""
    # Créer un répertoire temporaire
    temp_dir = tempfile.TemporaryDirectory()

    # Créer le logger
    logger = Logger()

    # Contexte pour les tests
    context = {
        "temp_dir": temp_dir,
        "logger": logger,
        "env_variables": {},
        "rez_aliases": [],
    }

    yield context

    # Cleanup
    temp_dir.cleanup()


@given(parsers.parse('a valid production name "{prod_name}"'))
def valid_production_name(prod_env_context, prod_name):
    """Définir un nom de production valide."""
    prod_env_context["prod_name"] = prod_name


@given("studio and production configuration files exist")
def config_files_exist(prod_env_context):
    """Créer les fichiers de configuration studio et production."""
    # Créer la structure de répertoires
    config_dir = os.path.join(prod_env_context["temp_dir"].name, "config")
    studio_dir = os.path.join(config_dir, "studio")
    prod_dir = os.path.join(
        config_dir, "prods", prod_env_context["prod_name"], "config"
    )

    os.makedirs(studio_dir, exist_ok=True)
    os.makedirs(prod_dir, exist_ok=True)

    # Créer les fichiers de configuration studio
    with open(os.path.join(studio_dir, "software.ini"), "w") as f:
        f.write(
            """
[maya]
version=2023.3.0
packages = ["mtoa-2.2", "golaem-4"]

[nuke]
version = 12.2
packages = ["ofxSuperResolution", "neatVideo"]

[houdini]
version = 19.0
packages = ["redshift-3.5.10"]
"""
        )

    with open(os.path.join(studio_dir, "pipeline.ini"), "w") as f:
        f.write(
            """
[common]
packages = ["vfxCore-2.5"]

[maya]
packages = ["vfxMayaTools-2.0"]

[nuke]
packages = ["vfxNukeTools-2.0"]

[houdini]
packages = ["vfxHoudiniTools-1.5"]

[environment]
STUDIO_ROOT=/s/studio
TOOLS_ROOT=/s/studio/tools
"""
        )

    # Créer les fichiers de configuration de la production
    with open(os.path.join(prod_dir, "software.ini"), "w") as f:
        f.write(
            """
[maya]
version=2023.3.2
packages = ["mtoa-2.3", "golaem-4"]

[nuke]
version = 12.3
packages = ["ofxSuperResolution", "neatVideo"]

[nuke-13]
version = 13.2
packages = ["ofxSuperResolution", "neatVideo"]

[houdini]
version = 19.5
packages = ["redshift-3.5.14"]
"""
        )

    with open(os.path.join(prod_dir, "pipeline.ini"), "w") as f:
        f.write(
            """
[common]
packages = ["vfxCore-2.5"]

[maya]
packages = ["vfxMayaTools-2.3"]

[nuke]
packages = ["vfxNukeTools-2.1"]

[houdini]
packages = ["vfxHoudiniTools-1.8"]

[environment]
PROD=dlt
PROD_ROOT=/s/prods/dlt
PROD_TYPE=vfx
DLT_ASSETS=/s/prods/dlt/assets
DLT_SHOTS=/s/prods/dlt/shots
"""
        )

    # Créer le fichier de paramètres prod
    temp_dir = prod_env_context["temp_dir"].name
    with open(os.path.join(config_dir, "prod-settings.ini"), "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=%s/config/studio/software.ini:
%s/config/prods/{PROD_NAME}/config/software.ini
PIPELINE_CONFIG=%s/config/studio/pipeline.ini:
%s/config/prods/{PROD_NAME}/config/pipeline.ini
"""
            % (temp_dir, temp_dir, temp_dir, temp_dir)
        )

    # Sauvegarder les chemins dans le contexte
    prod_env_context["config_dir"] = config_dir

    # Mock pour ProductionEnvironment._load_config_paths
    prod_env_context["mock_load_config_paths"] = mock.patch(
        "src.production_environment.ProductionEnvironment._load_config_paths",
        return_value={
            "software": [
                os.path.join(studio_dir, "software.ini"),
                os.path.join(prod_dir, "software.ini"),
            ],
            "pipeline": [
                os.path.join(studio_dir, "pipeline.ini"),
                os.path.join(prod_dir, "pipeline.ini"),
            ],
        },
    )

    # Mock pour EnvironmentManager.set_environment_variables
    prod_env_context["mock_set_env_vars"] = mock.patch(
        "src.environment_manager.EnvironmentManager.set_environment_variables",
        side_effect=lambda vars: prod_env_context["env_variables"].update(
            vars
        ),
    )

    # Mock pour RezManager.create_alias
    prod_env_context["mock_create_alias"] = mock.patch(
        "src.rez_manager.RezManager.create_alias",
        side_effect=lambda sw_name, sw_ver, pkgs, alias_name=None: prod_env_context[
            "rez_aliases"
        ].append(
            {
                "software": sw_name,
                "version": sw_ver,
                "packages": pkgs,
                "alias": alias_name or sw_name,
            }
        ),
    )

    # Mock pour RezManager._validate_rez_installation
    prod_env_context["mock_validate_rez"] = mock.patch(
        "src.rez_manager.RezManager._validate_rez_installation"
    )


@when("I activate the production environment")
def activate_production_env(prod_env_context):
    """Activer l'environnement de production."""
    with (
        prod_env_context["mock_load_config_paths"],
        prod_env_context["mock_set_env_vars"],
        prod_env_context["mock_create_alias"],
        prod_env_context["mock_validate_rez"],
    ):

        prod_env = ProductionEnvironment(
            prod_env_context["prod_name"], prod_env_context["logger"]
        )
        prod_env.activate()

        # Sauvegarder l'environnement dans le contexte
        prod_env_context["prod_env"] = prod_env


@then("environment variables should be set from the pipeline configuration")
def check_env_variables(prod_env_context):
    """
    Vérifier que les variables d'environnement sont définies
    à partir de la configuration.
    """
    assert "PROD_ROOT" in prod_env_context["env_variables"]
    assert "PROD_TYPE" in prod_env_context["env_variables"]
    assert "DLT_ASSETS" in prod_env_context["env_variables"]
    assert "DLT_SHOTS" in prod_env_context["env_variables"]

    assert prod_env_context["env_variables"]["PROD_ROOT"] == "/s/prods/dlt"
    assert prod_env_context["env_variables"]["PROD_TYPE"] == "vfx"


@then("the PROD environment variable should be set to the production name")
def check_prod_env_var(prod_env_context):
    """
    Vérifier que la variable d'environnement PROD est définie
    avec le nom de production.
    """
    assert "PROD" in prod_env_context["env_variables"]
    assert prod_env_context["env_variables"]["PROD"] == prod_env_context["prod_name"]


@then("Rez aliases should be created for all configured software")
def check_rez_aliases_created(prod_env_context):
    """Vérifier que des alias Rez sont créés pour tous les logiciels configurés."""
    software_names = {
        alias["software"] for alias in prod_env_context["rez_aliases"]
    }
    assert "maya" in software_names
    assert "nuke" in software_names
    assert "nuke-13" in software_names
    assert "houdini" in software_names


@then("each alias should include the correct packages")
def check_alias_packages(prod_env_context):
    """Vérifier que chaque alias inclut les packages corrects."""
    for alias in prod_env_context["rez_aliases"]:
        if alias["software"] == "maya":
            assert "vfxCore-2.5" in alias["packages"]  # Common package
            assert ("vfxMayaTools-2.3" in
                    alias["packages"])  # Maya-specific package
            assert "mtoa-2.3" in alias["packages"]  # Plugin
            assert "golaem-4" in alias["packages"]  # Plugin

        elif alias["software"] == "nuke":
            assert "vfxCore-2.5" in alias["packages"]  # Common package
            assert ("vfxNukeTools-2.1" in
                    alias["packages"])  # Nuke-specific package
            assert "ofxSuperResolution" in alias["packages"]  # Plugin
            assert "neatVideo" in alias["packages"]  # Plugin


@then("I should get a list of all configured software with their versions")
def check_software_list(prod_env_context):
    """
    Vérifier que la liste des logiciels configurés avec leurs versions 
    est correcte.
    """
    with (
        prod_env_context["mock_load_config_paths"],
        prod_env_context["mock_validate_rez"],
    ):

        if "prod_env" not in prod_env_context:
            prod_env = ProductionEnvironment(
                prod_env_context["prod_name"], 
                prod_env_context["logger"]
            )
            prod_env_context["prod_env"] = prod_env

        software_list = prod_env_context["prod_env"].get_software_list()

        # Vérifier que tous les logiciels sont dans la liste
        software_dict = {
            sw["name"]: sw["version"] for sw in software_list
        }
        assert "maya" in software_dict
        assert "nuke" in software_dict
        assert "nuke-13" in software_dict
        assert "houdini" in software_dict

        # Vérifier les versions
        assert software_dict["maya"] == "2023.3.2"
        assert software_dict["nuke"] == "12.3"
        assert software_dict["nuke-13"] == "13.2"
        assert software_dict["houdini"] == "19.5"


@given("the production environment is activated")
def production_env_activated(prod_env_context):
    """S'assurer que l'environnement de production est activé."""
    with (
        prod_env_context["mock_load_config_paths"],
        prod_env_context["mock_set_env_vars"],
        prod_env_context["mock_create_alias"],
        prod_env_context["mock_validate_rez"],
    ):

        prod_env = ProductionEnvironment(
            prod_env_context["prod_name"], prod_env_context["logger"]
        )
        prod_env.activate()

        # Sauvegarder l'environnement dans le contexte
        prod_env_context["prod_env"] = prod_env


@when("I execute Maya with additional packages")
def execute_maya_with_packages(prod_env_context):
    """Exécuter Maya avec des packages supplémentaires."""
    # Mock pour execute_with_rez
    with mock.patch(
        "src.rez_manager.RezManager.execute_with_rez"
    ) as mock_execute:
        mock_execute.return_value = (0, "", "")

        additional_packages = ["dev-package-1", "dev-package-2"]
        prod_env_context["prod_env"].execute_software(
            "maya", additional_packages
        )

        # Sauvegarder les arguments dans le contexte
        prod_env_context["execute_args"] = mock_execute.call_args[0]
        prod_env_context["execute_kwargs"] = mock_execute.call_args[1]


@then("Maya should be launched with the additional packages")
def check_maya_launched_with_packages(prod_env_context):
    """Vérifier que Maya est lancé avec les packages supplémentaires."""
    # Vérifier que execute_with_rez a été appelé avec les bons arguments
    args = prod_env_context["execute_args"]
    assert args[0] == "maya"  # software_name
    assert args[1] == "2023.3.2"  # version

    # Vérifier que les packages supplémentaires sont inclus
    assert "dev-package-1" in args[2]  # packages
    assert "dev-package-2" in args[2]  # packages
