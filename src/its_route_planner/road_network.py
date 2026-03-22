"""Load drive networks from OpenStreetMap (OSMnx) and map edges to three costs."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import osmnx as ox
from shapely.geometry import Point

from its_route_planner.edge_costs import EdgeOverlay
from its_route_planner.graph import Edge, Graph

# Higher = worse (more perceived accident exposure / severity proxy), scaled by length.
_HIGHWAY_SAFETY_WEIGHT: dict[str, float] = {
    "motorway": 1.2,
    "motorway_link": 1.2,
    "trunk": 1.4,
    "trunk_link": 1.4,
    "primary": 1.6,
    "primary_link": 1.6,
    "secondary": 1.8,
    "secondary_link": 1.8,
    "tertiary": 2.0,
    "tertiary_link": 2.0,
    "residential": 2.6,
    "living_street": 2.4,
    "unclassified": 2.5,
    "service": 2.8,
    "track": 3.0,
}

# Higher = more surveillance exposure proxy (arterials / motorways).
_HIGHWAY_SURV_WEIGHT: dict[str, float] = {
    "motorway": 3.0,
    "motorway_link": 2.8,
    "trunk": 2.6,
    "primary": 2.4,
    "secondary": 2.0,
    "tertiary": 1.6,
    "residential": 1.0,
    "living_street": 0.9,
    "unclassified": 1.2,
    "service": 1.1,
    "track": 0.5,
}


def _primary_highway(edge_data: dict) -> str:
    hw = edge_data.get("highway")
    if isinstance(hw, list):
        hw = hw[0] if hw else None
    if not isinstance(hw, str):
        return "unclassified"
    base = hw.split("|")[0].strip()
    return base or "unclassified"


def _weights_for_edge(
    length_m: float,
    edge_data: dict,
    override: dict[str, float] | None,
) -> tuple[float, float, float]:
    """Return (time_sec, safety_cost, surveillance_cost) for one directed edge."""
    tt = edge_data.get("travel_time")
    if tt is None or (isinstance(tt, float) and tt != tt):  # nan
        speed = edge_data.get("speed_kph") or 30.0
        time_s = float(length_m) / max(float(speed) * 1000.0 / 3600.0, 0.1)
    else:
        time_s = float(tt)

    h = _primary_highway(edge_data)
    s_w = _HIGHWAY_SAFETY_WEIGHT.get(h, 2.4)
    c_w = _HIGHWAY_SURV_WEIGHT.get(h, 1.2)

    safety = float(length_m) * s_w * 0.01
    surveillance = float(length_m) * c_w * 0.01

    if override:
        if "time" in override:
            time_s = float(override["time"])
        if "safety" in override:
            safety = float(override["safety"])
        if "surveillance" in override:
            surveillance = float(override["surveillance"])

    return time_s, safety, surveillance


def nx_to_routing_graph(G: nx.MultiDiGraph, edge_overlay: EdgeOverlay | None = None) -> Graph:
    """
    Convert a projected OSMnx drive graph to our routing Graph.

    Expects `travel_time` (seconds) on edges when available (run
    `ox.add_edge_speeds` + `ox.add_edge_travel_times` first).

    ``edge_overlay`` maps ``(u, v, key)`` to optional ``time`` / ``safety`` /
    ``surveillance`` overrides (see ``load_edge_costs_csv``). Unspecified edges
    use highway-length proxies.
    """
    g = Graph()
    for u, v, key, data in G.edges(keys=True, data=True):
        length_m = float(data.get("length") or 0.0)
        if length_m <= 0:
            continue
        ovr = None
        if edge_overlay:
            ovr = edge_overlay.get((int(u), int(v), int(key)))
        t, s, c = _weights_for_edge(length_m, data, ovr)
        g.add_edge(int(u), Edge(int(v), time=t, safety=s, surveillance=c))
    return g


@dataclass(slots=True)
class RoadNetwork:
    """Routing graph + projected OSMnx graph for snapping (x,y in meters)."""

    routing: Graph
    projected: nx.MultiDiGraph

    def nearest_node(self, lat: float, lon: float) -> int:
        """Snap a WGS84 point to the nearest graph node (projected CRS)."""
        geom, _ = ox.projection.project_geometry(
            Point(lon, lat), crs="EPSG:4326", to_crs=self.projected.graph["crs"]
        )
        x, y = float(geom.x), float(geom.y)
        best: int | None = None
        best_d = float("inf")
        for n, data in self.projected.nodes(data=True):
            nx = float(data["x"])
            ny = float(data["y"])
            d2 = (nx - x) ** 2 + (ny - y) ** 2
            if d2 < best_d:
                best_d = d2
                best = int(n)
        if best is None:
            raise ValueError("empty graph")
        return best


def load_projected_graph(
    west: float,
    south: float,
    east: float,
    north: float,
    *,
    network_type: str = "drive",
    retain_all: bool = False,
) -> nx.MultiDiGraph:
    """
    Download OSM for the bbox and return a **projected** drive graph with speeds
    and travel times (same pipeline as :func:`from_bbox`, without building a routing
    :class:`Graph`).
    """
    bbox = (west, south, east, north)
    G = ox.graph_from_bbox(bbox, network_type=network_type, retain_all=retain_all)
    G = ox.project_graph(G)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    return G


def from_bbox(
    west: float,
    south: float,
    east: float,
    north: float,
    *,
    network_type: str = "drive",
    retain_all: bool = False,
    edge_overlay: EdgeOverlay | None = None,
) -> RoadNetwork:
    """
    Download OSM within bbox ``(west, south, east, north)`` in degrees.

    The graph is projected for metric lengths; edge speeds/travel times follow
    OSMnx defaults. Optional ``edge_overlay`` supplies CSV-joined safety /
    surveillance / time per ``(u, v, key)``.
    """
    G = load_projected_graph(
        west, south, east, north, network_type=network_type, retain_all=retain_all
    )
    routing = nx_to_routing_graph(G, edge_overlay=edge_overlay)
    return RoadNetwork(routing=routing, projected=G)
