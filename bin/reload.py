# -*- coding: utf-8 -*-

from types import ModuleType
from networkx import DiGraph

import importlib

import networkx
import reveal


def enum_modules(module: ModuleType, graph: DiGraph) -> None:
    graph.add_node(module)
    for name in dir(module):
        member = getattr(module, name)
        if (
            isinstance(member, ModuleType)
            and member.__name__.startswith(module.__name__)
            and member not in graph
        ):
            graph.add_edge(module, member)
            enum_modules(member, graph)


def main() -> None:
    graph = DiGraph()
    enum_modules(reveal, graph)
    for module in networkx.dfs_postorder_nodes(graph, reveal):
        print(f"Reloading {module.__name__}")
        importlib.reload(module)


if __name__ == "__main__":
    main()
