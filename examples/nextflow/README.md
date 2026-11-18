# Nextflow integration

Install Streetviz where the task executes and include the adjacent STREETVIZ process in your workflow. Feed it tuples in this order.

```groovy
tuple(run_id, graph_path, coords_path, edge_marks_path, node_marks_path, mark_id_base, coord_format)
```

Use file objects with distinct basenames for the four path inputs and empty files for unused markings. Pass either 0 or 1 for the marking ID base and either 'lonlat' or 'dimacs10-osm' for the coordinate format. Join upstream files by run ID before calling the process. The output channel STREETVIZ.out.report carries the run ID and HTML file. Choose the publication path in the parent workflow.
