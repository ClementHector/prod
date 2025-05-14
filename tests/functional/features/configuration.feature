Feature: Configuration management
  As a technical director
  I want to manage configurations with override capability
  So that I can have studio-wide defaults and production-specific overrides

  Background:
    Given a studio-wide software configuration file exists
    And a production-specific software configuration file exists

  Scenario: Loading and merging configuration files
    When I load both configuration files
    Then the merged configuration should contain all sections
    And production-specific values should override studio-wide values

  Scenario: Getting software version from merged configuration
    When I load both configuration files
    Then I should get the production-specific Maya version
    And I should get the production-specific Nuke version

  Scenario: Getting required packages for software
    When I load both configuration files
    Then Maya should have the specified required packages
    And Nuke should have the specified required packages
    
  Scenario: Temporary override of configuration values
    When I load both configuration files
    And I apply a temporary override to Maya version
    Then I should get the overridden Maya version 
    
  Scenario: Cross-platform path separators
    Given a prod-settings.ini file with mixed path separators
    When I initialize the production environment
    Then the configuration paths should be correctly split
    And the software configuration should be properly loaded
    And the available software should be correctly listed 