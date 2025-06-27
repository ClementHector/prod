"""
Configuration management for the Prod CLI tool.

This module provides a robust configuration system that supports loading,
merging, and overriding configuration files.
"""

import configparser
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from src.exceptions import ConfigError
from src.logger import get_logger


class ConfigManager:
    """
    Manages the loading and merging of configuration files.

    This class provides functionality to load configuration files, merge multiple
    configurations with proper override behavior, and access configuration values
    with appropriate type conversion and error handling.
    """

    def __init__(self) -> None:
        """Initialize the configuration manager with empty configuration."""
        self.config_parser = configparser.ConfigParser()
        self.config_parser.optionxform = str  # Preserve case sensitivity
        self.override_config = configparser.ConfigParser()
        self.override_config.optionxform = str
        self.logger = get_logger()

    def load_config(self, config_path: Union[str, Path]) -> None:
        """
        Load a configuration file.

        Args:
            config_path: Path to the configuration file

        Raises:
            ConfigError: If the configuration file doesn't exist or can't be read
        """
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            self.config_parser.read(str(path))
        except configparser.Error as e:
            raise ConfigError(f"Error reading configuration file {config_path}: {e}")

    def merge_configs(self, configs: List[Union[str, Path]]) -> None:
        """
        Merge multiple configuration files.

        Configurations are processed from left to right,
        with later files overriding earlier ones.

        Args:
            configs: List of paths to configuration files
        """
        for config in configs:
            path = Path(config)
            if path.exists():
                try:
                    self.config_parser.read(str(path))
                except configparser.Error as e:
                    self.logger.warning(f"Error reading config file {config}: {e}")
            else:
                self.logger.warning(f"Config file not found: {config}")

    def set_override(self, section: str, key: str, value: str) -> None:
        """
        Set an override value for a configuration key.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if not self.override_config.has_section(section):
            self.override_config.add_section(section)

        self.override_config[section][key] = value

    def get_merged_config(
        self, section: str, key: str, default: Optional[str] = None
    ) -> str:
        """
        Get a configuration value considering overrides.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if key not found

        Returns:
            The configuration value

        Raises:
            ConfigError: If the key is not found and no default is provided
        """
        if self.override_config.has_option(section, key):
            return self.override_config[section][key]

        if self.config_parser.has_option(section, key):
            return self.config_parser[section][key]

        if default is not None:
            return default

        raise ConfigError(f"Configuration key not found: {section}.{key}")

    def get_section(self, section: str) -> Dict[str, str]:
        """
        Get all key-value pairs from a configuration section.

        Args:
            section: Configuration section

        Returns:
            Dictionary of key-value pairs
        """
        result: Dict[str, str] = {}

        if self.config_parser.has_section(section):
            result.update(dict(self.config_parser[section]))

        if self.override_config.has_section(section):
            result.update(dict(self.override_config[section]))

        return result

    def has_section(self, section: str) -> bool:
        """
        Check if a section exists in any configuration.

        Args:
            section: Configuration section

        Returns:
            True if the section exists, False otherwise
        """
        return self.config_parser.has_section(
            section
        ) or self.override_config.has_section(section)

    def get_sections(self) -> List[str]:
        """
        Get all sections from both configurations.

        Returns:
            List of section names
        """
        sections: Set[str] = set(self.config_parser.sections())
        sections.update(self.override_config.sections())
        return sorted(list(sections))

    def clear_overrides(self) -> None:
        """Clear all override configurations."""
        self.override_config = configparser.ConfigParser()
        self.override_config.optionxform = str
