# -*- coding: utf-8 -*-
"""Utility functions"""

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from reveal.types import Comparable

import bisect

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["to_path", "is_sorted_asc", "is_sorted_desc"]


def to_path(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)):
        raise ValueError(f"Invalid path {path}")
    if isinstance(path, str):
        path = Path(path)
    return path


def is_sorted_asc(x: Sequence[Comparable]) -> bool:
    return all(x[i] < x[i + 1] for i in range(len(x) - 1))


def is_sorted_desc(x: Sequence[Comparable]) -> bool:
    return all(x[i] > x[i + 1] for i in range(len(x) - 1))


def bisect_left(array: MutableSequence[Comparable], x: Comparable) -> int:
    r = -1
    i = bisect.bisect_left(array, x)
    if i != len(array) and array[i] == x:
        r = i
    return r
