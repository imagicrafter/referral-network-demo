#!/usr/bin/env python3
"""
CLI interface for referral network tools.
Used by the Claude agent to query the database.
"""
import sys
import json
import argparse
import agent_tools


def main():
    parser = argparse.ArgumentParser(description='Referral Network Query Tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # find_hospital
    p = subparsers.add_parser('find_hospital', help='Search for hospitals by name')
    p.add_argument('name', help='Hospital name to search for')

    # get_referral_sources
    p = subparsers.add_parser('get_referral_sources', help='Find hospitals that refer to a hospital')
    p.add_argument('hospital_name', help='Hospital name (exact match)')

    # get_referral_destinations
    p = subparsers.add_parser('get_referral_destinations', help='Find hospitals that receive referrals')
    p.add_argument('hospital_name', help='Hospital name (exact match)')

    # get_network_statistics
    subparsers.add_parser('get_network_statistics', help='Get overall network statistics')

    # find_referral_path
    p = subparsers.add_parser('find_referral_path', help='Find path between two hospitals')
    p.add_argument('from_hospital', help='Source hospital ID')
    p.add_argument('to_hospital', help='Destination hospital ID')

    # get_providers_by_specialty
    p = subparsers.add_parser('get_providers_by_specialty', help='List providers by specialty')
    p.add_argument('specialty', help='Medical specialty')

    # get_hospitals_by_service
    p = subparsers.add_parser('get_hospitals_by_service', help='Find hospitals offering a service')
    p.add_argument('service', help='Service line name')

    # analyze_rural_access
    p = subparsers.add_parser('analyze_rural_access', help='Analyze rural hospital access')
    p.add_argument('service', help='Service name to analyze access for')

    # list - show available commands
    subparsers.add_parser('list', help='List all available commands')

    args = parser.parse_args()

    if args.command is None or args.command == 'list':
        print("Available commands:")
        print("  find_hospital <name>           - Search for hospitals by name")
        print("  get_referral_sources <id>      - Find hospitals that refer to a hospital")
        print("  get_referral_destinations <id> - Find hospitals that receive referrals")
        print("  get_network_statistics         - Get overall network statistics")
        print("  find_referral_path <from> <to> - Find path between two hospitals")
        print("  get_providers_by_specialty <s> - List providers by specialty")
        print("  get_hospitals_by_service <s>   - Find hospitals offering a service")
        print("  analyze_rural_access <service> - Analyze rural hospital access to a service")
        return

    try:
        if args.command == 'find_hospital':
            result = agent_tools.find_hospital(args.name)
        elif args.command == 'get_referral_sources':
            result = agent_tools.get_referral_sources(args.hospital_name)
        elif args.command == 'get_referral_destinations':
            result = agent_tools.get_referral_destinations(args.hospital_name)
        elif args.command == 'get_network_statistics':
            result = agent_tools.get_network_statistics()
        elif args.command == 'find_referral_path':
            result = agent_tools.find_referral_path(args.from_hospital, args.to_hospital)
        elif args.command == 'get_providers_by_specialty':
            result = agent_tools.get_providers_by_specialty(args.specialty)
        elif args.command == 'get_hospitals_by_service':
            result = agent_tools.get_hospitals_by_service(args.service)
        elif args.command == 'analyze_rural_access':
            result = agent_tools.analyze_rural_access(args.service)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
