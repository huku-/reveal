# -*- coding: utf-8 -*-
"""Consensus clustering using Louvain community detection algorithm."""

from reveal.graphs.graph import Graph
from reveal.graphs.hierarchy import ClusterType, Cluster, Hierarchy

from numpy.random import RandomState

import itertools
import logging

import networkx

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["consensus"]


def consensus(
    graph: Graph,
    weight: str = "weight",
    resolution: float = 1.0,
    num_iters: int = 100,
    prob: float = 0.85,
    random_state: RandomState | None = None,
) -> Hierarchy:
    """Perform consensus clustering using the Louvain community detection algorithm.

    Arguments:
        graph: Input graph to perform community detection on.
        weight: Attribute name that holds vertex and edge weights.
        resolution: Louvain algorithm resolution parameter.
        num_iters: Number of iterations for reaching consensus in each level of
            the hierarchy.
        prob: Probability for assigning vertices in the same community in the
            consensus graph.
        random_state: Random state to use for vertex shuffling.

    Returns:
        The resulting clustering hierarchy.
    """
    logger = logging.getLogger()

    dendrogram = Graph()
    root = Cluster(ClusterType.PRIME)
    dendrogram.add_node(root)

    num_levels = 2
    meta_graphs = [graph]
    prev_modularity = 0

    while True:
        consensus_graph = networkx.Graph()
        consensus_graph.add_nodes_from(graph.nodes)
        for _ in range(num_iters):
            for comm in networkx.community.louvain_communities(
                graph, weight=weight, resolution=resolution, seed=random_state
            ):
                for u, v in itertools.combinations(comm, 2):
                    if consensus_graph.has_edge(u, v):
                        consensus_graph.edges[u, v]["weight"] += 1
                    else:
                        consensus_graph.add_edge(u, v, weight=1)

        for e in consensus_graph.edges:
            consensus_graph.edges[e]["weight"] /= num_iters

        edges = []
        for e in consensus_graph.edges:
            if consensus_graph.edges[e]["weight"] < prob:
                edges.append(e)
        consensus_graph.remove_edges_from(edges)

        components = list(networkx.connected_components(consensus_graph))
        modularity = networkx.community.modularity(graph, components)
        if modularity <= prev_modularity:
            break

        num_levels += 1
        logger.info(
            "Number of levels %d, communities %d, modularity %f",
            num_levels,
            len(components),
            modularity,
        )

        membership = {}
        for component in components:
            cluster = Cluster(ClusterType.PRIME)
            dendrogram.add_node(cluster)
            for u in component:
                membership[u] = cluster
                dendrogram.add_edge(cluster, u)

        meta_graph = Graph()
        meta_graph.add_nodes_from(membership.values())
        for component in components:
            for u in component:
                for s in graph.neighbors(u):
                    e = membership[u], membership[s]
                    if meta_graph.has_edge(*e):
                        meta_graph.edges[e]["weight"] += 1
                    else:
                        meta_graph.add_edge(*e, weight=1)

        meta_graphs.insert(0, meta_graph)
        prev_modularity = modularity
        graph = meta_graph

    meta_graph = Graph()
    meta_graph.add_node(root)
    meta_graphs.insert(0, meta_graph)

    for cluster in graph.nodes:
        dendrogram.add_edge(root, cluster)

    return Hierarchy(dendrogram, meta_graphs, root, num_levels)
