"""
Cosmos DB Gremlin connection helper.
"""
import os
from dotenv import load_dotenv
from gremlin_python.driver import client, serializer

load_dotenv()

def get_client():
    """Create and return a Gremlin client connected to Cosmos DB."""
    
    account_name = os.getenv("COSMOS_ACCOUNT_NAME")
    primary_key = os.getenv("COSMOS_PRIMARY_KEY")
    database = os.getenv("COSMOS_DATABASE")
    graph = os.getenv("COSMOS_GRAPH")
    
    endpoint = f"wss://{account_name}.gremlin.cosmos.azure.com:443/"
    
    return client.Client(
        url=endpoint,
        traversal_source="g",
        username=f"/dbs/{database}/colls/{graph}",
        password=primary_key,
        message_serializer=serializer.GraphSONSerializersV2d0()
    )

def execute_query(gremlin_client, query, bindings=None):
    """Execute a Gremlin query and return results."""
    if bindings:
        callback = gremlin_client.submitAsync(query, bindings=bindings)
    else:
        callback = gremlin_client.submitAsync(query)
    result = callback.result()
    return result.all().result()

# Test connection
if __name__ == "__main__":
    print("Connecting to Cosmos DB Gremlin...")
    gremlin_client = get_client()
    
    # Simple test query
    result = execute_query(gremlin_client, "g.V().count()")
    print(f"Vertex count: {result}")
    
    gremlin_client.close()
    print("Connection successful!")
