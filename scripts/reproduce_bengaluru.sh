#!/usr/bin/env bash
# Reproduce the Bengaluru (Indiranagar → Koramangala) experiment from the report.
# Requires network (Overpass). Runtime can be several minutes on first download.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p results
OUT="${1:-results/bengaluru_reproduction.txt}"
"$ROOT/.venv/bin/its-route" osm \
  --west 77.61 --south 12.93 --east 77.67 --north 12.98 \
  --orig-node 448306395 --dest-node 309592695 \
  --show-baseline --limit 12 \
  | tee "$OUT"
echo "Wrote log: $OUT"
