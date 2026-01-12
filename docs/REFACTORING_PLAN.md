# Refactoring Plan: referral-network-demo

## Overview

Reorganize the codebase to eliminate ~45% code duplication, fix security issues, and establish a standard Python project structure.

## Current Issues Summary

1. **Code Duplication**: `cosmos_connection.py` duplicated, Gremlin queries duplicated between `agent_tools.py` and `function_app.py`
2. **Security**: `.env` with credentials tracked in git
3. **Obsolete Files**: `referral_agent.py` superseded by `run_agent.py`
4. **No Tests**: Zero test coverage
5. **No CI/CD**: Manual deployments only
6. **Scattered Config**: Multiple `.env` files, no root `requirements.txt`

---

## Proposed Directory Structure

```
referral-network-demo/
├── src/                          # Shared source code
│   ├── __init__.py
│   ├── cosmos_connection.py      # Single source for DB connection
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── definitions.py        # Tool definitions (shared across all consumers)
│   │   ├── queries.py            # Gremlin query implementations
│   │   └── diagram_generators.py # Mermaid diagram logic (moved from azure-functions/)
│   └── prompts/
│       ├── __init__.py
│       └── system_prompts.py     # Shared system prompts
│
├── cli/                          # CLI tools
│   ├── run_agent.py              # Unified agent launcher
│   ├── network_cli.py            # CLI interface
│   └── __init__.py
│
├── scripts/                      # Utility scripts
│   ├── load_sample_data.py
│   ├── explore_graph.py
│   └── export_for_powerbi.py
│
├── azure-functions/              # Azure Functions (backend API)
│   ├── function_app.py           # HTTP wrappers only (imports from src/)
│   ├── host.json
│   ├── requirements.txt
│   └── local.settings.json.example
│
├── gradient-agents/              # Gradient ADK agent
│   ├── main.py                   # ADK agent (imports from src/)
│   ├── .gradient/agent.yml
│   ├── requirements.txt
│   └── .env.example
│
├── pipes/                        # Open WebUI integration
│   ├── gradient-inference-pipe.py
│   └── do-function-pipe.py
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_queries.py
│   │   ├── test_diagram_generators.py
│   │   └── test_tools.py
│   └── integration/
│       └── test_api_endpoints.py
│
├── docs/
│   ├── azure_service_dependencies.md
│   ├── ARCHITECTURE.md           # New: Architecture overview
│   └── API.md                    # New: API documentation
│
├── .github/workflows/            # CI/CD
│   └── test.yml
│
├── .env.example                  # Environment template (no secrets)
├── .gitignore                    # Updated to exclude .env
├── pyproject.toml                # Project configuration
├── requirements.txt              # Root dependencies
├── requirements-dev.txt          # Dev dependencies (pytest, black, etc.)
├── README.md
├── DEPLOY.md
└── Makefile                      # Common tasks
```

---

## Implementation Phases

### Phase 1: Security & Critical Fixes (Do First)

**1.1 Remove secrets from git history**
- Create `.env.example` at root with placeholder values
- Update `.gitignore` to ensure `.env` is excluded
- Remove `.env` from tracking: `git rm --cached .env`

**1.2 Delete obsolete file**
- Delete `referral_agent.py` (superseded by `run_agent.py --azure`)

**Files to modify:**
- Create: `.env.example`
- Modify: `.gitignore`
- Delete: `referral_agent.py`

---

### Phase 2: Create Shared Module Structure

**2.1 Create `src/` directory with shared code**

```
src/
├── __init__.py
├── cosmos_connection.py      # Merged from both locations
├── tools/
│   ├── __init__.py
│   ├── definitions.py        # Extract TOOL_DEFINITIONS from agent_tools.py
│   ├── queries.py            # Extract query functions from agent_tools.py
│   └── diagram_generators.py # Move from azure-functions/
└── prompts/
    ├── __init__.py
    └── system_prompts.py     # Extract from run_agent.py, main.py
```

**2.2 Consolidate cosmos_connection.py**
- Merge `/cosmos_connection.py` and `/azure-functions/cosmos_connection.py`
- Handle dotenv conditionally based on environment

**2.3 Extract tool definitions**
- Move `TOOL_DEFINITIONS` from `agent_tools.py` to `src/tools/definitions.py`
- Both CLI and Azure Functions import from here

**2.4 Extract query implementations**
- Move query functions to `src/tools/queries.py`
- `function_app.py` imports and wraps these (removes ~200 lines of duplication)

**2.5 Move diagram generators**
- Move `azure-functions/diagram_generators.py` to `src/tools/diagram_generators.py`
- Update imports in `function_app.py`

**Files to create:**
- `src/__init__.py`
- `src/cosmos_connection.py`
- `src/tools/__init__.py`
- `src/tools/definitions.py`
- `src/tools/queries.py`
- `src/tools/diagram_generators.py`
- `src/prompts/__init__.py`
- `src/prompts/system_prompts.py`

**Files to modify:**
- `azure-functions/function_app.py` (import from src, remove duplicated code)
- `run_agent.py` (import from src)
- Delete: `/cosmos_connection.py` (moved to src/)
- Delete: `/agent_tools.py` (split into src/tools/)
- Delete: `/azure-functions/cosmos_connection.py`
- Delete: `/azure-functions/diagram_generators.py`

---

### Phase 3: Update Consumers

**3.1 Update Azure Functions**
- Refactor `function_app.py` to import from `src.tools.queries`
- Each endpoint becomes a thin wrapper (~10 lines instead of ~50)

**3.2 Update CLI tools**
- Update `run_agent.py` to import from `src/`
- Move to `cli/` directory

**3.3 Update Gradient Agent**
- Update `gradient-agents/main.py` to import from `src/`

**3.4 Update Open WebUI Pipes**
- Update pipes to import tool definitions from `src/`
- Note: Pipes are standalone files for Open WebUI, may need embedded definitions

**Files to modify:**
- `azure-functions/function_app.py`
- `run_agent.py` → `cli/run_agent.py`
- `network_cli.py` → `cli/network_cli.py`
- `gradient-agents/main.py`
- `pipes/gradient-inference-pipe.py`
- `pipes/do-function-pipe.py`

---

### Phase 4: Organize Utility Scripts

**4.1 Create scripts/ directory**
- Move: `load_sample_data.py` → `scripts/load_sample_data.py`
- Move: `explore_graph.py` → `scripts/explore_graph.py`
- Move: `export_for_powerbi.py` → `scripts/export_for_powerbi.py`
- Update imports to use `src/`

---

### Phase 5: Project Configuration

**5.1 Create pyproject.toml**
```toml
[project]
name = "referral-network-demo"
version = "1.0.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**5.2 Create root requirements.txt**
- Consolidate dependencies from all subdirectories

**5.3 Create requirements-dev.txt**
- pytest, black, isort, mypy, pylint

**5.4 Create Makefile**
```makefile
test:
    pytest tests/

lint:
    black --check .
    isort --check .

deploy-azure:
    cd azure-functions && func azure functionapp publish referral-network-api --python
```

**Files to create:**
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `Makefile`

---

### Phase 6: Add Tests (Optional - Recommend for Later)

**6.1 Create test infrastructure**
- `tests/conftest.py` with fixtures
- `tests/unit/test_queries.py`
- `tests/unit/test_diagram_generators.py`

**6.2 Add CI/CD**
- `.github/workflows/test.yml`

---

## Critical Files to Modify

| File | Action | Lines Changed (est.) |
|------|--------|---------------------|
| `azure-functions/function_app.py` | Refactor to import from src | -300 |
| `run_agent.py` | Move to cli/, update imports | ~50 |
| `agent_tools.py` | Split into src/tools/ | Delete (moved) |
| `cosmos_connection.py` (root) | Move to src/ | Delete (moved) |
| `cosmos_connection.py` (azure) | Delete (consolidated) | Delete |
| `referral_agent.py` | Delete (obsolete) | Delete |
| `gradient-agents/main.py` | Update imports | ~30 |
| `.gitignore` | Add .env exclusion | ~5 |

---

## Verification Steps

1. **After Phase 1:**
   - Verify `.env` is not tracked: `git status`
   - Verify app still runs: `python run_agent.py --test`

2. **After Phase 2-3:**
   - Test Azure Functions locally: `cd azure-functions && func start`
   - Test CLI: `python cli/run_agent.py --test`
   - Test API endpoints manually

3. **After Phase 4-5:**
   - Run `make test` (if tests added)
   - Deploy to Azure: `make deploy-azure`
   - Test in Open WebUI with updated pipe

4. **Full Integration Test:**
   - Ask agent: "Show me a diagram of the referral network"
   - Verify diagram renders correctly in Open WebUI

---

## Estimated Effort

| Phase | Effort | Risk |
|-------|--------|------|
| Phase 1: Security | 30 min | Low |
| Phase 2: Shared modules | 2-3 hours | Medium |
| Phase 3: Update consumers | 1-2 hours | Medium |
| Phase 4: Organize scripts | 30 min | Low |
| Phase 5: Project config | 30 min | Low |
| Phase 6: Tests | 2-3 hours | Low |

**Total: ~6-9 hours**

---

## Notes

- **Pipes caveat**: Open WebUI pipes are standalone files. They may need tool definitions embedded rather than imported, depending on how Open WebUI loads them.
- **Azure Functions deployment**: After refactoring, ensure `src/` is included in the deployment package.
- **Backward compatibility**: Keep CLI entry points working (`python run_agent.py` should still work via symlink or wrapper).
