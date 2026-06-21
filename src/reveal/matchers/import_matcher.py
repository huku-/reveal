# -*- coding: utf-8 -*-
"""Import matcher definitions."""

from reveal.datasets import Dataset
from reveal.features import function_features
from reveal.matchers import optimistic_matcher

from numpy import float64

import numpy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["ImportMatcher"]


class ImportMatcher(optimistic_matcher.OptimisticMatcher):
    """Matches imported symbols in the compared programs."""

    def _get_import_name(self, name: str) -> str:
        if "@@" in name:
            name = name[: name.index("@@")]
        if name.startswith("__imp_"):
            name = name[6:]
        return name

    def compare(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> float64:
        lhs_name = self._get_import_name(lhs.names[i])
        rhs_name = self._get_import_name(rhs.names[j])
        return float64(1 - int(lhs_name == rhs_name))

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        value = numpy.array([function_features.FUNCTION_TYPE_IMPORT], dtype=numpy.int8)
        return super().match(
            lhs.get_projected_dataset("function_type", value),
            rhs.get_projected_dataset("function_type", value),
        )
