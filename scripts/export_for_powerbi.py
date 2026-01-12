#!/usr/bin/env python3
"""
Export Cosmos DB Gremlin data to CSV and JSON for Power BI.
"""
import sys
import os

# Add parent directory to path for src/ imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import csv
from datetime import datetime
from src.cosmos_connection import get_client, execute_query

OUTPUT_DIR = "powerbi_export"


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    print(f"Output directory: {OUTPUT_DIR}/")


def export_hospitals(client):
    """Export hospitals to CSV and JSON."""
    print("\nExporting hospitals...")

    query = "g.V().hasLabel('hospital').valueMap(true)"
    results = execute_query(client, query)

    # Clean up the data
    hospitals = []
    for r in results:
        hospital = {
            'id': r.get('id', [''])[0] if isinstance(r.get('id'), list) else r.get('id', ''),
            'name': r.get('name', [''])[0] if isinstance(r.get('name'), list) else r.get('name', ''),
            'city': r.get('city', [''])[0] if isinstance(r.get('city'), list) else r.get('city', ''),
            'state': r.get('state', [''])[0] if isinstance(r.get('state'), list) else r.get('state', ''),
            'type': r.get('type', [''])[0] if isinstance(r.get('type'), list) else r.get('type', ''),
            'beds': r.get('beds', [0])[0] if isinstance(r.get('beds'), list) else r.get('beds', 0),
            'rural': r.get('rural', [False])[0] if isinstance(r.get('rural'), list) else r.get('rural', False),
        }
        hospitals.append(hospital)

    # Write CSV
    csv_path = f"{OUTPUT_DIR}/hospitals.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'city', 'state', 'type', 'beds', 'rural'])
        writer.writeheader()
        writer.writerows(hospitals)

    # Write JSON
    json_path = f"{OUTPUT_DIR}/hospitals.json"
    with open(json_path, 'w') as f:
        json.dump(hospitals, f, indent=2)

    print(f"  Exported {len(hospitals)} hospitals")
    return hospitals


def export_providers(client):
    """Export providers to CSV and JSON."""
    print("\nExporting providers...")

    query = "g.V().hasLabel('provider').valueMap(true)"
    results = execute_query(client, query)

    providers = []
    for r in results:
        provider = {
            'id': r.get('id', [''])[0] if isinstance(r.get('id'), list) else r.get('id', ''),
            'name': r.get('name', [''])[0] if isinstance(r.get('name'), list) else r.get('name', ''),
            'specialty': r.get('specialty', [''])[0] if isinstance(r.get('specialty'), list) else r.get('specialty', ''),
            'npi': r.get('npi', [''])[0] if isinstance(r.get('npi'), list) else r.get('npi', ''),
        }
        providers.append(provider)

    # Write CSV
    csv_path = f"{OUTPUT_DIR}/providers.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'specialty', 'npi'])
        writer.writeheader()
        writer.writerows(providers)

    # Write JSON
    json_path = f"{OUTPUT_DIR}/providers.json"
    with open(json_path, 'w') as f:
        json.dump(providers, f, indent=2)

    print(f"  Exported {len(providers)} providers")
    return providers


def export_service_lines(client):
    """Export service lines to CSV and JSON."""
    print("\nExporting service lines...")

    query = "g.V().hasLabel('service_line').valueMap(true)"
    results = execute_query(client, query)

    service_lines = []
    for r in results:
        svc = {
            'id': r.get('id', [''])[0] if isinstance(r.get('id'), list) else r.get('id', ''),
            'name': r.get('name', [''])[0] if isinstance(r.get('name'), list) else r.get('name', ''),
            'category': r.get('category', [''])[0] if isinstance(r.get('category'), list) else r.get('category', ''),
        }
        service_lines.append(svc)

    # Write CSV
    csv_path = f"{OUTPUT_DIR}/service_lines.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'category'])
        writer.writeheader()
        writer.writerows(service_lines)

    # Write JSON
    json_path = f"{OUTPUT_DIR}/service_lines.json"
    with open(json_path, 'w') as f:
        json.dump(service_lines, f, indent=2)

    print(f"  Exported {len(service_lines)} service lines")
    return service_lines


def export_referrals(client):
    """Export referral relationships to CSV and JSON."""
    print("\nExporting referrals...")

    query = """
    g.E().hasLabel('refers_to')
      .project('from_id', 'from_name', 'to_id', 'to_name', 'count', 'avg_acuity')
      .by(outV().values('id'))
      .by(outV().values('name'))
      .by(inV().values('id'))
      .by(inV().values('name'))
      .by('count')
      .by('avg_acuity')
    """
    results = execute_query(client, query)

    referrals = []
    for r in results:
        referral = {
            'from_hospital_id': r.get('from_id', ''),
            'from_hospital_name': r.get('from_name', ''),
            'to_hospital_id': r.get('to_id', ''),
            'to_hospital_name': r.get('to_name', ''),
            'referral_count': r.get('count', 0),
            'avg_acuity': r.get('avg_acuity', 0),
        }
        referrals.append(referral)

    # Write CSV
    csv_path = f"{OUTPUT_DIR}/referrals.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['from_hospital_id', 'from_hospital_name', 'to_hospital_id', 'to_hospital_name', 'referral_count', 'avg_acuity'])
        writer.writeheader()
        writer.writerows(referrals)

    # Write JSON
    json_path = f"{OUTPUT_DIR}/referrals.json"
    with open(json_path, 'w') as f:
        json.dump(referrals, f, indent=2)

    print(f"  Exported {len(referrals)} referral relationships")
    return referrals


def export_employment(client):
    """Export employment relationships to CSV and JSON."""
    print("\nExporting employment relationships...")

    query = """
    g.E().hasLabel('employs')
      .project('hospital_id', 'hospital_name', 'provider_id', 'provider_name', 'fte')
      .by(outV().values('id'))
      .by(outV().values('name'))
      .by(inV().values('id'))
      .by(inV().values('name'))
      .by('fte')
    """
    results = execute_query(client, query)

    employments = []
    for r in results:
        emp = {
            'hospital_id': r.get('hospital_id', ''),
            'hospital_name': r.get('hospital_name', ''),
            'provider_id': r.get('provider_id', ''),
            'provider_name': r.get('provider_name', ''),
            'fte': r.get('fte', 0),
        }
        employments.append(emp)

    # Write CSV
    csv_path = f"{OUTPUT_DIR}/employment.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['hospital_id', 'hospital_name', 'provider_id', 'provider_name', 'fte'])
        writer.writeheader()
        writer.writerows(employments)

    # Write JSON
    json_path = f"{OUTPUT_DIR}/employment.json"
    with open(json_path, 'w') as f:
        json.dump(employments, f, indent=2)

    print(f"  Exported {len(employments)} employment relationships")
    return employments


def export_hospital_services(client):
    """Export hospital-service relationships to CSV and JSON."""
    print("\nExporting hospital services...")

    query = """
    g.E().hasLabel('specializes_in')
      .project('hospital_id', 'hospital_name', 'service_id', 'service_name', 'volume', 'ranking')
      .by(outV().values('id'))
      .by(outV().values('name'))
      .by(inV().values('id'))
      .by(inV().values('name'))
      .by('volume')
      .by('ranking')
    """
    results = execute_query(client, query)

    services = []
    for r in results:
        svc = {
            'hospital_id': r.get('hospital_id', ''),
            'hospital_name': r.get('hospital_name', ''),
            'service_id': r.get('service_id', ''),
            'service_name': r.get('service_name', ''),
            'volume': r.get('volume', 0),
            'ranking': r.get('ranking', 0),
        }
        services.append(svc)

    # Write CSV
    csv_path = f"{OUTPUT_DIR}/hospital_services.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['hospital_id', 'hospital_name', 'service_id', 'service_name', 'volume', 'ranking'])
        writer.writeheader()
        writer.writerows(services)

    # Write JSON
    json_path = f"{OUTPUT_DIR}/hospital_services.json"
    with open(json_path, 'w') as f:
        json.dump(services, f, indent=2)

    print(f"  Exported {len(services)} hospital-service relationships")
    return services


def create_summary(hospitals, providers, service_lines, referrals, employments, hospital_services):
    """Create a summary file with metadata."""
    summary = {
        'export_timestamp': datetime.now().isoformat(),
        'record_counts': {
            'hospitals': len(hospitals),
            'providers': len(providers),
            'service_lines': len(service_lines),
            'referrals': len(referrals),
            'employment_relationships': len(employments),
            'hospital_services': len(hospital_services),
        },
        'files': [
            'hospitals.csv',
            'hospitals.json',
            'providers.csv',
            'providers.json',
            'service_lines.csv',
            'service_lines.json',
            'referrals.csv',
            'referrals.json',
            'employment.csv',
            'employment.json',
            'hospital_services.csv',
            'hospital_services.json',
        ]
    }

    with open(f"{OUTPUT_DIR}/export_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    return summary


def main():
    print("=" * 50)
    print(" Cosmos DB -> Power BI Export")
    print("=" * 50)

    ensure_output_dir()

    client = get_client()

    try:
        hospitals = export_hospitals(client)
        providers = export_providers(client)
        service_lines = export_service_lines(client)
        referrals = export_referrals(client)
        employments = export_employment(client)
        hospital_services = export_hospital_services(client)

        summary = create_summary(hospitals, providers, service_lines, referrals, employments, hospital_services)

        print("\n" + "=" * 50)
        print(" Export Complete!")
        print("=" * 50)
        print(f"\nFiles exported to: {OUTPUT_DIR}/")
        print(f"  - {summary['record_counts']['hospitals']} hospitals")
        print(f"  - {summary['record_counts']['providers']} providers")
        print(f"  - {summary['record_counts']['service_lines']} service lines")
        print(f"  - {summary['record_counts']['referrals']} referral relationships")
        print(f"  - {summary['record_counts']['employment_relationships']} employment relationships")
        print(f"  - {summary['record_counts']['hospital_services']} hospital-service relationships")
        print("\nCSV files are ready for Power BI import:")
        print("  1. Open Power BI Desktop")
        print("  2. Get Data -> Text/CSV")
        print("  3. Select the CSV files from powerbi_export/")
        print("  4. Create relationships between tables using the ID fields")

    finally:
        client.close()


if __name__ == "__main__":
    main()
