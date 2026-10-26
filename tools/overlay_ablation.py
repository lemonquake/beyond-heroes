"""Run a matched overlay on/off presentation ablation sequentially; no source is changed.

Use the actual Godot executable, not its console wrapper, so timeout targets the correct process tree.
Both variants run the same custom body, touch controls, 40-enemy workload, 90+20 frame warmup and 1200 samples.
The 'off' variant removes ALL hit/status overlays, so it estimates an upper bound on inactive-pass savings.
"""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OWNED_EVIDENCE_SOURCES = (
    "src/actors/character_visual.gd",
    "src/autoload/perf.gd",
    "src/autoload/settings.gd",
    "tests/tools/perf_probe.gd",
    "tests/tools/hero_port_perf.gd",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--out", type=Path, default=ROOT / "output/hero-port-20261026/perf/overlay-ablation")
    parser.add_argument("--profile", choices=("mobile", "pc-low"), default="mobile")
    parser.add_argument("--frames", type=int, default=1200)
    args = parser.parse_args()
    if args.godot.name.endswith("_console.exe"):
        parser.error("Pass the actual Godot executable rather than the _console.exe wrapper")
    args.out.mkdir(parents=True, exist_ok=True)
    sources = {p: hashlib.sha256((args.game / p).read_bytes()).hexdigest() for p in OWNED_EVIDENCE_SOURCES}
    metadata = {"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "game": str(args.game.resolve()), "godot": str(args.godot.resolve()),
                "source_sha256": sources, "runs": []}
    renderer = "gl_compatibility" if args.profile == "mobile" else "forward_plus"
    for mode in ("on", "off"):
        report = args.out / f"overlay-{mode}-{args.profile}.json"
        log = args.out / f"overlay-{mode}-{args.profile}.log"
        report.unlink(missing_ok=True)  # a prior report cannot make a failed run appear successful
        command = [str(args.godot.resolve()), "--path", str(args.game.resolve()), "--rendering-method", renderer,
                   "--resolution", "1280x720", "res://tests/tools/hero_port_perf.tscn", "--", "--class=knight",
                   "--slot=97", f"--profile={args.profile}", "--map=ruined_forest", "--stress=40",
                   f"--frames={args.frames}", "--body=custom", "--touch=1", "--overlay_settle=20",
                   f"--out={report.resolve()}"]
        if mode == "off":
            command.append("--no_overlay=1")
        started = time.monotonic()
        run = {"mode": mode, "command": command, "report": str(report.resolve()), "log": str(log.resolve())}
        metadata["runs"].append(run)
        print(f"Running overlays {mode}: {args.profile}", flush=True)
        with log.open("w", encoding="utf-8") as output:
            process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                process.wait(timeout=240)
            except subprocess.TimeoutExpired:
                # taskkill follows only the process this runner started and its descendants.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
                process.wait(timeout=15)
                run["timed_out"] = True
            run["exit_code"] = process.returncode
        run["elapsed_s"] = round(time.monotonic() - started, 3)
        metadata_path = args.out / f"pair-{args.profile}-metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        if process.returncode != 0 or run.get("timed_out") or not report.is_file():
            raise SystemExit(f"Overlay {mode} run failed; inspect {log}")
        if "SCRIPT ERROR" in log.read_text(encoding="utf-8"):
            raise SystemExit(f"Overlay {mode} has a script error; inspect {log}")
        data = json.loads(report.read_text(encoding="utf-8"))
        frame = data["total"]["frame"]
        if frame["samples"] != args.frames:
            raise SystemExit(f"Overlay {mode}: expected {args.frames} samples, got {frame['samples']}")
        if mode == "off" and "OVERLAY_ABLATION cleared=" not in log.read_text(encoding="utf-8"):
            raise SystemExit("Off run did not log the explicit overlay ablation")
        run["total"] = data["total"]
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"  median {frame['median']:.2f} ms; p95 {frame['p95']:.2f}; p99 {frame['p99']:.2f}; "
              f"draws {data['total']['draws']['median']:.0f}; duration {frame['duration_s']:.2f} s", flush=True)
    changed = [p for p, h in sources.items() if hashlib.sha256((args.game / p).read_bytes()).hexdigest() != h]
    if changed:
        raise SystemExit(f"Source changed during the pair: {changed}")
    print(f"Matched reports saved to {args.out}", flush=True)


if __name__ == "__main__":
    main()
