"""
Step definitions pour les tests fonctionnels de gestion de configuration.
"""

import os
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from src.config_manager import ConfigManager

# Importer tous les scénarios du fichier feature
scenarios("../features/configuration.feature")


@pytest.fixture
def config_context():
    """Fixture pour le contexte des tests de configuration."""
    context = {
        "temp_dir": tempfile.TemporaryDirectory(),
        "config_manager": ConfigManager(),
    }

    yield context

    # Cleanup
    context["temp_dir"].cleanup()


@given("a studio-wide software configuration file exists")
def studio_config_file(config_context):
    """Créer un fichier de configuration studio."""
    studio_config_path = os.path.join(
        config_context["temp_dir"].name, "studio_software.ini"
    )
    with open(studio_config_path, "w") as f:
        f.write(
            """
[maya]
version = 2023.3.0
packages = ["mtoa-2.2", "golaem-4"]

[nuke]
version = 12.2
packages = ["ofxSuperResolution", "neatVideo"]

[houdini]
version = 19.0
packages = ["redshift-3.5.10"]
"""
        )

    config_context["studio_config_path"] = studio_config_path


@given("a production-specific software configuration file exists")
def production_config_file(config_context):
    """Créer un fichier de configuration spécifique à la production."""
    prod_config_path = os.path.join(
        config_context["temp_dir"].name, "prod_software.ini"
    )
    with open(prod_config_path, "w") as f:
        f.write(
            """
[maya]
version = 2023.3.2
packages = ["mtoa-2.3", "golaem-4"]

[nuke]
version = 12.3
packages = ["ofxSuperResolution", "neatVideo"]

[nuke-13]
version = 13.2
packages = ["ofxSuperResolution", "neatVideo"]
"""
        )

    config_context["prod_config_path"] = prod_config_path


@when("I load both configuration files")
def load_configs(config_context):
    """Charger les deux fichiers de configuration."""
    config_context["config_manager"].merge_configs(
        [
            config_context["studio_config_path"],
            config_context["prod_config_path"],
        ]
    )


@then("the merged configuration should contain all sections")
def check_merged_sections(config_context):
    """Vérifier que la configuration fusionnée contient toutes les sections."""
    sections = config_context["config_manager"].get_sections()
    assert "maya" in sections
    assert "nuke" in sections
    assert "nuke-13" in sections
    assert "houdini" in sections


@then("production-specific values should override studio-wide values")
def check_override_values(config_context):
    """Vérifier que les valeurs spécifiques à la production remplacent les valeurs studio."""
    # Maya version should be from prod config
    maya_version = config_context["config_manager"].get_merged_config(
        "maya", "version"
    )
    assert maya_version == "2023.3.2"

    # Nuke version should be from prod config
    nuke_version = config_context["config_manager"].get_merged_config(
        "nuke", "version"
    )
    assert nuke_version == "12.3"

    # Houdini version should be from studio config (not overridden)
    houdini_version = config_context["config_manager"].get_merged_config(
        "houdini", "version"
    )
    assert houdini_version == "19.0"


@then("I should get the production-specific Maya version")
def check_maya_version(config_context):
    """Vérifier que la version de Maya est celle spécifique à la production."""
    maya_version = config_context["config_manager"].get_merged_config(
        "maya", "version"
    )
    assert maya_version == "2023.3.2"


@then("I should get the production-specific Nuke version")
def check_nuke_version(config_context):
    """Vérifier que la version de Nuke est celle spécifique à la production."""
    nuke_version = config_context["config_manager"].get_merged_config(
        "nuke", "version"
    )
    assert nuke_version == "12.3"


@then("Maya should have the specified required packages")
def check_maya_packages(config_context):
    """Vérifier que Maya a les packages requis spécifiés."""
    maya_packages = config_context["config_manager"].get_merged_config(
        "maya", "packages"
    )
    assert "mtoa-2.3" in maya_packages
    assert "golaem-4" in maya_packages


@then("Nuke should have the specified required packages")
def check_nuke_packages(config_context):
    """Vérifier que Nuke a les packages requis spécifiés."""
    nuke_packages = config_context["config_manager"].get_merged_config(
        "nuke", "packages"
    )
    assert "ofxSuperResolution" in nuke_packages
    assert "neatVideo" in nuke_packages


@when("I apply a temporary override to Maya version")
def apply_override(config_context):
    """Appliquer un override temporaire à la version de Maya."""
    config_context["config_manager"].apply_temporary_override(
        "maya", "version", "2023.4.0"
    )


@then("I should get the overridden Maya version")
def check_overridden_version(config_context):
    """Vérifier que la version de Maya est celle spécifiée par l'override."""
    maya_version = config_context["config_manager"].get_merged_config(
        "maya", "version"
    )
    assert maya_version == "2023.4.0"
