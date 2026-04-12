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

We implement **multi-objective label-setting (Pareto) search** (not weighted-sum scalarization):
- Maintain **several** partial path costs per node — every **nondominated** 3-vector seen so far at that node
- **Relax** edges like Dijkstra, but **add** a new label at the head only if it is **not dominated** by labels already stored there
- A **min-heap** picks **which label to expand next**; heap priority is **not** a new objective (**scalar key** on Slide 7)

**Note:** This is **not** MO-A\* — there is **no** admissible heuristic **h(v)** toward the goal; only **g**-style accumulated costs appear in the queue.

---

## Slide 7 — Data structures + dominance

| Structure | Meaning |
|-----------|---------|
| **labels[v]** | **Pairwise nondominated** partial vectors **c** = (T, S, C) for walks **s → v** |
| **Heap** | **(scalar_key, v, c)** — schedule expansion of accepted **(v, c)** |
| **back[(v, c)]** | **(u, c_u, w)** with **c = c_u + w**; **w** = exact edge vector (parallel edges) |

**Init:** **labels[s] = {(0,0,0)}**; **key(c) = T + S + C** (scheduling only — skip **stale** pops).

**Insert `c_new` at v:** reject if duplicate or dominated; else drop labels dominated by **c_new**; append. → **labels[v]** stays nondominated-minimal.

---

## Slide 8 — Main loop (compact)

- **Pop** **(u, c)**; if **c ∉ labels[u]** → **stale**, skip. Else relax each out-edge **w**: **c_new = c + w**; **`insert_nondominated`**; optional **lexicographic trim** to **N** labels (approximate).
- If **c_new** survived: **back[(v,c_new)] = (u,c,w)**, **push** **(v, c_new)**.
- **Stop** early if **`max_heap_pops`** hit. **Output:** reconstruct from each label at **t** → one route per nondominated **c** (exact mode).

---

## Slide 9 — Parallel edges & path reconstruction

- OSM yields a **multigraph**: several edges **u → v** with **different** **(t, s, c)**.
- **back[(v, c_new)]** stores the **full 3-vector w** of the chosen edge, not just endpoints — so reconstruction knows **which** parallel edge was taken.
- Return value: **(total_vector, node_path, edge_vectors)** with **sum(edge_vectors) = total_vector**.

**Stale heap entries:** after a pop, if **c** is no longer in **labels[u]**, **skip** — that partial cost was superseded; extending it would not improve the Pareto set.

---

## Slide 10 — Baseline, safeguards, complexity

**Baseline — single-objective Dijkstra:** minimize **one** component of **w** (e.g. time); reconstruct path; report the **true** **(T,S,C)** along that path for comparison.

**Safeguards** (optional; may break Pareto guarantees):
- **`--max-labels-per-node N`:** after insert, keep only **N** labels at **v** (lexicographic sort on **(T,S,C)**) — can drop nondominated solutions
- **`--max-heap-pops N`:** stop after **N** pops — search may end before all useful labels reach **t**

**Complexity (informal):** if **L** = max nondominated labels per node, roughly **O(|E| · L²)** time for dominance checks per relaxation, **O(|V| · L)** space — motivates safeguards on large city extracts.

---

## Slide 11 — Data & cost model

What we use now:
- **Road graph:** OpenStreetMap via OSMnx (downloaded per bbox)
- **Time:** edge travel time from OSMnx speeds (`travel_time`)
- **Safety & surveillance (default):** highway-type × length **proxies**

Optional “real layer” integration:
- CSV per edge `(u,v,key)` with overrides:
  - `--edge-costs my_edges.csv`

---

## Slide 12 — Privacy/surveillance layer (point pipeline)

If CCTV locations are available as points (lat/lon):
- Count points within a buffer (meters) near each road edge
- Convert counts into per-edge `surveillance` cost

Tooling:
- `scripts/points_to_edge_csv.py` → produces a CSV compatible with `--edge-costs`

---

## Slide 13 — System demo plan (live)

1. **Toy:** `its-route toy` — two Pareto paths on a 4-node graph (sanity check).
2. **Real network:** OSM bbox (e.g. **Bengaluru** Indiranagar→Koramangala corridor or a small NYC bbox).
   - CLI prints **`pareto_total_routes=…`**, baseline (min-time Dijkstra), and up to `--limit` rows.
3. Export **GeoJSON** (`--geojson` for first *N* routes, `--geojson-all` for the full Pareto set).
4. Open **`viewer/index.html`** (Leaflet) — load the GeoJSON file.

---

## Slide 14 — Demo commands (copy/paste)

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

## Slide 15 — Results (what to show)

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

## Slide 16 — Limitations & ethics

- **Data bias & incompleteness:** crime/CCTV datasets can be partial, outdated, or biased.
- **Proxy costs:** default safety/surveillance are proxies; not ground truth.
- **No personal tracking:** we model environmental exposure on roads; we do not identify individuals.

---

## Slide 17 — Future work

- **Multi-Objective A\*** with admissible vector heuristics (extension beyond current label-setting)
- More realistic safety models:
  - crime incidents, crash data, time-of-day variation
- Better surveillance exposure:
  - camera coverage models, not just point counts
- UI improvements:
  - preference sliders, route filtering, and explanations

---

## Slide 18 — Q&A

Questions?

