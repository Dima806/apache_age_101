"""N-hop and variable-length traversal in Cypher, SQL, and NetworkX.

The whole point of the first showpiece: variable length is one Cypher pattern,
``MATCH (a)-[:REL*min..max]->(b)``, versus a recursive CTE with a visited-set guard.
"""

from typing import Any

import psycopg

from src.age.cypher import run_cypher
from src.baselines.networkx_graph import NetworkxGraph
from src.baselines.sql_recursive import SqlGraph
from src.datasets.graphs import GraphData


def variable_length_cypher(
    start: int, min_hops: int, max_hops: int, rel: str, label: str = "Account"
) -> str:
    """The one-line Cypher pattern for variable-length reachability."""
    return (
        f"MATCH (a:{label} {{node_id: {start}}})-[:{rel}*{min_hops}..{max_hops}]->(b) "
        "RETURN DISTINCT b.node_id"
    )


def reachable_age(
    conn: psycopg.Connection[Any],
    graph: str,
    start: int,
    min_hops: int,
    max_hops: int,
    rel: str,
    label: str = "Account",
) -> set[int]:
    """Variable-length reachability through AGE."""
    query = variable_length_cypher(start, min_hops, max_hops, rel, label)
    rows = run_cypher(conn, graph, query, columns=("node_id",))
    return {int(row[0]) for row in rows}


def reachable_sql(
    graph: GraphData, start: int, min_hops: int, max_hops: int, rel: str
) -> set[int]:
    """Variable-length reachability via the SQL recursive CTE."""
    sql_graph = SqlGraph(graph)
    try:
        return sql_graph.reachable(start, min_hops, max_hops, rel)
    finally:
        sql_graph.close()


def reachable_networkx(
    graph: GraphData, start: int, min_hops: int, max_hops: int, rel: str
) -> set[int]:
    """Variable-length reachability in NetworkX."""
    return NetworkxGraph(graph, rel).reachable(start, min_hops, max_hops)
