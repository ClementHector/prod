"""
Tests unitaires pour la classe ConfigManager.
"""

import os
import tempfile

import pytest

from src.config_manager import ConfigManager


@pytest.fixture
def config_setup():
    """
    Fixture to set up test environment with temporary config files.

    Returns:
        Tuple of (config_manager, base_config_path, override_config_path, temp_dir)
    """
    # Create temporary config files
    temp_dir = tempfile.TemporaryDirectory()

    # Create base config
    base_config_path = os.path.join(temp_dir.name, "base.ini")
    with open(base_config_path, "w") as f:
        f.write(
            """
[section1]
key1 = value1
key2 = value2

[section2]
key1 = base_value
"""
        )

    # Create override config
    override_config_path = os.path.join(temp_dir.name, "override.ini")
    with open(override_config_path, "w") as f:
        f.write(
            """
[section1]
key2 = override_value

[section3]
key1 = new_value
"""
        )

    # Create config manager
    config_manager = ConfigManager()

    yield config_manager, base_config_path, override_config_path, temp_dir

    # Cleanup
    temp_dir.cleanup()


def test_load_config(config_setup):
    """Test loading a configuration file."""
    config_manager, base_config_path, _, _ = config_setup

    config_manager.load_config(base_config_path)

    # Check that the config was loaded
    assert config_manager.has_section("section1")
    assert config_manager.get_merged_config("section1", "key1") == "value1"
    assert config_manager.get_merged_config("section1", "key2") == "value2"


def test_merge_configs(config_setup):
    """Test merging multiple configuration files."""
    config_manager, base_config_path, override_config_path, _ = config_setup

    config_manager.merge_configs([base_config_path, override_config_path])

    # Check that the configs were merged
    assert config_manager.has_section("section1")
    assert config_manager.has_section("section2")
    assert config_manager.has_section("section3")

    # Check that the override value was applied
    assert config_manager.get_merged_config("section1", "key1") == "value1"
    assert config_manager.get_merged_config("section1", "key2") == "override_value"
    assert config_manager.get_merged_config("section3", "key1") == "new_value"


def test_load_override_config(config_setup):
    """Test loading an override configuration file."""
    config_manager, base_config_path, override_config_path, _ = config_setup

    config_manager.load_config(base_config_path)
    config_manager.load_override_config(override_config_path)

    # Check that the override was applied
    assert config_manager.get_merged_config("section1", "key1") == "value1"
    assert config_manager.get_merged_config("section1", "key2") == "override_value"
    assert config_manager.get_merged_config("section3", "key1") == "new_value"


def test_get_sections(config_setup):
    """Test getting all sections."""
    config_manager, base_config_path, override_config_path, _ = config_setup

    config_manager.merge_configs([base_config_path, override_config_path])

    # Check that all sections are returned
    sections = config_manager.get_sections()
    assert "section1" in sections
    assert "section2" in sections
    assert "section3" in sections


def test_get_section(config_setup):
    """Test getting all key-value pairs from a section."""
    config_manager, base_config_path, override_config_path, _ = config_setup

    config_manager.merge_configs([base_config_path, override_config_path])

    # Check that all key-value pairs are returned
    section = config_manager.get_section("section1")
    assert section["key1"] == "value1"
    assert section["key2"] == "override_value"
