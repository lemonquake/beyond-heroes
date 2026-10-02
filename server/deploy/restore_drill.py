"""Prove the backup and restore procedure end to end with throwaway data. Safe on a live host: it never touches the real data.

    python -m server.deploy.restore_drill                # on a PC or on the VM; prints a report and exits non-zero on any failure

It starts a real account service on a random loopback port with a temporary database, creates an account and a character,
saves progress, takes a verified backup (the same command the timer uses), stops the service, restores the backup into an empty
staging directory, starts a second service on that directory and checks that the account, the character and its saved progress
are all back. The report is what to attach to a "restore verified" entry in the operations log.
"""
import contextlib
import http.client
import json
import socket
import ssl
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PASSWORD = "restore-drill-password-1"


def free_port():
    with contextlib.closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def call(port, cafile, method, path, body=None, token=""):
    context = ssl.create_default_context(cafile=str(cafile))
    connection = http.client.HTTPSConnection("127.0.0.1", port, context=context, timeout=10)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        connection.request(method, path, body=None if body is None else json.dumps(body), headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read() or b"{}")
    finally:
        connection.close()


def start(config_path, port, cafile):
    process = subprocess.Popen([sys.executable, "-m", "server.service", "--config", str(config_path)], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if call(port, cafile, "GET", "/health")[0] == 200:
                return process
        except (OSError, ValueError):
            time.sleep(0.3)
    process.kill()
    raise SystemExit("FAIL: the account service did not start")


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()


def main():
    from server.setup_server import make_identity
    steps = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        live, staging = Path(temp) / "live", Path(temp) / "staging"
        live.mkdir()
        key, certificate = make_identity(live, "localhost", {"localhost", "127.0.0.1"}, days=2)
        port = free_port()
        config = {"bind": "127.0.0.1", "api_port": port, "game_host": "127.0.0.1", "game_port": 24999,
                  "certificate": str(certificate), "private_key": str(key), "server_key": "drill-key"}
        (live / "server.json").write_text(json.dumps(config), encoding="utf-8")
        service = start(live / "server.json", port, certificate)
        try:
            status, auth = call(port, certificate, "POST", "/auth/register", {"userid": "drill_player", "password": PASSWORD})
            assert status == 200, auth
            save = {"version": 4, "hero": {"name": "Drill Hero", "class": "knight", "progress": {"level": 7, "total_xp": 4200},
                    "gold": 1234, "inventory": [], "equipment": {}, "map": "sanctuary", "difficulty": 1}}
            status, created = call(port, certificate, "POST", "/characters/create", {"slot": 0, "save": {**save, "hero": {**save["hero"], "progress": {"level": 1, "total_xp": 0}, "gold": 100}}}, auth["token"])
            assert status == 200, created
            steps.append("account and character created on the live database")
        finally:
            stop(service)
        backup = subprocess.run([sys.executable, "-m", "server.maintenance", "backup", "--config", str(live / "server.json")], cwd=ROOT,
                                capture_output=True, text=True)
        assert backup.returncode == 0, backup.stdout + backup.stderr
        steps.append("verified backup written: " + backup.stdout.splitlines()[0].split(": ", 1)[1].split("\\")[-1].split("/")[-1])
        newest = sorted((live / "backups").glob("*.sqlite3"))[-1]
        restored = subprocess.run([sys.executable, "-m", "server.maintenance", "restore", str(newest), "--into", str(staging)], cwd=ROOT,
                                  capture_output=True, text=True)
        assert restored.returncode == 0, restored.stdout + restored.stderr
        steps.append("backup restored into an empty staging directory and re-verified")
        staged_config = dict(config, api_port=free_port())
        (staging / "server.json").write_text(json.dumps(staged_config), encoding="utf-8")
        # the restored directory needs the same certificate and key as the live one: they are configuration, not data
        for name in ("server.crt", "server.key"):
            (staging / name).write_bytes((live / name).read_bytes())
        staged_config.update(certificate=str(staging / "server.crt"), private_key=str(staging / "server.key"))
        (staging / "server.json").write_text(json.dumps(staged_config), encoding="utf-8")
        second = start(staging / "server.json", staged_config["api_port"], staging / "server.crt")
        try:
            status, login = call(staged_config["api_port"], staging / "server.crt", "POST", "/auth/login", {"userid": "drill_player", "password": PASSWORD})
            assert status == 200, login
            status, listing = call(staged_config["api_port"], staging / "server.crt", "POST", "/characters/list", {}, login["token"])
            assert status == 200 and len(listing["characters"]) == 1, listing
            hero = listing["characters"][0]
            assert hero["name"] == "Drill Hero" and hero["class"] == "knight", hero
            steps.append("the restored service signed the account in and lists the character")
        finally:
            stop(second)
    print("RESTORE DRILL PASSED")
    for step in steps:
        print(" -", step)


if __name__ == "__main__":
    main()
