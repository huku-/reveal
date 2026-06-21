# -*- coding: utf-8 -*-

from reveal.algorithms import cu_recovery
from reveal.datasets.cluster_dataset import HierarchicalClusterDataset
from reveal.datasets.function_dataset import FunctionDataset

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["REcoverDataset"]


class REcoverDataset(HierarchicalClusterDataset):

    def __init__(self, dataset: FunctionDataset, estimator: str) -> None:
        super().__init__(dataset, cu_recovery.get_recover_hierarchy(dataset, estimator))
