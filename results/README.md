# Results: reproduce logs, GeoJSON, and screenshots

Run everything from the **repository root** (`AIFA/`). Network access is required for OSM downloads (Overpass).

## 1. Environment (once per machine)

```bash
cd /path/to/AIFA
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
mkdir -p results
```

## 2. Console results (table + `pareto_total_routes`)

**Bengaluru (report scenario — pinned OSM nodes inside bbox):**

```bash
bash scripts/reproduce_bengaluru.sh results/bengaluru_reproduction.txt
```

Equivalent manual command:

```bash
.venv/bin/its-route osm \
  --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --limit 12 \
  | tee results/bengaluru_reproduction.txt
```

**What to capture for slides/report:** the printed **`pareto_total_routes=…`** line, the **baseline** row, and the first **12** Pareto rows (time, safety, surveillance, hops).

**Quick sanity check (no network — toy graph):**

```bash
.venv/bin/its-route toy
```

## 3. GeoJSON for the map (first N Pareto routes)

Writes one feature per route (colored in the viewer).

```bash
.venv/bin/its-route osm \
  --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --limit 12 \
  --geojson results/bengaluru_routes_12.geojson
```

**Optional — every Pareto route** (can be large / slow to render):

```bash
.venv/bin/its-route osm \
  --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --geojson-all results/bengaluru_routes_all.geojson
```

**Lat/lon snapping** (any city; replace bbox and coordinates):

```bash
.venv/bin/its-route osm --west W --south S --east E --north N \
  --orig-lat OLAT --orig-lon OLON --dest-lat DLAT --dest-lon DLON \
  --show-baseline --limit 12 --geojson results/my_routes.geojson
```

## 4. Map viewer + screenshots

**Option A — auto-load `viewer/routes.geojson` over HTTP**

1. Copy or symlink the GeoJSON next to the viewer (name must be `routes.geojson`):

   ```bash
   cp results/bengaluru_routes_12.geojson viewer/routes.geojson
   ```

2. Serve the repo and open the viewer:

   ```bash
   .venv/bin/python -m http.server 8765
   ```

3. In a browser: `http://127.0.0.1:8765/viewer/`  
   The map should load **`routes.geojson`** automatically and fit bounds.

**Option B — `file://` + Choose file**

Open `viewer/index.html` directly from disk and use **Choose file** to pick `results/bengaluru_routes_12.geojson` (tiles still load from the network).

**Taking screenshots**

- Zoom/pan so all routes are visible; click a line to show the popup if you want costs in the shot.
- **Windows (WSL):** use the Snipping Tool or **Win+Shift+S** on the browser window.
- **Linux desktop:** e.g. **GNOME:** `Shift+Print`, or **Spectacle** / **Flameshot** if installed.
- Save images into `results/` (e.g. `results/map_bengaluru_routes.png`) and reference them from your report or slides.

## 5. Optional: safeguards on huge areas

May **approximate** the Pareto set; use only if the run is too slow or runs out of memory:

```bash
.venv/bin/its-route osm \
  --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --limit 12 \
  --max-labels-per-node 30 --max-heap-pops 500000 \
  --geojson results/bengaluru_routes_12_approx.geojson
```

## Files in this folder (typical)

| File | Produced by |
|------|----------------|
| `bengaluru_reproduction.txt` | `reproduce_bengaluru.sh` or `tee` pipeline in §2 |
| `bengaluru_routes_12.geojson` | `--geojson` command in §3 |

OSM data changes over time; rerun the commands and refresh numbers before final submission.
