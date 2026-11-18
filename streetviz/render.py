import json
from html import escape
from urllib.parse import urlsplit
import os
import re
import tempfile
from importlib.resources import files
from pathlib import Path

from .model import Graph, Network, Markings


def group_styles(styles):
    result = {}
    if not isinstance(styles, dict):
        raise ValueError("group styles must be an object keyed by group ID")
    for key, style in styles.items():
        if not re.fullmatch(r"0|[1-9][0-9]*", str(key)) or not isinstance(style, dict):
            raise ValueError(f"invalid group style for {key!r}")
        if set(style) - {"color", "label"}:
            raise ValueError(f"unknown style field for group {key}")
        if "color" in style and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(style["color"])):
            raise ValueError(f"group {key}: expected #RRGGBB")
        if "label" in style and not isinstance(style["label"], str):
            raise ValueError(f"group {key}: expected a text label")
        result[str(key)] = style
    return result


def write_html(network, output, *, markings=None, basemap="osm", groups=None,
               tile_url=None, attribution=None):
    """Write one report from a network and optional sparse markings."""
    if isinstance(network, Graph):
        if markings is None:
            markings = Markings(network.node_marks, network.edge_marks)
        network = Network(network.positions, network.edges)
    if basemap not in ("osm", "none", "custom"):
        raise ValueError("basemap must be osm, none or custom")
    if basemap == "custom":
        if not tile_url or not attribution or not attribution.strip():
            raise ValueError("custom basemap requires tile_url and attribution")
        parts = urlsplit(tile_url)
        if parts.scheme != "https" or not parts.hostname or not all(
            token in parts.path + parts.query for token in ("{x}", "{y}", "{z}")
        ):
            raise ValueError("expected an HTTPS XYZ tile URL with {z}, {x} and {y}")
    elif tile_url is not None or attribution is not None:
        raise ValueError("tile_url and attribution require a custom basemap")
    marks = markings if markings is not None else Markings()
    nodes = {}
    for i, group in marks.node_groups.items():
        if type(i) is not int or not 1 <= i <= len(network.positions):
            raise ValueError(f"unknown node {i}")
        nodes[i] = str(group)
    edges = {}
    for (u, v), group in marks.edge_groups.items():
        pair = min(u, v), max(u, v)
        if type(u) is not int or type(v) is not int or pair not in network._edge_index:
            raise ValueError(f"unknown edge {pair}")
        key = f"{pair[0]},{pair[1]}"
        if key in edges and edges[key] != str(group):
            raise ValueError(f"conflicting groups for edge {pair}")
        edges[key] = str(group)
    for assignments in (marks.node_groups, marks.edge_groups):
        if any(type(g) is not int or g < 0 for g in assignments.values()):
            raise ValueError("group IDs must be nonnegative integers")

    output = Path(output)
    data = {
        "positions": network.positions, "edges": network.edges,
        "nodesMarked": nodes, "edgesMarked": edges, "basemap": basemap,
        "tileUrl": tile_url, "attribution": escape(attribution or ""),
        "groups": group_styles(groups if groups is not None else {}),
    }
    template = files(__package__).joinpath("viewer.html").read_text(encoding="utf-8")
    before, after = template.split("GRAPH_PAYLOAD")
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, encoding="utf-8",
                                     delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(before)
            stream.write(json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", r"\u003c"))
            stream.write(after)
            stream.close()
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
