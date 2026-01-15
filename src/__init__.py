"""
Healthcare Graph Agent - Shared source code.
This package contains shared modules used across CLI, Azure Functions, and Gradient agents.
"""
# Re-export from core module for backward compatibility
# Imports are lazy to avoid requiring gremlin_python for all operations
try:
    from src.core.cosmos_connection import get_client, execute_query
    __all__ = ['get_client', 'execute_query']
except ImportError:
    # gremlin_python not installed, exports not available
    __all__ = []
