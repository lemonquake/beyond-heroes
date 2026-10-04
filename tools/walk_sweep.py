"""Walk every map (or a sample of dungeon floors) with tests/tools/walk_probe.tscn and table the frame times (bh-037).

    python tools/walk_sweep.py --godot "C:/Users/Lemon PC/Desktop/Godot.exe" --label fix [--game game] [--seconds 45]
        [--maps agdao,sanctuary] [--floors sample|all] [--uncap] [--extra "--efficiency_mode=false"]

Each map is one fresh Godot process (a level-1 knight in hidden slot 97, god mode, the player's own settings.cfg read but
never written). Dungeons: "sample" walks the first and last floor of every dungeon. Results: output/bh-037/sweep/<label>/
<map>.json plus summary.md (worst 1 % low first). A map passes when its 1 % low is at least 60 fps and no frame
took longer than 50 ms.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "bh-037" / "sweep"


def all_maps(godot, game):
    tmp = Path(game) / "tests" / "tools" / "zz_sweep_list_tmp.gd"
    tmp.write_text('extends SceneTree\nfunc _init() -> void:\n\tawait process_frame\n'
                   '\tprint("MAPS ", " ".join(root.get_node("DB").maps.keys().map(func(k): return String(k))))\n\tquit()\n')
    try:
        out = subprocess.run([godot, "--headless", "--path", str(game), "--script", "res://tests/tools/zz_sweep_list_tmp.gd"],
                             capture_output=True, text=True, timeout=180).stdout
    finally:
        tmp.unlink(missing_ok=True)
        Path(str(tmp) + ".uid").unlink(missing_ok=True)
    line = next(l for l in out.splitlines() if l.startswith("MAPS "))
    return line.split()[1:]


def pick(ids, floors):
    if floors == "all":
        return ids
    fixed = [i for i in ids if not i.startswith("dg_")]
    fam = {}
    for i in ids:
        m = re.match(r"(dg_.+)_(\d+)$", i)
        if m:
            fam.setdefault(m.group(1), []).append(int(m.group(2)))
    dg = []
    for f, ns in sorted(fam.items()):
        dg += [f"{f}_{min(ns)}"] + ([f"{f}_{max(ns)}"] if max(ns) != min(ns) else [])
    return sorted(fixed) + dg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--godot", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--game", default=str(ROOT / "game"))
    ap.add_argument("--seconds", default="45")
    ap.add_argument("--maps", default="")
    ap.add_argument("--floors", default="sample")
    ap.add_argument("--uncap", action="store_true")
    ap.add_argument("--extra", default="")
    a = ap.parse_args()
    folder = OUT / a.label
    folder.mkdir(parents=True, exist_ok=True)
    ids = a.maps.split(",") if a.maps else pick(all_maps(a.godot, a.game), a.floors)
    print(f"{len(ids)} maps", flush=True)
    for i, m in enumerate(ids):
        rep = folder / f"{m}.json"
        if rep.exists():
            continue
        cmd = [a.godot, "--path", a.game, "res://tests/tools/walk_probe.tscn", "--", "--class=knight", "--slot=97",
               f"--map={m}", "--windowed=1920x1080", f"--seconds={a.seconds}", "--spike=25", f"--out={rep}"]
        if a.uncap:
            cmd.append("--uncap=1")
        cmd += a.extra.split()
        t0 = time.time()
        log = folder / f"{m}.log"
        with open(log, "w", encoding="utf-8", errors="replace") as fh:
            try:
                subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=int(a.seconds) + 420)
            except subprocess.TimeoutExpired:
                print(f"[{i + 1}/{len(ids)}] {m}: TIMEOUT", flush=True)
                continue
        if rep.exists():
            d = json.loads(rep.read_text())
            print(f"[{i + 1}/{len(ids)}] {m}: avg {d['avg_fps']} fps, 1% low {d['low1_fps']}, max {d['max_ms']} ms, "
                  f">17ms {d['over_17ms']}, >33ms {d['over_33ms']} ({time.time() - t0:.0f} s)", flush=True)
        else:
            print(f"[{i + 1}/{len(ids)}] {m}: no report (see {log.name})", flush=True)
    summarise(folder)


def summarise(folder):
    rows = []
    for f in sorted(folder.glob("*.json")):
        d = json.loads(f.read_text())
        worst = sorted(d.get("spikes", []), key=lambda e: -e["frame"])[:3]
        rows.append((d["low1_fps"], f.stem, d, worst))
    rows.sort(key=lambda r: r[0])
    lines = ["| map | avg fps | 1% low | median ms | p99 ms | max ms | >16.7 ms | >33 ms | pass | worst spikes |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for low, name, d, worst in rows:
        ok = low >= 60 and d["max_ms"] <= 50
        ws = "; ".join(f"{e['frame']} ms ({'pipes %d ' % e['pipelines'] if e['pipelines'] else ''}"
                       f"{'+'.join(list(e['added'])[:2])})" for e in worst)
        lines.append(f"| {name} | {d['avg_fps']} | {low} | {d['median_ms']} | {d['p99_ms']} | {d['max_ms']} | {d['over_17ms']} | "
                     f"{d['over_33ms']} | {'yes' if ok else 'NO'} | {ws} |")
    (folder / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        summarise(OUT / sys.argv[2])
    else:
        main()
