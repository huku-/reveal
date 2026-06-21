# -*- coding: utf-8 -*-
"""Vertex classification algorithm.

This module implements the vertex classification algorithm described in [01].

[01] `<https://ieeexplore.ieee.org/document/8330221>`_
"""

from reveal.graphs.graph import Graph

from reveal.algorithms import searching

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["classify_vertices"]


class _VertexClassifier(searching.DFS):
    """This class implements a DFS-based algorithm for computing the vertex
    classification described in [01].
    """

    def on_enter(self, tail: int | None, head: int) -> None:
        if tail is None:
            self._logger.debug("[ENTRY] %s", head)
            self._graph.nodes[head]["entry"] = True

    def on_probe(self, tail: int, head: int, direction: int) -> None:
        graph = self._graph
        if tail == head:
            self._logger.debug("[LOOP] %s", tail)
            graph.nodes[tail]["loop"] = True
        elif direction < 0:
            self._logger.debug("[CYCLE] %s ~> %s", tail, head)
            graph.nodes[head]["head"] = True
            graph.nodes[tail]["tail"] = True

    def on_leave(self, tail: int | None, head: int) -> None:
        graph = self._graph
        out_degree = graph.out_degree(head)
        if out_degree == 0:
            self._logger.debug("[EXIT] %s", head)
            graph.nodes[head]["exit"] = True
        elif out_degree == 1 and head in graph.successors(head):
            self._logger.debug("[TRAP] %s", head)
            graph.nodes[head]["trap"] = True

    def search(self) -> list[int]:
        super().search()

        vertex_types = [
            0,  # All vertices
            0,  # Entry points
            0,  # Exit points
            0,  # Traps
            0,  # Self-loops
            0,  # Loop heads
            0,  # Loop tails
        ]

        graph = self._graph
        for vertex in graph:
            attributes = graph.nodes[vertex]
            vertex_types[0] += 1
            if attributes.get("entry", False):
                vertex_types[1] += 1
            if attributes.get("exit", False):
                vertex_types[2] += 1
            if attributes.get("trap", False):
                vertex_types[3] += 1
            if attributes.get("loop", False):
                vertex_types[4] += 1
            if attributes.get("head", False):
                vertex_types[5] += 1
            if attributes.get("tail", False):
                vertex_types[6] += 1

        return vertex_types


def classify_vertices(graph: Graph) -> list[int]:
    """Runs the vertex classification algorithm described in [01].

    Arguments:
        graph: The graph to run the algorithm on.

    Returns:
        List of integers, with each integer giving the number of vertices in a
        specific vertex class (see [01], Section IV (A), p.3-5).
    """
    return _VertexClassifier(graph).search()
