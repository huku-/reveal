# -*- coding: utf-8 -*-
"""Type aliases"""

from typing import Any, Protocol

from numpy import float64

import abc


class Comparable(Protocol):
    @abc.abstractmethod
    def __lt__(self, other: Any) -> bool: ...


Match = tuple[Comparable, Any, Comparable, Any, float64]
Matches = list[Match]
