"""Sequential diagnostics for dense-combat CPU cost using existing probe flags.

This never edits gameplay source. 'collision-off' changes behavior in the probe only and cannot be shipped.
'enemy-cost' measures existing script callbacks by hand; it is not a rendered FPS benchmark.
"""

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--out", type=Path, default=ROOT / "output/hero-port-20261026/perf/dense-cpu-audit")
    parser.add_argument("--profile", choices=("mobile", "pc-low"), default="mobile")
    parser.add_argument("--frames", type=int, default=1200)
    args = parser.parse_args()
    if args.godot.name.endswith("_console.exe"):
        parser.error("Use the actual executable rather than the console wrapper")
    args.out.mkdir(parents=True, exist_ok=True)
    paths = ["src/actors/actor.gd", "src/actors/enemy/enemy.gd", "src/actors/character_visual.gd",
             "tests/tools/perf_probe.gd", "tests/tools/hero_port_perf.gd"]
    hashes = {p: hashlib.sha256((args.game / p).read_bytes()).hexdigest() for p in paths}
    metadata = {"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "game": str(args.game.resolve()), "source_sha256": hashes, "runs": []}
    renderer = "gl_compatibility" if args.profile == "mobile" else "forward_plus"
    for mode, option in (("control", []), ("collision-off", ["--no_enemy_collide=1"]),
                         ("enemy-cost", ["--enemy_cost=1"])):
        report = args.out / f"{mode}-{args.profile}.json"
        log = args.out / f"{mode}-{args.profile}.log"
        report.unlink(missing_ok=True)
        command = [str(args.godot.resolve()), "--path", str(args.game.resolve()), "--rendering-method", renderer,
                   "--resolution", "1280x720", "res://tests/tools/hero_port_perf.tscn", "--", "--class=knight",
                   "--slot=97", f"--profile={args.profile}", "--map=ruined_forest", "--stress=40",
                   f"--frames={args.frames}", "--body=custom", "--touch=1", "--overlay_settle=20",
                   f"--out={report.resolve()}", *option]
        run = {"mode": mode, "command": command, "log": str(log.resolve())}
        metadata["runs"].append(run)
        print(f"Running {mode}: {args.profile}", flush=True)
        started = time.monotonic()
        with log.open("w", encoding="utf-8") as output:
            process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                process.wait(timeout=240)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
                process.wait(timeout=15)
                run["timed_out"] = True
        run.update(exit_code=process.returncode, elapsed_s=round(time.monotonic() - started, 3))
        text = log.read_text(encoding="utf-8")
        metadata_path = args.out / f"audit-{args.profile}-metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        if process.returncode != 0 or run.get("timed_out") or "SCRIPT ERROR" in text:
            raise SystemExit(f"{mode} failed; inspect {log}")
        if mode == "enemy-cost":
            measured = re.search(r"ENEMYCOST enemies=(\d+) physics_process median ([\d.]+) ms p95 ([\d.]+) ms", text)
            if not measured:
                raise SystemExit(f"Missing ENEMYCOST measurements; inspect {log}")
            run["script_callback_measurement"] = {"enemies": int(measured[1]), "median_ms": float(measured[2]),
                                                   "p95_ms": float(measured[3]), "rendered_fps": False}
        else:
            if not report.is_file():
                raise SystemExit(f"Missing fresh report; inspect {log}")
            result = json.loads(report.read_text(encoding="utf-8"))
            if result["total"]["frame"]["samples"] != args.frames:
                raise SystemExit("Wrong sample count")
            run.update(report=str(report.resolve()), total=result["total"],
                       enemies_in_map=result.get("enemies_in_map"), engaged_at_end=result.get("engaged_at_end"))
            steps = re.search(r"PSTEPS physics steps per frame ([\d.]+)", text)
            if steps:
                run["physics_steps_per_frame"] = float(steps[1])
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"  {mode} finished in {run['elapsed_s']:.2f} s", flush=True)
    changed = [p for p, h in hashes.items() if hashlib.sha256((args.game / p).read_bytes()).hexdigest() != h]
    if changed:
        raise SystemExit(f"Source changed during audit: {changed}")
    print(f"Audit evidence saved to {args.out}", flush=True)


if __name__ == "__main__":
    main()
