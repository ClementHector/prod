"""
Configuration management for the Prod CLI tool.
"""

import configparser
from pathlib import Path
from typing import Dict, List, Optional


class ConfigManager:
    """
    Manages the loading and merging of configuration files.
    Supports configuration override and hierarchical configuration.
    """

    def __init__(self):
        self.config_parser = configparser.ConfigParser()
        self.override_config = configparser.ConfigParser()

    def load_config(self, config_path: str) -> None:
        """
        Loads a configuration file.

        Args:
            config_path: Path to the configuration file
        """
        path = Path(config_path)
        if path.exists():
            self.config_parser.read(config_path)
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

    def merge_configs(self, configs: List[str]) -> None:
        """
        Merges multiple configuration files.
        Configurations are processed from left to right,
        with later files overriding earlier ones.

        Args:
            configs: List of paths to configuration files
        """
        for config in configs:
            path = Path(config)
            if path.exists():
                self.config_parser.read(config)
            else:
                print(f"Warning: Config file not found: {config}")

    def get_merged_config(
        self, section: str, key: str, default: Optional[str] = None
    ) -> str:
        """
        Gets a configuration value considering overrides.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if key not found

        Returns:
            The configuration value
        """
        if self.override_config.has_option(section, key):
            return self.override_config[section][key]

        if self.config_parser.has_option(section, key):
            return self.config_parser[section][key]

        if default is not None:
            return default

        raise KeyError(f"Configuration key not found: {section}.{key}")

    def get_section(self, section: str) -> Dict[str, str]:
        """
        Gets all key-value pairs from a configuration section.

        Args:
            section: Configuration section

        Returns:
            Dictionary of key-value pairs
        """
        result = {}

        if self.config_parser.has_section(section):
            result.update(dict(self.config_parser[section]))

        if self.override_config.has_section(section):
            result.update(dict(self.override_config[section]))

        return result

    def has_section(self, section: str) -> bool:
        """
        Checks if a section exists in the configuration.

        Args:
            section: Configuration section

        Returns:
            True if the section exists
        """
        return self.config_parser.has_section(
            section
        ) or self.override_config.has_section(section)

    def get_sections(self) -> List[str]:
        """
        Gets all sections from the configuration.

        Returns:
            List of section names
        """
        sections = set(self.config_parser.sections())
        sections.update(self.override_config.sections())
        return list(sections)
