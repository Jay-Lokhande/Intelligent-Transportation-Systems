import networkx as nx

from its_route_planner.graph import Edge
from its_route_planner.road_network import nx_to_routing_graph
from its_route_planner.search import pareto_paths, sum_vectors


def test_nx_to_routing_graph_parallel_edges():
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:32618"
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_edge(1, 2, 0, length=100.0, travel_time=10.0, highway="residential")
    G.add_edge(1, 2, 1, length=120.0, travel_time=12.0, highway="primary")

    r = nx_to_routing_graph(G)
    assert len(r.neighbors(1)) == 2
    costs = sorted((e.vector() for e in r.neighbors(1)), key=lambda t: t[0])
    assert costs[0][0] == 10.0
    assert costs[1][0] == 12.0


def test_weights_fallback_without_travel_time():
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:32618"
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_edge(1, 2, 0, length=1000.0, speed_kph=50.0, highway="secondary")

    r = nx_to_routing_graph(G)
    e = r.neighbors(1)[0]
    assert isinstance(e, Edge)
    assert e.time > 0
    assert e.safety > 0 and e.surveillance > 0


def test_pareto_respects_parallel_edges():
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:32618"
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_edge(1, 2, 0, length=100.0, travel_time=10.0, highway="residential")
    G.add_edge(1, 2, 1, length=120.0, travel_time=12.0, highway="primary")

    r = nx_to_routing_graph(G)
    routes = pareto_paths(r, 1, 2)
    assert len(routes) == 2
    for c, path, edges in routes:
        assert path == [1, 2]
        assert sum_vectors(edges) == c
