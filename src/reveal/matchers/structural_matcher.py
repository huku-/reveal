# -*- coding: utf-8 -*-
"""Structural matcher.

This module implements the *structural matcher*, a matcher that, given a set of
initial matches, expands the isomorphism by looking for matching successors and
predecessors of already matched elements. Structural matching has been known in
the reverse engineering community for ages, with [01] being one of the earliest
records of this technique.

[01] `<https://static.googleusercontent.com/media/www.zynamics.com/en/downloads/bindiffsstic05-1.pdf>`_
"""

from reveal.datasets.dataset import Dataset

from reveal.matchers import matcher, singleton_matcher

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["ExactStructuralMatcher", "InexactStructuralMatcher"]


class _StructuralMatcher(matcher.Matcher):

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        matches = self._matches
        lhs_graph = lhs.graph
        rhs_graph = rhs.graph

        prev_num_matches = num_matches = 0
        while True:
            out_matches = sorted(
                [
                    (lhs_graph.out_degree(address1), address1, address2)
                    for address1, _, address2, _, _ in matches
                    if lhs_graph.out_degree(address1) == rhs_graph.out_degree(address2)
                ]
            )

            in_matches = sorted(
                [
                    (lhs_graph.in_degree(address1), address1, address2)
                    for address1, _, address2, _, _ in matches
                    if lhs_graph.in_degree(address1) == rhs_graph.in_degree(address2)
                ]
            )

            while out_matches or in_matches:
                if out_matches:
                    _, address1, address2 = out_matches.pop(0)
                    nlhs = lhs.get_successor_dataset(address1)
                    nrhs = rhs.get_successor_dataset(address2)
                    if nlhs and nrhs:
                        num_matches += super().match(nlhs, nrhs)
                if in_matches:
                    _, address1, address2 = in_matches.pop(0)
                    nlhs = lhs.get_predecessor_dataset(address1)
                    nrhs = rhs.get_predecessor_dataset(address2)
                    if nlhs and nrhs:
                        num_matches += super().match(nlhs, nrhs)

            if prev_num_matches == num_matches:
                break
            prev_num_matches = num_matches

        return num_matches


class ExactStructuralMatcher(
    _StructuralMatcher, singleton_matcher.ExactSingletonMatcher
):
    """Implements the exact structural matching logic."""


class InexactStructuralMatcher(
    _StructuralMatcher, singleton_matcher.InexactSingletonMatcher
):
    """Implements the inexact structural matching logic."""


class GreedyInexactStructuralMatcher(
    _StructuralMatcher, singleton_matcher.GreedyInexactSingletonMatcher
):
    """Implements the greedy inexact structural matching logic."""
