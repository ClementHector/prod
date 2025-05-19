"""
Unit tests for the interactive functions of EnvironmentManager.
"""

import os
from unittest.mock import patch

from src.environment_manager import EnvironmentManager


def test_generate_interactive_shell_script_with_software_list():
    """
    Test the generation of an interactive script with a directly provided software list.
    """
    # Test with Windows
    with patch("platform.system", return_value="Windows"):
        # Create the environment manager inside the patch context
        env_manager = EnvironmentManager()

        # Set environment variables
        env_manager.set_environment_variables(
            {"PROD": "dlt", "PROD_ROOT": "/s/prods/dlt", "PROD_TYPE": "vfx"}
        )

        # Prepare a software list
        software_list = ["maya:2024", "houdini:20.0", "nuke:14.0"]

        # Generate the script
        script_path = env_manager.generate_interactive_shell_script(
            "dlt", software_list
        )

        # Verify that the file exists
        assert os.path.exists(script_path)
        assert script_path.endswith(".ps1")  # PowerShell on Windows

        # Verify the script content
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

    # Test with Linux
    with patch("platform.system", return_value="Linux"):
        # Create a new environment manager inside the Linux patch context
        env_manager = EnvironmentManager()

        # Set environment variables
        env_manager.set_environment_variables(
            {"PROD": "dlt", "PROD_ROOT": "/s/prods/dlt", "PROD_TYPE": "vfx"}
        )

        # Generate the script
        script_path = env_manager.generate_interactive_shell_script(
            "dlt", software_list
        )

        # Verify that the file exists
        assert os.path.exists(script_path)
        assert script_path.endswith(".sh")  # Bash on Linux

        # Verify the script content
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
