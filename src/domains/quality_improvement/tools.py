"""
Quality improvement domain tools.

Tool implementations and definitions for tracking protocol adoption,
best practice spread, and outcome improvements.
"""
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
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
                if isinstance(value, list) and len(value) == 1:
                    clean_item[key] = value[0]
                else:
                    clean_item[key] = value
            cleaned.append(clean_item)
        else:
            cleaned.append(item)
    return cleaned


def _safe_string(value: str) -> str:
    """Escape single quotes for Gremlin queries."""
    return value.replace("'", "\\'")


# =============================================================================
# Tool implementations
# =============================================================================

def get_protocol_adoption_status(protocol_name: str) -> Dict[str, Any]:
    """
    Get adoption status for a protocol across all hospitals.

    Args:
        protocol_name: Name of the protocol (e.g., "Sepsis Bundle v2.0")

    Returns:
        Dictionary with adoption statistics and lists of adopters/non-adopters
    """
    client = get_graph_client()
    safe_name = _safe_string(protocol_name)

    # Get protocol details
    protocol_query = f"""
    g.V().has('protocol', 'name', TextP.containing('{safe_name}'))
        .valueMap(true)
    """
    protocol_results = execute_query(client, protocol_query)

    if not protocol_results:
        return {
            "error": f"Protocol '{protocol_name}' not found",
            "protocol": protocol_name
        }

    protocol_data = _clean_value_map(protocol_results)[0]

    # Get adopters with their adoption details
    adopters_query = f"""
    g.V().has('protocol', 'name', TextP.containing('{safe_name}'))
        .inE('adopted')
        .project('hospital', 'state', 'type', 'adoption_date', 'compliance_rate', 'phase')
        .by(outV().values('name'))
        .by(outV().values('state'))
        .by(outV().values('type'))
        .by('adoption_date')
        .by('compliance_rate')
        .by('adoption_phase')
    """
    adopters = execute_query(client, adopters_query)

    # Get total hospital count
    total_hospitals = execute_query(client, "g.V().hasLabel('hospital').count()")[0]

    # Get non-adopters
    non_adopters_query = f"""
    g.V().hasLabel('hospital')
        .not(__.out('adopted').has('name', TextP.containing('{safe_name}')))
        .project('hospital', 'state', 'type')
        .by('name')
        .by('state')
        .by('type')
    """
    non_adopters = execute_query(client, non_adopters_query)

    # Calculate statistics
    adopted_count = len(adopters)
    adoption_rate = round((adopted_count / total_hospitals) * 100, 1) if total_hospitals > 0 else 0

    # Count by phase
    by_phase = {"full": 0, "partial": 0, "pilot": 0}
    total_compliance = 0
    for adopter in adopters:
        phase = adopter.get('phase', 'pilot')
        by_phase[phase] = by_phase.get(phase, 0) + 1
        total_compliance += adopter.get('compliance_rate', 0)

    avg_compliance = round(total_compliance / adopted_count, 1) if adopted_count > 0 else 0

    return {
        "protocol": protocol_data.get('name', protocol_name),
        "release_date": protocol_data.get('release_date', ''),
        "category": protocol_data.get('category', ''),
        "total_hospitals": total_hospitals,
        "adopted_count": adopted_count,
        "adoption_rate": adoption_rate,
        "by_phase": by_phase,
        "avg_compliance_rate": avg_compliance,
        "adopters": adopters,
        "non_adopters": non_adopters
    }


def find_adoption_gaps(
    protocol_name: str,
    min_connections: int = 2
) -> Dict[str, Any]:
    """
    Find non-adopting hospitals with strong connections to successful adopters.
    These are high-potential targets for outreach.

    Args:
        protocol_name: Name of the protocol
        min_connections: Minimum connections to adopters to be considered high-potential

    Returns:
        Dictionary with high-potential targets and isolated hospitals
    """
    client = get_graph_client()
    safe_name = _safe_string(protocol_name)

    # Find non-adopters and count their connections to adopters
    # Using both refers_to and learned_from edges
    gap_query = f"""
    g.V().hasLabel('hospital')
        .not(__.out('adopted').has('name', TextP.containing('{safe_name}')))
        .as('non_adopter')
        .project('hospital', 'state', 'type', 'adopter_connections')
        .by('name')
        .by('state')
        .by('type')
        .by(
            __.both('refers_to', 'learned_from')
                .where(__.out('adopted').has('name', TextP.containing('{safe_name}')))
                .dedup()
                .count()
        )
    """

    results = execute_query(client, gap_query)

    high_potential = []
    isolated = []

    for hospital in results:
        connections = hospital.get('adopter_connections', 0)
        hospital_info = {
            "hospital": hospital.get('hospital', ''),
            "state": hospital.get('state', ''),
            "type": hospital.get('type', ''),
            "connections_to_adopters": connections
        }

        if connections >= min_connections:
            hospital_info["recommendation"] = "High potential - strong network ties to adopters"
            high_potential.append(hospital_info)
        elif connections == 0:
            hospital_info["recommendation"] = "Requires direct CHA intervention - no network connections to adopters"
            isolated.append(hospital_info)

    # Sort by connections descending
    high_potential.sort(key=lambda x: x['connections_to_adopters'], reverse=True)

    return {
        "protocol": protocol_name,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "high_potential_targets": high_potential,
        "isolated_hospitals": isolated,
        "summary": {
            "high_potential_count": len(high_potential),
            "isolated_count": len(isolated),
            "total_non_adopters": len(results)
        }
    }


def get_protocol_spread_path(
    protocol_name: str,
    hospital_name: str
) -> Dict[str, Any]:
    """
    Trace how a protocol spread to reach a specific hospital.
    Shows the chain of influence (who learned from whom).

    Args:
        protocol_name: Name of the protocol
        hospital_name: Hospital to trace path to

    Returns:
        Dictionary with influence chain and path analysis
    """
    client = get_graph_client()
    safe_protocol = _safe_string(protocol_name)
    safe_hospital = _safe_string(hospital_name)

    # First verify the hospital adopted the protocol
    adoption_check = f"""
    g.V().has('hospital', 'name', TextP.containing('{safe_hospital}'))
        .outE('adopted')
        .inV().has('name', TextP.containing('{safe_protocol}'))
        .count()
    """
    adopted = execute_query(client, adoption_check)[0]

    if not adopted:
        return {
            "error": f"Hospital '{hospital_name}' has not adopted protocol '{protocol_name}'",
            "hospital": hospital_name,
            "protocol": protocol_name
        }

    # Get the adoption date for this hospital
    adoption_info_query = f"""
    g.V().has('hospital', 'name', TextP.containing('{safe_hospital}'))
        .outE('adopted')
        .where(inV().has('name', TextP.containing('{safe_protocol}')))
        .valueMap()
    """
    adoption_info = execute_query(client, adoption_info_query)
    adoption_date = ""
    if adoption_info:
        adoption_info_clean = _clean_value_map(adoption_info)[0]
        adoption_date = adoption_info_clean.get('adoption_date', '')

    # Trace influence path backwards using learned_from edges
    path_query = f"""
    g.V().has('hospital', 'name', TextP.containing('{safe_hospital}'))
        .repeat(
            __.inE('learned_from')
                .has('protocol_context', TextP.containing('{safe_protocol}'))
                .outV()
                .simplePath()
        )
        .until(
            __.inE('learned_from')
                .has('protocol_context', TextP.containing('{safe_protocol}'))
                .count().is(0)
            .or()
            .loops().is(5)
        )
        .path()
        .by('name')
        .by(valueMap('interaction_type', 'date'))
    """

    paths = execute_query(client, path_query)

    influence_chain = []
    if paths:
        # Parse the first/shortest path
        for path in paths[:1]:  # Just take first path
            if isinstance(path, list):
                for j in range(0, len(path) - 1, 2):
                    if j + 2 < len(path):
                        edge_info = path[j + 1] if isinstance(path[j + 1], dict) else {}
                        influence_chain.append({
                            "step": (j // 2) + 1,
                            "from_hospital": path[j + 2] if j + 2 < len(path) else "",
                            "to_hospital": path[j],
                            "interaction_type": edge_info.get('interaction_type', ['unknown'])[0] if isinstance(edge_info.get('interaction_type'), list) else edge_info.get('interaction_type', 'unknown'),
                            "date": edge_info.get('date', [''])[0] if isinstance(edge_info.get('date'), list) else edge_info.get('date', '')
                        })

    # Find the original source (earliest adopter in the chain)
    original_source = influence_chain[-1]['from_hospital'] if influence_chain else hospital_name

    return {
        "hospital": hospital_name,
        "protocol": protocol_name,
        "adoption_date": adoption_date,
        "influence_chain": influence_chain,
        "original_source": original_source,
        "chain_length": len(influence_chain)
    }


def find_quality_champions(protocol_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Identify hospitals that have influenced multiple others to adopt protocols.

    Args:
        protocol_name: Optional - filter to specific protocol. If None, analyzes all protocols.

    Returns:
        Dictionary with ranked list of champion hospitals
    """
    client = get_graph_client()

    if protocol_name:
        safe_protocol = _safe_string(protocol_name)
        # Filter to specific protocol
        champions_query = f"""
        g.V().hasLabel('hospital')
            .where(
                __.out('adopted')
                    .has('name', TextP.containing('{safe_protocol}'))
            )
            .where(
                __.outE('adopted').has('compliance_rate', gte(85))
            )
            .project('hospital', 'state', 'influenced_count', 'protocols', 'methods')
            .by('name')
            .by('state')
            .by(__.in('learned_from').dedup().count())
            .by(__.out('adopted').values('name').dedup().fold())
            .by(__.inE('learned_from').values('interaction_type').groupCount())
        """
    else:
        # All protocols
        champions_query = """
        g.V().hasLabel('hospital')
            .where(
                __.outE('adopted').has('compliance_rate', gte(85))
            )
            .project('hospital', 'state', 'influenced_count', 'protocols', 'methods')
            .by('name')
            .by('state')
            .by(__.in('learned_from').dedup().count())
            .by(__.out('adopted').values('name').dedup().fold())
            .by(__.inE('learned_from').values('interaction_type').groupCount())
        """

    results = execute_query(client, champions_query)

    # Filter to hospitals that have influenced at least 1 other
    champions = []
    for hospital in results:
        influenced_count = hospital.get('influenced_count', 0)
        if influenced_count >= 1:
            champions.append({
                "hospital": hospital.get('hospital', ''),
                "state": hospital.get('state', ''),
                "hospitals_influenced": influenced_count,
                "protocols_championed": hospital.get('protocols', []),
                "influence_methods": hospital.get('methods', {}),
                "influence_score": round(influenced_count * 10, 1)  # Simple scoring
            })

    # Sort by influence count descending
    champions.sort(key=lambda x: x['hospitals_influenced'], reverse=True)

    return {
        "champions": champions[:20],  # Top 20
        "total_champions_identified": len(champions),
        "criteria": "Hospitals that influenced 1+ others with 85%+ compliance",
        "protocol_filter": protocol_name or "All protocols"
    }


def analyze_outcome_improvement(
    protocol_name: str,
    metric_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze outcome improvements for hospitals that adopted a protocol.

    Args:
        protocol_name: Name of the protocol
        metric_name: Optional - specific metric to analyze

    Returns:
        Dictionary with outcome analysis and improvement statistics
    """
    client = get_graph_client()
    safe_protocol = _safe_string(protocol_name)

    # Get outcome data for protocol adopters
    if metric_name:
        safe_metric = _safe_string(metric_name)
        outcomes_query = f"""
        g.V().has('protocol', 'name', TextP.containing('{safe_protocol}'))
            .in('adopted').as('hospital')
            .outE('achieved').as('outcome')
            .inV().has('name', TextP.containing('{safe_metric}')).as('metric')
            .select('hospital', 'outcome', 'metric')
            .by(valueMap('name'))
            .by(valueMap('baseline', 'current', 'measurement_period'))
            .by(valueMap('name', 'unit', 'direction'))
        """
    else:
        outcomes_query = f"""
        g.V().has('protocol', 'name', TextP.containing('{safe_protocol}'))
            .in('adopted').as('hospital')
            .outE('achieved').as('outcome')
            .inV().as('metric')
            .select('hospital', 'outcome', 'metric')
            .by(valueMap('name'))
            .by(valueMap('baseline', 'current', 'measurement_period'))
            .by(valueMap('name', 'unit', 'direction'))
        """

    results = execute_query(client, outcomes_query)

    if not results:
        return {
            "protocol": protocol_name,
            "error": "No outcome data found for protocol adopters",
            "metric_filter": metric_name
        }

    # Process outcomes by metric
    metrics_data: Dict[str, Dict[str, Any]] = {}
    for result in results:
        hospital = result.get('hospital', {})
        outcome = result.get('outcome', {})
        metric = result.get('metric', {})

        hospital_name = hospital.get('name', [''])[0] if isinstance(hospital.get('name'), list) else hospital.get('name', '')
        metric_name_val = metric.get('name', [''])[0] if isinstance(metric.get('name'), list) else metric.get('name', '')
        baseline = outcome.get('baseline', [0])[0] if isinstance(outcome.get('baseline'), list) else outcome.get('baseline', 0)
        current = outcome.get('current', [0])[0] if isinstance(outcome.get('current'), list) else outcome.get('current', 0)
        direction = metric.get('direction', ['lower_better'])[0] if isinstance(metric.get('direction'), list) else metric.get('direction', 'lower_better')

        if metric_name_val not in metrics_data:
            metrics_data[metric_name_val] = {
                "metric": metric_name_val,
                "unit": metric.get('unit', [''])[0] if isinstance(metric.get('unit'), list) else metric.get('unit', ''),
                "direction": direction,
                "hospitals": []
            }

        # Calculate improvement
        if direction == 'lower_better':
            improvement_pct = round(((baseline - current) / baseline) * 100, 1) if baseline > 0 else 0
        else:
            improvement_pct = round(((current - baseline) / baseline) * 100, 1) if baseline > 0 else 0

        metrics_data[metric_name_val]["hospitals"].append({
            "hospital": hospital_name,
            "baseline": baseline,
            "current": current,
            "improvement_pct": improvement_pct
        })

    # Calculate aggregate statistics per metric
    metrics_analyzed = []
    for metric_key, data in metrics_data.items():
        hospitals = data["hospitals"]
        if hospitals:
            avg_baseline = round(sum(h['baseline'] for h in hospitals) / len(hospitals), 1)
            avg_current = round(sum(h['current'] for h in hospitals) / len(hospitals), 1)
            avg_improvement = round(sum(h['improvement_pct'] for h in hospitals) / len(hospitals), 1)

            # Sort by improvement for top improvers
            sorted_hospitals = sorted(hospitals, key=lambda x: x['improvement_pct'], reverse=True)

            metrics_analyzed.append({
                "metric": data["metric"],
                "unit": data["unit"],
                "direction": data["direction"],
                "hospitals_with_data": len(hospitals),
                "avg_baseline": avg_baseline,
                "avg_current": avg_current,
                "avg_improvement_pct": avg_improvement,
                "top_improvers": sorted_hospitals[:5]
            })

    # Calculate overall summary
    total_hospitals = sum(m['hospitals_with_data'] for m in metrics_analyzed)

    return {
        "protocol": protocol_name,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "metrics_analyzed": metrics_analyzed,
        "overall_summary": {
            "total_outcome_records": total_hospitals,
            "metrics_count": len(metrics_analyzed)
        }
    }


# Import diagram generators
from src.domains.quality_improvement.diagrams import (
    generate_adoption_spread_diagram,
)


# =============================================================================
# Tool registry exports
# =============================================================================

TOOLS: Dict[str, Callable] = {
    "get_protocol_adoption_status": get_protocol_adoption_status,
    "find_adoption_gaps": find_adoption_gaps,
    "get_protocol_spread_path": get_protocol_spread_path,
    "find_quality_champions": find_quality_champions,
    "analyze_outcome_improvement": analyze_outcome_improvement,
    "generate_adoption_spread_diagram": generate_adoption_spread_diagram,
}


TOOL_DEFINITIONS: List[Dict] = [
    {
        "name": "get_protocol_adoption_status",
        "description": "Get adoption status for a quality improvement protocol across all hospitals. Returns adoption rates, compliance levels, and lists of adopters/non-adopters.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Name of the protocol (e.g., 'Sepsis Bundle v2.0', 'CLABSI Prevention Bundle')"
                }
            },
            "required": ["protocol_name"]
        }
    },
    {
        "name": "find_adoption_gaps",
        "description": "Find non-adopting hospitals that are well-connected to successful adopters. Identifies high-potential outreach targets and isolated hospitals needing intervention.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Name of the protocol"
                },
                "min_connections": {
                    "type": "integer",
                    "description": "Minimum connections to adopters to be considered high-potential (default: 2)",
                    "default": 2
                }
            },
            "required": ["protocol_name"]
        }
    },
    {
        "name": "get_protocol_spread_path",
        "description": "Trace how a protocol spread to reach a specific hospital. Shows the chain of influence with interaction types and dates.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Name of the protocol"
                },
                "hospital_name": {
                    "type": "string",
                    "description": "Name of the hospital to trace the path to"
                }
            },
            "required": ["protocol_name", "hospital_name"]
        }
    },
    {
        "name": "find_quality_champions",
        "description": "Identify hospitals that have influenced multiple others to adopt quality improvement protocols. Returns ranked list of influential hospitals with their methods and impact.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Optional: filter to a specific protocol. Leave empty to analyze all protocols."
                }
            },
            "required": []
        }
    },
    {
        "name": "analyze_outcome_improvement",
        "description": "Analyze outcome improvements for hospitals that adopted a protocol. Shows baseline vs current metrics, improvement percentages, and top improvers.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Name of the protocol to analyze"
                },
                "metric_name": {
                    "type": "string",
                    "description": "Optional: specific outcome metric to analyze"
                }
            },
            "required": ["protocol_name"]
        }
    },
    {
        "name": "generate_adoption_spread_diagram",
        "description": "Generate a Mermaid diagram visualizing how a protocol spread through the hospital network. Color-codes hospitals by adoption timing and shows influence relationships.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Name of the protocol to visualize"
                },
                "show_timeline": {
                    "type": "boolean",
                    "description": "Whether to color-code by adoption timing (default: true)",
                    "default": True
                },
                "max_hospitals": {
                    "type": "integer",
                    "description": "Maximum hospitals to include in diagram (default: 30)",
                    "default": 30
                }
            },
            "required": ["protocol_name"]
        }
    },
]
