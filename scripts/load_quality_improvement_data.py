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
