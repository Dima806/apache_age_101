"""Shortest path in Cypher, a recursive SQL CTE, and NetworkX."""

from typing import Any

import psycopg

from src.age.cypher import run_cypher
from src.baselines.networkx_graph import NetworkxGraph
from src.baselines.sql_recursive import SqlGraph
from src.datasets.graphs import GraphData


def shortest_path_cypher(
    source: int, target: int, rel: str, label: str = "Account", max_hops: int = 10
) -> str:
    """Cypher for the shortest path between two nodes.

    The variable-length match is **bounded** (``*1..max_hops``). AGE has no early-stopping
    shortest-path operator — it enumerates matching paths and we take the shortest — so an
    unbounded ``*`` explores every path and is ruinous on a dense graph. Returns
    ``nodes(p)`` (AGE does not support property access inside a list comprehension).
    """
    return (
        f"MATCH p = (a:{label} {{node_id: {source}}})-[:{rel}*1..{max_hops}]->"
        f"(b:{label} {{node_id: {target}}}) "
        "RETURN nodes(p) AS path ORDER BY length(p) LIMIT 1"
    )


def shortest_path_age(
    conn: psycopg.Connection[Any],
    graph: str,
    source: int,
    target: int,
    rel: str,
    label: str = "Account",
    max_hops: int = 10,
) -> list[int] | None:
    """Shortest path through AGE, or ``None`` if unreachable (``max_hops`` bounds it)."""
    query = shortest_path_cypher(source, target, rel, label, max_hops)
    rows = run_cypher(conn, graph, query, columns=("path",))
    if not rows:
        return None
    return [int(vertex["properties"]["node_id"]) for vertex in rows[0][0]]


def shortest_path_sql(
    graph: GraphData, source: int, target: int, rel: str, max_hops: int | None = None
) -> list[int] | None:
    """Shortest path via the recursive SQL CTE (``max_hops`` bounds the search)."""
    sql_graph = SqlGraph(graph)
    try:
        return sql_graph.shortest_path(source, target, rel, max_hops)
    finally:
        sql_graph.close()


def shortest_path_networkx(
    graph: GraphData, source: int, target: int, rel: str
) -> list[int] | None:
    """Shortest path in NetworkX."""
    return NetworkxGraph(graph, rel).shortest_path(source, target)
