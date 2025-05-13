"""
Rez package manager integration for the Prod CLI tool.
"""
import os
import platform
import subprocess
from typing import Dict, List, Optional, Tuple

from src.error_handler import RezError
from src.logger import Logger


class RezManager:
    """
    Manages Rez package manager integration, creating aliases for software.
    """
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initializes the Rez manager.
        
        Args:
            logger: Logger instance to use for logging
        """
        self.logger = logger
        self.system = platform.system()
        self._validate_rez_installation()
    
    def _validate_rez_installation(self) -> None:
        """
        Validates that Rez is installed and accessible.
        
        Raises:
            RezError: If Rez is not installed or not accessible
        """
        try:
            # Check if rez is in PATH
            subprocess.run(
                ["rez", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            raise RezError(
                "Rez is not installed or not in PATH. "
                "Please install Rez or add it to your PATH."
            )
    
    def create_alias(self, software_name: str, software_version: str, 
                    packages: List[str], alias_name: Optional[str] = None) -> str:
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
            
        # Generate the Rez command
        rez_command = self._generate_rez_command(
            software_name, software_version, packages
        )
        
        # Create the alias
        try:
            subprocess.run(
                ["rez-bind", "--alias", alias_name, "--command", rez_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            if self.logger:
                self.logger.info(
                    f"Created Rez alias '{alias_name}' for "
                    f"{software_name}-{software_version}"
                )
                
            return alias_name
            
        except subprocess.SubprocessError as e:
            if self.logger:
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
        # Start with the base package
        package_list = [f"{software_name}-{software_version}"]
        
        # Add additional packages
        package_list.extend(packages)
        
        # Format the command
        command = f"rez env {' '.join(package_list)} -- {software_name}"
        
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
                text=True
            )
            
            # Parse the output
            packages = {}
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
            if self.logger:
                self.logger.error(f"Failed to list Rez packages: {e}")
            raise RezError(f"Failed to list Rez packages: {e}")
    
    def execute_with_rez(self, software_name: str, software_version: str, 
                         packages: List[str], command: str, env_only: bool = False,
                         background: bool = False) -> Tuple[int, str, str]:
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
        # Start with the base package
        package_list = [f"{software_name}-{software_version}"]
        
        # Add additional packages
        package_list.extend(packages)
        
        # Build the command
        rez_command = ["rez", "env"] + package_list
        
        if env_only:
            rez_command += ["--shell"]
        else:
            rez_command += ["--", command]
        
        try:
            if background:
                # Run in background
                if self.system == "Windows":
                    # For Windows, use start command
                    subprocess.Popen(
                        ["start", "/b"] + rez_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True
                    )
                    return 0, "", ""
                else:
                    # For Unix-like systems, append "&"
                    subprocess.Popen(
                        rez_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setpgrp
                    )
                    return 0, "", ""
            else:
                # Run in foreground
                result = subprocess.run(
                    rez_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                return result.returncode, result.stdout, result.stderr
                
        except subprocess.SubprocessError as e:
            if self.logger:
                self.logger.error(f"Failed to execute command with Rez: {e}")
            raise RezError(f"Failed to execute command with Rez: {e}") 