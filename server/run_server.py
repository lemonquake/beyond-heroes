"""Run the HTTPS service and dedicated Godot coordinator together."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "data" / "server.json")
    parser.add_argument("--managed", action="store_true", help="Allow desktop controls to stop this server gracefully")
    args = parser.parse_args()
    if os.name == "nt" and args.godot.stem.endswith("_console"):
        native = args.godot.with_name(args.godot.stem.removesuffix("_console") + ".exe")
        if native.is_file():
            args.godot = native
    root = Path(__file__).resolve().parent.parent
    config = args.config.resolve()
    if not args.godot.is_file() or not config.is_file():
        raise SystemExit("Godot executable or server configuration is missing. Run setup_server.py first.")
    logs = config.parent / "logs"
    logs.mkdir(exist_ok=True)
    lock_file = None
    stop_file = config.parent / "stop.request"
    pid_file = config.parent / "launcher.pid"
    if args.managed:
        import msvcrt
        lock_file = (config.parent / "launcher.lock").open("a+b")
        if lock_file.seek(0, 2) == 0:
            lock_file.write(b"0")
            lock_file.flush()
        lock_file.seek(0)
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            lock_file.close()
            print("The managed official server is already running.", flush=True)
            return
        stop_file.unlink(missing_ok=True)
        pid_file.write_text(str(os.getpid()), encoding="ascii")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    processes = []
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        with (logs / (stamp + "-accounts.log")).open("w", encoding="utf-8") as accounts_log, (logs / (stamp + "-game.log")).open("w", encoding="utf-8") as game_log:
            processes.append(subprocess.Popen([sys.executable, "-m", "server.service", "--config", str(config)], cwd=root, stdout=accounts_log, stderr=subprocess.STDOUT, creationflags=flags))
            processes.append(subprocess.Popen([str(args.godot.resolve()), "--headless", "--max-fps", "30", "--path", str(root / "game"), "--", "--official-server=" + str(config)], cwd=root, stdout=game_log, stderr=subprocess.STDOUT, creationflags=flags))
            print("Official Beyond Heroes server started. Keep this process running; Ctrl+C stops both services.", flush=True)
            print("Data and logs:", config.parent, flush=True)
            while all(p.poll() is None for p in processes):
                if args.managed and stop_file.exists():
                    print("Desktop Stop requested. Saving a final backup…", flush=True)
                    break
                time.sleep(0.5)
            else:
                print("A server process stopped. See the logs above.", flush=True)
    except KeyboardInterrupt:
        print("Stopping server and backing up saved characters…", flush=True)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
        from server.service import Store
        settings = json.loads(config.read_text(encoding="utf-8"))
        backup = Store(config.parent, host=settings["game_host"]).backup()
        print("Saved database backup:", backup, flush=True)
        if args.managed:
            pid_file.unlink(missing_ok=True)
            stop_file.unlink(missing_ok=True)
            lock_file.close()


if __name__ == "__main__":
    main()
