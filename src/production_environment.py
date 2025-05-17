"""
Production environment management for the Prod CLI tool.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, cast

from src.config_manager import ConfigManager
from src.environment_manager import EnvironmentManager
from src.logger import get_logger
from src.path_processor import PathProcessor
from src.rez_manager import RezManager


class SoftwareConfig:
    """
    Manages software configuration.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initializes the software configuration.

        Args:
            config_manager: Configuration manager
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = get_logger()

    def get_software_version(self, software_name: str) -> str:
        """
        Gets the configured version for a software.

        Args:
            software_name: Name of the software

        Returns:
            Version of the software

        Raises:
            ConfigError: If software is not configured
        """
        if not self.config_manager.has_section(software_name):
            raise ConfigError(f"Software '{software_name}' is not configured")

        try:
            return self.config_manager.get_merged_config(software_name, "version")
        except KeyError:
            raise ConfigError(
                f"Version for software '{software_name}' is not configured"
            )

    def get_required_packages(self, software_name: str) -> List[str]:
        """
        Gets the list of required packages for a software.

        Args:
            software_name: Name of the software

        Returns:
            List of required packages

        Raises:
            ConfigError: If software is not configured
        """
        if not self.config_manager.has_section(software_name):
            raise ConfigError(f"Software '{software_name}' is not configured")

        try:
            packages_str = self.config_manager.get_merged_config(
                software_name, "packages", "[]"
            )
            return cast(List[str], ast.literal_eval(packages_str))
        except (KeyError, SyntaxError, ValueError) as e:
            self.logger.warning(f"Error parsing packages for {software_name}: {e}")
            return []

    def get_configured_software(self) -> List[str]:
        """
        Gets the list of all configured software.

        Returns:
            List of software names
        """
        excluded_sections = ["common", "environment"]
        return [
            section
            for section in self.config_manager.get_sections()
            if section not in excluded_sections
        ]


class PipelineConfig:
    """
    Manages pipeline configuration.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initializes the pipeline configuration.

        Args:
            config_manager: Configuration manager
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = get_logger()

    def get_common_packages(self) -> List[str]:
        """
        Gets common packages for all software.

        Returns:
            List of common packages
        """
        try:
            packages_str = self.config_manager.get_merged_config(
                "common", "packages", "[]"
            )
            return cast(List[str], ast.literal_eval(packages_str))
        except (KeyError, SyntaxError, ValueError) as e:
            self.logger.warning(f"Error parsing common packages: {e}")
            return []

    def get_software_packages(self, software_name: str) -> List[str]:
        """
        Gets software-specific packages.

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
        except (KeyError, SyntaxError, ValueError) as e:
            self.logger.warning(f"Error parsing packages for {software_name}: {e}")
            return []

    def get_environment_variables(self) -> Dict[str, str]:
        """
        Gets environment variables from the pipeline configuration.

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

    def __init__(self, prod_name: str):
        """
        Initializes the production environment.

        Args:
            prod_name: Name of the production
            logger: Logger instance
        """
        self.prod_name = prod_name
        self.logger = get_logger()
        self.config_paths = self._load_config_paths()
        self.software_config = self._parse_software_config()
        self.pipeline_config = self._parse_pipeline_config()
        self.env_manager = EnvironmentManager()
        self.rez_manager = RezManager()

    @staticmethod
    def _get_settings_path() -> Path:
        """
        Gets the path to the settings file.

        Returns:
            Path to the settings file
        """
        return Path(__file__).parent.joinpath("../config/prod-settings.ini").resolve()

    def _process_config_path(self, config_path: str) -> List[str]:
        """
        Process a configuration path string into a list of individual paths.
        Handles both Windows (;) and Unix (:) path separators.

        Args:
            config_path: Raw configuration path string

        Returns:
            List of processed paths
        """
        if not config_path:
            return []

        config_path = config_path.replace("{PROD_NAME}", self.prod_name)
        paths = []

        if ";" in config_path:
            # Windows-style path separator
            parts = config_path.split(";")
            for part in parts:
                if not part:
                    continue

                # Handle possible Unix-style subdirectories
                if ":" in part:
                    # Process Unix-style paths within Windows-style separators
                    if part.startswith("/"):
                        # Pure Unix path
                        unix_parts = part.split(":")
                        paths.extend([p for p in unix_parts if p])
                    else:
                        # Might be Windows drive letter
                        path_processor = PathProcessor(part)
                        paths.extend(path_processor.split_paths())
                else:
                    paths.append(part)
        elif ":" in config_path:
            # Unix-style path separator or Windows drive letters
            if config_path.startswith("/"):
                # Pure Unix path, direct split is fine
                unix_parts = config_path.split(":")
                paths.extend([p for p in unix_parts if p])
            else:
                # Might contain Windows drive letters
                path_processor = PathProcessor(config_path)
                paths = path_processor.split_paths()
        else:
            # Single path with no separators
            paths = [config_path]

        return [path for path in paths if path]

    def _load_config_paths(self) -> Dict[str, List[str]]:
        """
        Loads the configuration paths from environment variables.

        Returns:
            Dictionary of configuration paths
        """
        settings_path = self._get_settings_path()

        if not settings_path.exists():
            raise ConfigError(f"Prod settings file not found: {settings_path}")

        settings = ConfigManager()
        settings.load_config(settings_path)

        if not settings.has_section("environment"):
            raise ConfigError("Missing 'environment' section in prod settings file")

        software_config_path = settings.get_merged_config(
            "environment", "SOFTWARE_CONFIG", ""
        )
        pipeline_config_path = settings.get_merged_config(
            "environment", "PIPELINE_CONFIG", ""
        )

        software_paths = self._process_config_path(software_config_path)
        pipeline_paths = self._process_config_path(pipeline_config_path)

        self.logger.debug(f"Software config paths: {software_paths}")
        self.logger.debug(f"Pipeline config paths: {pipeline_paths}")

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

        software_list = []
        for software in self.get_software_list():
            name = software.get("name", "")
            version = software.get("version", "")
            software_list.append(f"{name}:{version}")

        env_script = self.env_manager.generate_interactive_shell_script(
            self.prod_name, software_list
        )

        self.logger.debug(f"Environment script generated: {env_script}")

        self.env_manager.source_interactive_shell(env_script)

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

    def execute_software(
        self,
        software_name: str,
        additional_packages: Optional[List[str]] = None,
        env_only: bool = False,
        background: bool = False,
    ) -> None:
        """
        Executes a software application.

        Args:
            software_name: Name of the software
            additional_packages: Additional packages to include
            env_only: If True, only enter the environment without executing the software
            background: If True, run the software in the background

        Raises:
            ConfigError: If software is not configured
        """
        if additional_packages is None:
            additional_packages = []

        try:
            version = self.software_config.get_software_version(software_name)
            packages = self.get_base_packages(software_name)
            packages.extend(additional_packages)

            return_code, _, stderr = self.rez_manager.execute_with_rez(
                software_name, version, packages, software_name, env_only, background
            )

            if return_code != 0 and self.logger:
                self.logger.error(f"Failed to execute {software_name}: {stderr}")

        except ConfigError as e:
            self.logger.error(f"Failed to execute {software_name}: {e}")
            raise
