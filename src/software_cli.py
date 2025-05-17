"""
Command line interface for software commands in the Prod CLI tool.
"""

import argparse
import os
import sys
from typing import Callable, List, Optional

from src.logger import Logger
from src.production_environment import ProductionEnvironment
from src.errors import ConfigError, RezError


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
        self.logger: Optional[Logger] = None

    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """
        Sets up the argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description=f"{self.software_name} launcher with Prod"
        )

        parser.add_argument(
            "--packages", nargs="+", help="Additional packages to include"
        )
        parser.add_argument(
            "--env-only",
            action="store_true",
            help="Enter environment only without launching",
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Runs the software CLI with the given arguments.

        Args:
            args: Command line arguments, if None, sys.argv[1:] is used

        Returns:
            Exit code
        """
        parsed_args = self.parser.parse_args(args if args is not None else sys.argv[1:])

        prod_name = os.environ.get("PROD")

        if not prod_name:
            error_msg = (
                "Error: No Variable PROD found in the environment."
                "Please add it to the configuration file."
            )
            print(error_msg)
            return 1

        log_level = "DEBUG" if parsed_args.verbose else "INFO"
        self.logger = Logger(log_level)

        try:
            env = ProductionEnvironment(prod_name)
            additional_packages = parsed_args.packages or []
            env_only = parsed_args.env_only

            env.execute_software(
                self.software_name, additional_packages, env_only, False
            )

            return 0

        except (ConfigError, RezError) as e:
            return 1


if __name__ == "__main__":
    script_name = os.path.basename(sys.argv[0])
    software_name = os.path.splitext(script_name)[0]

    cli = SoftwareCLI(software_name)
    sys.exit(cli.run())
