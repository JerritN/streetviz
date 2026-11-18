# Luxembourg street network

The included `luxembourg.html` shows the DIMACS 10 network and two example assignments. Edge 1–1113 belongs to group 0 and node 1113 belongs to group 7. To regenerate it, run the following from the project root with your two original compressed files in that directory.

```sh
python -m streetviz --graph luxembourg.osm.graph.bz2 --coords luxembourg.osm.xyz.bz2 \
  --coord-format dimacs10-osm --edge-marks examples/luxembourg/edge_marks.txt \
  --node-marks examples/luxembourg/node_marks.txt --output examples/luxembourg/luxembourg.html
python -m http.server 8000 --bind 127.0.0.1
```

[Open the served example](http://127.0.0.1:8000/examples/luxembourg/luxembourg.html). The decoder uses longitude x/100000 and latitude y/100000 − 1. Some roads in the 2010 graph differ from current basemap tiles. [Dataset](https://sites.cc.gatech.edu/dimacs10/archive/streets.shtml) · [Coordinate convention](https://networks.skewed.de/net/dimacs10_roads)
