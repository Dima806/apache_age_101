"""N-hop / variable-length traversal and shortest path: SQL and NetworkX must agree.

The AGE arm is asserted here only when a server is present; the baselines carry the
lesson otherwise (the "baselines run without AGE" requirement).
"""

import pytest

from src.age.connect import age_available
from src.datasets.graphs import KNOWS, GraphData
from src.evaluation.correctness import sets_agree
from src.queries import traversal
from src.queries.paths import shortest_path_networkx, shortest_path_sql


@pytest.mark.parametrize(
    ("min_hops", "max_hops", "expected"),
    [
        (1, 1, {1}),
        (2, 2, {2, 4}),
        (3, 3, {3}),
        (1, 3, {1, 2, 3, 4}),
    ],
)
def test_reachable_matches_truth(
    knows_graph: GraphData, min_hops: int, max_hops: int, expected: set[int]
) -> None:
    sql = traversal.reachable_sql(knows_graph, 0, min_hops, max_hops, KNOWS)
    nx_result = traversal.reachable_networkx(knows_graph, 0, min_hops, max_hops, KNOWS)
    assert sql == expected
    assert nx_result == expected
    assert sets_agree(sql, nx_result, expected)


def test_shortest_path_agrees(knows_graph: GraphData) -> None:
    sql = shortest_path_sql(knows_graph, 0, 3, KNOWS)
    nx_result = shortest_path_networkx(knows_graph, 0, 3, KNOWS)
    assert sql is not None and nx_result is not None
    assert sql[0] == 0 and sql[-1] == 3
    assert len(sql) == len(nx_result) == 4  # 0 -> _ -> _ -> 3, three hops


def test_shortest_path_unreachable(knows_graph: GraphData) -> None:
    assert shortest_path_sql(knows_graph, 3, 0, KNOWS) is None
    assert shortest_path_networkx(knows_graph, 3, 0, KNOWS) is None


@pytest.mark.skipif(not age_available(), reason="local Postgres with AGE not available")
def test_reachable_age_agrees(knows_graph: GraphData) -> None:
    from src.age.connect import get_connection
    from src.age.load import load_graph

    conn = get_connection()
    try:
        load_graph(conn, "traversal_test", knows_graph)
        age = traversal.reachable_age(conn, "traversal_test", 0, 1, 3, KNOWS)
        nx_result = traversal.reachable_networkx(knows_graph, 0, 1, 3, KNOWS)
        assert age == nx_result == {1, 2, 3, 4}
    finally:
        conn.close()


@pytest.mark.skipif(not age_available(), reason="local Postgres with AGE not available")
def test_shortest_path_age_agrees(knows_graph: GraphData) -> None:
    from src.age.connect import get_connection
    from src.age.load import load_graph
    from src.queries.paths import shortest_path_age

    conn = get_connection()
    try:
        load_graph(conn, "paths_test", knows_graph)
        age = shortest_path_age(conn, "paths_test", 0, 3, KNOWS)
        nx_result = shortest_path_networkx(knows_graph, 0, 3, KNOWS)
        assert age is not None and nx_result is not None
        assert age[0] == 0 and age[-1] == 3
        assert len(age) == len(nx_result)  # same shortest-path length
    finally:
        conn.close()
