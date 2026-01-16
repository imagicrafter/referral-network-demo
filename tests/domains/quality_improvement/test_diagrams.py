"""Tests for quality improvement diagram generators."""
import pytest
from unittest.mock import patch, MagicMock


class TestAdoptionSpreadDiagram:
    """Tests for generate_adoption_spread_diagram."""

    @pytest.fixture
    def mock_execute_query(self):
        """Patch execute_query for diagram tests."""
        with patch('src.domains.quality_improvement.diagrams.execute_query') as mock:
            yield mock

    @pytest.fixture
    def mock_get_client(self):
        """Patch get_client for diagram tests."""
        with patch('src.domains.quality_improvement.diagrams.get_client') as mock:
            mock.return_value = MagicMock()
            yield mock

    def test_diagram_returns_mermaid_string(self, mock_get_client, mock_execute_query):
        """Diagram should return string wrapped in mermaid code fence."""
        mock_execute_query.side_effect = [
            # Release date
            ["2024-01-15"],
            # Adopters
            [
                {"hospital": "Hospital A", "adoption_date": "2024-02-15",
                 "compliance_rate": 94.2, "type": "tertiary"}
            ],
            # Influences
            []
        ]

        from src.domains.quality_improvement.diagrams import generate_adoption_spread_diagram

        result = generate_adoption_spread_diagram("Sepsis Bundle v2.0")

        assert result.startswith("```mermaid")
        assert result.endswith("```")
        assert "graph" in result

    def test_diagram_handles_empty_data(self, mock_get_client, mock_execute_query):
        """Diagram should handle case with no adoption data gracefully."""
        mock_execute_query.side_effect = [
            ["2024-01-15"],  # Release date
            [],  # No adopters
            []   # No influences
        ]

        from src.domains.quality_improvement.diagrams import generate_adoption_spread_diagram

        result = generate_adoption_spread_diagram("Unknown Protocol")

        assert "NO_DATA" in result or "No adoption data" in result

    def test_diagram_includes_wave_classification(self, mock_get_client, mock_execute_query):
        """Diagram with show_timeline should include wave subgraphs."""
        mock_execute_query.side_effect = [
            ["2024-01-15"],  # Release date
            [
                {"hospital": "Hospital A", "adoption_date": "2024-02-15",
                 "compliance_rate": 94.2, "type": "tertiary"},
                {"hospital": "Hospital B", "adoption_date": "2024-08-15",
                 "compliance_rate": 85.0, "type": "regional"}
            ],
            []  # No influences
        ]

        from src.domains.quality_improvement.diagrams import generate_adoption_spread_diagram

        result = generate_adoption_spread_diagram("Sepsis Bundle v2.0", show_timeline=True)

        assert "subgraph" in result
        assert "Early Adopters" in result or "early" in result


class TestDiagramHelpers:
    """Tests for diagram helper functions."""

    def test_classify_adoption_wave_early(self):
        """Should classify as early if within 6 months of release."""
        from src.domains.quality_improvement.diagrams import _classify_adoption_wave

        result = _classify_adoption_wave("2024-03-15", "2024-01-15")
        assert result == "early"

    def test_classify_adoption_wave_mid(self):
        """Should classify as mid if 6-12 months after release."""
        from src.domains.quality_improvement.diagrams import _classify_adoption_wave

        result = _classify_adoption_wave("2024-09-15", "2024-01-15")
        assert result == "mid"

    def test_classify_adoption_wave_late(self):
        """Should classify as late if 12+ months after release."""
        from src.domains.quality_improvement.diagrams import _classify_adoption_wave

        result = _classify_adoption_wave("2025-03-15", "2024-01-15")
        assert result == "late"

    def test_classify_adoption_wave_invalid_date(self):
        """Should return mid for invalid dates."""
        from src.domains.quality_improvement.diagrams import _classify_adoption_wave

        result = _classify_adoption_wave("invalid", "2024-01-15")
        assert result == "mid"
