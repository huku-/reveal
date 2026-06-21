# -*- coding: utf-8 -*-
"""Features used for representing clusters of functions."""

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["ClusterFeatureVector"]


from reveal.features.features import Feature, FeatureVector
from reveal.features.function_features import FunctionFeatureVector
from reveal.features import util

import numpy

ClusterFeatureVector = FeatureVector(
    [
        Feature(numpy.int32, 1, util.point_distance, util.pairwise_sum, "c1"),
        Feature(numpy.int32, 1, util.point_distance, util.pairwise_sum, "c2"),
        Feature(numpy.int32, 1, util.point_distance, util.pairwise_sum, "c3"),
        Feature(numpy.int32, 1, util.point_distance, util.pairwise_sum, "c4"),
        Feature(numpy.int32, 1, util.point_distance, util.pairwise_sum, "c5"),
    ]
    + FunctionFeatureVector.features
)
