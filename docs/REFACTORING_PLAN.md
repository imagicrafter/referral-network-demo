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

### Phase 1: Security & Critical Fixes (Do First) - COMPLETED

**1.1 Remove secrets from git history**
- [x] Create `.env.example` at root with placeholder values
- [x] Update `.gitignore` to ensure `.env` is excluded
- [x] Verified `.env` is not tracked in git

**1.2 Delete obsolete file**
- [x] Delete `referral_agent.py` (superseded by `run_agent.py --azure`)

**Files modified:**
- Created: `.env.example`
- Verified: `.gitignore` (already correct)
- Deleted: `referral_agent.py`

---

### Phase 2: Create Shared Module Structure - COMPLETED

**2.1 Create `src/` directory with shared code**
- [x] Created `src/__init__.py`
- [x] Created `src/cosmos_connection.py` (merged with conditional dotenv loading)
- [x] Created `src/tools/__init__.py`
- [x] Created `src/tools/definitions.py` (extracted TOOL_DEFINITIONS)
- [x] Created `src/tools/queries.py` (extracted query functions)
- [x] Created `src/tools/diagram_generators.py` (copied from azure-functions/)
- [x] Created `src/prompts/__init__.py`
- [x] Created `src/prompts/system_prompts.py` (extracted shared prompts)

**Structure created:**
```
src/
├── __init__.py
├── cosmos_connection.py      # Merged from both locations
├── tools/
│   ├── __init__.py
│   ├── definitions.py        # TOOL_DEFINITIONS + get_tool_functions()
│   ├── queries.py            # All query functions
│   └── diagram_generators.py # Mermaid diagram generators
└── prompts/
    ├── __init__.py
    └── system_prompts.py     # SYSTEM_PROMPT + HOSPITAL_LIST
```

**Key improvements:**
- `cosmos_connection.py`: Loads dotenv only if not in Azure Functions (checks FUNCTIONS_WORKER_RUNTIME)
- `definitions.py`: Includes `get_tool_functions()` helper for easy function mapping
- `system_prompts.py`: Separates HOSPITAL_LIST for reuse

**Files to delete (in Phase 3 after consumers updated):**
- `/cosmos_connection.py` (moved to src/)
- `/agent_tools.py` (split into src/tools/)
- `/azure-functions/cosmos_connection.py`
- `/azure-functions/diagram_generators.py`

---

### Phase 3: Update Consumers - COMPLETED

**3.1 Update Azure Functions**
- [x] Refactored `function_app.py` to import from `src.tools.queries`
- [x] Each endpoint is now a thin wrapper (~10 lines instead of ~50)
- [x] Reduced from 576 lines to 349 lines (~40% reduction)

**3.2 Update CLI tools**
- [x] Created `cli/` directory
- [x] Created `cli/run_agent.py` with imports from `src/`
- [x] Created `cli/network_cli.py` with imports from `src/`
- [x] Created backward-compatible wrappers at root (`run_agent.py`, `network_cli.py`)

**3.3 Update Gradient Agent**
- [x] Updated `gradient-agents/main.py` to import from `src/`
- [x] Reduced from 300 lines to 195 lines (~35% reduction)

**3.4 Open WebUI Pipes**
- [ ] Pipes remain standalone (embedded definitions) - Open WebUI requires standalone files

**Files deleted (consolidated into src/):**
- `/cosmos_connection.py`
- `/agent_tools.py`
- `/azure-functions/cosmos_connection.py`
- `/azure-functions/diagram_generators.py`

---

### Phase 4: Organize Utility Scripts - COMPLETED

**4.1 Create scripts/ directory**
- [x] Created `scripts/` directory
- [x] Moved `load_sample_data.py` → `scripts/load_sample_data.py`
- [x] Moved `explore_graph.py` → `scripts/explore_graph.py`
- [x] Moved `export_for_powerbi.py` → `scripts/export_for_powerbi.py`
- [x] Updated all scripts to import from `src/`

**Files created:**
- `scripts/load_sample_data.py`
- `scripts/explore_graph.py`
- `scripts/export_for_powerbi.py`

---

### Phase 5: Project Configuration - COMPLETED

**5.1 Create pyproject.toml**
- [x] Created with project metadata, dependencies, optional dependencies
- [x] Configured pytest, black, isort, mypy settings

**5.2 Create root requirements.txt**
- [x] Consolidated dependencies: gremlinpython, python-dotenv, openai, gradient, httpx, pydantic

**5.3 Create requirements-dev.txt**
- [x] Added pytest, pytest-asyncio, pytest-cov, black, isort, mypy, pylint, flake8

**5.4 Create Makefile**
- [x] Created with targets: install, test, lint, format, typecheck, clean
- [x] Added run-agent, deploy-azure, load-data targets

**Files created:**
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
