"""Desktop start/stop controls for this PC; never stops unrelated processes."""
import argparse
import ctypes
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "server" / "data"
GODOT = Path(r"A:\Installer\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64.exe")


def running():
    try:
        pid = int((DATA / "launcher.pid").read_text())
    except (OSError, ValueError):
        return False
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
    finally:
        kernel.CloseHandle(handle)


def health():
    config = json.loads((DATA / "server.json").read_text(encoding="utf-8"))
    context = ssl.create_default_context(cafile=config["certificate"])
    with urllib.request.urlopen("https://127.0.0.1:%d/health" % config.get("api_port", 8443), context=context, timeout=2) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "status"])
    parser.add_argument("--godot", type=Path, default=GODOT)
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("These desktop controls are for Windows.")
    if args.action == "status":
        print(json.dumps({"managed_process_running": running(), "service": health()}))
        return
    if args.action == "stop":
        if not running():
            print("Managed official server is not running.")
            return
        (DATA / "stop.request").write_text("Stop and back up\n", encoding="ascii")
        for _ in range(80):
            if not running():
                print("Official server stopped; confirmed progress is saved.")
                return
            time.sleep(0.25)
        raise SystemExit("The server is still stopping. Check server/data/logs before starting again.")
    if running():
        print("Official server is already running.")
        return
    if not args.godot.is_file() or not (DATA / "server.json").is_file():
        raise SystemExit("Server configuration or Godot is missing.")
    # Do not start over an account service launched another way.
    try:
        existing = health()
    except (OSError, ValueError):
        existing = None
    if existing is not None:
        raise SystemExit("An account service is already running. Stop its original launcher first.")
    logs = DATA / "logs"
    logs.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    with (logs / (stamp + "-launcher.log")).open("w", encoding="utf-8") as output:
        process = subprocess.Popen([sys.executable, "-m", "server.run_server", "--godot", str(args.godot), "--managed"],
            cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(60):
        if process.poll() is not None:
            raise SystemExit("The launcher stopped. Check server/data/logs.")
        try:
            if health().get("game_online"):
                print("Official Beyond Heroes server is online; maximum 12 players.")
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.25)
    raise SystemExit("The server is still starting. Check server/data/logs.")


if __name__ == "__main__":
    main()
