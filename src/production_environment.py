"""
Production environment management for the Prod CLI tool.
"""
import ast
import json
import os
from typing import Dict, List, Optional

from src.config_manager import ConfigManager
from src.environment_manager import EnvironmentManager
from src.error_handler import ConfigError
from src.logger import Logger
from src.rez_manager import RezManager


class SoftwareConfig:
    """
    Manages software configuration.
    """
    def __init__(self, config_manager: ConfigManager, logger: Optional[Logger] = None):
        """
        Initializes the software configuration.
        
        Args:
            config_manager: Configuration manager
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = logger
    
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
            raise ConfigError(f"Version for software '{software_name}' is not configured")
    
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
            packages_str = self.config_manager.get_merged_config(software_name, "packages", "[]")
            return ast.literal_eval(packages_str)
        except (KeyError, SyntaxError, ValueError) as e:
            if self.logger:
                self.logger.warning(f"Error parsing packages for {software_name}: {e}")
            return []
    
    def get_configured_software(self) -> List[str]:
        """
        Gets the list of all configured software.
        
        Returns:
            List of software names
        """
        # Filter sections that correspond to software (excluding 'common', 'environment', etc.)
        excluded_sections = ["common", "environment"]
        return [section for section in self.config_manager.get_sections() 
                if section not in excluded_sections]


class PipelineConfig:
    """
    Manages pipeline configuration.
    """
    def __init__(self, config_manager: ConfigManager, logger: Optional[Logger] = None):
        """
        Initializes the pipeline configuration.
        
        Args:
            config_manager: Configuration manager
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = logger
    
    def get_common_packages(self) -> List[str]:
        """
        Gets common packages for all software.
        
        Returns:
            List of common packages
        """
        try:
            packages_str = self.config_manager.get_merged_config("common", "packages", "[]")
            return ast.literal_eval(packages_str)
        except (KeyError, SyntaxError, ValueError) as e:
            if self.logger:
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
                packages_str = self.config_manager.get_merged_config(software_name, "packages", "[]")
                return ast.literal_eval(packages_str)
            return []
        except (KeyError, SyntaxError, ValueError) as e:
            if self.logger:
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
    def __init__(self, prod_name: str, logger: Optional[Logger] = None):
        """
        Initializes the production environment.
        
        Args:
            prod_name: Name of the production
            logger: Logger instance
        """
        self.prod_name = prod_name
        self.logger = logger
        self.config_paths = self._load_config_paths()
        self.software_config = self._parse_software_config()
        self.pipeline_config = self._parse_pipeline_config()
        self.env_manager = EnvironmentManager(logger)
        self.rez_manager = RezManager(logger)
    
    def _load_config_paths(self) -> Dict[str, List[str]]:
        """
        Loads the configuration paths from environment variables.
        
        Returns:
            Dictionary of configuration paths
        """
        # Load from prod-settings.ini
        settings_path = os.path.join(os.path.dirname(__file__), '../config/prod-settings.ini')
        
        if not os.path.exists(settings_path):
            raise ConfigError(f"Prod settings file not found: {settings_path}")
            
        settings = ConfigManager()
        settings.load_config(settings_path)
        
        # Get the configuration paths
        if not settings.has_section("environment"):
            raise ConfigError(f"Missing 'environment' section in prod settings file")
            
        # Replace {PROD_NAME} with actual production name
        software_config_path = settings.get_merged_config("environment", "SOFTWARE_CONFIG", "")
        pipeline_config_path = settings.get_merged_config("environment", "PIPELINE_CONFIG", "")
        
        software_config_path = software_config_path.replace("{PROD_NAME}", self.prod_name)
        pipeline_config_path = pipeline_config_path.replace("{PROD_NAME}", self.prod_name)
        
        # Split paths by separator (: or ; depending on OS)
        separator = ";" if os.name == "nt" else ":"
        software_config_paths = software_config_path.split(separator) if software_config_path else []
        pipeline_config_paths = pipeline_config_path.split(separator) if pipeline_config_path else []
        
        return {
            "software": software_config_paths,
            "pipeline": pipeline_config_paths
        }
    
    def _parse_software_config(self) -> SoftwareConfig:
        """
        Parses the software configuration.
        
        Returns:
            SoftwareConfig instance
        """
        config_manager = ConfigManager()
        
        for config_path in self.config_paths["software"]:
            if os.path.exists(config_path):
                if self.logger:
                    self.logger.debug(f"Loading software config: {config_path}")
                config_manager.load_config(config_path)
            else:
                if self.logger:
                    self.logger.warning(f"Software config not found: {config_path}")
        
        return SoftwareConfig(config_manager, self.logger)
    
    def _parse_pipeline_config(self) -> PipelineConfig:
        """
        Parses the pipeline configuration.
        
        Returns:
            PipelineConfig instance
        """
        config_manager = ConfigManager()
        
        for config_path in self.config_paths["pipeline"]:
            if os.path.exists(config_path):
                if self.logger:
                    self.logger.debug(f"Loading pipeline config: {config_path}")
                config_manager.load_config(config_path)
            else:
                if self.logger:
                    self.logger.warning(f"Pipeline config not found: {config_path}")
        
        return PipelineConfig(config_manager, self.logger)
    
    def activate(self) -> None:
        """
        Activates the production environment.
        """
        self._set_environment_variables()
        self._create_rez_aliases()
    
    def _set_environment_variables(self) -> None:
        """
        Sets up the environment variables.
        """
        # Set up environment variables from pipeline config
        env_vars = self.pipeline_config.get_environment_variables()
        
        # Add PROD environment variable if not explicitly set
        if "PROD" not in env_vars:
            env_vars["PROD"] = self.prod_name
        
        # Set environment variables
        self.env_manager.set_environment_variables(env_vars)
        
        if self.logger:
            self.logger.info(f"Set environment variables for production '{self.prod_name}'")
    
    def _create_rez_aliases(self) -> None:
        """
        Creates Rez aliases for configured software.
        """
        software_list = self.software_config.get_configured_software()
        
        for software in software_list:
            try:
                # Get software version
                version = self.software_config.get_software_version(software)
                
                # Get packages
                packages = []
                
                # Add common packages
                packages.extend(self.pipeline_config.get_common_packages())
                
                # Add software-specific pipeline packages
                packages.extend(self.pipeline_config.get_software_packages(software))
                
                # Add software-specific required packages
                packages.extend(self.software_config.get_required_packages(software))
                
                # Create alias
                self.rez_manager.create_alias(software, version, packages)
                
            except (ConfigError, Exception) as e:
                if self.logger:
                    self.logger.error(f"Failed to create alias for {software}: {e}")
    
    def get_base_packages(self, software_name: str) -> List[str]:
        """
        Gets the base packages for a software.
        
        Args:
            software_name: Name of the software
            
        Returns:
            List of base packages
        """
        packages = []
        
        # Add common packages
        packages.extend(self.pipeline_config.get_common_packages())
        
        # Add software-specific pipeline packages
        packages.extend(self.pipeline_config.get_software_packages(software_name))
        
        # Add software-specific required packages
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
                software_list.append({
                    "name": software,
                    "version": version
                })
            except ConfigError:
                continue
                
        return software_list
    
    def execute_software(self, software_name: str, additional_packages: List[str] = None,
                        env_only: bool = False, background: bool = False) -> None:
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
            # Get software version
            version = self.software_config.get_software_version(software_name)
            
            # Get base packages
            packages = self.get_base_packages(software_name)
            
            # Add additional packages
            packages.extend(additional_packages)
            
            # Execute with Rez
            return_code, stdout, stderr = self.rez_manager.execute_with_rez(
                software_name, version, packages, software_name, env_only, background
            )
            
            if return_code != 0:
                if self.logger:
                    self.logger.error(f"Failed to execute {software_name}: {stderr}")
                    
        except (ConfigError, Exception) as e:
            if self.logger:
                self.logger.error(f"Failed to execute {software_name}: {e}")
            raise 