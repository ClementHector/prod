"""
Production environment management for the Prod CLI tool.

This module provides functionality for managing production environments,
including software configuration, pipeline configuration, and environment
activation.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, cast

from src.config_manager import ConfigManager
from src.environment_manager import EnvironmentManager
from src.exceptions import ConfigError
from src.logger import get_logger
from src.rez_manager import RezManager


class SoftwareConfig:
    """
    Manages software configuration.

    This class is responsible for retrieving software-specific configuration
    details including versions and required packages.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the software configuration.

        Args:
            config_manager: Configuration manager
        """
        self.config_manager = config_manager
        self.logger = get_logger()

    def get_software_version(self, software_name: str) -> str:
        """
        Get the configured version for a software.

        Args:
            software_name: Name of the software

        Returns:
            Version of the software

        Raises:
            ConfigError: If software is not configured
        """
        self._validate_software_exists(software_name)

        try:
            return self.config_manager.get_merged_config(software_name, "version")
        except ConfigError:
            raise ConfigError(
                f"Version for software '{software_name}' is not configured"
            )

    def get_required_packages(self, software_name: str) -> List[str]:
        """
        Get the list of required packages for a software.

        Args:
            software_name: Name of the software

        Returns:
            List of required packages

        Raises:
            ConfigError: If software is not configured
        """
        self._validate_software_exists(software_name)

        try:
            packages_str = self.config_manager.get_merged_config(
                software_name, "packages", "[]"
            )
            return cast(List[str], ast.literal_eval(packages_str))
        except (SyntaxError, ValueError) as e:
            self.logger.warning(f"Error parsing packages for {software_name}: {e}")
            return []

    def get_configured_software(self) -> List[str]:
        """
        Get the list of all configured software.

        Returns:
            List of software names
        """
        excluded_sections = {"common", "environment"}
        return [
            section
            for section in self.config_manager.get_sections()
            if section not in excluded_sections
        ]

    def _validate_software_exists(self, software_name: str) -> None:
        """
        Validate that the software exists in the configuration.

        Args:
            software_name: Name of the software to validate

        Raises:
            ConfigError: If software is not configured
        """
        if not self.config_manager.has_section(software_name):
            raise ConfigError(f"Software '{software_name}' is not configured")


class PipelineConfig:
    """
    Manages pipeline configuration.

    This class is responsible for retrieving pipeline-specific configuration
    details including common packages and environment variables.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the pipeline configuration.

        Args:
            config_manager: Configuration manager
        """
        self.config_manager = config_manager
        self.logger = get_logger()

    def get_common_packages(self) -> List[str]:
        """
        Get common packages for all software.

        Returns:
            List of common packages
        """
        try:
            packages_str = self.config_manager.get_merged_config(
                "common", "packages", "[]"
            )
            return cast(List[str], ast.literal_eval(packages_str))
        except (SyntaxError, ValueError) as e:
            self.logger.warning(f"Error parsing common packages: {e}")
            return []

    def get_software_packages(self, software_name: str) -> List[str]:
        """
        Get software-specific packages.

        Args:
            software_name: Name of the software

        Returns:
            List of software-specific packages
        """
        try:
            if self.config_manager.has_section(software_name):
                packages_str = self.config_manager.get_merged_config(
                    software_name, "packages", "[]"
                )
                return cast(List[str], ast.literal_eval(packages_str))
            return []
        except (SyntaxError, ValueError) as e:
            self.logger.warning(f"Error parsing packages for {software_name}: {e}")
            return []

    def get_environment_variables(self) -> Dict[str, str]:
        """
        Get environment variables from the pipeline configuration.

        Returns:
            Dictionary of environment variables
        """
        if not self.config_manager.has_section("environment"):
            return {}

        return self.config_manager.get_section("environment")


class ProductionEnvironment:
    """
    Manages a production environment.
    """

    def __init__(self, prod_name: str, verbose: bool = False):
        """
        Initializes the production environment.

        Args:
            prod_name: Name of the production
            verbose: Whether to enable verbose mode
        """
        self.prod_name = prod_name
        self.verbose = verbose
        self.logger = get_logger()
        self.config_paths = self._load_config_paths()
        self.software_config = self._parse_software_config()
        self.pipeline_config = self._parse_pipeline_config()
        self.env_manager = EnvironmentManager()
        self.rez_manager = RezManager(verbose=verbose)

    @staticmethod
    def _get_settings_path() -> Path:
        """
        Gets the path to the settings file.

        Returns:
            Path to the settings file
        """
        return Path(__file__).parent.joinpath("../config/prod-settings.ini").resolve()

    def _expand_paths(self, paths: str) -> List[str]:
        """
        Expands environment variables in the given paths.

        Args:
            paths: Paths string to expand

        Returns:
            List of expanded paths
        """
        new_paths = []
        for p in paths.split(os.pathsep):
            p = os.path.expandvars(p)
            p = p.format(PROD_NAME=self.prod_name)
            new_paths.append(p)
        return new_paths

    def _load_config_paths(self) -> Dict[str, List[str]]:
        """
        Loads the configuration paths from environment variables.

        Returns:
            Dictionary of configuration paths

        Raises:
            ConfigError: If settings file or required sections/values are missing
        """
        settings_path = self._get_settings_path()

        if not settings_path.exists():
            raise ConfigError(f"Prod settings file not found: {settings_path}")

        settings = ConfigManager()
        settings.load_config(str(settings_path))

        if not settings.has_section("environment"):
            raise ConfigError("Missing 'environment' section in prod settings file")

        software_config_path = settings.get_merged_config(
            "environment", "SOFTWARE_CONFIG", ""
        )
        pipeline_config_path = settings.get_merged_config(
            "environment", "PIPELINE_CONFIG", ""
        )

        if not software_config_path or not pipeline_config_path:
            raise ConfigError(
                "Missing SOFTWARE_CONFIG or PIPELINE_CONFIG in prod settings"
            )

        software_paths = self._expand_paths(software_config_path)
        pipeline_paths = self._expand_paths(pipeline_config_path)
        return {"software": software_paths, "pipeline": pipeline_paths}

    def _parse_software_config(self) -> SoftwareConfig:
        """
        Parses the software configuration.

        Returns:
            SoftwareConfig instance
        """
        config_manager = ConfigManager()

        for config_path in self.config_paths["software"]:
            path = Path(config_path)
            if path.exists():
                self.logger.debug(f"Loading software config: {config_path}")
                config_manager.load_config(config_path)
            else:
                self.logger.warning(f"Software config not found: {config_path}")

        return SoftwareConfig(config_manager)

    def _parse_pipeline_config(self) -> PipelineConfig:
        """
        Parses the pipeline configuration.

        Returns:
            PipelineConfig instance
        """
        config_manager = ConfigManager()

        for config_path in self.config_paths["pipeline"]:
            path = Path(config_path)
            if path.exists():
                self.logger.debug(f"Loading pipeline config: {config_path}")
                config_manager.load_config(config_path)
            else:
                self.logger.warning(f"Pipeline config not found: {config_path}")

        return PipelineConfig(config_manager)

    def activate(self) -> None:
        """
        Activates the production environment.
        Sets environment variables directly and creates Rez aliases.
        Creates temporary shell scripts that will be used to enter a subshell where
        the 'exit' command will properly return to the original environment.
        """
        env_variables = self.pipeline_config.get_environment_variables()
        self.logger.debug("Setting environment variables from pipeline configuration")
        self.env_manager.set_environment_variables(env_variables)

        software_list = []
        for software in self.get_software_list():
            name = software.get("name", "")
            version = software.get("version", "")
            software_list.append(f"{name}:{version}")

        env_script = self.env_manager.generate_interactive_shell_script(
            self.prod_name, software_list
        )

        self.logger.debug(f"Environment script generated: {env_script}")
        self.env_manager.source_interactive_shell(env_script, self.verbose)
        self.logger.debug(f"Exited production environment '{self.prod_name}'")

    def get_base_packages(self, software_name: str) -> List[str]:
        """
        Gets the base packages for a software.

        Args:
            software_name: Name of the software

        Returns:
            List of base packages
        """
        packages = []
        packages.extend(self.pipeline_config.get_common_packages())
        packages.extend(self.pipeline_config.get_software_packages(software_name))
        packages.extend(self.software_config.get_required_packages(software_name))
        return packages

    def get_software_list(self) -> List[Dict[str, str]]:
        """
        Gets a list of configured software with their versions.

        Returns:
            List of dictionaries with software name and version
        """
        software_list = []

        for software in self.software_config.get_configured_software():
            try:
                version = self.software_config.get_software_version(software)
                software_list.append({"name": software, "version": version})
            except ConfigError:
                continue

        return software_list

    def _merge_packages(
        self, base_packages: List[str], override_packages: List[str]
    ) -> List[str]:
        """
        Merges two lists of packages, with override_packages taking precedence.

        If a package name (e.g., "goalem" from "goalem-1") appears in both lists,
        the version from override_packages will be used.

        Args:
            base_packages: The initial list of packages.
            override_packages: The list of packages to override or add.

        Returns:
            A new list of merged packages.
        """
        override_packages_names = tuple(
            [pkg.split("-")[0] for pkg in override_packages]
        )
        base_packages_without_overrides = [
            p for p in base_packages if not p.startswith(override_packages_names[0])
        ]
        return list(base_packages_without_overrides + override_packages)

    def execute_software(
        self,
        production_name: str,
        software_name: str,
        additional_packages: Optional[List[str]] = None,
        env_only: bool = False,
        background: bool = False,
    ) -> None:
        """
        Executes a software application.

        Args:
            production_name: Name of the production (unused in current logic, but kept for signature)
            software_name: Name of the software
            additional_packages: Additional packages to include, overriding base packages
            env_only: If True, only enter the environment without executing the software
            background: If True, run the software in the background

        Raises:
            ConfigError: If software is not configured
        """
        if additional_packages is None:
            additional_packages = []

        try:
            version = self.software_config.get_software_version(software_name)
            base_pkgs = self.get_base_packages(software_name)

            packages = self._merge_packages(base_pkgs, additional_packages)

            return_code, _, stderr = self.rez_manager.execute_with_rez(
                software_name, version, packages, software_name, env_only, background
            )

            if return_code != 0 and self.logger:
                self.logger.error(f"Failed to execute {software_name}: {stderr}")

        except ConfigError as e:
            self.logger.error(f"Failed to execute {software_name}: {e}")
            raise
