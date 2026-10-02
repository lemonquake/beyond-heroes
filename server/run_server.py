"""Run the HTTPS service and dedicated Godot coordinator together.

One parent keeps two children: the account service (Python) and the game coordinator (headless Godot). If either stops, the
other is stopped too and this process exits with an error so a supervisor (systemd) restarts the pair. A stop request
(SIGTERM/SIGINT, Ctrl+C, or the Windows desktop Stop control) stops the coordinator first, then lets the account service finish
its requests and save a backup. Every child is given a bounded time; a stuck one is killed so the parent always finishes.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

STOP_WAIT = 20       # seconds a child may take to stop after a polite request
KILL_WAIT = 5        # seconds to wait for a killed child


def prune_logs(logs: Path, keep: int) -> None:
    """Keep the newest `keep` log files; the folder cannot grow without bound across restarts."""
    files = sorted((p for p in logs.glob("*.log") if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
        except OSError:
            pass


def lock_exclusive(handle) -> bool:
    """Take a non-blocking exclusive lock on an open file; False when another process already holds it."""
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def stop_child(process: subprocess.Popen, name: str) -> int:
    """Ask a child to stop, wait a bounded time, then kill it. Never raises, always returns its exit code."""
    if process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=STOP_WAIT)
        except subprocess.TimeoutExpired:
            print(f"{name} did not stop within {STOP_WAIT} seconds; killing it.", flush=True)
            process.kill()
            try:
                process.wait(timeout=KILL_WAIT)
            except subprocess.TimeoutExpired:
                print(f"{name} could not be killed (pid {process.pid}).", flush=True)
        except OSError as error:
            print(f"Could not stop {name}: {error}", flush=True)
    return process.returncode if process.returncode is not None else -1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "data" / "server.json")
    parser.add_argument("--managed", action="store_true", help="Allow desktop controls to stop this server gracefully (Windows)")
    parser.add_argument("--stdio", action="store_true", help="Children write to this process's output (journald under systemd) instead of log files")
    parser.add_argument("--keep-logs", type=int, default=24, help="Log files to keep when writing log files")
    args = parser.parse_args()
    if os.name == "nt" and args.godot.stem.endswith("_console"):
        native = args.godot.with_name(args.godot.stem.removesuffix("_console") + ".exe")
        if native.is_file():
            args.godot = native
    root = Path(__file__).resolve().parent.parent
    config = args.config.resolve()
    if not args.godot.is_file() or not config.is_file():
        raise SystemExit("Godot executable or server configuration is missing. Run setup_server.py first.")
    # The coordinator needs only the loopback certificate, the internal key and the ports. When setup wrote a separate
    # coordinator.json it gets that instead of the full configuration (which also names the TLS private key).
    coordinator_config = config.with_name("coordinator.json")
    if not coordinator_config.is_file():
        coordinator_config = config
    logs = config.parent / "logs"
    lock_file = None
    stop_file = config.parent / "stop.request"
    pid_file = config.parent / "launcher.pid"
    if args.managed:
        lock_file = (config.parent / "launcher.lock").open("a+b")
        if lock_file.seek(0, 2) == 0:
            lock_file.write(b"0")
            lock_file.flush()
        lock_file.seek(0)
        if not lock_exclusive(lock_file):
            lock_file.close()
            print("The managed official server is already running.", flush=True)
            return 0
        stop_file.unlink(missing_ok=True)
        pid_file.write_text(str(os.getpid()), encoding="ascii")
    stopping = []

    def request_stop(signum, _frame):
        stopping.append(signum)

    for name in ("SIGTERM", "SIGINT", "SIGBREAK"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), request_stop)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    handles, children = [], []          # children: (name, process); stopped in reverse order
    exit_code = 0
    try:
        if args.stdio:
            accounts_out = game_out = None      # inherit: journald timestamps and rotates them
        else:
            logs.mkdir(exist_ok=True)
            prune_logs(logs, args.keep_logs - 2)
            accounts_out = (logs / (stamp + "-accounts.log")).open("w", encoding="utf-8")
            game_out = (logs / (stamp + "-game.log")).open("w", encoding="utf-8")
            handles += [accounts_out, game_out]
        children.append(("account service", subprocess.Popen([sys.executable, "-m", "server.service", "--config", str(config)], cwd=root,
                                                              stdout=accounts_out, stderr=subprocess.STDOUT if accounts_out else None, creationflags=flags)))
        children.append(("game coordinator", subprocess.Popen([str(args.godot.resolve()), "--headless", "--max-fps", "30", "--path", str(root / "game"),
                                                               "--", "--official-server=" + str(coordinator_config)], cwd=root,
                                                              stdout=game_out, stderr=subprocess.STDOUT if game_out else None, creationflags=flags)))
        print("Official Beyond Heroes server started. Send SIGTERM or press Ctrl+C to stop both services.", flush=True)
        print("Data:", config.parent, flush=True)
        while not stopping:
            if args.managed and stop_file.exists():
                print("Desktop Stop requested. Saving a final backup…", flush=True)
                stopping.append("stop-file")
                break
            dead = [name for name, process in children if process.poll() is not None]
            if dead:
                print("The %s stopped unexpectedly (exit %s). Stopping the other service so the supervisor can restart both." %
                      (dead[0], next(p.returncode for n, p in children if n == dead[0])), flush=True)
                exit_code = 1
                break
            time.sleep(0.5)
        else:
            print(f"Stop requested (signal {stopping[0]}); stopping the game coordinator, then the account service.", flush=True)
    except KeyboardInterrupt:
        print("Stopping server and backing up saved characters…", flush=True)
    finally:
        # a second signal while shutting down must not abandon cleanup
        for name in ("SIGTERM", "SIGINT", "SIGBREAK"):
            if hasattr(signal, name):
                signal.signal(getattr(signal, name), signal.SIG_IGN)
        for name, process in reversed(children):
            code = stop_child(process, name)
            print(f"The {name} stopped (exit {code}).", flush=True)
            if name == "account service" and code not in (0, None) and not stopping and exit_code == 0:
                exit_code = 1
        try:
            from server.service import Store
            settings = json.loads(config.read_text(encoding="utf-8"))
            backup = Store(config.parent, host=settings["game_host"]).backup()
            print("Saved database backup:", backup, flush=True)
        except Exception as error:        # never lose the exit path to a failed backup; the supervisor and logs show it
            print("Final database backup FAILED:", error, flush=True)
            exit_code = exit_code or 1
        for handle in handles:
            handle.close()
        if args.managed:
            pid_file.unlink(missing_ok=True)
            stop_file.unlink(missing_ok=True)
            lock_file.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
