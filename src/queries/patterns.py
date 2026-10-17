"""Co-occurrence, reachability, and impact-analysis patterns."""

import networkx as nx

from src.baselines.networkx_graph import NetworkxGraph
from src.baselines.sql_recursive import SqlGraph
from src.datasets.graphs import BOUGHT, DEPENDS_ON, GraphData


def impact_networkx(graph: GraphData, component: int, rel: str = DEPENDS_ON) -> set[int]:
    """Everything (transitively) affected if ``component`` fails."""
    return set(nx.descendants(NetworkxGraph(graph, rel).graph, component))


def impact_sql(graph: GraphData, component: int, rel: str = DEPENDS_ON) -> set[int]:
    """Impact set via the SQL recursive CTE (reachability to any depth)."""
    sql_graph = SqlGraph(graph)
    try:
        return sql_graph.reachable(component, 1, len(graph.nodes), rel)
    finally:
        sql_graph.close()


def co_purchased_items(graph: GraphData, user: int, rel: str = BOUGHT) -> set[int]:
    """Two-hop co-purchase recommendation: items bought by co-purchasers, minus own."""
    directed = graph.to_networkx(rel)
    own_items = set(directed.successors(user))
    co_purchasers: set[int] = set()
    for item in own_items:
        co_purchasers.update(directed.predecessors(item))
    co_purchasers.discard(user)
    recommended: set[int] = set()
    for other in co_purchasers:
        recommended.update(directed.successors(other))
    return recommended - own_items
