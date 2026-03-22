import os
from pathlib import Path

import pytest

from its_route_planner.point_layers import (
    surveillance_counts_near_points,
    write_surveillance_edge_csv,
)


def test_write_surveillance_edge_csv(tmp_path: Path):
    out = tmp_path / "e.csv"
    n = write_surveillance_edge_csv(
        out,
        {(1, 2, 0): 3, (1, 2, 1): 0},
        scale=0.5,
        skip_zero=True,
    )
    assert n == 1
    text = out.read_text()
    assert "1,2,0" in text
    assert "1.5" in text


def test_requires_projected_graph():
    import networkx as nx

    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:4326"
    with pytest.raises(ValueError, match="projected"):
        surveillance_counts_near_points(G, [0.0], [0.0], buffer_m=10.0)


@pytest.mark.skipif(os.getenv("ITS_NETWORK") != "1", reason="set ITS_NETWORK=1 to run Overpass test")
def test_surveillance_counts_near_points_integration():
    from its_route_planner.road_network import load_projected_graph

    G = load_projected_graph(-74.01, 40.748, -73.995, 40.758)
    c = surveillance_counts_near_points(G, [-74.006], [40.752], buffer_m=200.0)
    assert len(c) >= 1
