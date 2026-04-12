# Algorithms in detail

This document describes the routing algorithms implemented in `its_route_planner`: **multi-objective label-setting (Pareto) search**, optional **approximation safeguards**, **single-objective Dijkstra** (baseline), and the **dominance** primitives used for label sets.

Math below uses **plain text and code** (no LaTeX-style escape sequences), so plain-text search and naive regex will not hit tricky backslash-plus-parenthesis patterns.

---

## 1. Problem setup

### 1.1 Graph

- **Input:** a **directed multigraph** **G = (V, E)**.
- Each **directed edge** from **u** to **v** has a **nonnegative cost 3-vector**

  **w(e) = (t_e, s_e, c_e)** — same as edge attributes **time**, **safety**, **surveillance** in code — interpreted as **travel time** (seconds), **safety cost**, and **surveillance cost** (unitless, higher = worse), all **to be minimized**.

Parallel edges **u → v** are allowed (multiple `Edge` objects in the adjacency list). They are distinguished by their **full** cost vector when relaxed, and by storing the **actual edge vector** used on the back-pointer (Section 4).

### 1.2 Path cost

For a path **p = (v₀, …, v_k)** with edges **e_i**: v_{i−1} → v_i,

**C(p) = sum over i of w(e_i)** (component-wise sum).

### 1.3 Dominance and Pareto optimality

For two cost vectors **a**, **b** in ℝ³₊:

- **a** **dominates** **b** (strict Pareto dominance for minimization) iff  
  **a[j] ≤ b[j]** for all j ∈ {1,2,3} and **a[j] < b[j]** for **at least one** j.

A path is **Pareto-optimal** (among all **s**–**t** paths) if **no** other **s**–**t** path has a cost vector that dominates its cost vector.

**Goal:** enumerate **one** **s**–**t** path per **nondominated** cost vector at **t** (the Pareto set in objective space; multiple paths with the **same** **C** are deduplicated by `insert_nondominated` when vectors are exactly equal).

---

## 2. Dominance maintenance at a node (`pareto.py`)

Each node **v** holds a finite set `labels[v]` of **pairwise nondominated** vectors (partial path costs from **s** to **v**).

### 2.1 `insert_nondominated(labels, candidate)`

Implemented logic:

1. If `candidate` is **already** in `labels` (exact tuple equality), **reject** (return `False`).
2. If **any** existing label **dominates** `candidate`, **reject**.
3. Otherwise **remove** every existing label **dominated by** `candidate`.
4. **Append** `candidate` and return `True`.

This keeps `labels` as an **inclusion-minimal** set such that no stored vector dominates another—i.e. the **nondominated** set among all insertions performed.

---

## 3. Multi-objective label-setting search (`pareto_paths`)

This is the main routine in `search.py`. It is a **label-setting / multi-criteria** scheme: extend partial paths by edges, but keep **multiple** nondominated cost vectors per node instead of a single distance.

### 3.1 Data structures

| Structure | Role |
|-----------|------|
| `labels[v]` | `list` of nondominated **partial** cost vectors **c** at node **v** |
| `heap` | Min-heap of triples `(key, v, c)` to schedule expansions |
| `back[(v, c)]` | Back-pointer: predecessor node, predecessor cost vector at predecessor, and **edge** vector used for the step into **v** (for multigraph reconstruction) |

**Initialization**

- `labels[s] = {(0,0,0)}`.
- `back[(s,(0,0,0))] = (None, None, None)`.
- Push `(key(s,(0,0,0)), s, (0,0,0))` onto the heap.

**Scalar heap key**

**key(v, c) = c[0] + c[1] + c[2]** (implementation: `_scalar_key(c)`).

This **does not** define a new objective; it only **orders** which partial label to expand next. Stale or dominated entries are skipped (Section 3.3).

### 3.2 Main loop (conceptual)

```
while heap not empty:
    if max_heap_pops exceeded: break   # optional safeguard

    pop (key, u, c) from heap
    if c is not in labels[u]:          # stale entry → skip
        continue

    for each outgoing edge e from u to v with vector w:
        c_new = c + w   (component-wise)

        L = labels[v]  (create empty if needed)
        if not insert_nondominated(L, c_new):
            continue   # dominated or duplicate

        # optional: max_labels_per_node → trim L (approximate; Section 5)
        if c_new was trimmed out of L:
            continue   # do not enqueue or set back-pointer

        back[(v, c_new)] = (u, c, w)
        push (key(v,c_new), v, c_new) onto heap
```

After termination, every vector in `labels[t]` is **nondominated among labels that reached t** under **exact** search (no trimming / early stop). Reconstruction (Section 4) yields a concrete path for each such vector.

### 3.3 Why “stale” heap entries are safe

Whenever a label at **u** is popped, if that exact vector **c** is **no longer** in `labels[u]` (because it was removed when another label dominated it, or after trimming), the algorithm **skips** expansion. Any extension of a dominated partial cost would not contribute to a Pareto-optimal full path under exact dominance pruning; skipping those pops is standard in multicriteria search with a heap.

### 3.4 Correctness intuition (exact mode)

- **Soundness:** Every stored label at **v** corresponds to **some** walk from **s** with that cost (induction on relaxations).
- **Nondomination at each node:** `insert_nondominated` enforces pairwise nondomination among stored labels at **v**.
- **Pareto set at t:** Any **s**–**t** path whose cost is **dominated** by another **s**–**t** path would induce a dominated label at **t**; such labels are never kept. Conversely, under exact search (no caps), standard label-setting arguments for additive vector costs on finite graphs ensure that **nondominated** labels at **t** correspond to **Pareto-optimal** paths (up to tie-breaking among paths with **identical** **C**).

**Caveat:** **Zero-cost cycles** (e.g. all three components zero on a cycle) can break finiteness; the implementation assumes **positive travel time** on edges used in practice so that partial costs strictly increase along any simple relevant path and the label set remains finite.

---

## 4. Path reconstruction and parallel edges

Back-pointer for a **successful** label at **(v, c_new)**:

**back[(v, c_new)] = (u, c_u, w_uv)**

where **c_new = c_u + w_uv** for the **chosen** parallel edge.

**Reconstruction:** start at **(t, c_t)**, follow `back` until **(s, 0)**, collecting node sequence and edge vectors; reverse both lists.

The returned triple per solution is:

**(C_path, [v₀,…,v_k], [w₁,…,w_k])**

so that `sum_vectors(edge_vectors) == C_path` even when multiple edges share the same endpoints.

---

## 5. Approximation safeguards (optional)

### 5.1 `max_heap_pops`

After **N** heap **pops**, the loop **stops**. Search may terminate before all useful labels reach **t**. Recorded in `ParetoSearchStats` as truncated.

### 5.2 `max_labels_per_node`

After a successful `insert_nondominated`, if `|labels[v]| > N`, the list is **sorted lexicographically** by **(c₁, c₂, c₃)** and **truncated** to the first **N** vectors.

- **Effect:** Some nondominated labels may be **discarded** → **no longer guaranteed Pareto-optimal** globally.
- **Implementation detail:** If the newly inserted vector is dropped by trimming, the code **does not** push it to the heap or record `back` for it.

---

## 6. Baseline: single-objective Dijkstra (`single_objective_shortest`)

**Purpose:** Compare the Pareto set to a **single** route that minimizes **one** edge weight:

- `objective = 0` → minimize sum of **t_e**
- `objective = 1` → minimize sum of **s_e**
- `objective = 2` → minimize sum of **c_e**

**Algorithm:** Classic Dijkstra:

- `dist[v]` = best scalar distance found so far.
- Relax each edge with weight **w = edge.vector()[objective]**.
- Predecessor map stores `(prev_node, full_edge_vector)` for reconstruction.

**Output:** `(scalar_sum, full_vector_sum, node_path, edge_vectors)` where `full_vector_sum` is the **true** 3-vector sum along that path (not just the minimized component).

---

## 7. Complexity (informal)

Let **L** be the **maximum** number of nondominated labels stored at any node during the run.

- **Time:** Roughly **O(|E| · L²)** in the worst case for naive dominance checks per insertion (each insert scans `labels[v]`). With caps, **L ≤ N**.
- **Space:** **O(|V| · L)** for label lists plus heap and back-pointers.

In dense urban OSM subgraphs, **L** can grow large; hence **CLI safeguards** and **bbox** size matter.

---

## 8. Relation to A*

**This codebase does not implement multi-objective A star (MO-A*).** There is **no** separate admissible heuristic **h(v)** used in an **f = g + h** style for each objective. The heap key is only a **scheduling** priority on the **current partial cost** **c**.

A natural extension (future work) would attach a vector lower bound **h(v)** toward **t** and define consistent rules for expanding labels while preserving Pareto optimality (e.g. NAMOA*-style algorithms).

---

## 9. File map

| File | Role |
|------|------|
| `pareto.py` | `dominates`, `insert_nondominated` |
| `search.py` | `pareto_paths`, `_reconstruct_path`, `single_objective_shortest`, safeguards |
| `graph.py` | `Edge`, `Graph` adjacency |
| `road_network.py` | OSM → `Edge` costs **(t, s, c)** |

For reproducible experiments and CLI flags, see `REPORT.md` section 7.1 and `README.md`.
