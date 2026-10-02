"""Repeatable frame-time matrix for the beta: same scenarios, same settings, warmed up, repeated, then summarised.

    python tools/perf_matrix.py run --label baseline --godot "C:/path/Godot.exe" [--repeats 3] [--profiles pc-low,mobile] [--only town,forest]
    python tools/perf_matrix.py compare baseline candidate            # markdown table of the two labels
    python tools/perf_matrix.py run --root output/map-design-20261003/perf --set map-design --label map-design-baseline ...

Each run is one Godot process (tests/tools/beta_release_perf.tscn: boots the real game, walks the hero through the map's spawn
points, discards a warm-up, then samples frames with vsync and the frame cap off). Nothing is saved: a hidden save slot is used and
the quality profile is applied for the run only. The window is 1280x720. "mobile" runs the OpenGL (gl_compatibility) renderer with
the efficiency preset; it is the phone's *settings on this PC*, not a phone measurement.

Results go to output/beta-20261002/perf/<label>/ as one JSON per run plus summary.json (median of the per-run medians and
the worst per-run p95/p99, so one slow run cannot hide).
"""
import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "beta-20261002" / "perf"

SCENARIOS = {
    "town": {"map": "sanctuary", "spots": "3", "frames": "300"},
    "town-wide-map": {"map": "sanctuary", "spots": "3", "frames": "300", "minimap_zoom": "2"},
    "forest": {"map": "ruined_forest", "spots": "3", "frames": "300"},
    "interior": {"map": "int_tavern", "spots": "2", "frames": "300"},
    "dungeon": {"map": "catacombs", "spots": "3", "frames": "300"},
    "combat": {"map": "ruined_forest", "stress": "40", "frames": "300"},
    "combat-12": {"map": "ruined_forest", "stress": "12", "frames": "300"},
}
# Map-design pass (2026-10-03): every island route, Agdao's terraces, the interiors with the most furniture and the dungeon
# floors the brief names. `--set map-design` runs these plus the original seven; spots are the maps' own spawn points.
MAP_DESIGN = {
    "westreach": {"map": "westreach", "spots": "3", "frames": "300"},
    "olivar": {"map": "olivar", "spots": "3", "frames": "300"},
    "wyman": {"map": "wyman_outpost", "spots": "3", "frames": "300"},
    "causeway": {"map": "weeping_causeway", "spots": "2", "frames": "300"},
    "agdao": {"map": "agdao", "spots": "4", "frames": "300"},
    "coilwood": {"map": "zr_coilwood", "spots": "3", "frames": "300"},
    "barrens": {"map": "zr_barrens", "spots": "3", "frames": "300"},
    "bridge": {"map": "bridge_of_death", "spots": "2", "frames": "300"},
    "citadel": {"map": "zr_citadel", "spots": "3", "frames": "300"},
    "guildhouse": {"map": "int_guildhouse", "spots": "2", "frames": "300"},
    "domestic": {"map": "int_netmender", "spots": "2", "frames": "300"},
    "dg-deeps": {"map": "dg_deeps_2", "spots": "3", "frames": "300"},
    "dg-warren": {"map": "dg_warren_2", "spots": "3", "frames": "300"},
    "dg-ember": {"map": "dg_ember_3", "spots": "3", "frames": "300"},
    "dg-barrow": {"map": "dg_barrow_2", "spots": "3", "frames": "300"},
    "dg-orrery": {"map": "dg_orrery_2", "spots": "3", "frames": "300"},
    "dg-jade": {"map": "dg_jade_sepulchre_3", "spots": "3", "frames": "300"},
    "dg-obsidian": {"map": "dg_obsidian_engine_3", "spots": "3", "frames": "300"},
    "dg-vein": {"map": "dg_veinworks_7", "spots": "3", "frames": "300"},
}
SETS = {"beta": SCENARIOS, "map-design": {**SCENARIOS, **MAP_DESIGN}}
PROFILES = {
    "pc-low": {"renderer": "forward_plus"},
    "mobile": {"renderer": "gl_compatibility"},
}
METRICS = ("frame", "gpu", "script", "physics", "draws", "prims", "objects", "lights", "cpu_render")


ALL = {**SCENARIOS, **MAP_DESIGN}


GAME = ROOT / "game"


def run_one(godot, label, scenario, profile, repeat):
    spec, prof = ALL[scenario], PROFILES[profile]
    folder = OUT / label
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / f"{scenario}__{profile}__r{repeat}.json"
    command = [str(godot), "--path", str(GAME), "--rendering-method", prof["renderer"], "--resolution", "1280x720",
               "res://tests/tools/beta_release_perf.tscn", "--", "--class=knight", "--slot=97", f"--profile={profile}",
               f"--out={report}"] + [f"--{key}={value}" for key, value in spec.items()]
    log = folder / f"{scenario}__{profile}__r{repeat}.log"
    started = time.time()
    with log.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            process.wait(timeout=240)
        except subprocess.TimeoutExpired:
            process.kill()      # only the process this script started
            raise SystemExit(f"{scenario}/{profile} r{repeat} exceeded four minutes")
    if process.returncode != 0 or not report.is_file():
        raise SystemExit(f"{scenario}/{profile} r{repeat} failed; see {log}")
    print(f"  {scenario:9s} {profile:7s} r{repeat}: {time.time() - started:5.0f} s", flush=True)
    return json.loads(report.read_text())


def summarise(label):
    rows = {}
    for path in sorted((OUT / label).glob("*__r*.json")):
        scenario, profile, _ = path.stem.rsplit("__", 2)
        total = json.loads(path.read_text())["total"]
        rows.setdefault((scenario, profile), []).append(total)
    summary = {}
    for (scenario, profile), runs in rows.items():
        entry = {"runs": len(runs)}
        for metric in METRICS:
            if metric not in runs[0]:
                continue
            entry[metric] = {"median": round(statistics.median(r[metric]["median"] for r in runs), 2),
                             "p95": round(max(r[metric].get("p95", r[metric]["median"]) for r in runs), 2)}
        entry["frame"]["p99"] = round(max(r["frame"].get("p99", r["frame"]["median"]) for r in runs), 2)
        summary[f"{scenario}/{profile}"] = entry
    (OUT / label / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def compare(a, b):
    first, second = summarise(a), summarise(b)
    print(f"| scenario | profile | runs | frame median {a} -> {b} (ms) | p95 | p99 | script ms | physics ms | gpu ms | draws | lights |")
    print("| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |")
    for key in first:
        if key not in second:
            continue
        scenario, profile = key.split("/")
        x, y = first[key], second[key]

        def pair(metric, field="median"):
            return f"{x[metric][field]} -> {y[metric][field]}" if metric in x and metric in y else "n/a"
        print(f"| {scenario} | {profile} | {x['runs']}/{y['runs']} | {pair('frame')} | {pair('frame', 'p95')} | {pair('frame', 'p99')} | "
              f"{pair('script')} | {pair('physics')} | {pair('gpu')} | {pair('draws')} | {pair('lights')} |")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("--label", required=True)
    run.add_argument("--godot", required=True, type=Path)
    run.add_argument("--repeats", type=int, default=3)
    run.add_argument("--profiles", default="pc-low,mobile")
    run.add_argument("--only", default="")
    run.add_argument("--set", default="beta", choices=sorted(SETS))
    run.add_argument("--root", default="", help="output root (default output/beta-20261002/perf)")
    run.add_argument("--keep-going", action="store_true", help="record a failed run and continue")
    run.add_argument("--game", default="", help="game project folder (default game/; a frozen copy measures a baseline)")
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("a")
    cmp_.add_argument("b")
    cmp_.add_argument("--root", default="")
    args = parser.parse_args()
    global OUT, GAME
    if getattr(args, "game", ""):
        GAME = Path(args.game)
    if args.root:
        OUT = (ROOT / args.root) if not Path(args.root).is_absolute() else Path(args.root)
    if args.action == "compare":
        compare(args.a, args.b)
        return
    print("A first run per scenario is a warm-up for the disk cache and is kept in the folder but not summarised separately.")
    for repeat in range(1, args.repeats + 1):
        for scenario in (args.only.split(",") if args.only else list(SETS[args.set])):
            for profile in args.profiles.split(","):
                try:
                    run_one(args.godot, args.label, scenario, profile, repeat)
                except SystemExit as failure:
                    if not args.keep_going:
                        raise
                    print("  FAILED", failure, flush=True)
    summarise(args.label)
    print("summary:", OUT / args.label / "summary.json")


if __name__ == "__main__":
    sys.exit(main())
