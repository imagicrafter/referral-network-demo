"""
Dynamic tool registry for multi-domain analytics platform.

Loads domain configuration from YAML, resolves dependencies,
and provides unified access to tools across all enabled domains.

References:
- Python Plugin Architecture: https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
- Registry Pattern: https://github.com/SughoshKulkarni/Python-Registry
"""
import os
import importlib
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional
import yaml

from src.core.exceptions import (
    ConfigurationError,
    DomainNotFoundError,
    ToolNotFoundError,
    DependencyError,
)


class ToolRegistry:
    """
    Central registry for discovering and loading tools from enabled domains.

    Usage:
        registry = ToolRegistry()
        registry.load_domains()

        # Get all tools
        tools = registry.get_all_tools()
        result = tools["find_hospital"](name="Children's")

        # Get tool definitions for LLM
        definitions = registry.get_tool_definitions()
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the tool registry.

        Args:
            config_path: Path to domains.yaml. If None, uses default location.
        """
        if config_path is None:
            # Find config relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "domains.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.domains: Dict[str, Dict[str, Any]] = {}
        self._tools: Dict[str, Callable] = {}
        self._tool_definitions: List[Dict] = []
        self._loaded = False

        # Load configuration on init
        self._load_config()

    def _load_config(self) -> None:
        """Load and validate the domains configuration file."""
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path, 'r') as f:
            # Use safe_load for security
            self.config = yaml.safe_load(f)

        if not self.config or 'domains' not in self.config:
            raise ConfigurationError(
                "Invalid configuration: 'domains' section required"
            )

        self.domains = self.config.get('domains', {})

    def _resolve_dependencies(self, domain_name: str, resolved: set, visiting: set) -> List[str]:
        """
        Resolve domain dependencies using topological sort.

        Args:
            domain_name: Name of the domain to resolve
            resolved: Set of already resolved domains
            visiting: Set of domains currently being visited (for cycle detection)

        Returns:
            List of domain names in dependency order

        Raises:
            DependencyError: If circular dependency detected or dependency not found
        """
        if domain_name in resolved:
            return []

        if domain_name in visiting:
            raise DependencyError(f"Circular dependency detected: {domain_name}")

        if domain_name not in self.domains:
            raise DomainNotFoundError(f"Domain not found: {domain_name}")

        domain_config = self.domains[domain_name]
        if not domain_config.get('enabled', False):
            return []

        visiting.add(domain_name)
        order = []

        # Resolve dependencies first
        for dep in domain_config.get('depends_on', []):
            if dep not in self.domains:
                raise DependencyError(
                    f"Domain '{domain_name}' depends on unknown domain: {dep}"
                )
            order.extend(self._resolve_dependencies(dep, resolved, visiting))

        visiting.remove(domain_name)
        resolved.add(domain_name)
        order.append(domain_name)

        return order

    def get_enabled_domains(self) -> List[str]:
        """
        Get list of enabled domains in dependency order.

        Returns:
            List of enabled domain names, dependencies first
        """
        resolved: set = set()
        visiting: set = set()
        order: List[str] = []

        for domain_name, domain_config in self.domains.items():
            if domain_config.get('enabled', False):
                order.extend(
                    self._resolve_dependencies(domain_name, resolved, visiting)
                )

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for d in order:
            if d not in seen:
                seen.add(d)
                result.append(d)

        return result

    def load_domains(self) -> None:
        """
        Load tools and definitions from all enabled domains.

        This method:
        1. Resolves domain dependencies
        2. Imports each domain's module
        3. Collects tools and definitions
        """
        if self._loaded:
            return

        enabled_domains = self.get_enabled_domains()

        for domain_name in enabled_domains:
            domain_config = self.domains[domain_name]
            module_path = domain_config.get('module', f'src.domains.{domain_name}')

            try:
                # Import the domain's tools module
                tools_module = importlib.import_module(f"{module_path}.tools")

                # Get TOOLS dict (maps name -> function)
                if hasattr(tools_module, 'TOOLS'):
                    domain_tools = tools_module.TOOLS

                    # Filter to only configured tools
                    configured_tools = set(domain_config.get('tools', []))
                    for tool_name, tool_func in domain_tools.items():
                        if tool_name in configured_tools:
                            self._tools[tool_name] = tool_func

                # Get TOOL_DEFINITIONS list
                if hasattr(tools_module, 'TOOL_DEFINITIONS'):
                    domain_defs = tools_module.TOOL_DEFINITIONS
                    configured_tools = set(domain_config.get('tools', []))

                    for tool_def in domain_defs:
                        tool_name = tool_def.get('name', '')
                        if tool_name in configured_tools:
                            self._tool_definitions.append(tool_def)

            except ImportError as e:
                raise ConfigurationError(
                    f"Failed to import domain '{domain_name}' from {module_path}: {e}"
                )

        self._loaded = True

    def get_all_tools(self) -> Dict[str, Callable]:
        """
        Get all loaded tool functions.

        Returns:
            Dict mapping tool names to callable functions
        """
        if not self._loaded:
            self.load_domains()
        return self._tools.copy()

    def get_tool(self, name: str) -> Callable:
        """
        Get a specific tool by name.

        Args:
            name: Tool name

        Returns:
            Tool function

        Raises:
            ToolNotFoundError: If tool not found
        """
        if not self._loaded:
            self.load_domains()

        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")

        return self._tools[name]

    def get_tool_definitions(self) -> List[Dict]:
        """
        Get tool definitions for LLM function calling.

        Returns:
            List of tool definitions in OpenAI-compatible format
        """
        if not self._loaded:
            self.load_domains()
        return self._tool_definitions.copy()

    def get_openai_tools(self) -> List[Dict]:
        """
        Get tool definitions wrapped in OpenAI function calling format.

        Returns:
            List of tool definitions with type: "function" wrapper
        """
        definitions = self.get_tool_definitions()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"]
                }
            }
            for tool_def in definitions
        ]

    def list_tools(self) -> List[str]:
        """
        List all available tool names.

        Returns:
            List of tool names
        """
        if not self._loaded:
            self.load_domains()
        return list(self._tools.keys())

    def get_domain_info(self, domain_name: str) -> Dict[str, Any]:
        """
        Get information about a specific domain.

        Args:
            domain_name: Name of the domain

        Returns:
            Domain configuration dict

        Raises:
            DomainNotFoundError: If domain not found
        """
        if domain_name not in self.domains:
            raise DomainNotFoundError(f"Domain not found: {domain_name}")
        return self.domains[domain_name].copy()
