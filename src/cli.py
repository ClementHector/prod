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

        subparsers = parser.add_subparsers(dest="command", help="Command to execute")

        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )

        list_parser = subparsers.add_parser("list", help="List available productions")
        list_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )

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

        if not args:
            self.parser.print_help()
            return 0

        known_commands = {"list"}
        if args[0] in known_commands:
            parsed_args = self.parser.parse_args(args)
        else:

            class Args(argparse.Namespace):
                """Simple namespace to mimic argparse.Namespace."""

                pass

            enter_args = Args()
            enter_args.production = args[0]
            enter_args.verbose = "--verbose" in args or "-v" in args
            log_level = "DEBUG" if enter_args.verbose else "INFO"
            self.logger = Logger(log_level)
            self.error_handler = ErrorHandler()
            return self._handle_enter_command(enter_args)

        is_verbose = getattr(parsed_args, "verbose", False)
        log_level = "DEBUG" if is_verbose else "INFO"
        self.logger = Logger(log_level)
        self.error_handler = ErrorHandler()

        try:
            if parsed_args.command == "list":
                return self._handle_list_command()
            else:
                self.parser.print_help()
                return 0
        except (ConfigError, RezError) as e:
            if self.error_handler:
                self.error_handler.handle_error(e)
            else:
                print(f"Error: {e}")
            return 1

    def _handle_list_command(self) -> int:
        """
        Handles the list command.

        Returns:
            Exit code
        """
        prods_dir = os.path.join(os.path.dirname(__file__), "../config/prods")

        if not os.path.exists(prods_dir):
            print("No productions found")
            return 0

        try:
            prods = [
                d
                for d in os.listdir(prods_dir)
                if os.path.isdir(os.path.join(prods_dir, d))
            ]

            if prods:
                print("Available productions:")
                for prod in sorted(prods):
                    print(f"* {prod}")
            else:
                print("No productions found")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to list productions: {e}")
            else:
                print(f"Failed to list productions: {e}")

        return 0

    def _handle_enter_command(self, args: argparse.Namespace) -> int:
        """
        Handles the enter command.

        Args:
            args: Command line arguments

        Returns:
            Exit code
        """
        try:
            env = ProductionEnvironment(args.production)
            env.activate()
            return 0
        except ConfigError as e:
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
