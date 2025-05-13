"""
Command line interface for software commands in the Prod CLI tool.
"""
import argparse
import os
import sys
from typing import List, Optional

from src.error_handler import ConfigError, ErrorHandler, RezError
from src.logger import Logger
from src.production_environment import ProductionEnvironment


class SoftwareCLI:
    """
    Manages the command line interface for software commands.
    """
    def __init__(self, software_name: str):
        """
        Initializes the software CLI.
        
        Args:
            software_name: Name of the software
        """
        self.software_name = software_name
        self.parser = self._setup_argument_parser()
        self.logger = None
        self.error_handler = None
    
    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """
        Sets up the argument parser.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(description=f'{self.software_name} launcher with Prod')
        
        parser.add_argument('--packages', nargs='+', help='Additional packages to include')
        parser.add_argument('--env-only', action='store_true', help='Enter environment only without launching')
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Runs the software CLI with the given arguments.
        
        Args:
            args: Command line arguments, if None, sys.argv[1:] is used
            
        Returns:
            Exit code
        """
        if args is None:
            args = sys.argv[1:]
            
        # Parse arguments
        parsed_args = self.parser.parse_args(args)
        
        # Get the production name from environment
        prod_name = os.environ.get('PROD')
        
        if not prod_name:
            print("Error: No production environment is active. Please enter a production first with 'prod enter <production>'.")
            return 1
            
        # Initialize logger
        log_level = 'DEBUG' if parsed_args.verbose else 'INFO'
        self.logger = Logger(log_level)
        
        # Initialize error handler
        self.error_handler = ErrorHandler(self.logger)
        
        # Execute the software
        try:
            env = ProductionEnvironment(prod_name, self.logger)
            
            additional_packages = parsed_args.packages or []
            env_only = parsed_args.env_only
            
            env.execute_software(self.software_name, additional_packages, env_only, False)
            
            return 0
            
        except (ConfigError, RezError, Exception) as e:
            self.error_handler.handle_error(e)
            return 1


def create_software_entry_point(software_name: str) -> callable:
    """
    Creates an entry point function for a software.
    
    Args:
        software_name: Name of the software
        
    Returns:
        Entry point function
    """
    def main() -> int:
        """
        Main entry point for the software CLI.
        
        Returns:
            Exit code
        """
        cli = SoftwareCLI(software_name)
        return cli.run()
        
    return main
    

# Create entry points for common software
# These will be used in setup.py to create console scripts
maya_main = create_software_entry_point('maya')
nuke_main = create_software_entry_point('nuke')
houdini_main = create_software_entry_point('houdini')


if __name__ == '__main__':
    # If directly executed, extract the software name from the script name
    script_name = os.path.basename(sys.argv[0])
    software_name = os.path.splitext(script_name)[0]
    
    # Create and run the CLI
    cli = SoftwareCLI(software_name)
    sys.exit(cli.run()) 