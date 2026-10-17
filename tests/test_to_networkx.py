"""Subgraph extraction: row parsing is pure; the full round-trip needs AGE."""

from typing import Any

import pytest

from src.age.connect import age_available
from src.age.to_networkx import rows_to_networkx


def test_rows_to_networkx_builds_expected_graph() -> None:
    rows: list[tuple[Any, ...]] = [
        (
            {"id": 1, "label": "Account", "properties": {"name": "a"}},
            {"id": 10, "label": "PAYS", "properties": {"amount": 5}},
            {"id": 2, "label": "Account", "properties": {"name": "b"}},
        ),
        (
            {"id": 2, "label": "Account", "properties": {"name": "b"}},
            {"id": 11, "label": "PAYS", "properties": {"amount": 7}},
            {"id": 3, "label": "Account", "properties": {"name": "c"}},
        ),
    ]
    graph = rows_to_networkx(rows)
    assert set(graph.nodes) == {1, 2, 3}
    assert set(graph.edges) == {(1, 2), (2, 3)}
    assert graph.nodes[1]["label"] == "Account"
    assert graph.edges[1, 2]["label"] == "PAYS"
    assert graph.edges[1, 2]["amount"] == 5


@pytest.mark.skipif(not age_available(), reason="local Postgres with AGE not available")
def test_extracted_subgraph_matches_age(ring_graph: Any) -> None:
    from src.age.connect import get_connection
    from src.age.load import load_graph
    from src.age.to_networkx import subgraph_to_networkx

    conn = get_connection()
    try:
        load_graph(conn, "extract_test", ring_graph)
        extracted = subgraph_to_networkx(conn, "extract_test", "MATCH (a)-[r:PAYS]->(b)")
        assert extracted.number_of_edges() == len(
            [e for e in ring_graph.edges if e.label == "PAYS"]
        )
    finally:
        conn.close()
