"""
Steps implementation for configuration management scenarios.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

from behave import given, then, when

from src.config_manager import ConfigManager
from src.logger import Logger
from src.production_environment import (
    ProductionEnvironment,
    SoftwareConfig,
)


@given("a studio-wide software configuration file exists")
def step_impl_studio_config_exists(context):
    context.temp_dir = tempfile.TemporaryDirectory()

    # Create studio-wide software config
    context.studio_config_path = os.path.join(
        context.temp_dir.name, "studio-software.ini"
    )
    with open(context.studio_config_path, "w") as f:
        f.write(
            """
[maya]
version = 2022
packages = ["mayaUSD", "mtoa"]

[nuke]
version = 13.0
packages = ["neatvideo", "cryptomatte"]

[houdini]
version = 19.0
packages = ["redshift", "karma"]
"""
        )


@given("a production-specific software configuration file exists")
def step_impl_prod_config_exists(context):
    # Create production-specific software config
    context.prod_config_path = os.path.join(context.temp_dir.name, "prod-software.ini")
    with open(context.prod_config_path, "w") as f:
        f.write(
            """
[maya]
version = 2023
packages = ["golaem", "mtoa"]

[nuke]
packages = ["superStereo", "neatvideo"]

[common]
packages = ["python3", "pyside2"]
"""
        )


@when("I load both configuration files")
def step_impl_load_both_configs(context):
    context.config_manager = ConfigManager()
    context.config_manager.merge_configs(
        [context.studio_config_path, context.prod_config_path]
    )
    context.software_config = SoftwareConfig(context.config_manager)


@then("the merged configuration should contain all sections")
def step_impl_merged_contains_all_sections(context):
    sections = context.config_manager.get_sections()
    assert "maya" in sections
    assert "nuke" in sections
    assert "houdini" in sections
    assert "common" in sections


@then("production-specific values should override studio-wide values")
def step_impl_prod_overrides_studio(context):
    # Maya version should be from production config
    maya_version = context.config_manager.get_merged_config("maya", "version")
    assert maya_version == "2023"

    # Nuke version should still be from studio config
    nuke_version = context.config_manager.get_merged_config("nuke", "version")
    assert nuke_version == "13.0"


@then("I should get the production-specific Maya version")
def step_impl_get_prod_maya_version(context):
    maya_version = context.software_config.get_software_version("maya")
    assert maya_version == "2023"


@then("I should get the production-specific Nuke version")
def step_impl_get_prod_nuke_version(context):
    nuke_version = context.software_config.get_software_version("nuke")
    assert nuke_version == "13.0"


@then("Maya should have the specified required packages")
def step_impl_maya_required_packages(context):
    packages = context.software_config.get_required_packages("maya")
    assert "golaem" in packages
    assert "mtoa" in packages
    assert len(packages) == 2


@then("Nuke should have the specified required packages")
def step_impl_nuke_required_packages(context):
    packages = context.software_config.get_required_packages("nuke")
    assert "superStereo" in packages
    assert "neatvideo" in packages
    assert len(packages) == 2


@when("I apply a temporary override to Maya version")
def step_impl_apply_temp_override(context):
    context.config_manager.apply_temporary_override("maya", "version", "2024")


@then("I should get the overridden Maya version")
def step_impl_get_overridden_version(context):
    version = context.config_manager.get_merged_config("maya", "version")
    assert version == "2024"

    # SoftwareConfig should also use the override
    version = context.software_config.get_software_version("maya")
    assert version == "2024"


@given("a prod-settings.ini file with mixed path separators")
def step_impl_prod_settings_with_mixed_separators(context):
    context.temp_dir = tempfile.TemporaryDirectory()

    # Create settings file
    context.settings_path = os.path.join(context.temp_dir.name, "prod-settings.ini")
    with open(context.settings_path, "w") as f:
        f.write(
            """
[environment]
SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini:C:\\path\\to\\prod\\{PROD_NAME}\\config\\software.ini
PIPELINE_CONFIG=C:\\path\\to\\studio\\pipeline.ini:C:\\path\\to\\prod\\{PROD_NAME}\\config\\pipeline.ini
"""
        )

    # Create the software configuration files
    os.makedirs(
        os.path.join(context.temp_dir.name, "path", "to", "studio"), exist_ok=True
    )
    os.makedirs(
        os.path.join(
            context.temp_dir.name, "path", "to", "prod", "test_prod", "config"
        ),
        exist_ok=True,
    )

    # Studio software config
    studio_config_path = os.path.join(
        context.temp_dir.name, "path", "to", "studio", "software.ini"
    )
    with open(studio_config_path, "w") as f:
        f.write(
            """
[maya]
version = 2022
packages = ["mayaUSD", "mtoa"]

[nuke]
version = 13.0
packages = ["neatvideo", "cryptomatte"]
"""
        )

    # Production software config
    prod_config_path = os.path.join(
        context.temp_dir.name,
        "path",
        "to",
        "prod",
        "test_prod",
        "config",
        "software.ini",
    )
    with open(prod_config_path, "w") as f:
        f.write(
            """
[maya]
version = 2023
packages = ["golaem", "mtoa"]
"""
        )

    # Pipeline configs will be ignored in this test
    context.studio_config_path = studio_config_path.replace("\\", os.path.sep)
    context.prod_config_path = prod_config_path.replace("\\", os.path.sep)

    # Store the created file paths for verification
    context.expected_software_paths = [
        context.studio_config_path,
        context.prod_config_path,
    ]


@when("I initialize the production environment")
def step_impl_initialize_prod_env(context):
    # Create a mock logger
    context.logger = MagicMock(spec=Logger)

    # Patch to use our temporary directory and paths
    with patch("os.path.dirname", return_value=os.path.dirname(context.settings_path)):
        with patch("os.path.join", side_effect=lambda *args: os.path.join(*args)):
            with patch(
                "os.path.exists",
                side_effect=lambda path: (
                    os.path.exists(
                        path.replace(
                            "C:\\path", os.path.join(context.temp_dir.name, "path")
                        )
                    )
                    if path.startswith("C:\\path")
                    else os.path.exists(path)
                ),
            ):
                with patch("src.production_environment.ConfigManager.load_config"):
                    # Initialize the production environment
                    context.prod_env = ProductionEnvironment(
                        "test_prod",
                    )

                    # Store the config paths for verification
                    context.config_paths = context.prod_env.config_paths


@then("the configuration paths should be correctly split")
def step_impl_config_paths_correctly_split(context):
    # Check that there are 2 software config paths
    assert len(context.config_paths["software"]) == 2

    # Check that the paths are as expected
    assert context.config_paths["software"][0] == "C:\\path\\to\\studio\\software.ini"
    assert (
        context.config_paths["software"][1]
        == "C:\\path\\to\\prod\\test_prod\\config\\software.ini"
    )


@then("the software configuration should be properly loaded")
def step_impl_software_config_properly_loaded(context):
    # Patch load_config to use our test files
    def mock_load_config_side_effect(self, path):
        if path.startswith("C:\\path"):
            # Modify the path to point to our temp directory
            modified_path = path.replace(
                "C:\\path", os.path.join(context.temp_dir.name, "path")
            )
            modified_path = modified_path.replace("\\", os.path.sep)
            # Call the real ConfigManager.load_config with the modified path
            real_config = ConfigManager()
            real_config.merge_configs([modified_path])
            # Copy the config parser to the mocked object
            self.config_parser = real_config.config_parser
            self.override_config = real_config.override_config
        return None

    # Create a real ProductionEnvironment with our test files
    with patch("os.path.dirname", return_value=os.path.dirname(context.settings_path)):
        with patch("os.path.join", side_effect=lambda *args: os.path.join(*args)):
            with patch(
                "os.path.exists",
                side_effect=lambda path: (
                    os.path.exists(
                        path.replace(
                            "C:\\path", os.path.join(context.temp_dir.name, "path")
                        )
                    )
                    if path.startswith("C:\\path")
                    else os.path.exists(path)
                ),
            ):
                with patch.object(
                    ConfigManager, "load_config", mock_load_config_side_effect
                ):
                    prod_env = ProductionEnvironment("test_prod")

                    # Verify that the software configuration is correctly loaded
                    assert (
                        prod_env.software_config.get_software_version("maya") == "2023"
                    )
                    assert (
                        prod_env.software_config.get_software_version("nuke") == "13.0"
                    )
                    assert "golaem" in prod_env.software_config.get_required_packages(
                        "maya"
                    )


@then("the available software should be correctly listed")
def step_impl_available_software_correctly_listed(context):
    # Create a real ProductionEnvironment with our test files
    with patch("os.path.dirname", return_value=os.path.dirname(context.settings_path)):
        with patch("os.path.join", side_effect=lambda *args: os.path.join(*args)):
            with patch(
                "os.path.exists",
                side_effect=lambda path: (
                    os.path.exists(
                        path.replace(
                            "C:\\path", os.path.join(context.temp_dir.name, "path")
                        )
                    )
                    if path.startswith("C:\\path")
                    else os.path.exists(path)
                ),
            ):
                with patch.object(
                    ConfigManager,
                    "load_config",
                    side_effect=lambda self, path: (
                        ConfigManager.load_config(
                            self,
                            path.replace(
                                "C:\\path", os.path.join(context.temp_dir.name, "path")
                            ).replace("\\", os.path.sep),
                        )
                        if path.startswith("C:\\path")
                        else None
                    ),
                ):
                    prod_env = ProductionEnvironment("test_prod")

                    # Get the list of available software
                    software_list = prod_env.software_config.get_configured_software()

                    # Verify that the expected software are listed
                    assert "maya" in software_list
                    assert "nuke" in software_list


@when("I request the configuration for a specific software")
def request_software_configuration(context):
    """Request configuration for a specific software."""
    # Mock config manager to return our test config
    with patch.object(ConfigManager, "load_config", return_value=context.merged_config):
        # Create a ProductionEnvironment
        context.prod_env = ProductionEnvironment("test_prod")

        # Get the software configuration
        context.software_config = context.prod_env.get_software_config()


@then("the separator in paths should be interpreted correctly for the OS")
def check_path_separators(context):
    """Check that path separators are interpreted correctly for the OS."""
    # Create a test config with Windows paths but Unix separator and vice versa
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a settings file with mixed separators
        settings_path = os.path.join(temp_dir, "prod-settings.ini")
        with open(settings_path, "w") as f:
            f.write(
                "[environment]\n"
                "SOFTWARE_CONFIG=C:\\path\\to\\studio\\software.ini:"
                "C:\\path\\to\\prod\\{PROD_NAME}\\config\\software.ini\n"
            )
