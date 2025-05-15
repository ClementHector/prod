"""
Environment variable management for the Prod CLI tool.
"""

import os
import platform
import subprocess
import tempfile
from typing import Dict, List, Optional

from src.logger import get_logger

class EnvironmentManager:
    """
    Manages environment variables for production environments.
    """

    def __init__(self):
        """
        Initializes the environment manager.

        """
        self.logger = get_logger()
        self.system = platform.system()
        self.original_env = os.environ.copy()
        self.current_env = os.environ.copy()
        self.env_variables: Dict[str, str] = {}

    def set_environment_variables(self, variables: Dict[str, str]) -> None:
        """
        Sets up environment variables.

        Args:
            variables: Dictionary of environment variables to set
        """
        # Store all variables for script generation
        self.env_variables.update(variables)

        for key, value in variables.items():
            self._set_environment_variable(key, value)
            self.logger.debug(f"Set environment variable: {key}={value}")

    def _set_environment_variable(self, key: str, value: str) -> None:
        """
        Sets an environment variable.

        Args:
            key: Environment variable name
            value: Environment variable value
        """
        # Update the current environment
        self.current_env[key] = value

        # Set the environment variable in the process
        os.environ[key] = value

    def set_path_variables(self, path_variables: Dict[str, List[str]]) -> None:
        """
        Sets up path environment variables.

        Args:
            path_variables: Dictionary of path environment variables to set
        """
        for key, paths in path_variables.items():
            # Get the existing path
            existing_path = self.current_env.get(key, "")

            # Format paths according to the operating system
            formatted_paths = self._format_paths(paths)

            # Append the new paths to the existing path
            separator = self._get_path_separator()
            new_path = existing_path

            # Add each path if it's not already in the existing path
            for path in formatted_paths:
                # Normalize the path for comparison
                norm_path = self._normalize_path(path)

                # Check if the path is already in the existing path
                if existing_path and norm_path not in [
                    self._normalize_path(p) for p in existing_path.split(separator)
                ]:
                    new_path = f"{path}{separator}{new_path}" if new_path else path

            # Set the new path
            self._set_environment_variable(key, new_path)
            self.logger.debug(f"Set path variable: {key}={new_path}")

    def _format_paths(self, paths: List[str]) -> List[str]:
        """
        Formats paths according to the operating system.

        Args:
            paths: List of paths to format

        Returns:
            List of formatted paths
        """
        formatted_paths = []
        # Check the operating system at call time
        current_system = platform.system()

        for path in paths:
            # Replace environment variables in the path
            path = os.path.expandvars(path)

            # Format for Windows
            if current_system == "Windows":
                path = path.replace("/", "\\")

            formatted_paths.append(path)

        return formatted_paths

    def _get_path_separator(self) -> str:
        """
        Gets the path separator for the current operating system.

        Returns:
            Path separator
        """
        # Check the operating system at call time
        current_system = platform.system()
        return ";" if current_system == "Windows" else ":"

    def _normalize_path(self, path: str) -> str:
        """
        Normalizes a path for comparison.

        Args:
            path: Path to normalize

        Returns:
            Normalized path
        """
        return os.path.normpath(path.lower())

    def reset_environment(self) -> None:
        """
        Resets the environment to its original state.
        """
        # Remove all environment variables that were set by this manager
        for key in list(self.env_variables.keys()):
            if key in os.environ:
                del os.environ[key]

        # Restore original environment variables that were modified
        for key, value in self.original_env.items():
            if key not in os.environ and key in self.env_variables:
                os.environ[key] = value

        # Update the current environment
        self.current_env = os.environ.copy()
        # Clear the stored environment variables
        self.env_variables.clear()

        self.logger.debug("Reset environment to original state")

    def generate_shell_script(self, prod_name: str) -> str:
        """
        Generates a shell script that sets the environment variables.

        Args:
            prod_name: Name of the production

        Returns:
            Path to the generated script
        """
        # Check the operating system at call time
        # instead of using self.system which is defined at initialization
        current_system = platform.system()
        if current_system == "Windows":
            return self._generate_powershell_script(prod_name)
        else:
            return self._generate_bash_script(prod_name)

    def _generate_powershell_script(self, prod_name: str) -> str:
        """
        Generates a PowerShell script that sets the environment variables.

        Args:
            prod_name: Name of the production

        Returns:
            Path to the generated script
        """
        # Create a temporary file for the script
        script_dir = os.path.join(tempfile.gettempdir(), "prod_cli")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, f"prod_env_{prod_name}.ps1")

        with open(script_path, "w") as f:
            f.write("# Generated by Prod CLI\n")
            f.write("# This script sets up the environment for the production\n\n")

            # Add a function to set environment variables
            f.write("function Set-ProdEnvironment {\n")

            # Set each environment variable
            for key, value in self.env_variables.items():
                f.write(f"    $env:{key} = '{value}'\n")

            f.write(
                "    Write-Host \"Environment configured for production '{0}'\""
                "-f $env:PROD -ForegroundColor Green\n"
            )
            f.write("}\n\n")

            # Call the function
            f.write("# Call the function\n")
            f.write("Set-ProdEnvironment\n")

        self.logger.debug(f"Generated PowerShell script: {script_path}")

        return script_path

    def _generate_bash_script(self, prod_name: str) -> str:
        """
        Generates a Bash script that sets the environment variables.

        Args:
            prod_name: Name of the production

        Returns:
            Path to the generated script
        """
        # Create a temporary file for the script
        script_dir = os.path.join(tempfile.gettempdir(), "prod_cli")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, f"prod_env_{prod_name}.sh")

        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# Generated by Prod CLI\n")
            f.write("# This script sets up the environment for the production\n\n")

            # Set each environment variable
            for key, value in self.env_variables.items():
                f.write(f"export {key}='{value}'\n")

            f.write(
                '\nprintf "Environment configured for production \'%s\'\\n" "$PROD"\n'
            )

        # Make the script executable
        os.chmod(script_path, 0o755)

        self.logger.debug(f"Generated Bash script: {script_path}")

        return script_path

    def apply_environment_to_parent_shell(self, script_path: str) -> None:
        """
        Attempts to execute the script in the parent shell to apply environment variables.
        This is primarily used for testing and debugging, as in most shells
        this is not possible.

        Args:
            script_path: Path to the shell script
        """
        try:
            # Check the operating system at call time
            current_system = platform.system()

            if current_system == "Windows":
                # In PowerShell, use & operator to execute the script
                command = f"& '{script_path}'"
                subprocess.run(["powershell", "-Command", command], check=True)
            else:
                # In Bash, source the script
                command = f"source '{script_path}'"
                subprocess.run(["bash", "-c", command], check=True)

            self.logger.debug(f"Executed environment script: {script_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to execute environment script: {e}")

    def generate_interactive_shell_script(
        self, prod_name: str, software_list: Optional[List[str]] = None
    ) -> str:
        """
        Generates an interactive shell script that sets environment variables
        and defines an 'exit' command to properly exit the production environment.

        Args:
            prod_name: Name of the production
            software_list: Optional list of software items in format "name:version"

        Returns:
            Path to the generated script
        """
        # Check the operating system at call time
        current_system = platform.system()
        if current_system == "Windows":
            return self._generate_interactive_powershell_script(
                prod_name, software_list
            )
        else:
            return self._generate_interactive_bash_script(prod_name, software_list)

    def _generate_interactive_powershell_script(
        self, prod_name: str, software_list: Optional[List[str]] = None
    ) -> str:
        """
        Generates an interactive PowerShell script with custom exit function.

        Args:
            prod_name: Name of the production
            software_list: Optional list of software items in format "name:version"

        Returns:
            Path to the generated script
        """
        # Create a temporary file for the script
        script_dir = os.path.join(tempfile.gettempdir(), "prod_cli")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, f"prod_interactive_{prod_name}.ps1")

        with open(script_path, "w") as f:
            f.write("# Generated by Prod CLI\n")
            f.write("# This script sets up an interactive production environment\n\n")

            # Create a custom prompt to show the production name
            f.write("function global:prompt {\n")
            f.write(f'    "[PROD:{prod_name}] $(Get-Location)> "\n')
            f.write("}\n\n")

            # Define safe environment variable getter
            f.write("function Get-EnvSafe {\n")
            f.write('    param([string]$Name, [string]$Default = "")\n')
            f.write('    if (Test-Path "Env:\\${Name}") {\n')
            f.write('        return (Get-Item "Env:\\${Name}").Value\n')
            f.write("    }\n")
            f.write("    return $Default\n")
            f.write("}\n\n")

            # Create a function to set environment variables
            f.write("function Set-ProdEnvironment {\n")

            # Set each environment variable
            for key, value in self.env_variables.items():
                # Replace single quotes with escaped single quotes for PowerShell
                safe_value = value.replace("'", "''")
                f.write(f"    $env:{key} = '{safe_value}'\n")
            f.write("}")

            # Call the function
            f.write("# Set environment variables\n")
            f.write("Set-ProdEnvironment\n\n")

            # Create software alias functions
            f.write("# Define software aliases\n")

            # Use directly provided software list or fall back to environment variable
            software_items = []
            if software_list:
                software_items = software_list
            else:
                software_list_var = self.env_variables.get("SOFTWARE_LIST", "")
                if software_list_var:
                    software_items = software_list_var.split(";")

            for item in software_items:
                if ":" in item:
                    software_name, version = item.split(":", 1)
                    # Create a PowerShell function for each software
                    f.write(f"function global:{software_name} {{\n")
                    f.write("    param(\n")
                    f.write("        [Parameter(ValueFromRemainingArguments=$true)]\n")
                    f.write("        [string[]]$Params\n")
                    f.write("    )\n")

                    # Construct the Rez command
                    current_system = platform.system()
                    if current_system == "Windows":
                        # For Windows, use rez env with powershell
                        cmd = f'    $rezCmd = "rez env {software_name}-{version} -- {software_name}"\n'
                        f.write(cmd)
                        f.write("    if ($Params) {\n")
                        f.write('        $rezCmd += " " + ($Params -join " ")\n')
                        f.write("    }\n")
                        f.write("    Invoke-Expression $rezCmd\n")
                    else:
                        # For Unix, pass arguments directly
                        cmd = f"    rez env {software_name}-{version} -- {software_name} $Params\n"
                        f.write(cmd)

                    f.write("}\n\n")

                    # Add help text for the software
                    f.write(f"# Help for {software_name}\n")
                    f.write(f"function global:Help-{software_name} {{\n")
                    usage_msg = f'    Write-Host "Usage: {software_name} [options]" -ForegroundColor Cyan\n'
                    f.write(usage_msg)
                    launch_msg = (
                        f'    Write-Host "Launches {software_name} version {version} with Rez" '
                        f"-ForegroundColor Cyan\n"
                    )
                    f.write(launch_msg)
                    package_msg = (
                        f'    Write-Host "For package options, use: {software_name} '
                        f'--packages pkg1 pkg2" -ForegroundColor Cyan\n'
                    )
                    f.write(package_msg)
                    f.write("}\n\n")

            # Display welcome message
            f.write("$prodName = Get-EnvSafe 'PROD' 'unknown'\n")
            f.write(
                'Write-Host "==========================================" -ForegroundColor Cyan\n'
            )
            f.write(
                'Write-Host "PRODUCTION ENVIRONMENT ACTIVATED: " -NoNewline -ForegroundColor Cyan\n'
            )
            f.write('Write-Host "$prodName" -ForegroundColor Green\n')
            f.write(
                'Write-Host "==========================================" -ForegroundColor Cyan\n'
            )
            exit_msg = "Write-Host \"Type 'exit' to leave the production environment`n\" -ForegroundColor DarkGray\n\n"
            f.write(exit_msg)

            # List available software
            f.write('Write-Host "Available Software Tools:" -ForegroundColor Cyan\n')

            # Directly use software_items instead of parsing from environment variable
            if software_items:
                for item in software_items:
                    if ":" in item:
                        software_name, version = item.split(":", 1)
                        f.write(
                            f'Write-Host "* {software_name} (version {version})" -ForegroundColor White\n'
                        )
                    else:
                        f.write(f'Write-Host "* {item}" -ForegroundColor White\n')
            else:
                f.write(
                    'Write-Host "No software configured for this production" -ForegroundColor Yellow\n'
                )

        self.logger.debug(f"Generated interactive PowerShell script: {script_path}")

        return script_path

    def _generate_interactive_bash_script(
        self, prod_name: str, software_list: Optional[List[str]] = None
    ) -> str:
        """
        Generates an interactive Bash script with custom exit function.

        Args:
            prod_name: Name of the production
            software_list: Optional list of software items in format "name:version"

        Returns:
            Path to the generated script
        """
        # Create a temporary file for the script
        script_dir = os.path.join(tempfile.gettempdir(), "prod_cli")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, f"prod_interactive_{prod_name}.sh")

        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# Generated by Prod CLI\n")
            f.write("# This script sets up an interactive production environment\n\n")

            # Save original exit command
            f.write("# Save original exit command\n")
            f.write("function original_exit() {\n")
            f.write('    builtin exit "$@"\n')
            f.write("}\n\n")

            # Custom exit function to exit the production environment
            f.write("# Override exit command to exit production environment\n")
            f.write("function exit() {\n")
            f.write(
                '    printf "\\033[32mExited production environment \'%s\'\\033[0m\\n" "$PROD"\n'
            )
            f.write('    original_exit "$@"\n')
            f.write("}\n\n")

            # Set environment variables
            f.write("# Set environment variables\n")
            for key, value in self.env_variables.items():
                # Escape single quotes
                safe_value = value.replace("'", "'\\''")
                f.write(f"export {key}='{safe_value}'\n")

            # Define software aliases
            f.write("\n# Define software aliases\n")

            # Use directly provided software list or fall back to environment variable
            software_items = []
            if software_list:
                software_items = software_list
            else:
                software_list_var = self.env_variables.get("SOFTWARE_LIST", "")
                if software_list_var:
                    software_items = software_list_var.split(";")

            for item in software_items:
                if ":" in item:
                    software_name, version = item.split(":", 1)
                    # Create a bash function for each software
                    f.write(f"function {software_name}() {{\n")
                    f.write(
                        f'    rez env {software_name}-{version} -- {software_name} "$@"\n'
                    )
                    f.write("}\n")

                    # Export the function to make it available as a command
                    f.write(f"export -f {software_name}\n\n")

            # Custom prompt to show the production name
            f.write("\n# Set custom prompt\n")
            f.write('export PS1="[PROD:$PROD] \\w> "\n\n')

            # Display welcome message
            f.write("echo\n")
            f.write('printf "==========================================\\n"\n')
            f.write('printf "PRODUCTION ENVIRONMENT ACTIVATED: %s\\n" "$PROD"\n')
            f.write('printf "==========================================\\n"\n')
            f.write("echo\n")
            f.write(
                "printf \"Type 'exit' to leave the production environment\\n\\n\"\n"
            )

            # List available software
            f.write('printf "Available Software Tools:\\n"\n')

            # Directly use software_items instead of parsing from environment variable
            if software_items:
                for item in software_items:
                    if ":" in item:
                        software_name, version = item.split(":", 1)
                        f.write(
                            f'printf "  * {software_name} (version {version})\\n"\n'
                        )
                    else:
                        f.write(f'printf "  * {item}\\n"\n')
            else:
                f.write('printf "No software configured for this production\\n"\n')

        # Make the script executable
        os.chmod(script_path, 0o755)

        self.logger.debug(f"Generated interactive Bash script: {script_path}")

        return script_path

    def source_interactive_shell(self, script_path: str) -> None:
        """
        Sources the interactive shell script to enter a subshell with the production environment.
        This function will start a new interactive shell and only return when the user exits that shell.

        Args:
            script_path: Path to the interactive shell script
        """
        try:
            self.logger.debug(
                f"Starting interactive shell with script: {script_path}"
            )

            # Check the operating system at call time
            current_system = platform.system()
            if current_system == "Windows":
                # In PowerShell, use -File to execute the script in a new interactive shell
                # Using double-quoted path to handle spaces in path
                ps_path = "powershell.exe"
                # Using -NoExit to keep the shell open after executing the script
                # Using -ExecutionPolicy Bypass to allow script execution regardless of system policy
                # Using -NoLogo to suppress the PowerShell copyright banner
                cmd = f'{ps_path} -NoLogo -NoExit -ExecutionPolicy Bypass -File "{script_path}"'
                os.system(cmd)
            else:
                # In Bash, source the script in a new interactive shell
                os.system(f'bash --rcfile "{script_path}"')

            self.logger.debug("Interactive shell exited")
        except Exception as e:
            self.logger.error(f"Failed to source interactive shell script: {e}")
