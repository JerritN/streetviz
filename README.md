# Streetviz

Explore a geographic network and its node or edge groups in an interactive HTML report. Use the CLI for METIS files or pass coordinates and edges directly from Python. Requires Python 3.10+ and uses the standard library.

## Quickstart

From the project directory, run the included four-node example.

```sh
python -m streetviz --graph examples/quickstart/network.graph \
  --coords examples/quickstart/positions.txt --coord-format lonlat \
  --edge-marks examples/quickstart/edge-groups.txt \
  --node-marks examples/quickstart/node-groups.txt \
  --groups examples/quickstart/groups.json --basemap none --output network.html
```

Open `network.html` and click the red edge to inspect “Route A” (group 0). Toggle **Connect same-group nodes** to highlight the edge between survey sites 2 and 3. Both marking files and the group styles are optional. Install with `python -m pip install .` to use the `streetviz` command from other directories.

## Inputs

| File | Format |
| --- | --- |
| Graph | Undirected unweighted METIS. Header `n m [000]`, then one adjacency row per vertex, numbered from 1. Include both directions. A blank adjacency row represents an isolated vertex. |
| Coordinates | One `x y [z]` row per vertex in graph order. Select `--coord-format lonlat` for decimal longitude and latitude, or `dimacs10-osm` for scaled and shifted DIMACS street coordinates. Height is ignored. |
| Edge groups | One `u v group` per marked edge. Either endpoint order is valid. |
| Node groups | One `vertex group` per marked vertex. |
| Group styles | Optional UTF-8 JSON object keyed by group ID, e.g. `{"0":{"label":"Route A","color":"#a33243"}}`. Each entry can specify either field or both. |

Graph, coordinate and marking files can be plain text or bzip2 with a `.bz2` suffix. They support whole-line comments beginning with `%` or `#`. Group IDs are nonnegative integers. Missing assignments use the default drawing style. Group colors are deterministic unless overridden. Markings default to 1-based IDs, with `--mark-id-base 0` available for zero-based files. IDs refer to the original graph.

## Basemaps and viewing

Choose `--basemap none` for a plain background or `--basemap osm` (default) for OpenStreetMap. For your own XYZ raster provider, select `--basemap custom` and supply both `--tile-url 'https://your-host/{z}/{x}/{y}.png'` and `--attribution 'Provider credit'`. The custom source expects 256-pixel raster tiles. The URL is visible in the output HTML.

To enable tiles, serve the output directory with `python -m http.server 8000 --bind 127.0.0.1` and open [the report](http://127.0.0.1:8000/network.html). Opening a local HTML file directly shows a plain background. All modes use WebGL and fetch the pinned MapLibre JS/CSS from unpkg. Graph data travels inside the HTML. Marked nodes are visible at every zoom and unmarked nodes appear from zoom level 14. Embed the report on another page with `<iframe src="network.html" title="Network map"></iframe>`.

For large graphs the overview samples features in the current viewport and reserves a separate budget for marked edges. Zoom in until the sampling notice disappears to inspect all visible features. The report still contains the full graph. After updating Streetviz, regenerate older HTML reports to use the new viewer.

## Architecture and Python API

`Network` stores immutable positions and undirected edges. `read_metis` constructs it from files and `read_markings` imports optional sparse assignments separately. The CLI calls these adapters and passes their results to `write_html`, which embeds them in the packaged viewer. MapLibre expands the edges into line segments in the browser. Generation and viewing both hold the graph in memory.

```python
from streetviz import Network, Markings, write_html

network = Network(positions=[(8.40, 49.01), (8.41, 49.02)], edges=[(1, 2)])
for name, marks in {
    "route": Markings(edge_groups={(1, 2): 0}),
    "sites": Markings(node_groups={2: 3}),
}.items():
    write_html(network, f"{name}.html", markings=marks, basemap="none")
```

To reuse a network from disk, replace the constructor with `read_metis(graph_path, coords_path, coord_format="lonlat")`. An existing `load_graph(...)` caller can continue using that convenience function by specifying `coord_format`.

## Examples and tests

- [Luxembourg street network](examples/luxembourg/README.md)
- [Nextflow integration](examples/nextflow/README.md)
- Run `python -m unittest discover -s tests` from the project directory.
