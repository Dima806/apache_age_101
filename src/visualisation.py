"""Draw graphs and matched subgraphs for the notebooks and the Streamlit app."""

from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

plt.switch_backend("Agg")  # headless: render to files, never a GUI window

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figures"


def draw_graph(
    graph: nx.DiGraph,
    path: Path | None = None,
    title: str | None = None,
    highlight: Iterable[int] | None = None,
    seed: int = 7,
) -> Path | None:
    """Draw ``graph`` with optional highlighted nodes; save to ``path`` if given."""
    highlight_set = set(highlight or [])
    layout = nx.spring_layout(graph, seed=seed)
    colours = ["#e4572e" if node in highlight_set else "#4c6ef5" for node in graph.nodes]

    fig, ax = plt.subplots(figsize=(7, 5))
    nx.draw_networkx(
        graph,
        pos=layout,
        ax=ax,
        node_color=colours,
        node_size=280,
        font_size=7,
        edge_color="#adb5bd",
        arrows=True,
    )
    if title:
        ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()

    if path is None:
        plt.close(fig)
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
