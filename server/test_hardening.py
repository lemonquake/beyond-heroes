"""Hardening tests for the account service, its HTTP boundary, backups/restore and the supervising runner.

These complement test_service.py (database invariants). Everything here uses throwaway directories, a throwaway certificate and
loopback sockets; no real player data or real server key is read.
"""
import contextlib
import http.client
import json
import os
import socket
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from server import maintenance
from server.service import ApiError, HttpServer, Store, audit_progress, client_address, digest, prune_backups
from server.test_service import PASSWORD, save

ROOT = Path(__file__).resolve().parent.parent


def free_port():
    with contextlib.closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class AddressTests(unittest.TestCase):
    def test_forwarded_header_is_trusted_only_from_the_proxy(self):
        trusted = frozenset({"127.0.0.1"})
        self.assertEqual(("203.0.113.9", True), client_address("127.0.0.1", "203.0.113.9", trusted))
        self.assertEqual(("203.0.113.9", True), client_address("127.0.0.1", "1.2.3.4, 203.0.113.9", trusted),
                         "the right-most entry is the one the proxy appended; earlier entries are client-supplied")
        self.assertEqual(("198.51.100.4", False), client_address("198.51.100.4", "203.0.113.9", trusted),
                         "a client that is not the proxy cannot choose its address")
        self.assertEqual(("127.0.0.1", False), client_address("127.0.0.1", "not-an-address", trusted))
        self.assertEqual(("127.0.0.1", False), client_address("127.0.0.1", "203.0.113.9", frozenset()))
        self.assertEqual(("127.0.0.1", False), client_address("127.0.0.1", "", trusted))


class ProgressAuditTests(unittest.TestCase):
    def hero(self, level=5, xp=1000, gold=100):
        return {"progress": {"level": level, "total_xp": xp}, "gold": gold}

    def test_normal_play_is_not_flagged(self):
        self.assertEqual([], audit_progress(self.hero(), self.hero(6, 1800, 400), 120))

    def test_jumps_are_flagged(self):
        flags = audit_progress(self.hero(), self.hero(40, 10**9, 10**8), 5)
        self.assertTrue(any(flag.startswith("level+") for flag in flags))
        self.assertTrue(any(flag.startswith("gold+") for flag in flags))
        self.assertIn("xp_rate", flags)
        self.assertIn("xp_decreased", audit_progress(self.hero(xp=5000), self.hero(xp=10), 60))


class BackupTests(unittest.TestCase):
    def test_pruning_keeps_recent_and_one_per_day_and_bounds_disk(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            names = []
            for day in range(1, 41):
                for hour in (1, 7, 13, 19):
                    names.append("202610%02d-%02d0000-abcdef.sqlite3" % (day, hour) if day <= 31 else "202611%02d-%02d0000-abcdef.sqlite3" % (day - 31, hour))
            for name in names:
                (folder / name).write_bytes(b"x")
            (folder / "notes.txt").write_text("keep me")
            kept = prune_backups(folder, keep=16, keep_days=30)
            left = sorted(p.name for p in folder.glob("*.sqlite3"))
            self.assertEqual(kept, len(left))
            self.assertLessEqual(len(left), 16 + 30)
            self.assertIn(max(names), left, "the newest backup always survives")
            self.assertTrue((folder / "notes.txt").exists(), "files that are not backups are never deleted")
            days = {name[:8] for name in left}
            self.assertGreaterEqual(len(days), 20, "older days are still represented by one backup each")


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        with patch("server.service.password_hash", lambda password, salt: bytes.fromhex(digest(password + salt.hex()))):
            self.store = Store(self.dir / "live")
            token = self.store.handle("POST", "/auth/register", {"userid": "restore_me", "password": PASSWORD})["token"]
            self.store.handle("POST", "/characters/create", {"slot": 0, "save": save()}, token=token)

    def tearDown(self):
        self.temp.cleanup()

    def test_backup_verifies_and_restores_into_staging(self):
        backup = self.store.backup()
        counts = maintenance.verify(backup)
        self.assertEqual(1, counts["accounts"])
        self.assertEqual(1, counts["characters"])
        restored = maintenance.restore_into(backup, self.dir / "staging")
        self.assertEqual(counts, maintenance.verify(restored))
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.restore_into(backup, self.dir / "staging")          # never overwrites a restored database

    def test_damaged_and_foreign_files_are_refused(self):
        garbage = self.dir / "garbage.sqlite3"
        garbage.write_bytes(b"not a database" * 100)
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.verify(garbage)
        other = self.dir / "other.sqlite3"
        with contextlib.closing(sqlite3.connect(other)) as db:
            db.execute("CREATE TABLE unrelated(x)")
            db.commit()
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.verify(other)
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.verify(self.dir / "missing.sqlite3")

    def test_corrupted_character_json_is_caught(self):
        backup = self.store.backup()
        with contextlib.closing(sqlite3.connect(backup)) as db:
            db.execute("UPDATE characters SET data='{broken'")
            db.commit()
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.verify(backup)

    def test_replace_keeps_the_old_database_aside_and_refuses_while_in_use(self):
        backup = self.store.backup()
        live = self.dir / "live"
        with contextlib.closing(sqlite3.connect(live / maintenance.DB_NAME)) as busy:
            busy.execute("BEGIN EXCLUSIVE")
            with self.assertRaises(maintenance.MaintenanceError):
                maintenance.replace_live(backup, live)
            busy.rollback()
        maintenance.replace_live(backup, live)
        self.assertEqual(1, len(list(live.glob("before-restore-*"))))
        self.assertEqual(1, maintenance.verify(live / maintenance.DB_NAME)["characters"])


class HttpBoundaryTests(unittest.TestCase):
    """The real HTTP handler over TLS on loopback, behind a pretend trusted proxy."""

    @classmethod
    def setUpClass(cls):
        from server.setup_server import make_identity
        cls.temp = tempfile.TemporaryDirectory()
        directory = Path(cls.temp.name)
        key, certificate = make_identity(directory, "localhost", {"localhost", "127.0.0.1"}, days=2)
        cls.kdf = patch("server.service.password_hash", lambda password, salt: bytes.fromhex(digest(password + salt.hex())))
        cls.kdf.start()
        cls.store = Store(directory / "data")
        cls.secret = "internal-test-key"
        cls.server = HttpServer(("127.0.0.1", 0), cls.store, cls.secret, trusted_proxies=["127.0.0.1"])
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certificate, key)
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True, do_handshake_on_connect=False)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
        cls.thread.start()
        cls.context = ssl.create_default_context(cafile=str(certificate))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.kdf.stop()
        cls.temp.cleanup()

    def call(self, method, path, body=None, headers=None, raw=None):
        connection = http.client.HTTPSConnection("127.0.0.1", self.port, context=self.context, timeout=10)
        try:
            data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
            sent = {"Content-Type": "application/json", **(headers or {})}
            connection.request(method, path, body=data, headers=sent)
            response = connection.getresponse()
            payload = response.read()
            return response.status, (json.loads(payload) if payload else {}), dict(response.getheaders())
        finally:
            connection.close()

    def test_health_reports_protocol_and_version(self):
        status, body, headers = self.call("GET", "/health")
        self.assertEqual(200, status)
        self.assertEqual(20, body["protocol"])
        self.assertIn("version", body)
        self.assertEqual("no-store", headers["Cache-Control"])

    def test_oversized_malformed_and_wrong_type_requests_are_refused(self):
        status, _, _ = self.call("POST", "/auth/login", headers={"Content-Length": str(3 * 1024 * 1024)}, raw=b"{}")
        self.assertEqual(413, status, "a body larger than the limit is refused before it is read")
        status, body, _ = self.call("POST", "/auth/login", raw=b"{not json")
        self.assertEqual(400, status)
        status, body, _ = self.call("POST", "/auth/login", raw=b'{"userid": NaN}')
        self.assertEqual(400, status, "non-finite JSON numbers are refused")
        status, _, _ = self.call("POST", "/auth/login", raw=b"[]")
        self.assertEqual(400, status, "a JSON array is not a request object")
        status, _, _ = self.call("POST", "/auth/login", raw=b"{}", headers={"Content-Type": "text/plain"})
        self.assertEqual(415, status)
        status, _, _ = self.call("DELETE", "/health")
        self.assertIn(status, (404, 501))

    def test_internal_routes_are_unreachable_through_the_proxy(self):
        # the TCP peer is loopback (like a local proxy) and the key is right; a forwarded client address means it came through the proxy
        status, body, _ = self.call("POST", "/internal/start", {}, headers={"X-Server-Key": self.secret, "X-Forwarded-For": "203.0.113.9"})
        self.assertEqual(403, status)
        # a direct loopback call with the key (the game coordinator) still works; without the key it does not
        status, _, _ = self.call("POST", "/internal/heartbeat", {}, headers={"X-Server-Key": self.secret})
        self.assertEqual(200, status)
        status, _, _ = self.call("POST", "/internal/heartbeat", {}, headers={"X-Server-Key": "guess"})
        self.assertEqual(403, status)

    def test_rate_limits_follow_the_forwarded_client_not_the_proxy(self):
        for index in range(30):
            status, *_ = self.call("POST", "/auth/login", {"userid": "nobody_%d" % index, "password": PASSWORD}, headers={"X-Forwarded-For": "203.0.113.50"})
            self.assertEqual(401, status)
        status, body, headers = self.call("POST", "/auth/login", {"userid": "nobody_x", "password": PASSWORD}, headers={"X-Forwarded-For": "203.0.113.50"})
        self.assertEqual(429, status)
        self.assertEqual("60", headers.get("Retry-After"))
        status, *_ = self.call("POST", "/auth/login", {"userid": "nobody_y", "password": PASSWORD}, headers={"X-Forwarded-For": "203.0.113.51"})
        self.assertEqual(401, status, "another client behind the same proxy is unaffected")

    def test_a_client_cannot_use_the_forwarded_header_to_dodge_limits_without_a_proxy(self):
        server = HttpServer(("127.0.0.1", 0), self.store, self.secret, trusted_proxies=[])
        try:
            self.assertEqual(frozenset(), server.trusted_proxies)
        finally:
            server.server_close()

    def test_unknown_routes_and_methods_do_not_leak_details(self):
        status, body, _ = self.call("POST", "/nope", {})
        self.assertIn(status, (401, 404))
        self.assertNotIn("Traceback", json.dumps(body))
        status, body, _ = self.call("GET", "/internal/start")
        self.assertEqual(404, status)


class RunnerTests(unittest.TestCase):
    """server.run_server with a stand-in for the Godot coordinator: child failure and clean stop."""

    def setUp(self):
        from server.setup_server import make_identity
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.dir = Path(self.temp.name)
        data = self.dir / "data"
        data.mkdir()
        key, certificate = make_identity(data, "localhost", {"localhost", "127.0.0.1"}, days=2)
        self.port = free_port()
        config = {"bind": "127.0.0.1", "api_port": self.port, "game_host": "127.0.0.1", "game_port": 24999, "certificate": str(certificate),
                  "private_key": str(key), "server_key": "runner-test-key"}
        (data / "server.json").write_text(json.dumps(config), encoding="utf-8")
        self.config = data / "server.json"
        self.data = data

    def tearDown(self):
        # on Windows the stand-in runs behind cmd.exe, which terminate() does not take with it: tell any stray one to leave
        (self.dir / "stub.stop").write_text("stop")
        time.sleep(1.5)
        self.temp.cleanup()

    def forever(self):
        return "import os, time\nwhile not os.path.exists(r'%s'): time.sleep(0.3)\n" % (self.dir / "stub.stop")

    def stub(self, body):
        script = self.dir / "stub_godot.py"
        script.write_text(body, encoding="utf-8")
        if os.name == "nt":
            launcher = self.dir / "stub_godot.cmd"
            launcher.write_text('@"%s" "%s" %%*\r\n' % (sys.executable, script), encoding="ascii")
        else:
            launcher = self.dir / "stub_godot.sh"
            launcher.write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, script), encoding="ascii")
            launcher.chmod(0o755)
        return launcher

    def run_runner(self, godot, extra=()):
        return subprocess.Popen([sys.executable, "-m", "server.run_server", "--godot", str(godot), "--config", str(self.config), *extra],
                                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def wait_health(self, limit=40):
        context = ssl.create_default_context(cafile=str(self.data / "server.crt"))
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            try:
                with contextlib.closing(http.client.HTTPSConnection("127.0.0.1", self.port, context=context, timeout=2)) as connection:
                    connection.request("GET", "/health")
                    return json.loads(connection.getresponse().read())
            except (OSError, ValueError):
                time.sleep(0.3)
        self.fail("the account service did not come up")

    def test_a_dead_coordinator_stops_everything_with_an_error_and_a_backup(self):
        godot = self.stub("import sys; sys.exit(3)\n")
        process = self.run_runner(godot)
        output, _ = process.communicate(timeout=60)
        self.assertEqual(1, process.returncode, output)
        self.assertIn("stopped unexpectedly", output)
        self.assertTrue(list((self.data / "backups").glob("*.sqlite3")), "a final backup was written\n" + output)
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", self.port), timeout=1).close()   # the account service is gone too

    @unittest.skipIf(os.name == "nt", "a polite SIGTERM cannot be sent to a Windows process; the stop-file path covers Windows")
    def test_sigterm_stops_both_children_and_saves_a_backup(self):
        godot = self.stub("import time\nwhile True: time.sleep(1)\n")
        process = self.run_runner(godot)
        self.wait_health()
        process.send_signal(15)
        output, _ = process.communicate(timeout=60)
        self.assertEqual(0, process.returncode, output)
        self.assertIn("Saved database backup", output)

    def test_desktop_stop_request_shuts_down_cleanly(self):
        godot = self.stub("import time\nwhile True: time.sleep(1)\n")
        process = self.run_runner(godot, ["--managed"])
        self.wait_health()
        (self.data / "stop.request").write_text("stop", encoding="ascii")
        output, _ = process.communicate(timeout=60)
        self.assertEqual(0, process.returncode, output)
        self.assertIn("Saved database backup", output)
        self.assertFalse((self.data / "launcher.pid").exists())

    def test_log_files_are_bounded(self):
        from server.run_server import prune_logs
        logs = self.dir / "logs"
        logs.mkdir()
        for index in range(60):
            path = logs / ("%03d.log" % index)
            path.write_text("x")
            os.utime(path, (1000 + index, 1000 + index))
        prune_logs(logs, 10)
        self.assertEqual(10, len(list(logs.glob("*.log"))))
        self.assertTrue((logs / "059.log").exists())


if __name__ == "__main__":
    unittest.main()
