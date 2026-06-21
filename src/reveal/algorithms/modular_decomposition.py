# -*- coding: utf-8 -*-

from typing import Any
from collections.abc import Callable, Iterator

from reveal.graphs.hierarchy import ClusterType, Cluster, Hierarchy

from networkx import DiGraph, Graph

import collections
import dataclasses
import enum
import itertools

import networkx

from reveal.graphs.graph import Graph as MyGraph

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["get_modular_decomposition"]


Node = Cluster
NodeList = list[int | Node]
ActiveEdges = dict[int, list[int]]
LeftNodes = dict[int, bool]


@enum.unique
class NodeFlags(enum.IntFlag):
    LEFT = enum.auto()
    RIGHT = enum.auto()
    LEFT_OF_PIVOT = enum.auto()
    MARKED = enum.auto()


@dataclasses.dataclass(slots=True)
class NodeData(object):
    is_left: bool = False
    is_right: bool = False
    left_of_pivot: bool = False


def is_node(x: Any) -> bool:
    """Determine whether *x* is a valid node for the types of graphs managed by
    this module.

    We assume all graphs, in this module, hold the following types of nodes:

    * Integers representing program elements (e.g. addresses of data or code of
      the program in question).
    * Instances, or subclass instances, of :cls:`Node` representing internal
      non-leaf nodes in cotrees, MD-trees etc.

    Checks of whether a node is valid, as per the above requirements, are spread
    around in the module's code. This function makes the aforementioned check
    easily modifiable, in the event of future refactorings.

    Args:
        x: Object whose type to be checked against the valid node types.

    Returns:
        Boolean indicating whether *x* is a valid graph node type or not.
    """
    return isinstance(x, (int, Node))


class Tree(DiGraph):
    """Represents a MD-tree.

    It's called a "tree", but basically represents a forest of MD-trees. When
    the algorithm terminates, it should contain a single tree, hence the name.
    Nodes in this tree are either integers, in which case they are leaves, or
    instances of :cls:`Node`, in which case they are internal non-leaf nodes.
    Methods of this class attempt to preserve the tree invariant (i.e. that all
    nodes have at most one parent).
    """

    def root(self, node: int | Node) -> int | Node:
        """Return the root of the tree that contains *node*.

        Args:
            node: Node to start traversing upwards from.

        Returns:
            The root of tree that contains *node*.
        """
        while is_node(parent := self.parent(node)):
            node = parent
        return node

    def parent(self, node: int | Node) -> Node | None:
        """Return the unique parent of *node*, if one exists.

        Args:
            node: Node whose parent to return.

        Returns:
            The parent of *node*, or `None` if *node* has no parent.
        """
        parents = list(self.predecessors(node))
        if len(parents) > 1:
            raise ValueError(
                f"Tree invariant violation (node {node} has parents {parents})"
            )
        return next(iter(parents), None)

    def set_parent(self, node: int | Node, parent: int | Node | None) -> None:
        """Make *parent* the single parent of *node*. If *parent* is `None`, the
        existing parent is removed and *node* becomes a root node. In any case,
        the previous parent edge, if any, is removed.

        Args:
            node: Node whose parent to set/unset.
            parent: New parent node or `None`.
        """
        if is_node(prev_parent := self.parent(node)):
            self.remove_edge(prev_parent, node)
        if is_node(parent):
            self.add_edge(parent, node)

    def children(self, node: int | Node) -> NodeList:
        """Return the list of children of *node*.

        Args:
            node: Node whose children to return.

        Returns:
            List of children.
        """
        return list(self.successors(node))

    def add_child(self, parent: int | Node, child: int | Node) -> None:
        """Make *child* a child of *parent*.

        Args:
            parent: Parent node.
            child: Child node.
        """
        self.set_parent(child, parent)


def _maybe_merge(
    md_tree: Tree, root: int | Node, node_type: ClusterType, node: int | Node
) -> None:
    parent = md_tree.parent(node)
    children = md_tree.children(root)
    if isinstance(root, Node) and root.cluster_type == node_type and children:
        md_tree.remove_node(root)
        for child in children:
            md_tree.add_edge(parent, child)
    else:
        md_tree.add_edge(parent, root)


def _check_for_parallel(
    md_tree: Tree,
    forest: NodeList,
    pointers: dict[int, tuple[int, int]],
    left: int,
    right: int,
) -> bool:
    if right >= len(forest):
        return False
    i = right
    right += 1
    while i < right:
        root = forest[i]
        node_left, node_right = pointers[root]
        if node_left < left:
            return False
        if node_right > right:
            right = node_right
        i += 1
    return True


def _dfs_preorder_leaves(md_tree: Tree, root: int | Node) -> Iterator[int | None]:
    """Return a DFS ordering of the leaves of the sub-tree of *md_tree* rooted
    at *root*.

    Args:
        md_tree: The tree to traverse.
        root: The sub-tree root to start the DFS traversal from.

    Returns:
        An iterator over the leaves in DFS order.
    """
    yield from (
        node
        for node in networkx.dfs_preorder_nodes(md_tree, source=root)
        if isinstance(node, int)
    )


def _set_left_right_pointers(
    graph: Graph, md_tree: Tree, forest: NodeList
) -> dict[int, tuple[int, int]]:

    indices = dict.fromkeys(graph, -1)
    for i, node in enumerate(forest):
        if isinstance(node, Node):
            for node in _dfs_preorder_leaves(md_tree, node):
                indices[node] = i
        else:
            indices[node] = i

    pointers = {}
    for i, node in enumerate(forest):
        root = md_tree.root(node)
        nodes = list(_dfs_preorder_leaves(md_tree, root))

        adjacencies = []
        for n in nodes:
            adjacencies += list(graph.neighbors(n))

        connections = [0] * len(forest)
        max_module = -1
        for v in adjacencies:
            j = indices[v]
            if j > max_module:
                max_module = j
            connections[j] = 1

        min_module = 0
        while min_module < i and connections[min_module]:
            min_module += 1
        max_module += 1
        pointers[root] = (min_module, max_module)

    return pointers


def _is_connected_to_pivot(
    graph: Graph, md_tree: Tree, root: int | Node, pivot_neighbors: list[int]
) -> bool:
    if isinstance(root, int):
        r = root in pivot_neighbors
    else:
        r = any(
            _is_connected_to_pivot(graph, md_tree, child, pivot_neighbors)
            for child in md_tree.successors(root)
        )
    return r


def _assembly(graph: Graph, md_tree: Tree, pivot: int, forest: NodeList) -> Node:

    #
    # Add pivot in the MD-tree.
    #
    md_tree.add_node(pivot, data=NodeData())
    parent = pivot

    #
    # Add pivot node in the current forest at the appropriate index. All trees
    # connected to the pivot go to the "left" of pivot and then all trees not
    # connected to pivot go to the "right" of pivot.
    #
    pivot_neighbors = list(graph.neighbors(pivot))
    i = 1
    for i in range(1, len(forest)):
        node = forest[i]
        root = md_tree.root(node)
        if not _is_connected_to_pivot(graph, md_tree, root, pivot_neighbors):
            break
    forest.insert(i, pivot)

    pointers = _set_left_right_pointers(graph, md_tree, forest)

    current_left = i
    current_right = i + 1
    included_left = i
    included_right = i + 1

    while True:
        indices = []
        added_left = False
        added_right = False

        if _check_for_parallel(md_tree, forest, pointers, current_left, current_right):
            indices.append(current_right)
            current_right += 1
            added_right = True
        else:
            indices.append(current_left - 1)
            current_left -= 1
            added_left = True

        while indices:
            i = indices.pop(0)
            left, right = pointers[forest[i]]

            if left < current_left:
                indices += list(range(current_left - 1, left - 1, -1))
                current_left = left
                added_left = True

            if right > current_right:
                indices += list(range(current_right, right))
                current_right = right
                added_right = True

        node_type = ClusterType.PARALLEL
        if added_left and added_right:
            node_type = ClusterType.PRIME
        elif added_left:
            node_type = ClusterType.SERIES
        node = Node(node_type)
        md_tree.add_node(node, data=NodeData())
        md_tree.add_edge(node, parent)

        for i in range(current_left, included_left):
            n = forest[i]
            rn = md_tree.root(n)
            _maybe_merge(md_tree, rn, node_type, parent)

        for i in range(included_right, current_right):
            n = forest[i]
            rn = md_tree.root(n)
            _maybe_merge(md_tree, rn, node_type, parent)

        parent = node
        included_left = current_left
        included_right = current_right

        if current_left <= 0 and current_right >= len(forest):
            break

    return parent


def _clear_left_right(md_tree: Tree, node: int | Node) -> None:
    data = md_tree.nodes[node]["data"]
    data.is_left = False
    data.is_right = False
    for child in md_tree.children(node):
        _clear_left_right(md_tree, child)


def _get_promoted_tree(md_tree: Tree, node: int | Node) -> NodeList:

    forest = []

    data = md_tree.nodes[node]["data"]

    if data.is_left:
        for child in md_tree.children(node):
            child_data = md_tree.nodes[child]["data"]
            if child_data.is_left:
                md_tree.set_parent(child, None)
                forest += _get_promoted_tree(md_tree, child)

    forest.append(node)

    if data.is_right:
        for child in md_tree.children(node):
            child_data = md_tree.nodes[child]["data"]
            if child_data.is_right:
                md_tree.set_parent(child, None)
                forest += _get_promoted_tree(md_tree, child)

    return forest


def _promotion(md_tree: Tree, forest: NodeList) -> NodeList:
    roots = []
    for node in forest:
        if is_node(root := md_tree.root(node)) and root not in roots:
            roots.append(root)

    promoted_forest = []
    for root in roots:
        promoted_forest += _get_promoted_tree(md_tree, root)

    #
    # Clean-up step.
    #
    roots = []
    for node in promoted_forest:
        if is_node(root := md_tree.root(node)) and root not in roots:
            roots.append(root)

    new_promoted_forest = []
    for root in roots:
        root_data = md_tree.nodes[root]["data"]
        if root_data.is_left or root_data.is_right:
            children = md_tree.children(root)
            if children:
                if len(children) == 1:
                    md_tree.set_parent(children[0], None)
                    md_tree.remove_node(root)
                    new_promoted_forest.append(children[0])
                else:
                    new_promoted_forest.append(root)
            elif isinstance(root, int):
                new_promoted_forest.append(root)
            else:
                md_tree.remove_node(root)
        else:
            new_promoted_forest.append(root)

    for node in new_promoted_forest:
        root = md_tree.root(node)
        _clear_left_right(md_tree, root)

    return new_promoted_forest


def _mark_lr_children(md_tree: Tree, node: int | Node, left: bool) -> None:
    for child in md_tree.children(node):
        _mark_lr(md_tree, child, left)


def _mark_lr_ancestors(md_tree: Tree, node: int | Node, left: bool) -> None:
    parent = md_tree.parent(node)
    if is_node(parent):
        _mark_lr(md_tree, parent, left)
        _mark_lr_ancestors(md_tree, parent, left)


def _mark_lr(md_tree: Tree, node: int | Node, left: bool) -> None:
    data = md_tree.nodes[node]["data"]
    if left:
        data.is_left = True
    else:
        data.is_right = True


def _construct_tree(md_tree: Tree, node: int | Node, children: NodeList) -> int | Node:
    if len(children) > 1:
        root = Node(node.cluster_type)
        md_tree.add_node(root, data=NodeData())
        for child in children:
            md_tree.add_child(root, child)
    else:
        root = children[0]
        md_tree.set_parent(root, None)
    return root


def _refinement_non_prime(
    forest: NodeList,
    md_tree: Tree,
    node: int | Node,
    marked: NodeList,
    left_split: bool,
) -> None:
    a_set = []
    b_set = []

    for child in md_tree.successors(node):
        if child in marked:
            a_set.append(child)
        else:
            b_set.append(child)

    if a_set and b_set:
        a_root = _construct_tree(md_tree, node, a_set)
        b_root = _construct_tree(md_tree, node, b_set)

        parent = md_tree.parent(node)

        if is_node(parent):  # is not None
            md_tree.add_child(node, a_root)
            md_tree.add_child(node, b_root)
        else:
            root = md_tree.root(node)
            root_data = md_tree.nodes[root]["data"]
            i = forest.index(root)

            a_data = md_tree.nodes[a_root]["data"]
            a_data.is_left = root_data.is_left
            a_data.is_right = root_data.is_right
            a_data.left_of_pivot = root_data.left_of_pivot

            b_data = md_tree.nodes[b_root]["data"]
            b_data.is_left = root_data.is_left
            b_data.is_right = root_data.is_right
            b_data.left_of_pivot = root_data.left_of_pivot

            if left_split:
                forest[i] = a_root
                forest.insert(i + 1, b_root)
            else:
                forest[i] = b_root
                forest.insert(i + 1, a_root)

            md_tree.remove_node(root)

        _mark_lr(md_tree, a_root, left_split)
        _mark_lr_ancestors(md_tree, a_root, left_split)
        _mark_lr(md_tree, b_root, left_split)
        _mark_lr_ancestors(md_tree, b_root, left_split)


def _refinement_prime(md_tree: Tree, node: int | Node, left_split: bool) -> None:
    _mark_lr(md_tree, node, left_split)
    _mark_lr_ancestors(md_tree, node, left_split)
    _mark_lr_children(md_tree, node, left_split)


def _mark(md_tree: Tree, nodes: NodeList) -> NodeList:
    """Recursively mark nodes in the MD-tree.

    The list of leaf nodes, in *nodes*, is first marked. Then, the MD-tree is
    traversed "upwards" and the nodes, whose children have all been marked, are
    marked too. This process is recursively repeated until no more nodes can be
    marked.

    This function has several benefits, compared to the original implementation
    in C++:

    * Uses a queue instead of recursion and combines several C++ methods of the
      original implementation.

    * Saves memory by not requiring node attributes for storing the mark flag
      and the number of marked children for each node in the MD-tree.

    * Does not use timestamps and hence does not require a timestamp attribute
      for each node in the MD-tree.

    Args:
        md_tree: The MD-tree currently being populated.
        nodes: Leaf nodes to mark first.

    Returns:
        List of maximally marked nodes (i.e. marked nodes that either have no
        parent, or their parent is not marked).
    """

    num_marked_children = collections.defaultdict(int)
    marked = []

    #
    # Consume the nodes argument. We don't use it in the caller anyway.
    #
    while nodes:
        node = nodes.pop(0)

        #
        # For leaf nodes of the MD-tree, the following predicate is always
        # trivially true.
        #
        if md_tree.out_degree(node) == num_marked_children[node]:
            marked.append(node)
            parent = md_tree.parent(node)
            if is_node(parent):
                num_marked_children[parent] += 1
                if parent not in nodes:
                    nodes.append(parent)

    for node in marked:
        parent = md_tree.parent(node)
        if not is_node(parent) or parent not in marked:
            nodes.append(node)

    return nodes


def _refinement(
    graph: Graph,
    md_tree: Tree,
    pivot: int,
    active_edges: ActiveEdges,
    left_nodes: LeftNodes,
    forest: NodeList,
) -> None:
    """Implements the refinement step of the algorithm.

    Args:
        graph: The input graph.
        md_tree: The MD-tree currently being populated.
        pivot: The current pivot.
        active_edges: Dictionary mapping nodes of the input graph to lists of
            other nodes reachable over active edges.
        left_nodes: Dictionary mapping nodes of graph to booleans; ``True`` if
            node is to the "left" of pivot, ``False`` otherwise.
        forest: The forest of MD-trees (a list of their root nodes) as returned
            by the recursion step.
    """
    for u in (u for u in graph if u != pivot):
        marked = _mark(md_tree, [v for v in active_edges[u] if v in md_tree])

        marked_parents = []
        for v in marked:
            if is_node(parent := md_tree.parent(v)) and parent not in marked_parents:
                marked_parents.append(parent)

        for v in marked_parents:
            root = md_tree.root(v)
            data = md_tree.nodes[root]["data"]
            left_split = left_nodes[u] or data.left_of_pivot
            if v.cluster_type == ClusterType.PRIME:
                _refinement_prime(md_tree, v, left_split)
            else:
                _refinement_non_prime(forest, md_tree, v, marked, left_split)


def _recursion(
    graph: Graph, md_tree: Tree, pivot_picker: Callable
) -> tuple[int, ActiveEdges, LeftNodes, NodeList]:
    """Implements the recursion step of the algorithm.

    Args:
        graph: The input graph.
        md_tree: The MD-tree currently being populated.
        pivot_picker: Callable that returns the next pivot to use.

    Returns:
        A tuple consisting of:
        * The pivot that was selected.
        * Information on active edges (a dictionary mapping nodes of the input
          graph to lists of other nodes reachable over active edges).
        * Information on the position of nodes relative to the chosen pivot (a
          dictionary mapping nodes of graph to booleans; ``True`` if node is to
          the "left" of pivot, ``False`` otherwise).
        * The resulting forest of MD-trees (a list of their root nodes).
    """
    distances = dict.fromkeys(graph, -1)
    active_edges = {u: [] for u in graph}
    left_nodes = dict.fromkeys(graph, False)
    pivot = pivot_picker(graph)
    queue = [pivot]
    distances[pivot] = 0
    while queue:
        u = queue.pop(0)
        for v in graph.neighbors(u):
            if distances[v] == -1:
                distances[v] = distances[u] + 1
                queue.append(v)

            #
            # An edge of a graph is called active, if and only if it is adjacent
            # to pivot or connects two vertices from different $N_i$. The next
            # predicate catches both cases.
            #
            if distances[u] != distances[v]:
                active_edges[u].append(v)

            #
            # All neighbors of the pivot are placed to the "left".
            #
            if u == pivot:
                left_nodes[v] = True

    forest = []
    sorter = lambda u: distances[u]
    for distance, nodes in itertools.groupby(sorted(graph, key=sorter), sorter):
        if distance:
            subgraph = graph.subgraph(nodes)
            root = _get_modular_decomposition(subgraph, md_tree, pivot_picker)

            #
            # If forest is currently empty, this is the first MD-tree that is to
            # be added. This MD-tree corresponds to nodes at distance 1 from the
            # pivot (i.e. neighbors), so, mark its root as being to the "left".
            #
            if not forest:
                data = md_tree.nodes[root]["data"]
                data.left_of_pivot = True
            forest.append(root)

    return pivot, active_edges, left_nodes, forest


def _modular_decomposition(graph: Graph, md_tree: Tree, pivot_picker: Callable) -> Node:
    """Implements the four steps of the modular decomposition algorithm, namely,
    recursion, refinement, promotion and assembly. The input graph should be
    connected.

    Args:
        graph: The input graph.
        md_tree: The MD-tree currently being populated.
        pivot_picker: Callable that returns the next pivot to use.

    Returns:
        The root node of the MD-tree corresponding to the input graph.
    """
    pivot, active_edges, left_nodes, forest = _recursion(graph, md_tree, pivot_picker)
    _refinement(graph, md_tree, pivot, active_edges, left_nodes, forest)
    forest = _promotion(md_tree, forest)
    return _assembly(graph, md_tree, pivot, forest)


def _modular_decomposition_components(
    graph: Graph, md_tree: Tree, pivot_picker: Callable
) -> Node:
    """Construct the MD-tree of a disconnected, undirected graph.

    Basically, this function iterates through the connected components of the
    input graph and constructs the MD-tree of each component. The per-component
    MD-trees become children of a single parallel node, which corresponds to the
    root of the overall MD-tree.

    Args:
        graph: The input graph.
        md_tree: The MD-tree currently being populated.
        pivot_picker: Callable that returns the next pivot to use.

    Returns:
        The root node of the MD-tree corresponding to the input graph.
    """
    root = Node(ClusterType.PARALLEL)
    md_tree.add_node(root, data=NodeData())
    for component in networkx.connected_components(graph):
        subgraph = graph.subgraph(component)
        sub_root = _get_modular_decomposition(subgraph, md_tree, pivot_picker)
        md_tree.add_edge(root, sub_root)
    return root


def _get_modular_decomposition(
    graph: Graph, md_tree: Tree, pivot_picker: Callable
) -> int | Node:
    """Construct the modular decomposition of an undirected graph. Internal
    function that handles both connected and disconnected graphs appropriately.

    Args:
        graph: Input graph.
        md_tree: The MD-tree currently being populated.
        pivot_picker: Callable that returns the next pivot to use.

    Returns:
        The root node of the MD-tree corresponding to the input graph.
    """
    number_of_nodes = graph.number_of_nodes()
    if number_of_nodes == 0:
        raise ValueError("Graph has no vertices")
    if number_of_nodes == 1:
        root = next(iter(graph))
        md_tree.add_node(root, data=NodeData())
    elif networkx.is_connected(graph):
        root = _modular_decomposition(graph, md_tree, pivot_picker)
    else:
        root = _modular_decomposition_components(graph, md_tree, pivot_picker)
    return root


def get_modular_decomposition(
    graph: Graph, pivot_picker: Callable | None = None
) -> Hierarchy:
    """Construct the modular decomposition of an undirected graph.

    Args:
        graph: Input graph.
        pivot_picker: A callable that takes as input subgraphs of the input graph
            and returns the pivot node to be used. If ``None``, the default pivot
            picker is used, which returns the first node of the input graph as
            pivot.

    Returns:
        A tuple holding the MD-tree of the input graph and its root node.
    """
    if not pivot_picker:
        pivot_picker = lambda graph: next(iter(graph))
    md_tree = Tree()
    root = _get_modular_decomposition(
        graph if not graph.is_directed() else networkx.to_undirected(graph),
        md_tree,
        pivot_picker,
    )

    #
    # Save some memory by removing the "data" attribute from nodes of the MD-tree.
    # We don't need them any more.
    #
    for node in md_tree:
        del md_tree.nodes[node]["data"]

    dendrogram = MyGraph()

    meta_graph = MyGraph()
    meta_graph.add_nodes_from([n for n in md_tree if isinstance(n, Cluster)])

    dendrogram.add_nodes_from(meta_graph.nodes)
    for n in graph.nodes:
        p = md_tree.parent(n)
        dendrogram.add_edge(p, n)
    for s, d in graph.edges:
        s_mod = md_tree.parent(s)
        d_mod = md_tree.parent(d)
        if meta_graph.has_edge(s_mod, d_mod):
            meta_graph.edges[s_mod, d_mod]["weight"] += 1
        else:
            meta_graph.add_edge(s_mod, d_mod, weight=1)

    root = Cluster(ClusterType.PRIME)
    mg = MyGraph()
    mg.add_node(root)
    dendrogram.add_node(root)
    for n in meta_graph:
        dendrogram.add_edge(root, n)

    return Hierarchy(dendrogram, [mg, meta_graph, graph], root, 3)
