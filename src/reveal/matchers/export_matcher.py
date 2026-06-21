# -*- coding: utf-8 -*-
"""Export matcher definitions."""

from reveal.datasets import Dataset
from reveal.features import function_features
from reveal.matchers import optimistic_matcher

from numpy import float64

import numpy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["ExportMatcher"]


class ExportMatcher(optimistic_matcher.OptimisticMatcher):
    """Matches exported symbols in the compared programs."""

    def compare(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> float64:
        return float64(1 - int(lhs.names[i] == rhs.names[j]))

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        value = numpy.array([function_features.FUNCTION_TYPE_EXPORT], dtype=numpy.int8)
        return super().match(
            lhs.get_projected_dataset("function_type", value),
            rhs.get_projected_dataset("function_type", value),
        )
