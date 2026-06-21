# -*- coding: utf-8 -*-
"""Name matcher definitions."""

from reveal.datasets import Dataset
from reveal.matchers import optimistic_matcher

from numpy import float64

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["NameMatcher"]


class NameMatcher(optimistic_matcher.OptimisticMatcher):
    """Match same names in two programs."""

    def compare(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> float64:
        return float64(1 - int(lhs.names[i] == rhs.names[j]))
