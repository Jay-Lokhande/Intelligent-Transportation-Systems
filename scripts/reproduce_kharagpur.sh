#!/usr/bin/env bash
# Kharagpur demo: bbox around town; origin ~ railway area, destination ~ IIT Kharagpur.
# Snaps lat/lon to nearest graph nodes. Requires network (Overpass). Runtime varies.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p results
OUT="${1:-results/kharagpur_reproduction.txt}"
"$ROOT/.venv/bin/its-route" osm \
  --west 87.21 --south 22.30 --east 87.34 --north 22.36 \
  --orig-lat 22.3395 --orig-lon 87.2255 \
  --dest-lat 22.3145 --dest-lon 87.2950 \
  --show-baseline --limit 12 \
  | tee "$OUT"
echo "Wrote log: $OUT"
