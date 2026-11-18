process STREETVIZ {
    tag "${run_id}"

    input:
    tuple val(run_id), path(graph), path(coords), path(edge_marks), path(node_marks), val(mark_id_base), val(coord_format)

    output:
    tuple val(run_id), path('streetgraph.html'), emit: report

    script:
    """
    streetviz --graph "${graph}" --coords "${coords}" \
        --edge-marks "${edge_marks}" --node-marks "${node_marks}" \
        --coord-format "${coord_format}" --mark-id-base ${mark_id_base} --output streetgraph.html
    """
}
