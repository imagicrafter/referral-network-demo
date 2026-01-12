"""
Tool definitions for AI agent frameworks.
Shared by CLI agents, Gradient ADK, and Azure Functions.
"""

TOOL_DEFINITIONS = [
    {
        "name": "find_hospital",
        "description": "Search for hospitals by name, state, type, or rural status. Use partial names like 'Children's Mercy' to find matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Hospital name (partial match supported)"},
                "state": {"type": "string", "description": "State abbreviation (e.g., 'MO', 'KS')"},
                "hospital_type": {"type": "string", "enum": ["tertiary", "community", "regional", "specialty"]},
                "rural": {"type": "boolean", "description": "Whether the hospital is in a rural area"}
            }
        }
    },
    {
        "name": "get_referral_sources",
        "description": "Find all hospitals that refer patients to a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the receiving hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_referral_destinations",
        "description": "Find all hospitals that receive referrals from a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the referring hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_network_statistics",
        "description": "Get overall statistics about the referral network",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "find_referral_path",
        "description": "Find referral paths between two hospitals",
        "parameters": {
            "type": "object",
            "properties": {
                "from_hospital": {"type": "string", "description": "Starting hospital name"},
                "to_hospital": {"type": "string", "description": "Destination hospital name"},
                "max_hops": {"type": "integer", "description": "Maximum intermediate hospitals", "default": 3}
            },
            "required": ["from_hospital", "to_hospital"]
        }
    },
    {
        "name": "get_providers_by_specialty",
        "description": "Find providers by medical specialty",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string", "description": "Medical specialty name"}
            },
            "required": ["specialty"]
        }
    },
    {
        "name": "get_hospitals_by_service",
        "description": "Find hospitals offering a specific service line",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service line"}
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "analyze_rural_access",
        "description": "Analyze how rural hospitals connect to specialized services",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the specialized service"}
            },
            "required": ["service_name"]
        }
    }
]


# Map tool names to functions for easy lookup
def get_tool_functions():
    """
    Returns a dictionary mapping tool names to their implementations.
    Import this after queries module is available to avoid circular imports.
    """
    from src.tools import queries
    return {
        "find_hospital": queries.find_hospital,
        "get_referral_sources": queries.get_referral_sources,
        "get_referral_destinations": queries.get_referral_destinations,
        "get_network_statistics": queries.get_network_statistics,
        "find_referral_path": queries.find_referral_path,
        "get_providers_by_specialty": queries.get_providers_by_specialty,
        "get_hospitals_by_service": queries.get_hospitals_by_service,
        "analyze_rural_access": queries.analyze_rural_access,
    }
