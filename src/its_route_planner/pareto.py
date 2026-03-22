"""Dominance checks for minimization of vector costs."""

from __future__ import annotations

from typing import Iterable, Sequence, TypeVar

T = TypeVar("T", bound=Sequence[float])


def dominates(a: T, b: T) -> bool:
    """True if a is <= b in every component and strictly < in at least one."""
    if len(a) != len(b):
        raise ValueError("vectors must have same length")
    le = all(x <= y for x, y in zip(a, b, strict=True))
    lt = any(x < y for x, y in zip(a, b, strict=True))
    return le and lt


def is_nondominated(candidate: T, others: Iterable[T]) -> bool:
    """True if no vector in others dominates candidate."""
    return not any(dominates(o, candidate) for o in others)


def insert_nondominated(
    labels: list[T],
    candidate: T,
) -> bool:
    """
    Insert candidate into labels if nondominated; remove labels dominated by candidate.
    Returns True if candidate was inserted.
    """
    if candidate in labels:
        return False
    if any(dominates(l, candidate) for l in labels):
        return False
    labels[:] = [l for l in labels if not dominates(candidate, l)]
    labels.append(candidate)
    return True
