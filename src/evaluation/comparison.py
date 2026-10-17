"""The arena: score AGE / SQL / NetworkX on readability, correctness, and runtime."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.evaluation.readability import count_loc
from src.evaluation.runtime import time_call


@dataclass
class Implementation:
    """One way of answering a question: a label, a callable, and the query text."""

    name: str
    call: Callable[[], Any]
    query: str = field(default="")


def _equal(result: Any, truth: Any) -> bool:
    if isinstance(result, set) or isinstance(truth, set):
        return set(result) == set(truth)
    return bool(result == truth)


def compare(impls: list[Implementation], truth: Any | None = None) -> pd.DataFrame:
    """Run each implementation and tabulate lines of code, runtime, and correctness.

    ``truth`` is the planted answer; when given, each row gets a ``correct`` flag,
    which is how the arena shows all approaches agreeing where they should.
    """
    records: list[dict[str, Any]] = []
    for impl in impls:
        result, seconds = time_call(impl.call)
        record: dict[str, Any] = {
            "approach": impl.name,
            "lines_of_code": count_loc(impl.query),
            "seconds": round(seconds, 6),
        }
        if truth is not None:
            record["correct"] = _equal(result, truth)
        records.append(record)
    return pd.DataFrame(records)
