#!/usr/bin/env python3
"""
Build a --edge-costs CSV from point locations (e.g. CCTV) near road edges.

Example:
  python3 scripts/points_to_edge_csv.py \\
    --west -74.05 --south 40.70 --east -73.90 --north 40.80 \\
    --points data/cctv.csv --lon-col lon --lat-col lat \\
    --buffer-m 25 --scale 0.02 --out edge_surveillance.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from its_route_planner.point_layers import (  # noqa: E402
    surveillance_counts_near_points,
    write_surveillance_edge_csv,
)
from its_route_planner.road_network import load_projected_graph  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(
        description="Count points per OSM edge (buffer) and write edge-cost CSV"
    )
    p.add_argument("--west", type=float, required=True)
    p.add_argument("--south", type=float, required=True)
    p.add_argument("--east", type=float, required=True)
    p.add_argument("--north", type=float, required=True)
    p.add_argument("--points", type=Path, required=True, help="CSV with lat/lon columns")
    p.add_argument("--lat-col", default="lat")
    p.add_argument("--lon-col", default="lon")
    p.add_argument(
        "--buffer-m",
        type=float,
        default=25.0,
        help="buffer distance in meters around each road centerline",
    )
    p.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="multiply surveillance count by this (tune cost units)",
    )
    p.add_argument("--out", type=Path, required=True, help="output CSV path")
    p.add_argument(
        "--include-zero",
        action="store_true",
        help="write rows with zero counts too (large file)",
    )
    p.add_argument("--network-type", default="drive")
    p.add_argument("--retain-all", action="store_true")
    args = p.parse_args()

    df = pd.read_csv(args.points)
    lat_col = args.lat_col.lower()
    lon_col = args.lon_col.lower()
    cols = {c.lower(): c for c in df.columns}
    if lat_col not in cols or lon_col not in cols:
        raise SystemExit(f"need columns {args.lat_col!r} and {args.lon_col!r} (case-insensitive)")
    lat = df[cols[lat_col]].astype(float)
    lon = df[cols[lon_col]].astype(float)

    print("loading OSM graph (network)...")
    G = load_projected_graph(
        args.west,
        args.south,
        args.east,
        args.north,
        network_type=args.network_type,
        retain_all=args.retain_all,
    )
    counts = surveillance_counts_near_points(G, lons=list(lon), lats=list(lat), buffer_m=args.buffer_m)
    n = write_surveillance_edge_csv(
        args.out,
        counts,
        scale=args.scale,
        skip_zero=not args.include_zero,
    )
    print(f"wrote {n} rows to {args.out} ({len(counts)} edges with >=1 point)")


if __name__ == "__main__":
    main()
