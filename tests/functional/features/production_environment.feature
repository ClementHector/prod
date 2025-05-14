Feature: Production environment management
  As a technical director
  I want to manage production environments
  So that I can provide isolated environments for different productions

  Background:
    Given a valid production name "dlt"
    And studio and production configuration files exist

  Scenario: Activating a production environment
    When I activate the production environment
    Then environment variables should be set from the pipeline configuration
    And the PROD environment variable should be set to the production name
    And an interactive shell script should be generated

  Scenario: Creating Rez aliases for software
    When I activate the production environment
    Then Rez aliases should be created for all configured software
    And each alias should include the correct packages

  Scenario: Getting software list
    When I activate the production environment
    Then I should get a list of all configured software with their versions

  Scenario: Executing software with additional packages
    Given the production environment is activated
    When I execute Maya with additional packages
    Then Maya should be launched with the additional packages
    
  Scenario: Interactive shell environment with exit command
    Given the production environment is activated
    When an interactive shell is created
    Then a custom prompt with the production name should be shown
    And the native exit command should be available to exit the environment 