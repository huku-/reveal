# -*- coding: utf-8 -*-
"""REveal diffing entry point."""

from pathlib import Path

from reveal.types import Matches
from reveal.datasets.cluster_dataset import ClusterDataset, HierarchicalClusterDataset
from reveal.datasets.dataset import Dataset
from reveal.datasets.function_dataset import FunctionDataset
from reveal.matchers.matcher import Matcher

import logging
import pickle
import time

from reveal import util
from reveal.algorithms import simple_lsh
from reveal.datasets import (
    louvain_dataset,
    function_dataset,
    modular_decomposition_dataset,
    recover_dataset,
)
from reveal.matchers import (
    export_matcher,
    import_matcher,
    monotonic_matcher,
    singleton_matcher,
    structural_matcher,
    name_matcher,
)

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["Differ"]


_EXACT_MATCHERS: list[type[Matcher]] = [
    singleton_matcher.ExactSingletonMatcher,
    structural_matcher.ExactStructuralMatcher,
    monotonic_matcher.ExactMonotonicMatcher,
]

_INEXACT_MATCHERS: list[type[Matcher]] = [
    singleton_matcher.InexactSingletonMatcher,
    # singleton_matcher.GreedyInexactSingletonMatcher,
    structural_matcher.InexactStructuralMatcher,
    monotonic_matcher.InexactMonotonicMatcher,
]

_CLUSTER_EXACT_MATCHERS: list[type[Matcher]] = [
    singleton_matcher.ExactSingletonMatcher,
    structural_matcher.ExactStructuralMatcher,
]

_CLUSTER_INEXACT_MATCHERS: list[type[Matcher]] = [
    singleton_matcher.InexactSingletonMatcher,
    # singleton_matcher.GreedyInexactSingletonMatcher,
    structural_matcher.InexactStructuralMatcher,
]


class Differ(object):
    """Entry point to REveal's binary diffing logic."""

    def __init__(
        self,
        lhs_path: str | Path,
        rhs_path: str | Path,
        results_path: str | Path,
        match_inexact: bool = True,
        match_imports: bool = False,
        match_exports: bool = False,
        match_names: bool = False,
        match_hierarchical: str | None = None,
        write_time: bool = False,
    ) -> None:
        super().__init__()
        self.logger = logging.getLogger()
        self.lhs_path = util.to_path(lhs_path)
        self.rhs_path = util.to_path(rhs_path)
        self.results_path = util.to_path(results_path)
        self.match_inexact = match_inexact
        self.match_imports = match_imports
        self.match_exports = match_exports
        self.match_names = match_names
        self.match_hierarchical = match_hierarchical
        self.write_time = write_time

    def _run_matcher(
        self, matcher: type[Matcher], lhs: Dataset, rhs: Dataset, matches: Matches
    ) -> int:
        """Instantiate and run a matcher on two datasets.

        Args:
            matcher: Matcher to instantiate and run.
            lhs: Left-hand side dataset.
            rhs: Right-hand side dataset.
            matches: List to be populated with new matches.

        Returns:
            Number of new matches dicovered.
        """
        self.logger.debug("Entering %s (%d/%d)", matcher.__name__, len(lhs), len(rhs))
        time_start = int(time.time())
        num_matches = matcher(matches).match(lhs, rhs)
        time_end = int(time.time())
        self.logger.debug(
            "Found %d new matches in %d seconds (%d/%d)",
            num_matches,
            time_end - time_start,
            len(lhs),
            len(rhs),
        )
        return num_matches

    def _run_matchers(
        self,
        matchers: list[type[Matcher]],
        lhs: Dataset,
        rhs: Dataset,
        matches: Matches,
    ) -> int:
        """Instantiate and run a series of matches, until no more matches can be
        found.

        Args:
            matchers: List of matchers to instantiate and run.
            lhs: Left-hand side dataset.
            rhs: Right-hand side dataset.
            matches: List to be populated with new matches.

        Returns:
            Number of new matches dicovered.
        """
        prev_num_matches = num_matches = 0
        while lhs and rhs:
            for matcher in matchers:
                num_matches += self._run_matcher(matcher, lhs, rhs, matches)
            if num_matches == prev_num_matches:
                break
            prev_num_matches = num_matches
        return num_matches

    def _match_functions(
        self, lhs: FunctionDataset, rhs: FunctionDataset, matches: Matches
    ) -> int:
        """Match function datasets.

        Args:
            lhs: Left-hand side function dataset.
            rhs: Right-hand side function dataset.
            matches: List to be populated with new function matches.

        Returns:
            Number of new function matches discovered.
        """
        prev_num_matches = num_matches = 0
        while lhs and rhs:
            num_matches += self._run_matchers(_EXACT_MATCHERS, lhs, rhs, matches)
            if self.match_inexact:
                num_matches += self._run_matchers(_INEXACT_MATCHERS, lhs, rhs, matches)
            if num_matches == prev_num_matches:
                break
            prev_num_matches = num_matches
        return num_matches

    def _match_clusters(
        self, cd_lhs: ClusterDataset, cd_rhs: ClusterDataset, matches: Matches
    ) -> int:
        """Match cluster datasets.

        Args:
            cd_lhs: Left-hand side cluster dataset.
            cd_rhs: Right-hand side cluster dataset.
            matches: List to be populated with new cluster matches.

        Returns:
            Number of new cluster matches discovered.
        """
        prev_num_matches = num_matches = 0
        while cd_lhs and cd_rhs:
            num_matches += self._run_matchers(
                _CLUSTER_EXACT_MATCHERS,
                cd_lhs,
                cd_rhs,
                matches,
            )
            num_matches += self._run_matchers(
                _CLUSTER_INEXACT_MATCHERS,
                cd_lhs,
                cd_rhs,
                matches,
            )
            if prev_num_matches == num_matches:
                break
            prev_num_matches = num_matches
        return num_matches

    def _match_hierarchical_datasets(
        self,
        ch_lhs: HierarchicalClusterDataset,
        ch_rhs: HierarchicalClusterDataset,
        matched_clusters: Matches,
        matched_funcs: Matches,
        use_lsh: bool = False,
    ) -> int:
        """Match hierarchical cluster datasets.

        Args:
            ch_lhs: Left-hand side hierarchical cluster dataset.
            ch_rhs: Right-hand side hierarchical cluster dataset.
            matched_clusters: List to be populated with new cluster matches.
            matched_funcs: List to be populated with new function matches.
            use_lsh: Whether to use LSH to further divide function datasets.

        Returns:
            Number of new function matches discovered.
        """
        # Match highest level clusters (i.e., clusters of clusters etc.).
        matched_clusters = []
        lhs_num_levels = ch_lhs.hierarchy.num_levels
        rhs_num_levels = ch_rhs.hierarchy.num_levels
        num_levels = min(lhs_num_levels, rhs_num_levels)
        cd_lhs = ch_lhs.cluster_dataset_at(lhs_num_levels - num_levels + 1)
        cd_rhs = ch_rhs.cluster_dataset_at(rhs_num_levels - num_levels + 1)
        self._match_clusters(cd_lhs, cd_rhs, matched_clusters)

        # Consecutively match lower levels of clusters.
        matched_levels = [list(matched_clusters)]
        for i in range(2, num_levels - 1):
            matched_clusters = []
            for _, lhs_cluster, _, rhs_cluster, _ in matched_levels[i - 2]:
                if lhs_cluster.cluster_type == rhs_cluster.cluster_type:
                    lhs_cluster_children = list(
                        ch_lhs.hierarchy.dendrogram.successors(lhs_cluster)
                    )
                    rhs_cluster_children = list(
                        ch_rhs.hierarchy.dendrogram.successors(rhs_cluster)
                    )
                    cd_lhs = ch_lhs.cluster_dataset_at(
                        lhs_num_levels - num_levels + i,
                        filter_clusters=lhs_cluster_children,
                    )
                    cd_rhs = ch_rhs.cluster_dataset_at(
                        rhs_num_levels - num_levels + i,
                        filter_clusters=rhs_cluster_children,
                    )
                    self._match_clusters(cd_lhs, cd_rhs, matched_clusters)
            matched_levels.append(list(matched_clusters))

        # Match functions of matched clusters at all levels.
        prev_num_matches = num_matches = 0
        while True:
            for i in range(len(matched_levels) - 1, -1, -1):
                for _, lhs_cluster, _, rhs_cluster, _ in matched_levels[i]:
                    fd_lhs = ch_lhs.function_dataset_at(lhs_cluster)
                    fd_rhs = ch_rhs.function_dataset_at(rhs_cluster)
                    if use_lsh:
                        lshd_lhs = simple_lsh.simple_lsh(fd_lhs)
                        lshd_rhs = simple_lsh.simple_lsh(fd_rhs)
                        for h in set(lshd_lhs) & set(lshd_rhs):
                            num_matches += self._match_functions(
                                lshd_lhs[h], lshd_rhs[h], matched_funcs
                            )
                    num_matches += self._match_functions(fd_lhs, fd_rhs, matched_funcs)
            if prev_num_matches == num_matches:
                break
            prev_num_matches = num_matches

        return num_matches

    def diff(self) -> None:
        """Start the diffing process."""

        start_time = int(time.time())

        logger = self.logger

        logger.info("Loading dataset #1 from %s", self.lhs_path)
        dataset1 = function_dataset.load(self.lhs_path)
        logger.info("Loading dataset #2 from %s", self.rhs_path)
        dataset2 = function_dataset.load(self.rhs_path)

        match_hierarchical = self.match_hierarchical
        if match_hierarchical:
            if match_hierarchical == "louvain":
                logger.info("Building Louvain hierarhical dataset #1")
                ch_lhs = louvain_dataset.LouvainDataset(dataset1)
                logger.info("Building Louvain hierarhical dataset #2")
                ch_rhs = louvain_dataset.LouvainDataset(dataset2)
            elif match_hierarchical == "modular_decomposition":
                logger.info("Building modular decomposition hierarhical dataset #1")
                ch_lhs = modular_decomposition_dataset.ModularDecompositionDataset(
                    dataset1
                )
                logger.info("Building modular decomposition hierarhical dataset #2")
                ch_rhs = modular_decomposition_dataset.ModularDecompositionDataset(
                    dataset2
                )
            elif match_hierarchical.startswith("recover-"):
                logger.info("Building REcover hierarhical dataset #1")
                ch_lhs = recover_dataset.REcoverDataset(
                    dataset1, match_hierarchical[8:]
                )
                logger.info("Building REcover hierarhical dataset #2")
                ch_rhs = recover_dataset.REcoverDataset(
                    dataset2, match_hierarchical[8:]
                )
            else:
                raise ValueError(
                    f"Unsupported hierarchal matching algorithm {match_hierarchical}"
                )

        matches = []
        num_matches = 0

        # Create initial set of reliable matches.
        if self.match_imports:
            num_matches += self._run_matcher(
                import_matcher.ImportMatcher, dataset1, dataset2, matches
            )
        if self.match_exports:
            num_matches += self._run_matcher(
                export_matcher.ExportMatcher, dataset1, dataset2, matches
            )
        if self.match_names:
            num_matches += self._run_matcher(
                name_matcher.NameMatcher, dataset1, dataset2, matches
            )
        if self.match_imports or self.match_exports or self.match_names:
            num_matches += self._run_matchers(
                [
                    structural_matcher.ExactStructuralMatcher,
                    structural_matcher.InexactStructuralMatcher,
                    monotonic_matcher.InexactMonotonicMatcher,
                ],
                dataset1,
                dataset2,
                matches,
            )

        matched_clusters = []
        prev_num_matches = num_matches
        while dataset1 and dataset2:
            if match_hierarchical:
                logger.info("Matching hierarchical datasets")
                num_matches += self._match_hierarchical_datasets(
                    ch_lhs,
                    ch_rhs,
                    matched_clusters,
                    matches,
                    use_lsh=match_hierarchical == "louvain",
                )
            num_matches += self._run_matchers(
                _EXACT_MATCHERS, dataset1, dataset2, matches
            )
            if self.match_inexact:
                num_matches += self._run_matchers(
                    _INEXACT_MATCHERS, dataset1, dataset2, matches
                )
            if num_matches == prev_num_matches:
                break
            prev_num_matches = num_matches

        end_time = int(time.time())

        logger.info(
            "Found a total of %d matches in %d seconds",
            num_matches,
            end_time - start_time,
        )

        if not self.results_path.exists():
            self.results_path.mkdir()

        logger.info("Saving matched functions")
        with open(self.results_path / "matched.pcl", "wb") as fp:
            for match in matches:
                pickle.dump(match, fp)

        logger.info("Saving unmatched dataset #1 functions")
        with open(self.results_path / "unmatched1.pcl", "wb") as fp:
            pickle.dump(zip(dataset1.primary_keys, dataset1.names), fp)

        logger.info("Saving unmatched dataset #2 functions")
        with open(self.results_path / "unmatched2.pcl", "wb") as fp:
            pickle.dump(zip(dataset2.primary_keys, dataset2.names), fp)

        logger.info("Done")
