"""The plain-SQL baseline: joins and recursive CTEs with a visited-set guard.

Backed by stdlib SQLite (whose ``WITH RECURSIVE`` is standard SQL), so the painful
relational form of each graph question runs with no server and no AGE. The same
shape of query is what you would write against Postgres.
"""

import sqlite3

from src.datasets.graphs import GraphData
from src.evaluation.correctness import canonical_ring

_SCHEMA = """
CREATE TABLE nodes (node_id INTEGER PRIMARY KEY, label TEXT);
CREATE TABLE edges (src INTEGER, dst INTEGER, label TEXT);
CREATE INDEX idx_edges_src ON edges (src, label);
CREATE INDEX idx_edges_dst ON edges (dst, label);
"""

# Variable-length traversal: one recursive CTE, a visited-set guard in `path`
# so it cannot loop forever on a cycle. In SQL this is the whole story; in Cypher
# it is `MATCH (a)-[:REL*min..max]->(b)`.
_REACHABLE = """
WITH RECURSIVE walk(node, depth, path) AS (
    SELECT :start, 0, ',' || :start || ','
    UNION ALL
    SELECT e.dst, w.depth + 1, w.path || e.dst || ','
    FROM walk w
    JOIN edges e ON e.src = w.node AND e.label = :rel
    WHERE w.depth < :max_hops
      AND instr(w.path, ',' || e.dst || ',') = 0
)
SELECT DISTINCT node FROM walk
WHERE depth BETWEEN :min_hops AND :max_hops;
"""

_SHORTEST = """
WITH RECURSIVE walk(node, depth, path) AS (
    SELECT :source, 0, ',' || :source || ','
    UNION ALL
    SELECT e.dst, w.depth + 1, w.path || e.dst || ','
    FROM walk w
    JOIN edges e ON e.src = w.node AND e.label = :rel
    WHERE w.depth < :max_hops
      AND instr(w.path, ',' || e.dst || ',') = 0
)
SELECT path, depth FROM walk
WHERE node = :target
ORDER BY depth
LIMIT 1;
"""

# Cycle detection: walk from every node, allowed to close back onto its own start.
_RINGS = """
WITH RECURSIVE walk(start, node, depth, path) AS (
    SELECT n.node_id, n.node_id, 0, ',' || n.node_id || ','
    FROM nodes n
    UNION ALL
    SELECT w.start, e.dst, w.depth + 1, w.path || e.dst || ','
    FROM walk w
    JOIN edges e ON e.src = w.node AND e.label = :rel
    WHERE w.depth < :max_len
      AND (e.dst = w.start OR instr(w.path, ',' || e.dst || ',') = 0)
)
SELECT DISTINCT path FROM walk
WHERE node = start AND depth >= :min_len;
"""


def _parse_path(path: str) -> list[int]:
    """Turn a ',1,2,3,' guard string into ``[1, 2, 3]``."""
    return [int(tok) for tok in path.split(",") if tok]


class SqlGraph:
    """Load a graph into in-memory SQLite and answer graph questions in SQL."""

    def __init__(self, graph: GraphData) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(_SCHEMA)
        self.conn.executemany(
            "INSERT INTO nodes (node_id, label) VALUES (?, ?)",
            [(n.node_id, n.label) for n in graph.nodes],
        )
        self.conn.executemany(
            "INSERT INTO edges (src, dst, label) VALUES (?, ?, ?)",
            [(e.src, e.dst, e.label) for e in graph.edges],
        )
        self.conn.commit()
        self._node_count = len(graph.nodes)

    def close(self) -> None:
        self.conn.close()

    def reachable(self, start: int, min_hops: int, max_hops: int, rel: str) -> set[int]:
        """Nodes reachable from ``start`` by a simple path of length in [min, max]."""
        cur = self.conn.execute(
            _REACHABLE,
            {"start": start, "rel": rel, "min_hops": min_hops, "max_hops": max_hops},
        )
        return {row[0] for row in cur.fetchall()}

    def shortest_path(
        self, source: int, target: int, rel: str, max_hops: int | None = None
    ) -> list[int] | None:
        """A shortest path from ``source`` to ``target``, or ``None``.

        ``max_hops`` bounds the recursion. The CTE enumerates simple paths, so on a large
        connected graph an unbounded search is ruinous — bounding it is part of the SQL
        pain this project measures. Defaults to the node count (fine for small graphs).
        """
        cap = self._node_count if max_hops is None else max_hops
        cur = self.conn.execute(
            _SHORTEST,
            {"source": source, "target": target, "rel": rel, "max_hops": cap},
        )
        row = cur.fetchone()
        return _parse_path(row[0]) if row else None

    def find_rings(self, min_len: int, max_len: int, rel: str) -> set[tuple[int, ...]]:
        """All directed cycles of length in [min_len, max_len], canonicalised."""
        cur = self.conn.execute(_RINGS, {"rel": rel, "min_len": min_len, "max_len": max_len})
        found: set[tuple[int, ...]] = set()
        for (path,) in cur.fetchall():
            nodes = _parse_path(path)
            # The closing node repeats the start; drop it to get the cycle's members.
            found.add(canonical_ring(nodes[:-1]))
        return found
