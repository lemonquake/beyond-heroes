"""Exercise a real dedicated server with twelve Godot clients and a restart.

Runs in an isolated temporary database and leaves only logs in output/.
"""
import argparse
import contextlib
import json
import os
import re
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


# Engine messages printed while a headless process quits; they say nothing about gameplay or networking.
TEARDOWN = re.compile(r"(still in use at exit|leaked at exit|ObjectDB instances|RID allocations|Pages in use exist at exit|"
                      r"resources still in use|Orphan StringName|StringName.*leaked|at: (~|_?cleanup|finalize))", re.I)
FAILURE = re.compile(r"^(SCRIPT ERROR|ERROR|USER ERROR|Parse Error)|Traceback \(most recent call last\)|Account service request failed")


def log_problems(folder, prefixes):
    """Lines in process logs that show a script error, engine error or Python traceback (teardown noise excluded).

    A process can print PASS and exit 0 while a handler threw; the exit status alone is not a test result."""
    problems, teardown = [], 0
    for path in sorted(folder.glob("*.log")):
        if not any(path.name.startswith(prefix) for prefix in prefixes):
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for number, line in enumerate(lines):
            if not FAILURE.search(line):
                continue
            context = " ".join(lines[number:number + 3])
            if TEARDOWN.search(context):
                teardown += 1
            else:
                problems.append(f"{path.name}:{number + 1}: {line.strip()[:200]}")
    return problems, teardown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--coordinator", type=Path,
                        help="An exported dedicated-server build to run as the coordinator (tools/export_server.py); clients still use --godot")
    parser.add_argument("--stages", default="all", help="comma list of: capacity,restart,custom,world,version,hostile,bandwidth (default all except bandwidth)")
    parser.add_argument("--allow-log-errors", action="store_true", help="report log problems without failing (diagnosis only)")
    args = parser.parse_args()
    wanted = {"capacity", "restart", "custom", "world", "version", "hostile"} if args.stages == "all" else set(args.stages.split(","))
    if os.name == "nt" and args.godot.stem.endswith("_console"):
        native = args.godot.with_name(args.godot.stem.removesuffix("_console") + ".exe")
        if native.is_file():
            args.godot = native
    root = Path(__file__).resolve().parent.parent
    source = json.loads((root / "server/data/server.json").read_text())
    output = root / "output/official-integration"
    output.mkdir(exist_ok=True)
    for old in output.glob("*.log"):
        old.unlink()
    context = ssl.create_default_context(cafile=source["certificate"])
    url = "https://127.0.0.1:18443"
    processes, handles = [], []
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def spawn(command, label):
        log = (output / (label + ".log")).open("w", encoding="utf-8")
        handles.append(log)
        process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        processes.append(process)
        return process

    def api(path, data=None, token=""):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(url + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
        with urllib.request.urlopen(request, context=context, timeout=5) as response:
            return json.loads(response.read())

    def wait(predicate, limit=60):
        deadline = time.monotonic()+limit
        while time.monotonic() < deadline:
            try:
                if predicate():
                    return
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(0.2)
        raise AssertionError("Timed out waiting for server/client state; inspect output/official-integration logs")

    def stop(process):
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=15)

    godot = str(args.godot.resolve())
    results = []

    def client(scene, extra, label):
        return spawn([godot, "--headless", "--max-fps", "30", "--path", str(root / "game"), scene, "--", *extra,
                      "--certificate=" + source["certificate"]], label)

    def passed(stage, text, prefixes):
        problems, teardown = log_problems(output, prefixes)
        note = f" ({teardown} engine shutdown messages ignored)" if teardown else ""
        if problems and not args.allow_log_errors:
            print(f"FAIL: {stage}: process logs contain errors{note}", flush=True)
            for line in problems[:20]:
                print("   ", line, flush=True)
            raise AssertionError(f"{stage}: {len(problems)} error line(s) in process logs")
        if problems:
            print(f"WARN: {stage}: {len(problems)} error line(s) in process logs (allowed)", flush=True)
            for line in problems[:5]:
                print("   ", line, flush=True)
        results.append(stage)
        print(f"PASS: {text}; process logs clean{note}", flush=True)

    def finish(procs, limit, why):
        for process in procs:
            assert process.wait(timeout=limit) == 0, why

    try:
        with tempfile.TemporaryDirectory(prefix="beyond-heroes-official-") as directory:
            config_path = Path(directory) / "server.json"
            config = {**source, "api_port": 18443, "game_port": 24690, "game_host": "127.0.0.1"}
            config_path.write_text(json.dumps(config), encoding="utf-8")
            service_command = [sys.executable, "-m", "server.service", "--config", str(config_path)]
            game_command = ([str(args.coordinator.resolve()), "--headless", "--max-fps", "30"] if args.coordinator else
                            [godot, "--headless", "--max-fps", "30", "--path", str(root / "game")]) + ["--", "--official-server=" + str(config_path)]
            service = spawn(service_command, "accounts")
            wait(lambda: api("/health"))
            game = spawn(game_command, "dedicated")
            wait(lambda: api("/health")["game_online"])

            if "capacity" in wanted:
                clients = [client("res://tests/tools/net_probe_official.tscn", ["--userid=probe_%02d" % i, "--expected=12", "--hold=8"], "client-%02d" % i) for i in range(12)]
                wait(lambda: all("OFFICIAL_PROBE READY" in (output / ("client-%02d.log" % i)).read_text(encoding="utf-8") for i in range(12)), 120)
                assert api("/health")["players"] == 12
                # A thirteenth account may exist, but it cannot enter a full game.
                auth = api("/auth/register", {"userid": "probe_extra", "password": "test-only-long-password-2026"})
                from server.test_service import save
                character = api("/characters/create", {"slot": 0, "save": save()}, auth["token"])["character"]["id"]
                try:
                    api("/characters/play", {"character": character}, auth["token"])
                    raise AssertionError("Thirteenth player was accepted")
                except urllib.error.HTTPError as error:
                    assert json.loads(error.read())["code"] == "server_full"
                finish(clients, 45, "Client probe failed")
                time.sleep(1.5)   # let the coordinator finish handling twelve departures before its log is read
                passed("capacity", "12 real HTTPS/ENet clients; thirteenth refused; committed saves confirmed", ("client-", "dedicated", "accounts"))

            if "restart" in wanted:
                if "capacity" in wanted:
                    stop(game)
                    stop(service)
                    service = spawn(service_command, "accounts-restarted")
                    wait(lambda: api("/health"))
                    game = spawn(game_command, "dedicated-restarted")
                    wait(lambda: api("/health")["game_online"])
                    # Two clients load real map/player scenes and recover their prior character data.
                    resumed = [client("res://tests/tools/net_probe_official.tscn", ["--userid=probe_%02d" % i, "--resume=1", "--full=1", "--trade=1", "--expected=2"], "resumed-%02d" % i) for i in range(2)]
                    finish(resumed, 90, "Real-map reconnect probe failed")
                    time.sleep(1.0)
                    passed("restart", "server restart; two real map clients resumed progress, traded atomically and saved on exit", ("resumed-", "dedicated-restarted", "accounts-restarted"))
                else:
                    print("SKIP: restart stage needs the capacity stage's accounts", flush=True)

            if "custom" in wanted:
                custom = []
                for role in ("host", "join"):
                    custom.append(spawn([godot, "--headless", "--max-fps", "30", "--path", str(root / "game"),
                        "res://tests/tools/net_probe_custom.tscn", "--", "--role=" + role], "custom-" + role))
                    if role == "host":
                        wait(lambda: any(room.get("name") == "Integration Custom Game" for room in api("/custom/list")["games"]))
                finish(custom, 60, "Custom room probe failed")
                passed("custom", "custom host and client; separate fresh characters; shared directory listing", ("custom-",))

            if "world" in wanted:
                # Two heroes on one map: the owner leaves and the remaining hero takes over its live monsters.
                pair = [client("res://tests/tools/net_probe_world.tscn", ["--scenario=handoff", "--map=ruined_forest", "--userid=handoff_%s" % n], "world-handoff-" + n) for n in "ab"]
                finish(pair, 150, "Map owner hand-off probe failed")
                logs = " ".join((output / ("world-handoff-%s.log" % n)).read_text(encoding="utf-8", errors="replace") for n in "ab")
                assert "WORLD_PROBE OWNER" in logs and "WORLD_PROBE HANDOFF" in logs, "hand-off did not run both halves"
                passed("world-handoff", "map owner left; the other hero took over its live monsters", ("world-handoff", "dedicated"))
                # Two heroes on different maps: each owns its own map, neither sees the other's monsters or avatar.
                apart = [client("res://tests/tools/net_probe_world.tscn", ["--scenario=separate", "--map=" + m, "--userid=apart_%s" % n], "world-apart-" + n) for n, m in (("a", "sanctuary"), ("b", "ruined_forest"))]
                finish(apart, 150, "Separate-map probe failed")
                passed("world-separate", "heroes on different maps each ran their own map", ("world-apart", "dedicated"))
                # A lost connection keeps the lease for a short grace window; release and reload restores confirmed progress.
                lone = [client("res://tests/tools/net_probe_world.tscn", ["--scenario=reconnect", "--userid=reconnect_a"], "world-reconnect")]
                finish(lone, 120, "Reconnect probe failed")
                passed("world-reconnect", "dropped connection, refused duplicate play, release, reload with progress, rejoin", ("world-reconnect", "dedicated"))

            if "bandwidth" in wanted:
                # heroes together on a real map with monsters: what the coordinator sends and receives, and what one client sends and receives
                rows = []
                for count in (2, 4, 6):
                    group = [client("res://tests/tools/net_probe_world.tscn", ["--scenario=bandwidth", "--map=ruined_forest", "--expected=%d" % count, "--hold=35", "--userid=bw%d_%d" % (count, i)], "bandwidth-%d-%d" % (count, i)) for i in range(count)]
                    finish(group, 240, "Bandwidth probe failed with %d clients" % count)
                    for i in range(count):
                        for line in (output / ("bandwidth-%d-%d.log" % (count, i))).read_text(encoding="utf-8", errors="replace").splitlines():
                            if line.startswith("BANDWIDTH"):
                                rows.append(line)
                (output / "bandwidth-summary.txt").write_text(chr(10).join(rows) + chr(10), encoding="utf-8")
                passed("bandwidth", "per-client traffic measured with 2, 4 and 6 heroes on one map (see bandwidth-summary.txt)", ("bandwidth-", "dedicated"))

            if "version" in wanted:
                old = [client("res://tests/tools/net_probe_world.tscn", ["--scenario=version", "--userid=version_a"], "version-a")]
                finish(old, 90, "Version-mismatch probe failed")
                passed("version", "a game with another protocol number was refused with both versions named", ("version-", "dedicated"))

            if "hostile" in wanted:
                bad = [client("res://tests/tools/net_probe_world.tscn", ["--scenario=hostile", "--userid=hostile_a"], "hostile-a")]
                finish(bad, 120, "Hostile-client probe failed")
                health = api("/health")
                assert health["game_online"], "coordinator went offline after hostile input"
                passed("hostile", "malformed, oversized, non-finite and flooding messages were absorbed", ("hostile", "dedicated"))

            stop(game)
            stop(service)
            print("STAGES PASSED:", ", ".join(results), flush=True)
    finally:
        for process in reversed(processes):
            stop(process)
        for handle in handles:
            handle.close()


if __name__ == "__main__":
    main()
