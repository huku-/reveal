# -*- coding: utf-8 -*-
"""A more powerful DFS implementation."""

from typing import Any

from reveal.graphs.graph import Graph

import logging

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["DFS"]


class DFS(object):
    """A more powerful DFS implementation.

    Searching is performed using *open* and *closed* sets of vertices [01]. A
    vertex is added in the *closed* set if the algorithm has finished processing
    it and won't visit it again in the future (e.g., the whole sub-tree rooted
    at the vertex in question has been visited). Vertices in the *open* set have
    been visited, but the algorithm has not finished processing them yet (e.g.,
    the vertex is still in the stack).

    Descendants may implement the `on_enter()`, `on_probe()` and `on_leave()`
    callbacks, to hook into the graph searching process. This allows for greater
    flexibility when developing graph algorithms, compared to the NetworkX
    approach, which just returns the search order of the graph's vertices or
    edges.

    [01] `<https://stackoverflow.com/questions/27063959>`_
    """

    def __init__(self, graph: Graph) -> None:
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._graph = graph

    def on_enter(self, tail: int | None, head: int) -> None:
        self._logger.debug("[ENTER] %s ~> %s", tail, head)

    def on_probe(self, tail: int, head: int, direction: int) -> None:
        self._logger.debug("[PROBE] %s ~> %s (%d)", tail, head, direction)

    def on_leave(self, tail: int | None, head: int) -> None:
        self._logger.debug("[LEAVE] %s <~ %s", tail, head)

    def _get_start_vertex(self, closed_set: set) -> int | None:
        graph = self._graph
        vertices = sorted(set(graph.nodes) - closed_set)
        if vertices:
            for vertex in vertices:
                if graph.in_degree(vertex) == 0:
                    return vertex
            return vertices[0]

    def search(self) -> Any:
        """Start the DFS."""

        graph = self._graph
        closed_set = set()
        open_set = set()

        vertex = self._get_start_vertex(closed_set)
        while vertex is not None:
            self.on_enter(None, vertex)
            stack = [(None, vertex, graph.successors(vertex))]
            closed_set.add(vertex)
            open_set.add(vertex)
            while len(stack):
                predecessor, vertex, successors = stack[-1]
                try:
                    successor = next(successors)
                    if successor not in closed_set:
                        self.on_enter(vertex, successor)
                        stack.append((vertex, successor, graph.successors(successor)))
                        closed_set.add(successor)
                        open_set.add(successor)
                    elif successor in open_set:
                        self.on_probe(vertex, successor, -1)
                    else:
                        self.on_probe(vertex, successor, 1)
                except StopIteration:
                    stack.pop()
                    self.on_leave(predecessor, vertex)
                    open_set.discard(vertex)
            vertex = self._get_start_vertex(closed_set)
