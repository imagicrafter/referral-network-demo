# Domain: Antimicrobial Stewardship Network

## Overview

| Attribute | Value |
|-----------|-------|
| **Domain ID** | `antimicrobial_stewardship` |
| **Priority** | LOW (specialized use case) |
| **Depends On** | `referral_network`, `quality_improvement` |
| **Estimated Effort** | 3-4 weeks |
| **CHA Alignment** | Antimicrobial Stewardship Dashboard, PHIS Data |

---

## Business Context

### Problem Statement

CHA has a dedicated antimicrobial stewardship dashboard that tracks antibiotic usage and resistance patterns. This domain extends that capability with network analysis to understand:

- How do stewardship practices spread between hospitals?
- Which hospitals are leaders in antimicrobial stewardship?
- Are there correlations between stewardship adoption and resistance patterns?
- What's the regional impact of stewardship programs?

### Why Graph Analytics?

Antimicrobial resistance is a network problem:
- Resistance patterns can spread through patient transfers
- Best practices spread through hospital collaborations
- Regional stewardship programs create interconnected improvements

Graph analysis connects practice adoption to outcome patterns.

### CHA Programs This Supports

- **Antimicrobial Stewardship Dashboard** - PHIS-based antibiotic tracking
- **Infection Prevention Collaboratives** - Multi-hospital stewardship initiatives
- **Antibiotic Resistance Research** - PHIS research network studies
- **CDC Partnership** - National antimicrobial stewardship efforts

---

## Power BI vs Agent Comparison

### Power BI Dashboard Shows (The "What")

| Visual | Metric | User Question Answered |
|--------|--------|------------------------|
| Antibiotic Utilization | Days of therapy per 1000 patient days | "How much are we using antibiotics?" |
| Broad-spectrum Usage | % broad vs narrow spectrum | "Are we using appropriate agents?" |
| Resistance Trends | Resistance rates over time | "Is resistance increasing?" |
| Peer Comparison | Benchmark vs similar hospitals | "How do we compare?" |

### Agent Answers (The "Why")

| User Question | Graph Capability Required | Power BI Limitation |
|---------------|---------------------------|---------------------|
| "How did the new pneumonia protocol spread through our region?" | Protocol adoption traversal | Cannot track spread patterns |
| "Which hospitals have successfully reduced broad-spectrum use?" | Outcome correlation with adoption | Limited cause-effect analysis |
| "Is there a relationship between our referral partners' resistance patterns and ours?" | Cross-hospital correlation via referral edges | No network correlation |
| "Who should we learn from to improve our gram-negative resistance?" | Best practice identification via graph | Static benchmarking only |

---

## Graph Schema

### Vertex Types

#### `antimicrobial_protocol`

Stewardship guideline or protocol.

```yaml
antimicrobial_protocol:
  label: "antimicrobial_protocol"
  description: "Antimicrobial stewardship protocol or guideline"
  properties:
    - name: protocol_id
      type: string
      required: true
      indexed: true
      example: "asp_pneumonia_v2"
      
    - name: name
      type: string
      required: true
      example: "Community-Acquired Pneumonia Stewardship Protocol"
      
    - name: category
      type: string
      required: true
      enum:
        - empiric_therapy
        - de_escalation
        - duration_optimization
        - diagnostic_stewardship
        - prophylaxis
      example: "empiric_therapy"
      
    - name: target_condition
      type: string
      required: true
      example: "Community-Acquired Pneumonia"
      
    - name: target_organisms
      type: list
      required: false
      example: ["S. pneumoniae", "H. influenzae", "M. pneumoniae"]
      
    - name: key_recommendations
      type: list
      required: true
      example: [
        "Narrow-spectrum beta-lactam first-line",
        "48-hour IV to PO conversion",
        "5-day course for uncomplicated"
      ]
      
    - name: evidence_source
      type: string
      required: false
      example: "IDSA/PIDS Guidelines 2023"
      
    - name: release_date
      type: date
      required: true
      example: "2024-01-15"
      
    - name: version
      type: string
      required: false
      example: "2.0"
```

#### `organism`

Pathogen being treated.

```yaml
organism:
  label: "organism"
  description: "Bacterial pathogen relevant to stewardship"
  properties:
    - name: organism_id
      type: string
      required: true
      indexed: true
      example: "org_s_aureus"
      
    - name: name
      type: string
      required: true
      example: "Staphylococcus aureus"
      
    - name: gram_type
      type: string
      required: true
      enum:
        - gram_positive
        - gram_negative
        - atypical
        - fungal
      example: "gram_positive"
      
    - name: common_infections
      type: list
      required: false
      example: ["Skin/soft tissue", "Bacteremia", "Osteomyelitis"]
      
    - name: resistance_concerns
      type: list
      required: false
      example: ["MRSA", "Vancomycin-intermediate"]
```

#### `resistance_pattern`

Observed resistance data.

```yaml
resistance_pattern:
  label: "resistance_pattern"
  description: "Antibiotic resistance observation at a hospital"
  properties:
    - name: pattern_id
      type: string
      required: true
      indexed: true
      example: "res_mrsa_cmkc_2024"
      
    - name: organism
      type: string
      required: true
      example: "Staphylococcus aureus"
      
    - name: antibiotic
      type: string
      required: true
      example: "Oxacillin"
      
    - name: resistance_type
      type: string
      required: true
      enum:
        - susceptible
        - intermediate
        - resistant
      example: "resistant"
      
    - name: resistance_rate
      type: float
      required: true
      description: "Percentage of isolates resistant"
      example: 35.5
      
    - name: isolate_count
      type: integer
      required: false
      description: "Number of isolates tested"
      example: 245
      
    - name: measurement_period
      type: string
      required: true
      example: "2024-Q4"
      
    - name: trend
      type: string
      required: false
      enum:
        - increasing
        - stable
        - decreasing
      example: "stable"
```

#### `antibiotic`

Antimicrobial agent.

```yaml
antibiotic:
  label: "antibiotic"
  description: "Antimicrobial medication"
  properties:
    - name: antibiotic_id
      type: string
      required: true
      indexed: true
      example: "abx_ampicillin"
      
    - name: name
      type: string
      required: true
      example: "Ampicillin"
      
    - name: class
      type: string
      required: true
      example: "Penicillin"
      
    - name: spectrum
      type: string
      required: true
      enum:
        - narrow
        - moderate
        - broad
        - extended
      example: "moderate"
      
    - name: route
      type: list
      required: true
      example: ["IV", "PO"]
      
    - name: stewardship_tier
      type: string
      required: false
      enum:
        - unrestricted
        - guided
        - restricted
      description: "Stewardship restriction level"
      example: "unrestricted"
```

### Edge Types

#### `follows_protocol`

Hospital follows stewardship protocol.

```yaml
follows_protocol:
  label: "follows_protocol"
  from_vertex: hospital
  to_vertex: antimicrobial_protocol
  description: "Hospital has adopted this stewardship protocol"
  properties:
    - name: adoption_date
      type: date
      required: true
      example: "2024-03-01"
      
    - name: adherence_rate
      type: float
      required: false
      description: "Percentage of cases following protocol"
      example: 82.5
      
    - name: champion
      type: string
      required: false
      description: "Stewardship champion leading implementation"
      example: "Dr. Smith, ID"
      
    - name: customizations
      type: list
      required: false
      example: ["Added local antibiogram guidance"]
```

#### `observed_resistance`

Hospital observed resistance pattern.

```yaml
observed_resistance:
  label: "observed_resistance"
  from_vertex: hospital
  to_vertex: resistance_pattern
  description: "Hospital observed this resistance pattern"
  properties:
    - name: reporting_period
      type: string
      required: true
      example: "2024-Q4"
      
    - name: data_source
      type: string
      required: false
      enum:
        - clinical_lab
        - infection_control
        - antibiogram
      example: "antibiogram"
```

#### `effective_against`

Protocol is effective against organism.

```yaml
effective_against:
  label: "effective_against"
  from_vertex: antimicrobial_protocol
  to_vertex: organism
  description: "Protocol targets this organism"
  properties:
    - name: effectiveness_rating
      type: string
      required: true
      enum:
        - first_line
        - alternative
        - salvage
      example: "first_line"
      
    - name: expected_susceptibility
      type: float
      required: false
      description: "Expected susceptibility rate"
      example: 95.0
```

#### `shared_stewardship_with`

Stewardship collaboration between hospitals.

```yaml
shared_stewardship_with:
  label: "shared_stewardship_with"
  from_vertex: hospital
  to_vertex: hospital
  description: "Hospitals collaborate on stewardship efforts"
  properties:
    - name: collaboration_type
      type: string
      required: true
      enum:
        - shared_antibiogram
        - joint_protocol
        - regional_collaborative
        - mentorship
      example: "regional_collaborative"
      
    - name: start_date
      type: date
      required: false
      example: "2024-01-01"
      
    - name: protocols_shared
      type: list
      required: false
      example: ["asp_pneumonia_v2", "asp_uti_v1"]
```

---

## Agent Tools

### Tool: `get_stewardship_adoption_status`

```python
def get_stewardship_adoption_status(
    protocol_name: str = None,
    condition: str = None
) -> dict:
    """
    Get adoption status for antimicrobial stewardship protocols.
    
    Use this tool when the user asks about:
    - Which hospitals use a stewardship protocol
    - Stewardship program adoption
    - Protocol implementation status
    
    Args:
        protocol_name: Optional - specific protocol name
        condition: Optional - filter by target condition
        
    Returns:
        {
            "protocols_analyzed": [
                {
                    "protocol": "Community-Acquired Pneumonia Stewardship Protocol",
                    "category": "empiric_therapy",
                    "adoption_summary": {
                        "total_hospitals": 52,
                        "adopted_count": 38,
                        "adoption_rate": 73.1,
                        "avg_adherence_rate": 78.5
                    },
                    "top_performers": [
                        {
                            "hospital": "Children's Mercy KC",
                            "adherence_rate": 92.5,
                            "adoption_date": "2024-01-15"
                        }
                    ],
                    "non_adopters": [
                        {"hospital": "Regional Medical Center", "state": "MO"}
                    ]
                }
            ]
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "get_stewardship_adoption_status",
        "description": "Get adoption status for antimicrobial stewardship protocols. Shows which hospitals have implemented specific protocols and their adherence rates.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Specific protocol name to check"
                },
                "condition": {
                    "type": "string",
                    "description": "Filter by target condition (e.g., 'pneumonia', 'UTI')"
                }
            },
            "required": []
        }
    }
}
```

---

### Tool: `analyze_resistance_patterns`

```python
def analyze_resistance_patterns(
    organism: str,
    antibiotic: str = None,
    region: str = None
) -> dict:
    """
    Analyze antibiotic resistance patterns across hospitals.
    
    Use this tool when the user asks about:
    - Resistance rates
    - Resistance trends
    - Regional resistance patterns
    
    Args:
        organism: Organism name (e.g., "S. aureus")
        antibiotic: Optional - specific antibiotic
        region: Optional - geographic filter
        
    Returns:
        {
            "organism": "Staphylococcus aureus",
            "analysis_period": "2024",
            "resistance_summary": [
                {
                    "antibiotic": "Oxacillin",
                    "resistance_name": "MRSA",
                    "network_avg_rate": 32.5,
                    "trend": "stable",
                    "hospital_breakdown": [
                        {
                            "hospital": "Children's Mercy KC",
                            "rate": 28.5,
                            "vs_network": -4.0,
                            "isolates": 245
                        },
                        {
                            "hospital": "Regional Medical",
                            "rate": 42.0,
                            "vs_network": +9.5,
                            "isolates": 85
                        }
                    ]
                }
            ],
            "correlation_with_stewardship": {
                "protocol": "MRSA Decolonization Protocol",
                "hospitals_with_protocol_rate": 25.2,
                "hospitals_without_protocol_rate": 38.8,
                "difference": -13.6,
                "statistical_significance": "p < 0.01"
            }
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "analyze_resistance_patterns",
        "description": "Analyze antibiotic resistance patterns across hospitals. Shows rates, trends, and correlation with stewardship adoption.",
        "parameters": {
            "type": "object",
            "properties": {
                "organism": {
                    "type": "string",
                    "description": "Organism name (e.g., 'S. aureus', 'E. coli')"
                },
                "antibiotic": {
                    "type": "string",
                    "description": "Specific antibiotic to analyze"
                },
                "region": {
                    "type": "string",
                    "description": "Geographic region filter"
                }
            },
            "required": ["organism"]
        }
    }
}
```

---

### Tool: `find_stewardship_leaders`

```python
def find_stewardship_leaders(
    category: str = None,
    metric: str = "overall"
) -> dict:
    """
    Identify hospitals leading in antimicrobial stewardship.
    
    Use this tool when the user asks about:
    - Best stewardship programs
    - Who to learn from
    - Stewardship leaders
    
    Args:
        category: Optional - protocol category filter
        metric: Ranking metric (overall, adherence, utilization, resistance)
        
    Returns:
        {
            "ranking_metric": "overall",
            "leaders": [
                {
                    "rank": 1,
                    "hospital": "Children's Mercy Kansas City",
                    "stewardship_score": 94.5,
                    "metrics": {
                        "protocols_adopted": 8,
                        "avg_adherence": 91.2,
                        "broad_spectrum_reduction": -22.5,
                        "resistance_trends": "improving"
                    },
                    "notable_practices": [
                        "Real-time stewardship alerts",
                        "Prospective audit with feedback",
                        "Regional antibiogram leadership"
                    ],
                    "hospitals_mentored": 5
                }
            ],
            "improvement_opportunities": [
                {
                    "hospital": "Regional Medical Center",
                    "current_score": 62.0,
                    "gap_areas": ["Limited protocol adoption", "High broad-spectrum use"],
                    "recommended_mentor": "Children's Mercy KC"
                }
            ]
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "find_stewardship_leaders",
        "description": "Identify hospitals leading in antimicrobial stewardship. Ranks by various metrics and identifies mentorship opportunities.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Protocol category filter (empiric_therapy, de_escalation, etc.)"
                },
                "metric": {
                    "type": "string",
                    "description": "Ranking metric: overall, adherence, utilization, resistance",
                    "default": "overall"
                }
            },
            "required": []
        }
    }
}
```

---

### Tool: `analyze_stewardship_impact`

```python
def analyze_stewardship_impact(
    protocol_name: str,
    outcome_metric: str = "utilization"
) -> dict:
    """
    Analyze the impact of a stewardship protocol on outcomes.
    
    Use this tool when the user asks about:
    - Does stewardship work
    - Protocol effectiveness
    - Impact of stewardship programs
    
    Args:
        protocol_name: Protocol to analyze
        outcome_metric: Metric to measure (utilization, resistance, outcomes)
        
    Returns:
        {
            "protocol": "Community-Acquired Pneumonia Stewardship Protocol",
            "analysis_type": "before_after_comparison",
            "impact_analysis": {
                "utilization_impact": {
                    "metric": "Broad-spectrum days per 1000 patient days",
                    "before_adoption": 145.5,
                    "after_adoption": 98.2,
                    "change": -32.5,
                    "change_pct": -22.4,
                    "statistical_significance": "p < 0.001"
                },
                "clinical_outcomes": {
                    "length_of_stay_change": -0.5,
                    "readmission_rate_change": -2.1,
                    "adverse_event_change": "no significant change"
                },
                "resistance_impact": {
                    "target_organism": "S. pneumoniae",
                    "resistance_trend": "stable",
                    "interpretation": "Maintained susceptibility despite reduced usage"
                }
            },
            "hospitals_in_analysis": 38,
            "recommendation": "Protocol demonstrates significant utilization reduction without adverse outcomes. Recommend network-wide adoption."
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "analyze_stewardship_impact",
        "description": "Analyze the impact of a stewardship protocol on utilization, resistance, and clinical outcomes.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Protocol name to analyze"
                },
                "outcome_metric": {
                    "type": "string",
                    "description": "Outcome to measure: utilization, resistance, outcomes",
                    "default": "utilization"
                }
            },
            "required": ["protocol_name"]
        }
    }
}
```

---

### Tool: `generate_stewardship_network_diagram`

```python
def generate_stewardship_network_diagram(
    protocol_name: str = None,
    show_resistance: bool = False
) -> dict:
    """
    Generate a diagram showing stewardship collaboration network.
    
    Args:
        protocol_name: Optional - focus on specific protocol
        show_resistance: Whether to overlay resistance data
        
    Returns:
        {
            "diagram": "graph LR\\n    subgraph High Performers...",
            "diagram_type": "mermaid",
            "summary": {
                "hospitals_shown": 25,
                "collaborations": 18,
                "protocols_represented": 5
            }
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "generate_stewardship_network_diagram",
        "description": "Generate a diagram showing antimicrobial stewardship collaboration network and protocol adoption patterns.",
        "parameters": {
            "type": "object",
            "properties": {
                "protocol_name": {
                    "type": "string",
                    "description": "Focus on specific protocol"
                },
                "show_resistance": {
                    "type": "boolean",
                    "description": "Overlay resistance data on diagram",
                    "default": false
                }
            },
            "required": []
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
        "protocol_id": "asp_pneumonia_v2",
        "name": "Community-Acquired Pneumonia Stewardship Protocol",
        "category": "empiric_therapy",
        "target_condition": "Community-Acquired Pneumonia",
        "target_organisms": ["S. pneumoniae", "H. influenzae", "M. pneumoniae"],
        "key_recommendations": [
            "Ampicillin first-line for uncomplicated CAP",
            "48-hour IV to PO transition evaluation",
            "5-day course for uncomplicated cases"
        ],
        "evidence_source": "IDSA/PIDS Guidelines 2023"
    },
    {
        "protocol_id": "asp_uti_v1",
        "name": "Urinary Tract Infection Stewardship Protocol",
        "category": "empiric_therapy",
        "target_condition": "Urinary Tract Infection",
        "key_recommendations": [
            "Cephalexin first-line for uncomplicated cystitis",
            "Culture-directed therapy within 48 hours",
            "3-day course for uncomplicated cystitis"
        ]
    }
]
```

### Sample Resistance Patterns

```python
SAMPLE_RESISTANCE = [
    {
        "pattern_id": "res_mrsa_cmkc_2024",
        "organism": "Staphylococcus aureus",
        "antibiotic": "Oxacillin",
        "resistance_type": "resistant",
        "resistance_rate": 28.5,
        "isolate_count": 245,
        "measurement_period": "2024-Q4",
        "trend": "decreasing"
    }
]
```

---

## Configuration

### domains.yaml Entry

```yaml
antimicrobial_stewardship:
  enabled: true
  name: "Antimicrobial Stewardship Network"
  description: >
    Analyze antimicrobial stewardship program adoption and effectiveness.
    Correlates stewardship practices with resistance patterns and outcomes.
  version: "1.0.0"
  
  depends_on:
    - referral_network
    - quality_improvement
  
  module: "antimicrobial_stewardship"
  
  tools:
    - get_stewardship_adoption_status
    - analyze_resistance_patterns
    - find_stewardship_leaders
    - analyze_stewardship_impact
    - generate_stewardship_network_diagram
  
  schema:
    vertex_types:
      - antimicrobial_protocol
      - organism
      - resistance_pattern
      - antibiotic
    edge_types:
      - follows_protocol
      - observed_resistance
      - effective_against
      - shared_stewardship_with
```

---

## Data Sources

### PHIS Antimicrobial Dashboard

- Antibiotic utilization (DOT/1000 patient days)
- Broad vs narrow spectrum ratios
- Diagnosis-specific prescribing patterns

### Hospital Antibiograms

- Local resistance rates
- Organism-antibiotic susceptibility matrices
- Trend data over time

### CHA Collaborative Data

- Protocol adoption status
- Stewardship program participation
- Quality improvement metrics

---

## Implementation Notes

### Dependency on Quality Improvement Domain

This domain extends the `quality_improvement` domain's protocol tracking with antimicrobial-specific data:
- Inherits `adopted` edge pattern
- Adds resistance correlation analysis
- Specializes protocol schema for antimicrobial details

### Key Gremlin Patterns

```groovy
// Pattern 1: Protocol adoption with resistance correlation
g.V().has('antimicrobial_protocol', 'name', protocol_name)
    .in('follows_protocol').as('adopter')
    .out('observed_resistance')
    .has('organism', organism_name)
    .project('hospital', 'adherence', 'resistance')
    .by(select('adopter').values('name'))
    .by(select('adopter').inE('follows_protocol').values('adherence_rate'))
    .by('resistance_rate')

// Pattern 2: Stewardship leader identification
g.V().hasLabel('hospital')
    .project('name', 'protocols', 'avg_adherence', 'mentored')
    .by('name')
    .by(__.out('follows_protocol').count())
    .by(__.outE('follows_protocol').values('adherence_rate').mean())
    .by(__.out('shared_stewardship_with').count())
    .order().by(select('avg_adherence'), decr)

// Pattern 3: Resistance trend analysis
g.V().hasLabel('hospital')
    .out('observed_resistance')
    .has('organism', 'Staphylococcus aureus')
    .has('antibiotic', 'Oxacillin')
    .group()
    .by('measurement_period')
    .by('resistance_rate')
```

---

*Document Version: 1.0*  
*Last Updated: January 2026*
