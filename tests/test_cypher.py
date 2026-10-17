"""agtype parsing is pure and always runs; the live AGE check skips without a server."""

import pytest

from src.age.connect import age_available
from src.age.cypher import parse_agtype


def test_parse_scalars() -> None:
    assert parse_agtype("1") == 1
    assert parse_agtype("1.5") == 1.5
    assert parse_agtype('"hello"') == "hello"
    assert parse_agtype("true") is True
    assert parse_agtype("null") is None


def test_parse_non_string_passthrough() -> None:
    assert parse_agtype(3) == 3
    assert parse_agtype(None) is None


def test_parse_vertex() -> None:
    raw = '{"id": 1, "label": "Account", "properties": {"name": "a"}}::vertex'
    parsed = parse_agtype(raw)
    assert parsed == {"id": 1, "label": "Account", "properties": {"name": "a"}}


def test_parse_edge() -> None:
    raw = '{"id": 7, "label": "PAYS", "properties": {"amount": 5}}::edge'
    assert parse_agtype(raw)["label"] == "PAYS"


def test_parse_unparseable_returns_input() -> None:
    assert parse_agtype("not json") == "not json"


@pytest.mark.skipif(not age_available(), reason="local Postgres with AGE not available")
def test_run_cypher_against_age() -> None:
    from src.age.connect import get_connection
    from src.age.cypher import run_cypher
    from src.age.load import ensure_graph

    conn = get_connection()
    try:
        ensure_graph(conn, "cypher_smoke")
        run_cypher(conn, "cypher_smoke", "CREATE (:Account {node_id: 1})")
        rows = run_cypher(
            conn, "cypher_smoke", "MATCH (a:Account) RETURN a.node_id", columns=("node_id",)
        )
        assert [int(r[0]) for r in rows] == [1]
    finally:
        conn.close()
