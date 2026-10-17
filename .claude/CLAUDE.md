# Project: apache_age_101

> Detailed working guide for agents. See `.llm/PRD_apache_age_101.md` for the full spec.

## Identity

**Apache AGE 101: The Graph Database Hiding Inside Your Postgres** — an educational "101"
portfolio project for a data-science audience. Apache AGE is a PostgreSQL extension that adds the
openCypher query language to the Postgres you already run, so graph queries live next to your
relational tables with no second database, no copy, and no ETL.

Deliverable shape: a GitHub repo with **6 Jupyter notebooks**, a **`src/` library**, and a
**lightweight Streamlit app**, all runnable inside a **2-CPU / 8 GB GitHub Codespace** (no GPU).

Narrative build-up across the notebooks:
1. graphs live in your database →
2. the n-hop join problem →
3. fraud rings and pathfinding →
4. AGE vs SQL vs NetworkX (the arena) →
5. graph algorithms — the honest limit →
6. decision framework.

## Thesis (say it in one breath)

Graph-shaped questions — *how are these two accounts connected, is there a payment ring, who is
three hops away, what breaks if this supplier fails* — are a pile of self-joins or an ugly recursive
CTE in SQL, and **one line of Cypher in AGE**, run inside the same Postgres as your tables.

- `MATCH (a)-[:KNOWS*1..6]->(b)` replaces four stacked self-joins / a 20–30 line recursive CTE with
  a visited-set guard.
- A fraud ring (A pays B pays C pays back to A) is ~impossible in relational algebra and a short
  `MATCH` cycle pattern in AGE.
- **The honest limit:** AGE is a *pattern-matching and pathfinding engine, not a graph-algorithms
  library.* It has no built-in PageRank, community detection, or centrality. The honest workflow is:
  **traverse/extract a subgraph in AGE → compute the algorithm in NetworkX/igraph → write scores
  back** as node properties.

Never oversell AGE as an analytics engine. Never claim it needs no server. Both are the whole point.

## Stack & constraints

- **Python 3.11+**, package manager **`uv`**. All open source, **CPU only**, **2-CPU / 8 GB**.
- **HONEST EXCEPTION:** AGE is a Postgres *extension*, so this project runs **one local PostgreSQL
  server** in the Codespace. It is **local-only: no cloud, no managed service, no account, no API
  key, no registration.** This is stated plainly, not hidden — it is the one thing AGE requires.
- Install path: `scripts/install_age.sh` installs PostgreSQL via apt and **builds the matching
  Apache AGE release from source** (pinned PG major + matching AGE release — AGE targets specific
  Postgres majors), then `CREATE EXTENSION age`. The `apache/age` Docker image is documented as an
  **optional zero-build fallback**, not the default.
- Connect with **`psycopg[binary]` (psycopg3)**.
- **Baselines are pure pip** (plain-SQL recursive CTEs conceptually + NetworkX in memory), so the
  lessons in notebooks 02 and 04–06 still run **even if AGE fails to build**. Mark AGE-specific
  cells clearly.
- Graphs are kept to **thousands of nodes/edges** so AGE queries, the SQL baselines, and *exact*
  NetworkX algorithms all finish in seconds. Each notebook runs **< 6 min** (after the one-time AGE
  build).
- Key deps: `psycopg[binary]`, `networkx`, `pandas`, `numpy`, `matplotlib`, `plotly`, `pyvis`,
  `streamlit`, `pydantic`, `pydantic-settings`, `pyyaml`. Optional `[algos]`: `python-igraph`.
  Dev: `pytest`, `ruff`, `ty`, `jupyter`, `ipykernel`, `nbconvert`, `nbclient`.

## Setup sequence

```
make setup      # Python env (uv sync --all-extras + register kernel)
make age        # ONE-TIME: apt Postgres + build AGE from source + CREATE EXTENSION (local only)
make db-start   # start the local Postgres service
make load       # generate planted graphs + load into AGE and relational tables
make test       # assert everything agrees with planted truth
```

`make age` is a one-time build (a few minutes) deliberately split out so the Python env and
baselines are usable immediately.

## Repository structure

```
scripts/     install_age.sh (apt PG + build AGE, pinned versions) · init_db.sql (CREATE EXTENSION/LOAD/create_graph)
config/      settings.yaml — DB connection, graph names, dataset sizes, seeds
src/age/     connect (psycopg + LOAD age + search_path) · cypher (run_cypher + agtype parsing)
             load (relational tables → AGE graph) · to_networkx (extract an AGE subgraph → NetworkX)
src/baselines/   sql_recursive (joins + recursive CTE with visited-set guard) · networkx_graph (in-memory)
src/queries/     traversal (n-hop, variable-length) · paths (shortest path) · rings (cycle detection)
                 patterns (co-occurrence, reachability, impact)
src/datasets/    graphs.py — synthetic graphs with PLANTED rings/paths/communities (known truth)
src/evaluation/  correctness (vs truth + 3-way agreement) · readability (LOC/complexity)
                 runtime (vs size & hop depth) · comparison (arena harness)
src/visualisation.py   graph drawing (networkx + matplotlib / pyvis)
app/streamlit_app.py   Cypher console · n-hop explorer · fraud-ring finder · three-way comparison
notebooks/01..06       the narrative above
tests/           test_cypher · test_traversal · test_rings · test_to_networkx
outputs/figures/ generated figures for the Medium article (7–8 figures)
```

## The core pattern: three implementations per question

Every graph question is answered **three ways** and compared in the arena:
1. **Cypher through AGE** (`run_cypher`),
2. **plain SQL** (joins + recursive CTEs with a visited-set guard against cycles),
3. **NetworkX in memory**.

Scored on **readability** (lines of code / how the query reads), **correctness** (against planted
truth, with all three agreeing where they should), and **runtime** (as graph size and hop depth
grow). There is **no single winner** — each has a region:
- AGE and NetworkX express traversal cleanly; SQL balloons with depth.
- NetworkX is fastest in memory but must load the whole graph into Python.
- AGE runs in the database next to the data, no copy.

## Datasets (planted ground truth)

Synthetic business graphs generated locally, seeded, committed as seed scripts (nothing downloaded):
- **social-and-transaction graph** with planted fraud rings (known cycles) → ring detection + multi-hop.
- **bipartite user–item co-purchase graph** → recommendation-style two-hop traversal.
- **dependency / lineage graph** (supply chain or data lineage) → reachability, shortest path, impact.
- **small knowledge graph** of entities/relations → the GraphRAG link.

Because rings, shortest paths, and communities are *planted*, every answer is checked against truth
**and** cross-checked across AGE / SQL / NetworkX.

## Key concepts to teach

- Modeling vocabulary: **node, edge, property, label**. The one modeling decision behind every
  graph: *what is a node, what is an edge, what is a property.*
- **Multi-hop = N self-joins** in SQL; **variable-length = recursive CTE + visited-set** (guards
  against infinite loops on cycles). Cypher: `MATCH (a)-[:REL*1..n]->(b)` — one line.
- **Cycle / ring detection** (A→B→C→A): painful/effectively impossible in SQL, a short Cypher
  pattern in AGE. This is the fraud-ring showpiece.
- **AGE runs Cypher INSIDE the same Postgres** as your tables: no second DB, no copy, no ETL.
- **AGE ≠ analytics library.** No built-in PageRank/community/centrality. Pattern: Cypher extracts
  the subgraph → NetworkX/igraph computes → write scores back as node properties.
- **pgvector can live in the same Postgres** → graph + vector retrieval in one DB. Cross-links to
  `graphrag_vs_vectorrag` and `vector_search_101`.
- **Decision framework:** plain SQL for shallow 1–2 hop you already query relationally · AGE for
  multi-hop / path patterns / cycle detection next to data already in Postgres · NetworkX/igraph for
  in-memory graph algorithms · a dedicated graph DB (Neo4j + GDS) for very large graphs, heavy graph
  OLTP, or a mature built-in algorithms library · and the often-best combined pattern: keep the
  graph in AGE, pull subgraphs into Python for the heavy algorithms.

## AGE / psycopg gotchas

- Per connection you must `LOAD 'age';` and `SET search_path = ag_catalog, "$user", public;` before
  running Cypher. `connect.py` centralizes this; everything else uses it.
- `CREATE EXTENSION age;` once per database (in `init_db.sql`), then `create_graph('<name>')`.
- Cypher is invoked as `SELECT * FROM cypher('<graph>', $$ <cypher> $$) AS (col agtype, ...);` — the
  column list and `agtype` casts are required. `run_cypher(graph, query)` is the **one adapter** the
  whole project uses; route all Cypher through it and parse `agtype` into plain Python / pandas there.
- Keep the graph and the relational baseline as **the same records in the same database, queried two
  ways** — that equivalence is a teaching point, so load both from one source in `load.py`.

## Conventions

- `ruff` (line-length 99, `E,F,W,I,UP,N,B,A,SIM,PTH`, ignore `E501`) + `ruff format`; `ty` for types.
- `pytest` with `-v --tb=short`, tests under `tests/`.
- Run modules from the repo root as `python -m src.<pkg>.<mod>` (src is imported as `src`).
- Reproducibility: seeds and graph sizes live in `config/settings.yaml`; correctness is **asserted**
  against planted truth and across the three implementations — not just eyeballed.

## Resilience

The SQL and NetworkX baselines are pure Python, so notebooks 02 and 04–06 teach their lessons even
without AGE. AGE-specific cells are clearly marked. `make load` and the AGE tests need a running
local Postgres; the baselines do not.

## Success bar (what "done" means)

`CREATE EXTENSION age` works and `run_cypher` returns rows on a known graph · AGE n-hop matches the
SQL CTE and NetworkX on planted paths · all planted rings found · AGE shortest path matches NetworkX
· subgraph extraction round-trips (extracted NetworkX graph matches the AGE graph) · honest-limit
pattern computes PageRank in NetworkX and writes it back · local-only verified · baselines run
without AGE · each notebook < 6 min · `make lint` and `make test` pass with zero errors.

## Token Rules

- Caveman mode: ON. **Code-first** — prefer working code and terse explanation over prose.
- `/compact` at notebook boundaries.
