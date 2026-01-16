# PRP: Quality Improvement Protocol Spread Domain

**Feature**: Add quality improvement analytics domain for tracking protocol adoption and best practice spread across the hospital network
**Priority**: HIGH - Recommended as next implementation
**Estimated Complexity**: Medium-High
**Target Version**: 2.1.0
**Domain ID**: `quality_improvement`
**Depends On**: `referral_network`

---

## 1. Overview

### 1.1 What We're Building

Implement a new analytics domain that tracks quality improvement protocol adoption, spread patterns, and outcome improvements across the children's hospital network. This domain adds:

- **2 new vertex types**: `protocol`, `outcome_metric`
- **4 new edge types**: `adopted`, `learned_from`, `achieved`, `measures`
- **6 new tools**: Query and visualization tools for protocol adoption analysis
- **1 diagram generator**: Mermaid visualization for protocol spread patterns

### 1.2 Why This Matters

| Current State | Problem | Target State |
|---------------|---------|--------------|
| Only referral network analytics | Cannot track quality improvement initiatives | Full protocol adoption tracking |
| No protocol spread analysis | Cannot identify influence patterns | Graph traversal for learning paths |
| No gap identification | Cannot target outreach effectively | Centrality-based gap analysis |
| Dashboard shows "what" | Cannot answer "why" questions | Relationship-based analytics |

### 1.3 Success Criteria

1. **Domain loads correctly**: `make validate-config` passes with `quality_improvement` enabled
2. **Tools registered**: `make list-tools` shows all 6 new tools
3. **Sample data loads**: `python scripts/load_quality_improvement_data.py` completes
4. **All tests pass**: `pytest tests/domains/quality_improvement/ -v` passes
5. **Diagram generation works**: `generate_adoption_spread_diagram` returns valid Mermaid
6. **Dependency handled**: Domain loads after `referral_network` (uses existing `hospital` vertices)

---

## 2. Architecture

### 2.1 File Structure to Create

```
src/domains/quality_improvement/
├── __init__.py              # Export TOOLS and TOOL_DEFINITIONS
├── tools.py                 # Tool implementations and definitions
├── diagrams.py              # Mermaid diagram generators
├── schema.py                # Vertex/edge type documentation
└── sample_data.py           # Sample data definitions

scripts/
└── load_quality_improvement_data.py  # Data loader script

tests/domains/quality_improvement/
├── __init__.py
├── test_tools.py            # Unit tests for tools
└── test_diagrams.py         # Unit tests for diagram generation
```

### 2.2 Config Update

Add to `config/domains.yaml`:

```yaml
quality_improvement:
  enabled: true
  name: "Quality Improvement Analytics"
  description: >
    Track protocol adoption, best practice spread, and outcome improvements
    across the hospital network. Analyze how quality initiatives propagate
    through referral and collaboration relationships.
  version: "1.0.0"
  depends_on:
    - referral_network
  module: "src.domains.quality_improvement"
  tools:
    - get_protocol_adoption_status
    - find_adoption_gaps
    - get_protocol_spread_path
    - find_quality_champions
    - analyze_outcome_improvement
    - generate_adoption_spread_diagram
  vertex_types:
    - protocol
    - outcome_metric
  edge_types:
    - adopted
    - learned_from
    - achieved
    - measures
```

### 2.3 Dependency Diagram

```
config/domains.yaml (updated)
       │
       ▼
src/core/tool_registry.py
       │
       ├──► src/domains/referral_network/ (loads first - has hospital vertices)
       │
       └──► src/domains/quality_improvement/ (loads second - depends on referral_network)
                   │
                   ├── tools.py (imports from src.core.cosmos_connection)
                   ├── diagrams.py (imports from src.core.diagram_base)
                   └── schema.py (references referral_network.hospital)
```

---

## 3. Implementation Tasks

### Phase 1: Create Domain Module Structure

#### Task 1.1: Create `src/domains/quality_improvement/__init__.py`

```python
"""
Quality Improvement Analytics Domain.

Provides tools for tracking protocol adoption, best practice spread, and outcome
improvements across the hospital network. Analyzes how quality initiatives
propagate through referral and collaboration relationships.

CHA Programs Supported:
- IPSO Collaborative (Improving Sepsis Outcomes)
- CLABSI Prevention
- Pediatric Early Warning Score
- Safe Medication Administration
"""
from src.domains.quality_improvement.tools import TOOLS, TOOL_DEFINITIONS

__all__ = ["TOOLS", "TOOL_DEFINITIONS"]
```

#### Task 1.2: Create `src/domains/quality_improvement/schema.py`

**Pattern Reference**: `src/domains/referral_network/schema.py` (if exists) or inline documentation

```python
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
```

### Phase 2: Implement Tools

#### Task 2.1: Create `src/domains/quality_improvement/tools.py`

**Pattern Reference**: `src/domains/referral_network/tools.py:1-421`

```python
"""
Quality improvement domain tools.

Tool implementations and definitions for tracking protocol adoption,
best practice spread, and outcome improvements.
"""
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
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
        for i, path in enumerate(paths[:1]):  # Just take first path
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
    metrics_data = {}
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
    improved = sum(1 for m in metrics_analyzed for h in metrics_data.get(m['metric'], {}).get('hospitals', []) if h['improvement_pct'] > 0)

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
```

#### Task 2.2: Create `src/domains/quality_improvement/diagrams.py`

**Pattern Reference**: `src/domains/referral_network/diagrams.py:1-562`

```python
"""
Mermaid diagram generators for quality improvement domain.

Generates valid Mermaid syntax from Cosmos DB graph data for protocol
adoption and spread visualization.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from src.core.diagram_base import (
    sanitize_node_id,
    escape_label,
    COLORS,
)
from src.core.cosmos_connection import get_client, execute_query


# Additional colors for adoption waves
ADOPTION_COLORS = {
    "early": "#4CAF50",    # Green - early adopters
    "mid": "#FFC107",      # Yellow/Amber - mid adopters
    "late": "#FF9800",     # Orange - late adopters
    "non_adopter": "#F44336",  # Red - not yet adopted
}


def _safe_string(value: str) -> str:
    """Escape single quotes for Gremlin queries."""
    return value.replace("'", "\\'")


def _classify_adoption_wave(adoption_date: str, release_date: str) -> str:
    """
    Classify hospital into adoption wave based on timing.

    Args:
        adoption_date: Date hospital adopted (YYYY-MM-DD)
        release_date: Protocol release date (YYYY-MM-DD)

    Returns:
        Wave classification: 'early', 'mid', 'late', or 'non_adopter'
    """
    try:
        adopted = datetime.strptime(adoption_date, "%Y-%m-%d")
        released = datetime.strptime(release_date, "%Y-%m-%d")

        days_since_release = (adopted - released).days

        if days_since_release <= 180:  # First 6 months
            return "early"
        elif days_since_release <= 365:  # 6-12 months
            return "mid"
        else:  # 12+ months
            return "late"
    except (ValueError, TypeError):
        return "mid"  # Default if dates can't be parsed


def _get_wave_style(wave: str) -> str:
    """Get Mermaid style for adoption wave."""
    color = ADOPTION_COLORS.get(wave, ADOPTION_COLORS["mid"])
    text_color = "#fff" if wave != "mid" else "#000"
    return f"fill:{color},color:{text_color}"


def generate_adoption_spread_diagram(
    protocol_name: str,
    show_timeline: bool = True,
    max_hospitals: int = 30
) -> str:
    """
    Generate a Mermaid diagram showing how a protocol spread through the network.

    Args:
        protocol_name: Name of the protocol
        show_timeline: Whether to color-code by adoption timing
        max_hospitals: Maximum number of hospitals to include

    Returns:
        Mermaid diagram string wrapped in code fence
    """
    client = get_client()
    safe_protocol = _safe_string(protocol_name)

    # Get protocol release date
    protocol_query = f"""
    g.V().has('protocol', 'name', TextP.containing('{safe_protocol}'))
        .values('release_date')
    """
    release_results = execute_query(client, protocol_query)
    release_date = release_results[0] if release_results else "2024-01-01"

    # Get adopters with adoption dates
    adopters_query = f"""
    g.V().has('protocol', 'name', TextP.containing('{safe_protocol}'))
        .inE('adopted')
        .project('hospital', 'adoption_date', 'compliance_rate', 'type')
        .by(outV().values('name'))
        .by('adoption_date')
        .by('compliance_rate')
        .by(outV().values('type'))
        .limit({max_hospitals})
    """
    adopters = execute_query(client, adopters_query)

    # Get influence relationships (learned_from edges)
    influence_query = f"""
    g.E().hasLabel('learned_from')
        .has('protocol_context', TextP.containing('{safe_protocol}'))
        .project('from', 'to', 'interaction_type')
        .by(outV().values('name'))
        .by(inV().values('name'))
        .by('interaction_type')
    """
    influences = execute_query(client, influence_query)

    if not adopters:
        escaped_protocol = escape_label(protocol_name)
        return f'```mermaid\ngraph LR\n    NO_DATA["No adoption data found for {escaped_protocol}"]\n```'

    # Classify adopters into waves
    hospital_waves = {}
    hospital_compliance = {}
    for adopter in adopters:
        hospital = adopter.get('hospital', '')
        adoption_date = adopter.get('adoption_date', '')
        compliance = adopter.get('compliance_rate', 0)

        wave = _classify_adoption_wave(adoption_date, release_date) if show_timeline else "mid"
        hospital_waves[hospital] = wave
        hospital_compliance[hospital] = compliance

    # Build diagram
    lines = []

    # Add title
    lines.append("---")
    lines.append(f'title: "Protocol Spread: {escape_label(protocol_name)}"')
    lines.append("---")
    lines.append("graph LR")

    # Group hospitals by wave if showing timeline
    if show_timeline:
        waves = {"early": [], "mid": [], "late": []}
        for hospital, wave in hospital_waves.items():
            waves[wave].append(hospital)

        # Add subgraphs for each wave
        wave_labels = {
            "early": "Early Adopters (0-6 months)",
            "mid": "Mid Adopters (6-12 months)",
            "late": "Late Adopters (12+ months)"
        }

        for wave_key, hospitals in waves.items():
            if hospitals:
                lines.append(f"    subgraph {wave_key}[{wave_labels[wave_key]}]")
                for hospital in hospitals:
                    node_id = sanitize_node_id(hospital)
                    escaped_name = escape_label(hospital)
                    compliance = hospital_compliance.get(hospital, 0)
                    lines.append(f'        {node_id}["{escaped_name}<br/>{compliance}%"]')
                lines.append("    end")
    else:
        # No grouping, just add all nodes
        for hospital in hospital_waves.keys():
            node_id = sanitize_node_id(hospital)
            escaped_name = escape_label(hospital)
            compliance = hospital_compliance.get(hospital, 0)
            lines.append(f'    {node_id}["{escaped_name}<br/>{compliance}%"]')

    lines.append("")

    # Add influence edges
    for influence in influences:
        from_hospital = influence.get('from', '')
        to_hospital = influence.get('to', '')
        interaction_type = influence.get('interaction_type', '')

        # Only add edge if both hospitals are in our adopters list
        if from_hospital in hospital_waves and to_hospital in hospital_waves:
            from_id = sanitize_node_id(from_hospital)
            to_id = sanitize_node_id(to_hospital)

            # Abbreviate interaction type for edge label
            type_abbrev = {
                "site_visit": "visit",
                "webinar": "web",
                "collaborative_meeting": "collab",
                "peer_consult": "consult",
                "publication": "pub",
                "conference_presentation": "conf"
            }
            label = type_abbrev.get(interaction_type, interaction_type[:6])
            lines.append(f'    {from_id} -->|"{label}"| {to_id}')

    lines.append("")

    # Add styles
    for hospital, wave in hospital_waves.items():
        node_id = sanitize_node_id(hospital)
        style = _get_wave_style(wave)
        lines.append(f"    style {node_id} {style}")

    # Add legend if showing timeline
    if show_timeline:
        lines.append("")
        lines.append("    subgraph Legend[Legend]")
        lines.append('        LE["Early (0-6 mo)"]')
        lines.append('        LM["Mid (6-12 mo)"]')
        lines.append('        LL["Late (12+ mo)"]')
        lines.append("    end")
        lines.append(f"    style LE fill:{ADOPTION_COLORS['early']},color:#fff")
        lines.append(f"    style LM fill:{ADOPTION_COLORS['mid']},color:#000")
        lines.append(f"    style LL fill:{ADOPTION_COLORS['late']},color:#fff")

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"
```

### Phase 3: Create Sample Data

#### Task 3.1: Create `src/domains/quality_improvement/sample_data.py`

```python
"""
Sample data definitions for quality improvement domain.

Used by scripts/load_quality_improvement_data.py to populate test data.
"""

SAMPLE_PROTOCOLS = [
    {
        "id": "proto-001",
        "name": "Sepsis Bundle v2.0",
        "category": "infection_control",
        "release_date": "2024-01-15",
        "source": "CHA IPSO Collaborative",
        "evidence_level": "high",
        "description": "Evidence-based bundle for early sepsis recognition and treatment",
        "version": "2.0"
    },
    {
        "id": "proto-002",
        "name": "CLABSI Prevention Bundle",
        "category": "infection_control",
        "release_date": "2023-06-01",
        "source": "CHA Quality Collaborative",
        "evidence_level": "high",
        "description": "Central line-associated bloodstream infection prevention",
        "version": "1.5"
    },
    {
        "id": "proto-003",
        "name": "Pediatric Early Warning Score",
        "category": "safety",
        "release_date": "2023-09-15",
        "source": "CHA Safety Committee",
        "evidence_level": "moderate",
        "description": "Standardized assessment for detecting clinical deterioration",
        "version": "1.0"
    },
    {
        "id": "proto-004",
        "name": "Safe Medication Administration",
        "category": "medication_safety",
        "release_date": "2024-03-01",
        "source": "CHA Pharmacy Network",
        "evidence_level": "high",
        "description": "Five rights verification and barcode scanning protocol",
        "version": "2.0"
    }
]

SAMPLE_METRICS = [
    {
        "id": "metric-001",
        "name": "Sepsis Mortality Rate",
        "unit": "percentage",
        "direction": "lower_better",
        "benchmark": 5.0,
        "data_source": "PHIS"
    },
    {
        "id": "metric-002",
        "name": "Time to Antibiotics",
        "unit": "minutes",
        "direction": "lower_better",
        "benchmark": 60,
        "data_source": "PHIS"
    },
    {
        "id": "metric-003",
        "name": "CLABSI Rate",
        "unit": "per 1000 line days",
        "direction": "lower_better",
        "benchmark": 1.0,
        "data_source": "NHSN"
    },
    {
        "id": "metric-004",
        "name": "Unplanned ICU Transfers",
        "unit": "per 1000 patient days",
        "direction": "lower_better",
        "benchmark": 5.0,
        "data_source": "Internal"
    }
]

# Hospital IDs from referral_network sample data
SAMPLE_ADOPTIONS = [
    # Sepsis Bundle - tertiary centers adopted early
    {"hospital": "hosp-001", "protocol": "proto-001", "adoption_date": "2024-02-15", "compliance_rate": 94.2, "adoption_phase": "full", "champion": "Dr. Sarah Chen"},
    {"hospital": "hosp-002", "protocol": "proto-001", "adoption_date": "2024-03-01", "compliance_rate": 91.0, "adoption_phase": "full", "champion": "Dr. Michael Roberts"},
    {"hospital": "hosp-003", "protocol": "proto-001", "adoption_date": "2024-04-01", "compliance_rate": 88.5, "adoption_phase": "full", "champion": "Dr. James Park"},
    {"hospital": "hosp-008", "protocol": "proto-001", "adoption_date": "2024-05-15", "compliance_rate": 86.0, "adoption_phase": "partial", "champion": "Dr. Lisa Martinez"},
    # Regional hospitals adopted later
    {"hospital": "hosp-007", "protocol": "proto-001", "adoption_date": "2024-09-01", "compliance_rate": 78.0, "adoption_phase": "partial", "champion": "Dr. Amy Wilson"},

    # CLABSI Prevention - earlier protocol, more adoptions
    {"hospital": "hosp-001", "protocol": "proto-002", "adoption_date": "2023-07-15", "compliance_rate": 96.0, "adoption_phase": "full", "champion": "Dr. Sarah Chen"},
    {"hospital": "hosp-002", "protocol": "proto-002", "adoption_date": "2023-08-01", "compliance_rate": 94.5, "adoption_phase": "full", "champion": "Dr. Emily Watson"},
    {"hospital": "hosp-003", "protocol": "proto-002", "adoption_date": "2023-09-01", "compliance_rate": 92.0, "adoption_phase": "full", "champion": "Dr. James Park"},
    {"hospital": "hosp-007", "protocol": "proto-002", "adoption_date": "2024-01-15", "compliance_rate": 85.0, "adoption_phase": "full", "champion": "Dr. Amy Wilson"},
    {"hospital": "hosp-008", "protocol": "proto-002", "adoption_date": "2024-02-01", "compliance_rate": 88.0, "adoption_phase": "full", "champion": "Dr. Lisa Martinez"},
]

SAMPLE_LEARNED_FROM = [
    # Sepsis Bundle spread pattern
    {"from_hospital": "hosp-001", "to_hospital": "hosp-002", "interaction_type": "collaborative_meeting", "date": "2024-02-01", "protocol_context": "Sepsis Bundle v2.0", "effectiveness_rating": 5},
    {"from_hospital": "hosp-001", "to_hospital": "hosp-003", "interaction_type": "site_visit", "date": "2024-03-15", "protocol_context": "Sepsis Bundle v2.0", "effectiveness_rating": 5},
    {"from_hospital": "hosp-002", "to_hospital": "hosp-008", "interaction_type": "webinar", "date": "2024-04-20", "protocol_context": "Sepsis Bundle v2.0", "effectiveness_rating": 4},
    {"from_hospital": "hosp-003", "to_hospital": "hosp-007", "interaction_type": "peer_consult", "date": "2024-07-10", "protocol_context": "Sepsis Bundle v2.0", "effectiveness_rating": 4},

    # CLABSI spread pattern
    {"from_hospital": "hosp-001", "to_hospital": "hosp-002", "interaction_type": "conference_presentation", "date": "2023-06-15", "protocol_context": "CLABSI Prevention Bundle", "effectiveness_rating": 5},
    {"from_hospital": "hosp-001", "to_hospital": "hosp-003", "interaction_type": "site_visit", "date": "2023-08-01", "protocol_context": "CLABSI Prevention Bundle", "effectiveness_rating": 5},
    {"from_hospital": "hosp-002", "to_hospital": "hosp-007", "interaction_type": "webinar", "date": "2023-11-15", "protocol_context": "CLABSI Prevention Bundle", "effectiveness_rating": 4},
    {"from_hospital": "hosp-003", "to_hospital": "hosp-008", "interaction_type": "peer_consult", "date": "2024-01-10", "protocol_context": "CLABSI Prevention Bundle", "effectiveness_rating": 4},
]

SAMPLE_OUTCOMES = [
    # Sepsis Bundle outcomes
    {"hospital": "hosp-001", "metric": "metric-001", "baseline": 7.5, "current": 3.2, "measurement_period": "Q4-2025", "sample_size": 150},
    {"hospital": "hosp-001", "metric": "metric-002", "baseline": 95, "current": 52, "measurement_period": "Q4-2025", "sample_size": 150},
    {"hospital": "hosp-002", "metric": "metric-001", "baseline": 8.0, "current": 4.1, "measurement_period": "Q4-2025", "sample_size": 120},
    {"hospital": "hosp-003", "metric": "metric-001", "baseline": 7.2, "current": 4.5, "measurement_period": "Q4-2025", "sample_size": 135},

    # CLABSI outcomes
    {"hospital": "hosp-001", "metric": "metric-003", "baseline": 2.1, "current": 0.8, "measurement_period": "Q4-2025", "sample_size": 8500},
    {"hospital": "hosp-002", "metric": "metric-003", "baseline": 1.9, "current": 0.7, "measurement_period": "Q4-2025", "sample_size": 9200},
    {"hospital": "hosp-003", "metric": "metric-003", "baseline": 2.3, "current": 1.0, "measurement_period": "Q4-2025", "sample_size": 7800},
]

SAMPLE_MEASURES = [
    {"protocol": "proto-001", "metric": "metric-001", "weight": 0.6, "target_improvement": 40.0, "is_primary": True},
    {"protocol": "proto-001", "metric": "metric-002", "weight": 0.4, "target_improvement": 35.0, "is_primary": False},
    {"protocol": "proto-002", "metric": "metric-003", "weight": 1.0, "target_improvement": 50.0, "is_primary": True},
    {"protocol": "proto-003", "metric": "metric-004", "weight": 1.0, "target_improvement": 30.0, "is_primary": True},
]
```

#### Task 3.2: Create `scripts/load_quality_improvement_data.py`

**Pattern Reference**: `scripts/load_sample_data.py:1-293`

```python
#!/usr/bin/env python3
"""
Load sample quality improvement data into Cosmos DB Gremlin.

This script adds protocol adoption, learning relationships, and outcome
data to the existing hospital graph.

IMPORTANT: Run scripts/load_sample_data.py first to ensure hospital
vertices exist.
"""
import sys
import os

# Add parent directory to path for src/ imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.core.cosmos_connection import get_client, execute_query
from src.domains.quality_improvement.sample_data import (
    SAMPLE_PROTOCOLS,
    SAMPLE_METRICS,
    SAMPLE_ADOPTIONS,
    SAMPLE_LEARNED_FROM,
    SAMPLE_OUTCOMES,
    SAMPLE_MEASURES,
)


def verify_hospitals_exist(client) -> bool:
    """Verify that hospital vertices exist (from referral_network data)."""
    count = execute_query(client, "g.V().hasLabel('hospital').count()")[0]
    if count == 0:
        print("ERROR: No hospital vertices found!")
        print("Please run 'python scripts/load_sample_data.py' first.")
        return False
    print(f"Found {count} hospital vertices.")
    return True


def clean_quality_improvement_data(client):
    """Remove only quality improvement vertices and edges."""
    print("Cleaning existing quality improvement data...")

    # Remove edges first
    execute_query(client, "g.E().hasLabel('adopted').drop()")
    execute_query(client, "g.E().hasLabel('learned_from').drop()")
    execute_query(client, "g.E().hasLabel('achieved').drop()")
    execute_query(client, "g.E().hasLabel('measures').drop()")

    # Remove vertices
    execute_query(client, "g.V().hasLabel('protocol').drop()")
    execute_query(client, "g.V().hasLabel('outcome_metric').drop()")

    print("Quality improvement data cleared.")


def load_protocols(client):
    """Load protocol vertices."""
    print(f"Loading {len(SAMPLE_PROTOCOLS)} protocols...")

    for p in SAMPLE_PROTOCOLS:
        query = """
        g.addV('protocol')
          .property('id', id)
          .property('partitionKey', pk)
          .property('name', name)
          .property('category', category)
          .property('release_date', release_date)
          .property('source', source)
          .property('evidence_level', evidence_level)
          .property('description', description)
          .property('version', version)
        """
        bindings = {
            'id': p['id'],
            'pk': 'protocol',
            'name': p['name'],
            'category': p['category'],
            'release_date': p['release_date'],
            'source': p['source'],
            'evidence_level': p['evidence_level'],
            'description': p['description'],
            'version': p['version']
        }
        execute_query(client, query, bindings)
        print(f"  Added: {p['name']}")

    print("Protocols loaded.")


def load_metrics(client):
    """Load outcome metric vertices."""
    print(f"Loading {len(SAMPLE_METRICS)} outcome metrics...")

    for m in SAMPLE_METRICS:
        query = """
        g.addV('outcome_metric')
          .property('id', id)
          .property('partitionKey', pk)
          .property('name', name)
          .property('unit', unit)
          .property('direction', direction)
          .property('benchmark', benchmark)
          .property('data_source', data_source)
        """
        bindings = {
            'id': m['id'],
            'pk': 'outcome_metric',
            'name': m['name'],
            'unit': m['unit'],
            'direction': m['direction'],
            'benchmark': m['benchmark'],
            'data_source': m['data_source']
        }
        execute_query(client, query, bindings)
        print(f"  Added: {m['name']}")

    print("Outcome metrics loaded.")


def load_adoption_edges(client):
    """Load hospital-protocol adoption edges."""
    print(f"Loading {len(SAMPLE_ADOPTIONS)} adoption relationships...")

    for a in SAMPLE_ADOPTIONS:
        query = """
        g.V().has('hospital', 'id', hosp_id)
          .addE('adopted')
          .to(g.V().has('protocol', 'id', proto_id))
          .property('adoption_date', adoption_date)
          .property('compliance_rate', compliance_rate)
          .property('adoption_phase', adoption_phase)
          .property('champion', champion)
        """
        bindings = {
            'hosp_id': a['hospital'],
            'proto_id': a['protocol'],
            'adoption_date': a['adoption_date'],
            'compliance_rate': a['compliance_rate'],
            'adoption_phase': a['adoption_phase'],
            'champion': a['champion']
        }
        execute_query(client, query, bindings)
        print(f"  Added: {a['hospital']} adopted {a['protocol']}")

    print("Adoption edges loaded.")


def load_learned_from_edges(client):
    """Load hospital-hospital learned_from edges."""
    print(f"Loading {len(SAMPLE_LEARNED_FROM)} learning relationships...")

    for l in SAMPLE_LEARNED_FROM:
        query = """
        g.V().has('hospital', 'id', from_id)
          .addE('learned_from')
          .to(g.V().has('hospital', 'id', to_id))
          .property('interaction_type', interaction_type)
          .property('date', date)
          .property('protocol_context', protocol_context)
          .property('effectiveness_rating', effectiveness_rating)
        """
        bindings = {
            'from_id': l['to_hospital'],  # Note: edge direction is TO learned FROM
            'to_id': l['from_hospital'],
            'interaction_type': l['interaction_type'],
            'date': l['date'],
            'protocol_context': l['protocol_context'],
            'effectiveness_rating': l['effectiveness_rating']
        }
        execute_query(client, query, bindings)
        print(f"  Added: {l['to_hospital']} learned from {l['from_hospital']}")

    print("Learning edges loaded.")


def load_outcome_edges(client):
    """Load hospital-metric achieved edges."""
    print(f"Loading {len(SAMPLE_OUTCOMES)} outcome measurements...")

    for o in SAMPLE_OUTCOMES:
        query = """
        g.V().has('hospital', 'id', hosp_id)
          .addE('achieved')
          .to(g.V().has('outcome_metric', 'id', metric_id))
          .property('baseline', baseline)
          .property('current', current)
          .property('measurement_period', measurement_period)
          .property('sample_size', sample_size)
        """
        bindings = {
            'hosp_id': o['hospital'],
            'metric_id': o['metric'],
            'baseline': o['baseline'],
            'current': o['current'],
            'measurement_period': o['measurement_period'],
            'sample_size': o['sample_size']
        }
        execute_query(client, query, bindings)
        print(f"  Added: {o['hospital']} -> {o['metric']}")

    print("Outcome edges loaded.")


def load_measures_edges(client):
    """Load protocol-metric measures edges."""
    print(f"Loading {len(SAMPLE_MEASURES)} protocol-metric relationships...")

    for m in SAMPLE_MEASURES:
        query = """
        g.V().has('protocol', 'id', proto_id)
          .addE('measures')
          .to(g.V().has('outcome_metric', 'id', metric_id))
          .property('weight', weight)
          .property('target_improvement', target_improvement)
          .property('is_primary', is_primary)
        """
        bindings = {
            'proto_id': m['protocol'],
            'metric_id': m['metric'],
            'weight': m['weight'],
            'target_improvement': m['target_improvement'],
            'is_primary': m['is_primary']
        }
        execute_query(client, query, bindings)
        print(f"  Added: {m['protocol']} measures {m['metric']}")

    print("Measures edges loaded.")


def verify_data(client):
    """Verify loaded data with counts."""
    print("\n--- Quality Improvement Data Verification ---")

    protocol_count = execute_query(client, "g.V().hasLabel('protocol').count()")[0]
    print(f"Protocols: {protocol_count}")

    metric_count = execute_query(client, "g.V().hasLabel('outcome_metric').count()")[0]
    print(f"Outcome Metrics: {metric_count}")

    adopted_count = execute_query(client, "g.E().hasLabel('adopted').count()")[0]
    print(f"Adoption relationships: {adopted_count}")

    learned_count = execute_query(client, "g.E().hasLabel('learned_from').count()")[0]
    print(f"Learning relationships: {learned_count}")

    achieved_count = execute_query(client, "g.E().hasLabel('achieved').count()")[0]
    print(f"Outcome measurements: {achieved_count}")

    measures_count = execute_query(client, "g.E().hasLabel('measures').count()")[0]
    print(f"Protocol-metric relationships: {measures_count}")


def main():
    print("=" * 50)
    print("Quality Improvement Data Loader")
    print("=" * 50)

    client = get_client()

    try:
        # Verify prerequisites
        if not verify_hospitals_exist(client):
            return

        clean_quality_improvement_data(client)
        time.sleep(1)

        load_protocols(client)
        load_metrics(client)
        load_adoption_edges(client)
        load_learned_from_edges(client)
        load_outcome_edges(client)
        load_measures_edges(client)

        verify_data(client)

        print("\n Quality improvement data loading complete!")

    finally:
        client.close()


if __name__ == "__main__":
    main()
```

### Phase 4: Create Tests

#### Task 4.1: Create `tests/domains/quality_improvement/__init__.py`

```python
"""Tests for quality improvement domain."""
```

#### Task 4.2: Create `tests/domains/quality_improvement/test_tools.py`

**Pattern Reference**: `tests/core/test_tool_registry.py:1-170`

```python
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
```

#### Task 4.3: Create `tests/domains/quality_improvement/test_diagrams.py`

```python
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
```

### Phase 5: Update Configuration

#### Task 5.1: Update `config/domains.yaml`

Add the quality_improvement domain configuration (see Section 2.2).

---

## 4. Validation Gates

### 4.1 Syntax and Import Checks

```bash
# Check Python syntax for all new files
python -m py_compile src/domains/quality_improvement/__init__.py
python -m py_compile src/domains/quality_improvement/tools.py
python -m py_compile src/domains/quality_improvement/diagrams.py
python -m py_compile src/domains/quality_improvement/schema.py
python -m py_compile src/domains/quality_improvement/sample_data.py
python -m py_compile scripts/load_quality_improvement_data.py
```

### 4.2 Configuration Validation

```bash
# Validate config loads without errors
make validate-config

# Should show quality_improvement in enabled domains
make list-domains

# Should show all 17 tools (11 from referral_network + 6 from quality_improvement)
make list-tools
```

### 4.3 Unit Tests

```bash
# Run all quality improvement tests
pytest tests/domains/quality_improvement/ -v

# Run with coverage
pytest tests/domains/quality_improvement/ -v --cov=src/domains/quality_improvement
```

### 4.4 Integration Tests

```bash
# Load sample data (requires referral_network data loaded first)
python scripts/load_sample_data.py
python scripts/load_quality_improvement_data.py

# Run integration tests
pytest tests/domains/quality_improvement/ -v -m integration
```

### 4.5 Full System Test

```bash
# Test full tool registry with both domains
python -c "
from src.core.tool_registry import ToolRegistry
r = ToolRegistry()
r.load_domains()
print(f'Domains: {r.get_enabled_domains()}')
print(f'Tools: {r.list_tools()}')
print(f'Total tools: {len(r.list_tools())}')

# Test a quality improvement tool
tool = r.get_tool('get_protocol_adoption_status')
result = tool('Sepsis Bundle v2.0')
print(f'Protocol adoption status: {result}')
"
```

---

## 5. External References

### 5.1 Gremlin Query Documentation

- **Apache TinkerPop Gremlin Reference**: https://tinkerpop.apache.org/docs/current/reference/
- **Cosmos DB Gremlin Support**: https://learn.microsoft.com/en-us/azure/cosmos-db/gremlin/support
- **TextP Predicates**: https://tinkerpop.apache.org/docs/current/reference/#textp-predicate

### 5.2 Key Gremlin Patterns Used

```groovy
// Pattern 1: Traversal from vertex through edge to related vertex
g.V().has('protocol', 'name', 'Sepsis Bundle')
    .inE('adopted')  // Incoming edges
    .outV()          // Source vertex of those edges

// Pattern 2: Multi-hop path traversal
g.V().has('hospital', 'name', 'Hospital A')
    .repeat(__.inE('learned_from').outV().simplePath())
    .until(__.loops().is(5))
    .path()

// Pattern 3: Graph pattern matching with where clause
g.V().hasLabel('hospital')
    .not(__.out('adopted').has('name', 'Sepsis Bundle'))  // Non-adopters
    .where(__.both('refers_to').out('adopted').has('name', 'Sepsis Bundle'))  // Connected to adopters
```

### 5.3 Mermaid Diagram Syntax

- **Mermaid Flowchart Docs**: https://mermaid.js.org/syntax/flowchart.html
- **Subgraphs**: https://mermaid.js.org/syntax/flowchart.html#subgraphs
- **Styling Nodes**: https://mermaid.js.org/syntax/flowchart.html#styling-a-node

---

## 6. Implementation Notes

### 6.1 Critical Gotchas

1. **Edge Direction for learned_from**: The `learned_from` edge goes FROM the learning hospital TO the teaching hospital. When Hospital B learns from Hospital A:
   ```python
   # Hospital B (learner) --learned_from--> Hospital A (teacher)
   g.V().has('hospital', 'id', 'hosp-B')
       .addE('learned_from')
       .to(g.V().has('hospital', 'id', 'hosp-A'))
   ```

2. **TextP.containing for Partial Matches**: Cosmos DB Gremlin requires `TextP.containing()` for partial string matching, not `has('name', containing('..'))`.

3. **valueMap Returns Lists**: Gremlin's `valueMap()` returns property values as lists even for single values. Use the `_clean_value_map()` helper.

4. **Dependency Order**: The `quality_improvement` domain must list `referral_network` in `depends_on` because it uses `hospital` vertices from that domain.

### 6.2 Performance Considerations

- Index `protocol.name` for fast lookups
- Index `adopted.adoption_date` for timeline queries
- Limit diagram queries to `max_hospitals` to prevent oversized diagrams

---

## 7. Task Checklist

### Phase 1: Domain Module Structure
- [ ] Create `src/domains/quality_improvement/__init__.py`
- [ ] Create `src/domains/quality_improvement/schema.py`

### Phase 2: Implement Tools
- [ ] Create `src/domains/quality_improvement/tools.py`
- [ ] Create `src/domains/quality_improvement/diagrams.py`

### Phase 3: Sample Data
- [ ] Create `src/domains/quality_improvement/sample_data.py`
- [ ] Create `scripts/load_quality_improvement_data.py`

### Phase 4: Tests
- [ ] Create `tests/domains/quality_improvement/__init__.py`
- [ ] Create `tests/domains/quality_improvement/test_tools.py`
- [ ] Create `tests/domains/quality_improvement/test_diagrams.py`

### Phase 5: Configuration
- [ ] Update `config/domains.yaml` with quality_improvement domain

### Phase 6: Validation
- [ ] Run `make validate-config`
- [ ] Run `make list-tools` (expect 17 tools)
- [ ] Run `python scripts/load_sample_data.py` (if not already done)
- [ ] Run `python scripts/load_quality_improvement_data.py`
- [ ] Run `pytest tests/domains/quality_improvement/ -v`

---

## 8. Quality Score

**Confidence Level: 8.5/10**

### Strengths
- Complete code examples for all files
- Clear patterns from existing `referral_network` domain
- Comprehensive test coverage plan
- Detailed Gremlin query patterns with gotchas documented
- Sample data that creates realistic adoption spread patterns

### Risks
- Complex Gremlin queries for path traversal may need tuning
- Edge direction semantics must be carefully maintained
- Integration tests require live Cosmos DB connection

### Mitigation
- Test each tool individually before integration
- Use mocked tests for unit testing, integration tests for live DB
- Validate sample data loading creates expected graph structure

---

## 9. Agent Instructions

When implementing this PRP:

1. **Create files in order**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. **Run validation gates after each phase** to catch issues early
3. **Load sample data BEFORE running integration tests**
4. **Pay attention to edge direction** for `learned_from` edges
5. **Use `TextP.containing()` for partial string matches** in Gremlin queries

The implementation is self-contained - all code is provided in this PRP. Follow the file structure exactly and the domain will integrate with the existing tool registry automatically.
