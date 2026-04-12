# Privacy & Safety Aware Route Planner (Multi-Objective Pareto)

**Course:** [course code]  
**Team / author:** [names]  
**Date:** [date]

## 1. Introduction

- **Problem:** Urban route choice often optimizes only travel time, ignoring **safety** (crime / accident risk) and **surveillance exposure** (e.g. CCTV density).
- **Goal:** Propose routes that are **Pareto-optimal** under three objectives (minimize travel time, safety cost, surveillance cost) so users can choose trade-offs instead of a single “shortest” path.
- **Scope:** Road network from OpenStreetMap (OSM); edge costs from defaults, CSV overrides, and optional point layers (e.g. CCTV → surveillance).

## 2. Related work (brief)

- Multi-objective shortest paths; label-setting / Pareto routing vs weighted-sum scalarization.
- ITS and privacy-aware routing (cite 2–4 papers or course notes).

## 3. Problem formulation

- **Graph:** Directed multigraph **G = (V, E)**; each edge has nonnegative costs **(t_e, s_e, c_e)**: time (seconds), safety, surveillance.
- **Path cost:** Componentwise sum along edges: **(T, S, C) = Σ_e (t_e, s_e, c_e)**.
- **Dominance (minimize all):** Path **p** dominates **q** iff **T_p ≤ T_q**, **S_p ≤ S_q**, **C_p ≤ C_q** with at least one strict inequality.
- **Output:** **Pareto set** of nondominated simple paths from origin to destination (or an **approximation** when safeguards truncate search).

## 4. Algorithm

- **Full write-up:** see **`ALGORITHM.md`** (pseudocode-level detail, data structures, multigraph back-pointers, safeguards, complexity, and relation to A\*).
- **Implemented search:** Multi-objective **label-setting** with a priority queue; each node keeps a **nondominated** set of cost vectors; dominated labels are discarded.
- **Baselines:** Single-objective **Dijkstra** on travel time only (`single_objective_shortest`) for comparison.
- **Safeguards (optional):** `max_labels_per_node`, `max_heap_pops` — may yield **approximate** Pareto sets; document when used.
- **Optional extension (if you add it):** Multi-objective A* with admissible heuristics — not required if above is clearly described.

## 5. Data and cost model

- **Road graph:** OSMnx `graph_from_bbox` → projected graph; travel time from OSMnx speeds / `travel_time`.
- **Default safety / surveillance:** Highway-type × length proxies in code (`road_network.py`).
- **Overrides:** CSV keyed by OSMnx `(u, v, key)` for `time`, `safety`, `surveillance`.
- **Point layers:** `scripts/points_to_edge_csv.py` counts points within a buffer per edge → surveillance column (tune `--scale`).

## 6. Implementation

- **Stack:** Python 3.10+, OSMnx, GeoPandas (point pipeline), CLI `its-route`.
- **Outputs:** Console; **GeoJSON** for map viewer (`viewer/index.html`).
- **Reproducibility:** Pin bbox, seeds for synthetic data, `pytest`, README commands.

## 7. Experiments (suggested)

| Experiment | What to report |
|------------|----------------|
| Toy graph | Two Pareto routes; dominance check. |
| Real bbox | Number of Pareto routes; time vs baseline min-time path; qualitative map. |
| CSV / CCTV overlay | How surveillance costs change route set vs defaults. |
| Truncation | Effect of `--max-labels-per-node` / `--max-heap-pops` on runtime and solution quality. |

Include **1–2 figures** (map screenshots or cost scatter: **T** vs **S** or **C**).

### 7.1 Reproducibility — Bengaluru (explicit OSM nodes)

**Scenario:** bbox **77.61°E–77.67°E**, **12.93°N–12.98°N**; origin OSM node **448306395**, destination **309592695** (Indiranagar → Koramangala corridor, per report).

**One command (prints baseline + first 12 Pareto routes + total count):**

```bash
.venv/bin/its-route osm --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --limit 12 | tee results/bengaluru_reproduction.txt
```

Or: `bash scripts/reproduce_bengaluru.sh`

**Recorded run (this repo, 2026-04-12):** see `results/bengaluru_reproduction.txt`. Summary:

- `pareto_total_routes=75` (OSM edits can shift counts vs an older “76 routes” table — always re-run and paste the printed `pareto_total_routes=…`).
- Baseline (min time): **530.7 s**, safety **84.817**, surveillance **127.225**, **34** hops.
- The printed top-12 Pareto rows match the **shape** of the report’s table (same trade-off story: small time increases can lower surveillance).

**Map export (first 12 routes):**

```bash
.venv/bin/its-route osm --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --limit 12 --geojson results/bengaluru_routes_12.geojson
```

**All Pareto routes (can be large):** add `--geojson-all results/bengaluru_routes_all.geojson`.

## 8. Ethics and limitations

- **Not tracking individuals** — modeling environmental exposure and risk on road segments.
- **Data bias:** Crime and CCTV inventories are incomplete; proxies are not ground truth.
- **Fairness:** High “safety” cost on certain areas must be discussed carefully (avoid stigmatizing neighborhoods without context).

## 9. Conclusion

- What you achieved; what would be needed for deployment (live traffic, validated risk models, user studies).

## Appendix: Commands reference

```bash
.venv/bin/its-route toy
# Snap lat/lon to nearest nodes:
.venv/bin/its-route osm --west W --south S --east E --north N \
  --orig-lat … --orig-lon … --dest-lat … --dest-lon … \
  --show-baseline --geojson routes.geojson
# Or pin exact OSM endpoints (recommended for reproducible report numbers):
.venv/bin/its-route osm --west W --south S --east E --north N \
  --orig-node U --dest-node V --show-baseline --geojson routes.geojson
.venv/bin/python scripts/points_to_edge_csv.py --west W … --points cctv.csv --out edge_surveillance.csv
```

Replace placeholders with real floats; same bbox for graph build and edge CSV.
