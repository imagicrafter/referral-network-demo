#!/usr/bin/env python3
"""
Backward-compatible wrapper for cli/network_cli.py.
This allows 'python network_cli.py' to continue working from the root directory.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI module
from cli.network_cli import main

if __name__ == "__main__":
    main()
