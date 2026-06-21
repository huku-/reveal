# -*- coding: utf-8 -*-

from reveal.algorithms import louvain
from reveal.datasets.cluster_dataset import HierarchicalClusterDataset
from reveal.datasets.function_dataset import FunctionDataset

import numpy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["LouvainDataset"]


class LouvainDataset(HierarchicalClusterDataset):

    def __init__(self, dataset: FunctionDataset) -> None:
        super().__init__(
            dataset,
            louvain.consensus(
                dataset.graph,
                weight="weight",
                num_iters=100,
                # num_iters=1,
                prob=0.95,
                random_state=numpy.random.RandomState(1),
            ),
        )
