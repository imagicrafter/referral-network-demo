"""
Referral network domain tools.

Consolidates tool definitions and query implementations for the
referral network analytics domain.
"""
from typing import Dict, List, Any, Optional, Callable
from src.core.cosmos_connection import get_client, execute_query

# =============================================================================
# Database helpers
# =============================================================================

_client = None


def get_graph_client():
    """Get or create the Gremlin client."""
    global _client
    if _client is None:
        _client = get_client()
    return _client


def _clean_value_map(results: list) -> List[Dict]:
    """Convert Gremlin valueMap results to cleaner dictionaries."""
    cleaned = []
    for item in results:
        if isinstance(item, dict):
            clean_item = {}
            for key, value in item.items():
                # valueMap returns lists for each property
                if isinstance(value, list) and len(value) == 1:
                    clean_item[key] = value[0]
                else:
                    clean_item[key] = value
            cleaned.append(clean_item)
        else:
            cleaned.append(item)
    return cleaned


# =============================================================================
# Tool implementations
# =============================================================================

def find_hospital(
    name: Optional[str] = None,
    state: Optional[str] = None,
    hospital_type: Optional[str] = None,
    rural: Optional[bool] = None
) -> List[Dict]:
    """
    Find hospitals matching the given criteria.

    Args:
        name: Hospital name (partial match)
        state: State abbreviation (e.g., 'MO', 'KS')
        hospital_type: Type ('tertiary', 'community', 'regional', 'specialty')
        rural: Whether the hospital is in a rural area

    Returns:
        List of matching hospitals with their properties
    """
    client = get_graph_client()

    query = "g.V().hasLabel('hospital')"

    if name:
        safe_name = name.replace("'", "\\'")
        query += f".has('name', TextP.containing('{safe_name}'))"
    if state:
        query += f".has('state', '{state}')"
    if hospital_type:
        query += f".has('type', '{hospital_type}')"
    if rural is not None:
        query += f".has('rural', {str(rural).lower()})"

    query += ".valueMap(true)"

    results = execute_query(client, query)
    return _clean_value_map(results)


def get_referral_sources(hospital_name: str) -> List[Dict]:
    """
    Find all hospitals that refer patients to the specified hospital.

    Args:
        hospital_name: Name of the receiving hospital

    Returns:
        List of referring hospitals with referral volumes
    """
    client = get_graph_client()
    safe_name = hospital_name.replace("'", "\\'")

    query = f"""
    g.V().has('hospital', 'name', '{safe_name}')
      .inE('refers_to')
      .order().by('count', decr)
      .project('referring_hospital', 'referral_count', 'avg_acuity')
      .by(outV().values('name'))
      .by('count')
      .by('avg_acuity')
    """

    return execute_query(client, query)


def get_referral_destinations(hospital_name: str) -> List[Dict]:
    """
    Find all hospitals that receive referrals from the specified hospital.

    Args:
        hospital_name: Name of the referring hospital

    Returns:
        List of destination hospitals with referral volumes
    """
    client = get_graph_client()
    safe_name = hospital_name.replace("'", "\\'")

    query = f"""
    g.V().has('hospital', 'name', '{safe_name}')
      .outE('refers_to')
      .order().by('count', decr)
      .project('destination_hospital', 'referral_count', 'avg_acuity')
      .by(inV().values('name'))
      .by('count')
      .by('avg_acuity')
    """

    return execute_query(client, query)


def get_network_statistics() -> Dict[str, Any]:
    """
    Get overall statistics about the referral network.

    Returns:
        Dictionary with network statistics
    """
    client = get_graph_client()

    stats = {}
    stats['total_hospitals'] = execute_query(client,
        "g.V().hasLabel('hospital').count()")[0]
    stats['total_providers'] = execute_query(client,
        "g.V().hasLabel('provider').count()")[0]
    stats['total_referral_relationships'] = execute_query(client,
        "g.E().hasLabel('refers_to').count()")[0]
    stats['total_referral_volume'] = execute_query(client,
        "g.E().hasLabel('refers_to').values('count').sum()")[0]
    stats['rural_hospitals'] = execute_query(client,
        "g.V().hasLabel('hospital').has('rural', true).count()")[0]
    stats['tertiary_centers'] = execute_query(client,
        "g.V().hasLabel('hospital').has('type', 'tertiary').count()")[0]

    return stats


def find_referral_path(
    from_hospital: str,
    to_hospital: str,
    max_hops: int = 3
) -> List:
    """
    Find referral paths between two hospitals.

    Args:
        from_hospital: Starting hospital name
        to_hospital: Destination hospital name
        max_hops: Maximum number of intermediate hospitals

    Returns:
        List of paths, where each path is a list of hospital names
    """
    client = get_graph_client()

    safe_from = from_hospital.replace("'", "\\'")
    safe_to = to_hospital.replace("'", "\\'")

    query = f"""
    g.V().has('hospital', 'name', '{safe_from}')
      .repeat(out('refers_to').simplePath())
      .until(has('name', '{safe_to}').or().loops().is(gte({max_hops})))
      .has('name', '{safe_to}')
      .path()
      .by('name')
      .limit(10)
    """

    return execute_query(client, query)


def get_providers_by_specialty(specialty: str) -> List[Dict]:
    """
    Find providers by specialty and their hospital affiliations.

    Args:
        specialty: Medical specialty (e.g., 'Pediatric Cardiology')

    Returns:
        List of providers with their hospital affiliations
    """
    client = get_graph_client()
    safe_specialty = specialty.replace("'", "\\'")

    query = f"""
    g.V().hasLabel('provider')
      .has('specialty', '{safe_specialty}')
      .project('provider_name', 'specialty')
      .by('name')
      .by('specialty')
    """

    return execute_query(client, query)


def get_hospitals_by_service(service_name: str) -> List[Dict]:
    """
    Find hospitals that offer a specific service line.

    Args:
        service_name: Name of the service (e.g., 'Cardiac Surgery')

    Returns:
        List of hospitals with volume and ranking
    """
    client = get_graph_client()
    safe_service = service_name.replace("'", "\\'")

    query = f"""
    g.V().has('service_line', 'name', '{safe_service}')
      .inE('specializes_in')
      .order().by('ranking', incr)
      .project('hospital', 'volume', 'ranking')
      .by(outV().values('name'))
      .by('volume')
      .by('ranking')
    """

    return execute_query(client, query)


def analyze_rural_access(service_name: str) -> List[Dict]:
    """
    Analyze how rural hospitals connect to specialized services.

    Args:
        service_name: Name of the specialized service

    Returns:
        Analysis of rural hospital access to the service
    """
    client = get_graph_client()
    safe_service = service_name.replace("'", "\\'")

    query = f"""
    g.V().hasLabel('hospital').has('rural', true)
      .project('rural_hospital', 'state')
      .by('name')
      .by('state')
    """

    return execute_query(client, query)


# Import diagram generators
from src.domains.referral_network.diagrams import (
    generate_referral_network_diagram,
    generate_path_diagram,
    generate_service_network_diagram,
)


# =============================================================================
# Tool registry exports
# =============================================================================

TOOLS: Dict[str, Callable] = {
    "find_hospital": find_hospital,
    "get_referral_sources": get_referral_sources,
    "get_referral_destinations": get_referral_destinations,
    "get_network_statistics": get_network_statistics,
    "find_referral_path": find_referral_path,
    "get_providers_by_specialty": get_providers_by_specialty,
    "get_hospitals_by_service": get_hospitals_by_service,
    "analyze_rural_access": analyze_rural_access,
    "generate_referral_network_diagram": generate_referral_network_diagram,
    "generate_path_diagram": generate_path_diagram,
    "generate_service_network_diagram": generate_service_network_diagram,
}


TOOL_DEFINITIONS: List[Dict] = [
    {
        "name": "find_hospital",
        "description": "Search for hospitals by name, state, type, or rural status. Use partial names like 'Children's Mercy' to find matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Hospital name (partial match supported)"},
                "state": {"type": "string", "description": "State abbreviation (e.g., 'MO', 'KS')"},
                "hospital_type": {"type": "string", "enum": ["tertiary", "community", "regional", "specialty"]},
                "rural": {"type": "boolean", "description": "Whether the hospital is in a rural area"}
            }
        }
    },
    {
        "name": "get_referral_sources",
        "description": "Find all hospitals that refer patients to a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the receiving hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_referral_destinations",
        "description": "Find all hospitals that receive referrals from a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the referring hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_network_statistics",
        "description": "Get overall statistics about the referral network",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "find_referral_path",
        "description": "Find referral paths between two hospitals",
        "parameters": {
            "type": "object",
            "properties": {
                "from_hospital": {"type": "string", "description": "Starting hospital name"},
                "to_hospital": {"type": "string", "description": "Destination hospital name"},
                "max_hops": {"type": "integer", "description": "Maximum intermediate hospitals", "default": 3}
            },
            "required": ["from_hospital", "to_hospital"]
        }
    },
    {
        "name": "get_providers_by_specialty",
        "description": "Find providers by medical specialty",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string", "description": "Medical specialty name"}
            },
            "required": ["specialty"]
        }
    },
    {
        "name": "get_hospitals_by_service",
        "description": "Find hospitals offering a specific service line",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service line"}
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "analyze_rural_access",
        "description": "Analyze how rural hospitals connect to specialized services",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the specialized service"}
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "generate_referral_network_diagram",
        "description": "Generate a Mermaid diagram showing hospital referral relationships",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Optional: focus on specific hospital"},
                "include_volumes": {"type": "boolean", "description": "Show referral counts", "default": True},
                "direction": {"type": "string", "enum": ["LR", "TB", "RL", "BT"], "default": "LR"}
            }
        }
    },
    {
        "name": "generate_path_diagram",
        "description": "Generate a Mermaid diagram showing paths between two hospitals",
        "parameters": {
            "type": "object",
            "properties": {
                "from_hospital": {"type": "string", "description": "Starting hospital name"},
                "to_hospital": {"type": "string", "description": "Destination hospital name"},
                "max_hops": {"type": "integer", "description": "Maximum path length", "default": 3}
            },
            "required": ["from_hospital", "to_hospital"]
        }
    },
    {
        "name": "generate_service_network_diagram",
        "description": "Generate a Mermaid diagram showing hospitals that provide a service",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service line"},
                "include_rankings": {"type": "boolean", "description": "Show hospital rankings", "default": True}
            },
            "required": ["service_name"]
        }
    },
]
