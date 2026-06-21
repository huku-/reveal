# -*- coding: utf-8 -*-

from reveal.datasets.function_dataset import FunctionDataset
from reveal.features.function_features import FunctionFeatureVector

import numpy

import collections


def simple_lsh(dataset: FunctionDataset, num_planes: int = 16) -> dict[FunctionDataset]:
    """Simple LSH implementation based on random hyperplanes.

    Args:
        dataset: Dataset whose elements to split in LSH buckets.
        num_planes: Number of random hyperplanes to generate.

    Returns:
        Dictionary of LSH datasets keyd by hash.
    """

    # The input vector consists of the concatenation of the following features.
    num_dims = (
        FunctionFeatureVector["vertex_classification"].size
        + FunctionFeatureVector["edge_classification"].size
        + FunctionFeatureVector["insn_bow"].size
    )
    plane_norms = numpy.random.randn(num_planes, num_dims)

    buckets = collections.defaultdict(list)
    for i, row in enumerate(dataset.rows):
        v = numpy.concatenate(
            [
                row["vertex_classification"].value,
                row["edge_classification"].value,
                row["insn_bow"].value,
            ]
        )
        h = 0
        for b in numpy.packbits(numpy.dot(v, plane_norms.T) >= 0):
            h <<= 8
            h |= b
        buckets[h].append(dataset.primary_keys[i])

    datasets = {}
    for h in buckets:
        datasets[h] = dataset.get_neighbor_dataset(sorted(buckets[h]))
    return datasets
