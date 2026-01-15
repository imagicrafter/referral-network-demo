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


@pytest.fixture
def real_registry():
    """Provide a tool registry with actual production configuration."""
    return ToolRegistry()
