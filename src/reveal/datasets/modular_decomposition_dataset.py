# -*- coding: utf-8 -*-

from reveal.algorithms import modular_decomposition
from reveal.datasets.cluster_dataset import HierarchicalClusterDataset
from reveal.datasets.function_dataset import FunctionDataset

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["ModularDecompositionDataset"]


class ModularDecompositionDataset(HierarchicalClusterDataset):
    """Modular decomposition hierarchical cluster dataset."""

    def __init__(self, dataset: FunctionDataset) -> None:
        super().__init__(
            dataset, modular_decomposition.get_modular_decomposition(dataset.graph)
        )
