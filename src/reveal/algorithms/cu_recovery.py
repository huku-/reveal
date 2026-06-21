# -*- coding: utf-8 -*-

from reveal import util
from reveal.graphs.graph import Graph
from reveal.graphs.hierarchy import Cluster, ClusterType, Hierarchy

from recover import cu_map

import logging

import recover


def get_recover_hierarchy(dataset, estimator: str) -> Hierarchy:
    path = util.to_path(dataset.path)

    if (
        not (path / "afcg.pcl").exists()
        or not (path / "dfg.pcl").exists()
        or not (path / "pdg.pcl").exists()
        or not (path / "segs.pcl").exists()
    ):
        raise FileNotFoundError("REcover export data not found")

    if not (path / f"cu_map-{estimator}-brute_fast.pcl").exists():
        logging.info("Running REcover analysis %s / brute_fast", estimator)
        recover.analyze(
            path,
            estimator=estimator,
            optimizer="brute_fast",
            pickle_path=path / "cu_map-apsnse-brute_fast.pcl",
        )

    dendrogram = Graph()

    cm = cu_map.CUMap.load(path / f"cu_map-{estimator}-brute_fast.pcl")

    cug = Graph()
    for cu in cm.get_cus():
        c = Cluster(ClusterType.PRIME)
        cug.add_node(c)
        dendrogram.add_node(c)
        for ea in cu.get_func_eas():
            dendrogram.add_edge(c, ea)

    for cu in cm.get_cus():
        for ea in cu.get_func_eas():
            s_cu = list(dendrogram.predecessors(ea))[0]
            for succ_ea in dataset.graph.successors(ea):
                if succ_ea in dendrogram:
                    d_cu = list(dendrogram.predecessors(succ_ea))[0]
                    if cug.has_edge(s_cu, d_cu):
                        cug.edges[s_cu, d_cu]["weight"] += 1
                    else:
                        cug.add_edge(s_cu, d_cu, weight=1)

    root = Cluster(ClusterType.PRIME)
    mg = Graph()
    mg.add_node(root)
    dendrogram.add_node(root)
    for n in cug:
        dendrogram.add_edge(root, n)

    return Hierarchy(dendrogram, [mg, cug, dataset.graph], root, 3)
