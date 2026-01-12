"""
Mermaid diagram generators for hospital referral network.
Generates valid Mermaid syntax from Cosmos DB graph data.
"""
import json
import hashlib
from typing import Dict, List, Optional, Any


def sanitize_node_id(name: str) -> str:
    """
    Convert hospital/entity name to valid Mermaid node ID.
    Uses first letters of each word plus a short hash for uniqueness.
    """
    # Remove special characters and split into words
    clean_name = name.replace("'", "").replace(".", "").replace("-", " ")
    words = clean_name.split()

    # Take first letter of each word
    initials = "".join(word[0].upper() for word in words if word)

    # Add short hash for uniqueness (handles "Regional Medical Center" vs "Rural Medical Center")
    name_hash = hashlib.md5(name.encode()).hexdigest()[:4]

    return f"{initials}_{name_hash}"


def escape_label(text: str) -> str:
    """Escape special characters for Mermaid labels."""
    return text.replace('"', "'").replace("<", "&lt;").replace(">", "&gt;")


def get_hospital_style(hospital_type: str, is_rural: bool = False) -> str:
    """Get Mermaid style based on hospital type."""
    if is_rural:
        return "fill:#FF9800,color:#fff"  # Orange for rural

    styles = {
        "tertiary": "fill:#4CAF50,color:#fff",      # Green
        "community": "fill:#2196F3,color:#fff",      # Blue
        "regional": "fill:#9C27B0,color:#fff",       # Purple
        "specialty": "fill:#E91E63,color:#fff",      # Pink
    }
    return styles.get(hospital_type, "fill:#607D8B,color:#fff")  # Default gray


def generate_referral_network_diagram(
    referrals: List[Dict],
    hospitals: List[Dict],
    hospital_name: Optional[str] = None,
    include_volumes: bool = True,
    direction: str = "LR"
) -> str:
    """
    Generate a Mermaid flowchart showing hospital referral relationships.

    Args:
        referrals: List of referral relationships with from_name, to_name, count
        hospitals: List of hospital data for styling
        hospital_name: Optional focus hospital
        include_volumes: Whether to show referral counts on edges
        direction: Mermaid direction (LR, TB, RL, BT)

    Returns:
        Valid Mermaid diagram string
    """
    if not referrals:
        return "```mermaid\ngraph LR\n    NO_DATA[\"No referral data found\"]\n```"

    # Build hospital lookup for types
    hospital_types = {}
    hospital_rural = {}
    for h in hospitals:
        name = h.get('name', '')
        hospital_types[name] = h.get('type', 'community')
        hospital_rural[name] = h.get('rural', False)

    lines = [f"graph {direction}"]

    # Track unique nodes
    nodes = {}
    edges = []
    styles = []

    for ref in referrals:
        from_name = ref.get('from_name', ref.get('referring_hospital', ''))
        to_name = ref.get('to_name', ref.get('destination_hospital', ''))
        count = ref.get('count', ref.get('referral_count', 0))

        if not from_name or not to_name:
            continue

        # Create node IDs
        from_id = sanitize_node_id(from_name)
        to_id = sanitize_node_id(to_name)

        # Add nodes if not seen
        if from_id not in nodes:
            nodes[from_id] = from_name
            h_type = hospital_types.get(from_name, 'community')
            is_rural = hospital_rural.get(from_name, False)
            styles.append(f"    style {from_id} {get_hospital_style(h_type, is_rural)}")

        if to_id not in nodes:
            nodes[to_id] = to_name
            h_type = hospital_types.get(to_name, 'community')
            is_rural = hospital_rural.get(to_name, False)
            styles.append(f"    style {to_id} {get_hospital_style(h_type, is_rural)}")

        # Create edge
        if include_volumes and count:
            edges.append(f"    {from_id} -->|\"{count}\"| {to_id}")
        else:
            edges.append(f"    {from_id} --> {to_id}")

    # Add node definitions
    for node_id, name in nodes.items():
        escaped_name = escape_label(name)
        lines.append(f'    {node_id}["{escaped_name}"]')

    # Add blank line for readability
    lines.append("")

    # Add edges
    lines.extend(edges)

    # Add blank line for readability
    lines.append("")

    # Add styles
    lines.extend(styles)

    # Wrap in code fence
    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"


def generate_path_diagram(
    paths: List[List[str]],
    hospitals: List[Dict],
    from_hospital: str,
    to_hospital: str
) -> str:
    """
    Generate a Mermaid diagram showing paths between two hospitals.

    Args:
        paths: List of paths, each path is a list of hospital names
        hospitals: List of hospital data for styling
        from_hospital: Starting hospital name
        to_hospital: Destination hospital name

    Returns:
        Valid Mermaid diagram string
    """
    if not paths:
        from_escaped = escape_label(from_hospital)
        to_escaped = escape_label(to_hospital)
        return f'```mermaid\ngraph LR\n    NO_PATH["No path found from {from_escaped} to {to_escaped}"]\n```'

    # Build hospital lookup for types
    hospital_types = {}
    hospital_rural = {}
    for h in hospitals:
        name = h.get('name', '')
        hospital_types[name] = h.get('type', 'community')
        hospital_rural[name] = h.get('rural', False)

    lines = ["graph LR"]

    # Track unique nodes and edges
    nodes = {}
    edges = set()
    styles = []

    for path_idx, path in enumerate(paths):
        if not isinstance(path, list):
            continue

        for i, hospital in enumerate(path):
            node_id = sanitize_node_id(hospital)

            # Add node if not seen
            if node_id not in nodes:
                nodes[node_id] = hospital
                h_type = hospital_types.get(hospital, 'community')
                is_rural = hospital_rural.get(hospital, False)

                # Highlight start and end
                if hospital == from_hospital:
                    styles.append(f"    style {node_id} fill:#4CAF50,color:#fff,stroke:#2E7D32,stroke-width:3px")
                elif hospital == to_hospital:
                    styles.append(f"    style {node_id} fill:#F44336,color:#fff,stroke:#C62828,stroke-width:3px")
                else:
                    styles.append(f"    style {node_id} {get_hospital_style(h_type, is_rural)}")

            # Create edge to next hospital
            if i < len(path) - 1:
                next_hospital = path[i + 1]
                next_id = sanitize_node_id(next_hospital)
                edge = f"    {node_id} --> {next_id}"
                edges.add(edge)

    # Add node definitions
    for node_id, name in nodes.items():
        escaped_name = escape_label(name)
        lines.append(f'    {node_id}["{escaped_name}"]')

    lines.append("")

    # Add edges
    lines.extend(sorted(edges))

    lines.append("")

    # Add styles
    lines.extend(styles)

    # Add legend
    lines.append("")
    lines.append("    subgraph Legend")
    lines.append('        START["🟢 Start"]')
    lines.append('        END["🔴 End"]')
    lines.append("    end")

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"


def generate_service_network_diagram(
    service_data: List[Dict],
    service_name: str,
    include_rankings: bool = True
) -> str:
    """
    Generate a Mermaid diagram showing hospitals that provide a specific service.

    Args:
        service_data: List of hospitals with volume and ranking for the service
        service_name: Name of the service line
        include_rankings: Whether to show hospital rankings

    Returns:
        Valid Mermaid diagram string
    """
    if not service_data:
        escaped_service = escape_label(service_name)
        return f'```mermaid\ngraph TD\n    NO_DATA["No hospitals found for {escaped_service}"]\n```'

    lines = ["graph TD"]

    # Create central service node
    service_id = sanitize_node_id(service_name)
    escaped_service = escape_label(service_name)
    lines.append(f'    {service_id}(("{escaped_service}"))')

    # Add hospital nodes
    nodes = []
    edges = []
    styles = [f"    style {service_id} fill:#673AB7,color:#fff,stroke:#4527A0,stroke-width:2px"]

    for item in service_data:
        hospital = item.get('hospital', '')
        volume = item.get('volume', 0)
        ranking = item.get('ranking', 0)

        if not hospital:
            continue

        node_id = sanitize_node_id(hospital)
        escaped_name = escape_label(hospital)

        # Create label with ranking if included
        if include_rankings and ranking:
            label = f"#{ranking}: {escaped_name}<br/>Volume: {volume}"
        else:
            label = f"{escaped_name}<br/>Volume: {volume}"

        nodes.append(f'    {node_id}["{label}"]')
        edges.append(f"    {service_id} --> {node_id}")

        # Color based on ranking
        if ranking == 1:
            styles.append(f"    style {node_id} fill:#FFD700,color:#000")  # Gold
        elif ranking <= 3:
            styles.append(f"    style {node_id} fill:#C0C0C0,color:#000")  # Silver
        else:
            styles.append(f"    style {node_id} fill:#CD7F32,color:#fff")  # Bronze

    lines.extend(nodes)
    lines.append("")
    lines.extend(edges)
    lines.append("")
    lines.extend(styles)

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"


def generate_provider_diagram(
    providers: List[Dict],
    hospitals: List[Dict],
    specialty: Optional[str] = None
) -> str:
    """
    Generate a Mermaid diagram showing providers and their hospital affiliations.

    Args:
        providers: List of provider data with affiliations
        hospitals: List of hospital data
        specialty: Optional specialty filter

    Returns:
        Valid Mermaid diagram string
    """
    if not providers:
        return "```mermaid\ngraph TD\n    NO_DATA[\"No provider data found\"]\n```"

    lines = ["graph TD"]

    nodes = []
    edges = []
    styles = []

    # Group by specialty if not filtered
    if specialty:
        spec_id = sanitize_node_id(specialty)
        escaped_spec = escape_label(specialty)
        nodes.append(f'    {spec_id}(("{escaped_spec}")')
        styles.append(f"    style {spec_id} fill:#009688,color:#fff")

    seen_hospitals = set()

    for prov in providers:
        prov_name = prov.get('provider_name', prov.get('name', ''))
        prov_spec = prov.get('specialty', '')
        hospital = prov.get('hospital', '')

        if not prov_name:
            continue

        prov_id = sanitize_node_id(prov_name)
        escaped_prov = escape_label(prov_name)

        nodes.append(f'    {prov_id}["{escaped_prov}"]')
        styles.append(f"    style {prov_id} fill:#03A9F4,color:#fff")

        if specialty:
            spec_id = sanitize_node_id(specialty)
            edges.append(f"    {spec_id} --> {prov_id}")

        if hospital and hospital not in seen_hospitals:
            hosp_id = sanitize_node_id(hospital)
            escaped_hosp = escape_label(hospital)
            nodes.append(f'    {hosp_id}["{escaped_hosp}"]')
            seen_hospitals.add(hospital)
            styles.append(f"    style {hosp_id} fill:#4CAF50,color:#fff")

        if hospital:
            hosp_id = sanitize_node_id(hospital)
            edges.append(f"    {prov_id} -.-> {hosp_id}")

    lines.extend(nodes)
    lines.append("")
    lines.extend(edges)
    lines.append("")
    lines.extend(styles)

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"
