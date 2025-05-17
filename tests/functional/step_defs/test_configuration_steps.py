"""
Step definitions pour les tests fonctionnels de gestion de configuration.
"""

import os
import tempfile

import pytest
from pytest_bdd import given, scenarios, then, when

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
    """Check that the merged configuration contains all sections."""
    sections = config_context["config_manager"].get_sections()
    assert "maya" in sections
    assert "nuke" in sections
    assert "nuke-13" in sections
    assert "houdini" in sections


@then("production-specific values should override studio-wide values")
def check_override_values(config_context):
    """
    Check that production-specific values override studio-wide values.
    """
    # Maya version should be from prod config
    maya_version = config_context["config_manager"].get_merged_config("maya", "version")
    assert maya_version == "2023.3.2"

    # Nuke version should be from prod config
    nuke_version = config_context["config_manager"].get_merged_config("nuke", "version")
    assert nuke_version == "12.3"

    # Houdini version should be from studio config (not overridden)
    houdini_version = config_context["config_manager"].get_merged_config(
        "houdini", "version"
    )
    assert houdini_version == "19.0"


@then("I should get the production-specific Maya version")
def check_maya_version(config_context):
    """Check that the Maya version is the production-specific one."""
    maya_version = config_context["config_manager"].get_merged_config("maya", "version")
    assert maya_version == "2023.3.2"


@then("I should get the production-specific Nuke version")
def check_nuke_version(config_context):
    """Check that the Nuke version is the production-specific one."""
    nuke_version = config_context["config_manager"].get_merged_config("nuke", "version")
    assert nuke_version == "12.3"


@then("Maya should have the specified required packages")
def check_maya_packages(config_context):
    """Check that Maya has the specified required packages."""
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


@then("I should get the overridden Maya version")
def check_overridden_version(config_context):
    """Vérifier que la version de Maya est celle spécifiée par l'override."""
    maya_version = config_context["config_manager"].get_merged_config("maya", "version")
    assert maya_version == "2023.4.0"


@given("a prod-settings.ini file with mixed path separators")
def prod_settings_with_mixed_separators(config_context):
    """Create a prod-settings.ini file with mixed path separators."""
    # Create the prod-settings.ini file
    settings_path = os.path.join(config_context["temp_dir"].name, "prod-settings.ini")

    with open(settings_path, "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini:/unix/path/software.ini:C:\\path\\to\\prod\\{PROD_NAME}\\config\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\studio\\pipeline.ini:/unix/path/pipeline.ini:C:\\path\\to\\prod\\{PROD_NAME}\\config\\pipeline.ini
"""
        )

    config_context["settings_path"] = settings_path
    config_context["prod_name"] = "test_prod"


@when("I initialize the production environment")
def initialize_production_environment(config_context, monkeypatch):
    """Initialize the production environment with the mixed path separators."""
    from src.logger import Logger
    from src.production_environment import ProductionEnvironment

    # Mock the logger
    logger = Logger()  # Mock Path.exists to always return True
    from pathlib import Path

    original_exists = Path.exists

    def mock_exists(self):
        return True

    monkeypatch.setattr(Path, "exists", mock_exists)

    # Mock path joining for prod-settings.ini
    original_joinpath = Path.joinpath

    def mock_joinpath(self, *args):
        if args and "prod-settings.ini" in str(args[-1]):
            return Path(config_context["settings_path"])
        return original_joinpath(self, *args)

    monkeypatch.setattr(Path, "joinpath", mock_joinpath)

    # Keep the os.path mocks for backward compatibility
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    def mock_path_join(*args):
        if args and "prod-settings.ini" in args[-1]:
            return config_context["settings_path"]
        # Use the real os.path.join for other cases, but avoiding recursion
        return os.path.normpath("/".join(args))

    monkeypatch.setattr(os.path, "join", mock_path_join)

    # Create the production environment
    config_context["prod_env"] = ProductionEnvironment(
        config_context["prod_name"],
    )


@then("the configuration paths should be correctly split")
def check_configuration_paths(config_context):
    """Check that the configuration paths are correctly split."""
    config_paths = config_context["prod_env"].config_paths

    # Get the actual paths as they are
    software_paths = config_paths["software"]
    pipeline_paths = config_paths["pipeline"]

    # Manually check that the expected path segments are present
    found_studio_software = False
    found_unix_software = False
    found_prod_software = False

    # Check in all path strings for each piece
    for path in software_paths:
        if "studio" in path and "software.ini" in path:
            found_studio_software = True
        if "/unix/path" in path and "software.ini" in path:
            found_unix_software = True
        if "prod" in path and "test_prod" in path and "software.ini" in path:
            found_prod_software = True

    # Assert that all path segments were found
    assert found_studio_software, "Missing studio software path"
    assert found_unix_software, "Missing Unix software path"
    assert found_prod_software, "Missing production software path"

    # Similar check for pipeline paths
    found_studio_pipeline = False
    found_unix_pipeline = False
    found_prod_pipeline = False

    for path in pipeline_paths:
        if "studio" in path and "pipeline.ini" in path:
            found_studio_pipeline = True
        if "/unix/path" in path and "pipeline.ini" in path:
            found_unix_pipeline = True
        if "prod" in path and "test_prod" in path and "pipeline.ini" in path:
            found_prod_pipeline = True

    # Assert that all path segments were found
    assert found_studio_pipeline, "Missing studio pipeline path"
    assert found_unix_pipeline, "Missing Unix pipeline path"
    assert found_prod_pipeline, "Missing production pipeline path"


@then("the software configuration should be properly loaded")
def check_software_configuration_loading(config_context, monkeypatch):
    """Check that the software configuration is properly loaded."""
    # This step is mainly to verify that no errors occur during configuration loading
    # We've already mocked the file existence check, so this is a simple assertion
    assert hasattr(config_context["prod_env"], "software_config")
    assert config_context["prod_env"].software_config is not None


@then("the available software should be correctly listed")
def check_available_software(config_context, monkeypatch):
    """Check that the available software is correctly listed."""
    # Mock the get_configured_software method to return a list of software
    monkeypatch.setattr(
        config_context["prod_env"].software_config,
        "get_configured_software",
        lambda: ["maya", "nuke", "houdini"],
    )

    # Mock the get_software_version method to return a version for each software
    def mock_get_software_version(software_name):
        versions = {"maya": "2023.3.2", "nuke": "13.2", "houdini": "19.5"}
        return versions.get(software_name, "1.0.0")

    monkeypatch.setattr(
        config_context["prod_env"].software_config,
        "get_software_version",
        mock_get_software_version,
    )

    # Get the software list
    software_list = config_context["prod_env"].get_software_list()

    # Check the software list
    assert len(software_list) == 3

    # Check all expected software is present
    software_names = [item["name"] for item in software_list]
    assert "maya" in software_names
    assert "nuke" in software_names
    assert "houdini" in software_names

    # Check that versions are included
    for item in software_list:
        assert "version" in item, f"Version missing for {item['name']}"
        assert item["version"] == mock_get_software_version(item["name"])
