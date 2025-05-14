Feature: Environment variables management
  As a technical director
  I want to have environment variables automatically set when activating a production
  So that I can quickly access production-specific paths and settings

  Background:
    Given a valid production name "dlt"
    And studio and production configuration files exist

  Scenario: Environment variables are set when activating a production
    When I run the command "prod dlt"
    Then environment variables should be set from the pipeline configuration
    And the PROD environment variable should be set to the production name

  Scenario: Environment variables are removed when exiting the production environment
    Given the production environment is activated
    When I exit the environment with the "exit" command
    Then the production environment variables should no longer be set