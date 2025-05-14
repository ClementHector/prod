"""
Command line interface for the Prod CLI tool.
"""

import argparse
import os
import sys
from typing import List, Optional

from src.error_handler import ConfigError, ErrorHandler, RezError
from src.logger import Logger
from src.production_environment import ProductionEnvironment


class CLI:
    """
    Manages the command line interface for the Prod CLI tool.
    """

    def __init__(self):
        """
        Initializes the CLI.
        """
        self.parser = self._setup_argument_parser()
        self.logger = None
        self.error_handler = None

    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """
        Sets up the argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Prod CLI Tool for managing production environments"
        )

        # Main parser for prod command
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")

        # List command
        list_parser = subparsers.add_parser("list", help="List available productions")
        list_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )

        # Software command (handled in software_cli.py)

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Runs the CLI with the given arguments.

        Args:
            args: Command line arguments, if None, sys.argv[1:] is used

        Returns:
            Exit code
        """
        if args is None:
            args = sys.argv[1:]

        # Si aucun argument, afficher l'aide
        if not args:
            self.parser.print_help()
            return 0

        # On parse d'abord la sous-commande connue
        known_commands = {"list"}
        if args[0] in known_commands:
            parsed_args = self.parser.parse_args(args)
        else:
            # Si le premier argument n'est pas une sous-commande
            # On le traite comme un nom de production
            class Args(argparse.Namespace):
                """Simple namespace to mimic argparse.Namespace."""

                pass

            enter_args = Args()
            enter_args.production = args[0]
            enter_args.verbose = False
            log_level = "INFO"
            self.logger = Logger(log_level)
            self.error_handler = ErrorHandler(self.logger)
            return self._handle_enter_command(enter_args)

        # Initialisation du logger
        is_list_cmd = getattr(parsed_args, "command", None) == "list"
        is_verbose = getattr(parsed_args, "verbose", False)

        log_level = "DEBUG" if (is_list_cmd and is_verbose) else "INFO"
        self.logger = Logger(log_level)

        # Initialisation du gestionnaire d'erreurs
        self.error_handler = ErrorHandler(self.logger)

        # Gestion des commandes
        try:
            if parsed_args.command == "list":
                return self._handle_list_command(parsed_args)
            else:
                self.parser.print_help()
                return 0

        except (ConfigError, RezError, Exception) as e:
            if self.error_handler:
                self.error_handler.handle_error(e)
            else:
                print(f"Error: {e}")
            return 1

    def _handle_list_command(self, args: argparse.Namespace) -> int:
        """
        Handles the list command.

        Args:
            args: Command line arguments

        Returns:
            Exit code
        """
        # Get prods from config/prods directory
        prods_dir = os.path.join(os.path.dirname(__file__), "../config/prods")

        if not os.path.exists(prods_dir):
            print("No productions found")
            return 0

        # Get all directories in prods dir
        prods = []
        try:
            prods = [
                d
                for d in os.listdir(prods_dir)
                if os.path.isdir(os.path.join(prods_dir, d))
            ]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to list productions: {e}")
            else:
                print(f"Failed to list productions: {e}")

        # Print productions
        if prods:
            print("Available productions:")
            for prod in sorted(prods):
                print(f"* {prod}")
        else:
            print("No productions found")

        return 0

    def _handle_enter_command(self, args: argparse.Namespace) -> int:
        """
        Handles the enter command.

        Args:
            args: Command line arguments

        Returns:
            Exit code
        """
        # Create and activate the production environment
        try:
            env = ProductionEnvironment(args.production, self.logger)
            env.activate()

            print(f"Entered production environment '{args.production}'")
            print("Available software:")

            # Print available software
            software_list = env.get_software_list()
            if software_list:
                for software in software_list:
                    print(f"* {software['name']} (version {software['version']})")
            else:
                print("No software configured for this production")

            return 0

        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(e)
            else:
                print(f"Error: {e}")
            return 1


def main() -> int:
    """
    Main entry point for the Prod CLI tool.

    Returns:
        Exit code
    """
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
