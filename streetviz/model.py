"""File adapters. Node IDs remain one-based throughout the public model."""
import bz2
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Network:
    """Geographic positions in vertex order and undirected one-based endpoints."""
    positions: tuple
    edges: tuple
    _edge_index: frozenset = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        positions = tuple(tuple(p) for p in self.positions)
        if not positions:
            raise ValueError("expected at least one vertex")
        for x, y in positions:
            if not (-180 <= x <= 180 and -85.051129 <= y <= 85.051129):
                raise ValueError("coordinate outside map bounds")
        edges = []
        for u, v in self.edges:
            if any(type(i) is not int or not 1 <= i <= len(positions) for i in (u, v)) or u == v:
                raise ValueError(f"invalid edge {u}, {v}")
            edges.append((min(u, v), max(u, v)))
        index = frozenset(edges)
        if len(index) != len(edges):
            raise ValueError("duplicate undirected edge")
        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "edges", tuple(edges))
        object.__setattr__(self, "_edge_index", index)


@dataclass
class Markings:
    node_groups: dict[int, int] = field(default_factory=dict)
    edge_groups: dict[tuple[int, int], int] = field(default_factory=dict)


@dataclass
class Graph:
    positions: list[tuple[float, float]]
    edges: list[tuple[int, int]]
    node_marks: dict[int, int]
    edge_marks: dict[tuple[int, int], int]


def rows(path, keep_empty=False):
    path = Path(path)
    opener = bz2.open if path.suffix == ".bz2" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for number, raw in enumerate(stream, 1):
            line = raw.strip()
            if line.startswith(("%", "#")) or (not line and not keep_empty):
                continue
            yield f"{path}:{number}", line.split()


def integers(location, fields):
    try:
        return [int(field) for field in fields]
    except ValueError as exc:
        raise ValueError(f"{location}: expected integer fields") from exc


def topology(path):
    records = rows(path, keep_empty=True)
    loc, fields = next(records, (str(path), []))
    if len(fields) not in (2, 3):
        raise ValueError(f"{loc}: expected METIS header 'nodes edges [fmt]'")
    n, m, *fmt = integers(loc, fields)
    if n < 1 or m < 0 or any(fmt):
        raise ValueError(f"{loc}: expected a nonempty undirected unweighted graph")
    edges = set()
    pending = set()
    count = 0
    for count, (loc, fields) in enumerate(records, 1):
        if count > n:
            raise ValueError(f"{loc}: too many adjacency rows")
        for v in integers(loc, fields):
            if not 1 <= v <= n or count == v:
                raise ValueError(f"{loc}: invalid neighbor {v} of {count}")
            edge = min(v, count), max(v, count)
            if count < v and edge not in edges:
                edges.add(edge)
                pending.add(edge)
            elif count > v and edge in pending:
                pending.remove(edge)
            else:
                raise ValueError(f"{loc}: duplicate or asymmetric adjacency {count} {v}")
    if count != n or len(edges) != m or pending:
        raise ValueError(f"{path}: adjacency rows, edge count or reverse entries disagree with header")
    return n, edges


def coordinates(path, n, coord_format):
    if coord_format not in ("dimacs10-osm", "lonlat"):
        raise ValueError(f"Unknown coordinate format {coord_format!r}")
    result = []
    for loc, fields in rows(path):
        if len(fields) not in (2, 3):
            raise ValueError(f"{loc}: expected x y [z]")
        try:
            x, y, *_ = map(float, fields)
        except ValueError as exc:
            raise ValueError(f"{loc}: invalid coordinate") from exc
        if coord_format == "dimacs10-osm":
            x, y = x / 100000, y / 100000 - 1
        if not (-180 <= x <= 180 and -85.051129 <= y <= 85.051129):
            raise ValueError(f"{loc}: coordinate outside street map bounds")
        result.append((round(x, 10), round(y, 10)))
    if len(result) != n:
        raise ValueError(f"{path}: expected {n} coordinates, found {len(result)}")
    return result


def markings(path, n, base, edges=None):
    result = {}
    if path is None:
        return result
    for loc, fields in rows(path):
        if len(fields) != (2 if edges is None else 3):
            raise ValueError(f"{loc}: expected node group or edge endpoints and group")
        *ids, group = integers(loc, fields)
        ids = [i + 1 - base for i in ids]
        if group < 0 or any(i < 1 or i > n for i in ids):
            raise ValueError(f"{loc}: invalid group or node outside graph")
        key = ids[0] if edges is None else tuple(sorted(ids))
        if edges is not None and key not in edges:
            raise ValueError(f"{loc}: edge {key} is absent from graph")
        if key in result and result[key] != group:
            raise ValueError(f"{loc}: conflicting groups for {key}")
        result[key] = group
    return result


def read_metis(graph, coords, *, coord_format):
    n, edges = topology(graph)
    return Network(coordinates(coords, n, coord_format), sorted(edges))


def read_markings(network, *, edge_marks=None, node_marks=None, mark_id_base=1):
    if mark_id_base not in (0, 1):
        raise ValueError("mark_id_base must be 0 or 1")
    n = len(network.positions)
    return Markings(markings(node_marks, n, mark_id_base),
                    markings(edge_marks, n, mark_id_base, network._edge_index))


def load_graph(graph, coords, *, coord_format, **options):
    """Compatibility adapter for callers using a single marked graph."""
    network = read_metis(graph, coords, coord_format=coord_format)
    marks = read_markings(network, **options)
    return Graph(list(network.positions), list(network.edges), marks.node_groups, marks.edge_groups)
