from its_route_planner.demo import toy_graph
from its_route_planner.search import (
    ParetoSearchStats,
    pareto_paths,
    path_cost,
    single_objective_shortest,
    sum_vectors,
)


def test_toy_pareto():
    g = toy_graph()
    routes = pareto_paths(g, 0, 3)
    costs = {c for c, _, _ in routes}
    assert (2.0, 5.0, 1.0) in costs
    assert (6.0, 1.0, 1.0) in costs
    assert len(costs) == 2
    for c, path, edges in routes:
        assert sum_vectors(edges) == c
        assert path_cost(g, path) == c


def test_baseline_min_time_matches_fastest_pareto():
    g = toy_graph()
    b = single_objective_shortest(g, 0, 3, 0)
    assert b is not None
    scalar, total, path, edges = b
    assert scalar == 2.0
    assert sum_vectors(edges) == total
    assert total[0] == min(c[0] for c, _, _ in pareto_paths(g, 0, 3))


def test_max_heap_pops_can_truncate():
    g = toy_graph()
    st = ParetoSearchStats()
    routes = pareto_paths(g, 0, 3, max_heap_pops=1, stats=st)
    assert st.truncated
    assert not routes
