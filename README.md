# Prod

A Python-based CLI tool designed to streamline and manage production environments for visual effects and animation studios. Cross-platform support for Windows, Linux, and macOS.

## Objectives

- Simplify production environment configuration
- Separate packages defined by Technical Directors (TDs) from those defined by Supervisors
- Optimize plugin lists to include only those actually used in production
- Enable package overrides for artists to test development versions
- Implement beta mechanisms for production deployments
- Create production aliases
- Cross-platform support (Windows, Linux, macOS)
- Do not use third-party libraries

## Features

### Command Line Interface

```bash
# List available productions
prod list

* dlt
* prod1
...

# Enter in a production that will create the aliases based on the configuration files
prod dlt

# Launch maya
maya
```

### Environment Configuration

The tool uses environment variables to locate configuration files. Multiple paths can be specified using the separator:

```bash
# Software and plugins configuration path
SOFTWARE_CONFIG=/path/to/studio-software.ini:/path/to/prod-software.ini

# Pipeline packages configuration path
PIPELINE_CONFIG=/path/to/studio-pipeline.ini:/path/to/prod-pipeline.ini
```

When multiple configuration files are specified, they are processed in order from left to right. Each subsequent file overrides the settings from the previous files. For example, in the path `/path/to/studio-software.ini:/path/to/prod-software.ini`, any settings defined in `prod-software.ini` will override the corresponding settings in `studio-software.ini`. This allows for production-specific configurations to take precedence over studio-wide defaults.

### Configuration Files

All configuration files use the INI format for consistency and better parsing capabilities.

#### Software Configuration (software.ini)
Managed by Supervisors and Technical Directors, defines software versions and their required plugins:

```ini
[maya]
version=2023.3.2
packages = ["mtoa-2.3", "golaem-4"]

[nuke]
version = 12.3
packages = ["ofxSuperResolution", "neatVideo"]

[nuke-13]
version = 13.2
packages = ["ofxSuperResolution", "neatVideo"]
```

#### Pipeline Configuration (pipeline.ini)
Managed by Technical Directors, defines packages used for different software:

```ini
[common]
packages = ["vfxCore-2.5"]

[maya]
packages = ["vfxMayaTools-2.3"]

[nuke]
packages = ["vfxNukeTools-2.1"]

[environment]
PROD=dlt
PROD_ROOT=/s/prods/dlt
PROD_TYPE=vfx
```

### Production Management

The `prod` command manages production environments by:
1. Reading the production configuration file to locate production paths
2. Setting up environment variables with the correct configuration paths
3. Creating Rez aliases based on the software and package configurations

Example workflow:
```bash
# Enter the 'dlt' production
prod dlt

# This will create Rez aliases based on the configuration
# For example, for Maya it will create an alias equivalent to:
rez env maya-2023.3.2 mtoa-2.3 golaem-4 vfxMayaTools-2.3 -- maya
```

### Command Line Options

```bash
# Run Maya with specific package overrides
maya --packages golaem-6.3

# Get help
maya --help

# Available options:
--packages    Add or override packages
--env-only    Enter in rez environment without opening the DCC
--verbose     Set verbosity (default: No verbosity)
```

## Requirements

- Python 3.9+
- Rez package manager (version 2.0+)
- Operating System: Windows, Linux, or macOS

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/prod.git
   cd prod
   ```

2. Configure the production paths in the tool's configuration file:
   ```bash
   # Copy the example configuration
   cp config/prod-settings.ini.example config/prod-settings.ini
   # Edit the configuration with your studio paths
   ```

3. Install the package:
   ```bash
   # Install in development mode
   pip install -e .

   # Or install normally
   pip install .
   ```

## Usage

1. Update your config/prod-settings.ini to point to your configuration files:
   ```ini
   [environment]
   SOFTWARE_CONFIG=/path/to/studio/software.ini:/path/to/prods/{PROD_NAME}/config/software.ini
   PIPELINE_CONFIG=/path/to/studio/pipeline.ini:/path/to/prods/{PROD_NAME}/config/pipeline.ini
   ```

2. Create production configurations:
   ```bash
   mkdir -p config/prods/your_production/config
   # Create software.ini and pipeline.ini in this directory
   ```

3. Use the `prod` command to enter a production environment:
   ```bash
   # List available productions
   prod list

   # Enter a production
   prod your_production
   ```

4. Use the created Rez aliases to launch software with the correct configuration:
   ```bash
   maya
   nuke
   houdini
   ```

## Project Structure

```
/
├── config/                      # Configuration files
│   ├── error_messages.json      # Custom error messages
│   ├── prod-settings.ini        # Tool settings (paths to configs)
│   ├── prod-settings.ini.example # Example settings file
│   ├── studio/                  # Studio-wide configuration
│   │   ├── pipeline.ini         # Studio Pipeline configuration
│   │   └── software.ini         # Studio Software configuration
│   │
│   └── prods/                   # Productions configuration
│       ├── dlt/                 # Example production
│       │   └── config/          # Production configuration
│       │       ├── pipeline.ini # Production Pipeline configuration
│       │       └── software.ini # Production Software configuration
│       └── your_production/     # Your production
│           └── ...
│
├── src/                         # Source code
│   ├── __init__.py              # Package initialization
│   ├── cli.py                   # Command line interface
│   ├── config_manager.py        # Configuration management
│   ├── environment_manager.py   # Environment variables management
│   ├── error_handler.py         # Error handling
│   ├── logger.py                # Logging system
│   ├── production_environment.py # Production environment management
│   ├── rez_manager.py           # Rez integration
│   └── software_cli.py          # Software-specific CLI
│
├── setup.py                     # Package setup script
└── README.md                    # This file
```

## Advanced Usage

### Package Management

```bash
# Enter production
prod dlt

# Override multiple packages for a software
maya --packages golaem-6.3 vfxMayaTools-2.4

# Use a specific package version for development
maya --packages vfxMayaTools-dev
```

### Development Workflow

```bash
# Enter production
prod dlt

# Launch Maya with a development package
maya --packages vfxMayaTools-dev

# Enter in development environment of a package
maya --packages vfxMayaTools-dev --env-only
```

## Extending the Tool

To add support for a new software:

1. Add the software to your configuration files.
2. Add an entry point in setup.py:
   ```python
   entry_points={
       'console_scripts': [
           'new_software=src.software_cli:create_software_entry_point("new_software")',
       ],
   }
   ```
3. Reinstall the package:
   ```bash
   pip install -e .
   ```

## Contributing

This tool is maintained by Technical Directors and Supervisors. Please contact the development team for any issues or feature requests.

## Code Quality

This project uses several tools to ensure code quality and security:

- **flake8**: For code style and syntax checking
- **black**: For automatic code formatting
- **isort**: For import sorting
- **mypy**: For static type checking
- **bandit**: For security vulnerability scanning
- **pytest**: For unit and functional testing with BDD

To run these tools locally:

```bash
# Code style and formatting
black src tests
isort src tests
flake8 src tests --config=.flake8

# Type checking
mypy src

# Security scanning
bandit -r src -ll

# Tests
pytest tests/unittest -v  # Unit tests
pytest tests/functional -v  # BDD tests
```

## License

[Add your license information here]