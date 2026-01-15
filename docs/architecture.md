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

## Directory Structure

```
referral-network-demo/
├── config/                         # Configuration files
│   └── domains.yaml                # Domain enable/disable and tool lists
│
├── src/
│   ├── core/                       # Shared infrastructure
│   │   ├── __init__.py
│   │   ├── cosmos_connection.py    # Database connection helper
│   │   ├── tool_registry.py        # Dynamic tool registration
│   │   ├── diagram_base.py         # Base diagram utilities
│   │   └── exceptions.py           # Custom exceptions
│   │
│   ├── domains/                    # Feature modules
│   │   └── referral_network/       # Referral network analytics
│   │       ├── __init__.py
│   │       ├── tools.py            # Tool implementations
│   │       ├── diagrams.py         # Mermaid diagram generators
│   │       └── schema.py           # Vertex/edge type definitions
│   │
│   └── prompts/                    # Shared across domains
│       └── system_prompts.py
│
├── tests/                          # Test infrastructure
│   ├── conftest.py                 # Shared fixtures
│   ├── core/
│   │   └── test_tool_registry.py
│   └── domains/
│       └── referral_network/
│
└── docs/
    ├── architecture.md             # This file
    └── adding_domains.md           # Guide for new domains
```

## Tool Registry Pattern

The `ToolRegistry` class provides dynamic tool discovery and loading:

1. **Configuration Loading**: Loads `config/domains.yaml` on initialization
2. **Dependency Resolution**: Resolves domain dependencies using topological sort
3. **Dynamic Import**: Dynamically imports enabled domain modules
4. **Unified Access**: Provides unified access to tools and definitions

### Usage

```python
from src.core.tool_registry import ToolRegistry

# Initialize and load
registry = ToolRegistry()
registry.load_domains()

# Get all tools
tools = registry.get_all_tools()
result = tools["find_hospital"](name="Children's")

# Get tool definitions for LLM
definitions = registry.get_tool_definitions()

# Get OpenAI-compatible format
openai_tools = registry.get_openai_tools()
```

## Domain Module Structure

Each domain module must provide:

- `tools.py`: Contains `TOOLS` dict and `TOOL_DEFINITIONS` list
- Optional: `diagrams.py`, `schema.py`, `sample_data.py`

### Required Exports

```python
# tools.py
TOOLS: Dict[str, Callable] = {
    "tool_name": tool_function,
}

TOOL_DEFINITIONS: List[Dict] = [
    {
        "name": "tool_name",
        "description": "What the tool does",
        "parameters": {...}
    },
]
```

## Configuration

Domain configuration in `config/domains.yaml`:

```yaml
version: "1.0"

domains:
  domain_name:
    enabled: true
    name: "Human-readable name"
    description: "What this domain does"
    version: "1.0.0"
    depends_on: []  # List of dependency domain names
    module: "src.domains.domain_name"
    tools:
      - tool_name_1
      - tool_name_2
```

## Adding New Domains

See [adding_domains.md](adding_domains.md) for a complete guide.
