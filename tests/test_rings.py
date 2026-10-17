"""Planted fraud rings must be found by every approach (the core correctness bar)."""

import pytest

from src.age.connect import age_available
from src.config import DatasetSettings, Settings
from src.datasets.graphs import PAYS, GraphData, social_transaction_graph
from src.evaluation.correctness import all_rings_found, rings_to_canonical
from src.queries.rings import find_rings_networkx, find_rings_sql


def test_planted_ring_found_in_tiny_graph(ring_graph: GraphData) -> None:
    sql = find_rings_sql(ring_graph, 3, 5, PAYS)
    nx_result = find_rings_networkx(ring_graph, 3, 5, PAYS)
    expected = rings_to_canonical(ring_graph.rings)
    assert sql == expected
    assert nx_result == expected
    assert all_rings_found(sql, ring_graph.rings)


def test_generated_rings_recovered_exactly() -> None:
    # Small, so the recursive SQL cycle search stays fast.
    settings = Settings(
        dataset=DatasetSettings(
            seed=11,
            n_accounts=60,
            n_communities=3,
            n_rings=4,
            ring_min_len=3,
            ring_max_len=4,
            avg_knows_degree=3,
            avg_pays_degree=2,
        )
    )
    graph = social_transaction_graph(settings)
    assert graph.rings, "generator should plant rings"

    planted = rings_to_canonical(graph.rings)
    sql = find_rings_sql(graph, 3, 5, PAYS)
    nx_result = find_rings_networkx(graph, 3, 5, PAYS)

    # Construction guarantees the planted rings are the ONLY cycles in PAYS.
    assert planted == sql == nx_result


@pytest.mark.skipif(not age_available(), reason="local Postgres with AGE not available")
def test_rings_age_agrees(ring_graph: GraphData) -> None:
    from src.age.connect import get_connection
    from src.age.load import load_graph
    from src.queries.rings import find_rings_age

    conn = get_connection()
    try:
        load_graph(conn, "rings_test", ring_graph)
        age = find_rings_age(conn, "rings_test", 3, 5, PAYS)
        assert all_rings_found(age, ring_graph.rings)
    finally:
        conn.close()
