from shapely.geometry import LineString

import networkx as nx

from its_route_planner.geojson_export import linestring_from_node_path, routes_to_geojson


def test_linestring_from_node_path():
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:32618"
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_edge(1, 2, 0, length=100.0, geometry=LineString([(0, 0), (100, 0)]))
    ls = linestring_from_node_path(G, [1, 2])
    assert ls is not None
    assert ls.length > 0


def test_routes_to_geojson():
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:32618"
    G.add_node(1, x=586000.0, y=4511000.0)
    G.add_node(2, x=586100.0, y=4511000.0)
    G.add_edge(1, 2, 0, length=100.0, geometry=LineString([(586000, 4511000), (586100, 4511000)]))
    routes = [((10.0, 2.0, 1.0), [1, 2], [(10.0, 2.0, 1.0)])]
    fc = routes_to_geojson(G, routes)
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert fc["features"][0]["geometry"]["type"] == "LineString"
    assert "coordinates" in fc["features"][0]["geometry"]
