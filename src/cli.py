"""
Command line interface for the Prod CLI tool.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

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

    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """
        Sets up the argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Prod CLI Tool for managing production environments"
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        subparsers.add_parser("list", help="List available productions")

        launch_parser = subparsers.add_parser(
            "launch", help="Launch software from a production"
        )
        launch_parser.add_argument("software", help="Software to launch")
        launch_parser.add_argument("--prod", required=True, help="Production name")
        launch_parser.add_argument(
            "--packages", nargs="+", help="Additional packages to include"
        )
        launch_parser.add_argument(
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
        if args is None:
            args = sys.argv[1:]

        if not args:
            self.parser.print_help()
            return 0

        is_verbose = "--verbose" in args or "-v" in args
        self.logger = Logger(is_verbose)

        known_commands = {"list", "launch"}
        if args[0] in known_commands:
            parsed_args = self.parser.parse_args(args)
            if parsed_args.command == "list":
                return self._handle_list_command()
            elif parsed_args.command == "launch":
                return self._handle_launch_command(parsed_args)
            self.parser.print_help()
            return 0

        enter_args = argparse.Namespace()
        enter_args.production = args[0]
        enter_args.verbose = is_verbose
        return self._handle_enter_command(enter_args)

    def _handle_list_command(self) -> int:
        """
        Handles the list command.

        Returns:
            Exit code - 0 for success, 1 for error
        """
        prods_dir = Path(__file__).parent.joinpath("../config/prods").resolve()

        if not prods_dir.exists():
            print("No productions found")
            return 0

        try:
            prods = [d.name for d in prods_dir.iterdir() if d.is_dir()]

            if prods:
                print("Available productions:")
                for prod in sorted(prods):
                    print(f"* {prod}")
            else:
                print("No productions found")

            return 0

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to list productions: {e}")
            else:
                print(f"Failed to list productions: {e}")

            return 1

    def _handle_enter_command(self, args: argparse.Namespace) -> int:
        """
        Handles the enter command.

        Args:
            args: Command line arguments

        Returns:
            Exit code - 0 for success, 1 for error
        """
        try:
            env = ProductionEnvironment(args.production, verbose=args.verbose)
            env.activate()
            return 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to enter production {args.production}: {e}")
            else:
                print(f"Failed to enter production {args.production}: {e}")
            return 1

    def _handle_launch_command(self, args: argparse.Namespace) -> int:
        """
        Handles the launch command.

        Args:
            args: Command line arguments

        Returns:
            Exit code - 0 for success, 1 for error
        """
        try:
            env = ProductionEnvironment(args.prod, verbose=args.verbose)
            self.logger.info(f"Launching {args.software} from production {args.prod}")
            additional_packages = args.packages if hasattr(args, "packages") else None
            env_only = args.env_only if hasattr(args, "env_only") else False
            env.execute_software(
                args.prod, args.software, additional_packages, env_only, background=True
            )
            return 0
        except Exception as e:
            self.logger.error(f"Failed to launch {args.software}: {e}")
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
