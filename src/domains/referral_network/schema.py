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
