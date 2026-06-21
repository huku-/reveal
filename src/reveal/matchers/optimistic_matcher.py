# -*- coding: utf-8 -*-

from reveal.datasets import Dataset

from reveal.matchers import matcher

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["OptimisticMatcher"]


class OptimisticMatcher(matcher.Matcher):
    """Base class for optimistic matchers (i.e., first match wins)."""

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        num_matches = 0
        for i in range(len(lhs) - 1, -1, -1):
            for j in range(len(rhs) - 1, -1, -1):
                if self.compare(lhs, rhs, i, j) == 0:
                    self._handle_match(lhs, rhs, i, j)
                    num_matches += 1
                    break
        return num_matches
