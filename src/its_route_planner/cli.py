"""CLI: toy graph (step 1) or OSM bbox routing (step 2+)."""

from __future__ import annotations

import argparse

from its_route_planner.demo import toy_graph
from its_route_planner.edge_costs import load_edge_costs_csv, write_edge_key_template
from its_route_planner.geojson_export import routes_to_geojson, write_geojson
from its_route_planner.road_network import from_bbox
from its_route_planner.search import ParetoSearchStats, pareto_paths, single_objective_shortest


def _cmd_toy(args: argparse.Namespace) -> None:
    g = toy_graph()
    routes = pareto_paths(g, args.source, args.target)
    if not routes:
        print("no path")
        return
    print(f"Pareto routes {args.source} -> {args.target}:")
    for cost, path, _edges in sorted(routes, key=lambda x: x[0][0]):
        print(f"  cost (time, safety, surveillance)={cost}  path={path}")


def _cmd_osm(args: argparse.Namespace) -> None:
    print(
        f"loading OSM bbox west={args.west} south={args.south} east={args.east} north={args.north}..."
    )
    overlay = load_edge_costs_csv(args.edge_costs) if args.edge_costs else None
    net = from_bbox(
        args.west,
        args.south,
        args.east,
        args.north,
        network_type=args.network_type,
        retain_all=args.retain_all,
        edge_overlay=overlay,
    )
    if args.edge_keys_out:
        n = write_edge_key_template(net.projected, args.edge_keys_out)
        print(f"wrote {n} edge rows to {args.edge_keys_out}")

    node_ids = args.orig_node is not None and args.dest_node is not None
    latlon = all(
        x is not None
        for x in (args.orig_lat, args.orig_lon, args.dest_lat, args.dest_lon)
    )
    if node_ids and latlon:
        raise SystemExit("use either --orig-node/--dest-node or all four lat/lon flags, not both")
    if not node_ids and not latlon:
        raise SystemExit(
            "provide --orig-node and --dest-node, or --orig-lat/--orig-lon/--dest-lat/--dest-lon"
        )

    routing_nodes = set(net.routing.nodes())
    if node_ids:
        o, d = int(args.orig_node), int(args.dest_node)
        if o not in routing_nodes or d not in routing_nodes:
            raise SystemExit(
                f"origin/destination node not in bbox graph (origin in graph: {o in routing_nodes}, "
                f"dest in graph: {d in routing_nodes})"
            )
        print(f"origin node={o}  destination node={d}  (explicit OSM node ids)")
    else:
        o = net.nearest_node(float(args.orig_lat), float(args.orig_lon))
        d = net.nearest_node(float(args.dest_lat), float(args.dest_lon))
        print(f"origin node={o}  destination node={d}  (snapped from lat/lon)")
    if args.show_baseline:
        b = single_objective_shortest(net.routing, o, d, 0)
        if b is None:
            print("baseline (min time): no path")
        else:
            _sc, tot, path, _ev = b
            print(
                f"baseline (min time only): time_s={tot[0]:.1f} safety={tot[1]:.3f} "
                f"surv={tot[2]:.3f}  hops={len(path) - 1}"
            )
    stats = ParetoSearchStats()
    routes = pareto_paths(
        net.routing,
        o,
        d,
        max_labels_per_node=args.max_labels_per_node,
        max_heap_pops=args.max_heap_pops,
        stats=stats,
    )
    if stats.truncated:
        print(f"warning: search truncated — {'; '.join(stats.notes)}")
    if not routes:
        print("no path (disconnected subgraph or same node?)")
        return
    print(f"pareto_total_routes={len(routes)}")
    show = routes[: args.limit]
    print(f"Pareto routes (showing {len(show)} of {len(routes)}):")
    for cost, path, _ev in sorted(show, key=lambda x: x[0][0]):
        plen = len(path) - 1
        print(
            f"  time_s={cost[0]:.1f} safety={cost[1]:.3f} surv={cost[2]:.3f}  hops={plen}  nodes={path[:8]}{'...' if len(path) > 8 else ''}"
        )
    if args.geojson:
        fc = routes_to_geojson(net.projected, show)
        write_geojson(args.geojson, fc)
        print(f"wrote GeoJSON: {args.geojson} ({len(fc['features'])} features)")
    if args.geojson_all:
        fc_all = routes_to_geojson(net.projected, routes)
        write_geojson(args.geojson_all, fc_all)
        print(f"wrote GeoJSON (all Pareto): {args.geojson_all} ({len(fc_all['features'])} features)")


def main() -> None:
    p = argparse.ArgumentParser(description="Pareto-optimal multi-objective routes")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("toy", help="4-node demo graph (no network)")
    t.add_argument("--from", dest="source", type=int, default=0)
    t.add_argument("--to", dest="target", type=int, default=3)
    t.set_defaults(func=_cmd_toy)

    o = sub.add_parser("osm", help="Road network from OpenStreetMap (bbox in degrees)")
    o.add_argument("--west", type=float, required=True)
    o.add_argument("--south", type=float, required=True)
    o.add_argument("--east", type=float, required=True)
    o.add_argument("--north", type=float, required=True)
    o.add_argument(
        "--orig-node",
        type=int,
        default=None,
        help="origin graph node id (OSM); use with --dest-node instead of lat/lon",
    )
    o.add_argument(
        "--dest-node",
        type=int,
        default=None,
        help="destination graph node id (OSM); use with --orig-node instead of lat/lon",
    )
    o.add_argument("--orig-lat", type=float, default=None)
    o.add_argument("--orig-lon", type=float, default=None)
    o.add_argument("--dest-lat", type=float, default=None)
    o.add_argument("--dest-lon", type=float, default=None)
    o.add_argument(
        "--network-type",
        default="drive",
        choices=["drive", "drive_service", "walk", "bike", "all"],
    )
    o.add_argument(
        "--retain-all",
        action="store_true",
        help="keep all components (default: largest only)",
    )
    o.add_argument(
        "--limit",
        type=int,
        default=12,
        help="max routes to print (Pareto set can be large)",
    )
    o.add_argument(
        "--edge-costs",
        metavar="PATH",
        help="CSV with columns u,v,key and optional safety,surveillance,time overrides",
    )
    o.add_argument(
        "--edge-keys-out",
        metavar="PATH",
        help="write all u,v,key rows (empty costs) for manual editing, then use --edge-costs",
    )
    o.add_argument(
        "--geojson",
        metavar="PATH",
        help="write first --limit Pareto routes as GeoJSON (WGS84 LineStrings)",
    )
    o.add_argument(
        "--geojson-all",
        metavar="PATH",
        help="write all Pareto routes as GeoJSON (can be large)",
    )
    o.add_argument(
        "--show-baseline",
        action="store_true",
        help="print single-objective shortest path minimizing travel time (Dijkstra)",
    )
    o.add_argument(
        "--max-labels-per-node",
        type=int,
        default=None,
        metavar="N",
        help="cap nondominated labels per node (approximate Pareto; use on large graphs)",
    )
    o.add_argument(
        "--max-heap-pops",
        type=int,
        default=None,
        metavar="N",
        help="stop after N heap extractions (approximate; safety valve)",
    )
    o.set_defaults(func=_cmd_osm)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
