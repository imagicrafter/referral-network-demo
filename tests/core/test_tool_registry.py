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

    def test_disabled_domain_not_loaded(self, tmp_path):
        """Disabled domains should not appear in enabled list."""
        import yaml

        config = {
            "version": "1.0",
            "domains": {
                "enabled_domain": {
                    "enabled": True,
                    "module": "a",
                    "tools": [],
                    "depends_on": [],
                },
                "disabled_domain": {
                    "enabled": False,
                    "module": "b",
                    "tools": [],
                    "depends_on": [],
                }
            }
        }

        config_path = tmp_path / "domains.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        registry = ToolRegistry(config_path=str(config_path))
        domains = registry.get_enabled_domains()

        assert "enabled_domain" in domains
        assert "disabled_domain" not in domains


class TestToolRegistryIntegration:
    """Integration tests with real domain modules."""

    @pytest.mark.integration
    def test_loads_referral_network_domain(self, real_registry):
        """Should load the referral network domain successfully."""
        real_registry.load_domains()

        tools = real_registry.list_tools()
        assert "find_hospital" in tools
        assert "get_network_statistics" in tools
        assert len(tools) == 11  # Expected number of tools

    @pytest.mark.integration
    def test_tool_definitions_format(self, real_registry):
        """Tool definitions should have required fields."""
        real_registry.load_domains()

        definitions = real_registry.get_tool_definitions()

        for tool_def in definitions:
            assert "name" in tool_def
            assert "description" in tool_def
            assert "parameters" in tool_def

    @pytest.mark.integration
    def test_openai_tools_format(self, real_registry):
        """OpenAI tools format should have proper wrapper."""
        real_registry.load_domains()

        openai_tools = real_registry.get_openai_tools()

        for tool in openai_tools:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    @pytest.mark.integration
    def test_get_domain_info(self, real_registry):
        """Should return domain configuration."""
        info = real_registry.get_domain_info("referral_network")

        assert info["enabled"] is True
        assert info["name"] == "Referral Network Analytics"
        assert "tools" in info
        assert len(info["tools"]) == 11
