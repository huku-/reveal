# -*- coding: utf-8 -*-
# pylint: disable=protected-access,redefined-builtin
"""Basic definitions for features and feature vectors."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Generic, TypeVar

from numpy import ndarray, float64

import abc

import numpy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["Feature", "FeatureVector", "FeatureValue", "FeatureVectorValue"]


T = TypeVar("T")


class Feature(abc.ABC, Generic[T]):
    """Represents a feature (e.g., age, height etc.). Specific instances of
    features (e.g., an instance representing an age of 25) are represented by
    class cls:`FeatureValue` instead.

    Feature instances are backed by 1-dimensional numpy arrays of primitive data
    types. Even scalar features (i.e., comprising of a single value) follow this
    rule, in which case, a 1x1 array is used. This class operates as a factory
    for creating such instances and implements the necessary machinery for
    enforcing consistent behavior.

    Args:
        dtype: Data type of numpy array (e.g., `float64` etc.).
        size: Size of 1-dimensional numpy array.
        distance_cb: Callable that takes two numpy arrays, corresponding to two
            feature instances, and computes some form of distance between them
            (e.g., Euclidean).
        aggregation_cb: Callable that takes two numpy arrays, corresponding to
            two feature instances, aggregates them and returns the result.
        id: Arbitrary feature type identifier (e.g., a string, a UUID etc.).
    """

    __slots__ = ("_dtype", "_size", "_distance_cb", "_aggregation_cb", "_id")

    def __init__(
        self,
        dtype: type[T],
        size: int,
        distance_cb: Callable[[FeatureValue, FeatureValue], float64],
        aggregation_cb: Callable[[FeatureValue, FeatureValue], ndarray],
        id: object | None = None,
    ) -> None:
        super().__init__()
        self._dtype = dtype
        self._size = size
        self._distance_cb = distance_cb
        self._aggregation_cb = aggregation_cb
        self._id = id

    def __str__(self) -> str:
        return f"Feature[dtype={self._dtype}, size={self._size}, id={self._id}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Feature):
            raise NotImplementedError
        return (
            self._dtype == other._dtype
            and self._size == other._size
            and self._distance_cb == other._distance_cb
            and self._aggregation_cb == other._aggregation_cb
            and self._id == other._id
        )

    def __call__(self, value: ndarray | Sequence[T] | None = None) -> FeatureValue:
        """Create an instance of this feature.

        Args:
            value: A 1-dimensional numpy array or sequence of values representing
                the feature instance.

        Returns:
            Feature instance.

        Raises:
            ValueError: If conversion to numpy array fails, or the format of the
                input value is not valid for this feature.
        """
        if value is not None:
            if isinstance(value, Sequence):
                value = numpy.array(value, dtype=self._dtype)
            if not isinstance(value, ndarray) or value.shape != (self._size,):
                raise ValueError(f"Invalid value {value} for feature {self}")
            if value.dtype != self._dtype:
                value = numpy.asarray(value, dtype=self._dtype)
        else:
            value = numpy.zeros(shape=(self._size,), dtype=self._dtype)
        return FeatureValue(self, value)

    @property
    def dtype(self) -> type[T]:
        return self._dtype

    @property
    def size(self) -> int:
        return self._size

    @property
    def distance_cb(self) -> Callable[[FeatureValue, FeatureValue], float64]:
        return self._distance_cb

    @property
    def aggregation_cb(self) -> Callable[[FeatureValue, FeatureValue], ndarray]:
        return self._aggregation_cb

    @property
    def id(self) -> object | None:
        return self._id


class FeatureVector(Sequence):
    """Represents a feature vector. Specific instances of feature vectors (e.g.,
    an instance representing a person of age 25 and height 1.85) are represented
    by class :cls:`FeatureVectorValue`.

    Args:
        features: Features comprising this feature vector.
    """

    __slots__ = ("_features", "_id_to_idx")

    def __init__(self, features: list[Feature]) -> None:
        super().__init__()
        self._features = features
        self._id_to_idx = {features[i].id: i for i in range(len(features))}

    def __str__(self) -> str:
        s = "FeatureVector[\n"
        s += "".join([f"\t{feature},\n" for feature in self._features])
        s += "]\n"
        return s

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FeatureVector):
            raise NotImplementedError
        return self._features == other._features

    def __len__(self) -> int:
        return len(self._features)

    def __getitem__(self, i: int | str) -> Feature:
        if not isinstance(i, int):
            i = self.get_feature_idx(i)
        return self._features[i]

    def __call__(
        self, values: ndarray | Sequence[Sequence[Any]] | None = None
    ) -> FeatureVectorValue:
        """Create an instance of this feature vector.

        Args:
            values: A 2-dimensional numpy array or sequence of values representing
                each feature's instance.

        Returns:
            Feature vector instance.

        Raises:
            ValueError: If the format of the input values is not valid for this
                feature vector.
        """
        feature_values = []
        if values is not None:
            if not isinstance(values, (ndarray, Sequence)) or len(values) != len(
                self._features
            ):
                raise ValueError(f"Invalid values {values} for feature vector {self}")
            for i, feature in enumerate(self._features):
                feature_values.append(feature(values[i]))
        else:
            for feature in self._features:
                feature_values.append(feature())
        return FeatureVectorValue(self, feature_values)

    @property
    def features(self) -> list[Feature]:
        return list(self._features)

    def get_feature_idx(self, id: object) -> int:
        """Return the index of the feature with the given id in this feature
        vector.

        Args:
            id: Feature id to look up.

        Returns:
            Index of feature.

        Raises:
            KeyError: If a feature with the given id does not exist in this
                feature vector.
        """
        if id not in self._id_to_idx:
            raise KeyError(f"No such feature {id}")
        return self._id_to_idx[id]

    def unflatten(self, values: ndarray | Sequence[Any]) -> FeatureVectorValue:
        """Create an instance of this feature vector from a flattened array or
        sequence of values.

        Args:
            values: Flattened array of values.

        Returns:
            Feature vector instance.

        Raises:
            ValueError: If the format of the input values is not valid for this
                feature vector.
        """
        if not isinstance(values, (ndarray, Sequence)) or len(values) != sum(
            (feature.size for feature in self._features)
        ):
            raise ValueError(
                f"Invalid values {values} for flattened feature vector {self}"
            )
        feature_values = []
        for feature in self._features:
            feature_values.append(feature(values[: feature.size]))
            values = values[feature.size :]
        return FeatureVectorValue(self, feature_values)


class FeatureValue(object):
    """Represents an instance of a feature (e.g., an age of 25).

    Args:
        feature: Feature.
        value: Value of feature.
    """

    __slots__ = ("_feature", "_value")

    def __init__(self, feature: Feature, value: Any) -> None:
        super().__init__()
        self._feature = feature
        self._value = value

    def __str__(self) -> str:
        return f"FeatureValue[value={self._value}, feature={self._feature}]"

    def __add__(self, other: object) -> FeatureValue:
        """Aggregate two feature instances and return the result.

        Args:
            other: Feature instance to aggregate with *self*.

        Returns:
            New feature instance holding the result of the aggregation.

        Raises:
            NotImplementedError: If *other* is not a :cls:`FeatureValue` instance.
            ValueError: If the aggregated feature instances belong to different
                features.
        """
        if not isinstance(other, FeatureValue):
            raise NotImplementedError
        if self._feature != other._feature:
            raise ValueError("Cannot aggregate instances of different features")
        # return type(self)(self._feature, self._feature.aggregation_cb(self, other))
        return self._feature(self._feature.aggregation_cb(self, other))

    def __sub__(self, other: object) -> float64:
        """Subtract two feature instances (i.e., compute their distance).

        Args:
            other: Feature instance to subtract from *self*.

        Returns:
            A float value representing the distance of the feature instances.

        Raises:
            NotImplementedError: If *other* is not a :cls:`FeatureValue` instance.
            ValueError: If the subtracted feature instances belong to different
                features.
        """
        if not isinstance(other, FeatureValue):
            raise NotImplementedError
        if self._feature != other._feature:
            raise ValueError("Cannot diff instances of different features")
        return self._feature.distance_cb(self, other)

    @property
    def feature(self) -> Feature:
        return self._feature

    @property
    def value(self) -> Any:
        return self._value


class FeatureVectorValue(Sequence):
    """Represents a feature vector instance."""

    __slots__ = ("_feature_vector", "_feature_values")

    def __init__(
        self, feature_vector: FeatureVector, feature_values: list[FeatureValue]
    ) -> None:
        super().__init__()
        self._feature_vector = feature_vector
        self._feature_values = feature_values

    def __str__(self) -> str:
        s = "FeatureVectorValue[\n"
        s += "".join(
            [f"\t{feature_value},\n" for feature_value in self._feature_values]
        )
        s += "]\n"
        return s

    def __len__(self) -> int:
        return len(self._feature_values)

    def __getitem__(self, i: int | str) -> FeatureValue:
        if not isinstance(i, int):
            i = self._feature_vector.get_feature_idx(i)
        return self._feature_values[i]

    def __add__(self, other: object) -> FeatureVectorValue:
        """Aggregate two feature vector instances and return the result.

        Args:
            other: Feature vector instance to aggregate with *self*.

        Returns:
            New feature vector instance holding the result of the aggregation.

        Raises:
            NotImplementedError: If *other* is not a :cls:`FeatureVectorValue`
                instance.
            ValueError: If the aggregated feature vector instances belong to
                different feature vectors.
        """
        if not isinstance(other, FeatureVectorValue):
            raise NotImplementedError
        if self._feature_vector != other._feature_vector:
            raise ValueError("Cannot aggregate instances of different feature vectors")
        feature_values = []
        for i, feature_value in enumerate(self._feature_values):
            feature_values.append(feature_value + other._feature_values[i])
        return FeatureVectorValue(self._feature_vector, feature_values)

    def __sub__(self, other: object) -> float64:
        """Subtract two feature vector instances (i.e., compute their distance).

        Args:
            other: Feature vector instance to subtract from *self*.

        Returns:
            A float value representing the distance of the feature vector instances.

        Raises:
            NotImplementedError: If *other* is not a :cls:`FeatureVectorValue`
                instance.
            ValueError: If the subtracted feature vector instances belong to
                different feature vectors.
        """
        if not isinstance(other, FeatureVectorValue):
            raise NotImplementedError
        if self._feature_vector != other._feature_vector:
            raise ValueError("Cannot subtract instances of different feature vectors")
        feature_values = []
        for i, feature_value in enumerate(self._feature_values):
            feature_values.append(feature_value - other._feature_values[i])
        return numpy.sum(feature_values, dtype=float64) / len(self._feature_values)

    @property
    def feature_vector(self) -> FeatureVector:
        return self._feature_vector

    def flatten(self) -> ndarray:
        """Flatten feature vector instance.

        Returns:
            A 1-dimensional array containing the flattened values of all feature
            instances of this feature vector instance.
        """
        return numpy.concat(
            [feature_value.value for feature_value in self._feature_values]
        )
