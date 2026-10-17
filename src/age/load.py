"""Load the synthetic graphs into AGE (and keep them as the SQL baseline's rows).

The graph and the relational data are the same records in the same database,
queried two ways. Run via ``make load`` / ``python -m src.age.load`` — needs a
local Postgres with AGE; not part of ``make ci``.
"""

import contextlib
from typing import Any

import psycopg

from src.age.connect import get_connection
from src.age.cypher import run_cypher
from src.config import Settings, load_settings
from src.datasets.graphs import GraphData, all_graphs


def _cypher_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _cypher_props(props: dict[str, Any]) -> str:
    if not props:
        return ""
    inner = ", ".join(f"{key}: {_cypher_value(val)}" for key, val in props.items())
    return f" {{{inner}}}"


def ensure_graph(conn: psycopg.Connection[Any], name: str) -> None:
    """Drop and recreate an AGE graph so loading is idempotent."""
    with contextlib.suppress(psycopg.Error):
        conn.execute("SELECT drop_graph(%s, true);", (name,))
    conn.execute("SELECT create_graph(%s);", (name,))


def load_graph(conn: psycopg.Connection[Any], name: str, data: GraphData) -> None:
    """Create every vertex and edge of ``data`` in the AGE graph ``name``."""
    ensure_graph(conn, name)
    for node in data.nodes:
        props = _cypher_props({"node_id": node.node_id, **node.props})
        run_cypher(conn, name, f"CREATE (:{node.label}{props})")
    for edge in data.edges:
        run_cypher(
            conn,
            name,
            f"MATCH (a {{node_id: {edge.src}}}), (b {{node_id: {edge.dst}}}) "
            f"CREATE (a)-[:{edge.label}]->(b)",
        )


def main(settings: Settings | None = None) -> None:
    """Load every dataset into its AGE graph."""
    settings = settings or load_settings()
    conn = get_connection(settings)
    try:
        for name, data in all_graphs(settings).items():
            load_graph(conn, name, data)
            print(f"loaded {name}: {len(data.nodes)} nodes, {len(data.edges)} edges")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
