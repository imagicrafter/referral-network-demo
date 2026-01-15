"""
Azure Functions backend API for Referral Network Agent Tools.
Exposes query functions as HTTP endpoints that can be called by the DO ADK agent.

Refactored to use modular architecture with ToolRegistry.
"""
import sys
import os

# Add parent directory to path for src/ imports (needed for Azure Functions deployment)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import azure.functions as func
import json
import logging

# Import from core modules
from src.core.tool_registry import ToolRegistry
from src.core.cosmos_connection import get_client, execute_query

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Initialize registry once at module load
_registry = None
_client = None


def get_registry():
    """Get or create the tool registry singleton."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load_domains()
    return _registry


def get_graph_client():
    """Get or create the Gremlin client."""
    global _client
    if _client is None:
        _client = get_client()
    return _client


def _clean_value_map(results: list) -> list:
    """Convert Gremlin valueMap results to cleaner dictionaries."""
    cleaned = []
    for item in results:
        if isinstance(item, dict):
            clean_item = {}
            for key, value in item.items():
                # valueMap returns lists for each property
                if isinstance(value, list) and len(value) == 1:
                    clean_item[key] = value[0]
                else:
                    clean_item[key] = value
            cleaned.append(clean_item)
        else:
            cleaned.append(item)
    return cleaned


# =============================================================================
# Helper functions
# =============================================================================

def _get_all_hospitals():
    """Get all hospitals with their properties."""
    client = get_graph_client()
    query = "g.V().hasLabel('hospital').valueMap(true)"
    results = execute_query(client, query)
    return _clean_value_map(results)


def _get_all_referrals():
    """Get all referral relationships."""
    client = get_graph_client()
    query = """
    g.E().hasLabel('refers_to')
      .project('from_name', 'to_name', 'count', 'avg_acuity')
      .by(outV().values('name'))
      .by(inV().values('name'))
      .by('count')
      .by('avg_acuity')
    """
    return execute_query(client, query)


# =============================================================================
# Health check
# =============================================================================

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "referral-network-api"}),
        mimetype="application/json"
    )


# =============================================================================
# Query Tool Endpoints
# =============================================================================

@app.route(route="tools/find_hospital", methods=["POST"])
def find_hospital(req: func.HttpRequest) -> func.HttpResponse:
    """Find hospitals matching the given criteria."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("find_hospital")
        body = req.get_json()
        results = tool_func(
            name=body.get("name"),
            state=body.get("state"),
            hospital_type=body.get("hospital_type"),
            rural=body.get("rural")
        )
        return func.HttpResponse(json.dumps(results), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in find_hospital: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/get_referral_sources", methods=["POST"])
def get_referral_sources(req: func.HttpRequest) -> func.HttpResponse:
    """Find all hospitals that refer patients to the specified hospital."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("get_referral_sources")
        body = req.get_json()
        hospital_name = body.get("hospital_name")
        if not hospital_name:
            return func.HttpResponse(
                json.dumps({"error": "hospital_name is required"}),
                status_code=400, mimetype="application/json"
            )
        results = tool_func(hospital_name)
        return func.HttpResponse(json.dumps(results), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in get_referral_sources: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/get_referral_destinations", methods=["POST"])
def get_referral_destinations(req: func.HttpRequest) -> func.HttpResponse:
    """Find all hospitals that receive referrals from the specified hospital."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("get_referral_destinations")
        body = req.get_json()
        hospital_name = body.get("hospital_name")
        if not hospital_name:
            return func.HttpResponse(
                json.dumps({"error": "hospital_name is required"}),
                status_code=400, mimetype="application/json"
            )
        results = tool_func(hospital_name)
        return func.HttpResponse(json.dumps(results), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in get_referral_destinations: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/get_network_statistics", methods=["POST", "GET"])
def get_network_statistics(req: func.HttpRequest) -> func.HttpResponse:
    """Get overall statistics about the referral network."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("get_network_statistics")
        stats = tool_func()
        return func.HttpResponse(json.dumps(stats), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in get_network_statistics: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/find_referral_path", methods=["POST"])
def find_referral_path(req: func.HttpRequest) -> func.HttpResponse:
    """Find referral paths between two hospitals."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("find_referral_path")
        body = req.get_json()
        from_hospital = body.get("from_hospital")
        to_hospital = body.get("to_hospital")
        max_hops = body.get("max_hops", 3)
        if not from_hospital or not to_hospital:
            return func.HttpResponse(
                json.dumps({"error": "from_hospital and to_hospital are required"}),
                status_code=400, mimetype="application/json"
            )
        results = tool_func(from_hospital, to_hospital, max_hops)
        return func.HttpResponse(json.dumps(results), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in find_referral_path: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/get_providers_by_specialty", methods=["POST"])
def get_providers_by_specialty(req: func.HttpRequest) -> func.HttpResponse:
    """Find providers by specialty and their hospital affiliations."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("get_providers_by_specialty")
        body = req.get_json()
        specialty = body.get("specialty")
        if not specialty:
            return func.HttpResponse(
                json.dumps({"error": "specialty is required"}),
                status_code=400, mimetype="application/json"
            )
        results = tool_func(specialty)
        return func.HttpResponse(json.dumps(results), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in get_providers_by_specialty: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/get_hospitals_by_service", methods=["POST"])
def get_hospitals_by_service(req: func.HttpRequest) -> func.HttpResponse:
    """Find hospitals that offer a specific service line."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("get_hospitals_by_service")
        body = req.get_json()
        service_name = body.get("service_name")
        if not service_name:
            return func.HttpResponse(
                json.dumps({"error": "service_name is required"}),
                status_code=400, mimetype="application/json"
            )
        results = tool_func(service_name)
        return func.HttpResponse(json.dumps(results), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in get_hospitals_by_service: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/analyze_rural_access", methods=["POST"])
def analyze_rural_access(req: func.HttpRequest) -> func.HttpResponse:
    """Analyze how rural hospitals connect to specialized services."""
    try:
        registry = get_registry()
        tool_func = registry.get_tool("analyze_rural_access")
        body = req.get_json()
        service_name = body.get("service_name")
        results = tool_func(service_name)
        return func.HttpResponse(json.dumps(results), mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in analyze_rural_access: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


# =============================================================================
# Diagram Generation Endpoints
# =============================================================================

@app.route(route="tools/generate_referral_network_diagram", methods=["POST"])
def api_generate_referral_network_diagram(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a Mermaid diagram showing hospital referral relationships."""
    try:
        registry = get_registry()
        generate_diagram = registry.get_tool("generate_referral_network_diagram")
        body = req.get_json() if req.get_body() else {}
        hospital_name = body.get("hospital_name")
        include_volumes = body.get("include_volumes", True)
        direction = body.get("direction", "LR")

        hospitals = _get_all_hospitals()

        if hospital_name:
            # Get referrals for specific hospital
            client = get_graph_client()
            safe_name = hospital_name.replace("'", "\\'")
            query = f"""
            g.V().has('hospital', 'name', '{safe_name}')
              .bothE('refers_to')
              .project('from_name', 'to_name', 'count')
              .by(outV().values('name'))
              .by(inV().values('name'))
              .by('count')
            """
            referrals = execute_query(client, query)
        else:
            referrals = _get_all_referrals()

        diagram = generate_diagram(
            referrals=referrals,
            hospitals=hospitals,
            hospital_name=hospital_name,
            include_volumes=include_volumes,
            direction=direction
        )

        # Return diagram as plain text so LLM can use it directly
        return func.HttpResponse(diagram, mimetype="text/plain")
    except Exception as e:
        logging.error(f"Error in generate_referral_network_diagram: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/generate_path_diagram", methods=["POST"])
def api_generate_path_diagram(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a Mermaid diagram showing paths between two hospitals."""
    try:
        registry = get_registry()
        generate_diagram = registry.get_tool("generate_path_diagram")
        find_path = registry.get_tool("find_referral_path")
        body = req.get_json()
        from_hospital = body.get("from_hospital")
        to_hospital = body.get("to_hospital")
        max_hops = body.get("max_hops", 3)

        if not from_hospital or not to_hospital:
            return func.HttpResponse(
                json.dumps({"error": "from_hospital and to_hospital are required"}),
                status_code=400, mimetype="application/json"
            )

        hospitals = _get_all_hospitals()
        paths = find_path(from_hospital, to_hospital, max_hops)
        referrals = _get_all_referrals()

        diagram = generate_diagram(
            paths=paths,
            hospitals=hospitals,
            from_hospital=from_hospital,
            to_hospital=to_hospital,
            referrals=referrals
        )

        # Return diagram as plain text so LLM can use it directly
        return func.HttpResponse(diagram, mimetype="text/plain")
    except Exception as e:
        logging.error(f"Error in generate_path_diagram: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/generate_service_network_diagram", methods=["POST"])
def api_generate_service_network_diagram(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a Mermaid diagram showing hospitals that provide a specific service."""
    try:
        registry = get_registry()
        generate_diagram = registry.get_tool("generate_service_network_diagram")
        get_hospitals = registry.get_tool("get_hospitals_by_service")
        body = req.get_json()
        service_name = body.get("service_name")
        include_rankings = body.get("include_rankings", True)

        if not service_name:
            return func.HttpResponse(
                json.dumps({"error": "service_name is required"}),
                status_code=400, mimetype="application/json"
            )

        service_data = get_hospitals(service_name)

        diagram = generate_diagram(
            service_data=service_data,
            service_name=service_name,
            include_rankings=include_rankings
        )

        # Return diagram as plain text so LLM can use it directly
        return func.HttpResponse(diagram, mimetype="text/plain")
    except Exception as e:
        logging.error(f"Error in generate_service_network_diagram: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )
