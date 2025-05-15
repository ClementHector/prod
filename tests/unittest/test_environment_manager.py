"""
Unit tests for the EnvironmentManager class.
"""

import os
import platform
import tempfile
from unittest.mock import patch

import pytest

from src.environment_manager import EnvironmentManager


@pytest.fixture
def env_manager():
    """
    Fixture to create an environment manager.

    Returns:
        EnvironmentManager
    """
    return EnvironmentManager()


def test_generate_powershell_script(env_manager):
    """
    Test generating a PowerShell script.
    """
    # Configure the test environment
    with patch("platform.system", return_value="Windows"):
        # Set environment variables
        env_manager.set_environment_variables(
            {"PROD": "dlt", "PROD_ROOT": "/s/prods/dlt", "PROD_TYPE": "vfx"}
        )

        # Generate the script
        script_path = env_manager.generate_shell_script("dlt")

        # Verify that the file exists
        assert os.path.exists(script_path)
        assert script_path.endswith(".ps1")

        # Verify the script content
        with open(script_path, "r") as f:
            content = f.read()
            assert "$env:PROD = 'dlt'" in content
            assert "$env:PROD_ROOT = '/s/prods/dlt'" in content
            assert "$env:PROD_TYPE = 'vfx'" in content
            assert "Set-ProdEnvironment" in content


def test_generate_bash_script(env_manager):
    """
    Test generating a Bash script.
    """
    # Configure the test environment
    with patch("platform.system", return_value="Linux"):
        # Set environment variables
        env_manager.set_environment_variables(
            {"PROD": "dlt", "PROD_ROOT": "/s/prods/dlt", "PROD_TYPE": "vfx"}
        )

        # Generate the script
        script_path = env_manager.generate_shell_script("dlt")

        # Verify that the file exists
        assert os.path.exists(script_path)
        assert script_path.endswith(".sh")

        # Verify the script content
        with open(script_path, "r") as f:
            content = f.read()
            assert "export PROD='dlt'" in content
            assert "export PROD_ROOT='/s/prods/dlt'" in content
            assert "export PROD_TYPE='vfx'" in content
            assert "#!/bin/bash" in content


def test_apply_environment_to_parent_shell(env_manager):
    """
    Test applying environment variables to the parent shell.
    This is primarily a test of the function rather than its effect,
    as it's not actually possible to modify the parent shell's environment.
    """
    # Create a temporary file to simulate a shell script
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        suffix=".ps1" if platform.system() == "Windows" else ".sh",
    ) as tmp:
        tmp.write("# Test script\n")
        tmp_path = tmp.name

    try:
        # Mock subprocess.run to avoid real execution
        with patch("subprocess.run") as mock_run:
            # Call the method
            env_manager.apply_environment_to_parent_shell(tmp_path)

            # Verify that subprocess.run was called
            mock_run.assert_called_once()
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
