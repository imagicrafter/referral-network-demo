# PRP: Modular Domain Architecture Reorganization

**Feature**: Transform single-purpose referral network agent into modular analytics platform
**Priority**: High
**Estimated Complexity**: Medium-High
**Target Version**: 2.0.0

---

## 1. Overview

### 1.1 What We're Building

Transform the `referral-network-demo` repository from a single-purpose referral network agent into a **modular analytics platform** that supports multiple healthcare analytics domains through a unified infrastructure.

### 1.2 Why This Matters

| Current State | Problem | Target State |
|---------------|---------|--------------|
| Flat file structure | Adding new domains requires modifying core files | Domain modules with clear boundaries |
| Hardcoded tool lists | Every new tool requires changes to 5+ files | Dynamic tool registry based on YAML config |
| Single-purpose agent | Cannot easily extend to new use cases | Multi-domain agent with pluggable capabilities |
| Tight coupling | Database, tools, and agent logic intermingled | Layered architecture with explicit dependencies |

### 1.3 Success Criteria

1. **All existing functionality works** - No regression in referral network features
2. **Tool registry loads correctly** - `make validate-config` passes
3. **Tools are discoverable** - `make list-tools` outputs all 11 referral network tools
4. **Tests pass** - `make test` completes successfully
5. **Single source of truth** - No duplicate tool definitions across files
6. **Documentation updated** - README reflects new structure

---

## 2. Architecture

### 2.1 File Dependency Diagram

```
config/domains.yaml
       │
       ▼
src/core/tool_registry.py ◄─────────────────────────┐
       │                                            │
       ├──► src/core/cosmos_connection.py           │
       │           │                                │
       │           ▼                                │
       │    src/domains/referral_network/tools.py ──┘
       │           │
       │           ▼
       │    src/domains/referral_network/diagrams.py
       │
       ▼
┌──────────────────────────────────────────────────┐
│              Consumers                            │
├──────────────────────────────────────────────────┤
│ cli/run_agent.py                                 │
│ cli/network_cli.py                               │
│ azure-functions/function_app.py                  │
│ gradient-agents/main.py                          │
│ pipes/gradient-inference-pipe.py                 │
└──────────────────────────────────────────────────┘
```

### 2.2 Target Directory Structure

```
referral-network-demo/
├── config/                         # NEW: Configuration files
│   ├── domains.yaml                # Domain enable/disable and tool lists
│   └── logging.yaml                # Optional: Logging configuration
│
├── src/
│   ├── __init__.py                 # Existing
│   │
│   ├── core/                       # NEW: Shared infrastructure
│   │   ├── __init__.py
│   │   ├── cosmos_connection.py    # MOVE from src/cosmos_connection.py
│   │   ├── tool_registry.py        # NEW: Dynamic tool registration
│   │   ├── diagram_base.py         # NEW: Base diagram utilities
│   │   └── exceptions.py           # NEW: Custom exceptions
│   │
│   ├── domains/                    # NEW: Feature modules
│   │   ├── __init__.py
│   │   │
│   │   └── referral_network/       # Existing functionality reorganized
│   │       ├── __init__.py
│   │       ├── tools.py            # CONSOLIDATE from src/tools/
│   │       ├── diagrams.py         # MOVE from src/tools/diagram_generators.py
│   │       ├── schema.py           # NEW: Vertex/edge type definitions
│   │       └── sample_data.py      # EXTRACT from scripts/load_sample_data.py
│   │
│   ├── tools/                      # DEPRECATED - will be removed
│   │   └── ...                     # Content moves to domains/referral_network/
│   │
│   ├── prompts/                    # Keep as-is (shared across domains)
│   │   ├── __init__.py
│   │   └── system_prompts.py
│   │
│   └── exports/                    # NEW: Reporting integrations
│       ├── __init__.py
│       └── powerbi.py              # EXTRACT from scripts/export_for_powerbi.py
│
├── tests/                          # NEW: Test infrastructure
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── core/
│   │   ├── test_tool_registry.py
│   │   └── test_cosmos_connection.py
│   └── domains/
│       └── referral_network/
│           ├── test_tools.py
│           └── test_diagrams.py
│
└── docs/
    ├── architecture.md             # NEW: Architecture overview
    └── adding_domains.md           # NEW: Guide for new domains
```

---

## 3. Implementation Tasks

### Phase 1: Create Core Infrastructure

#### Task 1.1: Create config/domains.yaml

**File**: `config/domains.yaml`

```yaml
# Domain configuration for referral-network-demo
# Controls which analytics domains are enabled and their dependencies

version: "1.0"

defaults:
  # Default settings applied to all domains unless overridden
  max_tool_timeout: 30  # seconds

domains:
  referral_network:
    enabled: true
    name: "Referral Network Analytics"
    description: "Hospital referral flow analysis and visualization"
    version: "1.0.0"
    depends_on: []  # No dependencies - foundational domain
    module: "src.domains.referral_network"

    tools:
      - find_hospital
      - get_referral_sources
      - get_referral_destinations
      - get_network_statistics
      - find_referral_path
      - get_providers_by_specialty
      - get_hospitals_by_service
      - analyze_rural_access
      - generate_referral_network_diagram
      - generate_path_diagram
      - generate_service_network_diagram

    vertex_types:
      - hospital
      - provider
      - service_line

    edge_types:
      - refers_to
      - employs
      - specializes_in

  # Placeholder for Phase 2 - Quality Improvement domain
  # quality_improvement:
  #   enabled: false
  #   depends_on: [referral_network]
  #   module: "src.domains.quality_improvement"
```

#### Task 1.2: Create src/core/__init__.py

**File**: `src/core/__init__.py`

```python
"""
Core infrastructure for referral-network-demo.
Provides shared utilities used by all domain modules.
"""
from src.core.cosmos_connection import get_client, execute_query
from src.core.tool_registry import ToolRegistry
from src.core.exceptions import (
    DomainNotFoundError,
    ToolNotFoundError,
    ConfigurationError,
)

__all__ = [
    "get_client",
    "execute_query",
    "ToolRegistry",
    "DomainNotFoundError",
    "ToolNotFoundError",
    "ConfigurationError",
]
```

#### Task 1.3: Move src/cosmos_connection.py to src/core/cosmos_connection.py

**Action**: Move file, keep same content. Update the module path.

**Key Pattern** (from existing `src/cosmos_connection.py:10-16`):
```python
# Load dotenv only if available and not in Azure Functions
# Azure Functions automatically load app settings as env vars
try:
    from dotenv import load_dotenv
    # Only load if FUNCTIONS_WORKER_RUNTIME not set (not in Azure Functions)
    if not os.getenv("FUNCTIONS_WORKER_RUNTIME"):
        load_dotenv()
except ImportError:
    pass  # dotenv not installed, assume env vars are already set
```

#### Task 1.4: Create src/core/exceptions.py

**File**: `src/core/exceptions.py`

```python
"""Custom exceptions for the referral network platform."""


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class DomainNotFoundError(Exception):
    """Raised when a requested domain is not found or not enabled."""
    pass


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found in any enabled domain."""
    pass


class DependencyError(Exception):
    """Raised when domain dependencies cannot be resolved."""
    pass
```

#### Task 1.5: Create src/core/tool_registry.py

**File**: `src/core/tool_registry.py`

This is the **critical component** that enables the modular architecture.

```python
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
```

#### Task 1.6: Create src/core/diagram_base.py

**File**: `src/core/diagram_base.py`

Extract shared diagram utilities from existing `src/tools/diagram_generators.py`:

```python
"""
Base diagram utilities shared across domain diagram generators.

Extracted from src/tools/diagram_generators.py for reuse across domains.
"""
import hashlib
from typing import Dict


def sanitize_node_id(name: str) -> str:
    """
    Convert entity name to valid Mermaid node ID.
    Uses first letters of each word plus a short hash for uniqueness.

    Args:
        name: Entity name (e.g., hospital name)

    Returns:
        Valid Mermaid node ID (e.g., "CMKC_f9e3")
    """
    # Remove special characters and split into words
    clean_name = name.replace("'", "").replace(".", "").replace("-", " ")
    words = clean_name.split()

    # Take first letter of each word
    initials = "".join(word[0].upper() for word in words if word)

    # Add short hash for uniqueness
    name_hash = hashlib.md5(name.encode()).hexdigest()[:4]

    return f"{initials}_{name_hash}"


def escape_label(text: str) -> str:
    """
    Escape special characters for Mermaid labels.

    Args:
        text: Label text

    Returns:
        Escaped text safe for Mermaid syntax
    """
    return text.replace('"', "'").replace("<", "&lt;").replace(">", "&gt;")


# Color palette for consistent styling across domains
COLORS = {
    # Hospital types
    "tertiary": "#4CAF50",      # Green
    "community": "#2196F3",     # Blue
    "regional": "#9C27B0",      # Purple
    "specialty": "#E91E63",     # Pink
    "rural": "#FF9800",         # Orange
    "default": "#607D8B",       # Gray

    # Status colors
    "start": "#4CAF50",         # Green
    "end": "#F44336",           # Red
    "highlight": "#FFD700",     # Gold

    # Service colors
    "service": "#673AB7",       # Deep Purple
}


def get_style(color_key: str, stroke: bool = False) -> str:
    """
    Get Mermaid style string for a color key.

    Args:
        color_key: Key from COLORS dict
        stroke: Whether to add stroke styling

    Returns:
        Mermaid style string (e.g., "fill:#4CAF50,color:#fff")
    """
    color = COLORS.get(color_key, COLORS["default"])
    text_color = "#fff" if color_key != "highlight" else "#000"

    style = f"fill:{color},color:{text_color}"

    if stroke:
        # Darker stroke version of the color
        style += f",stroke:{color},stroke-width:2px"

    return style
```

### Phase 2: Create Domain Module

#### Task 2.1: Create src/domains/__init__.py

**File**: `src/domains/__init__.py`

```python
"""
Domain modules for the analytics platform.

Each domain provides:
- tools.py: Tool implementations and definitions
- diagrams.py: Mermaid diagram generators (optional)
- schema.py: Vertex/edge type definitions
- sample_data.py: Sample data loader
"""
```

#### Task 2.2: Create src/domains/referral_network/__init__.py

**File**: `src/domains/referral_network/__init__.py`

```python
"""
Referral Network Analytics Domain.

Provides tools for analyzing hospital referral patterns, provider
networks, and service line coverage in children's hospitals.
"""
from src.domains.referral_network.tools import TOOLS, TOOL_DEFINITIONS

__all__ = ["TOOLS", "TOOL_DEFINITIONS"]
```

#### Task 2.3: Create src/domains/referral_network/tools.py

**File**: `src/domains/referral_network/tools.py`

Consolidate `src/tools/definitions.py` and `src/tools/queries.py`:

```python
"""
Referral network domain tools.

Consolidates tool definitions and query implementations for the
referral network analytics domain.
"""
from typing import Dict, List, Any, Optional, Callable
from src.core.cosmos_connection import get_client, execute_query

# =============================================================================
# Database helpers
# =============================================================================

_client = None


def get_graph_client():
    """Get or create the Gremlin client."""
    global _client
    if _client is None:
        _client = get_client()
    return _client


def _clean_value_map(results: list) -> List[Dict]:
    """Convert Gremlin valueMap results to cleaner dictionaries."""
    cleaned = []
    for item in results:
        if isinstance(item, dict):
            clean_item = {}
            for key, value in item.items():
                # valueMap returns lists for each property
                if isinstance(value, list) and len(value) == 1:
                    clean_item[key] = value[0]
                else:
                    clean_item[key] = value
            cleaned.append(clean_item)
        else:
            cleaned.append(item)
    return cleaned


# =============================================================================
# Tool implementations
# =============================================================================

def find_hospital(
    name: Optional[str] = None,
    state: Optional[str] = None,
    hospital_type: Optional[str] = None,
    rural: Optional[bool] = None
) -> List[Dict]:
    """
    Find hospitals matching the given criteria.

    Args:
        name: Hospital name (partial match)
        state: State abbreviation (e.g., 'MO', 'KS')
        hospital_type: Type ('tertiary', 'community', 'regional', 'specialty')
        rural: Whether the hospital is in a rural area

    Returns:
        List of matching hospitals with their properties
    """
    client = get_graph_client()

    query = "g.V().hasLabel('hospital')"

    if name:
        safe_name = name.replace("'", "\\'")
        query += f".has('name', TextP.containing('{safe_name}'))"
    if state:
        query += f".has('state', '{state}')"
    if hospital_type:
        query += f".has('type', '{hospital_type}')"
    if rural is not None:
        query += f".has('rural', {str(rural).lower()})"

    query += ".valueMap(true)"

    results = execute_query(client, query)
    return _clean_value_map(results)


def get_referral_sources(hospital_name: str) -> List[Dict]:
    """
    Find all hospitals that refer patients to the specified hospital.

    Args:
        hospital_name: Name of the receiving hospital

    Returns:
        List of referring hospitals with referral volumes
    """
    client = get_graph_client()
    safe_name = hospital_name.replace("'", "\\'")

    query = f"""
    g.V().has('hospital', 'name', '{safe_name}')
      .inE('refers_to')
      .order().by('count', decr)
      .project('referring_hospital', 'referral_count', 'avg_acuity')
      .by(outV().values('name'))
      .by('count')
      .by('avg_acuity')
    """

    return execute_query(client, query)


def get_referral_destinations(hospital_name: str) -> List[Dict]:
    """
    Find all hospitals that receive referrals from the specified hospital.

    Args:
        hospital_name: Name of the referring hospital

    Returns:
        List of destination hospitals with referral volumes
    """
    client = get_graph_client()
    safe_name = hospital_name.replace("'", "\\'")

    query = f"""
    g.V().has('hospital', 'name', '{safe_name}')
      .outE('refers_to')
      .order().by('count', decr)
      .project('destination_hospital', 'referral_count', 'avg_acuity')
      .by(inV().values('name'))
      .by('count')
      .by('avg_acuity')
    """

    return execute_query(client, query)


def get_network_statistics() -> Dict[str, Any]:
    """
    Get overall statistics about the referral network.

    Returns:
        Dictionary with network statistics
    """
    client = get_graph_client()

    stats = {}
    stats['total_hospitals'] = execute_query(client,
        "g.V().hasLabel('hospital').count()")[0]
    stats['total_providers'] = execute_query(client,
        "g.V().hasLabel('provider').count()")[0]
    stats['total_referral_relationships'] = execute_query(client,
        "g.E().hasLabel('refers_to').count()")[0]
    stats['total_referral_volume'] = execute_query(client,
        "g.E().hasLabel('refers_to').values('count').sum()")[0]
    stats['rural_hospitals'] = execute_query(client,
        "g.V().hasLabel('hospital').has('rural', true).count()")[0]
    stats['tertiary_centers'] = execute_query(client,
        "g.V().hasLabel('hospital').has('type', 'tertiary').count()")[0]

    return stats


def find_referral_path(
    from_hospital: str,
    to_hospital: str,
    max_hops: int = 3
) -> List:
    """
    Find referral paths between two hospitals.

    Args:
        from_hospital: Starting hospital name
        to_hospital: Destination hospital name
        max_hops: Maximum number of intermediate hospitals

    Returns:
        List of paths, where each path is a list of hospital names
    """
    client = get_graph_client()

    safe_from = from_hospital.replace("'", "\\'")
    safe_to = to_hospital.replace("'", "\\'")

    query = f"""
    g.V().has('hospital', 'name', '{safe_from}')
      .repeat(out('refers_to').simplePath())
      .until(has('name', '{safe_to}').or().loops().is(gte({max_hops})))
      .has('name', '{safe_to}')
      .path()
      .by('name')
      .limit(10)
    """

    return execute_query(client, query)


def get_providers_by_specialty(specialty: str) -> List[Dict]:
    """
    Find providers by specialty and their hospital affiliations.

    Args:
        specialty: Medical specialty (e.g., 'Pediatric Cardiology')

    Returns:
        List of providers with their hospital affiliations
    """
    client = get_graph_client()
    safe_specialty = specialty.replace("'", "\\'")

    query = f"""
    g.V().hasLabel('provider')
      .has('specialty', '{safe_specialty}')
      .project('provider_name', 'specialty')
      .by('name')
      .by('specialty')
    """

    return execute_query(client, query)


def get_hospitals_by_service(service_name: str) -> List[Dict]:
    """
    Find hospitals that offer a specific service line.

    Args:
        service_name: Name of the service (e.g., 'Cardiac Surgery')

    Returns:
        List of hospitals with volume and ranking
    """
    client = get_graph_client()
    safe_service = service_name.replace("'", "\\'")

    query = f"""
    g.V().has('service_line', 'name', '{safe_service}')
      .inE('specializes_in')
      .order().by('ranking', incr)
      .project('hospital', 'volume', 'ranking')
      .by(outV().values('name'))
      .by('volume')
      .by('ranking')
    """

    return execute_query(client, query)


def analyze_rural_access(service_name: str) -> List[Dict]:
    """
    Analyze how rural hospitals connect to specialized services.

    Args:
        service_name: Name of the specialized service

    Returns:
        Analysis of rural hospital access to the service
    """
    client = get_graph_client()
    safe_service = service_name.replace("'", "\\'")

    query = f"""
    g.V().hasLabel('hospital').has('rural', true)
      .project('rural_hospital', 'state')
      .by('name')
      .by('state')
    """

    return execute_query(client, query)


# Import diagram generators
from src.domains.referral_network.diagrams import (
    generate_referral_network_diagram,
    generate_path_diagram,
    generate_service_network_diagram,
)


# =============================================================================
# Tool registry exports
# =============================================================================

TOOLS: Dict[str, Callable] = {
    "find_hospital": find_hospital,
    "get_referral_sources": get_referral_sources,
    "get_referral_destinations": get_referral_destinations,
    "get_network_statistics": get_network_statistics,
    "find_referral_path": find_referral_path,
    "get_providers_by_specialty": get_providers_by_specialty,
    "get_hospitals_by_service": get_hospitals_by_service,
    "analyze_rural_access": analyze_rural_access,
    "generate_referral_network_diagram": generate_referral_network_diagram,
    "generate_path_diagram": generate_path_diagram,
    "generate_service_network_diagram": generate_service_network_diagram,
}


TOOL_DEFINITIONS: List[Dict] = [
    {
        "name": "find_hospital",
        "description": "Search for hospitals by name, state, type, or rural status. Use partial names like 'Children's Mercy' to find matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Hospital name (partial match supported)"},
                "state": {"type": "string", "description": "State abbreviation (e.g., 'MO', 'KS')"},
                "hospital_type": {"type": "string", "enum": ["tertiary", "community", "regional", "specialty"]},
                "rural": {"type": "boolean", "description": "Whether the hospital is in a rural area"}
            }
        }
    },
    {
        "name": "get_referral_sources",
        "description": "Find all hospitals that refer patients to a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the receiving hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_referral_destinations",
        "description": "Find all hospitals that receive referrals from a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the referring hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_network_statistics",
        "description": "Get overall statistics about the referral network",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "find_referral_path",
        "description": "Find referral paths between two hospitals",
        "parameters": {
            "type": "object",
            "properties": {
                "from_hospital": {"type": "string", "description": "Starting hospital name"},
                "to_hospital": {"type": "string", "description": "Destination hospital name"},
                "max_hops": {"type": "integer", "description": "Maximum intermediate hospitals", "default": 3}
            },
            "required": ["from_hospital", "to_hospital"]
        }
    },
    {
        "name": "get_providers_by_specialty",
        "description": "Find providers by medical specialty",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string", "description": "Medical specialty name"}
            },
            "required": ["specialty"]
        }
    },
    {
        "name": "get_hospitals_by_service",
        "description": "Find hospitals offering a specific service line",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service line"}
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "analyze_rural_access",
        "description": "Analyze how rural hospitals connect to specialized services",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the specialized service"}
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "generate_referral_network_diagram",
        "description": "Generate a Mermaid diagram showing hospital referral relationships",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Optional: focus on specific hospital"},
                "include_volumes": {"type": "boolean", "description": "Show referral counts", "default": True},
                "direction": {"type": "string", "enum": ["LR", "TB", "RL", "BT"], "default": "LR"}
            }
        }
    },
    {
        "name": "generate_path_diagram",
        "description": "Generate a Mermaid diagram showing paths between two hospitals",
        "parameters": {
            "type": "object",
            "properties": {
                "from_hospital": {"type": "string", "description": "Starting hospital name"},
                "to_hospital": {"type": "string", "description": "Destination hospital name"},
                "max_hops": {"type": "integer", "description": "Maximum path length", "default": 3}
            },
            "required": ["from_hospital", "to_hospital"]
        }
    },
    {
        "name": "generate_service_network_diagram",
        "description": "Generate a Mermaid diagram showing hospitals that provide a service",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service line"},
                "include_rankings": {"type": "boolean", "description": "Show hospital rankings", "default": True}
            },
            "required": ["service_name"]
        }
    },
]
```

#### Task 2.4: Move/Create src/domains/referral_network/diagrams.py

**File**: `src/domains/referral_network/diagrams.py`

Move content from `src/tools/diagram_generators.py` with updated imports:

```python
"""
Mermaid diagram generators for referral network domain.

Generates valid Mermaid syntax from Cosmos DB graph data.
"""
from typing import Dict, List, Optional, Any
import logging

from src.core.diagram_base import (
    sanitize_node_id,
    escape_label,
    get_style,
    COLORS,
)

# ... (Copy all existing functions from src/tools/diagram_generators.py)
# Update get_hospital_style to use the shared get_style function
# Keep all the generate_* functions as-is
```

**Note**: The existing `src/tools/diagram_generators.py` has 579 lines. Copy all functions but update imports to use `src.core.diagram_base`.

#### Task 2.5: Create src/domains/referral_network/schema.py

**File**: `src/domains/referral_network/schema.py`

```python
"""
Schema definitions for the referral network domain.

Documents vertex and edge types stored in Cosmos DB Gremlin.
"""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class VertexType:
    """Definition of a vertex type in the graph."""
    label: str
    description: str
    properties: Dict[str, str]  # property_name -> description
    partition_key_pattern: str


@dataclass
class EdgeType:
    """Definition of an edge type in the graph."""
    label: str
    description: str
    from_vertex: str
    to_vertex: str
    properties: Dict[str, str]


# Vertex type definitions
HOSPITAL = VertexType(
    label="hospital",
    description="Healthcare facility that provides patient care",
    properties={
        "id": "Unique identifier (e.g., 'hosp-001')",
        "name": "Full hospital name",
        "city": "City location",
        "state": "State abbreviation (e.g., 'MO', 'KS')",
        "type": "Hospital type: tertiary, community, regional, specialty",
        "beds": "Number of beds (integer)",
        "rural": "Whether in rural area (boolean)",
    },
    partition_key_pattern="hospital_{state}"
)

PROVIDER = VertexType(
    label="provider",
    description="Healthcare provider (physician, specialist)",
    properties={
        "id": "Unique identifier (e.g., 'prov-001')",
        "name": "Provider name (e.g., 'Dr. Sarah Chen')",
        "specialty": "Medical specialty",
        "npi": "National Provider Identifier",
    },
    partition_key_pattern="provider_midwest"
)

SERVICE_LINE = VertexType(
    label="service_line",
    description="Medical service line offered by hospitals",
    properties={
        "id": "Unique identifier (e.g., 'svc-001')",
        "name": "Service name (e.g., 'Cardiac Surgery')",
        "category": "Category: surgical, medical, critical_care, primary",
    },
    partition_key_pattern="service_line"
)

# Edge type definitions
REFERS_TO = EdgeType(
    label="refers_to",
    description="Referral relationship between hospitals",
    from_vertex="hospital",
    to_vertex="hospital",
    properties={
        "count": "Number of referrals (integer)",
        "avg_acuity": "Average patient acuity score (float)",
    }
)

EMPLOYS = EdgeType(
    label="employs",
    description="Employment relationship between hospital and provider",
    from_vertex="hospital",
    to_vertex="provider",
    properties={
        "fte": "Full-time equivalent (0.0-1.0)",
    }
)

SPECIALIZES_IN = EdgeType(
    label="specializes_in",
    description="Hospital offering a service line",
    from_vertex="hospital",
    to_vertex="service_line",
    properties={
        "volume": "Annual case volume (integer)",
        "ranking": "National ranking (integer, 1 = best)",
    }
)

# Export all types
VERTEX_TYPES = [HOSPITAL, PROVIDER, SERVICE_LINE]
EDGE_TYPES = [REFERS_TO, EMPLOYS, SPECIALIZES_IN]
```

### Phase 3: Update Consumers

#### Task 3.1: Update cli/run_agent.py

**File**: `cli/run_agent.py`

Key changes:
- Import from `src.core.tool_registry` instead of `src.tools.definitions`
- Use `ToolRegistry` to get tools and definitions

```python
#!/usr/bin/env python3
"""
Unified launcher for Referral Network Agent.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
from dotenv import load_dotenv

load_dotenv()

# Import from core - NEW
from src.core.tool_registry import ToolRegistry
from src.prompts.system_prompts import SYSTEM_PROMPT

# Initialize registry once
_registry = None

def get_registry():
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load_domains()
    return _registry


def run_azure_agent():
    """Run the Azure OpenAI agent."""
    import json
    import time
    from openai import AzureOpenAI, RateLimitError

    registry = get_registry()
    TOOL_FUNCTIONS = registry.get_all_tools()

    # ... rest of function, replace:
    # - TOOL_DEFINITIONS with registry.get_tool_definitions()
    # - get_tool_functions() with registry.get_all_tools()


def run_gradient_agent():
    """Run the Gradient agent."""
    import json
    from gradient import AsyncGradient

    registry = get_registry()
    TOOL_FUNCTIONS = registry.get_all_tools()

    # ... rest of function with same pattern


# ... rest of file stays similar
```

#### Task 3.2: Update azure-functions/function_app.py

**File**: `azure-functions/function_app.py`

Key changes:
- Import from `src.core.tool_registry`
- Initialize registry at module level
- Each endpoint calls registry.get_tool()

```python
"""
Azure Functions backend API for Referral Network Agent Tools.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import azure.functions as func
import json
import logging

from src.core.tool_registry import ToolRegistry

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Initialize registry once at module load
_registry = None

def get_registry():
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load_domains()
    return _registry


@app.route(route="tools/{tool_name}", methods=["POST"])
def execute_tool(req: func.HttpRequest) -> func.HttpResponse:
    """Generic tool execution endpoint."""
    tool_name = req.route_params.get('tool_name')

    try:
        registry = get_registry()
        tool_func = registry.get_tool(tool_name)

        body = req.get_json() if req.get_body() else {}
        result = tool_func(**body)

        # Return as JSON for data tools, plain text for diagrams
        if tool_name.startswith('generate_'):
            return func.HttpResponse(result, mimetype="text/plain")
        return func.HttpResponse(json.dumps(result), mimetype="application/json")

    except Exception as e:
        logging.error(f"Error in {tool_name}: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Keep individual endpoints for backward compatibility
@app.route(route="tools/find_hospital", methods=["POST"])
def find_hospital(req: func.HttpRequest) -> func.HttpResponse:
    return execute_tool(req)

# ... add similar wrappers for all existing endpoints
```

#### Task 3.3: Update gradient-agents/main.py

**File**: `gradient-agents/main.py`

Key changes:
- Import from `src.core.tool_registry`
- Use `registry.get_openai_tools()` for LLM

```python
"""
Referral Network Agent using Gradient ADK.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import httpx
from typing import Dict, List, Any

from dotenv import load_dotenv
from gradient import AsyncGradient
from gradient_adk import entrypoint

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Import from core - NEW
from src.core.tool_registry import ToolRegistry
from src.prompts.system_prompts import SYSTEM_PROMPT

# Initialize registry
_registry = None

def get_registry():
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load_domains()
    return _registry


def get_tools_schema() -> List[Dict]:
    """Get tool definitions in OpenAI format."""
    return get_registry().get_openai_tools()


# ... rest of file with same pattern
```

### Phase 4: Update Build Infrastructure

#### Task 4.1: Update Makefile

**File**: `Makefile` (add new targets)

```makefile
# Add after existing targets

# Configuration validation
validate-config:
	python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); r.load_domains(); print('Config valid, loaded', len(r.list_tools()), 'tools')"

list-tools:
	python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); r.load_domains(); print('\\n'.join(r.list_tools()))"

list-domains:
	python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); print('\\n'.join(r.get_enabled_domains()))"

# Test by domain
test-domain:
	pytest tests/domains/$(DOMAIN)/ -v

test-core:
	pytest tests/core/ -v
```

#### Task 4.2: Update pyproject.toml

**File**: `pyproject.toml` (update package discovery)

```toml
[project]
name = "referral-network-demo"
version = "2.0.0"  # Bump version
# ... rest stays same

dependencies = [
    "gremlinpython>=3.7.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",  # Add for config loading
]

[tool.setuptools.packages.find]
where = ["."]
include = ["src*", "cli*", "scripts*", "config*"]  # Add config
```

#### Task 4.3: Update requirements.txt

**File**: `requirements.txt`

```
gremlinpython>=3.7.0
python-dotenv>=1.0.0
PyYAML>=6.0
```

### Phase 5: Create Tests

#### Task 5.1: Create tests/conftest.py

**File**: `tests/conftest.py`

```python
"""Shared test fixtures for the referral network platform."""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from src.core.tool_registry import ToolRegistry


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Minimal valid configuration for testing."""
    return {
        "version": "1.0",
        "domains": {
            "test_domain": {
                "enabled": True,
                "name": "Test Domain",
                "module": "tests.fixtures.test_domain",
                "tools": ["test_tool"],
                "depends_on": [],
            }
        }
    }


@pytest.fixture
def mock_gremlin_client():
    """Mock Gremlin client for unit tests."""
    client = MagicMock()
    client.submitAsync.return_value.result.return_value.all.return_value.result.return_value = []
    return client


@pytest.fixture
def tool_registry(tmp_path, mock_config):
    """Provide a tool registry with test configuration."""
    import yaml

    config_path = tmp_path / "domains.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(mock_config, f)

    return ToolRegistry(config_path=str(config_path))
```

#### Task 5.2: Create tests/core/test_tool_registry.py

**File**: `tests/core/test_tool_registry.py`

```python
"""Tests for the tool registry."""
import pytest
from unittest.mock import patch, MagicMock

from src.core.tool_registry import ToolRegistry
from src.core.exceptions import (
    ConfigurationError,
    DomainNotFoundError,
    ToolNotFoundError,
    DependencyError,
)


class TestToolRegistry:
    """Test suite for ToolRegistry."""

    def test_init_loads_config(self, tool_registry):
        """Registry should load config on initialization."""
        assert tool_registry.config is not None
        assert "domains" in tool_registry.config

    def test_missing_config_raises_error(self, tmp_path):
        """Missing config file should raise ConfigurationError."""
        with pytest.raises(ConfigurationError):
            ToolRegistry(config_path=str(tmp_path / "nonexistent.yaml"))

    def test_get_enabled_domains(self, tool_registry):
        """Should return list of enabled domains."""
        domains = tool_registry.get_enabled_domains()
        assert "test_domain" in domains

    def test_dependency_resolution_order(self, tmp_path):
        """Dependencies should be loaded before dependents."""
        import yaml

        config = {
            "version": "1.0",
            "domains": {
                "base": {
                    "enabled": True,
                    "module": "tests.fixtures.base",
                    "tools": [],
                    "depends_on": [],
                },
                "dependent": {
                    "enabled": True,
                    "module": "tests.fixtures.dependent",
                    "tools": [],
                    "depends_on": ["base"],
                }
            }
        }

        config_path = tmp_path / "domains.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        registry = ToolRegistry(config_path=str(config_path))
        domains = registry.get_enabled_domains()

        assert domains.index("base") < domains.index("dependent")

    def test_circular_dependency_raises_error(self, tmp_path):
        """Circular dependencies should raise DependencyError."""
        import yaml

        config = {
            "version": "1.0",
            "domains": {
                "a": {"enabled": True, "module": "a", "tools": [], "depends_on": ["b"]},
                "b": {"enabled": True, "module": "b", "tools": [], "depends_on": ["a"]},
            }
        }

        config_path = tmp_path / "domains.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        registry = ToolRegistry(config_path=str(config_path))

        with pytest.raises(DependencyError):
            registry.get_enabled_domains()

    def test_get_tool_not_found(self, tool_registry):
        """Getting nonexistent tool should raise ToolNotFoundError."""
        with pytest.raises(ToolNotFoundError):
            tool_registry.get_tool("nonexistent_tool")


class TestToolRegistryIntegration:
    """Integration tests with real domain modules."""

    @pytest.mark.integration
    def test_loads_referral_network_domain(self):
        """Should load the referral network domain successfully."""
        registry = ToolRegistry()
        registry.load_domains()

        tools = registry.list_tools()
        assert "find_hospital" in tools
        assert "get_network_statistics" in tools

    @pytest.mark.integration
    def test_tool_definitions_format(self):
        """Tool definitions should have required fields."""
        registry = ToolRegistry()
        registry.load_domains()

        definitions = registry.get_tool_definitions()

        for tool_def in definitions:
            assert "name" in tool_def
            assert "description" in tool_def
            assert "parameters" in tool_def
```

### Phase 6: Update Documentation

#### Task 6.1: Create docs/architecture.md

**File**: `docs/architecture.md`

```markdown
# Architecture Overview

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  cli/run_agent.py  │  gradient-agents/  │  azure-functions/ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Infrastructure                       │
│           src/core/tool_registry.py                         │
│           src/core/cosmos_connection.py                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Domain Modules                            │
│           src/domains/referral_network/                     │
│           src/domains/quality_improvement/ (future)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│           Azure Cosmos DB (Gremlin API)                     │
└─────────────────────────────────────────────────────────────┘
```

## Tool Registry Pattern

The `ToolRegistry` class provides dynamic tool discovery and loading:

1. Loads `config/domains.yaml` on initialization
2. Resolves domain dependencies (topological sort)
3. Dynamically imports enabled domain modules
4. Provides unified access to tools and definitions

## Adding New Domains

See [adding_domains.md](adding_domains.md) for a complete guide.
```

#### Task 6.2: Create docs/adding_domains.md

**File**: `docs/adding_domains.md`

```markdown
# Adding New Analytics Domains

## Quick Start

1. Create domain directory: `src/domains/your_domain/`
2. Add to `config/domains.yaml`
3. Implement `tools.py` with `TOOLS` and `TOOL_DEFINITIONS`
4. Run `make validate-config`

## Domain Module Structure

```
src/domains/your_domain/
├── __init__.py          # Export TOOLS and TOOL_DEFINITIONS
├── tools.py             # Tool implementations and definitions
├── diagrams.py          # Optional: Mermaid generators
├── schema.py            # Optional: Vertex/edge documentation
└── sample_data.py       # Optional: Test data loader
```

## Required Exports

Your `tools.py` must export:

```python
TOOLS: Dict[str, Callable] = {
    "your_tool": your_tool_function,
}

TOOL_DEFINITIONS: List[Dict] = [
    {
        "name": "your_tool",
        "description": "What the tool does",
        "parameters": {
            "type": "object",
            "properties": {...},
        }
    },
]
```

## Configuration

Add to `config/domains.yaml`:

```yaml
domains:
  your_domain:
    enabled: true
    name: "Your Domain Name"
    module: "src.domains.your_domain"
    depends_on: []  # or list of domain names
    tools:
      - your_tool
```
```

---

## 4. Validation Gates

### 4.1 Syntax and Style Checks

```bash
# Check Python syntax
python -m py_compile src/core/tool_registry.py
python -m py_compile src/domains/referral_network/tools.py

# Format check (if black installed)
black --check src/ --line-length 100

# Type check (if mypy installed)
mypy src/core/tool_registry.py --ignore-missing-imports
```

### 4.2 Configuration Validation

```bash
# Validate config loads without errors
python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); print('Config loaded')"

# Validate domains load
python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); r.load_domains(); print('Loaded', len(r.list_tools()), 'tools')"
```

### 4.3 Functional Tests

```bash
# List all tools (should show 11 tools)
make list-tools

# Test database connection
python run_agent.py --test

# Run test suite
pytest tests/ -v

# Run specific domain tests
pytest tests/domains/referral_network/ -v
```

### 4.4 Integration Tests

```bash
# Test Azure Functions locally
cd azure-functions && func start &
sleep 5
curl -X POST http://localhost:7071/api/tools/get_network_statistics
pkill -f "func start"

# Test CLI with registry
python cli/run_agent.py --test
```

---

## 5. Rollback Strategy

If issues arise:

1. **Immediate**: Keep old `src/tools/` as fallback, consumers can import from there
2. **Config toggle**: Add `use_legacy: true` flag to domains.yaml to bypass registry
3. **Branch**: Work on `feature/modular-architecture` branch, only merge when stable

---

## 6. External References

### Python Plugin Architecture
- [Python Packaging Guide - Plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
- [Registry Pattern Reference](https://github.com/SughoshKulkarni/Python-Registry)
- [Dynamic Module Loading](https://pytutorial.com/python-runtime-module-loading-with-importlibimport_module/)

### YAML Configuration
- [PyYAML Best Practices](https://python.land/data-processing/python-yaml)
- [Python Configuration Guide](https://betterstack.com/community/guides/scaling-python/yaml-files-in-python/)

### Existing Codebase Patterns
- Tool definition pattern: `src/tools/definitions.py:6-93`
- Query implementation pattern: `src/tools/queries.py:39-73`
- Azure Functions route pattern: `azure-functions/function_app.py:83-99`
- Diagram generation pattern: `src/tools/diagram_generators.py:114-232`

---

## 7. Task Checklist

### Phase 1: Core Infrastructure
- [ ] Create `config/domains.yaml`
- [ ] Create `src/core/__init__.py`
- [ ] Move `src/cosmos_connection.py` → `src/core/cosmos_connection.py`
- [ ] Create `src/core/exceptions.py`
- [ ] Create `src/core/tool_registry.py`
- [ ] Create `src/core/diagram_base.py`

### Phase 2: Domain Module
- [ ] Create `src/domains/__init__.py`
- [ ] Create `src/domains/referral_network/__init__.py`
- [ ] Create `src/domains/referral_network/tools.py` (consolidate definitions + queries)
- [ ] Move `src/tools/diagram_generators.py` → `src/domains/referral_network/diagrams.py`
- [ ] Create `src/domains/referral_network/schema.py`

### Phase 3: Update Consumers
- [ ] Update `cli/run_agent.py` to use ToolRegistry
- [ ] Update `cli/network_cli.py` to use ToolRegistry
- [ ] Update `azure-functions/function_app.py` to use ToolRegistry
- [ ] Update `gradient-agents/main.py` to use ToolRegistry

### Phase 4: Build Infrastructure
- [ ] Update `Makefile` with new targets
- [ ] Update `pyproject.toml` (version bump, add pyyaml)
- [ ] Update `requirements.txt` (add pyyaml)

### Phase 5: Tests
- [ ] Create `tests/__init__.py`
- [ ] Create `tests/conftest.py`
- [ ] Create `tests/core/test_tool_registry.py`

### Phase 6: Documentation
- [ ] Create `docs/architecture.md`
- [ ] Create `docs/adding_domains.md`
- [ ] Update `README.md` with new structure

### Phase 7: Cleanup
- [ ] Remove deprecated `src/tools/` after migration verified
- [ ] Run full test suite
- [ ] Test all consumers (CLI, Azure Functions, Gradient)

---

## 8. Quality Score

**Confidence Level: 8/10**

**Strengths:**
- Detailed code examples from existing codebase
- Clear task ordering with dependencies
- Comprehensive validation gates
- Rollback strategy included

**Risks:**
- Azure Functions deployment path complexity (needs `src/` copied)
- Diagram generators have 579 lines to migrate
- No existing tests to verify non-regression

**Mitigation:**
- Phase work incrementally, test after each phase
- Keep old `src/tools/` as fallback during transition
- Add integration tests before removing deprecated code
