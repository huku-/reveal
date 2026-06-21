# -*- coding: utf-8 -*-
"""Algorithms for computing graph signatures."""

from reveal.graphs.graph import Graph

from reveal.algorithms import searching

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["get_bit_signature", "get_string_signature"]


class _BitSignature(searching.DFS):
    """Implements a simple DFS-based algorithm that computes a bit signature out
    of a given graph. A *1*-bit is appended in the bit signature whenever a
    vertex is entered for the first time and a *0*-bit when leaving the vertex.
    The usual vertex ordering is followed.
    """

    def __init__(self, graph: Graph) -> None:
        super().__init__(graph)
        self._signature = 0

    def on_enter(self, tail: int | None, head: int) -> None:
        super().on_enter(tail, head)
        self._signature <<= 1
        self._signature |= 1

    def on_leave(self, tail: int | None, head: int) -> None:
        super().on_leave(tail, head)
        self._signature <<= 1

    def search(self) -> int:
        super().search()
        return self._signature


class _StringSignature(searching.DFS):
    """Implements a simple DFS-based algorithm that computes a string signature
    out of a given graph. The signature is composed of the following symbols,
    ordered based on the usual vertex ordering rules:

    * **S** - Indicates a DFS entry point vertex.
    * **E** - Indicates a vertex is entered for the first time.
    * **B** - Indicates a back-edge probe.
    * **F** - Indicates a forward-edge probe.
    * **L** - Indicates a departure from a vertex.
    """

    def __init__(self, graph: Graph) -> None:
        super().__init__(graph)
        self._signature = 0

    def _append(self, x: int) -> None:
        self._signature <<= 3
        self._signature |= x & 0b111

    def on_enter(self, tail: int | None, head: int) -> None:
        super().on_enter(tail, head)
        if tail is None:
            self._append(0b000)  # "S"
        else:
            self._append(0b001)  # "E"

    def on_probe(self, tail: int, head: int, direction: int) -> None:
        super().on_probe(tail, head, direction)
        if direction < 0:
            self._append(0b010)  # "B"
        elif direction > 0:
            self._append(0b011)  # "F"
        else:
            self._append(0b100)  # "P"

    def on_leave(self, tail: int | None, head: int) -> None:
        super().on_leave(tail, head)
        self._append(0b101)  # "L"

    def search(self) -> int:
        super().search()
        return self._signature


def get_bit_signature(graph: Graph) -> int:
    """Run the bit signature algorithm on the given graph.

        graph: The graph to run the algorithm on.

    Returns:
        The graph's bit signature.
    """
    return _BitSignature(graph).search()


def get_string_signature(graph: Graph) -> int:
    """Run the string signature algorithm on the given graph.

    Arguments:
        graph: The graph to run the algorithm on.

    Returns:
        The graph's string signature
    """
    return _StringSignature(graph).search()
