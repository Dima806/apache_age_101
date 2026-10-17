"""The same graph in memory as a NetworkX DiGraph, plus the traversal baseline."""

import networkx as nx

from src.datasets.graphs import GraphData
from src.evaluation.correctness import canonical_ring


class NetworkxGraph:
    """In-memory baseline: traversal and pathfinding over a NetworkX DiGraph."""

    def __init__(self, graph: GraphData, rel: str | None = None) -> None:
        self.graph: nx.DiGraph = graph.to_networkx(rel)

    def reachable(self, start: int, min_hops: int, max_hops: int) -> set[int]:
        """Endpoints of simple paths from ``start`` whose length is in [min, max].

        Mirrors the SQL recursive CTE (visited-set guard = simple paths), so the two
        baselines agree exactly.
        """
        result: set[int] = set()
        stack: list[tuple[int, int, frozenset[int]]] = [(start, 0, frozenset({start}))]
        while stack:
            node, depth, visited = stack.pop()
            if min_hops <= depth <= max_hops:
                result.add(node)
            if depth >= max_hops:
                continue
            for nbr in self.graph.successors(node):
                if nbr not in visited:
                    stack.append((nbr, depth + 1, visited | {nbr}))
        return result

    def shortest_path(self, source: int, target: int) -> list[int] | None:
        """A shortest path (unit weights) or ``None`` if unreachable."""
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def find_rings(self, min_len: int, max_len: int) -> set[tuple[int, ...]]:
        """All simple directed cycles with length in [min_len, max_len], canonicalised."""
        found: set[tuple[int, ...]] = set()
        for cycle in nx.simple_cycles(self.graph, length_bound=max_len):
            if min_len <= len(cycle) <= max_len:
                found.add(canonical_ring(cycle))
        return found

    def pagerank(self) -> dict[int, float]:
        """PageRank — the analytics AGE has no built-in for (the honest limit)."""
        return nx.pagerank(self.graph)
