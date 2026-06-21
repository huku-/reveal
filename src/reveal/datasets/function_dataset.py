"""Function datasets."""

from pathlib import Path

from reveal.types import Comparable
from reveal.datasets.dataset import Dataset
from reveal.features.features import FeatureVectorValue
from reveal.graphs.graph import Graph

from reveal.features import function_features

import pickle

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["FunctionDataset", "load"]


class FunctionDataset(Dataset):

    def __init__(
        self,
        graph: Graph,
        primary_keys: list[Comparable],
        names: list[str],
        rows: list[FeatureVectorValue],
        parent: Dataset | None = None,
        path: str | Path | None = None,
    ) -> None:
        super().__init__(graph, primary_keys, names, rows, parent=parent)
        if isinstance(path, str):
            path = Path(path)
        self.path = path


def load(path: str | Path) -> FunctionDataset:
    """Load function dataset from *path*.

    Args:
        path: Absolute path to exported function dataset.

    Returns:
        Loaded function dataset.
    """

    if isinstance(path, str):
        path = Path(path)

    with open(path / "fcg.pcl", "rb") as fp:
        graph = pickle.load(fp)

    primary_keys = []
    names = []
    rows = []

    with open(path / "fvs.pcl", "rb") as fp:
        while True:
            try:
                ent = pickle.load(fp)
                primary_keys.append(ent[0])
                names.append(ent[1])
                row = ent[2:]
                rows.append(function_features.FunctionFeatureVector.unflatten(row))
            except EOFError:
                break
    return FunctionDataset(graph, primary_keys, names, rows, path=path)
