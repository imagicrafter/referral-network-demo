# Domain: Workforce Analytics

## Overview

| Attribute | Value |
|-----------|-------|
| **Domain ID** | `workforce` |
| **Priority** | LOW (complex data requirements) |
| **Depends On** | `referral_network` |
| **Estimated Effort** | 4-5 weeks |
| **CHA Alignment** | PROSPECT Data Program, HR Metrics Dashboard |

---

## Business Context

### Problem Statement

CHA tracks workforce metrics extensively through the PROSPECT program. However, traditional HR analytics shows snapshots; it cannot answer:

- Where does talent flow between children's hospitals?
- What career pathways lead to retention vs. turnover?
- Which training programs produce leaders?
- Are there regional talent imbalances?

Graph analysis reveals movement patterns, training pathways, and retention factors across the network.

### Why Graph Analytics?

Workforce dynamics are inherently relational:
- Staff move between hospitals
- Training creates competency pipelines
- Mentorship relationships influence retention
- Regional networks compete for talent

### CHA Programs This Supports

- **PROSPECT** - Pediatric Research in Office Settings to Pediatric Excellence in Care and Training
- **HR Metrics Dashboard** - Tableau-powered workforce analytics
- **Workforce Development Initiatives** - Training and retention programs
- **Nursing Excellence Programs** - Specialty certification pathways

---

## Power BI vs Agent Comparison

### Power BI Dashboard Shows (The "What")

| Visual | Metric | User Question Answered |
|--------|--------|------------------------|
| Turnover Rate | Annual turnover by role | "What's our nursing turnover?" |
| Headcount | FTEs by department | "How many staff do we have?" |
| Vacancy Rate | Open positions | "What positions are unfilled?" |
| Tenure Distribution | Staff by years of service | "What's our experience mix?" |

### Agent Answers (The "Why")

| User Question | Graph Capability Required | Power BI Limitation |
|---------------|---------------------------|---------------------|
| "Where do nurses go when they leave our hospital?" | Career movement traversal | Cannot track cross-org movement |
| "What career path leads to nursing leadership?" | Path pattern analysis | No sequence analysis |
| "Which hospitals are net importers vs exporters of talent?" | Network flow analysis | No flow modeling |
| "What training predicts 5-year retention?" | Multi-variable path correlation | Limited predictive capability |

---

## Graph Schema

### Vertex Types

#### `role`

Job position or title.

```yaml
role:
  label: "role"
  description: "Job position or role type"
  properties:
    - name: role_id
      type: string
      required: true
      indexed: true
      example: "rn_bedside_picu"
      
    - name: title
      type: string
      required: true
      example: "PICU Registered Nurse"
      
    - name: category
      type: string
      required: true
      enum:
        - nursing
        - physician
        - allied_health
        - administrative
        - support
        - leadership
      example: "nursing"
      
    - name: specialty
      type: string
      required: false
      example: "Pediatric Intensive Care"
      
    - name: level
      type: string
      required: true
      enum:
        - entry
        - experienced
        - senior
        - lead
        - manager
        - director
        - executive
      example: "experienced"
      
    - name: requires_certification
      type: list
      required: false
      example: ["RN License", "PALS", "CCRN"]
      
    - name: avg_salary_range
      type: string
      required: false
      example: "$65,000-$85,000"
```

#### `training_program`

Education or certification program.

```yaml
training_program:
  label: "training_program"
  description: "Professional development or certification program"
  properties:
    - name: program_id
      type: string
      required: true
      indexed: true
      example: "cert_ccrn"
      
    - name: name
      type: string
      required: true
      example: "Critical Care Registered Nurse Certification"
      
    - name: type
      type: string
      required: true
      enum:
        - certification
        - degree
        - residency
        - fellowship
        - continuing_ed
        - leadership_development
      example: "certification"
      
    - name: provider
      type: string
      required: false
      example: "AACN"
      
    - name: duration_months
      type: integer
      required: false
      example: 6
      
    - name: target_roles
      type: list
      required: false
      example: ["PICU RN", "NICU RN", "Cardiac ICU RN"]
```

#### `certification`

Professional certification.

```yaml
certification:
  label: "certification"
  description: "Professional certification or license"
  properties:
    - name: cert_id
      type: string
      required: true
      indexed: true
      example: "cert_ccrn"
      
    - name: name
      type: string
      required: true
      example: "CCRN - Critical Care Registered Nurse"
      
    - name: issuing_body
      type: string
      required: true
      example: "AACN"
      
    - name: renewal_years
      type: integer
      required: false
      example: 3
      
    - name: is_required
      type: boolean
      required: false
      description: "Whether certification is required for certain roles"
      default: false
```

#### `staff_cohort`

Anonymized group of staff members (no PII).

```yaml
staff_cohort:
  label: "staff_cohort"
  description: "Anonymized cohort of staff for aggregate analysis"
  privacy_note: "Contains NO individual identifiers - aggregated data only"
  properties:
    - name: cohort_id
      type: string
      required: true
      indexed: true
      example: "cohort_rn_picu_hired_2022"
      
    - name: role_category
      type: string
      required: true
      example: "nursing"
      
    - name: specialty
      type: string
      required: false
      example: "PICU"
      
    - name: hire_year
      type: integer
      required: true
      example: 2022
      
    - name: cohort_size
      type: integer
      required: true
      example: 45
      
    - name: avg_tenure_years
      type: float
      required: false
      example: 2.5
      
    - name: retention_rate_1yr
      type: float
      required: false
      example: 85.0
      
    - name: retention_rate_3yr
      type: float
      required: false
      example: 65.0
```

### Edge Types

#### `holds_role`

Staff cohort holds roles at a hospital.

```yaml
holds_role:
  label: "holds_role"
  from_vertex: staff_cohort
  to_vertex: hospital
  description: "Staff cohort is employed at hospital in specific role"
  properties:
    - name: role_id
      type: string
      required: true
      example: "rn_bedside_picu"
      
    - name: count
      type: integer
      required: true
      description: "Number of staff in this role"
      example: 28
      
    - name: start_period
      type: string
      required: true
      example: "2022-Q1"
      
    - name: status
      type: string
      required: true
      enum:
        - active
        - departed
        - transferred
      example: "active"
```

#### `moved_to`

Career movement between hospitals.

```yaml
moved_to:
  label: "moved_to"
  from_vertex: hospital
  to_vertex: hospital
  description: "Staff movement from one hospital to another"
  properties:
    - name: role_category
      type: string
      required: true
      example: "nursing"
      
    - name: volume
      type: integer
      required: true
      description: "Number of staff who made this move"
      example: 12
      
    - name: time_period
      type: string
      required: true
      example: "FY2024"
      
    - name: avg_tenure_at_source
      type: float
      required: false
      description: "Average years at source hospital before moving"
      example: 3.5
      
    - name: movement_reason
      type: string
      required: false
      enum:
        - career_advancement
        - relocation
        - compensation
        - work_environment
        - family
        - unknown
      example: "career_advancement"
```

#### `completed`

Staff completed training program.

```yaml
completed:
  label: "completed"
  from_vertex: staff_cohort
  to_vertex: training_program
  description: "Staff cohort completed this training"
  properties:
    - name: completion_count
      type: integer
      required: true
      example: 35
      
    - name: completion_period
      type: string
      required: true
      example: "2023"
      
    - name: pass_rate
      type: float
      required: false
      example: 92.5
      
    - name: subsequent_retention_rate
      type: float
      required: false
      description: "Retention rate after completing program"
      example: 88.0
```

#### `requires`

Role requires certification.

```yaml
requires:
  label: "requires"
  from_vertex: role
  to_vertex: certification
  description: "Role requires this certification"
  properties:
    - name: requirement_type
      type: string
      required: true
      enum:
        - mandatory
        - preferred
        - advancement
      example: "mandatory"
      
    - name: grace_period_months
      type: integer
      required: false
      example: 12
```

#### `leads_to`

Career progression path.

```yaml
leads_to:
  label: "leads_to"
  from_vertex: role
  to_vertex: role
  description: "Common career progression from one role to another"
  properties:
    - name: avg_transition_years
      type: float
      required: true
      example: 3.5
      
    - name: transition_count
      type: integer
      required: true
      description: "Number of staff who made this progression"
      example: 45
      
    - name: success_rate
      type: float
      required: false
      description: "Percentage who successfully transition"
      example: 78.5
```

---

## Agent Tools

### Tool: `analyze_talent_flow`

```python
def analyze_talent_flow(
    role_category: str = None,
    time_period: str = None
) -> dict:
    """
    Analyze net talent flow between hospitals - who's importing vs exporting talent.
    
    Use this tool when the user asks about:
    - Where talent is going
    - Which hospitals gain/lose staff
    - Regional talent competition
    
    Args:
        role_category: Optional filter (nursing, physician, etc.)
        time_period: Optional period (e.g., "FY2024")
        
    Returns:
        {
            "analysis_period": "FY2024",
            "role_category": "nursing",
            "net_flow_analysis": [
                {
                    "hospital": "Children's Mercy Kansas City",
                    "inbound": 45,
                    "outbound": 22,
                    "net_flow": +23,
                    "status": "net_importer",
                    "top_sources": [
                        {"hospital": "Regional Medical Center", "volume": 12},
                        {"hospital": "KU Medical Center", "volume": 8}
                    ],
                    "top_destinations": [
                        {"hospital": "Texas Children's", "volume": 8}
                    ]
                },
                {
                    "hospital": "Regional Medical Center",
                    "inbound": 15,
                    "outbound": 35,
                    "net_flow": -20,
                    "status": "net_exporter",
                    ...
                }
            ],
            "regional_summary": {
                "total_movements": 450,
                "stayed_in_region": 280,
                "left_region": 170,
                "regional_retention": 62.2
            },
            "movement_drivers": {
                "career_advancement": 35,
                "compensation": 28,
                "relocation": 22,
                "work_environment": 15
            }
        }
    """
```

**Gremlin Query:**

```groovy
// Calculate net talent flow
g.V().hasLabel('hospital').as('h')
    .project('hospital', 'inbound', 'outbound')
    .by('name')
    .by(__.inE('moved_to').has('role_category', role_cat).values('volume').sum())
    .by(__.outE('moved_to').has('role_category', role_cat).values('volume').sum())
    .order().by(
        math('inbound - outbound')
    , decr)
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "analyze_talent_flow",
        "description": "Analyze talent flow between hospitals. Identifies net importers/exporters and movement patterns.",
        "parameters": {
            "type": "object",
            "properties": {
                "role_category": {
                    "type": "string",
                    "description": "Filter by role category (nursing, physician, allied_health, etc.)"
                },
                "time_period": {
                    "type": "string",
                    "description": "Time period to analyze (e.g., 'FY2024')"
                }
            },
            "required": []
        }
    }
}
```

---

### Tool: `find_career_pathways`

```python
def find_career_pathways(
    starting_role: str = None,
    target_role: str = None,
    role_category: str = None
) -> dict:
    """
    Identify common career progression patterns.
    
    Use this tool when the user asks about:
    - Career paths
    - How to advance
    - Progression patterns
    
    Args:
        starting_role: Optional - starting role ID or title
        target_role: Optional - target role to reach
        role_category: Optional - filter by category
        
    Returns:
        {
            "pathways": [
                {
                    "pathway_id": "rn_to_nurse_manager",
                    "name": "Bedside RN to Nurse Manager",
                    "steps": [
                        {
                            "role": "Bedside RN",
                            "avg_duration_years": 3.0,
                            "key_requirements": ["RN License", "BSN"]
                        },
                        {
                            "role": "Charge Nurse",
                            "avg_duration_years": 2.0,
                            "key_requirements": ["Leadership course"]
                        },
                        {
                            "role": "Nurse Manager",
                            "avg_duration_years": null,
                            "key_requirements": ["MSN preferred", "Management certification"]
                        }
                    ],
                    "total_avg_years": 5.0,
                    "success_rate": 45.0,
                    "staff_on_pathway": 125,
                    "completion_count": 28
                }
            ],
            "fastest_progression": {
                "pathway": "rn_to_nurse_manager",
                "fastest_time_years": 3.5,
                "hospital": "Children's Mercy KC",
                "success_factors": ["Leadership development program", "Mentorship"]
            }
        }
    """
```

**Gremlin Query:**

```groovy
// Find career pathways
g.V().has('role', 'role_id', starting_role)
    .repeat(__.out('leads_to').simplePath())
    .until(
        __.has('role_id', target_role)
        .or()
        .out('leads_to').count().is(0)
        .or()
        .loops().is(5)
    )
    .path()
    .by(valueMap('title', 'level'))
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "find_career_pathways",
        "description": "Identify common career progression patterns. Shows typical paths from one role to another with timing and requirements.",
        "parameters": {
            "type": "object",
            "properties": {
                "starting_role": {
                    "type": "string",
                    "description": "Starting role ID or title"
                },
                "target_role": {
                    "type": "string",
                    "description": "Target role to reach"
                },
                "role_category": {
                    "type": "string",
                    "description": "Filter by category (nursing, physician, etc.)"
                }
            },
            "required": []
        }
    }
}
```

---

### Tool: `identify_retention_factors`

```python
def identify_retention_factors(
    role_category: str,
    hospital_name: str = None
) -> dict:
    """
    Analyze what predicts staff retention.
    
    Use this tool when the user asks about:
    - What keeps staff
    - Retention drivers
    - Why people stay
    
    Args:
        role_category: Role category to analyze
        hospital_name: Optional - specific hospital
        
    Returns:
        {
            "role_category": "nursing",
            "analysis_period": "2020-2024",
            "retention_factors": [
                {
                    "factor": "Completed specialty certification",
                    "retention_impact": "+25%",
                    "correlation": 0.72,
                    "cohorts_analyzed": 450,
                    "detail": "Staff with CCRN certification show 25% higher 3-year retention"
                },
                {
                    "factor": "Leadership development program",
                    "retention_impact": "+18%",
                    "correlation": 0.65,
                    ...
                },
                {
                    "factor": "Internal transfer opportunity",
                    "retention_impact": "+22%",
                    ...
                }
            ],
            "risk_factors": [
                {
                    "factor": "No promotion within 3 years",
                    "turnover_impact": "+45%",
                    "affected_cohort_size": 280
                }
            ],
            "recommendations": [
                "Invest in specialty certification support",
                "Create visible internal mobility paths",
                "Implement structured promotion timelines"
            ]
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "identify_retention_factors",
        "description": "Analyze what factors predict staff retention. Identifies training, career paths, and other factors correlated with retention.",
        "parameters": {
            "type": "object",
            "properties": {
                "role_category": {
                    "type": "string",
                    "description": "Role category to analyze (nursing, physician, etc.)"
                },
                "hospital_name": {
                    "type": "string",
                    "description": "Optional: specific hospital to analyze"
                }
            },
            "required": ["role_category"]
        }
    }
}
```

---

### Tool: `generate_workforce_flow_diagram`

```python
def generate_workforce_flow_diagram(
    role_category: str,
    region: str = None
) -> dict:
    """
    Visualize staff movement patterns between hospitals.
    
    Use this tool when the user asks to:
    - Show talent flow
    - Visualize movement
    - Map workforce patterns
    
    Args:
        role_category: Role category to visualize
        region: Optional - filter to region
        
    Returns:
        {
            "diagram": "graph LR\\n    subgraph Net Importers...",
            "diagram_type": "mermaid",
            "summary": {
                "hospitals_shown": 15,
                "total_movements": 280,
                "net_importers": 6,
                "net_exporters": 9
            },
            "legend": {
                "green_node": "Net importer (gaining talent)",
                "red_node": "Net exporter (losing talent)",
                "edge_width": "Movement volume"
            }
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "generate_workforce_flow_diagram",
        "description": "Generate a Mermaid diagram showing talent flow between hospitals. Highlights net importers/exporters.",
        "parameters": {
            "type": "object",
            "properties": {
                "role_category": {
                    "type": "string",
                    "description": "Role category to visualize"
                },
                "region": {
                    "type": "string",
                    "description": "Optional: filter to specific region"
                }
            },
            "required": ["role_category"]
        }
    }
}
```

---

## Sample Data

### Sample Roles

```python
SAMPLE_ROLES = [
    {
        "role_id": "rn_bedside_picu",
        "title": "PICU Registered Nurse",
        "category": "nursing",
        "specialty": "Pediatric Intensive Care",
        "level": "experienced",
        "requires_certification": ["RN License", "PALS", "BLS"],
        "avg_salary_range": "$65,000-$85,000"
    },
    {
        "role_id": "rn_charge_picu",
        "title": "PICU Charge Nurse",
        "category": "nursing",
        "specialty": "Pediatric Intensive Care",
        "level": "lead",
        "requires_certification": ["RN License", "CCRN", "Leadership cert"],
        "avg_salary_range": "$75,000-$95,000"
    },
    {
        "role_id": "mgr_nursing_picu",
        "title": "PICU Nurse Manager",
        "category": "nursing",
        "specialty": "Pediatric Intensive Care",
        "level": "manager",
        "requires_certification": ["RN License", "MSN preferred"],
        "avg_salary_range": "$95,000-$120,000"
    }
]
```

---

## Configuration

### domains.yaml Entry

```yaml
workforce:
  enabled: true
  name: "Workforce Analytics"
  description: >
    Analyze staff movement, career pathways, and retention factors across
    the children's hospital network. Identifies talent flow patterns and
    training effectiveness.
  version: "1.0.0"
  
  depends_on:
    - referral_network
  
  module: "workforce"
  
  tools:
    - analyze_talent_flow
    - find_career_pathways
    - identify_retention_factors
    - generate_workforce_flow_diagram
  
  schema:
    vertex_types:
      - role
      - training_program
      - certification
      - staff_cohort
    edge_types:
      - holds_role
      - moved_to
      - completed
      - requires
      - leads_to
```

---

## Data Privacy

### Aggregated Data Only

This domain uses cohort-level data, never individual employee records:
- Minimum cohort size of 20 for any analysis
- No names, employee IDs, or other PII
- Movement data is aggregated counts, not individual tracking
- Salary data is ranges, not individual values

### PROSPECT Data Usage

Data sourced from PROSPECT should follow CHA data sharing agreements:
- Aggregate metrics only
- No competitive salary benchmarking at individual level
- Movement data anonymized to regional level

---

## Implementation Notes

### Complex Data Requirements

This domain has higher data requirements than others:
- Requires longitudinal employment data
- Needs cross-hospital movement tracking
- Training completion records must be linked

Consider starting with a smaller pilot:
- Single role category (nursing)
- Regional subset of hospitals
- Recent time period (2-3 years)

### Key Gremlin Patterns

```groovy
// Pattern 1: Net flow calculation
g.V().hasLabel('hospital')
    .project('name', 'in', 'out')
    .by('name')
    .by(__.inE('moved_to').values('volume').sum())
    .by(__.outE('moved_to').values('volume').sum())

// Pattern 2: Career path traversal
g.V().has('role', 'level', 'entry')
    .repeat(__.out('leads_to'))
    .until(__.has('level', 'manager'))
    .path()

// Pattern 3: Training impact on retention
g.V().hasLabel('staff_cohort')
    .where(__.out('completed').hasLabel('training_program'))
    .values('retention_rate_3yr')
    .mean()
```

---

*Document Version: 1.0*  
*Last Updated: January 2026*
