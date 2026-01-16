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
