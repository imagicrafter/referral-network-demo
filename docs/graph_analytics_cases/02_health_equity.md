# Domain: Health Equity & Access Analysis

## Overview

| Attribute | Value |
|-----------|-------|
| **Domain ID** | `health_equity` |
| **Priority** | HIGH |
| **Depends On** | `referral_network` |
| **Estimated Effort** | 2-3 weeks |
| **CHA Alignment** | Child Opportunity Index research, disparity gap initiatives, IPSO equity study |

---

## Business Context

### Problem Statement

CHA's recent research showed quality improvement programs can reduce care disparities. This domain analyzes geographic and demographic access patterns to identify underserved populations and recommend interventions.

Key questions this domain answers:
1. **Access gaps** - Which communities lack timely access to pediatric specialty services?
2. **Equity analysis** - How does service access correlate with Child Opportunity Index?
3. **Expansion planning** - Where should services be added to maximize equity impact?
4. **Disparity tracking** - Are improvement programs reducing or widening gaps?

### Why Graph Analytics?

Geographic access analysis requires understanding the relationship between populations, facilities, and services. Graph databases excel at:
- Modeling service area overlaps
- Finding optimal paths from underserved areas to providers
- Analyzing network effects of adding/removing services

### CHA Programs This Supports

- **IPSO Equity Study** - Research on quality improvement reducing disparities
- **Child Opportunity Index** - Partnership with diversitydatakids.org
- **Rural Health Initiative** - Improving access for rural populations
- **Medicaid Access Programs** - Ensuring coverage translates to access

---

## Power BI vs Agent Comparison

### Power BI Dashboard Shows (The "What")

| Visual | Metric | User Question Answered |
|--------|--------|------------------------|
| Service Map | Facilities with specific services | "Where is NICU care available?" |
| Population Overlay | Demographics by region | "How many children live in each county?" |
| Distance Metrics | Average travel time to care | "What's the median drive time to a children's hospital?" |
| COI Heatmap | Child Opportunity Index by tract | "Which areas have low opportunity scores?" |

### Agent Answers (The "Why")

| User Question | Graph Capability Required | Power BI Limitation |
|---------------|---------------------------|---------------------|
| "Which communities are >60 min from any NICU?" | Service area gap analysis | Cannot compute coverage gaps dynamically |
| "If we add cardiac surgery at Hospital X, how many underserved children gain access?" | What-if network analysis | Static data only |
| "Show the referral path options for a family in rural Missouri needing oncology" | Multi-hop path finding | No pathfinding capability |
| "Which hospitals serve the lowest COI populations?" | Join geographic + facility data with traversal | Complex cross-filtering limited |

---

## Graph Schema

### Vertex Types

#### `census_tract`

Geographic area with demographic data.

```yaml
census_tract:
  label: "census_tract"
  description: "Census tract with pediatric population and opportunity data"
  properties:
    - name: geoid
      type: string
      required: true
      indexed: true
      description: "Census tract GEOID (11 digits)"
      example: "29095010100"
      
    - name: state
      type: string
      required: true
      example: "MO"
      
    - name: county
      type: string
      required: true
      example: "Jackson"
      
    - name: population_under_18
      type: integer
      required: true
      description: "Total population under 18 years"
      example: 2450
      
    - name: child_opportunity_index
      type: float
      required: false
      description: "COI score 0-100, higher is better opportunity"
      example: 45.2
      
    - name: coi_category
      type: string
      required: false
      enum:
        - very_low
        - low
        - moderate
        - high
        - very_high
      example: "low"
      
    - name: median_household_income
      type: float
      required: false
      example: 42500.00
      
    - name: pct_medicaid
      type: float
      required: false
      description: "Percentage of children on Medicaid"
      example: 38.5
      
    - name: pct_uninsured
      type: float
      required: false
      description: "Percentage of children uninsured"
      example: 4.2
      
    - name: urban_rural
      type: string
      required: true
      enum:
        - urban
        - suburban
        - rural
        - frontier
      example: "rural"
      
    - name: latitude
      type: float
      required: true
      description: "Centroid latitude"
      example: 39.0997
      
    - name: longitude
      type: float
      required: true
      description: "Centroid longitude"
      example: -94.5786
```

#### `service_gap`

Identified gap in service coverage.

```yaml
service_gap:
  label: "service_gap"
  description: "Identified gap in pediatric service coverage"
  properties:
    - name: gap_id
      type: string
      required: true
      indexed: true
      example: "gap_nicu_rural_mo_2025"
      
    - name: service_name
      type: string
      required: true
      example: "NICU Level III"
      
    - name: gap_type
      type: string
      required: true
      enum:
        - distance
        - capacity
        - specialty
        - availability
        - wait_time
      example: "distance"
      
    - name: affected_population
      type: integer
      required: true
      description: "Number of children affected by this gap"
      example: 15000
      
    - name: severity_score
      type: float
      required: true
      description: "Gap severity 0-100, higher is more severe"
      example: 78.5
      
    - name: identified_date
      type: date
      required: true
      example: "2025-01-15"
      
    - name: recommended_action
      type: string
      required: false
      example: "Add NICU services at Regional Medical Center"
```

### Edge Types

#### `serves_population`

Hospital serves a geographic area.

```yaml
serves_population:
  label: "serves_population"
  from_vertex: hospital
  to_vertex: census_tract
  description: "Hospital provides services to this geographic area"
  properties:
    - name: travel_time_minutes
      type: float
      required: true
      description: "Estimated driving time in minutes"
      example: 45.5
      
    - name: distance_miles
      type: float
      required: true
      example: 32.4
      
    - name: is_primary_service_area
      type: boolean
      required: true
      description: "Whether this is the primary (closest) hospital for the tract"
      default: false
      
    - name: patient_volume
      type: integer
      required: false
      description: "Annual patient volume from this tract"
      example: 125
      
    - name: service_types
      type: string
      required: false
      description: "Comma-separated list of services used"
      example: "emergency,inpatient,specialty"
```

#### `has_gap`

Census tract has identified service gap.

```yaml
has_gap:
  label: "has_gap"
  from_vertex: census_tract
  to_vertex: service_gap
  description: "Geographic area has an identified service gap"
  properties:
    - name: nearest_provider_miles
      type: float
      required: true
      description: "Distance to nearest provider of this service"
      example: 85.3
      
    - name: nearest_provider_name
      type: string
      required: false
      example: "Children's Mercy Kansas City"
      
    - name: wait_time_days
      type: integer
      required: false
      description: "Average wait time for appointment"
      example: 45
```

#### `could_serve`

Potential service expansion relationship.

```yaml
could_serve:
  label: "could_serve"
  from_vertex: hospital
  to_vertex: census_tract
  description: "Hospital could serve this area if service was added"
  properties:
    - name: service_if_added
      type: string
      required: true
      description: "Service that would enable coverage"
      example: "Pediatric Cardiology"
      
    - name: travel_time_minutes
      type: float
      required: true
      example: 35.0
      
    - name: population_gained
      type: integer
      required: true
      description: "Additional children who would have access"
      example: 8500
```

---

## Agent Tools

### Tool: `analyze_service_access_gaps`

```python
def analyze_service_access_gaps(
    service_name: str,
    max_travel_minutes: int = 60,
    min_coi_threshold: float = None,
    state: str = None
) -> dict:
    """
    Identify populations with inadequate access to a service.
    
    Use this tool when the user asks about:
    - Which communities lack access to a service
    - Access gaps for specific services
    - Underserved populations
    
    Args:
        service_name: Name of the service (e.g., "NICU", "Pediatric Cardiology")
        max_travel_minutes: Maximum acceptable travel time (default: 60)
        min_coi_threshold: Optional - only include tracts with COI below this value
        state: Optional - filter to specific state
        
    Returns:
        {
            "service": "NICU Level III",
            "access_threshold_minutes": 60,
            "analysis_summary": {
                "total_tracts_analyzed": 1250,
                "tracts_with_access": 980,
                "tracts_without_access": 270,
                "children_without_access": 45000,
                "pct_population_underserved": 12.3
            },
            "underserved_areas": [
                {
                    "geoid": "29095010100",
                    "county": "Jackson",
                    "state": "MO",
                    "population_under_18": 2450,
                    "nearest_provider": "Children's Mercy KC",
                    "travel_time_minutes": 78,
                    "distance_miles": 52.3,
                    "child_opportunity_index": 35.2,
                    "coi_category": "low",
                    "urban_rural": "rural"
                },
                ...
            ],
            "by_coi_category": {
                "very_low": {"tracts": 45, "children": 12000, "pct_underserved": 28.5},
                "low": {"tracts": 82, "children": 18000, "pct_underserved": 18.2},
                "moderate": {"tracts": 65, "children": 8500, "pct_underserved": 8.1},
                "high": {"tracts": 48, "children": 4500, "pct_underserved": 4.2},
                "very_high": {"tracts": 30, "children": 2000, "pct_underserved": 1.8}
            },
            "disparity_ratio": 15.8,
            "disparity_interpretation": "Very low COI areas are 15.8x more likely to lack access than very high COI areas"
        }
    """
```

**Gremlin Query:**

```groovy
// Find census tracts without adequate access to a service
g.V().hasLabel('census_tract')
    .not(
        __.in('serves_population')
            .out('provides')
            .has('service', 'name', service_name)
            .where(
                __.inE('serves_population')
                    .has('travel_time_minutes', lte(max_travel_minutes))
            )
    )
    .project('geoid', 'county', 'state', 'population', 'coi', 'nearest')
    .by('geoid')
    .by('county')
    .by('state')
    .by('population_under_18')
    .by('child_opportunity_index')
    .by(
        __.in('serves_population')
            .out('provides')
            .has('service', 'name', service_name)
            .order().by(__.inE('serves_population').values('travel_time_minutes'))
            .limit(1)
            .values('name')
    )
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "analyze_service_access_gaps",
        "description": "Identify populations lacking adequate access to a pediatric service. Analyzes by travel time threshold and breaks down by Child Opportunity Index categories.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service (e.g., 'NICU', 'Pediatric Cardiology', 'Trauma Center')"
                },
                "max_travel_minutes": {
                    "type": "integer",
                    "description": "Maximum acceptable travel time in minutes (default: 60)",
                    "default": 60
                },
                "min_coi_threshold": {
                    "type": "number",
                    "description": "Optional: only include tracts with COI below this value (0-100)"
                },
                "state": {
                    "type": "string",
                    "description": "Optional: filter to specific state (e.g., 'MO', 'KS')"
                }
            },
            "required": ["service_name"]
        }
    }
}
```

---

### Tool: `find_optimal_service_expansion`

```python
def find_optimal_service_expansion(
    service_name: str,
    num_recommendations: int = 3,
    prioritize_equity: bool = True
) -> dict:
    """
    Recommend hospitals that could most reduce access gaps if they added a service.
    
    Use this tool when the user asks about:
    - Where to add new services
    - Which hospitals should expand capabilities
    - How to reduce access disparities
    
    Args:
        service_name: Name of the service to expand
        num_recommendations: Number of hospitals to recommend
        prioritize_equity: Whether to weight by COI (prioritize underserved)
        
    Returns:
        {
            "service": "Pediatric Cardiology",
            "current_gap": {
                "children_without_access": 45000,
                "tracts_without_access": 270
            },
            "recommendations": [
                {
                    "rank": 1,
                    "hospital": "Regional Medical Center",
                    "city": "Springfield",
                    "state": "MO",
                    "current_services": ["Emergency", "PICU", "General Surgery"],
                    "impact_if_added": {
                        "children_gaining_access": 18500,
                        "tracts_gaining_access": 85,
                        "pct_gap_closed": 41.1,
                        "avg_coi_of_served": 38.2
                    },
                    "equity_score": 92.5,
                    "feasibility_notes": "Has PICU infrastructure, would need catheterization lab"
                },
                {
                    "rank": 2,
                    "hospital": "Community Children's Hospital",
                    ...
                }
            ],
            "combined_impact": {
                "if_top_3_implemented": {
                    "children_gaining_access": 38000,
                    "pct_gap_closed": 84.4,
                    "remaining_gap": 7000
                }
            }
        }
    """
```

**Gremlin Query:**

```groovy
// Find hospitals that could serve underserved areas
g.V().hasLabel('hospital')
    .not(__.out('provides').has('name', service_name))  // Doesn't have service
    .as('hospital')
    .out('could_serve')
    .has('service_if_added', service_name)
    .as('coverage')
    .inV().hasLabel('census_tract')
    .as('tract')
    .select('hospital', 'coverage', 'tract')
    .by(valueMap('name', 'city', 'state'))
    .by(valueMap('travel_time_minutes', 'population_gained'))
    .by(valueMap('population_under_18', 'child_opportunity_index'))
    .group()
    .by(select('hospital'))
    .by(
        fold()
            .project('total_population', 'tract_count', 'avg_coi')
            .by(unfold().select('coverage').values('population_gained').sum())
            .by(unfold().count())
            .by(unfold().select('tract').values('child_opportunity_index').mean())
    )
    .order().by(select(values).select('total_population'), decr)
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "find_optimal_service_expansion",
        "description": "Recommend hospitals that could most reduce access gaps if they added a specific service. Ranks by population impact and optionally prioritizes equity.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to expand"
                },
                "num_recommendations": {
                    "type": "integer",
                    "description": "Number of hospitals to recommend (default: 3)",
                    "default": 3
                },
                "prioritize_equity": {
                    "type": "boolean",
                    "description": "Weight recommendations toward low-COI areas (default: true)",
                    "default": true
                }
            },
            "required": ["service_name"]
        }
    }
}
```

---

### Tool: `compare_access_by_coi`

```python
def compare_access_by_coi(
    service_name: str,
    state: str = None
) -> dict:
    """
    Compare service access metrics between high and low COI areas.
    Identifies statistically significant disparities.
    
    Use this tool when the user asks about:
    - Health equity analysis
    - Disparities in access
    - COI correlation with service availability
    
    Args:
        service_name: Name of the service to analyze
        state: Optional - filter to specific state
        
    Returns:
        {
            "service": "Pediatric Oncology",
            "analysis_type": "equity_comparison",
            "coi_comparison": {
                "very_low_coi": {
                    "coi_range": "0-20",
                    "tracts": 245,
                    "total_children": 85000,
                    "avg_travel_time_minutes": 72.5,
                    "pct_with_access_60min": 45.2,
                    "pct_with_access_30min": 12.1
                },
                "low_coi": {
                    "coi_range": "20-40",
                    ...
                },
                "moderate_coi": {
                    "coi_range": "40-60",
                    ...
                },
                "high_coi": {
                    "coi_range": "60-80",
                    ...
                },
                "very_high_coi": {
                    "coi_range": "80-100",
                    "tracts": 180,
                    "total_children": 62000,
                    "avg_travel_time_minutes": 28.3,
                    "pct_with_access_60min": 94.5,
                    "pct_with_access_30min": 78.2
                }
            },
            "disparity_metrics": {
                "travel_time_ratio": 2.56,
                "access_gap_60min": 49.3,
                "access_gap_30min": 66.1,
                "statistical_significance": "p < 0.001",
                "effect_size": "large"
            },
            "interpretation": "Children in very low COI areas travel 2.6x longer and are half as likely to have 60-minute access compared to very high COI areas."
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "compare_access_by_coi",
        "description": "Compare service access between high and low Child Opportunity Index areas. Quantifies health equity disparities with statistical analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to analyze"
                },
                "state": {
                    "type": "string",
                    "description": "Optional: filter to specific state"
                }
            },
            "required": ["service_name"]
        }
    }
}
```

---

### Tool: `find_referral_options`

```python
def find_referral_options(
    from_location: str,
    service_name: str,
    max_options: int = 5
) -> dict:
    """
    Find referral options for a family needing a specific service.
    
    Use this tool when the user asks about:
    - Where a patient can be referred
    - Options for families in a specific area
    - Closest providers of a service
    
    Args:
        from_location: Census tract GEOID, city name, or hospital name
        service_name: Name of the needed service
        max_options: Maximum number of options to return
        
    Returns:
        {
            "from_location": "Rural Jackson County, MO",
            "service_needed": "Pediatric Neurosurgery",
            "options": [
                {
                    "rank": 1,
                    "hospital": "Children's Mercy Kansas City",
                    "city": "Kansas City",
                    "state": "MO",
                    "travel_time_minutes": 65,
                    "distance_miles": 48.2,
                    "service_details": {
                        "program_size": "Large",
                        "surgeons": 8,
                        "annual_cases": 450
                    },
                    "referral_path": "Direct"
                },
                {
                    "rank": 2,
                    "hospital": "St. Louis Children's Hospital",
                    "city": "St. Louis",
                    "state": "MO",
                    "travel_time_minutes": 180,
                    "distance_miles": 245.0,
                    "referral_path": "Via Regional Medical Center"
                }
            ],
            "access_notes": "Closest option requires 65+ minute drive. Consider telemedicine for initial consult."
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "find_referral_options",
        "description": "Find referral options for a family needing a specific service from a given location. Returns ranked list of providers with travel times and referral paths.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_location": {
                    "type": "string",
                    "description": "Starting location - census tract GEOID, city name, or hospital name"
                },
                "service_name": {
                    "type": "string",
                    "description": "Name of the needed service"
                },
                "max_options": {
                    "type": "integer",
                    "description": "Maximum options to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["from_location", "service_name"]
        }
    }
}
```

---

### Tool: `generate_equity_map_diagram`

```python
def generate_equity_map_diagram(
    service_name: str,
    state: str = None,
    highlight_gaps: bool = True
) -> dict:
    """
    Generate a diagram showing service coverage with equity overlay.
    
    Use this tool when the user asks to:
    - Visualize access gaps
    - Show service coverage map
    - Display equity analysis
    
    Args:
        service_name: Name of the service
        state: Optional - filter to specific state
        highlight_gaps: Whether to highlight underserved areas
        
    Returns:
        {
            "diagram": "graph TB\\n    subgraph Covered Areas...",
            "diagram_type": "mermaid",
            "coverage_summary": {
                "covered_population": 850000,
                "uncovered_population": 45000,
                "coverage_rate": 95.0
            },
            "legend": {
                "green": "Within 30 min",
                "yellow": "30-60 min",
                "orange": "60-90 min",
                "red": "90+ min or no access"
            }
        }
    """
```

**Tool Definition:**

```json
{
    "type": "function",
    "function": {
        "name": "generate_equity_map_diagram",
        "description": "Generate a diagram visualizing service coverage with gaps highlighted. Shows geographic distribution of access.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to map"
                },
                "state": {
                    "type": "string",
                    "description": "Optional: filter to specific state"
                },
                "highlight_gaps": {
                    "type": "boolean",
                    "description": "Whether to highlight underserved areas (default: true)",
                    "default": true
                }
            },
            "required": ["service_name"]
        }
    }
}
```

---

## Sample Data

### Sample Census Tracts

```python
SAMPLE_CENSUS_TRACTS = [
    {
        "geoid": "29095010100",
        "state": "MO",
        "county": "Jackson",
        "population_under_18": 2450,
        "child_opportunity_index": 35.2,
        "coi_category": "low",
        "median_household_income": 42500,
        "pct_medicaid": 38.5,
        "pct_uninsured": 4.2,
        "urban_rural": "suburban",
        "latitude": 39.0997,
        "longitude": -94.5786
    },
    {
        "geoid": "29077000100",
        "state": "MO",
        "county": "Greene",
        "population_under_18": 1850,
        "child_opportunity_index": 22.8,
        "coi_category": "very_low",
        "median_household_income": 28500,
        "pct_medicaid": 52.3,
        "pct_uninsured": 8.1,
        "urban_rural": "rural",
        "latitude": 37.2090,
        "longitude": -93.2923
    },
    # More tracts...
]
```

### Sample Service Gaps

```python
SAMPLE_SERVICE_GAPS = [
    {
        "gap_id": "gap_nicu_rural_mo_2025",
        "service_name": "NICU Level III",
        "gap_type": "distance",
        "affected_population": 15000,
        "severity_score": 78.5,
        "identified_date": "2025-01-15",
        "recommended_action": "Add NICU services at Regional Medical Center or expand telemedicine"
    },
    {
        "gap_id": "gap_cardiology_southwest_mo_2025",
        "service_name": "Pediatric Cardiology",
        "gap_type": "specialty",
        "affected_population": 28000,
        "severity_score": 65.2,
        "identified_date": "2025-01-15",
        "recommended_action": "Establish outreach clinic at Springfield facility"
    }
]
```

---

## Configuration

### domains.yaml Entry

```yaml
health_equity:
  enabled: true
  name: "Health Equity & Access Analysis"
  description: >
    Analyze geographic and demographic access patterns to identify underserved
    populations and recommend interventions. Correlates service availability
    with Child Opportunity Index and other equity metrics.
  version: "1.0.0"
  
  depends_on:
    - referral_network
  
  module: "health_equity"
  
  tools:
    - analyze_service_access_gaps
    - find_optimal_service_expansion
    - compare_access_by_coi
    - find_referral_options
    - generate_equity_map_diagram
  
  schema:
    vertex_types:
      - census_tract
      - service_gap
    edge_types:
      - serves_population
      - has_gap
      - could_serve
```

---

## Data Sources

### Child Opportunity Index

- **Source:** diversitydatakids.org
- **Update frequency:** Annual
- **Coverage:** All US census tracts
- **Integration:** Download CSV, map to census tract vertices

### Census Data

- **Source:** US Census Bureau ACS 5-year estimates
- **Key tables:** B09001 (population by age), S1701 (poverty), S2701 (insurance)
- **GEOID format:** State (2) + County (3) + Tract (6) = 11 digits

### Travel Time Calculations

- **Method:** Driving time via routing API (Google Maps, OSRM)
- **Assumptions:** Non-rush hour, standard routes
- **Caching:** Pre-compute hospital-to-tract travel times

---

## Implementation Notes

### Extends Referral Network

This domain builds on the `analyze_rural_access` tool already in the referral network domain. It adds:
- Census tract vertices with demographic data
- COI integration
- Service-specific gap analysis
- Equity comparison tools

### Key Gremlin Patterns

```groovy
// Pattern 1: Find underserved areas for a service
g.V().hasLabel('census_tract')
    .where(
        __.in('serves_population')
            .where(__.out('provides').has('name', service_name))
            .values('travel_time_minutes')
            .min()
            .is(gt(60))
    )
    .valueMap()

// Pattern 2: Calculate coverage by COI category
g.V().hasLabel('census_tract')
    .group()
    .by('coi_category')
    .by(
        project('total', 'covered')
        .by(count())
        .by(
            where(
                __.in('serves_population')
                    .where(__.out('provides').has('name', service_name))
                    .has('travel_time_minutes', lte(60))
            )
            .count()
        )
    )

// Pattern 3: Impact analysis for adding a service
g.V().has('hospital', 'name', hospital_name)
    .out('could_serve')
    .has('service_if_added', service_name)
    .inV()
    .values('population_under_18')
    .sum()
```

### Performance Considerations

- Pre-compute travel times (expensive to calculate on-the-fly)
- Index census tract GEOIDs
- Consider materialized views for common equity calculations

---

*Document Version: 1.0*  
*Last Updated: January 2026*
