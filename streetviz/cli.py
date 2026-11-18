import argparse
import json
from pathlib import Path

from . import read_metis, read_markings, write_html


def main():
    parser = argparse.ArgumentParser(description="Render a marked METIS street graph as HTML.")
    for name in ("graph", "coords", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--edge-marks", type=Path, help="rows of u v group")
    parser.add_argument("--node-marks", type=Path, help="rows of node group")
    parser.add_argument("--mark-id-base", type=int, choices=[0, 1], default=1)
    parser.add_argument("--coord-format", choices=["dimacs10-osm", "lonlat"], required=True)
    parser.add_argument("--basemap", choices=["osm", "none", "custom"], default="osm")
    parser.add_argument("--groups", type=Path, help="optional JSON group labels and colors")
    parser.add_argument("--tile-url", help="custom HTTPS raster XYZ tile template")
    parser.add_argument("--attribution", help="custom tile provider attribution text")
    opts = vars(parser.parse_args())
    output = opts.pop("output")
    try:
        if any(isinstance(v, Path) and v.resolve() == output.resolve() for v in opts.values()):
            raise ValueError("output path must differ from inputs")
        network = read_metis(opts.pop("graph"), opts.pop("coords"), coord_format=opts.pop("coord_format"))
        group_file = opts.pop("groups")
        groups = json.loads(group_file.read_text(encoding="utf-8")) if group_file else {}
        basemap = opts.pop("basemap")
        tile_url, attribution = opts.pop("tile_url"), opts.pop("attribution")
        write_html(network, output, markings=read_markings(network, **opts), basemap=basemap, groups=groups,
                   tile_url=tile_url, attribution=attribution)
    except (ValueError, OSError, EOFError) as exc:
        parser.exit(2, f"streetviz: {exc}\n")
    print(f"{output} ({len(network.positions):,} nodes, {len(network.edges):,} edges)")
