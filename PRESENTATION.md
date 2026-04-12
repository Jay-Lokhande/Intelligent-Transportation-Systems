# Privacy & Safety Aware Route Planner (Multi-Objective Pareto Routing)

**Course:** [course code]  
**Team:** [names]  
**Date:** [date]  

---

## Slide 1 — Title

**Privacy & Safety Aware Route Planner**  
Multi-Objective Route Planning for ITS (Pareto-optimal paths)

- Objectives: **time**, **safety risk**, **surveillance exposure**
- Output: **multiple trade-off routes**, not one “shortest path”

---

## Slide 2 — Motivation (ITS context)

- Standard navigation optimizes **time** only.
- Real commuters care about:
  - **Safety** (crime/accident-prone streets)
  - **Privacy** (surveillance exposure such as CCTV density)
- A single “best route” hides trade-offs. We show **choices**.

---

## Slide 3 — Problem statement

Given:
- Road network as a **directed multigraph** **G = (V, E)** (OSM can have parallel edges)
- Edge costs **(t_e, s_e, c_e)**: travel time, safety cost, surveillance cost

Goal:
- Find **Pareto-optimal** routes from origin to destination:
  - No returned route is strictly worse in all objectives than another.

---

## Slide 4 — Why multi-objective (Pareto) instead of weighted sum?

- Weighted-sum requires choosing weights **before** seeing trade-offs.
- Different users want different trade-offs (fastest vs safest vs lowest surveillance).
- Pareto front provides a **menu of optimal compromises**.

---

## Slide 5 — Core definitions

- Path cost vector: **(T, S, C) = sum over edges e in path of (t_e, s_e, c_e)**
- Dominance (minimization):
  - **a** strictly dominates **b** iff **a ≤ b** componentwise and **a < b** in at least one component
- Pareto set: all **non-dominated** route cost vectors.

---

## Slide 6 — Method (algorithm overview)

We implement **multi-objective label-setting (Pareto) search** — as in the report:
- Each node stores a set of **nondominated labels** (cost vectors)
- A min-heap orders exploration by **sum** of the three costs (scalar key)
- Dominated labels are **pruned**; labels at the destination yield **Pareto-optimal** routes

**Note:** This is **not** MO-A\* (no separate admissible heuristic \(h\)); that remains optional future work.

---

## Slide 7 — Baseline & safeguards

- Baseline: **single-objective Dijkstra** minimizing **time only**
  - Lets us compare “fastest route” vs Pareto set trade-offs
- Safeguards for large graphs (may approximate Pareto):
  - `--max-labels-per-node N`
  - `--max-heap-pops N`

---

## Slide 8 — Data & cost model

What we use now:
- **Road graph:** OpenStreetMap via OSMnx (downloaded per bbox)
- **Time:** edge travel time from OSMnx speeds (`travel_time`)
- **Safety & surveillance (default):** highway-type × length **proxies**

Optional “real layer” integration:
- CSV per edge `(u,v,key)` with overrides:
  - `--edge-costs my_edges.csv`

---

## Slide 9 — Privacy/surveillance layer (point pipeline)

If CCTV locations are available as points (lat/lon):
- Count points within a buffer (meters) near each road edge
- Convert counts into per-edge `surveillance` cost

Tooling:
- `scripts/points_to_edge_csv.py` → produces a CSV compatible with `--edge-costs`

---

## Slide 10 — System demo plan (live)

1. **Toy:** `its-route toy` — two Pareto paths on a 4-node graph (sanity check).
2. **Real network:** OSM bbox (e.g. **Bengaluru** Indiranagar→Koramangala corridor or a small NYC bbox).
   - CLI prints **`pareto_total_routes=…`**, baseline (min-time Dijkstra), and up to `--limit` rows.
3. Export **GeoJSON** (`--geojson` for first *N* routes, `--geojson-all` for the full Pareto set).
4. Open **`viewer/index.html`** (Leaflet) — load the GeoJSON file.

---

## Slide 11 — Demo commands (copy/paste)

**Reproducible Bengaluru run** (explicit OSM nodes — must lie inside bbox):

```bash
cd /path/to/repo
.venv/bin/its-route osm --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --limit 12 \
  --geojson results/bengaluru_routes_12.geojson
# Or: bash scripts/reproduce_bengaluru.sh
```

**Snap from lat/lon** (any city):

```bash
.venv/bin/its-route osm --west -74.01 --south 40.748 --east -73.995 --north 40.758 \
  --orig-lat 40.7527 --orig-lon -74.0060 --dest-lat 40.7545 --dest-lon -74.0015 \
  --show-baseline --geojson routes.geojson
```

**Map viewer:**

```bash
.venv/bin/python -m http.server 8765
```

Open `http://127.0.0.1:8765/viewer/` and load your `.geojson` (or copy it to `viewer/routes.geojson` for auto-load over HTTP).

---

## Slide 12 — Results (what to show)

Suggested visuals:
- **Map:** screenshot from `viewer/index.html` loading `results/bengaluru_routes_12.geojson` (or your run’s file)
- **Table:** first 12 Pareto rows + baseline — columns: time (s), safety, surveillance, hops
- **Story:** baseline is fastest but often **highest surveillance**; accepting ~30–45 s more time can **lower surveillance** via quieter links

**Logged example (repo, 2026-04-12 — OSM can drift):**
- **`pareto_total_routes=75`** (report your own `pareto_total_routes=…` from the CLI)
- **Baseline (min time):** ~**530.7 s**, safety **84.817**, surveillance **127.225**, **34** hops
- Full console log: `results/bengaluru_reproduction.txt`

Update slide numbers if your rerun differs; cite **run date** and “OSM snapshot.”

---

## Slide 13 — Limitations & ethics

- **Data bias & incompleteness:** crime/CCTV datasets can be partial, outdated, or biased.
- **Proxy costs:** default safety/surveillance are proxies; not ground truth.
- **No personal tracking:** we model environmental exposure on roads; we do not identify individuals.

---

## Slide 14 — Future work

- **Multi-Objective A\*** with admissible vector heuristics (extension beyond current label-setting)
- More realistic safety models:
  - crime incidents, crash data, time-of-day variation
- Better surveillance exposure:
  - camera coverage models, not just point counts
- UI improvements:
  - preference sliders, route filtering, and explanations

---

## Slide 15 — Q&A

Questions?

