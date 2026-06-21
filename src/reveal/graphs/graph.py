# -*- coding: utf-8 -*-
"""Base definitions for graphs used by REveal.

Our implementation is based on NetworkX, but uses its facilities to provide
ordered views over the graphs' vertices and adjacency lists.
"""

from typing import Any
from collections.abc import Iterator

import bisect

import networkx


__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["Graph"]


class _OrderedDict(object):
    """A class that behaves like a built-in dictionary, but maintains the keys
    and values in lists, sorted by key value. It is much slower than a built-in
    dictionary, but an attempt is made to save some time by using binary search.
    """

    def __init__(self) -> None:
        super().__init__()
        self._keys: list[int] = []
        self._values: list[Any] = []

    def __setitem__(self, key: int, value: Any) -> None:
        keys = self._keys
        values = self._values
        i = bisect.bisect_left(keys, key)
        if i != len(keys) and keys[i] == key:
            values[i] = value
        else:
            keys.insert(i, key)
            values.insert(i, value)

    def __getitem__(self, key: int) -> Any:
        keys = self._keys
        i = bisect.bisect_left(keys, key)
        if i != len(keys) and keys[i] == key:
            return self._values[i]
        raise KeyError(f"{key}")

    def __delitem__(self, key: int) -> None:
        keys = self._keys
        i = bisect.bisect_left(keys, key)
        if i == len(keys) or keys[i] != key:
            raise KeyError(f"{key}")
        del self._values[i]
        del self._keys[i]

    def __contains__(self, key: int) -> bool:
        keys = self._keys
        i = bisect.bisect_left(keys, key)
        return i != len(keys) and keys[i] == key

    def __iter__(self) -> Iterator[int]:
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)

    def get(self, key: int, default: Any = None) -> Any:
        try:
            value = self[key]
        except KeyError:
            value = default
        return value

    def keys(self) -> Iterator[int]:
        return iter(self._keys)

    def values(self) -> Iterator[Any]:
        return iter(self._values)

    def items(self) -> Iterator[tuple[int, Any]]:
        for i, key in enumerate(self._keys):
            yield key, self._values[i]

    def clear(self) -> None:
        self._keys = []
        self._values = []


class Graph(networkx.DiGraph):
    """Represents a directed graph whose vertices and adjacency lists are
    ordered.

    Since we use this class to represent *Function Call Graphs* (FCGs), *Control
    Flow Graphs* (CFGs) and others, vertices are, in fact, integers holding
    program addresses. Consequently, with our design, vertices in the graphs and
    their successors/predecessors are always processed in order of increasing
    address.

    >>> graph = Graph()
    >>> graph.add_node("B")
    >>> graph.add_node("A")
    >>> graph.add_node("C")
    >>> print(list(graph.nodes))
    ['A', 'B', 'C']
    >>> graph.add_edge("A", "C")
    >>> graph.add_edge("A", "B")
    >>> print(list(graph.successors("A")))
    ['B', 'C']

    Notice how, in the above examples, the view over the graph's vertices, as
    well as the successors of node *A*, are both ordered lexicographically.
    """

    node_dict_factory = _OrderedDict
    adjlist_inner_dict_factory = _OrderedDict
