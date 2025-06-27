"""
Command line interface for the Prod CLI tool.
"""

import argparse
import os
from pathlib import Path
from typing import List, Optional

from src.logger import Logger
from src.production_environment import ProductionEnvironment


class LAUNCHCLI:
    """
    Manages the launch command line interface for the Prod CLI tool.
    """

    def __init__(self):
        """
        Initializes the CLI.
        """
        self.parser = self._setup_argument_parser()
        self.logger = None

    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """
        Sets up the argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Prod CLI Tool for launching software from productions",
        )
        parser.add_argument(
            "software",
            help="Software to launch"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Verbose output"
        )
        parser.add_argument(
            "--prod", "-p",
            required=True,
            help="Production name to launch software from"
        )
        parser.add_argument(
            "--packages",
            nargs="+",
            help="Additional packages to include"
        )
        parser.add_argument(
            "--env-only",
            action="store_true",
            help="Enter environment only without launching",
        )

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Runs the CLI with the given arguments.

        Args:
            args: Command line arguments, if None, sys.argv[1:] is used

        Returns:
            Exit code - 0 for success, 1 for error
        """
        parsed_args = self.parser.parse_args(args)
        self.logger = Logger(parsed_args.verbose)

        try:
            env = ProductionEnvironment(parsed_args.prod, verbose=parsed_args.verbose)
            self.logger.info(f"Launching {parsed_args.software} from production {parsed_args.prod}")
            additional_packages = parsed_args.packages if hasattr(parsed_args, "packages") else None
            env_only = parsed_args.env_only if hasattr(parsed_args, "env_only") else False
            env.execute_software(
                parsed_args.software, additional_packages, env_only,
            )
            return 0
        except Exception as e:
            self.logger.error(f"Failed to launch {parsed_args.software}: {e}")
            return 1


class PRODUCTIONCLI:

    """
    Manages the command line interface for the Prod CLI tool.
    """

    def __init__(self):
        """
        Initializes the CLI.
        """
        self.parser = self._setup_argument_parser()
        self.logger = None

    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """
        Sets up the argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Prod CLI Tool for managing production environments",
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Verbose output"
        )
        parser.add_argument(
            "--list", "-l",
            action="store_true",
            help="List available productions"
        )
        parser.add_argument(
            "production",
            nargs="?",
            choices=list_prod_names(),
            help="Name of the production to enter"
        )

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Runs the CLI with the given arguments.

        Args:
            args: Command line arguments, if None, sys.argv[1:] is used

        Returns:
            Exit code - 0 for success, 1 for error
        """
        parsed_args = self.parser.parse_args(args)
        self.logger = Logger(parsed_args.verbose)

        if parsed_args.list:
            return self._handle_list_command()

        if not parsed_args.production:
            self.logger.error("Please specify a production name")
            self.parser.print_help()
            return 1

        return self._handle_enter_command(parsed_args.production, parsed_args.verbose)

    def _handle_list_command(self):
        """
        Handles the list command.
        """

        prods = list_prod_names()

        if prods:
            print("Available productions:")
            for prod in sorted(prods):
                print(f"* {prod}")

    def _handle_enter_command(self, production_name: str, verbose: bool) -> int:
        """
        Handles the enter command.

        Args:
            production_name: Name of the production

        Returns:
            Exit code - 0 for success, 1 for error
        """
        try:
            env = ProductionEnvironment(production_name, verbose=verbose)
            env.activate()
            return 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to enter production {production_name}: {e}")
            else:
                print(f"Failed to enter production {production_name}: {e}")
            return 1


def list_prod_names():
    """
    Lists the names of available productions.
    Returns:
        List of production names
    """

    prods_dir = Path(__file__).parent.joinpath("../config/prods").resolve()
    if not prods_dir.exists():
        print("No productions found")
        return []
    return [d.name for d in prods_dir.iterdir() if d.is_dir()]


def prod() -> int:
    """
    Main entry point for the Prod CLI tool.

    Returns:
        Exit code
    """
    cli = PRODUCTIONCLI()
    return cli.run()


def prod_launch() -> int:
    """
    Main entry point for the Prod Launch CLI tool.

    Returns:
        Exit code
    """
    cli = LAUNCHCLI()
    return cli.run()
