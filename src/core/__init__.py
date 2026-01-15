"""
Core infrastructure for healthcare-graph-agent.
Provides shared utilities used by all domain modules.
"""
from src.core.tool_registry import ToolRegistry
from src.core.exceptions import (
    DomainNotFoundError,
    ToolNotFoundError,
    ConfigurationError,
)

# Database connection is optional (requires gremlin_python)
try:
    from src.core.cosmos_connection import get_client, execute_query
    __all__ = [
        "get_client",
        "execute_query",
        "ToolRegistry",
        "DomainNotFoundError",
        "ToolNotFoundError",
        "ConfigurationError",
    ]
except ImportError:
    __all__ = [
        "ToolRegistry",
        "DomainNotFoundError",
        "ToolNotFoundError",
        "ConfigurationError",
    ]
