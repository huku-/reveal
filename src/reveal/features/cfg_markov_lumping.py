# -*- coding: utf-8 -*-

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["CFGMarkovLumper"]


from relib.model import Function, Program

from networkx import Graph
from numpy import ndarray

from reveal.algorithms import markov_lumping

import numpy


class CFGMarkovLumper(object):
    """Markov lumping for function CFGs."""

    def __init__(self, program: Program, function: Function) -> None:
        super().__init__()
        self._program = program
        self._function = function

    def _get_stationary_probabilities(self, matrix: ndarray) -> ndarray:
        """Compute the stationary probability vector of a stochastic matrix.

        Args:
            matrix: A stochastic matrix.

        Returns:
            Vector of stationary probabilities.
        """
        n = matrix.shape[0]
        a = matrix.T - numpy.eye(n)
        a[-1] = numpy.ones(n)
        b = numpy.zeros(n)
        b[-1] = 1
        return numpy.linalg.lstsq(a, b)[0].round(6)

    def _assign_edge_weights(self, cfg: Graph) -> None:
        """Assign weights to the edges of a CFG.

        The weight assignment scheme implemented here is based on the maximum
        distance of basic-blocks from function exits and traps (see the vertex
        classification algorithm for more information on these terms).

        More specifically, for each outgoing edge from basic-block A to B and C,
        edge A-B is assigned a higher weight than A-C if the path leading to B
        is more distant from a function exit or trap than this leading to C (i.e.,
        the path to B leads to the main body of the function and thus is more
        highly likely to be executed).

        Args:
            cfg: The CFG to assign weights to.
        """
        exit_bb_eas = [
            bb_ea
            for bb_ea in cfg
            if cfg.nodes[bb_ea].get("trap") or cfg.nodes[bb_ea].get("exit")
        ]
        if exit_bb_eas:
            max_distances = {}
            for bb_ea in cfg:
                max_distance = 0
                if bb_ea not in exit_bb_eas:
                    max_distance = max(
                        [
                            abs(cfg.nodes[bb_ea]["depth"] - cfg.nodes[ea]["depth"])
                            for ea in exit_bb_eas
                        ]
                    )
                max_distance += 1
                max_distances[bb_ea] = max_distance
        else:
            max_distances = {bb_ea: 1 for bb_ea in cfg}

        for bb_ea in cfg:
            if cfg.out_degree(bb_ea):
                succ_bb_eas = list(cfg.successors(bb_ea))
                denom = sum([max_distances[succ_bb_ea] for succ_bb_ea in succ_bb_eas])
                for succ_bb_ea in succ_bb_eas:
                    cfg.edges[(bb_ea, succ_bb_ea)]["weight"] = (
                        max_distances[succ_bb_ea] / denom if denom else 0
                    )

    def lump_cfg(self) -> ndarray:
        """Assign edge weights to a function's CFG, compute the lumped Markovian
        stochastic matrix and return its stationary probability vector.

        Only the 64 largest elements of the probability vector are kept. The
        vector is also sorted, which results in information loss, but it's
        better for our purposes.

        Returns:
            Stationary probability vector.
        """
        cfg = self._function.get_cfg()
        self._assign_edge_weights(cfg)
        lumped_matrix = markov_lumping.get_markov_lumping(cfg)
        p = self._get_stationary_probabilities(lumped_matrix)
        p[::-1].sort()
        if p.shape[0] < 64:
            p = numpy.append(p, numpy.zeros(64 - p.shape[0]))
        else:
            p = p[:64]
        return p
