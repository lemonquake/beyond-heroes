"""Run one Godot QA command with bounded lifetime, captured output and a receipt."""
import argparse
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--godot", default="A:/Installer/Godot_v4.7.2-stable_win64/Godot_v4.7.2-stable_win64.exe")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    folder = ROOT / "output/hero-port-20261026"
    folder.mkdir(parents=True, exist_ok=True)
    log = folder / (args.label + ".log")
    start = time.monotonic()
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen([args.godot, *command], stdout=output, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        timed_out = False
        try:
            process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            process.wait(timeout=15)
    receipt = {"command": [args.godot, *command], "exit": process.returncode, "timeout": timed_out,
               "elapsed_s": time.monotonic() - start, "log": str(log)}
    (folder / (args.label + "-receipt.json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))
    print("\n".join(log.read_text(errors="replace").splitlines()[-12:]))
    raise SystemExit(process.returncode or int(timed_out))
