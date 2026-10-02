"""Backup, verify and restore the account database. Works on Windows and Linux; never prints credentials.

    python -m server.maintenance backup  --config server.json            # one verified backup into <data>/backups
    python -m server.maintenance verify  FILE                             # integrity, schema and character data checks
    python -m server.maintenance restore FILE --into DIR                  # restore into a staging directory (safe to repeat)
    python -m server.maintenance restore FILE --replace --config server.json --yes
                                                                          # replace the live database (service must be stopped)

`restore --into` is what a restore drill uses: it never touches the live data. `--replace` first moves the current database
aside (kept in <data>/before-restore-<time>/), refuses to run while the service holds the database, and verifies the result.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path

DB_NAME = "beyond_heroes.sqlite3"
TABLES = ("accounts", "sessions", "characters", "imports", "leases", "tickets", "audit", "trades", "trade_approvals")


class MaintenanceError(Exception):
    pass


def verify(path: Path) -> dict:
    """Open a database read-only and prove it is a complete, readable Beyond Heroes database. Returns counts."""
    path = Path(path)
    if not path.is_file():
        raise MaintenanceError(f"{path} does not exist.")
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        db = sqlite3.connect(uri, uri=True, timeout=15)
    except sqlite3.Error as error:
        raise MaintenanceError(f"Could not open {path.name}: {error}")
    with contextlib.closing(db):
        try:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise MaintenanceError("SQLite integrity check failed.")
            if db.execute("PRAGMA foreign_key_check").fetchall():
                raise MaintenanceError("Foreign key check failed (a character or lease points at a missing account).")
            version = db.execute("SELECT version FROM schema_version").fetchone()
            if version is None or version[0] != 1:
                raise MaintenanceError("Unsupported database schema version; use a compatible server release.")
            counts = {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in TABLES}
            for cid, data in db.execute("SELECT id, data FROM characters"):
                hero = json.loads(data)["hero"]
                if not isinstance(hero.get("name"), str) or hero.get("class") not in ("knight", "mage", "ranger", "shadowblade"):
                    raise MaintenanceError(f"Character {cid[:8]} has unreadable data.")
        except sqlite3.Error as error:
            raise MaintenanceError(f"Database is damaged or incomplete: {error}")
        except (ValueError, KeyError, TypeError) as error:
            raise MaintenanceError(f"A character record is not valid JSON save data: {error}")
    return counts


def restore_into(source: Path, directory: Path) -> Path:
    """Copy a verified backup into `directory` as a fresh database (SQLite online-backup API, so WAL is consistent)."""
    verify(source)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / DB_NAME
    if target.exists():
        raise MaintenanceError(f"{target} already exists; choose an empty staging directory.")
    with contextlib.closing(sqlite3.connect(Path(source).resolve().as_uri() + "?mode=ro", uri=True)) as src, \
            contextlib.closing(sqlite3.connect(target)) as dst:
        src.backup(dst)
    verify(target)
    return target


def replace_live(source: Path, data_dir: Path) -> Path:
    """Put a verified backup in place of the live database. The service and coordinator must be stopped first."""
    verify(source)
    data_dir = Path(data_dir)
    live = data_dir / DB_NAME
    if live.exists():
        # an exclusive lock proves nothing else (the service, a backup) has the database open
        try:
            with contextlib.closing(sqlite3.connect(live, timeout=2)) as db:
                db.execute("BEGIN EXCLUSIVE")
                db.rollback()
        except sqlite3.OperationalError:
            raise MaintenanceError("The database is in use. Stop the service (systemctl stop beyond-heroes) and try again.")
        aside = data_dir / ("before-restore-" + time.strftime("%Y%m%d-%H%M%S"))
        aside.mkdir()
        for suffix in ("", "-wal", "-shm"):
            candidate = Path(str(live) + suffix)
            if candidate.exists():
                shutil.move(str(candidate), aside / candidate.name)
        print(f"The previous database was moved to {aside}")
    return restore_into(source, data_dir)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("--config", type=Path, default=Path(__file__).parent / "data" / "server.json")
    check = sub.add_parser("verify")
    check.add_argument("file", type=Path)
    restore = sub.add_parser("restore")
    restore.add_argument("file", type=Path)
    restore.add_argument("--into", type=Path, help="staging directory (does not touch live data)")
    restore.add_argument("--replace", action="store_true", help="replace the live database named by --config")
    restore.add_argument("--config", type=Path, default=Path(__file__).parent / "data" / "server.json")
    restore.add_argument("--yes", action="store_true", help="confirm --replace")
    args = parser.parse_args(argv)
    try:
        if args.action == "backup":
            from server.service import Store
            config = json.loads(args.config.read_text(encoding="utf-8"))
            target = Store(args.config.parent, host=config["game_host"]).backup()
            print("Verified backup:", target)
            print("Contents:", json.dumps(verify(target)))
        elif args.action == "verify":
            print("Backup is readable:", json.dumps(verify(args.file)))
        else:
            if bool(args.into) == args.replace:
                parser.error("choose exactly one of --into DIR or --replace")
            if args.replace:
                if not args.yes:
                    parser.error("--replace needs --yes (it replaces the live database)")
                target = replace_live(args.file, args.config.parent)
            else:
                target = restore_into(args.file, args.into)
            print("Restored and verified:", target)
            print("Contents:", json.dumps(verify(target)))
    except MaintenanceError as error:
        print("ERROR:", error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
