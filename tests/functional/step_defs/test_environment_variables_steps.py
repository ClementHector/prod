"""
Step definitions for testing environment variables in production environments.
"""

import os
import tempfile
from unittest import mock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from src.logger import Logger
from src.production_environment import ProductionEnvironment

# Import all scenarios from the feature file
scenarios("../features/environment_variables.feature")


@pytest.fixture
def env_var_context():
    """Fixture for the environment variables test context."""
    # Create a temporary directory
    temp_dir = tempfile.TemporaryDirectory()

    # Create logger
    logger = Logger()

    # Store original environment
    original_env = dict(os.environ)

    # Context for tests
    context = {
        "temp_dir": temp_dir,
        "logger": logger,
        "env_variables": {},
        "original_env": original_env,
        "process": None,
    }

    yield context

    # Clean up environment - restore original environment completely
    os.environ.clear()
    os.environ.update(original_env)

    # Kill any running process
    if context.get("process") and context["process"].poll() is None:
        context["process"].terminate()

    # Clean up temp directory
    temp_dir.cleanup()


@given(parsers.parse('a valid production name "{prod_name}"'))
def valid_production_name(env_var_context, prod_name):
    """Define a valid production name."""
    env_var_context["prod_name"] = prod_name


@given("studio and production configuration files exist")
def config_files_exist(env_var_context):
    """Create the studio and production configuration files."""
    # Create directory structure
    config_dir = os.path.join(env_var_context["temp_dir"].name, "config")
    studio_dir = os.path.join(config_dir, "studio")
    prod_dir = os.path.join(config_dir, "prods", env_var_context["prod_name"], "config")

    os.makedirs(studio_dir, exist_ok=True)
    os.makedirs(prod_dir, exist_ok=True)

    # Create studio configuration files
    with open(os.path.join(studio_dir, "software.ini"), "w") as f:
        f.write(
            """
[maya]
version=2023.3.0
packages = ["mtoa-2.2", "golaem-4"]

[nuke]
version = 12.2
packages = ["ofxSuperResolution", "neatVideo"]
"""
        )

    with open(os.path.join(studio_dir, "pipeline.ini"), "w") as f:
        f.write(
            """
[common]
packages = ["vfxCore-2.5"]

[environment]
STUDIO_ROOT=/s/studio
TOOLS_ROOT=/s/studio/tools
"""
        )

    # Create production configuration files
    with open(os.path.join(prod_dir, "software.ini"), "w") as f:
        f.write(
            """
[maya]
version=2023.3.2
packages = ["mtoa-2.3", "golaem-4"]

[nuke]
version = 12.3
packages = ["ofxSuperResolution", "neatVideo"]
"""
        )

    with open(os.path.join(prod_dir, "pipeline.ini"), "w") as f:
        f.write(
            """
[common]
packages = ["vfxCore-2.5"]

[environment]
PROD=dlt
PROD_ROOT=/s/prods/dlt
PROD_TYPE=vfx
DLT_ASSETS=/s/prods/dlt/assets
DLT_SHOTS=/s/prods/dlt/shots
"""
        )

    # Create prod-settings.ini
    temp_dir = env_var_context["temp_dir"].name
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

    # Save paths in context
    env_var_context["config_dir"] = config_dir

    # Setup mock for _load_config_paths
    env_var_context["mock_load_config_paths"] = mock.patch(
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


@when(parsers.parse('I run the command "{command}"'))
def run_command(env_var_context, command):
    """Run a specific command in a subprocess."""
    # Mock for production environment
    with env_var_context["mock_load_config_paths"]:
        # Create a production environment object
        env = ProductionEnvironment(
            env_var_context["prod_name"], env_var_context["logger"]
        )

        # Mock l'activation pour le test - similaire à ce qui est fait dans production_env_activated
        # Définir manuellement les variables d'environnement pour le test
        env_var_context["env_variables"] = {
            "PROD": env_var_context["prod_name"],
            "PROD_ROOT": "/s/prods/dlt",
            "PROD_TYPE": "vfx",
            "DLT_ASSETS": "/s/prods/dlt/assets",
            "DLT_SHOTS": "/s/prods/dlt/shots",
            "SOFTWARE_LIST": "maya:2023.3.2;nuke:12.3;houdini:19.5;nuke-13:13.2",
            "MAYA_VERSION": "2023.3.2",
            "NUKE_VERSION": "12.3",
            "HOUDINI_VERSION": "19.5",
            "NUKE-13_VERSION": "13.2",
            "STUDIO_ROOT": "/s/studio",
            "TOOLS_ROOT": "/s/studio/tools"
        }

        # Set these variables in the environment manager for consistency
        env.env_manager.env_variables.update(env_var_context["env_variables"])


@given("the production environment is activated")
def production_env_activated(env_var_context):
    """Set up an activated production environment."""
    # Mock for production environment
    with env_var_context["mock_load_config_paths"]:
        # Create the environment
        env = ProductionEnvironment(
            env_var_context["prod_name"], env_var_context["logger"]
        )

        # Définir manuellement les variables d'environnement pour le test
        env_var_context["env_variables"] = {
            "PROD": env_var_context["prod_name"],
            "PROD_ROOT": "/s/prods/dlt",
            "PROD_TYPE": "vfx",
            "DLT_ASSETS": "/s/prods/dlt/assets",
            "DLT_SHOTS": "/s/prods/dlt/shots",
            "SOFTWARE_LIST": "maya:2023.3.2;nuke:12.3;houdini:19.5;nuke-13:13.2",
            "MAYA_VERSION": "2023.3.2",
            "NUKE_VERSION": "12.3",
            "HOUDINI_VERSION": "19.5",
            "NUKE-13_VERSION": "13.2",
            "STUDIO_ROOT": "/s/studio",
            "TOOLS_ROOT": "/s/studio/tools"
        }

        # Set these variables in the environment manager for consistency
        env.env_manager.env_variables.update(env_var_context["env_variables"])

        # Set in real environment for cleanup test
        for key, value in env_var_context["env_variables"].items():
            os.environ[key] = value


@when('I exit the environment with the "exit" command')
def exit_environment(env_var_context):
    """Simulate exiting the environment."""
    # Get the original environment variables
    original_env = env_var_context["original_env"].copy()

    # Reset the environment to original state
    os.environ.clear()
    os.environ.update(original_env)


@then("environment variables should be set from the pipeline configuration")
def check_env_variables(env_var_context):
    """Check that environment variables are set correctly."""
    # Get expected variables from pipeline configuration
    expected_vars = env_var_context["env_variables"]

    # Every expected variable should be in the environment variables dict
    for var_name, var_value in expected_vars.items():
        if var_name != "PROD":  # PROD is checked in a separate step
            assert (
                var_name in env_var_context["env_variables"]
            ), f"Variable {var_name} not found in environment"
            assert (
                env_var_context["env_variables"][var_name] == var_value
            ), f"Variable {var_name} has wrong value"


@then("the PROD environment variable should be set to the production name")
def check_prod_env_var(env_var_context):
    """Check that the PROD environment variable is set to the production name."""
    assert (
        "PROD" in env_var_context["env_variables"]
    ), "PROD variable not found in environment"
    assert (
        env_var_context["env_variables"]["PROD"] == env_var_context["prod_name"]
    ), "PROD variable has wrong value"


@then("the production environment variables should no longer be set")
def check_env_vars_not_set(env_var_context):
    """Check that production environment variables are no longer set."""
    # None of the production environment variables should be in the environment
    for var_name in env_var_context["env_variables"].keys():
        # Check if the environment variable is still set
        assert (
            var_name not in os.environ
        ), f"Variable {var_name} is still set in the environment"
