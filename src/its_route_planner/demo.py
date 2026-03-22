"""Small hand-built graph for tests and CLI."""

from __future__ import annotations

from its_route_planner.graph import Edge, Graph


def toy_graph() -> Graph:
    """
    Diamond with two intermediate routes:

        0 --(1,5,0)--> 1 --(1,0,1)-->
         \\                           3
          --(5,1,0)--> 2 --(1,0,1)-->

    Two Pareto paths 0->3: (2,5,1) via 1 vs (6,1,1) via 2.
    """
    g = Graph()
    g.add_edge(0, Edge(1, time=1.0, safety=5.0, surveillance=0.0))
    g.add_edge(0, Edge(2, time=5.0, safety=1.0, surveillance=0.0))
    g.add_edge(1, Edge(3, time=1.0, safety=0.0, surveillance=1.0))
    g.add_edge(2, Edge(3, time=1.0, safety=0.0, surveillance=1.0))
    return g
