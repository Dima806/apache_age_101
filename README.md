# apache_age_101

> A hands-on introduction to **Apache AGE**, the extension that turns the PostgreSQL you already run
> into a graph database — on CPU, with a single local Postgres instance and **no cloud, no account,
> and no second database to operate**.

A large share of real data lives in PostgreSQL, and a large share of real questions about it are
graph-shaped: *how are these two accounts connected, is there a payment ring, who is three hops away,
what breaks if this supplier fails.* SQL answers these badly — a four-hop question is four self-joins,
and a variable-length one is a recursive CTE with a visited-set guard. The usual reaction is to stand
up Neo4j and copy the data over. Apache AGE offers a third path: run **openCypher inside the Postgres
you already have**.

```cypher
-- "accounts within six hops of this one" — one line, next to your tables
MATCH (a:Account {node_id: 0})-[:KNOWS*1..6]->(b) RETURN DISTINCT b.node_id
```

## The idea, in one breath

- Multi-hop traversal is `MATCH (a)-[:REL*1..6]->(b)` in Cypher, versus a dozen-plus lines of
  recursive SQL. **Same database, no ETL.**
- A fraud ring (A pays B pays C pays back to A) is ~impossible in relational algebra and a short
  `MATCH (a)-[:PAYS*3..5]->(a)` pattern in AGE.
- **The honest limit:** AGE is a *pattern-matching and pathfinding engine, not a graph-analytics
  library.* No built-in PageRank, communities, or centrality. The productive workflow is **traverse
  in AGE → extract the subgraph → compute in NetworkX → write the scores back**.

Every graph question is answered **three ways** — Cypher (AGE), plain SQL (recursive CTE), and
NetworkX — and scored on readability, correctness (against *planted* truth), and runtime.

## Quickstart (2-CPU / 8 GB Codespace)

```bash
make setup      # Python env (uv sync --all-extras) + register the Jupyter kernel
make age        # ONE-TIME: install local Postgres + build Apache AGE + CREATE EXTENSION (local only)
make db-start   # start the local Postgres service (also after a Codespace restart)
make load       # generate the planted graphs and load them into AGE (+ relational rows)
make test       # assert every answer matches planted truth and agrees across AGE/SQL/NetworkX
make notebooks  # execute all six notebooks end to end
make run        # launch the Streamlit app
```

The **one honest exception** to the "no server" spirit of these 101 projects: AGE is a PostgreSQL
*extension*, so this runs one **local** Postgres (no cloud, no account, no API key). `make age`
installs it and builds the matching AGE release from source with **no interactive password**; the
`apache/age` Docker image is noted as a zero-build fallback. If AGE is not available, notebooks 02
and 04–06 still teach their lessons on the pure SQL/NetworkX baselines.

## The notebooks

| # | Notebook | What it shows |
|---|----------|---------------|
| 01 | Graphs Live in Your Database | Connect, run Cypher next to SQL on the same data; the node/edge/property/label vocabulary |
| 02 | The N-Hop Join Problem | 1 → 4 → variable-length reachability; one-line Cypher vs a recursive CTE; LOC measured |
| 03 | Fraud Rings and Pathfinding | Cycle detection finds every planted ring; shortest path, all inside the transaction DB |
| 04 | AGE vs SQL vs NetworkX | The arena: readability, correctness vs planted truth, runtime vs depth |
| 05 | Graph Algorithms, the Honest Limit | AGE has no PageRank → extract → NetworkX → write scores back → read back |
| 06 | Decision Framework | When to use SQL, AGE, NetworkX/igraph, or a dedicated graph DB |

Every notebook saves its **figures as PNG** under [`outputs/figures/`](outputs/figures) and its
**textual/numerical results as JSON** under [`outputs/data/`](outputs/data), ready for the companion
article.

## Project layout

```
src/age/          connect (LOAD age + search_path) · cypher (run_cypher + agtype parsing)
                  load (tables → AGE graph) · to_networkx (extract an AGE subgraph → NetworkX)
src/baselines/    sql_recursive (recursive CTEs on SQLite, visited-set guard) · networkx_graph
src/queries/      traversal · paths · rings · patterns  (each: Cypher | SQL | NetworkX)
src/datasets/     graphs.py — synthetic graphs with PLANTED rings/paths/communities
src/evaluation/   correctness · readability · runtime · comparison (the arena harness)
src/visualisation.py · src/outputs.py   graph drawing · PNG/JSON persistence helpers
app/streamlit_app.py   Cypher console · n-hop explorer · fraud-ring finder · three-way comparison
notebooks/01..06  the narrative above            scripts/  install_age.sh · init_db.sql
tests/            cypher · traversal · rings · to_networkx (AGE tests skip without a server)
config/settings.yaml   DB connection, graph names, dataset sizes, seeds
```

## Decision framework

| Use… | When |
|------|------|
| **plain SQL** | shallow 1–2 hop relationships you already query relationally |
| **Apache AGE** | multi-hop traversal, path patterns, or cycle detection on data **already in Postgres** |
| **NetworkX / igraph** | the graph fits in memory and you need graph *algorithms* (PageRank, communities) |
| **Neo4j + GDS** | very large graphs, heavy graph OLTP, or a mature built-in algorithms library |

…and the combined sweet spot: **keep the graph in AGE next to your tables, pull subgraphs into Python
for the heavy algorithms.** AGE is also just a Postgres extension, so **pgvector** can live in the
same database — graph traversal and vector search over one store.

## Related projects

Part of a series of hands-on data-science projects by [Dima806](https://github.com/Dima806):

- [`graphrag_vs_vectorrag`](https://github.com/Dima806/graphrag_vs_vectorrag) — Graph RAG vs vector
  RAG. The knowledge graph can live in AGE, with pgvector beside it for hybrid retrieval.
- [`gnn_101`](https://github.com/Dima806/gnn_101) — Intro to graph neural networks; AGE is a natural
  storage-and-query layer for the graphs GNNs learn on.
- [`geo_distance_arena`](https://github.com/Dima806/geo_distance_arena) — Straight-line vs real
  road-network shortest paths (OSMnx/NetworkX): the pathfinding story on actual maps.
- [`rag_101`](https://github.com/Dima806/rag_101) — Retrieval-augmented generation end to end on CPU;
  where a graph-backed retriever fits in the pipeline.
- [`retrieval_arena`](https://github.com/Dima806/retrieval_arena) — TF-IDF, BM25, dense, and hybrid
  retrieval compared: the vector half of hybrid graph-plus-vector search.
- [`embeddings_101`](https://github.com/Dima806/embeddings_101) — The representation behind vector
  search; pgvector can sit in the same Postgres as AGE.
- [`feature_engineering_arena`](https://github.com/Dima806/feature_engineering_arena) — Planted-signal
  feature engineering; graph features (degree, neighborhood counts) feed ML models.

## License

[Apache-2.0](LICENSE).
