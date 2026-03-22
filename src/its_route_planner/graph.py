"""Simple directed multigraph with three additive edge costs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Edge:
    """Directed edge with nonnegative scalar costs (minimize all)."""

    to: int
    time: float
    safety: float
    surveillance: float

    def __post_init__(self) -> None:
        if self.time < 0 or self.safety < 0 or self.surveillance < 0:
            raise ValueError("edge costs must be nonnegative")

    def vector(self) -> tuple[float, float, float]:
        return (self.time, self.safety, self.surveillance)


class Graph:
    """Adjacency list: node_id -> list of outgoing edges."""

    def __init__(self) -> None:
        self._adj: dict[int, list[Edge]] = {}

    def add_edge(self, frm: int, edge: Edge) -> None:
        self._adj.setdefault(frm, []).append(edge)
        self._adj.setdefault(edge.to, [])

    def neighbors(self, node: int) -> list[Edge]:
        return list(self._adj.get(node, ()))

    def nodes(self) -> list[int]:
        return sorted(self._adj.keys())
