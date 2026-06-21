# -*- coding: utf-8 -*-
"""Cluster datasets."""

from reveal.datasets.dataset import Dataset
from reveal.datasets.function_dataset import FunctionDataset
from reveal.graphs.hierarchy import Cluster, Hierarchy

import contextlib

from reveal.features import cluster_features, function_features

import numpy


class ClusterDataset(Dataset):
    """Cluster dataset."""

    pass


class HierarchicalClusterDataset(object):
    """Represents a hierarchical function cluster dataset."""

    def __init__(self, dataset: Dataset, hierarchy: Hierarchy) -> None:
        super().__init__()
        self._dataset = dataset
        self._hierarchy = hierarchy

    @property
    def hierarchy(self) -> Hierarchy:
        return self._hierarchy

    def function_dataset_at(self, cluster: Cluster) -> FunctionDataset:
        """Return a function dataset of all functions in a cluster.

        Args:
            cluster: Cluster of functions.

        Returns:
            Function dataset.
        """
        cluster_members = sorted(self._hierarchy.cluster_members(cluster))
        return self._dataset.get_neighbor_dataset(cluster_members)

    def cluster_dataset_at(
        self, level: int, filter_clusters: list[Cluster] | None = None
    ) -> ClusterDataset:
        """Return cluster dataset of clusters at level *level* in the hierarchical
        cluster dataset.

        Args:
            level: Level of clusters.
            filter_clusters: Only return a cluster if found in this list.

        Returns:
            Dataset of clusters at level *level*.
        """
        primary_keys = []
        names = []
        rows = []

        meta_graphs = self._hierarchy.meta_graphs

        for cluster in sorted(self._hierarchy.clusters(level)):
            if filter_clusters and cluster not in filter_clusters:
                continue

            #
            # Build the aggregated feature vector of functions in this cluster
            # (i.e., pairwise summation of individual feature vectors belonging
            # to each function in the cluster).
            #
            cluster_members = self._hierarchy.cluster_members(cluster)
            ffv = function_features.FunctionFeatureVector()
            for primary_key in cluster_members:
                with contextlib.suppress(ValueError):
                    i = self._dataset.index(primary_key)
                    ffv += self._dataset.rows[i]

            #
            # Build cluster feature vector, which consists of cluster-specific
            # features (e.g., size of cluster) concatenated with the aggregated
            # function feature vector.
            #
            cfv = numpy.concatenate(
                [
                    [
                        len(cluster_members),
                        sum(
                            dict(
                                meta_graphs[level + 1].in_degree(
                                    cluster_members, weight="weight"
                                )
                            ).values()
                        ),
                        sum(
                            dict(
                                meta_graphs[level + 1].out_degree(
                                    cluster_members, weight="weight"
                                )
                            ).values()
                        ),
                        meta_graphs[level].in_degree(cluster, weight="weight"),
                        meta_graphs[level].out_degree(cluster, weight="weight"),
                    ],
                    ffv.flatten(),
                ]
            )

            primary_keys.append(cluster)
            names.append(cluster)
            rows.append(cluster_features.ClusterFeatureVector.unflatten(cfv))

        return ClusterDataset(meta_graphs[level], primary_keys, names, rows)
