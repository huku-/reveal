# -*- coding: utf-8 -*-
"""Base matcher definitions."""

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["Matcher"]


from reveal.datasets import Dataset
from reveal.types import Matches

from numpy import float64

import abc
import bisect
import logging


class Matcher(abc.ABC):
    """Base class for all matchers."""

    def __init__(self, matches: Matches) -> None:
        super().__init__()
        self._logger = logging.getLogger()
        self._matches = matches

    def _handle_match(
        self,
        lhs: Dataset,
        rhs: Dataset,
        i: int,
        j: int,
        distance: float64 | None = None,
    ) -> None:
        """Should be called by matchers whenever a new match, between row `i` of
        dataset `lhs` and row `j` of dataset `rhs`, is detected. Inserts a new
        entry in the list of matches and removes the matched rows from their
        datasets.

        Args:
            lhs: Left-hand side dataset.
            rhs: Right-hard side dataset.
            i: Index of row in left-hand side dataset.
            j: Index of row in right-hand side dataset.
            distance: Distance score between the two rows.
        """

        lhs_name = lhs.names[i]
        rhs_name = rhs.names[j]
        bisect.insort_left(
            self._matches,
            (lhs.primary_keys[i], lhs_name, rhs.primary_keys[j], rhs_name, distance),
        )

        del lhs[i]
        del rhs[j]

        if distance:
            self._logger.debug(
                "Matches %6d | Matched %6d to %6d | Distance %12.4f | %s ~> %s",
                len(self._matches),
                i,
                j,
                distance,
                lhs_name,
                rhs_name,
            )
        else:
            self._logger.debug(
                "Matches %6d | Matched %6d to %6d | %s ~> %s",
                len(self._matches),
                i,
                j,
                lhs_name,
                rhs_name,
            )

    @abc.abstractmethod
    def compare(self, lhs: Dataset, rhs: Dataset, i: int, j: int) -> float64:
        """Compare two rows of two datasets.

        Args:
            lhs: Left-hand side dataset.
            rhs: Right-hard side dataset.
            i: Index of row in left-hand side dataset.
            j: Index of row in right-hand side dataset.

        Returns:
            Distance score between the compared rows.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        """Run this matcher.

        Args:
            lhs: Left-hand side dataset.
            rhs: Right-hand side dataset.

        Returns:
            Number of matches found.
        """
        raise NotImplementedError
