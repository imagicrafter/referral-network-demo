"""Tests for quality improvement domain tools."""
import pytest
from unittest.mock import patch, MagicMock

from src.core.tool_registry import ToolRegistry


class TestQualityImprovementToolsRegistration:
    """Test that quality improvement tools are properly registered."""

    @pytest.fixture
    def registry(self):
        """Provide tool registry with all domains loaded."""
        registry = ToolRegistry()
        registry.load_domains()
        return registry

    def test_domain_enabled(self, registry):
        """Quality improvement domain should be in enabled domains."""
        domains = registry.get_enabled_domains()
        assert "quality_improvement" in domains

    def test_all_tools_registered(self, registry):
        """All quality improvement tools should be registered."""
        tools = registry.list_tools()

        expected_tools = [
            "get_protocol_adoption_status",
            "find_adoption_gaps",
            "get_protocol_spread_path",
            "find_quality_champions",
            "analyze_outcome_improvement",
            "generate_adoption_spread_diagram",
        ]

        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool '{tool_name}' not registered"

    def test_tool_definitions_complete(self, registry):
        """Tool definitions should have all required fields."""
        definitions = registry.get_tool_definitions()

        qi_tools = [
            "get_protocol_adoption_status",
            "find_adoption_gaps",
            "get_protocol_spread_path",
            "find_quality_champions",
            "analyze_outcome_improvement",
            "generate_adoption_spread_diagram",
        ]

        for tool_def in definitions:
            if tool_def["name"] in qi_tools:
                assert "name" in tool_def
                assert "description" in tool_def
                assert "parameters" in tool_def
                assert len(tool_def["description"]) > 20, f"Description too short for {tool_def['name']}"


class TestQualityImprovementToolsFunctionality:
    """Test quality improvement tool functionality with mocked database."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Gremlin client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def mock_execute_query(self, mock_client):
        """Patch execute_query to return mock data."""
        with patch('src.domains.quality_improvement.tools.execute_query') as mock:
            yield mock

    @pytest.fixture
    def mock_get_client(self, mock_client):
        """Patch get_client to return mock client."""
        with patch('src.domains.quality_improvement.tools.get_client') as mock:
            mock.return_value = mock_client
            yield mock

    def test_get_protocol_adoption_status_structure(self, mock_get_client, mock_execute_query):
        """get_protocol_adoption_status should return properly structured data."""
        # Setup mock responses
        mock_execute_query.side_effect = [
            # Protocol query result
            [{"name": ["Sepsis Bundle v2.0"], "release_date": ["2024-01-15"], "category": ["infection_control"]}],
            # Adopters query result
            [
                {"hospital": "Hospital A", "state": "MO", "type": "tertiary",
                 "adoption_date": "2024-02-15", "compliance_rate": 94.2, "phase": "full"}
            ],
            # Total hospitals count
            [8],
            # Non-adopters query result
            [{"hospital": "Hospital B", "state": "KS", "type": "community"}],
        ]

        from src.domains.quality_improvement.tools import get_protocol_adoption_status

        result = get_protocol_adoption_status("Sepsis Bundle v2.0")

        assert "protocol" in result
        assert "adoption_rate" in result
        assert "adopters" in result
        assert "non_adopters" in result
        assert "by_phase" in result

    def test_find_adoption_gaps_structure(self, mock_get_client, mock_execute_query):
        """find_adoption_gaps should return high-potential and isolated hospitals."""
        mock_execute_query.return_value = [
            {"hospital": "Hospital A", "state": "MO", "type": "regional", "adopter_connections": 3},
            {"hospital": "Hospital B", "state": "KS", "type": "community", "adopter_connections": 0},
        ]

        from src.domains.quality_improvement.tools import find_adoption_gaps

        result = find_adoption_gaps("Sepsis Bundle v2.0")

        assert "high_potential_targets" in result
        assert "isolated_hospitals" in result
        assert "summary" in result

    def test_find_quality_champions_structure(self, mock_get_client, mock_execute_query):
        """find_quality_champions should return ranked list of champions."""
        mock_execute_query.return_value = [
            {"hospital": "Hospital A", "state": "MO", "influenced_count": 5,
             "protocols": ["Sepsis Bundle"], "methods": {"site_visit": 3, "webinar": 2}}
        ]

        from src.domains.quality_improvement.tools import find_quality_champions

        result = find_quality_champions()

        assert "champions" in result
        assert "total_champions_identified" in result


class TestQualityImprovementToolsIntegration:
    """Integration tests requiring live database connection."""

    @pytest.mark.integration
    def test_get_protocol_adoption_status_live(self):
        """Test get_protocol_adoption_status with live database."""
        registry = ToolRegistry()
        registry.load_domains()

        tool = registry.get_tool("get_protocol_adoption_status")
        result = tool("Sepsis Bundle v2.0")

        # Should return valid structure even if no data
        assert isinstance(result, dict)
        assert "protocol" in result or "error" in result

    @pytest.mark.integration
    def test_find_quality_champions_live(self):
        """Test find_quality_champions with live database."""
        registry = ToolRegistry()
        registry.load_domains()

        tool = registry.get_tool("find_quality_champions")
        result = tool()

        assert isinstance(result, dict)
        assert "champions" in result
