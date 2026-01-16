"""
Mermaid diagram generators for quality improvement domain.

Generates valid Mermaid syntax from Cosmos DB graph data for protocol
adoption and spread visualization.
"""
from typing import Dict, List, Optional
from datetime import datetime

from src.core.diagram_base import (
    sanitize_node_id,
    escape_label,
)
from src.core.cosmos_connection import get_client, execute_query


# Additional colors for adoption waves
ADOPTION_COLORS = {
    "early": "#4CAF50",    # Green - early adopters
    "mid": "#FFC107",      # Yellow/Amber - mid adopters
    "late": "#FF9800",     # Orange - late adopters
    "non_adopter": "#F44336",  # Red - not yet adopted
}


def _safe_string(value: str) -> str:
    """Escape single quotes for Gremlin queries."""
    return value.replace("'", "\\'")


def _classify_adoption_wave(adoption_date: str, release_date: str) -> str:
    """
    Classify hospital into adoption wave based on timing.

    Args:
        adoption_date: Date hospital adopted (YYYY-MM-DD)
        release_date: Protocol release date (YYYY-MM-DD)

    Returns:
        Wave classification: 'early', 'mid', 'late', or 'non_adopter'
    """
    try:
        adopted = datetime.strptime(adoption_date, "%Y-%m-%d")
        released = datetime.strptime(release_date, "%Y-%m-%d")

        days_since_release = (adopted - released).days

        if days_since_release <= 180:  # First 6 months
            return "early"
        elif days_since_release <= 365:  # 6-12 months
            return "mid"
        else:  # 12+ months
            return "late"
    except (ValueError, TypeError):
        return "mid"  # Default if dates can't be parsed


def _get_wave_style(wave: str) -> str:
    """Get Mermaid style for adoption wave."""
    color = ADOPTION_COLORS.get(wave, ADOPTION_COLORS["mid"])
    text_color = "#fff" if wave != "mid" else "#000"
    return f"fill:{color},color:{text_color}"


def generate_adoption_spread_diagram(
    protocol_name: str,
    show_timeline: bool = True,
    max_hospitals: int = 30
) -> str:
    """
    Generate a Mermaid diagram showing how a protocol spread through the network.

    Args:
        protocol_name: Name of the protocol
        show_timeline: Whether to color-code by adoption timing
        max_hospitals: Maximum number of hospitals to include

    Returns:
        Mermaid diagram string wrapped in code fence
    """
    client = get_client()
    safe_protocol = _safe_string(protocol_name)

    # Get protocol release date
    protocol_query = f"""
    g.V().has('protocol', 'name', TextP.containing('{safe_protocol}'))
        .values('release_date')
    """
    release_results = execute_query(client, protocol_query)
    release_date = release_results[0] if release_results else "2024-01-01"

    # Get adopters with adoption dates
    adopters_query = f"""
    g.V().has('protocol', 'name', TextP.containing('{safe_protocol}'))
        .inE('adopted')
        .project('hospital', 'adoption_date', 'compliance_rate', 'type')
        .by(outV().values('name'))
        .by('adoption_date')
        .by('compliance_rate')
        .by(outV().values('type'))
        .limit({max_hospitals})
    """
    adopters = execute_query(client, adopters_query)

    # Get influence relationships (learned_from edges)
    influence_query = f"""
    g.E().hasLabel('learned_from')
        .has('protocol_context', TextP.containing('{safe_protocol}'))
        .project('from', 'to', 'interaction_type')
        .by(outV().values('name'))
        .by(inV().values('name'))
        .by('interaction_type')
    """
    influences = execute_query(client, influence_query)

    if not adopters:
        escaped_protocol = escape_label(protocol_name)
        return f'```mermaid\ngraph LR\n    NO_DATA["No adoption data found for {escaped_protocol}"]\n```'

    # Classify adopters into waves
    hospital_waves: Dict[str, str] = {}
    hospital_compliance: Dict[str, float] = {}
    for adopter in adopters:
        hospital = adopter.get('hospital', '')
        adoption_date = adopter.get('adoption_date', '')
        compliance = adopter.get('compliance_rate', 0)

        wave = _classify_adoption_wave(adoption_date, release_date) if show_timeline else "mid"
        hospital_waves[hospital] = wave
        hospital_compliance[hospital] = compliance

    # Build diagram
    lines = []

    # Add title
    lines.append("---")
    lines.append(f'title: "Protocol Spread: {escape_label(protocol_name)}"')
    lines.append("---")
    lines.append("graph LR")

    # Group hospitals by wave if showing timeline
    if show_timeline:
        waves: Dict[str, List[str]] = {"early": [], "mid": [], "late": []}
        for hospital, wave in hospital_waves.items():
            waves[wave].append(hospital)

        # Add subgraphs for each wave
        wave_labels = {
            "early": "Early Adopters (0-6 months)",
            "mid": "Mid Adopters (6-12 months)",
            "late": "Late Adopters (12+ months)"
        }

        for wave_key, hospitals in waves.items():
            if hospitals:
                lines.append(f"    subgraph {wave_key}[\"{wave_labels[wave_key]}\"]")
                for hospital in hospitals:
                    node_id = sanitize_node_id(hospital)
                    escaped_name = escape_label(hospital)
                    compliance = hospital_compliance.get(hospital, 0)
                    lines.append(f'        {node_id}["{escaped_name}<br/>{compliance}%"]')
                lines.append("    end")
    else:
        # No grouping, just add all nodes
        for hospital in hospital_waves.keys():
            node_id = sanitize_node_id(hospital)
            escaped_name = escape_label(hospital)
            compliance = hospital_compliance.get(hospital, 0)
            lines.append(f'    {node_id}["{escaped_name}<br/>{compliance}%"]')

    lines.append("")

    # Add influence edges
    for influence in influences:
        from_hospital = influence.get('from', '')
        to_hospital = influence.get('to', '')
        interaction_type = influence.get('interaction_type', '')

        # Only add edge if both hospitals are in our adopters list
        if from_hospital in hospital_waves and to_hospital in hospital_waves:
            from_id = sanitize_node_id(from_hospital)
            to_id = sanitize_node_id(to_hospital)

            # Abbreviate interaction type for edge label
            type_abbrev = {
                "site_visit": "visit",
                "webinar": "web",
                "collaborative_meeting": "collab",
                "peer_consult": "consult",
                "publication": "pub",
                "conference_presentation": "conf"
            }
            label = type_abbrev.get(interaction_type, interaction_type[:6] if interaction_type else "")
            lines.append(f'    {from_id} -->|"{label}"| {to_id}')

    lines.append("")

    # Add styles
    for hospital, wave in hospital_waves.items():
        node_id = sanitize_node_id(hospital)
        style = _get_wave_style(wave)
        lines.append(f"    style {node_id} {style}")

    # Add legend if showing timeline
    if show_timeline:
        lines.append("")
        lines.append("    subgraph Legend[\"Legend\"]")
        lines.append('        LE["Early (0-6 mo)"]')
        lines.append('        LM["Mid (6-12 mo)"]')
        lines.append('        LL["Late (12+ mo)"]')
        lines.append("    end")
        lines.append(f"    style LE fill:{ADOPTION_COLORS['early']},color:#fff")
        lines.append(f"    style LM fill:{ADOPTION_COLORS['mid']},color:#000")
        lines.append(f"    style LL fill:{ADOPTION_COLORS['late']},color:#fff")

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"
