# Adding New Analytics Domains

This guide explains how to add new analytics domains to the platform.

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

## Step-by-Step Guide

### 1. Create the Domain Directory

```bash
mkdir -p src/domains/your_domain
```

### 2. Create `__init__.py`

```python
"""
Your Domain Name.

Description of what this domain does.
"""
from src.domains.your_domain.tools import TOOLS, TOOL_DEFINITIONS

__all__ = ["TOOLS", "TOOL_DEFINITIONS"]
```

### 3. Create `tools.py`

```python
"""
Your domain tools.

Tool implementations and definitions.
"""
from typing import Dict, List, Any, Callable
from src.core.cosmos_connection import get_client, execute_query


# Tool implementations
def your_tool(param1: str, param2: int = 10) -> List[Dict]:
    """
    Description of what the tool does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
    # Implementation here
    pass


# Registry exports
TOOLS: Dict[str, Callable] = {
    "your_tool": your_tool,
}

TOOL_DEFINITIONS: List[Dict] = [
    {
        "name": "your_tool",
        "description": "Description for the LLM",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of param1"
                },
                "param2": {
                    "type": "integer",
                    "description": "Description of param2",
                    "default": 10
                }
            },
            "required": ["param1"]
        }
    },
]
```

### 4. Add to Configuration

Add your domain to `config/domains.yaml`:

```yaml
domains:
  # ... existing domains ...

  your_domain:
    enabled: true
    name: "Your Domain Name"
    description: "What this domain does"
    version: "1.0.0"
    depends_on: []  # or ["referral_network"] if it depends on another domain
    module: "src.domains.your_domain"
    tools:
      - your_tool
```

### 5. Validate

```bash
# Check configuration loads correctly
make validate-config

# List all tools (should include your new tool)
make list-tools

# List enabled domains
make list-domains
```

## Adding Diagram Generators

If your domain needs visualization:

### 1. Create `diagrams.py`

```python
"""
Mermaid diagram generators for your domain.
"""
from typing import Dict, List, Optional
from src.core.diagram_base import sanitize_node_id, escape_label, COLORS


def generate_your_diagram(
    data: List[Dict],
    title: Optional[str] = None
) -> str:
    """Generate a Mermaid diagram."""
    lines = ["graph TD"]

    # Build diagram...

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"
```

### 2. Import in `tools.py`

```python
from src.domains.your_domain.diagrams import generate_your_diagram

TOOLS["generate_your_diagram"] = generate_your_diagram

TOOL_DEFINITIONS.append({
    "name": "generate_your_diagram",
    "description": "Generate a diagram...",
    "parameters": {...}
})
```

### 3. Add to Configuration

```yaml
tools:
  - your_tool
  - generate_your_diagram  # Add diagram tool
```

## Domain Dependencies

If your domain depends on another domain's tools:

```yaml
domains:
  your_domain:
    depends_on: ["referral_network"]
```

The registry will:
1. Load `referral_network` first
2. Then load `your_domain`
3. Detect circular dependencies and raise an error

## Testing Your Domain

### 1. Create Test Directory

```bash
mkdir -p tests/domains/your_domain
touch tests/domains/your_domain/__init__.py
```

### 2. Create Tests

```python
# tests/domains/your_domain/test_tools.py
import pytest
from src.core.tool_registry import ToolRegistry


class TestYourDomainTools:
    @pytest.fixture
    def registry(self):
        registry = ToolRegistry()
        registry.load_domains()
        return registry

    def test_your_tool_registered(self, registry):
        tools = registry.list_tools()
        assert "your_tool" in tools

    @pytest.mark.integration
    def test_your_tool_works(self, registry):
        tool = registry.get_tool("your_tool")
        result = tool(param1="test")
        assert result is not None
```

### 3. Run Tests

```bash
make test-domain DOMAIN=your_domain
```

## Best Practices

1. **Single Responsibility**: Each tool should do one thing well
2. **Clear Documentation**: Document parameters and return values
3. **Error Handling**: Return helpful error messages
4. **Consistent Naming**: Use snake_case for tool names
5. **Schema Documentation**: Create `schema.py` if adding new vertex/edge types
6. **Sample Data**: Create `sample_data.py` for testing
