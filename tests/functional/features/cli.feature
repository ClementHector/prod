Feature: Command line interface
  As a user
  I want to interact with the Prod CLI tool through command line
  So that I can manage productions and launch software

  Scenario: Listing available productions
    Given several productions exist
    When I run the command "prod list"
    Then I should see a list of all available productions

  Scenario: Entering a production environment
    Given a valid production "dlt" exists
    When I run the command "prod enter dlt"
    Then I should see a confirmation message
    And I should see a list of available software for that production
    And the environment variables should be set for that production

  Scenario: Launching software
    Given I am in the "dlt" production environment
    When I run the command "maya"
    Then Maya should be launched with the correct settings
    
  Scenario: Launching software with additional packages
    Given I am in the "dlt" production environment
    When I run the command "maya --packages dev-package"
    Then Maya should be launched with the additional package "dev-package"
    
  Scenario: Entering a Rez environment without launching software
    Given I am in the "dlt" production environment
    When I run the command "maya --env-only"
    Then I should be in a Rez environment for Maya
    And the software should not be launched 