"""Load per-edge safety / surveillance / time overrides from CSV (join to OSMnx edges)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import networkx as nx

# (u, v, key) -> partial overrides; keys "safety", "surveillance", "time" (optional)
EdgeOverlay = dict[tuple[int, int, int], dict[str, float]]


def load_edge_costs_csv(path: str | Path) -> EdgeOverlay:
    """
    Load edge cost overrides.

    Required columns: ``u``, ``v``, ``key`` (OSMnx MultiDiGraph edge identifiers).

    Optional columns (at least one): ``safety``, ``surveillance``, ``time`` (all nonnegative,
    minimized by the router). Values replace the default highway-based proxies for that edge.

    Header names are case-insensitive; extra columns are ignored.
    """
    rows = _read_csv_rows(path)
    if not rows:
        return {}

    header = {k.lower().strip(): k for k in rows[0].keys()}
    for req in ("u", "v", "key"):
        if req not in header:
            raise ValueError(f"CSV must contain column {req!r}: {path}")

    overlay: EdgeOverlay = {}
    for raw in rows:
        u = int(float(raw[header["u"]]))
        v = int(float(raw[header["v"]]))
        key = int(float(raw[header["key"]]))
        o: dict[str, float] = {}
        for name in ("safety", "surveillance", "time"):
            if name not in header:
                continue
            val = raw.get(header[name])
            if val is None or str(val).strip() == "":
                continue
            f = float(val)
            if f < 0:
                raise ValueError(f"negative {name} for edge {(u, v, key)}")
            o[name] = f
        if not o:
            continue
        overlay[(u, v, key)] = o
    return overlay


def _read_csv_rows(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    with p.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return [dict(row) for row in r]


def write_edge_key_template(G: nx.MultiDiGraph, path: str | Path) -> int:
    """
    Write ``u,v,key,safety,surveillance,time`` with empty cost columns so you can
    fill overrides and pass the file to ``load_edge_costs_csv``.

    ``G`` must be an OSMnx ``MultiDiGraph`` (same object as ``RoadNetwork.projected``).
    """
    p = Path(path)
    n = 0
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["u", "v", "key", "safety", "surveillance", "time"])
        for u, v, k, _d in G.edges(keys=True, data=True):
            w.writerow([int(u), int(v), int(k), "", "", ""])
            n += 1
    return n
