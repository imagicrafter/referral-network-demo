"""
Schema definitions for the quality improvement domain.

Documents vertex and edge types stored in Cosmos DB Gremlin.
These types build on the referral_network domain's hospital vertices.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class VertexType:
    """Definition of a vertex type in the graph."""
    label: str
    description: str
    properties: Dict[str, str]
    partition_key_pattern: str


@dataclass
class EdgeType:
    """Definition of an edge type in the graph."""
    label: str
    description: str
    from_vertex: str
    to_vertex: str
    properties: Dict[str, str]


# =============================================================================
# Vertex Types
# =============================================================================

PROTOCOL = VertexType(
    label="protocol",
    description="Quality improvement protocol or care bundle",
    properties={
        "id": "Unique identifier (e.g., 'proto-001')",
        "name": "Protocol name (e.g., 'Sepsis Bundle v2.0')",
        "category": "Category: infection_control, safety, clinical_pathway, documentation, medication_safety",
        "release_date": "Release date (YYYY-MM-DD format)",
        "source": "Originating organization (e.g., 'CHA IPSO Collaborative')",
        "evidence_level": "Evidence level: high, moderate, low, expert_consensus",
        "description": "Brief description of the protocol",
        "version": "Protocol version (e.g., '2.0')",
    },
    partition_key_pattern="protocol"
)

OUTCOME_METRIC = VertexType(
    label="outcome_metric",
    description="Measurable quality outcome linked to protocols",
    properties={
        "id": "Unique identifier (e.g., 'metric-001')",
        "name": "Metric name (e.g., 'Sepsis Mortality Rate')",
        "unit": "Unit of measurement (e.g., 'percentage', 'minutes')",
        "direction": "Improvement direction: higher_better, lower_better",
        "benchmark": "Target value representing good performance (float)",
        "data_source": "Data source (e.g., 'PHIS', 'NHSN', 'Internal')",
    },
    partition_key_pattern="outcome_metric"
)


# =============================================================================
# Edge Types
# =============================================================================

ADOPTED = EdgeType(
    label="adopted",
    description="Hospital adopted a protocol",
    from_vertex="hospital",  # From referral_network domain
    to_vertex="protocol",
    properties={
        "adoption_date": "Date of adoption (YYYY-MM-DD format)",
        "compliance_rate": "Current compliance percentage (0-100)",
        "champion": "Internal champion leading adoption",
        "adoption_phase": "Phase: pilot, partial, full",
        "notes": "Additional notes about adoption",
    }
)

LEARNED_FROM = EdgeType(
    label="learned_from",
    description="Knowledge transfer between hospitals - source hospital taught/influenced destination",
    from_vertex="hospital",
    to_vertex="hospital",
    properties={
        "interaction_type": "Type: site_visit, webinar, collaborative_meeting, peer_consult, publication, conference_presentation",
        "date": "Date of interaction (YYYY-MM-DD format)",
        "protocol_context": "Which protocol the learning was about",
        "effectiveness_rating": "Rating 1-5 of how helpful the interaction was",
        "topics_covered": "Comma-separated list of topics discussed",
    }
)

ACHIEVED = EdgeType(
    label="achieved",
    description="Hospital achieved outcome on a metric",
    from_vertex="hospital",
    to_vertex="outcome_metric",
    properties={
        "baseline": "Starting value before intervention (float)",
        "current": "Current measured value (float)",
        "measurement_period": "When current value was measured (e.g., 'Q3-2025')",
        "sample_size": "Number of cases in measurement (integer)",
    }
)

MEASURES = EdgeType(
    label="measures",
    description="Protocol is measured by an outcome metric",
    from_vertex="protocol",
    to_vertex="outcome_metric",
    properties={
        "weight": "Importance weight for composite scoring (0-1)",
        "target_improvement": "Expected improvement percentage",
        "is_primary": "Whether this is the primary outcome metric (boolean)",
    }
)


# Export all types
VERTEX_TYPES = [PROTOCOL, OUTCOME_METRIC]
EDGE_TYPES = [ADOPTED, LEARNED_FROM, ACHIEVED, MEASURES]
