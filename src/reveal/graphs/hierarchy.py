# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import ClassVar
from pathlib import Path
from networkx import DiGraph

from reveal.types import Comparable

import dataclasses
import enum
import functools
import warnings

import networkx

try:
    import pygraphviz
except ImportError:
    warnings.warn("Graph visualization disabled because pygraphviz is not installed")


__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["ClusterType", "Cluster", "Hierarchy"]


@enum.unique
class ClusterType(enum.IntEnum):
    """Type of cluster in a meta-graph."""

    PARALLEL = 0
    SERIES = 1
    PRIME = 2


@functools.total_ordering
class Cluster(Comparable):
    """Represents internal non-leaf vertices of meta-graphs. Effectively, these
    represent clusters in a hierarchical clustering of a graph (i.e., communities
    in a community graph, modules in modular decomposition tree etc.). We define
    a separate class for these vertices, which effectively creates a separate
    namespace, that avoids conflicts with vertices in the original graph.
    """

    _num_clusters: ClassVar[int] = 0

    def __init__(self, cluster_type: ClusterType) -> None:
        super().__init__()
        self._cluster_id = Cluster._num_clusters
        self._cluster_type = cluster_type
        Cluster._num_clusters += 1

    def __eq__(self, other: Cluster) -> bool:
        return isinstance(other, Cluster) and self.cluster_id == other.cluster_id

    def __lt__(self, other: Cluster) -> bool:
        return isinstance(other, Cluster) and self.cluster_id < other.cluster_id

    def __hash__(self) -> int:
        return hash(self._cluster_id)

    def __str__(self) -> str:
        return f"Cluster[{self.cluster_id}, {self.cluster_type.name}]"

    @property
    def cluster_id(self) -> int:
        return self._cluster_id

    @property
    def cluster_type(self) -> ClusterType:
        return self._cluster_type


@dataclasses.dataclass
class Hierarchy(object):
    """A class that represents a hierarchical clustering of a graph.

    The clustering is represented as a dendrogram of arbitrary depth, let's say
    *N*, where levels are numbered from *0* to *N-1*. Leaf vertices, at level
    *N-1* are vertices of the original graph. Each intermediate vertex represents
    a cluster consisting of its children, which might be either original graph
    vertices (for intermediate vertices at level *N-2*), or other clusters (for
    intermediate vertices at levels *0* to *N-3*). For each intermediate vertex,
    enumerating the leaves of the sub-tree rooted at that vertex, yields the
    original graph vertices in the corresponding cluster. The dendrogram always
    has a single root vertex, representing all vertices in the original graph
    (i.e., a single cluster).

    Arguments:
        dendrogram: The clustering's dendrogram.
        meta_graphs: List of meta-graphs, one for each level of the clustering.
        root: Dendrogram's root vertex.
        num_levels: Number of levels in this clustering.
    """

    dendrogram: DiGraph
    meta_graphs: list[DiGraph]
    root: Cluster
    num_levels: int

    def __post_init__(self) -> None:
        assert self.num_levels >= 1, f"Nonsensical number of levels {self.num_levels}"
        assert networkx.is_arborescence(
            self.dendrogram
        ), "Dendrogram is not an arborescence"

    def clusters(self, level: int) -> list[Cluster]:
        """Return the clusters at the given level of the dendrogram.

        Given a level index, it performs a BFS traversal of the dendrogram and
        returns the clusters at the specified depth.

        Arguments:
            level: Level index.

        Returns:
            List of clusters at the given level.
        """
        if level < -1 or level >= self.num_levels:
            raise IndexError(f"Invalid level {level}")
        return list(networkx.descendants_at_distance(self.dendrogram, self.root, level))

    def cluster_members(self, cluster: Cluster) -> list[int]:
        """Return the members of a cluster.

        Given a cluster in the dendrogram, it performs a DFS traversal of the
        sub-tree rooted at that cluster and returns all the leaves.

        Arguments:
            cluster: Cluster whose members to return.

        Returns:
            List of members in given cluster.
        """
        return [
            v
            for v in networkx.dfs_preorder_nodes(self.dendrogram, source=cluster)
            if isinstance(v, int)
        ]

    def draw(self, path: str | Path, labels: dict[int, str] | None = None) -> None:
        """Draw the hierarchy's dendrogram in Graphviz dot format.

        Arguments:
            path: Path to file to draw the graph to.
            labels: A dictionary mapping original graph vertices (i.e., leaf
                vertices in the dendrogram) to human-readable labels.
        """
        agraph = pygraphviz.AGraph(directed=True)
        agraph.node_attr.update(shape="rect")

        clusters = self.clusters(self.num_levels - 2)
        for c in clusters:
            successors = [
                labels[s] if labels else f"{s}"
                for s in self.dendrogram.successors(c)
            ]
            agraph.add_node(f"{c}_children", label="\n".join(successors))
            agraph.add_edge(c, f"{c}_children")

        for v in self.dendrogram:
            if v not in clusters:
                for s in self.dendrogram.successors(v):
                    agraph.add_edge(v, s)

        agraph.write(path)
