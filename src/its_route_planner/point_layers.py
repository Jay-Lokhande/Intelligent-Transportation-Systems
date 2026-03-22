"""Join point layers (e.g. CCTV) to road edges for surveillance cost CSV."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
import osmnx as ox

if TYPE_CHECKING:
    import networkx as nx


def surveillance_counts_near_points(
    G: "nx.MultiDiGraph",
    lons: Sequence[float],
    lats: Sequence[float],
    buffer_m: float,
) -> dict[tuple[int, int, int], int]:
    """
    Count how many WGS84 points fall within ``buffer_m`` (meters) of each directed edge.

    Uses the edge LineString buffered by ``buffer_m`` in the graph CRS. Typical use:
    CCTV locations as points → per-edge counts → ``surveillance`` column for
    :func:`its_route_planner.edge_costs.load_edge_costs_csv`.

    ``G`` must be **projected** (metric CRS), as produced by :func:`load_projected_graph`
    or OSMnx ``project_graph``.
    """
    if len(lons) != len(lats):
        raise ValueError("lons and lats must have the same length")
    crs = G.graph.get("crs")
    if crs is None or not ox.projection.is_projected(crs):
        raise ValueError("Graph must be projected (metric CRS); buffer_m is in meters.")
    _, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
    edges_b = edges.copy()
    edges_b["geometry"] = edges_b.geometry.buffer(float(buffer_m))
    gpts = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(list(lons), list(lats), crs="EPSG:4326"),
        crs="EPSG:4326",
    ).to_crs(G.graph["crs"])
    j = gpts.sjoin(edges_b, predicate="within")
    if j.empty:
        return {}
    s = j.groupby(["u", "v", "key"]).size()
    return {(int(a), int(b), int(c)): int(n) for (a, b, c), n in s.items()}


def write_surveillance_edge_csv(
    path: str | Path,
    counts: dict[tuple[int, int, int], int],
    *,
    scale: float = 1.0,
    skip_zero: bool = True,
) -> int:
    """
    Write ``u,v,key,safety,surveillance,time`` with surveillance ``scale * count``.

    Rows with zero count are omitted when ``skip_zero`` is True.
    Returns number of rows written.
    """
    n = 0
    p = Path(path)
    items = sorted(counts.items(), key=lambda kv: kv[0])
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["u", "v", "key", "safety", "surveillance", "time"])
        for (u, v, k), c in items:
            if skip_zero and c == 0:
                continue
            w.writerow([u, v, k, "", float(c) * scale, ""])
            n += 1
    return n
