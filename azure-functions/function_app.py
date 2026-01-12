"""
Azure Functions backend API for Referral Network Agent Tools.
Exposes agent_tools as HTTP endpoints that can be called by the DO ADK agent.
"""
import azure.functions as func
import json
import logging
import os
from typing import Dict, Any, Optional

# Import the Cosmos DB connection and tools
from cosmos_connection import get_client, execute_query

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Global Gremlin client
_client = None


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
                if isinstance(value, list) and len(value) == 1:
                    clean_item[key] = value[0]
                else:
                    clean_item[key] = value
            cleaned.append(clean_item)
        else:
            cleaned.append(item)
    return cleaned


# Health check endpoint
@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "referral-network-api"}),
        mimetype="application/json"
    )


# Tool: find_hospital
@app.route(route="tools/find_hospital", methods=["POST"])
def find_hospital(req: func.HttpRequest) -> func.HttpResponse:
    """
    Find hospitals matching the given criteria.

    Body:
        name: Hospital name (partial match)
        state: State abbreviation
        hospital_type: Type of hospital
        rural: Whether the hospital is in a rural area
    """
    try:
        body = req.get_json()
        name = body.get("name")
        state = body.get("state")
        hospital_type = body.get("hospital_type")
        rural = body.get("rural")

        client = get_graph_client()
        query = "g.V().hasLabel('hospital')"

        if name:
            safe_name = name.replace("'", "\\'")
            query += f".has('name', TextP.containing('{safe_name}'))"
        if state:
            query += f".has('state', '{state}')"
        if hospital_type:
            query += f".has('type', '{hospital_type}')"
        if rural is not None:
            query += f".has('rural', {str(rural).lower()})"

        query += ".valueMap(true)"

        results = execute_query(client, query)
        cleaned = _clean_value_map(results)

        return func.HttpResponse(
            json.dumps(cleaned),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in find_hospital: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: get_referral_sources
@app.route(route="tools/get_referral_sources", methods=["POST"])
def get_referral_sources(req: func.HttpRequest) -> func.HttpResponse:
    """Find all hospitals that refer patients to the specified hospital."""
    try:
        body = req.get_json()
        hospital_name = body.get("hospital_name")

        if not hospital_name:
            return func.HttpResponse(
                json.dumps({"error": "hospital_name is required"}),
                status_code=400,
                mimetype="application/json"
            )

        client = get_graph_client()
        safe_name = hospital_name.replace("'", "\\'")

        query = f"""
        g.V().has('hospital', 'name', '{safe_name}')
          .inE('refers_to')
          .order().by('count', decr)
          .project('referring_hospital', 'referral_count', 'avg_acuity')
          .by(outV().values('name'))
          .by('count')
          .by('avg_acuity')
        """

        results = execute_query(client, query)

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in get_referral_sources: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: get_referral_destinations
@app.route(route="tools/get_referral_destinations", methods=["POST"])
def get_referral_destinations(req: func.HttpRequest) -> func.HttpResponse:
    """Find all hospitals that receive referrals from the specified hospital."""
    try:
        body = req.get_json()
        hospital_name = body.get("hospital_name")

        if not hospital_name:
            return func.HttpResponse(
                json.dumps({"error": "hospital_name is required"}),
                status_code=400,
                mimetype="application/json"
            )

        client = get_graph_client()
        safe_name = hospital_name.replace("'", "\\'")

        query = f"""
        g.V().has('hospital', 'name', '{safe_name}')
          .outE('refers_to')
          .order().by('count', decr)
          .project('destination_hospital', 'referral_count', 'avg_acuity')
          .by(inV().values('name'))
          .by('count')
          .by('avg_acuity')
        """

        results = execute_query(client, query)

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in get_referral_destinations: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: get_network_statistics
@app.route(route="tools/get_network_statistics", methods=["POST", "GET"])
def get_network_statistics(req: func.HttpRequest) -> func.HttpResponse:
    """Get overall statistics about the referral network."""
    try:
        client = get_graph_client()

        stats = {}
        stats['total_hospitals'] = execute_query(client,
            "g.V().hasLabel('hospital').count()")[0]
        stats['total_providers'] = execute_query(client,
            "g.V().hasLabel('provider').count()")[0]
        stats['total_referral_relationships'] = execute_query(client,
            "g.E().hasLabel('refers_to').count()")[0]
        stats['total_referral_volume'] = execute_query(client,
            "g.E().hasLabel('refers_to').values('count').sum()")[0]
        stats['rural_hospitals'] = execute_query(client,
            "g.V().hasLabel('hospital').has('rural', true).count()")[0]
        stats['tertiary_centers'] = execute_query(client,
            "g.V().hasLabel('hospital').has('type', 'tertiary').count()")[0]

        return func.HttpResponse(
            json.dumps(stats),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in get_network_statistics: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: find_referral_path
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
                status_code=400,
                mimetype="application/json"
            )

        client = get_graph_client()
        safe_from = from_hospital.replace("'", "\\'")
        safe_to = to_hospital.replace("'", "\\'")

        query = f"""
        g.V().has('hospital', 'name', '{safe_from}')
          .repeat(out('refers_to').simplePath())
          .until(has('name', '{safe_to}').or().loops().is(gte({max_hops})))
          .has('name', '{safe_to}')
          .path()
          .by('name')
          .limit(10)
        """

        results = execute_query(client, query)

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in find_referral_path: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: get_providers_by_specialty
@app.route(route="tools/get_providers_by_specialty", methods=["POST"])
def get_providers_by_specialty(req: func.HttpRequest) -> func.HttpResponse:
    """Find providers by specialty and their hospital affiliations."""
    try:
        body = req.get_json()
        specialty = body.get("specialty")

        if not specialty:
            return func.HttpResponse(
                json.dumps({"error": "specialty is required"}),
                status_code=400,
                mimetype="application/json"
            )

        client = get_graph_client()
        safe_specialty = specialty.replace("'", "\\'")

        query = f"""
        g.V().hasLabel('provider')
          .has('specialty', '{safe_specialty}')
          .project('provider_name', 'specialty')
          .by('name')
          .by('specialty')
        """

        results = execute_query(client, query)

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in get_providers_by_specialty: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: get_hospitals_by_service
@app.route(route="tools/get_hospitals_by_service", methods=["POST"])
def get_hospitals_by_service(req: func.HttpRequest) -> func.HttpResponse:
    """Find hospitals that offer a specific service line."""
    try:
        body = req.get_json()
        service_name = body.get("service_name")

        if not service_name:
            return func.HttpResponse(
                json.dumps({"error": "service_name is required"}),
                status_code=400,
                mimetype="application/json"
            )

        client = get_graph_client()
        safe_service = service_name.replace("'", "\\'")

        query = f"""
        g.V().has('service_line', 'name', '{safe_service}')
          .inE('specializes_in')
          .order().by('ranking', incr)
          .project('hospital', 'volume', 'ranking')
          .by(outV().values('name'))
          .by('volume')
          .by('ranking')
        """

        results = execute_query(client, query)

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in get_hospitals_by_service: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: analyze_rural_access
@app.route(route="tools/analyze_rural_access", methods=["POST"])
def analyze_rural_access(req: func.HttpRequest) -> func.HttpResponse:
    """Analyze how rural hospitals connect to specialized services."""
    try:
        body = req.get_json()
        service_name = body.get("service_name")

        client = get_graph_client()

        query = """
        g.V().hasLabel('hospital').has('rural', true)
          .project('rural_hospital', 'state')
          .by('name')
          .by('state')
        """

        results = execute_query(client, query)

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in analyze_rural_access: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Import diagram generators
from diagram_generators import (
    generate_referral_network_diagram,
    generate_path_diagram,
    generate_service_network_diagram
)


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


# Tool: generate_referral_network_diagram
@app.route(route="tools/generate_referral_network_diagram", methods=["POST"])
def api_generate_referral_network_diagram(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a Mermaid diagram showing hospital referral relationships."""
    try:
        body = req.get_json() if req.get_body() else {}
        hospital_name = body.get("hospital_name")
        include_volumes = body.get("include_volumes", True)
        direction = body.get("direction", "LR")

        client = get_graph_client()

        # Get hospitals for styling
        hospitals = _get_all_hospitals()

        if hospital_name:
            # Get referrals for specific hospital
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
            # Get all referrals
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
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: generate_path_diagram
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
                status_code=400,
                mimetype="application/json"
            )

        client = get_graph_client()

        # Get hospitals for styling
        hospitals = _get_all_hospitals()

        # Find paths
        safe_from = from_hospital.replace("'", "\\'")
        safe_to = to_hospital.replace("'", "\\'")

        query = f"""
        g.V().has('hospital', 'name', '{safe_from}')
          .repeat(out('refers_to').simplePath())
          .until(has('name', '{safe_to}').or().loops().is(gte({max_hops})))
          .has('name', '{safe_to}')
          .path()
          .by('name')
          .limit(10)
        """

        paths = execute_query(client, query)

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
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Tool: generate_service_network_diagram
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
                status_code=400,
                mimetype="application/json"
            )

        client = get_graph_client()

        safe_service = service_name.replace("'", "\\'")

        query = f"""
        g.V().has('service_line', 'name', '{safe_service}')
          .inE('specializes_in')
          .order().by('ranking', incr)
          .project('hospital', 'volume', 'ranking')
          .by(outV().values('name'))
          .by('volume')
          .by('ranking')
        """

        service_data = execute_query(client, query)

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
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
