"""
Example Gremlin queries for the referral network.
Compatible with Azure Cosmos DB Gremlin API.
"""
from cosmos_connection import get_client, execute_query
import json

def print_results(title, results):
    """Pretty print query results."""
    print(f"\n{'='*50}")
    print(f" {title}")
    print('='*50)
    for item in results:
        if isinstance(item, dict):
            print(json.dumps(item, indent=2))
        else:
            print(item)

def main():
    client = get_client()
    
    try:
        # Query 1: List all hospitals
        print_results(
            "All Hospitals",
            execute_query(client, 
                "g.V().hasLabel('hospital').valueMap('name', 'city', 'state', 'type')"
            )
        )
        
        # Query 2: Find rural hospitals
        print_results(
            "Rural Hospitals",
            execute_query(client,
                "g.V().hasLabel('hospital').has('rural', true).values('name')"
            )
        )
        
        # Query 3: Which hospitals refer to Children's Mercy?
        print_results(
            "Hospitals Referring to Children's Mercy",
            execute_query(client, 
                "g.V().has('hospital', 'name', 'Children\\'s Mercy Kansas City').in('refers_to').valueMap('name', 'city')"
            )
        )
        
        # Query 4: Top referral sources by volume (Cosmos DB uses decr instead of desc)
        print_results(
            "Top Referral Sources to Children's Mercy (by volume)",
            execute_query(client, """
                g.V().has('hospital', 'name', 'Children\\'s Mercy Kansas City')
                  .inE('refers_to')
                  .order().by('count', decr)
                  .project('from_hospital', 'referral_count')
                  .by(outV().values('name'))
                  .by('count')
            """)
        )
        
        # Query 5: Which tertiary hospitals receive referrals from rural hospitals?
        print_results(
            "Rural to Tertiary Referral Patterns",
            execute_query(client, """
                g.V().hasLabel('hospital').has('rural', true)
                  .outE('refers_to')
                  .inV().has('type', 'tertiary')
                  .path()
                  .by('name')
                  .by('count')
                  .by('name')
            """)
        )
        
        # Query 6: Find all providers at Children's Mercy
        print_results(
            "Providers at Children's Mercy",
            execute_query(client,
                "g.V().has('hospital', 'name', 'Children\\'s Mercy Kansas City').out('employs').valueMap('name', 'specialty')"
            )
        )
        
        # Query 7: Which hospitals specialize in Cardiac Surgery?
        print_results(
            "Hospitals with Cardiac Surgery Programs",
            execute_query(client, """
                g.V().has('service_line', 'name', 'Cardiac Surgery')
                  .in('specializes_in')
                  .valueMap('name')
            """)
        )
        
        # Query 8: Network centrality - which hospital receives the most referrals?
        print_results(
            "Hospitals by Inbound Referral Count",
            execute_query(client, """
                g.V().hasLabel('hospital')
                  .project('hospital', 'inbound_referrals')
                  .by('name')
                  .by(inE('refers_to').count())
            """)
        )
        
        # Query 9: Find referral paths between two hospitals
        print_results(
            "Paths from Prairie Community to Children's Mercy",
            execute_query(client, """
                g.V().has('hospital', 'name', 'Prairie Community Hospital')
                  .repeat(out('refers_to').simplePath())
                  .until(has('name', 'Children\\'s Mercy Kansas City'))
                  .path()
                  .by('name')
                  .limit(5)
            """)
        )
        
        # Query 10: List all providers and their hospitals
        print_results(
            "All Providers and Their Hospitals",
            execute_query(client, """
                g.V().hasLabel('hospital')
                  .out('employs')
                  .project('provider', 'hospital')
                  .by('name')
                  .by(__.in('employs').values('name'))
            """)
        )
        
    finally:
        client.close()

if __name__ == "__main__":
    main()