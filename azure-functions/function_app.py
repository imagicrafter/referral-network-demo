"""
Azure Functions backend API for Referral Network Agent Tools.
Exposes query functions as HTTP endpoints that can be called by the DO ADK agent.

Refactored to use shared modules from src/.
"""
import sys
import os

# Add parent directory to path for src/ imports (needed for Azure Functions deployment)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import azure.functions as func
import json
import logging

# Import from shared modules
from src.tools.queries import (
    find_hospital as query_find_hospital,
    get_referral_sources as query_get_referral_sources,
    get_referral_destinations as query_get_referral_destinations,
    get_network_statistics as query_get_network_statistics,
    find_referral_path as query_find_referral_path,
    get_providers_by_specialty as query_get_providers_by_specialty,
    get_hospitals_by_service as query_get_hospitals_by_service,
    analyze_rural_access as query_analyze_rural_access,
    get_graph_client,
    _clean_value_map,
)
from src.tools.diagram_generators import (
    generate_referral_network_diagram,
    generate_path_diagram,
    generate_service_network_diagram,
)
from src.cosmos_connection import execute_query

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


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
        body = req.get_json()
        results = query_find_hospital(
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
        body = req.get_json()
        hospital_name = body.get("hospital_name")
        if not hospital_name:
            return func.HttpResponse(
                json.dumps({"error": "hospital_name is required"}),
                status_code=400, mimetype="application/json"
            )
        results = query_get_referral_sources(hospital_name)
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
        body = req.get_json()
        hospital_name = body.get("hospital_name")
        if not hospital_name:
            return func.HttpResponse(
                json.dumps({"error": "hospital_name is required"}),
                status_code=400, mimetype="application/json"
            )
        results = query_get_referral_destinations(hospital_name)
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
        stats = query_get_network_statistics()
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
        body = req.get_json()
        from_hospital = body.get("from_hospital")
        to_hospital = body.get("to_hospital")
        max_hops = body.get("max_hops", 3)
        if not from_hospital or not to_hospital:
            return func.HttpResponse(
                json.dumps({"error": "from_hospital and to_hospital are required"}),
                status_code=400, mimetype="application/json"
            )
        results = query_find_referral_path(from_hospital, to_hospital, max_hops)
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
        body = req.get_json()
        specialty = body.get("specialty")
        if not specialty:
            return func.HttpResponse(
                json.dumps({"error": "specialty is required"}),
                status_code=400, mimetype="application/json"
            )
        results = query_get_providers_by_specialty(specialty)
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
        body = req.get_json()
        service_name = body.get("service_name")
        if not service_name:
            return func.HttpResponse(
                json.dumps({"error": "service_name is required"}),
                status_code=400, mimetype="application/json"
            )
        results = query_get_hospitals_by_service(service_name)
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
        body = req.get_json()
        service_name = body.get("service_name")
        results = query_analyze_rural_access(service_name)
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

        diagram = generate_referral_network_diagram(
            referrals=referrals,
            hospitals=hospitals,
            hospital_name=hospital_name,
            include_volumes=include_volumes,
            direction=direction
        )

        return func.HttpResponse(
            json.dumps({"diagram": diagram, "referral_count": len(referrals)}),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in generate_referral_network_diagram: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/generate_path_diagram", methods=["POST"])
def api_generate_path_diagram(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a Mermaid diagram showing paths between two hospitals."""
    try:
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
        paths = query_find_referral_path(from_hospital, to_hospital, max_hops)

        diagram = generate_path_diagram(
            paths=paths,
            hospitals=hospitals,
            from_hospital=from_hospital,
            to_hospital=to_hospital
        )

        return func.HttpResponse(
            json.dumps({"diagram": diagram, "paths_found": len(paths)}),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in generate_path_diagram: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="tools/generate_service_network_diagram", methods=["POST"])
def api_generate_service_network_diagram(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a Mermaid diagram showing hospitals that provide a specific service."""
    try:
        body = req.get_json()
        service_name = body.get("service_name")
        include_rankings = body.get("include_rankings", True)

        if not service_name:
            return func.HttpResponse(
                json.dumps({"error": "service_name is required"}),
                status_code=400, mimetype="application/json"
            )

        service_data = query_get_hospitals_by_service(service_name)

        diagram = generate_service_network_diagram(
            service_data=service_data,
            service_name=service_name,
            include_rankings=include_rankings
        )

        return func.HttpResponse(
            json.dumps({"diagram": diagram, "hospitals_count": len(service_data)}),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in generate_service_network_diagram: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )
