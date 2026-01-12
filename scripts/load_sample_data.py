#!/usr/bin/env python3
"""
Load sample referral network data into Cosmos DB Gremlin.
"""
import sys
import os

# Add parent directory to path for src/ imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.cosmos_connection import get_client, execute_query


def clean_graph(client):
    """Remove all vertices and edges."""
    print("Cleaning existing data...")
    execute_query(client, "g.V().drop()")
    print("Graph cleared.")


def load_hospitals(client):
    """Load sample hospital vertices."""

    hospitals = [
        {"id": "hosp-001", "name": "Children's Mercy Kansas City", "city": "Kansas City", "state": "MO", "type": "tertiary", "beds": 354, "rural": False},
        {"id": "hosp-002", "name": "Children's Hospital Colorado", "city": "Aurora", "state": "CO", "type": "tertiary", "beds": 434, "rural": False},
        {"id": "hosp-003", "name": "St. Louis Children's Hospital", "city": "St. Louis", "state": "MO", "type": "tertiary", "beds": 402, "rural": False},
        {"id": "hosp-004", "name": "Regional Medical Center", "city": "Joplin", "state": "MO", "type": "community", "beds": 85, "rural": True},
        {"id": "hosp-005", "name": "Prairie Community Hospital", "city": "Salina", "state": "KS", "type": "community", "beds": 45, "rural": True},
        {"id": "hosp-006", "name": "Heartland Pediatrics", "city": "Topeka", "state": "KS", "type": "specialty", "beds": 30, "rural": False},
        {"id": "hosp-007", "name": "Ozark Regional Medical", "city": "Springfield", "state": "MO", "type": "regional", "beds": 120, "rural": False},
        {"id": "hosp-008", "name": "Nebraska Children's", "city": "Omaha", "state": "NE", "type": "tertiary", "beds": 145, "rural": False},
    ]

    print(f"Loading {len(hospitals)} hospitals...")

    for h in hospitals:
        query = """
        g.addV('hospital')
          .property('id', id)
          .property('partitionKey', pk)
          .property('name', name)
          .property('city', city)
          .property('state', state)
          .property('type', htype)
          .property('beds', beds)
          .property('rural', rural)
        """
        bindings = {
            'id': h["id"],
            'pk': f'hospital_{h["state"]}',
            'name': h["name"],
            'city': h["city"],
            'state': h["state"],
            'htype': h["type"],
            'beds': h["beds"],
            'rural': h["rural"]
        }
        execute_query(client, query, bindings)
        print(f"  Added: {h['name']}")

    print("Hospitals loaded.")


def load_providers(client):
    """Load sample provider vertices."""

    providers = [
        {"id": "prov-001", "name": "Dr. Sarah Chen", "specialty": "Pediatric Cardiology", "npi": "1234567890"},
        {"id": "prov-002", "name": "Dr. Michael Roberts", "specialty": "Pediatric Oncology", "npi": "2345678901"},
        {"id": "prov-003", "name": "Dr. Emily Watson", "specialty": "Pediatric Neurology", "npi": "3456789012"},
        {"id": "prov-004", "name": "Dr. James Park", "specialty": "Pediatric Surgery", "npi": "4567890123"},
        {"id": "prov-005", "name": "Dr. Lisa Martinez", "specialty": "Neonatology", "npi": "5678901234"},
        {"id": "prov-006", "name": "Dr. Robert Kim", "specialty": "Pediatric Cardiology", "npi": "6789012345"},
    ]

    print(f"Loading {len(providers)} providers...")

    for p in providers:
        query = """
        g.addV('provider')
          .property('id', id)
          .property('partitionKey', pk)
          .property('name', name)
          .property('specialty', specialty)
          .property('npi', npi)
        """
        bindings = {
            'id': p["id"],
            'pk': 'provider_midwest',
            'name': p["name"],
            'specialty': p["specialty"],
            'npi': p["npi"]
        }
        execute_query(client, query, bindings)
        print(f"  Added: {p['name']}")

    print("Providers loaded.")


def load_service_lines(client):
    """Load service line vertices."""

    service_lines = [
        {"id": "svc-001", "name": "Cardiac Surgery", "category": "surgical"},
        {"id": "svc-002", "name": "Oncology", "category": "medical"},
        {"id": "svc-003", "name": "NICU", "category": "critical_care"},
        {"id": "svc-004", "name": "Neurology", "category": "medical"},
        {"id": "svc-005", "name": "General Pediatrics", "category": "primary"},
    ]

    print(f"Loading {len(service_lines)} service lines...")

    for s in service_lines:
        query = """
        g.addV('service_line')
          .property('id', id)
          .property('partitionKey', pk)
          .property('name', name)
          .property('category', category)
        """
        bindings = {
            'id': s["id"],
            'pk': 'service_line',
            'name': s["name"],
            'category': s["category"]
        }
        execute_query(client, query, bindings)
        print(f"  Added: {s['name']}")

    print("Service lines loaded.")


def load_referral_edges(client):
    """Load referral relationships between hospitals."""

    referrals = [
        {"from": "hosp-004", "to": "hosp-001", "count": 145, "avg_acuity": 3.2},
        {"from": "hosp-005", "to": "hosp-001", "count": 87, "avg_acuity": 2.8},
        {"from": "hosp-006", "to": "hosp-001", "count": 62, "avg_acuity": 3.5},
        {"from": "hosp-007", "to": "hosp-001", "count": 93, "avg_acuity": 2.9},
        {"from": "hosp-007", "to": "hosp-003", "count": 78, "avg_acuity": 3.1},
        {"from": "hosp-004", "to": "hosp-003", "count": 34, "avg_acuity": 3.4},
        {"from": "hosp-005", "to": "hosp-002", "count": 23, "avg_acuity": 3.0},
        {"from": "hosp-004", "to": "hosp-007", "count": 56, "avg_acuity": 2.1},
        {"from": "hosp-005", "to": "hosp-006", "count": 41, "avg_acuity": 2.3},
        {"from": "hosp-001", "to": "hosp-002", "count": 12, "avg_acuity": 4.2},
        {"from": "hosp-001", "to": "hosp-008", "count": 8, "avg_acuity": 3.8},
        {"from": "hosp-003", "to": "hosp-001", "count": 15, "avg_acuity": 4.0},
    ]

    print(f"Loading {len(referrals)} referral relationships...")

    for r in referrals:
        query = """
        g.V().has('hospital', 'id', from_id)
          .addE('refers_to')
          .to(g.V().has('hospital', 'id', to_id))
          .property('count', cnt)
          .property('avg_acuity', acuity)
        """
        bindings = {
            'from_id': r["from"],
            'to_id': r["to"],
            'cnt': r["count"],
            'acuity': r["avg_acuity"]
        }
        execute_query(client, query, bindings)
        print(f"  Added: {r['from']} -> {r['to']} ({r['count']} referrals)")

    print("Referral edges loaded.")


def load_employment_edges(client):
    """Load hospital-provider employment relationships."""

    employments = [
        {"hospital": "hosp-001", "provider": "prov-001", "fte": 1.0},
        {"hospital": "hosp-001", "provider": "prov-002", "fte": 1.0},
        {"hospital": "hosp-001", "provider": "prov-005", "fte": 0.8},
        {"hospital": "hosp-002", "provider": "prov-003", "fte": 1.0},
        {"hospital": "hosp-003", "provider": "prov-004", "fte": 1.0},
        {"hospital": "hosp-003", "provider": "prov-006", "fte": 1.0},
        {"hospital": "hosp-008", "provider": "prov-005", "fte": 0.2},
    ]

    print(f"Loading {len(employments)} employment relationships...")

    for e in employments:
        query = """
        g.V().has('hospital', 'id', hosp_id)
          .addE('employs')
          .to(g.V().has('provider', 'id', prov_id))
          .property('fte', fte)
        """
        bindings = {
            'hosp_id': e["hospital"],
            'prov_id': e["provider"],
            'fte': e["fte"]
        }
        execute_query(client, query, bindings)
        print(f"  Added: {e['hospital']} employs {e['provider']}")

    print("Employment edges loaded.")


def load_service_edges(client):
    """Load hospital-service line relationships."""

    services = [
        {"hospital": "hosp-001", "service": "svc-001", "volume": 850, "ranking": 5},
        {"hospital": "hosp-001", "service": "svc-002", "volume": 620, "ranking": 12},
        {"hospital": "hosp-001", "service": "svc-003", "volume": 1200, "ranking": 3},
        {"hospital": "hosp-002", "service": "svc-001", "volume": 920, "ranking": 3},
        {"hospital": "hosp-002", "service": "svc-004", "volume": 780, "ranking": 8},
        {"hospital": "hosp-003", "service": "svc-001", "volume": 780, "ranking": 8},
        {"hospital": "hosp-003", "service": "svc-002", "volume": 890, "ranking": 6},
        {"hospital": "hosp-007", "service": "svc-005", "volume": 2400, "ranking": 25},
        {"hospital": "hosp-008", "service": "svc-003", "volume": 650, "ranking": 15},
    ]

    print(f"Loading {len(services)} service line relationships...")

    for s in services:
        query = """
        g.V().has('hospital', 'id', hosp_id)
          .addE('specializes_in')
          .to(g.V().has('service_line', 'id', svc_id))
          .property('volume', volume)
          .property('ranking', ranking)
        """
        bindings = {
            'hosp_id': s["hospital"],
            'svc_id': s["service"],
            'volume': s["volume"],
            'ranking': s["ranking"]
        }
        execute_query(client, query, bindings)
        print(f"  Added: {s['hospital']} -> {s['service']}")

    print("Service edges loaded.")


def verify_data(client):
    """Verify loaded data with counts."""
    print("\n--- Data Verification ---")

    vertex_count = execute_query(client, "g.V().count()")
    print(f"Total vertices: {vertex_count[0]}")

    edge_count = execute_query(client, "g.E().count()")
    print(f"Total edges: {edge_count[0]}")

    hospital_count = execute_query(client, "g.V().hasLabel('hospital').count()")
    print(f"Hospitals: {hospital_count[0]}")

    provider_count = execute_query(client, "g.V().hasLabel('provider').count()")
    print(f"Providers: {provider_count[0]}")

    referral_count = execute_query(client, "g.E().hasLabel('refers_to').count()")
    print(f"Referral relationships: {referral_count[0]}")


def main():
    print("=" * 50)
    print("Referral Network Data Loader")
    print("=" * 50)

    client = get_client()

    try:
        clean_graph(client)
        time.sleep(1)  # Brief pause after cleanup

        load_hospitals(client)
        load_providers(client)
        load_service_lines(client)
        load_referral_edges(client)
        load_employment_edges(client)
        load_service_edges(client)

        verify_data(client)

        print("\n Data loading complete!")

    finally:
        client.close()


if __name__ == "__main__":
    main()
