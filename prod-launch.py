#!/usr/bin/env python3
"""
Main entry point for the Prod CLI tool.
This script allows the tool to be run directly without installation.
"""
import sys
from src.cli import prod_launch

if __name__ == '__main__':
    sys.exit(prod_launch())