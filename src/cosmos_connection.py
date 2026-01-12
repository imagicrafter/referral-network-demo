"""
Cosmos DB Gremlin connection helper.
Consolidated from root and azure-functions versions.
"""
import os
from gremlin_python.driver import client, serializer

# Load dotenv only if available and not in Azure Functions
# Azure Functions automatically load app settings as env vars
try:
    from dotenv import load_dotenv
    # Only load if FUNCTIONS_WORKER_RUNTIME not set (not in Azure Functions)
    if not os.getenv("FUNCTIONS_WORKER_RUNTIME"):
        load_dotenv()
except ImportError:
    pass  # dotenv not installed, assume env vars are already set


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
