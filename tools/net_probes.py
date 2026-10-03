"""Run the local multi-process multiplayer probes (custom host + joiners on this PC) and summarise them.

    python tools/net_probes.py --godot "C:/path/Godot.exe" [--only explore,trade] [--out output/net-probes]

Each probe starts a host and one or two joiners as separate Godot processes on hidden save slots (90-94), waits for
them to finish (each process exits 0 on PASS) and prints the probe's own ok/FAIL lines. Logs go to --out. The
dedicated-server stages (twelve clients, restart, hand-off, bandwidth) are in server/integration_probe.py.
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "game"

# name -> list of (label, extra args); windowed probes take screenshots, the rest run headless
PROBES = {
    "explore": {"scene": "net_probe_explore", "headless": False, "roles": [
        ("host", ["--role=host", "--class=knight", "--slot=94", "--map=ruined_forest"]),
        ("join", ["--role=join", "--class=ranger", "--slot=93", "--map=sanctuary"])]},
    "trade": {"scene": "net_probe_trade", "headless": False, "roles": [
        ("host", ["--role=host", "--class=knight", "--slot=94", "--map=sanctuary"]),
        ("join", ["--role=join", "--class=ranger", "--slot=93", "--map=sanctuary"])]},
    "arena": {"scene": "net_probe_arena", "headless": True, "roles": [
        ("host", ["--role=host", "--class=knight", "--slot=94", "--map=wyman_outpost"]),
        ("join", ["--role=join", "--class=mage", "--slot=93", "--map=wyman_outpost"])]},
    "guild": {"scene": "net_probe_guild", "headless": True, "roles": [
        ("host", ["--role=host", "--class=knight", "--slot=94", "--map=sanctuary"]),
        ("join", ["--role=join", "--class=mage", "--slot=93", "--map=sanctuary"])]},
    "team": {"scene": "net_probe_team", "headless": False, "roles": [
        ("host", ["--role=host", "--class=knight", "--name=host", "--map=sanctuary", "--slot=90"]),
        ("scout", ["--role=scout", "--class=knight", "--name=scout", "--map=sanctuary", "--slot=91"]),
        ("ally", ["--role=ally", "--class=knight", "--name=ally", "--map=sanctuary", "--slot=92"])]},
}
RESULT = re.compile(r"^(EXPLORE|TRADE|ARENA|GUILD|TEAM)\[|SCRIPT ERROR|Parse Error")


def run(godot, name, out, limit):
    spec = PROBES[name]
    procs = []
    for label, extra in spec["roles"]:
        cmd = [godot] + (["--headless"] if spec["headless"] else ["--resolution", "960x540"]) + [
            "--path", str(GAME), f"res://tests/tools/{spec['scene']}.tscn", "--"] + extra + [f"--out={out}"]
        log = (out / f"{name}-{label}.log").open("w", encoding="utf-8")
        procs.append((label, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)), log))
        time.sleep(3.0)      # the host opens its room first
    ok = True
    for label, proc, log in procs:
        try:
            code = proc.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            proc.kill()      # only the processes this script started
            code = "timeout"
        log.close()
        ok = ok and code == 0
        lines = [l for l in (out / f"{name}-{label}.log").read_text(encoding="utf-8", errors="replace").splitlines() if RESULT.search(l)]
        print(f"--- {name}/{label}: exit {code}")
        for line in lines:
            if "FAIL" in line or "ERROR" in line or "PASS" in line or "SUMMARY" in line:
                print("   ", line[:200])
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--only", default="")
    parser.add_argument("--out", default="output/net-probes")
    parser.add_argument("--limit", type=int, default=300, help="seconds each process may take")
    parser.add_argument("--game", default="", help="game project folder (default game/; a frozen copy runs an older revision)")
    args = parser.parse_args()
    global GAME
    if args.game:
        GAME = Path(args.game)
    out = (ROOT / args.out) if not Path(args.out).is_absolute() else Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = args.only.split(",") if args.only else list(PROBES)
    results = {name: run(args.godot, name, out, args.limit) for name in names}
    print("NET PROBES:", ", ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in results.items()))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
