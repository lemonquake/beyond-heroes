"""Exercise a real dedicated server with twelve Godot clients and a restart.

Runs in an isolated temporary database and leaves only logs in output/.
"""
import argparse
import contextlib
import json
import os
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, required=True)
    args = parser.parse_args()
    if os.name == "nt" and args.godot.stem.endswith("_console"):
        native = args.godot.with_name(args.godot.stem.removesuffix("_console") + ".exe")
        if native.is_file():
            args.godot = native
    root = Path(__file__).resolve().parent.parent
    source = json.loads((root / "server/data/server.json").read_text())
    output = root / "output/official-integration"
    output.mkdir(exist_ok=True)
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

    try:
        with tempfile.TemporaryDirectory(prefix="beyond-heroes-official-") as directory:
            config_path = Path(directory) / "server.json"
            config = {**source, "api_port": 18443, "game_port": 24690, "game_host": "127.0.0.1"}
            config_path.write_text(json.dumps(config), encoding="utf-8")
            service_command = [sys.executable, "-m", "server.service", "--config", str(config_path)]
            game_command = [str(args.godot.resolve()), "--headless", "--max-fps", "30", "--path", str(root / "game"), "--", "--official-server="+str(config_path)]
            service = spawn(service_command, "accounts")
            wait(lambda: api("/health"))
            game = spawn(game_command, "dedicated")
            wait(lambda: api("/health")["game_online"])
            clients = []
            for index in range(12):
                command = [str(args.godot.resolve()), "--headless", "--max-fps", "30", "--path", str(root / "game"), "res://tests/tools/net_probe_official.tscn", "--",
                           "--userid=probe_%02d" % index, "--expected=12", "--hold=8", "--certificate="+source["certificate"]]
                clients.append(spawn(command, "client-%02d" % index))
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
            for client in clients:
                assert client.wait(timeout=45) == 0, "Client probe failed"
            print("PASS: 12 real HTTPS/ENet clients; thirteenth refused; committed saves confirmed", flush=True)
            stop(game)
            stop(service)
            service = spawn(service_command, "accounts-restarted")
            wait(lambda: api("/health"))
            game = spawn(game_command, "dedicated-restarted")
            wait(lambda: api("/health")["game_online"])
            # Two clients load real map/player scenes and recover their prior character data.
            resumed = []
            for index in range(2):
                resumed.append(spawn([str(args.godot.resolve()), "--headless", "--max-fps", "30", "--path", str(root / "game"), "res://tests/tools/net_probe_official.tscn", "--",
                    "--userid=probe_%02d" % index, "--resume=1", "--full=1", "--trade=1", "--expected=2", "--certificate="+source["certificate"]], "resumed-%02d" % index))
            for client in resumed:
                assert client.wait(timeout=90) == 0, "Real-map reconnect probe failed"
            print("PASS: server restart; two real map clients resumed progress, traded atomically and saved on exit", flush=True)
            custom = []
            for role in ("host", "join"):
                custom.append(spawn([str(args.godot.resolve()), "--headless", "--max-fps", "30", "--path", str(root / "game"),
                    "res://tests/tools/net_probe_custom.tscn", "--", "--role="+role], "custom-"+role))
                if role == "host":
                    wait(lambda: any(room.get("name") == "Integration Custom Game" for room in api("/custom/list")["games"]))
            for client in custom:
                assert client.wait(timeout=60) == 0, "Custom room probe failed"
            print("PASS: custom host and client; separate fresh characters; shared directory listing", flush=True)
            stop(game)
            stop(service)
    finally:
        for process in reversed(processes):
            stop(process)
        for handle in handles:
            handle.close()


if __name__ == "__main__":
    main()
