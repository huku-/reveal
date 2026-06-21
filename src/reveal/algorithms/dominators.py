# -*- coding: utf-8 -*-
"""Algorithms for computing dominator sets.

Methods in this module can be used for computing the immediate dominators and
the immediate dominator tree of a given graph. The algorithms implemented here
make use of the corresponding NetworkX code, with the exception that special
care is taken for graphs with multiple entry points.
"""

from reveal.graphs.graph import Graph

import networkx

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["get_immediate_dominators", "get_immediate_dominator_tree"]


#
# In order to support graphs with multiple entry points, we create a sentinel
# vertex that has an outgoing edge for each entry point. Since we deal with
# graphs of program addresses, we set the sentinel vertex to "-1" so that graph
# traversal algorithms believe the sentinel is always at the lowest address.
#
_SENTINEL = -1


def get_immediate_dominators(graph: Graph) -> dict[int, int]:
    """Get the immediate dominator of each vertex in the given graph.

    Arguments:
        graph: The graph whose immediate dominators to compute.

    Returns:
        A dictionary mapping each vertex to its immediate dominator.
    """

    graph.add_node(_SENTINEL)
    for vertex in graph:
        if graph.nodes[vertex].get("entry", False):
            graph.add_edge(_SENTINEL, vertex)

    assert (
        graph.out_degree(_SENTINEL) > 0
    ), "No entry nodes found. Vertex classifier needs to run first."

    immediate_dominators = networkx.immediate_dominators(graph, _SENTINEL)
    graph.remove_node(_SENTINEL)

    return immediate_dominators


def get_immediate_dominator_tree(graph: Graph) -> Graph:
    """Build the graph's immediate dominator tree. Each vertex in the tree
    dominates its children in the original graph.

    Arguments:
        graph: The graph whose immediate dominator tree to build.

    Returns:
        The graph's immediate dominator tree.
    """

    imm_doms = get_immediate_dominators(graph)
    imm_dom_tree = type(graph)()
    for vertex in imm_doms:
        imm_dom_tree.add_node(vertex)

    for vertex, imm_dom in imm_doms.items():
        if imm_dom != vertex:
            imm_dom_tree.add_edge(imm_dom, vertex)

    return imm_dom_tree
