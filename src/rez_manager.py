"""
Rez package manager integration for the Prod CLI tool.
"""

import os
import platform
import subprocess
from typing import Dict, List, Optional, Tuple

from src.error_handler import RezError
from src.logger import get_logger

WINDOWS_CREATE_NEW_PROCESS_GROUP = 0x00000200


class RezManager:
    """
    Manages Rez package manager integration, creating aliases for software.
    """

    def __init__(self):
        """
        Initializes the Rez manager.

        Args:
            logger: Logger instance to use for logging
        """
        self.logger = get_logger()
        self.system = platform.system()
        self._validate_rez_installation()

    def _validate_rez_installation(self) -> None:
        """
        Validates that Rez is installed and accessible.

        Raises:
            RezError: If Rez is not installed or not accessible
        """
        try:
            subprocess.run(
                ["rez", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            raise RezError(
                "Rez is not installed or not in PATH. "
                "Please install Rez or add it to your PATH."
            )

    def create_alias(
        self,
        software_name: str,
        software_version: str,
        packages: List[str],
        alias_name: Optional[str] = None,
    ) -> str:
        """
        Creates a Rez alias for a software.

        Args:
            software_name: Name of the software
            software_version: Version of the software
            packages: Additional packages to include
            alias_name: Name for the alias, defaults to software_name

        Returns:
            The created alias name

        Raises:
            RezError: If alias creation fails
        """
        if alias_name is None:
            alias_name = software_name

        rez_command = self._generate_rez_command(
            software_name, software_version, packages
        )

        try:
            subprocess.run(
                ["rez-bind", "--alias", alias_name, "--command", rez_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            self.logger.info(
                f"Created Rez alias '{alias_name}' for "
                f"{software_name}-{software_version}"
            )

            return alias_name
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to create Rez alias: {e}")
            raise RezError(f"Failed to create Rez alias: {e}")

    def _generate_rez_command(
        self, software_name: str, software_version: str, packages: List[str]
    ) -> str:
        """
        Generates a Rez command for a software with packages.

        Args:
            software_name: Name of the software
            software_version: Version of the software
            packages: Additional packages to include

        Returns:
            Rez command string
        """
        package_list = [f"{software_name}-{software_version}"]
        package_list.extend(packages)

        # Include the appropriate shell based on the platform
        # Get current system - don't rely on stored value which might be from initialization time
        current_system = platform.system()
        shell_prefix = ""
        if current_system == "Windows":
            shell_prefix = "cmd /c "
        else:
            shell_prefix = "bash -c "

        command = f"{shell_prefix}rez env {' '.join(package_list)} -- {software_name}"
        return command

    def list_available_packages(self) -> Dict[str, List[str]]:
        """
        Lists all available Rez packages.

        Returns:
            Dictionary of package families and their versions
        """
        try:
            result = subprocess.run(
                ["rez-search", "--format", "{name} {version}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )

            packages: Dict[str, List[str]] = {}
            for line in result.stdout.splitlines():
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]

                        if name not in packages:
                            packages[name] = []

                        packages[name].append(version)

            return packages

        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to list Rez packages: {e}")
            raise RezError(f"Failed to list Rez packages: {e}")

    def execute_with_rez(
        self,
        software_name: str,
        software_version: str,
        packages: List[str],
        command: str,
        env_only: bool = False,
        background: bool = False,
    ) -> Tuple[int, str, str]:
        """
        Executes a command with Rez environment.

        Args:
            software_name: Name of the software
            software_version: Version of the software
            packages: Additional packages to include
            command: Command to execute
            env_only: If True, only enter the environment without executing the command
            background: If True, run the command in the background

        Returns:
            Tuple of (return code, stdout, stderr)

        Raises:
            RezError: If execution fails
        """
        package_list = [f"{software_name}-{software_version}"]
        package_list.extend(packages)

        rez_command = ["rez", "env"] + package_list

        if env_only:
            rez_command += ["--shell"]
        else:
            rez_command += ["--", command]

        try:
            if background:
                if self.system == "Windows":
                    creationflags_value = 0
                    if platform.system() == "Windows":
                        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
                            creationflags_value = getattr(
                                subprocess, "CREATE_NEW_PROCESS_GROUP"
                            )
                        else:
                            creationflags_value = WINDOWS_CREATE_NEW_PROCESS_GROUP

                    cmd_parts = ["start", "/b"] + [str(arg) for arg in rez_command]
                    cmd_str = " ".join(cmd_parts)

                    subprocess.Popen(
                        cmd_str,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=creationflags_value,
                        shell=False,
                    )
                    return 0, "", ""
                else:
                    subprocess.Popen(
                        rez_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
                    )
                    return 0, "", ""
            else:
                result = subprocess.run(
                    rez_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                return result.returncode, result.stdout, result.stderr

        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute command with Rez: {e}")
            raise RezError(f"Failed to execute command with Rez: {e}")

    def launch_software(
        self, software_name: str, args: List[str] = None
    ) -> subprocess.Popen:
        """
        Launch software using Rez.

        Args:
            software_name: Name of the software to launch
            args: Additional command line arguments for the software

        Returns:
            Popen process object

        Raises:
            RezError: If software launch fails
        """
        if args is None:
            args = []

        try:
            # Construct command to run the software
            cmd = [software_name] + args

            # Launch the software
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.logger.info(f"Launched {software_name} with args: {args}")
            return process

        except subprocess.SubprocessError as e:
            error_msg = f"Failed to launch {software_name}: {e}"
            self.logger.error(error_msg)
            raise RezError(error_msg)
