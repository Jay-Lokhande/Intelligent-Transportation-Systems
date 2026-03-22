"""GeoJSON export for node paths on an OSMnx projected graph."""

from __future__ import annotations

import json
from typing import Any

import networkx as nx
import osmnx as ox
from shapely.geometry import LineString, mapping


def linestring_from_node_path(G: nx.MultiDiGraph, node_path: list[int]) -> LineString | None:
    """
    Build one LineString (projected CRS) along ``node_path`` using edge geometries.

    If parallel edges exist, picks the longest ``geometry`` for each step (heuristic).
    """
    if len(node_path) < 2:
        return None
    coords: list[tuple[float, float]] = []
    for u, v in zip(node_path[:-1], node_path[1:], strict=True):
        if u not in G or v not in G[u]:
            return None
        best_geom = None
        best_len = -1.0
        for _k, data in G[u][v].items():
            g = data.get("geometry")
            if g is None:
                continue
            ln = float(data.get("length") or 0.0)
            if ln >= best_len:
                best_len = ln
                best_geom = g
        if best_geom is None:
            xu, yu = float(G.nodes[u]["x"]), float(G.nodes[u]["y"])
            xv, yv = float(G.nodes[v]["x"]), float(G.nodes[v]["y"])
            geom = LineString([(xu, yu), (xv, yv)])
        else:
            geom = best_geom
        part = list(geom.coords)
        if coords and part and part[0] == coords[-1]:
            part = part[1:]
        coords.extend(part)
    if len(coords) < 2:
        return None
    return LineString(coords)


def routes_to_geojson(
    G: nx.MultiDiGraph,
    routes: list[tuple[tuple[float, float, float], list[int], list[tuple[float, float, float]]]],
) -> dict[str, Any]:
    """
    Build a GeoJSON FeatureCollection from ``pareto_paths`` results.

    Geometries are output in EPSG:4326 (lon/lat).
    """
    features: list[dict[str, Any]] = []
    for i, (cost, path, _edges) in enumerate(routes):
        ls = linestring_from_node_path(G, path)
        if ls is None:
            continue
        geom_wgs84, _ = ox.projection.project_geometry(ls, crs=G.graph["crs"], to_latlong=True)
        features.append(
            {
                "type": "Feature",
                "geometry": mapping(geom_wgs84),
                "properties": {
                    "index": i,
                    "time_s": cost[0],
                    "safety": cost[1],
                    "surveillance": cost[2],
                    "node_count": len(path),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def write_geojson(path: str, fc: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)
