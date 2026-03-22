from pathlib import Path

import networkx as nx

from its_route_planner.edge_costs import load_edge_costs_csv, write_edge_key_template
from its_route_planner.road_network import nx_to_routing_graph


def test_load_sample_csv():
    p = Path(__file__).resolve().parent / "fixtures" / "sample_edge_costs.csv"
    o = load_edge_costs_csv(p)
    assert o[(1, 2, 0)]["safety"] == 50.0
    assert o[(1, 2, 0)]["surveillance"] == 0.25


def test_overlay_overrides_weights():
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:32618"
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_edge(
        1,
        2,
        0,
        length=100.0,
        travel_time=10.0,
        highway="residential",
    )
    overlay = {(1, 2, 0): {"safety": 99.0, "surveillance": 3.0}}
    r = nx_to_routing_graph(G, edge_overlay=overlay)
    e = r.neighbors(1)[0]
    assert e.safety == 99.0
    assert e.surveillance == 3.0
    assert e.time == 10.0


def test_write_edge_key_template(tmp_path):
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:32618"
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=1.0, y=0.0)
    G.add_edge(1, 2, 0, length=1.0)
    G.add_edge(1, 2, 1, length=2.0)
    out = tmp_path / "t.csv"
    n = write_edge_key_template(G, out)
    assert n == 2
    text = out.read_text()
    assert "u,v,key" in text.replace(" ", "")
