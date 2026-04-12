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
- Road network as a directed graph \(G=(V,E)\)
- Edge costs \((t_e, s_e, c_e)\): travel time, safety cost, surveillance cost

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

- Path cost vector: \((T,S,C)=\sum_{e\in path}(t_e,s_e,c_e)\)
- Dominance (minimization):
  - \(a \prec b\) iff \(a \le b\) componentwise and \(a < b\) in at least one component
- Pareto set: all **non-dominated** route cost vectors.

---

## Slide 6 — Method (algorithm overview)

We implement **multi-objective label-setting search**:
- Each node stores a set of **nondominated labels** (cost vectors)
- When expanding, new labels that are dominated are **pruned**
- Pareto labels at the destination give the **Pareto-optimal routes**

(Optional note if asked: this is a multi-criteria Dijkstra/label-setting style search; A* heuristics are a future extension.)

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

1. Run OSM routing for a small bbox:
   - Returns **Pareto routes** + baseline time-only route
2. Export routes to **GeoJSON**
3. Visualize in `viewer/index.html` (Leaflet)

---

## Slide 11 — Demo commands (copy/paste)

```bash
.venv/bin/its-route osm --west -74.01 --south 40.748 --east -73.995 --north 40.758 \
  --orig-lat 40.7527 --orig-lon -74.0060 --dest-lat 40.7545 --dest-lon -74.0015 \
  --show-baseline --geojson routes.geojson

python3 -m http.server 8765
```

Open: `http://127.0.0.1:8765/viewer/` and load `routes.geojson`.

---

## Slide 12 — Results (what to show)

Suggested visuals:
- Map screenshot with 2–5 Pareto routes (different colors)
- Table of routes:
  - time_s, safety, surveillance, hops
- Short comparison:
  - baseline min-time route vs a safer/lower-surveillance Pareto alternative

Fill in:
- Example Pareto route count: [N]
- Runtime for bbox: [seconds]

---

## Slide 13 — Limitations & ethics

- **Data bias & incompleteness:** crime/CCTV datasets can be partial, outdated, or biased.
- **Proxy costs:** default safety/surveillance are proxies; not ground truth.
- **No personal tracking:** we model environmental exposure on roads; we do not identify individuals.

---

## Slide 14 — Future work

- True **Multi-Objective A\*** heuristics (admissible lower bounds)
- More realistic safety models:
  - crime incidents, crash data, time-of-day variation
- Better surveillance exposure:
  - camera coverage models, not just point counts
- UI improvements:
  - preference sliders, route filtering, and explanations

---

## Slide 15 — Q&A

Questions?

