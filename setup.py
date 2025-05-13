#!/usr/bin/env python3
"""
Setup script for the Prod CLI tool.
"""
from setuptools import setup, find_packages

setup(
    name="prod",
    version="0.1.0",
    description="Prod CLI Tool for managing production environments",
    author="VFX/Animation Studio",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    entry_points={
        'console_scripts': [
            'prod=src.cli:main',
            'maya=src.software_cli:maya_main',
            'nuke=src.software_cli:nuke_main',
            'houdini=src.software_cli:houdini_main',
        ],
    },
    extras_require={
        'dev': ['black', 'isort', 'flake8', 'mypy', 'bandit'],
        'test': ['pytest', 'pytest-cov', 'pytest-bdd'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Utilities",
    ],
) 