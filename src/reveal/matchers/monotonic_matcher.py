# -*- coding: utf-8 -*-
"""Monotonic matcher definitions.

This module implements the *monotonic matcher* described at [01].

[01] `<https://sci-hub.tw/10.1007/s11416-019-00339-6>`_
"""

from collections.abc import Iterator

from reveal.types import Comparable
from reveal.datasets.dataset import Dataset

import operator
import itertools

from reveal.matchers import matcher, singleton_matcher

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["ExactMonotonicMatcher", "InexactMonotonicMatcher"]


class _MonotonicMatcher(matcher.Matcher):
    """Monotonic matcher.

    This class implements a template algorithm for the monotonic matching logic,
    described at [01].
    """

    def _monotonic_partition(
        self, lhs_pks: Iterator[Comparable], rhs_pks: Iterator[Comparable]
    ) -> Iterator[tuple[Comparable, Comparable, Comparable, Comparable]]:
        zipped = zip(lhs_pks, rhs_pks)
        prev_lhs_pk, prev_rhs_pk = next(zipped)
        for lhs_pk, rhs_pk in zipped:
            if rhs_pk > prev_rhs_pk:
                yield prev_lhs_pk, lhs_pk, prev_rhs_pk, rhs_pk
            prev_lhs_pk = lhs_pk
            prev_rhs_pk = rhs_pk

    def match(self, lhs: Dataset, rhs: Dataset) -> int:
        num_matches = 0

        matches = self._matches
        if len(matches) < 2:
            return num_matches

        change = True
        while change:
            change = False

            # Create iterator for matched elements' primary keys of first dataset.
            lhs_pks = map(operator.itemgetter(0), itertools.islice(matches, None))

            # Create iterator for matched elements' primary keys of second dataset.
            rhs_pks = map(operator.itemgetter(2), itertools.islice(matches, None))

            #
            # Partition the matched elements in pairs of monotonically increasing
            # primary keys.
            #
            for p in self._monotonic_partition(lhs_pks, rhs_pks):
                lhs_pk_start, lhs_pk_end, rhs_pk_start, rhs_pk_end = p
                window = min(lhs_pk_end - lhs_pk_start, rhs_pk_end - rhs_pk_start)

                # Create cropped datasets.
                clhs = lhs.get_cropped_dataset(lhs_pk_start, lhs_pk_start + window + 1)
                crhs = rhs.get_cropped_dataset(rhs_pk_start, rhs_pk_start + window + 1)

                # Match cropped datasets.
                if clhs and crhs:
                    tmp_num_matches = super().match(clhs, crhs)
                    num_matches += tmp_num_matches
                    if tmp_num_matches > 0:
                        change = True

        return num_matches


class ExactMonotonicMatcher(_MonotonicMatcher, singleton_matcher.ExactSingletonMatcher):
    """Exact monotonic matcher."""


class InexactMonotonicMatcher(
    _MonotonicMatcher, singleton_matcher.InexactSingletonMatcher
):
    """Inexact monotonic matcher."""
