"""Readability scoring: lines of code per approach (SQL balloons, Cypher stays one line)."""

_COMMENT_PREFIXES = ("--", "#", "//")


def count_loc(snippet: str) -> int:
    """Count non-blank, non-comment lines in a query snippet."""
    total = 0
    for raw in snippet.strip().splitlines():
        line = raw.strip()
        if line and not line.startswith(_COMMENT_PREFIXES):
            total += 1
    return total
