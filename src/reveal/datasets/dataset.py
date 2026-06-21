# -*- coding: utf-8 -*-
"""Base dataset definitions."""

from __future__ import annotations

from collections.abc import Iterator

from reveal import util
from reveal.types import Comparable
from reveal.features.features import FeatureVectorValue
from reveal.graphs.graph import Graph

from numpy import ndarray

import bisect

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["Dataset"]


class Dataset(object):
    """Represents a dataset in its most general form. A dataset is a collection
    of rows. Rows are uniquely identified by primary keys and optionally a name.
    Generally, a dataset consists of an arbitrary collection of *NxM* records,
    where *N* is the number of rows (i.e., elements) and *M* the number of
    *columns* (i.e., features).

    In practice, rows hold feature vectors of program functions or clusters of
    functions, with each feature occupying a single column. Primary keys can be
    arbitrary ordinals, with the requirement that dataset rows should always be
    sorted with respect to their primary keys.

    Args:
        graph: A graph representing the relationship between the elements of the
            dataset.
        primary_keys: Sorted list of element primary keys,
        names: Names of elements.
        rows: Arbitrary *NxM* collection of records, sorted with respect to their
            primary keys.
        parent: Reference to parent dataset. Only meaningful for derived datasets.
    """

    def __init__(
        self,
        graph: Graph,
        primary_keys: list[Comparable],
        names: list[str],
        rows: list[FeatureVectorValue],
        parent: Dataset | None = None,
    ):
        super().__init__()
        self.graph = graph
        self.primary_keys = primary_keys
        self.names = names
        self.rows = rows
        self.parent = parent

        #
        # We have to make sure element primary keys are sorted either upwards
        # or downwards, otherwise matching algorithms will not work as expected.
        # If the assertion fails, something went wrong during dataset construction.
        #
        assert util.is_sorted_asc(primary_keys) or util.is_sorted_desc(
            primary_keys
        ), "Primary keys not sorted. This is a bug!"

    def __len__(self) -> int:
        return len(self.rows)

    def __bool__(self) -> bool:
        return bool(len(self))

    def __delitem__(self, index: int) -> None:
        if self.parent:
            i = self.parent.index(self.primary_keys[index])
            del self.parent[i]
        del self.primary_keys[index]
        del self.names[index]
        del self.rows[index]

    def index(self, primary_key: Comparable) -> int:
        """Return the index of an element in the dataset given its primary key.

        Args:
            primary_key: The primary key of the element to look up.

        Returns:
            The index of the element
        """
        if (i := util.bisect_left(self.primary_keys, primary_key)) >= 0:
            return i
        raise ValueError()

    def add(self, primary_key: Comparable, name: str, row: FeatureVectorValue) -> None:
        """Add an element at the appropriate index in the dataset.

        Args:
            primary_key: Element primary key.
            name: Name of element.
            row: Element feature vector.
        """
        i = bisect.bisect_left(self.primary_keys, primary_key)
        self.primary_keys.insert(i, primary_key)
        self.names.insert(i, name)
        self.rows.insert(i, row)

    def get_neighbor_dataset(self, primary_key_iter: Iterator[Comparable]) -> Dataset:
        """Utility method used for constructing successor and predecessor derived
        datasets.

        Args:
            primary_key_iter: Iterator of primary keys.

        Returns:
            A new derived dataset consisting of the elements whose primary keys
            are given by *primary_key_iter*.
        """

        primary_keys = []
        names = []
        rows = []

        for primary_key in primary_key_iter:
            if (i := util.bisect_left(self.primary_keys, primary_key)) >= 0:
                primary_keys.append(self.primary_keys[i])
                names.append(self.names[i])
                rows.append(self.rows[i])

        return type(self)(
            self.graph,
            primary_keys,
            names,
            rows,
            parent=self,
        )

    def get_successor_dataset(self, primary_key: Comparable) -> Dataset:
        """Given the primary key of an element, construct a derived dataset that
        consists of the element's successors.

        Args:
            primary_key: Primary key of element whose successor dataset to return.

        Returns:
            The derived successor dataset.
        """
        return self.get_neighbor_dataset(self.graph.successors(primary_key))

    def get_predecessor_dataset(self, primary_key: Comparable) -> Dataset:
        """Given the primary key of an element, construct a derived dataset that
        consists of the element's predecessors.

        Args:
            primary_key: Primary key of element whose predecessor dataset to return.

        Returns:
            The derived predecessor dataset.
        """
        return self.get_neighbor_dataset(self.graph.predecessors(primary_key))

    def get_projected_dataset(self, column: int | str, value: ndarray) -> Dataset:
        """Generate a derived dataset consisting of the elements whose column
        (i.e., feature) *column* equals *value*.

        Args:
            column: Index or name of column (i.e., feature).
            value: Feature velue.

        Returns:
            Derived dataset of matched elements.
        """

        primary_keys = []
        names = []
        rows = []

        for i in range(len(self)):
            if self.rows[i][column].value == value:
                primary_keys.append(self.primary_keys[i])
                names.append(self.names[i])
                rows.append(self.rows[i])

        return type(self)(
            self.graph,
            primary_keys,
            names,
            rows,
            parent=self,
        )

    def get_cropped_dataset(
        self, primary_key_min: Comparable, primary_key_max: Comparable
    ) -> Dataset:
        """Generate a derived dataset consisting of these rows whose primary key
        falls within the range from *primary_key_min* to *primary_key_max*.

        Args:
            primary_key_min: Minimum primary key value.
            primary_key_max: Maximum primary key value.

        Returns:
            A new derived dataset.
        """

        primary_keys = []
        names = []
        rows = []

        i = bisect.bisect(self.primary_keys, primary_key_min)
        while i < len(self) and self.primary_keys[i] < primary_key_max:
            primary_keys.append(self.primary_keys[i])
            names.append(self.names[i])
            rows.append(self.rows[i])
            i += 1

        return type(self)(
            self.graph,
            primary_keys,
            names,
            rows,
            parent=self,
        )
