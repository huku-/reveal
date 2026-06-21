# -*- coding: utf-8 -*-
"""This module implements the edge classification algorithm described in [01].

[01] `<https://census-labs.com/media/efficient-features-bindiff.pdf>`_
"""

from reveal.graphs.graph import Graph

from reveal.algorithms import depth_assigner

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["classify_edges"]


def classify_edges(graph: Graph) -> list[int]:
    """Implements the edge classification algorithm described in [01].

    Arguments:
        graph: The graph to run the algorithm on.

    Returns:
        List of integers, with each integer giving the number of edges in a
        specific edge class (see [01], Section IV (A), p.3-5).
    """

    depth_assigner.assign_depths(graph)

    edge_types = [
        0,  # Tree edges
        0,  # Forward edges
        0,  # Back edges
        0,  # Cross-link edges
    ]

    for edge in graph.edges():
        tail, head = edge
        tail_attributes = graph.nodes[tail]
        tail_depth = tail_attributes["depth"]
        head_attributes = graph.nodes[head]
        head_depth = head_attributes["depth"]
        if head_depth > tail_depth + 1:
            edge_types[1] += 1
        elif head_depth > tail_depth:
            edge_types[0] += 1
        elif head_depth < tail_depth:
            if tail_attributes.get("tail", False) and head_attributes.get(
                "head", False
            ):
                edge_types[2] += 1
            else:
                edge_types[3] += 1

    return edge_types
