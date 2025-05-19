"""
Rez package manager integration for the Prod CLI tool.

This module provides integration with the Rez package manager, allowing
for the execution of commands within Rez environments.
"""

import os
import platform
import subprocess
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from src.exceptions import RezError
from src.logger import get_logger

# Constants
WINDOWS_CREATE_NEW_PROCESS_GROUP = 0x00000200


class RezCommandBuilder:
    """
    Builder class for constructing Rez commands with consistent options.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the Rez command builder.

        Args:
            verbose: Whether to enable verbose mode in Rez commands
        """
        self.verbose = verbose

    def build_env_command(
        self, packages: List[str], command: Optional[str] = None
    ) -> List[str]:
        """
        Build a Rez environment command.

        Args:
            packages: Rez packages to include in the environment
            command: Command to execute in the environment (optional)

        Returns:
            List of command parts that can be executed with subprocess
        """
        rez_command = ["rez"]

        if self.verbose:
            rez_command.append("-v")

        rez_command.extend(["env"] + packages)

        if command:
            rez_command.extend(["--", command])

        return rez_command


class ProcessExecutor(ABC):
    """
    Abstract base class for executing processes in different environments.
    """

    @abstractmethod
    def execute(
        self, command: List[str], background: bool = False
    ) -> Tuple[int, str, str]:
        """
        Execute a command.

        Args:
            command: Command parts to execute
            background: Whether to run the command in the background

        Returns:
            Tuple of (return code, stdout, stderr)

        Raises:
            RezError: If execution fails
        """
        pass


class WindowsProcessExecutor(ProcessExecutor):
    """
    Process executor implementation for Windows systems.
    """

    def execute(
        self, command: List[str], background: bool = False
    ) -> Tuple[int, str, str]:
        """
        Execute a command on Windows.

        Args:
            command: Command parts to execute
            background: Whether to run the command in the background

        Returns:
            Tuple of (return code, stdout, stderr)

        Raises:
            RezError: If execution fails
        """
        try:
            if background:
                creationflags_value = getattr(
                    subprocess,
                    "CREATE_NEW_PROCESS_GROUP",
                    WINDOWS_CREATE_NEW_PROCESS_GROUP,
                )

                cmd_parts = ["start", "/b"] + [str(arg) for arg in command]
                cmd_str = " ".join(cmd_parts)

                subprocess.Popen(
                    cmd_str,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=creationflags_value,
                    shell=True,
                )
                return 0, "", ""
            else:
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,  # Don't raise exception on non-zero exit code
                )
                return result.returncode, result.stdout, result.stderr

        except subprocess.SubprocessError as e:
            raise RezError(f"Failed to execute command on Windows: {e}")


class UnixProcessExecutor(ProcessExecutor):
    """
    Process executor implementation for Unix-like systems.
    """

    def execute(
        self, command: List[str], background: bool = False
    ) -> Tuple[int, str, str]:
        """
        Execute a command on Unix-like systems.

        Args:
            command: Command parts to execute
            background: Whether to run the command in the background

        Returns:
            Tuple of (return code, stdout, stderr)

        Raises:
            RezError: If execution fails
        """
        try:
            if background:
                # For background processes on Unix, use process groups
                # to ensure they don't get terminated when the parent exits
                subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid if hasattr(os, "setsid") else None,
                    text=True,
                )
                return 0, "", ""
            else:
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,  # Don't raise exception on non-zero exit code
                )
                return result.returncode, result.stdout, result.stderr

        except subprocess.SubprocessError as e:
            raise RezError(f"Failed to execute command on Unix: {e}")


class RezManager:
    """
    Manages Rez package manager integration.

    This class provides a unified interface for executing commands within
    Rez environments across different platforms.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the Rez manager.

        Args:
            verbose: Whether to enable verbose mode

        Raises:
            RezError: If Rez is not installed or accessible
        """
        self.logger = get_logger()
        self.verbose = verbose
        self.system = platform.system()
        self.command_builder = RezCommandBuilder(verbose)

        # Select appropriate process executor based on platform
        if self.system == "Windows":
            self.process_executor = WindowsProcessExecutor()
        else:
            self.process_executor = UnixProcessExecutor()

        self._validate_rez_installation()

    def _validate_rez_installation(self) -> None:
        """
        Validate that Rez is installed and accessible.

        Raises:
            RezError: If Rez is not installed or not accessible
        """
        try:
            result = subprocess.run(
                ["rez", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )

            if result.returncode != 0:
                raise RezError(
                    f"Rez installation check failed: {result.stderr.strip()}"
                )

        except FileNotFoundError:
            raise RezError(
                "Rez is not installed or not in PATH. "
                "Please install Rez or add it to your PATH."
            )

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
        Execute a command within a Rez environment.

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
        # Create the complete package list with the main software package first
        package_list = [f"{software_name}-{software_version}"]
        package_list.extend(packages)

        # Build the Rez command
        rez_command = self.command_builder.build_env_command(
            packages=package_list,
            command=command if not env_only else None,
        )

        self.logger.info(f"Executing Rez command: {' '.join(rez_command)}")

        # Execute the command using the appropriate process executor
        try:
            return self.process_executor.execute(rez_command, background)
        except RezError as e:
            self.logger.error(f"Failed to execute command with Rez: {e}")
            raise
