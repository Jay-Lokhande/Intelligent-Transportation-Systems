"""Multi-objective label-setting search (Pareto-optimal paths)."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from its_route_planner.graph import Edge, Graph
from its_route_planner.pareto import insert_nondominated

Vector3 = tuple[float, float, float]

# (prev_node, prev_cost, edge_vector from prev_node -> node); source has Nones.
BackTriple = tuple[int | None, Vector3 | None, Vector3 | None]


def _add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scalar_key(c: Vector3) -> float:
    """PQ ordering; any monotone key works if dominated partial paths are skipped."""
    return c[0] + c[1] + c[2]


@dataclass
class ParetoSearchStats:
    """Filled when ``stats`` is passed to :func:`pareto_paths`."""

    truncated: bool = False
    notes: list[str] = field(default_factory=list)


def _trim_labels(lst: list[Vector3], max_n: int) -> None:
    """Keep the ``max_n`` best vectors by lexicographic (time, safety, surveillance)."""
    if len(lst) <= max_n:
        return
    lst.sort(key=lambda c: (c[0], c[1], c[2]))
    del lst[max_n:]


def pareto_paths(
    graph: Graph,
    source: int,
    target: int,
    *,
    max_labels_per_node: int | None = None,
    max_heap_pops: int | None = None,
    stats: ParetoSearchStats | None = None,
) -> list[tuple[Vector3, list[int], list[Vector3]]]:
    """
    Return Pareto-optimal paths as ``(cost_vector, node_path, edge_vectors)``.

    ``edge_vectors[i]`` is the cost of ``node_path[i] -> node_path[i + 1]`` (needed when
    the multigraph has parallel edges).

    ``max_labels_per_node`` and ``max_heap_pops`` are optional **safeguards** for large
    graphs.     When set, results may be **approximate** (no longer guaranteed Pareto).
    If ``stats`` is provided, truncation is recorded in ``stats.truncated`` / ``stats.notes``.
    """
    if max_labels_per_node is not None and max_labels_per_node < 1:
        raise ValueError("max_labels_per_node must be >= 1")
    if max_heap_pops is not None and max_heap_pops < 1:
        raise ValueError("max_heap_pops must be >= 1")

    labels: dict[int, list[Vector3]] = {source: [(0.0, 0.0, 0.0)]}
    back: dict[tuple[int, Vector3], BackTriple] = {
        (source, (0.0, 0.0, 0.0)): (None, None, None)
    }

    heap: list[tuple[float, int, Vector3]] = []
    heapq.heappush(heap, (_scalar_key((0.0, 0.0, 0.0)), source, (0.0, 0.0, 0.0)))

    pops = 0
    while heap:
        if max_heap_pops is not None and pops >= max_heap_pops:
            if stats is not None:
                stats.truncated = True
                stats.notes.append("stopped early: max_heap_pops")
            break
        _, node, cost = heapq.heappop(heap)
        pops += 1
        if cost not in labels.get(node, ()):
            continue

        for edge in graph.neighbors(node):
            new_cost = _add(cost, edge.vector())
            lst = labels.setdefault(edge.to, [])
            if not insert_nondominated(lst, new_cost):
                continue
            if max_labels_per_node is not None and len(lst) > max_labels_per_node:
                _trim_labels(lst, max_labels_per_node)
                if stats is not None:
                    stats.truncated = True
                    if not any(
                        "max_labels_per_node" in n for n in stats.notes
                    ):
                        stats.notes.append("trimmed: max_labels_per_node (approximate Pareto)")
            if new_cost not in lst:
                continue
            back[(edge.to, new_cost)] = (node, cost, edge.vector())
            heapq.heappush(heap, (_scalar_key(new_cost), edge.to, new_cost))

    if target not in labels:
        return []

    results: list[tuple[Vector3, list[int], list[Vector3]]] = []
    for c in labels[target]:
        path, edges = _reconstruct_path(back, target, c)
        results.append((c, path, edges))
    return results


def _reconstruct_path(
    back: dict[tuple[int, Vector3], BackTriple],
    target: int,
    cost: Vector3,
) -> tuple[list[int], list[Vector3]]:
    path: list[int] = []
    edges: list[Vector3] = []
    node: int | None = target
    c: Vector3 | None = cost
    while node is not None and c is not None:
        path.append(node)
        prev = back.get((node, c))
        if prev is None:
            break
        pnode, pcost, evec = prev
        if evec is not None:
            edges.append(evec)
        node, c = pnode, pcost
    path.reverse()
    edges.reverse()
    return path, edges


def single_objective_shortest(
    graph: Graph,
    source: int,
    target: int,
    objective: int,
) -> tuple[float, Vector3, list[int], list[Vector3]] | None:
    """
    Dijkstra minimizing one edge weight: ``0`` = time, ``1`` = safety, ``2`` = surveillance.

    Returns ``(scalar_sum, full_cost_vector, node_path, edge_vectors)`` for the shortest
    path under that scalar weight, or ``None`` if ``target`` is unreachable.
    """
    if objective not in (0, 1, 2):
        raise ValueError("objective must be 0, 1, or 2")
    if source == target:
        return (0.0, (0.0, 0.0, 0.0), [source], [])

    inf = float("inf")
    dist: dict[int, float] = {source: 0.0}
    pred: dict[int, tuple[int, Vector3]] = {}

    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, inf):
            continue
        for e in graph.neighbors(u):
            w = e.vector()[objective]
            nd = d + w
            if nd < dist.get(e.to, inf):
                dist[e.to] = nd
                pred[e.to] = (u, e.vector())
                heapq.heappush(heap, (nd, e.to))

    if target not in dist or target not in pred:
        return None

    nodes: list[int] = []
    edges: list[Vector3] = []
    cur = target
    while cur != source:
        nodes.append(cur)
        pr = pred.get(cur)
        if pr is None:
            return None
        p, evec = pr
        edges.append(evec)
        cur = p
    nodes.append(source)
    nodes.reverse()
    edges.reverse()
    total = sum_vectors(edges)
    scalar = total[objective]
    return (scalar, total, nodes, edges)


def sum_vectors(vectors: list[Vector3]) -> Vector3:
    t = [0.0, 0.0, 0.0]
    for v in vectors:
        for i in range(3):
            t[i] += v[i]
    return (t[0], t[1], t[2])


def path_cost(graph: Graph, node_path: list[int]) -> Vector3:
    """
    Sum edge costs along a node path.

    If several parallel edges exist between two consecutive nodes, uses the **first**
    matching edge in the adjacency list (ambiguous). Prefer ``sum_vectors(edge_vectors)``
    from ``pareto_paths`` results when parallel edges exist.
    """
    if len(node_path) < 2:
        return (0.0, 0.0, 0.0)
    total = [0.0, 0.0, 0.0]
    for u, v in zip(node_path[:-1], node_path[1:], strict=True):
        edge = _find_edge(graph, u, v)
        t = edge.vector()
        for i in range(3):
            total[i] += t[i]
    return (total[0], total[1], total[2])


def _find_edge(graph: Graph, frm: int, to: int) -> Edge:
    for e in graph.neighbors(frm):
        if e.to == to:
            return e
    raise ValueError(f"no edge {frm} -> {to}")
