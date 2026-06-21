# -*- coding: utf-8 -*-
"""Singleton matcher definitions."""

from reveal import util
from reveal.datasets import Dataset
from reveal.matchers import matcher

from numpy import float64

import bisect

import numpy
import scipy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = [
    "ExactSingletonMatcher",
    "InexactSingletonMatcher",
    "GreedyInexactSingletonMatcher",
]


class ExactSingletonMatcher(matcher.Matcher):
    """Exact singleton matcher."""

    def compare(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> float64:
        return lhs.rows[i] - rhs.rows[j]

    def _match_remaining(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> bool:
        """Make sure that row `i` of dataset `lhs` and row `j` of dataset `rhs`
        are unique in their datasets.

        Args:
            lhs: Left-hand side dataset.
            rhs: Right-hand side dataset.
            i: Index of row in left-hand side dataset.
            j: Index of row in right-hand side dataset.

        Returns:
            `True` if the rows are unique (i.e., singletons), `False` otherwise.
        """
        if all(
            self.compare(lhs, lhs, k, i) != 0 for k in range(len(lhs)) if k != i
        ) and all(self.compare(rhs, rhs, k, j) != 0 for k in range(len(rhs)) if k != j):
            self._handle_match(lhs, rhs, i, j)
            return True
        return False

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        num_matches = 0
        compared = []
        for i in range(len(lhs) - 1, -1, -1):
            for j in range(len(rhs) - 1, -1, -1):
                if self.compare(lhs, rhs, i, j) == 0:
                    if util.bisect_left(compared, rhs.primary_keys[j]) < 0:
                        if self._match_remaining(lhs, rhs, i, j):
                            num_matches += 1
                        else:
                            bisect.insort_left(compared, rhs.primary_keys[j])
                    break
        return num_matches


class InexactSingletonMatcher(matcher.Matcher):
    """Inexact singleton matcher based on the Hungarian algorithm."""

    def compare(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> float64:
        return lhs.rows[i] - rhs.rows[j]

    def _match_hungarian(self, lhs: Dataset, rhs: Dataset) -> int:
        lhs_sz = len(lhs)
        rhs_sz = len(rhs)
        matrix = numpy.full(shape=(lhs_sz, rhs_sz), fill_value=numpy.inf)
        for i in range(lhs_sz):
            for j in range(rhs_sz):
                matrix[i][j] = self.compare(lhs, rhs, i, j)

        mi, mj = scipy.optimize.linear_sum_assignment(matrix)

        matched = dict(zip(mi, mj))
        primary_keys = dict((i, rhs.primary_keys[j]) for i, j in matched.items())
        num_matches = 0
        for i in sorted(matched, reverse=True):
            j = rhs.index(primary_keys[i])
            self._handle_match(lhs, rhs, i, j, matrix[i][j])
            num_matches += 1

        return num_matches

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        num_matches = 0
        if lhs and rhs:
            num_matches += self._match_hungarian(lhs, rhs)
        return num_matches


class GreedyInexactSingletonMatcher(matcher.Matcher):
    """Implements the greedy inexact singleton matching logic."""

    def compare(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> float64:
        return lhs.rows[i] - rhs.rows[j]

    def _match_greedy(self, lhs: Dataset, rhs: Dataset) -> int:
        lhs_sz = len(lhs)
        rhs_sz = len(rhs)
        matrix = numpy.full(shape=(lhs_sz, rhs_sz), fill_value=numpy.inf)
        for i in range(lhs_sz):
            for j in range(rhs_sz):
                matrix[i][j] = self.compare(lhs, rhs, i, j)

        assignments = []
        for i in range(lhs_sz):
            min_m = numpy.inf
            min_j = -1
            for j in range(rhs_sz):
                if (
                    matrix[i][j] < min_m
                    and all(matrix[k][j] >= matrix[i][j] for k in range(i + 1, lhs_sz))
                    and all(matrix[i][k] >= matrix[i][j] for k in range(j + 1, rhs_sz))
                ):
                    min_m = matrix[i][j]
                    min_j = j
            if min_m != numpy.inf:
                for k in range(lhs_sz):
                    matrix[k][min_j] = numpy.inf
                assignments.append((i, min_j, min_m))

        assignments = list(reversed(assignments))

        addresses = [rhs.primary_keys[j] for (_, j, _) in assignments]

        num_matches = 0
        for k, (i, _, min_m) in enumerate(assignments):
            try:
                j = rhs.index(addresses[k])
                self._handle_match(lhs, rhs, i, j, min_m)
                num_matches += 1
            except ValueError:
                pass

        return num_matches

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        num_matches = 0
        if lhs and rhs:
            num_matches += self._match_greedy(lhs, rhs)
        return num_matches
