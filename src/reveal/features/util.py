# -*- coding: utf-8 -*-

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = [
    "no_sum",
    "pairwise_sum",
    "point_distance",
    "euclidean_distance",
    "hamming_distance",
]


from reveal.features.features import FeatureValue

from numpy import float64, ndarray

import numpy


def no_sum(x: FeatureValue, y: FeatureValue) -> ndarray:
    return numpy.zeros(len(x.value), dtype=numpy.int32)


def pairwise_sum(x: FeatureValue, y: FeatureValue) -> ndarray:
    return numpy.add(x.value, y.value)


def point_distance(x: FeatureValue, y: FeatureValue) -> float64:
    d = numpy.maximum(x.value[0], y.value[0])
    return numpy.abs(x.value[0] - y.value[0]) / d if d else float64()


def euclidean_distance(x: FeatureValue, y: FeatureValue) -> float64:
    d = numpy.maximum(numpy.linalg.norm(x.value), numpy.linalg.norm(y.value))
    return numpy.linalg.norm(x.value - y.value) / d if d else float64()


def hamming_distance(x: FeatureValue, y: FeatureValue) -> float64:
    dxy = x.value[0] ^ y.value[0]
    d = 0
    n = dxy.bit_length()
    for _ in range(dxy.bit_length()):
        d += dxy & 1
        dxy >>= 1
    return float64(d / n) if n else float64()
