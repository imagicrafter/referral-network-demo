# Domain: Quality Improvement Protocol Spread

## Overview

| Attribute | Value |
|-----------|-------|
| **Domain ID** | `quality_improvement` |
| **Priority** | HIGH - Recommended as next implementation |
| **Depends On** | `referral_network` |
| **Estimated Effort** | 2-3 weeks |
| **CHA Alignment** | Transforming Quality Conference, IPSO Collaborative, Sepsis initiatives |

---

## Business Context

### Problem Statement

CHA coordinates quality improvement initiatives across 200+ children's hospitals. When a new protocol (like the Sepsis Bundle) is released, leadership needs to understand:

1. **Adoption tracking** - Which hospitals have adopted and at what compliance level?
2. **Spread patterns** - How did successful practices spread through the network?
3. **Gap identification** - Which non-adopting hospitals are best positioned for outreach?
4. **Isolation detection** - Are there clusters not receiving best practices?

### Why Graph Analytics?

Traditional dashboards show adoption rates and compliance scores. But they cannot answer:

- "Hospital X adopted early and has great outcomes. Which hospitals learned from them?"
- "What's the typical pathway a protocol takes to spread?"
- "Which non-adopters are most connected to successful adopters?"

These questions require **relationship traversal** - the core strength of graph databases.

### CHA Programs This Supports

- **IPSO Collaborative** - Improving Sepsis Outcomes
- **Transforming Quality Conference** - Annual quality improvement sharing
- **CLABSI Prevention** - Central line infection reduction
- **Pediatric Early Warning Score** - Early deterioration detection

---

## Power BI vs Agent Comparison

### Power BI Dashboard Shows (The "What")

| Visual | Metric | User Question Answered |
|--------|--------|------------------------|
| KPI Card | "73% adoption rate" | "How many hospitals have adopted?" |
| Timeline Chart | Adoption trend over 18 months | "Is adoption accelerating?" |
| Geographic Map | Color-coded by adoption status | "Which regions are lagging?" |
| Compliance Scorecard | Bundle compliance rates | "How well are hospitals following the protocol?" |
| Outcome Metrics | Mortality rate improvements | "Is the protocol working?" |

### Agent Answers (The "Why")

| User Question | Graph Capability Required | Power BI Limitation |
|---------------|---------------------------|---------------------|
| "Which hospitals learned from Children's Mercy KC?" | Outbound `learned_from` traversal | Cannot model influence relationships |
| "What's the typical spread pathway?" | Path pattern analysis | No path traversal capability |
| "Which non-adopters should we target first?" | Centrality analysis with adoption filter | Cannot combine network position with adoption status |
| "Are there isolated clusters?" | Connected component analysis | No graph algorithms |

---

## Graph Schema

### Vertex Types

#### `protocol`

Quality improvement protocol or care bundle.

```yaml
protocol:
  label: "protocol"
  properties:
    - name: name
      type: string
      required: true
      indexed: true
      example: "Sepsis Bundle v2.0"
      
    - name: category
      type: string
      required: true
      enum:
        - infection_control
        - safety
        - clinical_pathway
        - documentation
        - medication_safety
      example: "infection_control"
      
    - name: release_date
      type: date
      required: true
      format: "YYYY-MM-DD"
      example: "2024-01-15"
      
    - name: source
      type: string
      required: false
      description: "Originating organization or collaborative"
      example: "CHA IPSO Collaborative"
      
    - name: evidence_level
      type: string
      required: false
      enum:
        - high
        - moderate
        - low
        - expert_consensus
      example: "high"
      
    - name: description
      type: string
      required: false
      description: "Brief description of the protocol"
      
    - name: version
      type: string
      required: false
      example: "2.0"
```

#### `outcome_metric`

Measurable quality outcome linked to protocols.

```yaml
outcome_metric:
  label: "outcome_metric"
  properties:
    - name: name
      type: string
      required: true
      indexed: true
      example: "Sepsis Mortality Rate"
      
    - name: unit
      type: string
      required: true
      example: "percentage"
      
    - name: direction
      type: string
      required: true
      enum:
        - higher_better
        - lower_better
      example: "lower_better"
      description: "Whether improvement means increase or decrease"
      
    - name: benchmark
      type: float
      required: false
      description: "Target value representing good performance"
      example: 5.0
      
    - name: data_source
      type: string
      required: false
      example: "PHIS"
```

### Edge Types

#### `adopted`

Hospital adopted a protocol.

```yaml
adopted:
  label: "adopted"
  from_vertex: hospital
  to_vertex: protocol
  properties:
    - name: adoption_date
      type: date
      required: true
      format: "YYYY-MM-DD"
      example: "2024-03-01"
      
    - name: compliance_rate
      type: float
      required: false
      description: "Current compliance percentage (0-100)"
      example: 94.2
      
    - name: champion
      type: string
      required: false
      description: "Internal champion leading adoption"
      example: "Dr. Sarah Johnson"
      
    - name: adoption_phase
      type: string
      required: true
      enum:
        - pilot
        - partial
        - full
      example: "full"
      
    - name: notes
      type: string
      required: false
```

#### `learned_from`

Knowledge transfer between hospitals.

```yaml
learned_from:
  label: "learned_from"
  from_vertex: hospital
  to_vertex: hospital
  description: "Source hospital taught/influenced the destination hospital"
  properties:
    - name: interaction_type
      type: string
      required: true
      enum:
        - site_visit
        - webinar
        - collaborative_meeting
        - peer_consult
        - publication
        - conference_presentation
      example: "site_visit"
      
    - name: date
      type: date
      required: true
      format: "YYYY-MM-DD"
      example: "2024-04-15"
      
    - name: protocol_context
      type: string
      required: false
      description: "Which protocol the learning was about"
      example: "Sepsis Bundle v2.0"
      
    - name: effectiveness_rating
      type: integer
      required: false
      description: "1-5 rating of how helpful the interaction was"
      min: 1
      max: 5
      
    - name: topics_covered
      type: string
      required: false
      description: "Comma-separated list of topics discussed"
```

#### `achieved`

Hospital achieved outcome on a metric.

```yaml
achieved:
  label: "achieved"
  from_vertex: hospital
  to_vertex: outcome_metric
  properties:
    - name: baseline
      type: float
      required: true
      description: "Starting value before intervention"
      example: 8.2
      
    - name: current
      type: float
      required: true
      description: "Current measured value"
      example: 4.1
      
    - name: measurement_period
      type: string
      required: true
      description: "When the current value was measured"
      example: "Q3-2025"
      
    - name: sample_size
      type: integer
      required: false
      description: "Number of cases in measurement"
      example: 150
```

#### `measures`

Protocol is measured by an outcome metric.

```yaml
measures:
  label: "measures"
  from_vertex: protocol
  to_vertex: outcome_metric
  properties:
    - name: weight
      type: float
      required: false
      description: "Importance weight for composite scoring (0-1)"
      example: 0.4
      
    - name: target_improvement
      type: float
      required: false
      description: "Expected improvement percentage"
      example: 25.0
      
    - name: is_primary
      type: boolean
      required: false
      description: "Whether this is the primary outcome metric"
      default: false
```

---

## Agent Tools

### Tool: `get_protocol_adoption_status`

```python
def get_protocol_adoption_status(protocol_name: str) -> dict:
    """
    Get adoption status for a protocol across all hospitals.
    
    Use this tool when the user asks about:
    - How many hospitals have adopted a protocol
    - Which hospitals have/haven't adopted
    - Overall adoption rates and compliance levels
    
    Args:
        protocol_name: Name of the protocol (e.g., "Sepsis Bundle v2.0")
        
    Returns:
        {
            "protocol": "Sepsis Bundle v2.0",
            "release_date": "2024-01-15",
            "total_hospitals": 156,
            "adopted_count": 114,
            "adoption_rate": 73.1,
            "by_phase": {
                "full": 89,
                "partial": 18,
                "pilot": 7
            },
            "avg_compliance_rate": 87.3,
            "adopters": [
                {
                    "hospital": "Children's Mercy Kansas City",
                    "state": "MO",
                    "type": "tertiary",
                    "adoption_date": "2024-03-01",
                    "compliance_rate": 94.2,
                    "phase": "full"
                },
                ...
            ],
            "non_adopters": [
                {
                    "hospital": "Regional Medical Center",
                    "state": "MO",
                    "type": "regional"
                },
                ...
            ]
        }
    """
```

**Gremlin Query:**

```groovy
// Get protocol details
g.V().has('protocol', 'name', protocol_name).as('p')
    .project('protocol', 'release_date', 'adopters', 'all_hospitals')
    .by('name')
    .by('release_date')
    .by(
        __.in('adopted')
            .project('hospital', 'state', 'type', 'adoption_date', 'compliance_rate', 'phase')
            .by('name')
            .by('state')
            .by('type')
            .by(__.inE('adopted').values('adoption_date'))
            .by(__.inE('adopted').values('compliance_rate'))
            .by(__.inE('adopted').values('adoption_phase'))
            .fold()
    )
    .by(
        g.V().hasLabel('hospital').count()
    )
```

**Tool Definition (OpenAI format):**

```json
{
    "type": "function",
    "function": {
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
    }
}
```

---

### Tool: `find_adoption_gaps`

```python
def find_adoption_gaps(
    protocol_name: str, 
    min_connections: int = 2
) -> dict:
    """
    Find non-adopting hospitals with strong connections to successful adopters.
    These are high-potential targets for outreach.
    
    Use this tool when the user asks about:
    - Which hospitals to target for adoption outreach
    - Gaps in protocol spread
    - Non-adopters that should have adopted by now
    
    Args:
        protocol_name: Name of the protocol
        min_connections: Minimum connections to adopters to be considered high-potential
        
    Returns:
        {
            "protocol": "Sepsis Bundle v2.0",
            "analysis_date": "2025-01-15",
            "high_potential_targets": [
                {
                    "hospital": "Heartland Regional",
                    "state": "MO",
                    "type": "regional",
                    "connections_to_adopters": 5,
                    "connected_adopters": [
                        {
                            "name": "Children's Mercy KC",
                            "compliance": 94.2,
                            "connection_type": "referral"
                        },
                        {
                            "name": "St. Louis Children's",
                            "compliance": 91.0,
                            "connection_type": "referral"
                        }
                    ],
                    "recommendation": "High potential - strong referral ties to top performers"
                },
                ...
            ],
            "isolated_hospitals": [
                {
                    "hospital": "Ozark Medical Center",
                    "state": "MO",
                    "connections_to_adopters": 0,
                    "nearest_adopter": "Springfield Children's",
                    "hops_to_nearest": 3,
                    "recommendation": "Requires direct CHA intervention - no network connections"
                }
            ],
            "summary": {
                "high_potential_count": 12,
                "isolated_count": 5,
                "total_non_adopters": 42
            }
        }
    """
```

**Gremlin Query:**

```groovy
// Find non-adopters and count their connections to adopters
g.V().has('protocol', 'name', protocol_name).as('p')
    .V().hasLabel('hospital')
    .not(__.out('adopted').has('name', protocol_name))
    .as('non_adopter')
    .project('hospital', 'state', 'type', 'adopter_connections')
    .by('name')
    .by('state')
    .by('type')
    .by(
        __.both('refers_to', 'learned_from')
            .where(__.out('adopted').has('name', protocol_name))
            .dedup()
            .fold()
    )
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
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
    }
}
```

---

### Tool: `get_protocol_spread_path`

```python
def get_protocol_spread_path(
    protocol_name: str,
    hospital_name: str
) -> dict:
    """
    Trace how a protocol spread to reach a specific hospital.
    Shows the chain of influence (who learned from whom).
    
    Use this tool when the user asks about:
    - How a hospital learned about a protocol
    - The influence chain for adoption
    - Who taught whom about a practice
    
    Args:
        protocol_name: Name of the protocol
        hospital_name: Hospital to trace path to
        
    Returns:
        {
            "hospital": "Regional Medical Center",
            "protocol": "Sepsis Bundle v2.0",
            "adoption_date": "2024-08-15",
            "influence_chain": [
                {
                    "step": 1,
                    "from_hospital": "Children's Mercy KC",
                    "to_hospital": "St. Louis Children's",
                    "interaction_type": "collaborative_meeting",
                    "date": "2024-02-15"
                },
                {
                    "step": 2,
                    "from_hospital": "St. Louis Children's",
                    "to_hospital": "Regional Medical Center",
                    "interaction_type": "site_visit",
                    "date": "2024-07-01"
                }
            ],
            "original_source": "Children's Mercy KC",
            "chain_length": 2,
            "total_hospitals_influenced_by_source": 12
        }
    """
```

**Gremlin Query:**

```groovy
// Trace influence path to hospital
g.V().has('hospital', 'name', hospital_name)
    .repeat(
        __.inE('learned_from')
            .has('protocol_context', protocol_name)
            .outV()
            .simplePath()
    )
    .until(
        __.inE('learned_from')
            .has('protocol_context', protocol_name)
            .count().is(0)
        .or()
        .loops().is(5)
    )
    .path()
    .by(valueMap('name'))
    .by(valueMap('interaction_type', 'date'))
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
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
    }
}
```

---

### Tool: `find_quality_champions`

```python
def find_quality_champions(protocol_name: str = None) -> dict:
    """
    Identify hospitals that have influenced multiple others to adopt protocols.
    
    Use this tool when the user asks about:
    - Which hospitals are quality leaders
    - Who has the most influence in the network
    - Best hospitals to partner with for spreading practices
    
    Args:
        protocol_name: Optional - filter to specific protocol. If None, analyzes all protocols.
        
    Returns:
        {
            "champions": [
                {
                    "hospital": "Children's Mercy Kansas City",
                    "state": "MO",
                    "hospitals_influenced": 12,
                    "protocols_championed": [
                        "Sepsis Bundle v2.0",
                        "CLABSI Prevention Bundle"
                    ],
                    "avg_compliance_of_influenced": 88.5,
                    "influence_methods": {
                        "site_visit": 5,
                        "webinar": 4,
                        "collaborative_meeting": 3
                    },
                    "influence_score": 95.2
                },
                {
                    "hospital": "Boston Children's Hospital",
                    "state": "MA",
                    "hospitals_influenced": 10,
                    ...
                }
            ],
            "total_champions_identified": 15,
            "criteria": "Hospitals that influenced 3+ others with 85%+ compliance"
        }
    """
```

**Gremlin Query:**

```groovy
// Find quality champions - hospitals that have influenced many others
g.V().hasLabel('hospital')
    .where(
        __.out('adopted').has('compliance_rate', gte(85))
    )
    .project('hospital', 'state', 'influenced_count', 'protocols', 'methods')
    .by('name')
    .by('state')
    .by(__.in('learned_from').dedup().count())
    .by(__.out('adopted').values('name').dedup().fold())
    .by(__.inE('learned_from').values('interaction_type').groupCount())
    .where(select('influenced_count').is(gte(3)))
    .order().by(select('influenced_count'), decr)
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
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
    }
}
```

---

### Tool: `analyze_outcome_improvement`

```python
def analyze_outcome_improvement(
    protocol_name: str,
    metric_name: str = None
) -> dict:
    """
    Analyze outcome improvements for hospitals that adopted a protocol.
    
    Use this tool when the user asks about:
    - Whether a protocol is working
    - Which hospitals improved the most
    - Correlation between compliance and outcomes
    
    Args:
        protocol_name: Name of the protocol
        metric_name: Optional - specific metric to analyze
        
    Returns:
        {
            "protocol": "Sepsis Bundle v2.0",
            "analysis_period": "2024-01-01 to 2025-01-15",
            "metrics_analyzed": [
                {
                    "metric": "Sepsis Mortality Rate",
                    "unit": "percentage",
                    "direction": "lower_better",
                    "hospitals_with_data": 89,
                    "avg_baseline": 8.2,
                    "avg_current": 4.8,
                    "avg_improvement_pct": 41.5,
                    "top_improvers": [
                        {
                            "hospital": "Children's Mercy KC",
                            "baseline": 7.5,
                            "current": 3.2,
                            "improvement_pct": 57.3,
                            "compliance_rate": 94.2
                        },
                        ...
                    ],
                    "correlation_compliance_improvement": 0.73,
                    "statistical_significance": "p < 0.001"
                }
            ],
            "overall_summary": {
                "hospitals_improved": 78,
                "hospitals_unchanged": 8,
                "hospitals_worsened": 3,
                "avg_improvement_all_metrics": 38.2
            }
        }
    """
```

**Gremlin Query:**

```groovy
// Get outcome data for protocol adopters
g.V().has('protocol', 'name', protocol_name)
    .in('adopted').as('hospital')
    .outE('achieved').as('outcome')
    .inV().as('metric')
    .select('hospital', 'outcome', 'metric')
    .by(valueMap('name', 'compliance_rate'))
    .by(valueMap('baseline', 'current', 'measurement_period'))
    .by(valueMap('name', 'unit', 'direction'))
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "analyze_outcome_improvement",
        "description": "Analyze outcome improvements for hospitals that adopted a protocol. Shows baseline vs current metrics, improvement percentages, and correlation with compliance.",
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
    }
}
```

---

### Tool: `generate_adoption_spread_diagram`

```python
def generate_adoption_spread_diagram(
    protocol_name: str,
    show_timeline: bool = True,
    max_hospitals: int = 30
) -> dict:
    """
    Generate a Mermaid diagram showing how a protocol spread through the network.
    
    Use this tool when the user asks to:
    - Visualize protocol spread
    - Show adoption patterns
    - Draw/display the influence network
    
    Args:
        protocol_name: Name of the protocol
        show_timeline: Whether to color-code by adoption timing
        max_hospitals: Maximum number of hospitals to include
        
    Returns:
        {
            "diagram": "graph LR\\n    subgraph Early Adopters...",
            "diagram_type": "mermaid",
            "hospitals_shown": 28,
            "adoption_waves": 3,
            "legend": {
                "green": "Early adopters (first 6 months)",
                "yellow": "Mid adopters (6-12 months)",
                "orange": "Late adopters (12+ months)",
                "red": "Not yet adopted"
            }
        }
    
    Diagram Features:
        - Color coding by adoption timing
        - Edge labels show interaction type
        - Subgraphs group hospitals by adoption wave
        - Node annotations show compliance rate
    """
```

**Diagram Generation Logic:**

```python
def _build_adoption_diagram(protocol_name: str, show_timeline: bool) -> str:
    """Build Mermaid diagram for protocol spread."""
    
    # Get adoption data
    adopters = _get_adopters_with_dates(protocol_name)
    influences = _get_influence_edges(protocol_name)
    
    # Classify into waves
    waves = _classify_adoption_waves(adopters)
    
    # Build diagram
    lines = ["graph LR"]
    
    # Add subgraphs for each wave
    for wave_name, hospitals in waves.items():
        lines.append(f"    subgraph {wave_name}")
        for h in hospitals:
            node_id = _sanitize_id(h['name'])
            label = f"{h['name']}<br/>{h['compliance_rate']}%"
            color = _get_wave_color(wave_name)
            lines.append(f"        {node_id}[\"{label}\"]")
        lines.append("    end")
    
    # Add influence edges
    for edge in influences:
        from_id = _sanitize_id(edge['from'])
        to_id = _sanitize_id(edge['to'])
        label = edge['interaction_type']
        lines.append(f"    {from_id} -->|{label}| {to_id}")
    
    # Add styling
    lines.extend(_get_style_definitions())
    
    return "\n".join(lines)
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
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
                    "default": true
                },
                "max_hospitals": {
                    "type": "integer",
                    "description": "Maximum hospitals to include in diagram (default: 30)",
                    "default": 30
                }
            },
            "required": ["protocol_name"]
        }
    }
}
```

---

## Sample Data

### Sample Protocols

```python
SAMPLE_PROTOCOLS = [
    {
        "name": "Sepsis Bundle v2.0",
        "category": "infection_control",
        "release_date": "2024-01-15",
        "source": "CHA IPSO Collaborative",
        "evidence_level": "high",
        "description": "Evidence-based bundle for early sepsis recognition and treatment"
    },
    {
        "name": "CLABSI Prevention Bundle",
        "category": "infection_control",
        "release_date": "2023-06-01",
        "source": "CHA Quality Collaborative",
        "evidence_level": "high",
        "description": "Central line-associated bloodstream infection prevention"
    },
    {
        "name": "Pediatric Early Warning Score",
        "category": "safety",
        "release_date": "2023-09-15",
        "source": "CHA Safety Committee",
        "evidence_level": "moderate",
        "description": "Standardized assessment for detecting clinical deterioration"
    },
    {
        "name": "Safe Medication Administration",
        "category": "medication_safety",
        "release_date": "2024-03-01",
        "source": "CHA Pharmacy Network",
        "evidence_level": "high",
        "description": "Five rights verification and barcode scanning protocol"
    }
]
```

### Sample Outcome Metrics

```python
SAMPLE_METRICS = [
    {
        "name": "Sepsis Mortality Rate",
        "unit": "percentage",
        "direction": "lower_better",
        "benchmark": 5.0,
        "data_source": "PHIS"
    },
    {
        "name": "Time to Antibiotics",
        "unit": "minutes",
        "direction": "lower_better",
        "benchmark": 60,
        "data_source": "PHIS"
    },
    {
        "name": "CLABSI Rate",
        "unit": "per 1000 line days",
        "direction": "lower_better",
        "benchmark": 1.0,
        "data_source": "NHSN"
    },
    {
        "name": "Unplanned ICU Transfers",
        "unit": "per 1000 patient days",
        "direction": "lower_better",
        "benchmark": 5.0,
        "data_source": "Internal"
    }
]
```

### Sample Adoption Pattern

```python
def generate_sample_adoptions(hospitals: list, protocol: dict) -> list:
    """
    Generate realistic adoption patterns.
    
    Pattern:
    - Tertiary centers adopt first (within 3 months)
    - Regional hospitals connected to tertiary centers adopt next (3-9 months)
    - Rural/isolated hospitals adopt last or not at all (9+ months)
    """
    adoptions = []
    
    # Wave 1: Tertiary centers (early adopters)
    tertiary = [h for h in hospitals if h['type'] == 'tertiary']
    for h in tertiary[:5]:
        adoptions.append({
            "hospital": h['name'],
            "protocol": protocol['name'],
            "adoption_date": _random_date_in_range(0, 90),  # First 3 months
            "compliance_rate": random.uniform(85, 98),
            "adoption_phase": "full",
            "champion": f"Dr. {fake.last_name()}"
        })
    
    # Wave 2: Connected regional hospitals (mid adopters)
    # ... continue pattern
    
    return adoptions
```

---

## Configuration

### domains.yaml Entry

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
  
  module: "quality_improvement"
  
  tools:
    - get_protocol_adoption_status
    - find_adoption_gaps
    - get_protocol_spread_path
    - find_quality_champions
    - analyze_outcome_improvement
    - generate_adoption_spread_diagram
  
  schema:
    vertex_types:
      - protocol
      - outcome_metric
    edge_types:
      - adopted
      - learned_from
      - achieved
      - measures
```

---

## Implementation Notes

### Key Gremlin Patterns

```groovy
// Pattern 1: Multi-hop influence traversal
g.V().has('hospital', 'name', 'Children\'s Mercy KC')
    .repeat(__.out('learned_from').simplePath())
    .times(3)
    .dedup()
    .values('name')

// Pattern 2: Gap analysis - non-adopters near adopters
g.V().has('protocol', 'name', 'Sepsis Bundle')
    .in('adopted').has('compliance_rate', gte(90)).as('adopter')
    .both('refers_to')
    .not(__.out('adopted').has('name', 'Sepsis Bundle'))
    .dedup()
    .project('hospital', 'connected_to')
    .by('name')
    .by(select('adopter').values('name'))

// Pattern 3: Influence ranking
g.V().hasLabel('hospital')
    .project('name', 'influence_score')
    .by('name')
    .by(__.in('learned_from').dedup().count())
    .order().by(select('influence_score'), decr)
```

### Dependencies on Referral Network

This domain uses existing `hospital` vertices and `refers_to` edges from the referral network. The `learned_from` edge type often parallels referral relationships - hospitals learn from those they refer to or receive referrals from.

### Performance Considerations

- Index `protocol.name` for fast lookups
- Index `adopted.adoption_date` for timeline queries
- Consider materializing influence scores if queried frequently

---

*Document Version: 1.0*  
*Last Updated: January 2026*
