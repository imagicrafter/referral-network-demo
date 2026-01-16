# Domain: Children with Medical Complexity (CMC) Care Coordination

## Overview

| Attribute | Value |
|-----------|-------|
| **Domain ID** | `cmc_coordination` |
| **Priority** | MEDIUM |
| **Depends On** | `referral_network` |
| **Estimated Effort** | 3-4 weeks |
| **CHA Alignment** | CARE Award initiatives, Medical Complexity Research Groups |

---

## Business Context

### Problem Statement

Over 9,000 children with medical complexity (CMC) require care coordination across multiple facilities. These children often see 10+ specialists across 3+ hospitals, creating fragmented care that leads to:

- Duplicated tests and procedures
- Conflicting treatment plans
- Care gaps during transitions
- Family burden and burnout
- Higher costs and worse outcomes

Graph analysis can reveal care fragmentation patterns and coordination opportunities that traditional systems miss.

### Why Graph Analytics?

CMC care is inherently a network problem:
- Multiple hospitals serving the same patient cohorts
- Complex specialist-to-specialist referral patterns
- Care plan dependencies across facilities
- Informal coordination relationships

Traditional EHR reports show encounters; graphs show relationships and gaps.

### CHA Programs This Supports

- **CARE Award** - Coordinating All Resources Effectively for medical complexity
- **Medical Complexity Research Network** - CHA research group focused on CMC
- **Accountable Care Organizations** - Value-based care for complex populations
- **Family Partnership Programs** - Family-centered care coordination

---

## Power BI vs Agent Comparison

### Power BI Dashboard Shows (The "What")

| Visual | Metric | User Question Answered |
|--------|--------|------------------------|
| Patient Volume | CMC patients by complexity tier | "How many complex patients do we serve?" |
| Provider Count | Average providers per patient | "How fragmented is care?" |
| Encounter Frequency | Visits per patient per year | "How often do CMC patients seek care?" |
| Cost Metrics | Cost per patient trends | "What's the cost trajectory?" |

### Agent Answers (The "Why")

| User Question | Graph Capability Required | Power BI Limitation |
|---------------|---------------------------|---------------------|
| "Show the care network for complex cardiac patients in our region" | Multi-hospital patient cohort traversal | Cannot model cross-facility care |
| "Which specialists are most frequently co-involved in CMC care?" | Provider co-occurrence analysis | No relationship modeling |
| "Visualize care fragmentation for patients seeing 5+ providers" | Network density analysis | Cannot compute fragmentation |
| "Identify hospitals with strong coordination that could mentor others" | Pattern matching on coordination edges | No qualitative relationship data |

---

## Graph Schema

### Vertex Types

#### `patient_cohort`

Anonymized group of similar patients (no PHI).

```yaml
patient_cohort:
  label: "patient_cohort"
  description: "Anonymized group of patients with similar characteristics"
  privacy_note: "Contains NO individual patient identifiers - aggregated data only"
  properties:
    - name: cohort_id
      type: string
      required: true
      indexed: true
      example: "cohort_cardiac_tier3_mo"
      
    - name: primary_diagnosis_category
      type: string
      required: true
      description: "Primary diagnosis grouping"
      enum:
        - cardiac
        - neurological
        - respiratory
        - gastrointestinal
        - oncology
        - genetic_metabolic
        - multiple_congenital
        - technology_dependent
      example: "cardiac"
      
    - name: complexity_tier
      type: string
      required: true
      enum:
        - tier1  # Single complex condition
        - tier2  # Multiple conditions, stable
        - tier3  # Multiple conditions, frequent crises
        - tier4  # Technology-dependent, highest complexity
      example: "tier3"
      
    - name: patient_count
      type: integer
      required: true
      description: "Number of patients in this cohort"
      example: 45
      
    - name: avg_age_years
      type: float
      required: false
      example: 8.5
      
    - name: avg_providers_per_patient
      type: float
      required: false
      description: "Average number of providers seen per patient"
      example: 12.3
      
    - name: avg_hospitals_per_patient
      type: float
      required: false
      description: "Average number of hospitals used per patient"
      example: 3.2
      
    - name: geographic_region
      type: string
      required: false
      example: "Greater Kansas City"
```

#### `care_plan`

Coordinated care plan template.

```yaml
care_plan:
  label: "care_plan"
  description: "Standardized care plan template for a condition"
  properties:
    - name: plan_id
      type: string
      required: true
      indexed: true
      example: "plan_cardiac_tier3_v2"
      
    - name: name
      type: string
      required: true
      example: "Complex Cardiac Care Pathway"
      
    - name: diagnosis_category
      type: string
      required: true
      example: "cardiac"
      
    - name: complexity_tier
      type: string
      required: true
      example: "tier3"
      
    - name: required_specialties
      type: list
      required: true
      description: "Specialties that must be involved"
      example: ["Cardiology", "Cardiac Surgery", "Pulmonology", "Nutrition"]
      
    - name: coordination_frequency
      type: string
      required: true
      enum:
        - weekly
        - biweekly
        - monthly
        - quarterly
      example: "monthly"
      
    - name: key_transitions
      type: list
      required: false
      description: "Critical transition points requiring coordination"
      example: ["Post-surgical", "ED to inpatient", "Hospital to home"]
      
    - name: version
      type: string
      required: false
      example: "2.0"
```

#### `specialist_group`

Group of specialists with a common focus.

```yaml
specialist_group:
  label: "specialist_group"
  description: "Group of specialists who commonly coordinate on CMC care"
  properties:
    - name: group_id
      type: string
      required: true
      indexed: true
      example: "cardiac_team_cmkc"
      
    - name: specialty_focus
      type: string
      required: true
      example: "Complex Cardiac"
      
    - name: primary_hospital
      type: string
      required: true
      example: "Children's Mercy Kansas City"
      
    - name: provider_count
      type: integer
      required: true
      example: 8
      
    - name: accepts_external_referrals
      type: boolean
      required: true
      default: true
```

### Edge Types

#### `receives_care_at`

Patient cohort receives care at a hospital.

```yaml
receives_care_at:
  label: "receives_care_at"
  from_vertex: patient_cohort
  to_vertex: hospital
  description: "Cohort receives care at this hospital"
  properties:
    - name: visit_frequency
      type: string
      required: true
      enum:
        - weekly
        - monthly
        - quarterly
        - annual
        - as_needed
      example: "monthly"
      
    - name: care_type
      type: string
      required: true
      enum:
        - primary
        - specialty
        - emergency
        - inpatient
        - surgical
      example: "specialty"
      
    - name: annual_encounters
      type: integer
      required: false
      description: "Total encounters per year for this cohort"
      example: 540
      
    - name: is_primary_facility
      type: boolean
      required: true
      description: "Whether this is the primary coordinating facility"
      default: false
```

#### `coordinated_with`

Care coordination relationship between hospitals.

```yaml
coordinated_with:
  label: "coordinated_with"
  from_vertex: hospital
  to_vertex: hospital
  description: "Formal care coordination relationship for CMC patients"
  properties:
    - name: cohort_id
      type: string
      required: false
      description: "Specific cohort this coordination applies to"
      example: "cohort_cardiac_tier3_mo"
      
    - name: coordination_type
      type: string
      required: true
      enum:
        - shared_ehr
        - care_conference
        - co_management
        - transfer_protocol
        - telemedicine
      example: "care_conference"
      
    - name: frequency
      type: string
      required: true
      enum:
        - weekly
        - biweekly
        - monthly
        - quarterly
        - as_needed
      example: "monthly"
      
    - name: start_date
      type: date
      required: false
      example: "2024-01-15"
      
    - name: effectiveness_rating
      type: integer
      required: false
      description: "1-5 rating of coordination effectiveness"
      min: 1
      max: 5
```

#### `follows_plan`

Hospital follows a care plan for a cohort.

```yaml
follows_plan:
  label: "follows_plan"
  from_vertex: hospital
  to_vertex: care_plan
  description: "Hospital implements this care plan"
  properties:
    - name: adherence_rate
      type: float
      required: false
      description: "Percentage adherence to plan elements"
      example: 85.5
      
    - name: customizations
      type: list
      required: false
      description: "Local adaptations to the standard plan"
      example: ["Added nutrition consult", "Modified follow-up schedule"]
      
    - name: implementation_date
      type: date
      required: false
      example: "2024-03-01"
```

#### `specialist_at`

Specialist group is based at a hospital.

```yaml
specialist_at:
  label: "specialist_at"
  from_vertex: specialist_group
  to_vertex: hospital
  description: "Specialist group is based at this hospital"
  properties:
    - name: is_primary_location
      type: boolean
      required: true
      default: true
      
    - name: clinic_days
      type: string
      required: false
      example: "Monday, Wednesday, Friday"
```

---

## Agent Tools

### Tool: `analyze_care_fragmentation`

```python
def analyze_care_fragmentation(
    complexity_tier: str = None,
    diagnosis_category: str = None,
    region: str = None
) -> dict:
    """
    Identify patient cohorts with fragmented care across many providers.
    
    Use this tool when the user asks about:
    - Care fragmentation patterns
    - Patients seeing too many providers
    - Coordination gaps
    
    Args:
        complexity_tier: Optional filter by tier (tier1-tier4)
        diagnosis_category: Optional filter by diagnosis
        region: Optional filter by geographic region
        
    Returns:
        {
            "analysis_summary": {
                "cohorts_analyzed": 45,
                "total_patients": 1250,
                "avg_providers_per_patient": 8.5,
                "avg_hospitals_per_patient": 2.8
            },
            "high_fragmentation_cohorts": [
                {
                    "cohort_id": "cohort_cardiac_tier4_kc",
                    "diagnosis_category": "cardiac",
                    "complexity_tier": "tier4",
                    "patient_count": 28,
                    "fragmentation_metrics": {
                        "avg_providers": 15.2,
                        "avg_hospitals": 4.1,
                        "unique_specialties": 12,
                        "coordination_score": 35
                    },
                    "hospitals_involved": [
                        {"name": "Children's Mercy KC", "care_type": "primary", "encounters": 180},
                        {"name": "KU Medical Center", "care_type": "specialty", "encounters": 45},
                        {"name": "St. Luke's", "care_type": "emergency", "encounters": 22}
                    ],
                    "missing_coordination": [
                        "No shared EHR between CMKC and KU",
                        "No regular care conferences"
                    ],
                    "recommendation": "Establish monthly care conferences between primary facilities"
                }
            ],
            "fragmentation_by_tier": {
                "tier1": {"avg_providers": 4.2, "avg_hospitals": 1.5},
                "tier2": {"avg_providers": 7.8, "avg_hospitals": 2.1},
                "tier3": {"avg_providers": 11.5, "avg_hospitals": 3.2},
                "tier4": {"avg_providers": 14.8, "avg_hospitals": 4.0}
            }
        }
    """
```

**Gremlin Query:**

```groovy
// Find cohorts with high fragmentation
g.V().hasLabel('patient_cohort')
    .has('avg_providers_per_patient', gte(10))
    .project('cohort', 'hospitals', 'coordination')
    .by(valueMap())
    .by(
        __.out('receives_care_at')
            .project('hospital', 'care_type', 'encounters')
            .by('name')
            .by(__.inE('receives_care_at').values('care_type'))
            .by(__.inE('receives_care_at').values('annual_encounters'))
            .fold()
    )
    .by(
        __.out('receives_care_at')
            .outE('coordinated_with')
            .count()
    )
    .order().by(select('cohort').select('avg_providers_per_patient'), decr)
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "analyze_care_fragmentation",
        "description": "Identify patient cohorts with fragmented care across many providers. Returns fragmentation metrics, involved hospitals, and coordination gaps.",
        "parameters": {
            "type": "object",
            "properties": {
                "complexity_tier": {
                    "type": "string",
                    "description": "Filter by complexity tier (tier1, tier2, tier3, tier4)",
                    "enum": ["tier1", "tier2", "tier3", "tier4"]
                },
                "diagnosis_category": {
                    "type": "string",
                    "description": "Filter by diagnosis category (cardiac, neurological, etc.)"
                },
                "region": {
                    "type": "string",
                    "description": "Filter by geographic region"
                }
            },
            "required": []
        }
    }
}
```

---

### Tool: `find_coordination_opportunities`

```python
def find_coordination_opportunities(hospital_name: str) -> dict:
    """
    Find other hospitals serving the same patient cohorts that could 
    benefit from formal coordination.
    
    Use this tool when the user asks about:
    - Which hospitals should coordinate
    - Care coordination opportunities
    - Partner identification
    
    Args:
        hospital_name: Name of the hospital to analyze
        
    Returns:
        {
            "hospital": "Children's Mercy Kansas City",
            "current_coordination": {
                "formal_partners": 3,
                "coordination_types": ["shared_ehr", "care_conference"]
            },
            "coordination_opportunities": [
                {
                    "partner_hospital": "KU Medical Center",
                    "shared_cohorts": [
                        {"cohort_id": "cohort_cardiac_tier4_kc", "patient_count": 28},
                        {"cohort_id": "cohort_neuro_tier3_kc", "patient_count": 35}
                    ],
                    "total_shared_patients": 63,
                    "current_coordination": "none",
                    "overlap_care_types": ["specialty", "surgical"],
                    "recommendation": "High priority - establish care conference protocol",
                    "priority_score": 92
                },
                {
                    "partner_hospital": "St. Luke's Hospital",
                    "shared_cohorts": [...],
                    "current_coordination": "transfer_protocol",
                    "recommendation": "Add shared EHR access for ED coordination",
                    "priority_score": 78
                }
            ],
            "potential_impact": {
                "patients_benefiting": 185,
                "estimated_encounter_reduction": "15-20%",
                "estimated_cost_savings": "$450K-$600K annually"
            }
        }
    """
```

**Gremlin Query:**

```groovy
// Find hospitals serving same cohorts without coordination
g.V().has('hospital', 'name', hospital_name).as('source')
    .in('receives_care_at').as('cohort')
    .out('receives_care_at')
    .where(neq('source'))
    .as('partner')
    .where(
        __.not(
            select('source').out('coordinated_with').where(eq('partner'))
        )
    )
    .group()
    .by(select('partner').values('name'))
    .by(
        select('cohort').valueMap('cohort_id', 'patient_count').fold()
    )
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "find_coordination_opportunities",
        "description": "Find hospitals serving the same CMC patient cohorts that could benefit from formal coordination relationships.",
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

### Tool: `identify_cmc_mentors`

```python
def identify_cmc_mentors(diagnosis_category: str) -> dict:
    """
    Find hospitals with strong CMC coordination outcomes that could mentor others.
    
    Use this tool when the user asks about:
    - Best practices in CMC care
    - Hospitals to learn from
    - Coordination role models
    
    Args:
        diagnosis_category: Diagnosis category to find mentors for
        
    Returns:
        {
            "diagnosis_category": "cardiac",
            "mentor_hospitals": [
                {
                    "hospital": "Children's Mercy Kansas City",
                    "mentor_score": 94,
                    "strengths": {
                        "coordination_relationships": 8,
                        "care_plan_adherence": 92.5,
                        "patient_satisfaction": 4.7,
                        "outcome_metrics": "top_quartile"
                    },
                    "cohorts_managed": [
                        {"cohort": "cohort_cardiac_tier3_kc", "patients": 45},
                        {"cohort": "cohort_cardiac_tier4_kc", "patients": 28}
                    ],
                    "coordination_practices": [
                        "Weekly multidisciplinary rounds",
                        "Shared EHR with 5 partner hospitals",
                        "Family care coordinator assigned to each patient"
                    ],
                    "contact": "CMC Program Director"
                }
            ],
            "mentorship_needs": [
                {
                    "hospital": "Regional Medical Center",
                    "current_score": 45,
                    "gap_areas": ["No formal coordination protocols", "Limited specialty access"],
                    "recommended_mentor": "Children's Mercy Kansas City",
                    "suggested_focus": "Establish care conference protocol"
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
        "name": "identify_cmc_mentors",
        "description": "Find hospitals with strong CMC coordination outcomes that could mentor others. Identifies best practices and mentorship opportunities.",
        "parameters": {
            "type": "object",
            "properties": {
                "diagnosis_category": {
                    "type": "string",
                    "description": "Diagnosis category to find mentors for (cardiac, neurological, etc.)"
                }
            },
            "required": ["diagnosis_category"]
        }
    }
}
```

---

### Tool: `generate_care_network_diagram`

```python
def generate_care_network_diagram(
    cohort_id: str = None,
    diagnosis_category: str = None,
    hospital_name: str = None
) -> dict:
    """
    Visualize care relationships for a patient cohort or diagnosis category.
    
    Use this tool when the user asks to:
    - Visualize care network
    - Show hospital relationships
    - Draw care coordination map
    
    Args:
        cohort_id: Specific cohort to visualize
        diagnosis_category: Category to visualize (shows all related cohorts)
        hospital_name: Show network centered on a specific hospital
        
    Returns:
        {
            "diagram": "graph LR\\n    subgraph Primary Care...",
            "diagram_type": "mermaid",
            "network_summary": {
                "hospitals": 5,
                "cohorts": 3,
                "coordination_edges": 8,
                "fragmentation_areas": 2
            },
            "legend": {
                "solid_line": "Formal coordination",
                "dashed_line": "Shared patients, no coordination",
                "red_node": "High fragmentation",
                "green_node": "Well-coordinated"
            }
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "generate_care_network_diagram",
        "description": "Generate a Mermaid diagram visualizing care relationships for CMC patients. Shows hospitals, coordination relationships, and fragmentation areas.",
        "parameters": {
            "type": "object",
            "properties": {
                "cohort_id": {
                    "type": "string",
                    "description": "Specific cohort ID to visualize"
                },
                "diagnosis_category": {
                    "type": "string",
                    "description": "Diagnosis category to visualize"
                },
                "hospital_name": {
                    "type": "string",
                    "description": "Center diagram on this hospital"
                }
            },
            "required": []
        }
    }
}
```

---

## Sample Data

### Sample Patient Cohorts

```python
SAMPLE_COHORTS = [
    {
        "cohort_id": "cohort_cardiac_tier4_kc",
        "primary_diagnosis_category": "cardiac",
        "complexity_tier": "tier4",
        "patient_count": 28,
        "avg_age_years": 6.5,
        "avg_providers_per_patient": 15.2,
        "avg_hospitals_per_patient": 4.1,
        "geographic_region": "Greater Kansas City"
    },
    {
        "cohort_id": "cohort_neuro_tier3_kc",
        "primary_diagnosis_category": "neurological",
        "complexity_tier": "tier3",
        "patient_count": 35,
        "avg_age_years": 8.2,
        "avg_providers_per_patient": 11.5,
        "avg_hospitals_per_patient": 3.2,
        "geographic_region": "Greater Kansas City"
    },
    {
        "cohort_id": "cohort_tech_dependent_mo",
        "primary_diagnosis_category": "technology_dependent",
        "complexity_tier": "tier4",
        "patient_count": 42,
        "avg_age_years": 4.8,
        "avg_providers_per_patient": 18.5,
        "avg_hospitals_per_patient": 5.2,
        "geographic_region": "Missouri Statewide"
    }
]
```

### Sample Care Plans

```python
SAMPLE_CARE_PLANS = [
    {
        "plan_id": "plan_cardiac_tier3_v2",
        "name": "Complex Cardiac Care Pathway",
        "diagnosis_category": "cardiac",
        "complexity_tier": "tier3",
        "required_specialties": [
            "Cardiology",
            "Cardiac Surgery", 
            "Pulmonology",
            "Nutrition",
            "Social Work"
        ],
        "coordination_frequency": "monthly",
        "key_transitions": [
            "Post-surgical recovery",
            "ED to inpatient admission",
            "Hospital to home discharge"
        ],
        "version": "2.0"
    }
]
```

---

## Configuration

### domains.yaml Entry

```yaml
cmc_coordination:
  enabled: true
  name: "CMC Care Coordination"
  description: >
    Analyze care patterns for children with medical complexity. Identifies
    care fragmentation, coordination opportunities, and mentorship potential
    across hospital networks.
  version: "1.0.0"
  
  depends_on:
    - referral_network
  
  module: "cmc_coordination"
  
  tools:
    - analyze_care_fragmentation
    - find_coordination_opportunities
    - identify_cmc_mentors
    - generate_care_network_diagram
  
  schema:
    vertex_types:
      - patient_cohort
      - care_plan
      - specialist_group
    edge_types:
      - receives_care_at
      - coordinated_with
      - follows_plan
      - specialist_at
```

---

## Privacy Considerations

### No PHI in Graph

This domain uses **aggregated cohort data only**. No individual patient information is stored:

- Cohorts represent groups of 20+ patients
- No names, MRNs, or dates of birth
- Geographic data is at region level, not address
- All metrics are averages across cohorts

### Data Sources

- Aggregate encounter data from hospital systems
- De-identified cohort definitions from care management programs
- Publicly available program information

---

## Implementation Notes

### Key Gremlin Patterns

```groovy
// Pattern 1: Find all hospitals serving a cohort
g.V().has('patient_cohort', 'cohort_id', cohort_id)
    .out('receives_care_at')
    .valueMap('name', 'type', 'state')

// Pattern 2: Find coordination gaps
g.V().hasLabel('hospital').as('h1')
    .in('receives_care_at')
    .out('receives_care_at')
    .where(neq('h1')).as('h2')
    .where(
        __.not(
            select('h1').out('coordinated_with').where(eq('h2'))
        )
    )
    .select('h1', 'h2')
    .by('name')
    .by('name')
    .dedup()

// Pattern 3: Calculate fragmentation score
g.V().has('patient_cohort', 'cohort_id', cohort_id)
    .project('cohort', 'hospital_count', 'coordination_count')
    .by('cohort_id')
    .by(__.out('receives_care_at').count())
    .by(
        __.out('receives_care_at')
            .outE('coordinated_with')
            .count()
    )
```

### Dependencies

- Uses existing `hospital` vertices from referral network
- Extends hospital relationships with `coordinated_with` edges
- Can leverage `refers_to` edges to identify implicit coordination needs

---

*Document Version: 1.0*  
*Last Updated: January 2026*
