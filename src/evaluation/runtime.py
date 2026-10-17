"""Runtime measurement: query time vs graph size and hop depth."""

from collections.abc import Callable
from time import perf_counter
from typing import Any


def time_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """Run ``fn`` once and return ``(result, seconds)``."""
    start = perf_counter()
    result = fn(*args, **kwargs)
    return result, perf_counter() - start


def benchmark(fn: Callable[..., Any], *args: Any, repeat: int = 3, **kwargs: Any) -> float:
    """Median wall-clock seconds of ``fn`` over ``repeat`` runs."""
    timings = sorted(time_call(fn, *args, **kwargs)[1] for _ in range(repeat))
    return timings[len(timings) // 2]
