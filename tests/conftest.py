"""Shared fixtures: tiny hand-built graphs with exactly known truth."""

import pytest

from src.datasets.graphs import KNOWS, PAYS, Edge, GraphData, Node


@pytest.fixture
def knows_graph() -> GraphData:
    """A tiny KNOWS graph with known multi-hop reachability.

    Edges: 0->1, 1->2, 2->3, 1->4, 4->3.
    From 0: 1 hop -> {1}; 2 hops -> {2, 4}; 3 hops -> {3}; 1..3 -> {1, 2, 3, 4}.
    """
    nodes = [Node(i, "Account", {"name": f"acct_{i}"}) for i in range(6)]
    edges = [
        Edge(0, 1, KNOWS),
        Edge(1, 2, KNOWS),
        Edge(2, 3, KNOWS),
        Edge(1, 4, KNOWS),
        Edge(4, 3, KNOWS),
    ]
    return GraphData("knows_test", nodes, edges)


@pytest.fixture
def ring_graph() -> GraphData:
    """A PAYS graph whose only cycle is the planted ring 0->1->2->0."""
    nodes = [Node(i, "Account") for i in range(5)]
    edges = [
        Edge(0, 1, PAYS),
        Edge(1, 2, PAYS),
        Edge(2, 0, PAYS),  # closes the ring
        Edge(0, 3, PAYS),  # chord out of the ring, no return
        Edge(3, 4, PAYS),
    ]
    return GraphData("ring_test", nodes, edges, rings=[[0, 1, 2]])
