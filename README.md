# ITS route planner (multi-objective Pareto)

- Step 1: core graph + multi-objective label-setting search.
- Step 2: OSM via OSMnx (bbox), travel time + placeholder safety/surveillance from `highway` tags.
- Step 3: optional **CSV overrides** per OSM edge `(u, v, key)` for safety/surveillance/time; **GeoJSON** export of Pareto routes.

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/its-route toy
# bbox = west, south, east, north (degrees). Requires network for Overpass.
# Use real floats — do not paste the literal characters "..." as arguments.
.venv/bin/its-route osm --west -74.02 --south 40.72 --east -73.95 --north 40.78 \
  --orig-lat 40.75 --orig-lon -74.00 --dest-lat 40.76 --dest-lon -73.98 \
  --geojson routes.geojson --show-baseline
# Pin exact OSM endpoints (must be inside the bbox graph); prints `pareto_total_routes=…`:
.venv/bin/its-route osm --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 --show-baseline --limit 12
# Large areas: optional caps (approximate Pareto if triggered):
#   --max-labels-per-node 30 --max-heap-pops 500000
# Same bbox; optional edge template / CSV overrides:
.venv/bin/its-route osm --west -74.02 --south 40.72 --east -73.95 --north 40.78 \
  --orig-lat 40.75 --orig-lon -74.00 --dest-lat 40.76 --dest-lon -73.98 \
  --edge-keys-out edges_template.csv
.venv/bin/its-route osm --west -74.02 --south 40.72 --east -73.95 --north 40.78 \
  --orig-lat 40.75 --orig-lon -74.00 --dest-lat 40.76 --dest-lon -73.98 \
  --edge-costs my_edges.csv --geojson routes.geojson
```

**Map viewer:** open `viewer/index.html` in a browser and use **Choose file** to load `routes.geojson`, or from the repo root run `python3 -m http.server 8765` and visit `http://127.0.0.1:8765/viewer/` (auto-loads `viewer/routes.geojson` if you copy the file there).

**Point layer → edge CSV (e.g. CCTV as surveillance):** use the **same bbox** as routing. Put points in a CSV with `lat` and `lon` columns, then:

```bash
.venv/bin/python scripts/points_to_edge_csv.py \
  --west -74.02 --south 40.72 --east -73.95 --north 40.78 \
  --points cctv.csv --buffer-m 25 --scale 0.02 --out edge_surveillance.csv
.venv/bin/its-route osm --west -74.02 --south 40.72 --east -73.95 --north 40.78 \
  --orig-lat 40.75 --orig-lon -74.00 --dest-lat 40.76 --dest-lon -73.98 \
  --edge-costs edge_surveillance.csv --geojson routes.geojson
```

`scale` maps “number of points near this road” into the surveillance cost column; tune it relative to your default highway-based costs. Crime / safety from polygons or another CSV can be added the same way (join externally, then merge into one `--edge-costs` file or extend the script).

**Course write-up:** see `REPORT.md` for a section outline (formulation, algorithm, experiments, ethics). **Algorithm details:** see `ALGORITHM.md` (dominance, label-setting loop, reconstruction, Dijkstra baseline, safeguards, complexity, vs A\*).
