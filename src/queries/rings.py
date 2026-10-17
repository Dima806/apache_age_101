"""Cycle / ring detection: the fraud-ring showpiece (A pays B pays C pays back to A)."""

from typing import Any

import psycopg

from src.age.cypher import run_cypher
from src.baselines.networkx_graph import NetworkxGraph
from src.baselines.sql_recursive import SqlGraph
from src.datasets.graphs import GraphData
from src.evaluation.correctness import canonical_ring


def ring_cypher(min_len: int, max_len: int, rel: str, label: str = "Account") -> str:
    """Cypher pattern that finds cycles of a bounded length.

    Returns ``nodes(p)`` (the whole vertex list) rather than a list comprehension over
    ``n.node_id``; AGE does not support property access inside a comprehension.
    """
    return f"MATCH p = (a:{label})-[:{rel}*{min_len}..{max_len}]->(a) RETURN nodes(p) AS ring"


def find_rings_age(
    conn: psycopg.Connection[Any],
    graph: str,
    min_len: int,
    max_len: int,
    rel: str,
    label: str = "Account",
) -> set[tuple[int, ...]]:
    """Find all bounded-length rings through AGE, canonicalised."""
    rows = run_cypher(conn, graph, ring_cypher(min_len, max_len, rel, label), columns=("ring",))
    found: set[tuple[int, ...]] = set()
    for row in rows:
        node_ids = [int(vertex["properties"]["node_id"]) for vertex in row[0]]
        # AGE closes the path on the start node; drop the repeat before canonicalising.
        found.add(canonical_ring(node_ids[:-1]))
    return found


def find_rings_sql(graph: GraphData, min_len: int, max_len: int, rel: str) -> set[tuple[int, ...]]:
    """Find all bounded-length rings via the recursive SQL CTE."""
    sql_graph = SqlGraph(graph)
    try:
        return sql_graph.find_rings(min_len, max_len, rel)
    finally:
        sql_graph.close()


def find_rings_networkx(
    graph: GraphData, min_len: int, max_len: int, rel: str
) -> set[tuple[int, ...]]:
    """Find all bounded-length rings in NetworkX."""
    return NetworkxGraph(graph, rel).find_rings(min_len, max_len)
