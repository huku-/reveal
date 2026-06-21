# -*- coding: utf-8 -*-
"""Algorithm for assigning depths to graph vertices.

Implements a DFS-based algorithm that assigns depths to the vertices of the
given graph. After the DFS phase, the algorithm performs a fix-point loop that
propagates and modifies the initially assigned depths, so that graph loops are
handled appropriately (i.e., so that the depth of the head vertex of a back-edge
is not higher than the depth of the tail vertex).

The depth of each vertex is assigned in a vertex attribute named *depth*.
"""

from reveal.graphs.graph import Graph

import logging

from reveal.algorithms import searching

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["assign_depths"]


class _DepthAssigner(searching.DFS):
    """Implements the depth assignment algorithm."""

    def __init__(self, graph: Graph) -> None:
        super().__init__(graph)
        self._back_edges: set[tuple[int, int]] = set()
        self._depth = 0

    def on_enter(self, tail: int | None, head: int) -> None:
        super().on_enter(tail, head)
        self._graph.nodes[head]["depth"] = self._depth
        self._depth += 1

    def on_probe(self, tail: int, head: int, direction: int) -> None:
        super().on_probe(tail, head, direction)
        if direction < 0:
            self._back_edges.add((tail, head))

    def on_leave(self, tail: int | None, head: int) -> None:
        super().on_leave(tail, head)
        self._depth -= 1

    def _propagate_vertex_round(self, vertex: int) -> bool:
        graph = self._graph
        depth = graph.nodes[vertex]["depth"]
        change = False
        for successor in graph.successors(vertex):
            if vertex != successor:
                successor_depth = graph.nodes[successor]["depth"]
                if (
                    depth >= successor_depth
                    and (vertex, successor) not in self._back_edges
                ):
                    graph.nodes[successor]["depth"] = depth + 1
                    change = True
        return change

    def _propagate_round(self) -> bool:
        change = False
        for vertex in self._graph:
            change |= self._propagate_vertex_round(vertex)
        return change

    def search(self) -> None:
        super().search()

        self._logger.debug("Starting depth propagation")
        change = self._propagate_round()
        while change:
            change = self._propagate_round()

        if self._logger.isEnabledFor(logging.DEBUG):
            for vertex in self._graph:
                depth = self._graph.nodes[vertex]["depth"]
                self._logger.debug("[DEPTH] %s %s", str(vertex), depth)


def assign_depths(graph: Graph) -> None:
    """Runs the depth assignment algorithm on a graph.

    Arguments:
        graph: The graph to run the algorithm on.
    """

    assert len(
        [v for v in graph if graph.nodes[v].get("entry")]
    ), "No entry nodes found. Vertex classifier needs to run first."

    _DepthAssigner(graph).search()
