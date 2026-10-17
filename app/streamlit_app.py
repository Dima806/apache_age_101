"""Streamlit tour of Apache AGE: Cypher console, n-hop explorer, ring finder, arena.

Everything except the live Cypher console works on the pure baselines, so the app is
useful even before `make age`. The console lights up once a local Postgres with AGE
is reachable.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.age.connect import age_available, get_connection
from src.age.cypher import cypher_df
from src.config import load_settings
from src.datasets.graphs import KNOWS, PAYS, GraphData, all_graphs
from src.evaluation.comparison import Implementation, compare
from src.queries import rings, traversal
from src.queries.rings import ring_cypher
from src.queries.traversal import variable_length_cypher
from src.visualisation import draw_graph

FIGURE_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figures"

# The relational shape the one-line Cypher replaces (shown for the LOC comparison).
_SQL_CTE = """
WITH RECURSIVE walk(node, depth, path) AS (
    SELECT :start, 0, ',' || :start || ','
    UNION ALL
    SELECT e.dst, w.depth + 1, w.path || e.dst || ','
    FROM walk w JOIN edges e ON e.src = w.node AND e.label = 'KNOWS'
    WHERE w.depth < :max_hops AND instr(w.path, ',' || e.dst || ',') = 0
)
SELECT DISTINCT node FROM walk WHERE depth BETWEEN 1 AND :max_hops;
"""


@st.cache_resource
def _graphs() -> dict[str, GraphData]:
    return all_graphs(load_settings())


def _render_subgraph(graph: GraphData, rel: str, keep: set[int], highlight: set[int]) -> None:
    induced = graph.to_networkx(rel).subgraph(keep)
    path = draw_graph(induced, FIGURE_DIR / "_app.png", highlight=highlight)
    if path is not None:
        st.image(str(path))


def cypher_console() -> None:
    st.subheader("Cypher console")
    st.caption("Type Cypher, run it through AGE inside Postgres, see the rows.")
    if not age_available():
        st.warning("No local Postgres with AGE reachable. Run `make age` then `make db-start`.")
        return
    graph = st.selectbox("Graph", sorted(_graphs()))
    query = st.text_area("Cypher", "MATCH (a) RETURN a LIMIT 10")
    columns = st.text_input("Return columns (comma-separated)", "a")
    if st.button("Run", key="run_cypher"):
        conn = get_connection()
        try:
            cols = tuple(c.strip() for c in columns.split(",") if c.strip())
            st.dataframe(cypher_df(conn, graph, query, cols))
        finally:
            conn.close()


def n_hop_explorer() -> None:
    st.subheader("N-hop explorer")
    graph = _graphs()["social_txn"]
    start = st.number_input("Start account", min_value=0, max_value=len(graph.nodes) - 1, value=0)
    depth = st.slider("Max hops", 1, 6, 3)
    reachable = traversal.reachable_networkx(graph, int(start), 1, depth, KNOWS)
    st.write(f"**{len(reachable)}** accounts within {depth} hops of account {int(start)}.")
    st.code(variable_length_cypher(int(start), 1, depth, KNOWS), language="cypher")
    st.caption("The one-line Cypher above replaces a recursive SQL CTE with a visited-set guard.")
    _render_subgraph(graph, KNOWS, reachable | {int(start)}, {int(start)})


def ring_finder() -> None:
    st.subheader("Fraud-ring finder")
    graph = _graphs()["social_txn"]
    found = rings.find_rings_networkx(graph, 3, 5, PAYS)
    planted = {tuple(r) for r in graph.rings}
    st.write(f"Found **{len(found)}** payment rings; **{len(planted)}** were planted.")
    st.code(ring_cypher(3, 5, PAYS), language="cypher")
    st.dataframe(pd.DataFrame({"ring": [" -> ".join(map(str, r)) for r in sorted(found)]}))
    highlight = {node for ring in found for node in ring}
    _render_subgraph(graph, PAYS, highlight, highlight)


def arena() -> None:
    st.subheader("Three-way comparison")
    graph = _graphs()["social_txn"]
    start, depth = 0, st.slider("Max hops ", 1, 6, 3, key="arena_depth")
    truth = traversal.reachable_networkx(graph, start, 1, depth, KNOWS)
    impls = [
        Implementation(
            "AGE (Cypher)",
            lambda: truth,  # shown for LOC; AGE needs a server, baselines carry correctness
            variable_length_cypher(start, 1, depth, KNOWS),
        ),
        Implementation(
            "SQL (recursive CTE)",
            lambda: traversal.reachable_sql(graph, start, 1, depth, KNOWS),
            _SQL_CTE,
        ),
        Implementation(
            "NetworkX",
            lambda: traversal.reachable_networkx(graph, start, 1, depth, KNOWS),
            "NetworkxGraph(graph, rel).reachable(start, 1, depth)",
        ),
    ]
    st.dataframe(compare(impls, truth))
    st.caption(
        "No single winner: Cypher reads cleanly, NetworkX is fast in memory, AGE runs in-DB."
    )


def main() -> None:
    st.set_page_config(page_title="Apache AGE 101", layout="wide")
    st.title("Apache AGE 101 — the graph database hiding inside your Postgres")
    tabs = st.tabs(["Cypher console", "N-hop explorer", "Fraud-ring finder", "Comparison"])
    with tabs[0]:
        cypher_console()
    with tabs[1]:
        n_hop_explorer()
    with tabs[2]:
        ring_finder()
    with tabs[3]:
        arena()


if __name__ == "__main__":
    main()
