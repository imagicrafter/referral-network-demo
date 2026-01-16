# Domain: Readmissions Network Analysis

## Overview

| Attribute | Value |
|-----------|-------|
| **Domain ID** | `readmissions` |
| **Priority** | MEDIUM |
| **Depends On** | `referral_network` |
| **Estimated Effort** | 2-3 weeks |
| **CHA Alignment** | Readmissions Benchmarking Tool, Value-Based Care Initiatives |

---

## Business Context

### Problem Statement

CHA recently launched a readmissions predictor tool that helps hospitals identify patients at risk of readmission. However, the tool focuses on patient-level factors. This domain extends the analysis to network-level patterns:

- Which post-discharge pathways have the best outcomes?
- Are readmissions clustered around specific transitions?
- Which hospital-provider partnerships reduce readmissions?
- Where are the care coordination gaps in the 30-day window?

### Why Graph Analytics?

Readmissions are often a network failure, not just a patient failure. Patients flow through a network of:
- Discharging hospitals
- Post-acute care providers (home health, SNF, rehab)
- Follow-up specialists
- Primary care providers

Graph analysis reveals which pathways succeed and which create risk.

### CHA Programs This Supports

- **Readmissions Benchmarking Tool** - Recently launched predictor
- **Value-Based Care Programs** - Financial incentives to reduce readmissions
- **Care Transitions Collaborative** - Best practices in discharge planning
- **PHIS Outcomes Tracking** - 30-day readmission rate reporting

---

## Power BI vs Agent Comparison

### Power BI Dashboard Shows (The "What")

| Visual | Metric | User Question Answered |
|--------|--------|------------------------|
| Readmission Rate KPI | Overall 30-day rate | "What's our readmission rate?" |
| Trend Chart | Rate over time | "Are we improving?" |
| Diagnosis Breakdown | Rate by APR-DRG | "Which diagnoses have highest rates?" |
| Peer Comparison | Benchmark vs peers | "How do we compare?" |

### Agent Answers (The "Why")

| User Question | Graph Capability Required | Power BI Limitation |
|---------------|---------------------------|---------------------|
| "Which post-discharge pathways have lowest readmission for asthma?" | Path analysis with outcome aggregation | Cannot model pathways |
| "Visualize where patients go after discharge and where they return from" | Flow network analysis | No flow visualization |
| "Which home health agencies have best outcomes for our cardiac patients?" | Partner performance comparison | Limited relationship modeling |
| "Identify care gaps in the 30-day post-discharge period" | Gap detection in care sequence | Static point-in-time data |

---

## Graph Schema

### Vertex Types

#### `diagnosis_group`

APR-DRG or diagnosis grouping.

```yaml
diagnosis_group:
  label: "diagnosis_group"
  description: "Diagnosis grouping for readmission analysis"
  properties:
    - name: code
      type: string
      required: true
      indexed: true
      description: "APR-DRG code"
      example: "APR-139"
      
    - name: name
      type: string
      required: true
      example: "Asthma"
      
    - name: category
      type: string
      required: true
      enum:
        - respiratory
        - cardiac
        - neurological
        - gastrointestinal
        - infection
        - surgical
        - mental_health
        - other
      example: "respiratory"
      
    - name: risk_tier
      type: string
      required: true
      enum:
        - low
        - moderate
        - high
        - very_high
      example: "moderate"
      
    - name: baseline_readmission_rate
      type: float
      required: false
      description: "National baseline 30-day readmission rate"
      example: 8.5
```

#### `post_acute_provider`

Post-discharge care provider.

```yaml
post_acute_provider:
  label: "post_acute_provider"
  description: "Provider of post-acute care services"
  properties:
    - name: provider_id
      type: string
      required: true
      indexed: true
      example: "hh_kc_001"
      
    - name: name
      type: string
      required: true
      example: "Kansas City Home Health"
      
    - name: type
      type: string
      required: true
      enum:
        - home_health
        - snf
        - rehab
        - outpatient_clinic
        - pcp
        - urgent_care
        - specialist
      example: "home_health"
      
    - name: specialty_focus
      type: string
      required: false
      description: "Primary specialty if applicable"
      example: "Pediatric Respiratory"
      
    - name: city
      type: string
      required: true
      example: "Kansas City"
      
    - name: state
      type: string
      required: true
      example: "MO"
      
    - name: quality_rating
      type: float
      required: false
      description: "CMS quality rating if applicable"
      example: 4.5
```

#### `discharge_pathway`

Common post-discharge care pattern.

```yaml
discharge_pathway:
  label: "discharge_pathway"
  description: "Standardized post-discharge care pathway"
  properties:
    - name: pathway_id
      type: string
      required: true
      indexed: true
      example: "pathway_asthma_standard"
      
    - name: name
      type: string
      required: true
      example: "Asthma Standard Discharge Pathway"
      
    - name: diagnosis_group
      type: string
      required: true
      example: "APR-139"
      
    - name: steps
      type: list
      required: true
      description: "Ordered list of care steps"
      example: ["PCP follow-up 48h", "Pulm specialist 7d", "Home health education"]
      
    - name: avg_readmission_rate
      type: float
      required: false
      description: "Average 30-day readmission rate for this pathway"
      example: 5.2
      
    - name: volume
      type: integer
      required: false
      description: "Number of patients on this pathway"
      example: 450
      
    - name: evidence_level
      type: string
      required: false
      enum:
        - high
        - moderate
        - low
        - local_best_practice
      example: "high"
```

### Edge Types

#### `discharged_to`

Patient discharged to post-acute provider.

```yaml
discharged_to:
  label: "discharged_to"
  from_vertex: hospital
  to_vertex: post_acute_provider
  description: "Hospital discharges patients to this provider"
  properties:
    - name: diagnosis_group
      type: string
      required: true
      description: "APR-DRG code for these patients"
      example: "APR-139"
      
    - name: volume
      type: integer
      required: true
      description: "Annual discharge volume"
      example: 125
      
    - name: readmission_rate
      type: float
      required: true
      description: "30-day readmission rate for this pairing"
      example: 4.8
      
    - name: avg_days_to_readmit
      type: float
      required: false
      description: "Average days until readmission when it occurs"
      example: 12.5
      
    - name: time_period
      type: string
      required: true
      description: "Measurement period"
      example: "FY2024"
```

#### `readmitted_from`

Readmission from post-acute setting.

```yaml
readmitted_from:
  label: "readmitted_from"
  from_vertex: hospital
  to_vertex: post_acute_provider
  description: "Hospital received readmission from this provider setting"
  properties:
    - name: volume
      type: integer
      required: true
      description: "Number of readmissions"
      example: 15
      
    - name: diagnosis_group
      type: string
      required: true
      example: "APR-139"
      
    - name: avg_days_post_discharge
      type: float
      required: true
      description: "Average days between discharge and readmission"
      example: 8.5
      
    - name: primary_reasons
      type: list
      required: false
      description: "Common reasons for readmission"
      example: ["Respiratory distress", "Medication non-adherence"]
      
    - name: time_period
      type: string
      required: true
      example: "FY2024"
```

#### `follows_pathway`

Hospital uses a discharge pathway.

```yaml
follows_pathway:
  label: "follows_pathway"
  from_vertex: hospital
  to_vertex: discharge_pathway
  description: "Hospital implements this discharge pathway"
  properties:
    - name: volume
      type: integer
      required: true
      description: "Patients on this pathway"
      example: 85
      
    - name: local_readmission_rate
      type: float
      required: true
      description: "This hospital's rate on this pathway"
      example: 4.2
      
    - name: adherence_rate
      type: float
      required: false
      description: "Percentage adherence to pathway steps"
      example: 92.5
      
    - name: customizations
      type: list
      required: false
      example: ["Added respiratory therapy call at day 3"]
```

#### `transitions_to`

Care transition between post-acute providers.

```yaml
transitions_to:
  label: "transitions_to"
  from_vertex: post_acute_provider
  to_vertex: post_acute_provider
  description: "Care transitions from one provider to another"
  properties:
    - name: volume
      type: integer
      required: true
      example: 45
      
    - name: avg_days_between
      type: float
      required: false
      description: "Average days between encounters"
      example: 3.5
      
    - name: diagnosis_group
      type: string
      required: false
      example: "APR-139"
```

---

## Agent Tools

### Tool: `analyze_discharge_pathways`

```python
def analyze_discharge_pathways(
    diagnosis_group: str,
    hospital_name: str = None
) -> dict:
    """
    Compare readmission rates across different discharge pathways.
    
    Use this tool when the user asks about:
    - Best discharge practices
    - Which pathways work
    - Comparing discharge approaches
    
    Args:
        diagnosis_group: APR-DRG code or name (e.g., "APR-139" or "Asthma")
        hospital_name: Optional - filter to specific hospital
        
    Returns:
        {
            "diagnosis": {
                "code": "APR-139",
                "name": "Asthma",
                "baseline_readmission_rate": 8.5
            },
            "pathways_compared": [
                {
                    "pathway_id": "pathway_asthma_enhanced",
                    "name": "Enhanced Asthma Discharge",
                    "steps": ["48h PCP", "7d Pulm", "Home health education", "14d check-in call"],
                    "performance": {
                        "hospitals_using": 12,
                        "total_volume": 580,
                        "avg_readmission_rate": 4.2,
                        "vs_baseline": -50.6,
                        "best_performer": {
                            "hospital": "Children's Mercy KC",
                            "rate": 2.8
                        }
                    },
                    "evidence_level": "high"
                },
                {
                    "pathway_id": "pathway_asthma_standard",
                    "name": "Standard Asthma Discharge",
                    "steps": ["7d PCP"],
                    "performance": {
                        "hospitals_using": 28,
                        "total_volume": 1250,
                        "avg_readmission_rate": 7.8,
                        "vs_baseline": -8.2
                    }
                }
            ],
            "recommendation": "Enhanced pathway shows 50% reduction vs baseline. Key differentiator is 48h PCP follow-up and home health education."
        }
    """
```

**Gremlin Query:**

```groovy
// Compare pathways for a diagnosis
g.V().has('discharge_pathway', 'diagnosis_group', diagnosis_code)
    .project('pathway', 'hospitals', 'avg_rate', 'volume')
    .by(valueMap('pathway_id', 'name', 'steps'))
    .by(__.in('follows_pathway').count())
    .by(__.in('follows_pathway').values('local_readmission_rate').mean())
    .by(__.in('follows_pathway').values('volume').sum())
    .order().by(select('avg_rate'))
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "analyze_discharge_pathways",
        "description": "Compare readmission rates across different discharge pathways for a diagnosis. Identifies best-performing pathways and key success factors.",
        "parameters": {
            "type": "object",
            "properties": {
                "diagnosis_group": {
                    "type": "string",
                    "description": "APR-DRG code or name (e.g., 'APR-139' or 'Asthma')"
                },
                "hospital_name": {
                    "type": "string",
                    "description": "Optional: filter to specific hospital"
                }
            },
            "required": ["diagnosis_group"]
        }
    }
}
```

---

### Tool: `find_successful_partnerships`

```python
def find_successful_partnerships(diagnosis_group: str) -> dict:
    """
    Identify hospital + post-acute provider partnerships with lowest readmission rates.
    
    Use this tool when the user asks about:
    - Best post-acute partners
    - Which providers reduce readmissions
    - Partnership performance
    
    Args:
        diagnosis_group: APR-DRG code or name
        
    Returns:
        {
            "diagnosis": "Asthma (APR-139)",
            "baseline_readmission_rate": 8.5,
            "top_partnerships": [
                {
                    "rank": 1,
                    "hospital": "Children's Mercy Kansas City",
                    "post_acute_provider": "Pediatric Home Care KC",
                    "provider_type": "home_health",
                    "partnership_metrics": {
                        "volume": 85,
                        "readmission_rate": 2.1,
                        "vs_baseline": -75.3,
                        "avg_days_to_readmit": 18.5
                    },
                    "success_factors": [
                        "Dedicated pediatric respiratory therapists",
                        "24/7 nurse hotline",
                        "Same-day escalation protocol"
                    ]
                },
                {
                    "rank": 2,
                    "hospital": "St. Louis Children's",
                    "post_acute_provider": "STL Pediatric Pulmonology Clinic",
                    "provider_type": "specialist",
                    ...
                }
            ],
            "underperforming_partnerships": [
                {
                    "hospital": "Regional Medical Center",
                    "post_acute_provider": "Generic Home Health",
                    "readmission_rate": 12.5,
                    "vs_baseline": +47.1,
                    "volume": 42,
                    "recommendation": "Consider partnership with Pediatric Home Care KC model"
                }
            ]
        }
    """
```

**Gremlin Query:**

```groovy
// Find best hospital-provider partnerships
g.V().hasLabel('hospital').as('h')
    .outE('discharged_to')
    .has('diagnosis_group', diagnosis_code)
    .has('volume', gte(20))  // Minimum volume for statistical significance
    .as('edge')
    .inV().as('provider')
    .select('h', 'edge', 'provider')
    .by('name')
    .by(valueMap('volume', 'readmission_rate'))
    .by(valueMap('name', 'type'))
    .order().by(select('edge').select('readmission_rate'))
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "find_successful_partnerships",
        "description": "Identify hospital and post-acute provider partnerships with the lowest readmission rates. Highlights success factors and underperforming relationships.",
        "parameters": {
            "type": "object",
            "properties": {
                "diagnosis_group": {
                    "type": "string",
                    "description": "APR-DRG code or name"
                }
            },
            "required": ["diagnosis_group"]
        }
    }
}
```

---

### Tool: `identify_readmission_risk_gaps`

```python
def identify_readmission_risk_gaps(hospital_name: str) -> dict:
    """
    Find diagnoses where hospital's readmission rate exceeds peers,
    and suggest pathway improvements.
    
    Use this tool when the user asks about:
    - Where we're underperforming
    - Improvement opportunities
    - Gap analysis for readmissions
    
    Args:
        hospital_name: Name of the hospital to analyze
        
    Returns:
        {
            "hospital": "Regional Medical Center",
            "analysis_period": "FY2024",
            "gap_analysis": [
                {
                    "diagnosis": "Asthma (APR-139)",
                    "hospital_rate": 11.5,
                    "peer_avg_rate": 6.8,
                    "best_peer_rate": 2.8,
                    "gap_vs_peer_avg": +69.1,
                    "volume": 125,
                    "current_pathway": "Standard discharge",
                    "current_post_acute": [
                        {"provider": "Generic Home Health", "rate": 14.2}
                    ],
                    "recommended_improvements": [
                        {
                            "action": "Adopt enhanced discharge pathway",
                            "expected_impact": "-40% to -50% reduction",
                            "implementation": "Add 48h PCP follow-up and home health education"
                        },
                        {
                            "action": "Partner with Pediatric Home Care KC",
                            "expected_impact": "-60% reduction based on peer performance",
                            "implementation": "Establish referral relationship"
                        }
                    ],
                    "priority_score": 92
                }
            ],
            "summary": {
                "diagnoses_above_peer_avg": 8,
                "total_excess_readmissions": 45,
                "estimated_annual_cost": "$675,000"
            }
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "identify_readmission_risk_gaps",
        "description": "Find diagnoses where a hospital's readmission rate exceeds peers. Provides specific pathway and partnership recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {
                    "type": "string",
                    "description": "Name of the hospital to analyze"
                }
            },
            "required": ["hospital_name"]
        }
    }
}
```

---

### Tool: `generate_readmission_flow_diagram`

```python
def generate_readmission_flow_diagram(
    hospital_name: str,
    diagnosis_group: str = None
) -> dict:
    """
    Visualize patient flow from discharge through readmission or success.
    
    Use this tool when the user asks to:
    - Visualize discharge flow
    - Show readmission patterns
    - Map post-discharge care
    
    Args:
        hospital_name: Hospital to analyze
        diagnosis_group: Optional - filter to specific diagnosis
        
    Returns:
        {
            "diagram": "graph LR\\n    Hospital[Children's Mercy]...",
            "diagram_type": "mermaid",
            "flow_summary": {
                "total_discharges": 450,
                "successful_transitions": 410,
                "readmissions": 40,
                "readmission_rate": 8.9
            },
            "legend": {
                "green_edge": "Successful pathway (low readmission)",
                "yellow_edge": "Moderate risk pathway",
                "red_edge": "High risk pathway",
                "edge_width": "Volume"
            }
        }
    
    Diagram shows:
        - Hospital at center
        - Post-acute providers as nodes
        - Edge thickness = volume
        - Edge color = readmission rate
        - Readmission arrows back to hospital
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "generate_readmission_flow_diagram",
        "description": "Generate a Mermaid diagram showing patient flow from hospital discharge through post-acute care. Highlights successful and high-risk pathways.",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {
                    "type": "string",
                    "description": "Hospital to analyze"
                },
                "diagnosis_group": {
                    "type": "string",
                    "description": "Optional: filter to specific diagnosis"
                }
            },
            "required": ["hospital_name"]
        }
    }
}
```

---

## Sample Data

### Sample Diagnosis Groups

```python
SAMPLE_DIAGNOSES = [
    {
        "code": "APR-139",
        "name": "Asthma",
        "category": "respiratory",
        "risk_tier": "moderate",
        "baseline_readmission_rate": 8.5
    },
    {
        "code": "APR-194",
        "name": "Heart Failure",
        "category": "cardiac",
        "risk_tier": "very_high",
        "baseline_readmission_rate": 18.2
    },
    {
        "code": "APR-137",
        "name": "Bronchiolitis",
        "category": "respiratory",
        "risk_tier": "low",
        "baseline_readmission_rate": 3.5
    }
]
```

### Sample Post-Acute Providers

```python
SAMPLE_POST_ACUTE = [
    {
        "provider_id": "hh_kc_001",
        "name": "Pediatric Home Care KC",
        "type": "home_health",
        "specialty_focus": "Pediatric Respiratory",
        "city": "Kansas City",
        "state": "MO",
        "quality_rating": 4.8
    },
    {
        "provider_id": "clinic_pulm_stl",
        "name": "STL Pediatric Pulmonology Clinic",
        "type": "specialist",
        "specialty_focus": "Pulmonology",
        "city": "St. Louis",
        "state": "MO",
        "quality_rating": 4.5
    }
]
```

---

## Configuration

### domains.yaml Entry

```yaml
readmissions:
  enabled: true
  name: "Readmissions Network Analysis"
  description: >
    Analyze post-discharge pathways and their impact on 30-day readmission
    rates. Identifies successful partnerships and improvement opportunities.
  version: "1.0.0"
  
  depends_on:
    - referral_network
  
  module: "readmissions"
  
  tools:
    - analyze_discharge_pathways
    - find_successful_partnerships
    - identify_readmission_risk_gaps
    - generate_readmission_flow_diagram
  
  schema:
    vertex_types:
      - diagnosis_group
      - post_acute_provider
      - discharge_pathway
    edge_types:
      - discharged_to
      - readmitted_from
      - follows_pathway
      - transitions_to
```

---

## Data Sources

### PHIS Data

- Inpatient encounters with APR-DRG
- 30-day readmission flags
- Discharge disposition codes

### Hospital Data

- Post-acute referral patterns
- Discharge pathway protocols
- Partnership agreements

### External Data

- CMS Home Health Compare ratings
- Post-acute provider directories

---

## Implementation Notes

### Key Gremlin Patterns

```groovy
// Pattern 1: Readmission flow analysis
g.V().has('hospital', 'name', hospital_name)
    .outE('discharged_to')
    .project('provider', 'volume', 'readmit_rate', 'readmit_volume')
    .by(inV().values('name'))
    .by('volume')
    .by('readmission_rate')
    .by(
        __.inV()
            .inE('readmitted_from')
            .where(outV().has('name', hospital_name))
            .values('volume')
            .sum()
    )

// Pattern 2: Pathway comparison
g.V().has('discharge_pathway', 'diagnosis_group', 'APR-139')
    .order().by(
        __.in('follows_pathway')
            .values('local_readmission_rate')
            .mean()
    )

// Pattern 3: Partnership performance ranking
g.V().has('hospital', 'name', hospital_name)
    .outE('discharged_to')
    .has('volume', gte(20))
    .order().by('readmission_rate')
    .project('provider', 'volume', 'rate')
    .by(inV().values('name'))
    .by('volume')
    .by('readmission_rate')
```

### Integration with CHA Tools

This domain complements CHA's existing Readmissions Benchmarking Tool by adding network-level analysis. The benchmarking tool identifies at-risk patients; this domain identifies at-risk pathways.

---

*Document Version: 1.0*  
*Last Updated: January 2026*
