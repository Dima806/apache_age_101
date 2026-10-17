"""Pull a subgraph out of AGE with Cypher and hand it to NetworkX.

This is the bridge for the honest-limit chapter: AGE traverses and extracts, Python
analyses. ``rows_to_networkx`` is pure (no DB), so it is unit-testable on its own.
"""

from collections.abc import Iterable
from typing import Any

import networkx as nx
import psycopg

from src.age.cypher import run_cypher


def _add_vertex(graph: nx.DiGraph, vertex: dict[str, Any]) -> None:
    graph.add_node(vertex["id"], label=vertex.get("label"), **(vertex.get("properties") or {}))


def rows_to_networkx(rows: Iterable[tuple[Any, ...]]) -> nx.DiGraph:
    """Build a DiGraph from ``(start_vertex, edge, end_vertex)`` agtype rows."""
    graph: nx.DiGraph = nx.DiGraph()
    for row in rows:
        start, edge, end = row[0], row[1], row[2]
        _add_vertex(graph, start)
        _add_vertex(graph, end)
        graph.add_edge(
            start["id"], end["id"], label=edge.get("label"), **(edge.get("properties") or {})
        )
    return graph


def subgraph_to_networkx(
    conn: psycopg.Connection[Any],
    graph: str,
    match: str = "MATCH (a)-[r]->(b)",
) -> nx.DiGraph:
    """Extract a subgraph via one Cypher query and return it as a NetworkX DiGraph."""
    rows = run_cypher(conn, graph, f"{match} RETURN a, r, b", columns=("a", "r", "b"))
    return rows_to_networkx(rows)
