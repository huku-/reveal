# -*- coding: utf-8 -*-
"""This module implements the Markov lumping algorithm described in [01].

[01] `<https://dl.acm.org/citation.cfm?id=2175560>`_
"""

from reveal.graphs.graph import Graph

import collections
import logging

import numpy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["get_markov_lumping"]


def _split_blocks(
    graph: Graph,
    blocks: list[list[int]],
    splitter: list[int],
    splitters: list[list[int]],
) -> None:

    for i in range(len(blocks) - 1, -1, -1):

        #
        # Separate vertices of this block into groups with respect to the total
        # outgoing weight towards splitter vertices.
        #
        block = blocks[i]
        new_blocks = collections.defaultdict(list)
        for vertex in block:
            weight = 0
            for successor in graph.successors(vertex):
                if successor in splitter:
                    weight += graph.edges[vertex, successor]["weight"]
            new_blocks[weight].append(vertex)

        #
        # If the current block has been split in N new blocks, we only need to
        # split the remaining blocks using N-1 of them as new splitters.
        #
        if len(new_blocks) > 1:
            for j, (weight, new_block) in enumerate(new_blocks.items()):
                blocks.append(new_block)
                if j > 0:
                    splitters.append(new_block)
            del blocks[i]


def get_markov_lumping(graph: Graph) -> numpy.ndarray:
    """Run the Markov lumping algorithm described in [01]. Returns the square
    transition matrix of the lumped Markov system.

    Arguments:
        graph: The graph to run the algorithm on.

    Returns:
        The square transition matrix of the lumped Markov system.
    """
    logger = logging.getLogger()

    blocks = [list(graph.nodes)]

    splitters = list(blocks)
    while len(splitters):
        splitter = splitters.pop()
        _split_blocks(graph, blocks, splitter, splitters)

    vertex_to_block = {}
    for i, block in enumerate(blocks):
        block.sort()
        for vertex in block:
            vertex_to_block[vertex] = i
    blocks.sort()

    dim = len(blocks)
    Q = numpy.zeros((dim, dim))
    for i, block in enumerate(blocks):
        logger.debug("Block #%d:", i)
        for vertex in block:
            for successor in graph.successors(vertex):
                j = vertex_to_block[successor]
                weight = graph.edges[vertex, successor]["weight"]
                logger.debug("\t%f %#x (%d)", weight, successor, j)
                Q[i][j] = weight

    return Q
