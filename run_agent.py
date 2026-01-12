#!/usr/bin/env python3
"""
Backward-compatible wrapper for cli/run_agent.py.
This allows 'python run_agent.py' to continue working from the root directory.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI module
from cli.run_agent import main

if __name__ == "__main__":
    main()
