"""``run_cypher`` — the single adapter that runs Cypher inside Postgres.

AGE exposes Cypher as ``SELECT * FROM cypher(graph, $$ ... $$) AS (col agtype, ...)``.
This wraps that call and parses AGE's ``agtype`` results into plain Python / pandas.
"""

import json
import re
from collections.abc import Sequence
from typing import Any, LiteralString, cast

import pandas as pd
import psycopg

# agtype tags entities with a type suffix (also inside lists/paths) that is not JSON.
_AGTYPE_TAG = re.compile(r"::(?:vertex|edge|path)")


def parse_agtype(value: Any) -> Any:
    """Turn one agtype cell into a Python scalar / dict / list.

    Vertices and edges arrive as ``{...}::vertex`` / ``{...}::edge`` (and a list of
    them, e.g. ``nodes(path)``, carries the tag on each element); scalars arrive as
    JSON. Tags are stripped everywhere before parsing; unparseable text is returned
    unchanged.
    """
    if not isinstance(value, str):
        return value
    cleaned = _AGTYPE_TAG.sub("", value)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return value


def run_cypher(
    conn: psycopg.Connection[Any],
    graph: str,
    query: str,
    columns: Sequence[str] = ("v",),
) -> list[tuple[Any, ...]]:
    """Run one Cypher ``query`` against ``graph`` and return parsed rows.

    ``columns`` names the ``RETURN`` columns; each is declared ``agtype`` as AGE
    requires. The graph name comes from trusted config, so it is inlined.
    """
    col_defs = ", ".join(f"{name} agtype" for name in columns)
    sql = f"SELECT * FROM cypher('{graph}', $$ {query} $$) AS ({col_defs})"
    with conn.cursor() as cur:
        # AGE's cypher() call cannot be parameterized; graph/query come from trusted
        # config and project code, so the dynamically-built statement is safe here.
        cur.execute(cast(LiteralString, sql))
        rows = cur.fetchall()
    return [tuple(parse_agtype(cell) for cell in row) for row in rows]


def cypher_df(
    conn: psycopg.Connection[Any],
    graph: str,
    query: str,
    columns: Sequence[str] = ("v",),
) -> pd.DataFrame:
    """Same as :func:`run_cypher`, returned as a pandas DataFrame."""
    return pd.DataFrame(run_cypher(conn, graph, query, columns), columns=list(columns))
