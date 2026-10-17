"""Check answers against planted truth and across the three implementations."""

from collections.abc import Iterable, Sequence


def canonical_ring(cycle: Sequence[int]) -> tuple[int, ...]:
    """Rotate a directed cycle to start at its smallest id (direction preserved).

    Lets ``[3, 1, 2]`` and ``[1, 2, 3]`` (the same ring 1->2->3->1) compare equal.
    """
    if not cycle:
        return ()
    n = len(cycle)
    start = min(range(n), key=lambda i: cycle[i])
    return tuple(cycle[start:]) + tuple(cycle[:start])


def rings_to_canonical(rings: Iterable[Sequence[int]]) -> set[tuple[int, ...]]:
    """Normalise a collection of cycles into a comparable set."""
    return {canonical_ring(r) for r in rings}


def all_rings_found(found: Iterable[Sequence[int]], planted: Iterable[Sequence[int]]) -> bool:
    """True when every planted ring is present in ``found``."""
    return rings_to_canonical(planted) <= rings_to_canonical(found)


def sets_agree(*results: Iterable[int]) -> bool:
    """True when all result collections contain exactly the same elements."""
    normalised = [set(r) for r in results]
    first = normalised[0]
    return all(s == first for s in normalised[1:])
