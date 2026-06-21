# -*- coding: utf-8 -*-
"""Algorithm for assigning weights (probabilities) to graph edges.

Each vertex is, first, assigned a maximum distance from an exit vertex. Then, a
probability is computed for each edge, based on the distance of the edge's head
from an exit vertex; the higher the distance, the higher the probability.

The rationale behind this probability assignment scheme is that, the higher the
distance of a vertex from an exit, the higher the probability that following the
corresponding edge will eventually lead to the most computationally intensive
part of a function.
"""

from reveal.graphs.graph import Graph


def assign_edge_weights(graph: Graph) -> None:
    """Runs the edge weight assigner algorithm on a graph.

    Arguments:
        graph: The graph to run the algorithm on.
    """

    assert len(
        [v for v in graph if graph.nodes[v].get("entry")]
    ), "No entry nodes found. Vertex classifier needs to run first."

    assert all(
        ["depth" in graph.nodes[v] for v in graph]
    ), "No vertex depths assigned. Depth assigner needs to run first."

    exit_vertices = [
        v for v in graph if graph.nodes[v].get("trap") or graph.nodes[v].get("exit")
    ]
    assert exit_vertices, "No exits/traps found in graph"

    distances = {}
    for v in graph:
        distance = 0
        if v not in exit_vertices:
            depth = graph.nodes[v]["depth"]
            distance = max(
                [abs(depth - graph.nodes[ev]["depth"]) for ev in exit_vertices]
            )
        distances[v] = distance

    for v in graph:
        if graph.out_degree(v):
            successors = list(graph.successors(v))
            denom = sum([distances[u] for u in successors])
            for u in successors:
                graph.edges[(v, u)]["weight"] = distances[u] / denom
