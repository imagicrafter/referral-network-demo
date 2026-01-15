"""
Base diagram utilities shared across domain diagram generators.

Extracted from src/tools/diagram_generators.py for reuse across domains.
"""
import hashlib
from typing import Dict


def sanitize_node_id(name: str) -> str:
    """
    Convert entity name to valid Mermaid node ID.
    Uses first letters of each word plus a short hash for uniqueness.

    Args:
        name: Entity name (e.g., hospital name)

    Returns:
        Valid Mermaid node ID (e.g., "CMKC_f9e3")
    """
    # Remove special characters and split into words
    clean_name = name.replace("'", "").replace(".", "").replace("-", " ")
    words = clean_name.split()

    # Take first letter of each word
    initials = "".join(word[0].upper() for word in words if word)

    # Add short hash for uniqueness
    name_hash = hashlib.md5(name.encode()).hexdigest()[:4]

    return f"{initials}_{name_hash}"


def escape_label(text: str) -> str:
    """
    Escape special characters for Mermaid labels.

    Args:
        text: Label text

    Returns:
        Escaped text safe for Mermaid syntax
    """
    return text.replace('"', "'").replace("<", "&lt;").replace(">", "&gt;")


# Color palette for consistent styling across domains
COLORS = {
    # Hospital types
    "tertiary": "#4CAF50",      # Green
    "community": "#2196F3",     # Blue
    "regional": "#9C27B0",      # Purple
    "specialty": "#E91E63",     # Pink
    "rural": "#FF9800",         # Orange
    "default": "#607D8B",       # Gray

    # Status colors
    "start": "#4CAF50",         # Green
    "end": "#F44336",           # Red
    "highlight": "#FFD700",     # Gold

    # Service colors
    "service": "#673AB7",       # Deep Purple
}


def get_style(color_key: str, stroke: bool = False) -> str:
    """
    Get Mermaid style string for a color key.

    Args:
        color_key: Key from COLORS dict
        stroke: Whether to add stroke styling

    Returns:
        Mermaid style string (e.g., "fill:#4CAF50,color:#fff")
    """
    color = COLORS.get(color_key, COLORS["default"])
    text_color = "#fff" if color_key != "highlight" else "#000"

    style = f"fill:{color},color:{text_color}"

    if stroke:
        # Darker stroke version of the color
        style += f",stroke:{color},stroke-width:2px"

    return style
