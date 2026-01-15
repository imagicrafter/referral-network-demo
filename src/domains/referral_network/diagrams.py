"""
Mermaid diagram generators for referral network domain.

Generates valid Mermaid syntax from Cosmos DB graph data.
"""
import logging
from typing import Dict, List, Optional, Any

from src.core.diagram_base import (
    sanitize_node_id,
    escape_label,
    COLORS,
)


def get_hospital_style(hospital_type: str, is_rural: bool = False) -> str:
    """Get Mermaid style based on hospital type."""
    if is_rural:
        return f"fill:{COLORS['rural']},color:#fff"

    styles = {
        "tertiary": f"fill:{COLORS['tertiary']},color:#fff",
        "community": f"fill:{COLORS['community']},color:#fff",
        "regional": f"fill:{COLORS['regional']},color:#fff",
        "specialty": f"fill:{COLORS['specialty']},color:#fff",
    }
    return styles.get(hospital_type, f"fill:{COLORS['default']},color:#fff")


def _analyze_diagram_complexity(
    node_names: List[str],
    hospital_types: Dict[str, str],
    hospital_rural: Dict[str, bool]
) -> tuple:
    """
    Analyze diagram complexity to determine if title/legend needed.

    Args:
        node_names: List of hospital names in the diagram
        hospital_types: Dict mapping hospital name to type
        hospital_rural: Dict mapping hospital name to rural status

    Returns:
        (is_complex, types_present, has_rural) tuple
    """
    types_present = set()
    has_rural = False

    for name in node_names:
        if hospital_rural.get(name, False):
            has_rural = True
        types_present.add(hospital_types.get(name, 'community'))

    # Count distinct visual styles (rural is a separate style)
    style_count = len(types_present) + (1 if has_rural else 0)

    # Complex if 5+ nodes OR 3+ distinct visual styles
    is_complex = len(node_names) >= 5 or style_count >= 3
    return is_complex, types_present, has_rural


def _generate_hospital_type_legend(types_present: set, has_rural: bool) -> tuple:
    """
    Generate Mermaid subgraph legend for hospital types.

    Args:
        types_present: Set of hospital types in the diagram
        has_rural: Whether any rural hospitals are present

    Returns:
        (legend_lines, style_lines) tuple - lines to add to diagram
    """
    type_config = {
        'tertiary': ('LT', 'Tertiary', COLORS['tertiary']),
        'community': ('LC', 'Community', COLORS['community']),
        'regional': ('LR', 'Regional', COLORS['regional']),
        'specialty': ('LS', 'Specialty', COLORS['specialty']),
    }

    legend_lines = ['    subgraph Legend[" "]']
    style_lines = []

    for type_key, (node_id, label, color) in type_config.items():
        if type_key in types_present:
            legend_lines.append(f'        {node_id}["{label}"]')
            style_lines.append(f'    style {node_id} fill:{color},color:#fff')

    if has_rural:
        legend_lines.append('        LRural["Rural"]')
        style_lines.append(f'    style LRural fill:{COLORS["rural"]},color:#fff')

    legend_lines.append('    end')

    return legend_lines, style_lines


def generate_referral_network_diagram(
    referrals: List[Dict],
    hospitals: List[Dict],
    hospital_name: Optional[str] = None,
    include_volumes: bool = True,
    direction: str = "LR",
    title: Optional[str] = None,
    include_legend: Optional[bool] = None
) -> str:
    """
    Generate a Mermaid flowchart showing hospital referral relationships.

    Args:
        referrals: List of referral relationships with from_name, to_name, count
        hospitals: List of hospital data for styling
        hospital_name: Optional focus hospital
        include_volumes: Whether to show referral counts on edges
        direction: Mermaid direction (LR, TB, RL, BT)
        title: Optional custom title (None = auto-generate for complex diagrams)
        include_legend: Whether to include legend (None = auto-detect based on complexity)

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

    # Analyze complexity for title/legend
    node_names = list(nodes.values())
    is_complex, types_present, has_rural = _analyze_diagram_complexity(
        node_names, hospital_types, hospital_rural
    )

    # Determine if we should show legend
    show_legend = include_legend if include_legend is not None else is_complex

    # Build title (auto-generate for complex diagrams if not provided)
    diagram_title = title
    if diagram_title is None and is_complex:
        if hospital_name:
            diagram_title = f"Referrals for {hospital_name}"
        else:
            diagram_title = "Hospital Referral Network"

    # Build diagram lines
    lines = []

    # Add title frontmatter if we have a title (quote to handle special chars)
    if diagram_title:
        lines.append("---")
        lines.append(f'title: "{diagram_title}"')
        lines.append("---")

    lines.append(f"graph {direction}")

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
    to_hospital: str,
    referrals: List[Dict] = None,
    title: Optional[str] = None,
    include_legend: Optional[bool] = None
) -> str:
    """
    Generate a Mermaid diagram showing paths between two hospitals.

    Args:
        paths: List of paths, each path is a list of hospital names
        hospitals: List of hospital data for styling
        from_hospital: Starting hospital name
        to_hospital: Destination hospital name
        referrals: Optional list of referral data with from_name, to_name, count
        title: Optional custom title (None = auto-generate for complex diagrams)
        include_legend: Whether to include hospital type legend (None = auto-detect)

    Returns:
        Valid Mermaid diagram string
    """
    # Build referral volume lookup
    volume_lookup = {}
    if referrals:
        for ref in referrals:
            from_name = ref.get('from_name', '')
            to_name = ref.get('to_name', '')
            count = ref.get('count', 0)
            if from_name and to_name:
                volume_lookup[(from_name, to_name)] = count

    # Handle empty or invalid paths
    if not paths:
        from_escaped = escape_label(from_hospital)
        to_escaped = escape_label(to_hospital)
        return f'```mermaid\ngraph LR\n    NO_PATH["No path found from {from_escaped} to {to_escaped}"]\n```'

    # Debug: Log what we received (remove in production)
    logging.info(f"[generate_path_diagram] Received paths type: {type(paths)}")
    logging.info(f"[generate_path_diagram] Received paths: {paths[:3] if len(paths) > 3 else paths}")
    if paths:
        logging.info(f"[generate_path_diagram] First path type: {type(paths[0])}")
        logging.info(f"[generate_path_diagram] First path: {paths[0]}")

    # Normalize paths - handle various Gremlin/Cosmos DB return formats
    normalized_paths = []
    for path in paths:
        if isinstance(path, list):
            # Already a list - use as-is
            normalized_paths.append(path)
        elif isinstance(path, dict):
            # Cosmos DB may return path as dict with 'objects' or 'labels' keys
            if 'objects' in path:
                normalized_paths.append(path['objects'])
            elif '@value' in path:
                # GraphSON format
                val = path['@value']
                if isinstance(val, dict) and 'objects' in val:
                    normalized_paths.append(val['objects'])
                elif isinstance(val, list):
                    normalized_paths.append(val)
        elif hasattr(path, 'objects'):
            # Gremlin Path object
            normalized_paths.append(list(path.objects))
        elif hasattr(path, '__iter__') and not isinstance(path, str):
            # Other iterable (but not string)
            normalized_paths.append(list(path))

    logging.info(f"[generate_path_diagram] Normalized paths: {normalized_paths}")

    if not normalized_paths:
        from_escaped = escape_label(from_hospital)
        to_escaped = escape_label(to_hospital)
        return f'```mermaid\ngraph LR\n    NO_PATH["No path found from {from_escaped} to {to_escaped}"]\n```'

    paths = normalized_paths

    # Build hospital lookup for types
    hospital_types = {}
    hospital_rural = {}
    for h in hospitals:
        name = h.get('name', '')
        hospital_types[name] = h.get('type', 'community')
        hospital_rural[name] = h.get('rural', False)

    # Track unique nodes and edges
    nodes = {}
    edges = {}  # Dict to store edge -> (from_hospital, to_hospital) for volume lookup
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
                    styles.append(f"    style {node_id} fill:{COLORS['start']},color:#fff,stroke:#2E7D32,stroke-width:3px")
                elif hospital == to_hospital:
                    styles.append(f"    style {node_id} fill:{COLORS['end']},color:#fff,stroke:#C62828,stroke-width:3px")
                else:
                    styles.append(f"    style {node_id} {get_hospital_style(h_type, is_rural)}")

            # Create edge to next hospital
            if i < len(path) - 1:
                next_hospital = path[i + 1]
                next_id = sanitize_node_id(next_hospital)
                edge_key = (node_id, next_id)
                if edge_key not in edges:
                    edges[edge_key] = (hospital, next_hospital)

    # Safety check - if no nodes were created, paths had unexpected format
    if not nodes:
        from_escaped = escape_label(from_hospital)
        to_escaped = escape_label(to_hospital)
        return f'```mermaid\ngraph LR\n    NO_PATH["No path found from {from_escaped} to {to_escaped}"]\n```'

    # Analyze complexity for title/legend
    node_names = list(nodes.values())
    is_complex, types_present, has_rural = _analyze_diagram_complexity(
        node_names, hospital_types, hospital_rural
    )

    # Determine if we should show hospital type legend (in addition to start/end legend)
    show_type_legend = include_legend if include_legend is not None else is_complex

    # Build title (auto-generate for complex diagrams if not provided)
    from_short = from_hospital.split()[0] if from_hospital else "Start"
    to_short = to_hospital.split()[0] if to_hospital else "End"
    diagram_title = title
    if diagram_title is None and is_complex:
        diagram_title = f"Referral Path: {from_short} to {to_short}"

    # Build diagram lines
    lines = []

    # Add title frontmatter if we have a title (quote to handle special chars)
    if diagram_title:
        lines.append("---")
        lines.append(f'title: "{diagram_title}"')
        lines.append("---")

    lines.append("graph LR")

    # Add node definitions
    for node_id, name in nodes.items():
        escaped_name = escape_label(name)
        lines.append(f'    {node_id}["{escaped_name}"]')

    lines.append("")

    # Add edges with optional volume labels
    for (from_id, to_id), (from_name, to_name) in sorted(edges.items()):
        volume = volume_lookup.get((from_name, to_name), 0)
        if volume:
            lines.append(f'    {from_id} -->|"{volume}"| {to_id}')
        else:
            lines.append(f"    {from_id} --> {to_id}")

    lines.append("")

    # Add styles
    lines.extend(styles)

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"


def generate_service_network_diagram(
    service_data: List[Dict],
    service_name: str,
    include_rankings: bool = True,
    title: Optional[str] = None,
    include_legend: Optional[bool] = None
) -> str:
    """
    Generate a Mermaid diagram showing hospitals that provide a specific service.

    Args:
        service_data: List of hospitals with volume and ranking for the service
        service_name: Name of the service line
        include_rankings: Whether to show hospital rankings
        title: Optional custom title (None = auto-generate for complex diagrams)
        include_legend: Whether to include ranking legend (None = auto-detect)

    Returns:
        Valid Mermaid diagram string
    """
    if not service_data:
        escaped_service = escape_label(service_name)
        return f'```mermaid\ngraph TD\n    NO_DATA["No hospitals found for {escaped_service}"]\n```'

    # Determine complexity (5+ hospitals = complex)
    is_complex = len(service_data) >= 5

    # Determine if we should show legend
    show_legend = include_legend if include_legend is not None else (is_complex and include_rankings)

    # Build title
    diagram_title = title
    if diagram_title is None and is_complex:
        diagram_title = f"{service_name} Service Network"

    # Build diagram lines
    lines = []

    # Add title frontmatter if we have a title (quote to handle special chars)
    if diagram_title:
        lines.append("---")
        lines.append(f'title: "{diagram_title}"')
        lines.append("---")

    lines.append("graph TD")

    # Create central service node (using stadium shape to avoid quote escaping issues)
    service_id = sanitize_node_id(service_name)
    escaped_service = escape_label(service_name)
    lines.append(f'    {service_id}(["{escaped_service}"])')

    # Add hospital nodes
    nodes = []
    edge_lines = []
    styles = [f"    style {service_id} fill:{COLORS['service']},color:#fff,stroke:#4527A0,stroke-width:2px"]

    for item in service_data:
        hospital = item.get('hospital', '')
        volume = item.get('volume', 0)
        ranking = item.get('ranking', 0)

        if not hospital:
            continue

        node_id = sanitize_node_id(hospital)
        escaped_name = escape_label(hospital)

        # Create label with hospital name and metrics (single line with separators)
        if include_rankings and ranking:
            label = f"{escaped_name} | Vol: {volume} | Rank: {ranking}"
        else:
            label = f"{escaped_name} | Vol: {volume}"

        nodes.append(f'    {node_id}["{label}"]')
        edge_lines.append(f"    {service_id} --> {node_id}")

        # Color based on ranking
        if ranking == 1:
            styles.append(f"    style {node_id} fill:{COLORS['highlight']},color:#000")  # Gold
        elif ranking <= 3:
            styles.append(f"    style {node_id} fill:#C0C0C0,color:#000")  # Silver
        else:
            styles.append(f"    style {node_id} fill:#CD7F32,color:#fff")  # Bronze

    lines.extend(nodes)
    lines.append("")
    lines.extend(edge_lines)
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
    edge_lines = []
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
            edge_lines.append(f"    {spec_id} --> {prov_id}")

        if hospital and hospital not in seen_hospitals:
            hosp_id = sanitize_node_id(hospital)
            escaped_hosp = escape_label(hospital)
            nodes.append(f'    {hosp_id}["{escaped_hosp}"]')
            seen_hospitals.add(hospital)
            styles.append(f"    style {hosp_id} fill:{COLORS['tertiary']},color:#fff")

        if hospital:
            hosp_id = sanitize_node_id(hospital)
            edge_lines.append(f"    {prov_id} -.-> {hosp_id}")

    lines.extend(nodes)
    lines.append("")
    lines.extend(edge_lines)
    lines.append("")
    lines.extend(styles)

    mermaid = "\n".join(lines)
    return f"```mermaid\n{mermaid}\n```"
