"""Synthetic, seeded business graphs with *planted* ground truth.

The planted rings, communities, and (by construction) acyclic dependencies are the
truth the arena checks AGE, SQL, and NetworkX against. Everything is generated
locally and deterministically from a seed; nothing is downloaded.
"""

import random
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from src.config import Settings, load_settings

# Relationship labels used across the project.
KNOWS = "KNOWS"
PAYS = "PAYS"
BOUGHT = "BOUGHT"
DEPENDS_ON = "DEPENDS_ON"
RELATED_TO = "RELATED_TO"


@dataclass(frozen=True)
class Node:
    """A graph vertex: a stable id, a label, and a bag of properties."""

    node_id: int
    label: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    """A directed graph edge from ``src`` to ``dst`` with a label and properties."""

    src: int
    dst: int
    label: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphData:
    """A whole graph plus the planted truth needed to grade answers."""

    name: str
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    communities: dict[int, int] = field(default_factory=dict)
    rings: list[list[int]] = field(default_factory=list)

    def node_rows(self) -> list[dict[str, Any]]:
        """Nodes as flat dict rows (for loading into AGE / relational tables)."""
        return [{"node_id": n.node_id, "label": n.label, **n.props} for n in self.nodes]

    def edge_rows(self) -> list[dict[str, Any]]:
        """Edges as flat dict rows."""
        return [{"src": e.src, "dst": e.dst, "label": e.label, **e.props} for e in self.edges]

    def edges_with_label(self, rel: str | None) -> list[Edge]:
        """All edges, or only those with the given relationship label."""
        if rel is None:
            return list(self.edges)
        return [e for e in self.edges if e.label == rel]

    def to_networkx(self, rel: str | None = None) -> nx.DiGraph:
        """Build a directed NetworkX graph, optionally restricted to one label."""
        graph: nx.DiGraph = nx.DiGraph()
        for node in self.nodes:
            graph.add_node(node.node_id, label=node.label, **node.props)
        for edge in self.edges_with_label(rel):
            graph.add_edge(edge.src, edge.dst, label=edge.label, **edge.props)
        return graph


def _add_reciprocal(edges: list[Edge], a: int, b: int, label: str) -> None:
    edges.append(Edge(a, b, label))
    edges.append(Edge(b, a, label))


def social_transaction_graph(settings: Settings | None = None) -> GraphData:
    """Accounts with KNOWS (community-structured) and PAYS (DAG + planted rings) edges.

    PAYS is constructed so that the *only* cycles are the planted fraud rings: random
    PAYS edges always go from a lower to a higher id (a DAG), and ring accounts take
    part in no other PAYS edge. Ring detection therefore recovers exactly the planted set.
    """
    cfg = (settings or load_settings()).dataset
    rng = random.Random(cfg.seed)

    nodes = [
        Node(i, "Account", {"name": f"acct_{i}", "risk": round(rng.random(), 3)})
        for i in range(cfg.n_accounts)
    ]
    communities = {i: i % cfg.n_communities for i in range(cfg.n_accounts)}
    by_community: dict[int, list[int]] = {c: [] for c in range(cfg.n_communities)}
    for node_id, comm in communities.items():
        by_community[comm].append(node_id)

    edges: list[Edge] = []

    # KNOWS: mostly within-community, a few bridges. Reciprocal (friendship is mutual).
    seen: set[tuple[int, int]] = set()
    for node_id in range(cfg.n_accounts):
        peers = by_community[communities[node_id]]
        for _ in range(cfg.avg_knows_degree):
            other = rng.choice(peers) if rng.random() < 0.85 else rng.randrange(cfg.n_accounts)
            if other == node_id:
                continue
            key = (min(node_id, other), max(node_id, other))
            if key in seen:
                continue
            seen.add(key)
            _add_reciprocal(edges, node_id, other, KNOWS)

    # Reserve disjoint groups of accounts for planted payment rings.
    pool = list(range(cfg.n_accounts))
    rng.shuffle(pool)
    rings: list[list[int]] = []
    reserved: set[int] = set()
    cursor = 0
    for _ in range(cfg.n_rings):
        length = rng.randint(cfg.ring_min_len, cfg.ring_max_len)
        if cursor + length > len(pool):
            break
        group = pool[cursor : cursor + length]
        cursor += length
        rings.append(group)
        reserved.update(group)
        for a, b in zip(group, group[1:] + group[:1], strict=True):
            edges.append(Edge(a, b, PAYS, {"amount": rng.randint(50, 5000)}))

    # Random PAYS edges among non-reserved accounts, strictly increasing id (acyclic).
    free = [i for i in range(cfg.n_accounts) if i not in reserved]
    for src in free:
        for _ in range(cfg.avg_pays_degree):
            dst = rng.choice(free)
            if dst <= src:
                continue
            edges.append(Edge(src, dst, PAYS, {"amount": rng.randint(50, 5000)}))

    return GraphData("social_txn", nodes, edges, communities, rings)


def copurchase_graph(settings: Settings | None = None) -> GraphData:
    """Bipartite user/item graph with BOUGHT edges, for two-hop co-purchase traversal."""
    cfg = (settings or load_settings()).dataset
    rng = random.Random(cfg.seed + 1)

    users = [Node(i, "User", {"name": f"user_{i}"}) for i in range(cfg.n_users)]
    offset = cfg.n_users
    items = [
        Node(offset + j, "Item", {"name": f"item_{j}", "category": j % 8})
        for j in range(cfg.n_items)
    ]
    edges: list[Edge] = []
    for user in users:
        for _ in range(rng.randint(2, 6)):
            item = offset + rng.randrange(cfg.n_items)
            edges.append(Edge(user.node_id, item, BOUGHT))
    return GraphData("copurchase", users + items, edges)


def dependency_graph(settings: Settings | None = None) -> GraphData:
    """Acyclic DEPENDS_ON graph of components, for reachability / shortest path / impact."""
    cfg = (settings or load_settings()).dataset
    rng = random.Random(cfg.seed + 2)

    nodes = [Node(i, "Component", {"name": f"svc_{i}"}) for i in range(cfg.n_components)]
    edges: list[Edge] = []
    for src in range(cfg.n_components):
        for _ in range(rng.randint(1, 3)):
            dst = rng.randrange(src + 1, cfg.n_components) if src + 1 < cfg.n_components else src
            if dst != src:
                edges.append(Edge(src, dst, DEPENDS_ON))
    return GraphData("dependency", nodes, edges)


def knowledge_graph(_settings: Settings | None = None) -> GraphData:
    """A tiny hand-authored entity/relation graph, the GraphRAG link."""
    names = ["Postgres", "AGE", "Cypher", "Neo4j", "NetworkX", "pgvector", "GraphRAG"]
    nodes = [Node(i, "Entity", {"name": name}) for i, name in enumerate(names)]
    idx = {name: i for i, name in enumerate(names)}
    pairs = [
        ("AGE", "Postgres"),
        ("AGE", "Cypher"),
        ("Neo4j", "Cypher"),
        ("pgvector", "Postgres"),
        ("GraphRAG", "AGE"),
        ("GraphRAG", "pgvector"),
        ("NetworkX", "AGE"),
    ]
    edges = [Edge(idx[a], idx[b], RELATED_TO) for a, b in pairs]
    return GraphData("knowledge", nodes, edges)


def all_graphs(settings: Settings | None = None) -> dict[str, GraphData]:
    """Generate every dataset keyed by its graph name."""
    settings = settings or load_settings()
    return {
        g.name: g
        for g in (
            social_transaction_graph(settings),
            copurchase_graph(settings),
            dependency_graph(settings),
            knowledge_graph(settings),
        )
    }


def _summarise(graphs: Iterable[GraphData]) -> None:
    for g in graphs:
        print(
            f"{g.name:<12} nodes={len(g.nodes):>5}  edges={len(g.edges):>6}  rings={len(g.rings)}"
        )


def main() -> None:
    """Generate all graphs from settings and print a summary (no DB required)."""
    graphs = all_graphs()
    print("Generated synthetic graphs (planted truth, local-only):")
    _summarise(graphs.values())


if __name__ == "__main__":
    main()
