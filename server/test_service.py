import copy
import contextlib
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from server.service import ApiError, Store, digest, password_hash

PASSWORD = "a long test password!"


def save(level=1):
    return {"version": 4, "settings": {"device_only": True}, "hero": {
        "name": "Aldric", "class": "knight", "progress": {"level": level, "total_xp": 0},
        "gold": 100, "inventory": [], "equipment": {}, "map": "sanctuary", "difficulty": 1}}


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Most tests exercise database/API invariants, not KDF speed. One separate
        # test uses the production scrypt parameters.
        cls.kdf_patch = patch("server.service.password_hash", lambda password, salt: bytes.fromhex(digest(password + salt.hex())))
        cls.kdf_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.kdf_patch.stop()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.now = 100000.0
        self.store = Store(Path(self.temp.name), clock=lambda: self.now)
        self.store.handle("POST", "/internal/start", internal=True)
        self.auth = self.register("player_one")
        self.token = self.auth["token"]

    def tearDown(self):
        self.temp.cleanup()

    def register(self, userid, ip="127.0.0.1"):
        return self.store.handle("POST", "/auth/register", {"userid": userid, "password": PASSWORD}, ip=ip)

    def post(self, path, body=None, token=None):
        return self.store.handle("POST", path, body, token=self.token if token is None else token)

    def create(self, token=None, slot=0, data=None):
        return self.post("/characters/create", {"slot": slot, "save": data or save()}, token)["character"]["id"]

    def play(self, cid, token=None):
        result = self.post("/characters/play", {"character": cid}, token)
        self.store.handle("POST", "/internal/redeem", {"ticket": result["ticket"], "peer": 123}, internal=True)
        return result

    def payload(self, cid, play, request_id="save-request-one", revision=0):
        return {"character": cid, "lease": play["lease"], "request_id": request_id, "revision": revision, "save": save(2)}

    def error(self, status, callback):
        with self.assertRaises(ApiError) as caught:
            callback()
        self.assertEqual(status, caught.exception.status)
        return caught.exception

    def test_credentials_are_hashed_and_sessions_are_not_stored_plaintext(self):
        with contextlib.closing(self.store.connect()) as db:
            account = db.execute("SELECT * FROM accounts").fetchone()
            session = db.execute("SELECT token FROM sessions").fetchone()[0]
        self.assertNotEqual(PASSWORD.encode(), account["password"])
        self.assertNotEqual(self.auth["recovery_code"], account["recovery"])
        self.assertNotEqual(self.token, session)
        self.error(409, lambda: self.register("PLAYER_ONE"))

    def test_password_rules_and_login(self):
        self.error(400, lambda: self.store.handle("POST", "/auth/register", {"userid": "short", "password": "bad"}))
        self.error(401, lambda: self.store.handle("POST", "/auth/login", {"userid": "player_one", "password": "wrong long password"}))
        result = self.store.handle("POST", "/auth/login", {"userid": "PLAYER_ONE", "password": PASSWORD})
        self.assertEqual("player_one", result["userid"])

    def test_recovery_revokes_sessions_and_is_single_use(self):
        cid = self.create()
        self.play(cid)
        body = {"userid": "player_one", "password": "new long password!", "recovery_code": self.auth["recovery_code"]}
        result = self.store.handle("POST", "/auth/recover", body)
        self.error(401, lambda: self.post("/characters/list"))
        self.error(401, lambda: self.store.handle("POST", "/auth/recover", body))
        self.assertNotEqual(self.auth["recovery_code"], result["recovery_code"])
        self.assertEqual(1, len(self.post("/characters/list", token=result["token"])["characters"]))

    def test_ownership_and_device_settings(self):
        cid = self.create()
        other = self.register("player_two")["token"]
        self.error(404, lambda: self.post("/characters/play", {"character": cid}, other))
        result = self.play(cid)
        self.assertNotIn("settings", result["save"])

    def test_import_is_idempotent_and_never_replaces_progress(self):
        body = {"slot": 0, "source": "original-slot-identity", "save": save(50)}
        result = self.post("/characters/import", body)
        cid = result["character"]["id"]
        play = self.play(cid)
        update = self.payload(cid, play)
        update["save"] = save(51)
        self.post("/characters/save", update)
        again = self.post("/characters/import", body)
        self.assertTrue(again["already_imported"])
        self.assertEqual(51, again["character"]["level"])
        changed = copy.deepcopy(body)
        changed["save"] = save(60)
        self.assertEqual(cid, self.post("/characters/import", changed)["character"]["id"])

    def test_slot_collision_and_new_character_rules(self):
        self.create()
        self.error(409, lambda: self.create())
        self.error(400, lambda: self.create(slot=1, data=save(20)))
        self.error(400, lambda: self.create(slot=-1))
        self.error(400, lambda: self.create(slot=8))

    def test_exclusive_account_lease_and_release(self):
        cid = self.create()
        second = self.create(slot=1)
        play = self.play(cid)
        self.error(409, lambda: self.post("/characters/play", {"character": second}))
        self.post("/characters/release", {"character": cid, "lease": play["lease"]})
        self.play(second)

    def test_ticket_requires_private_server_access_and_is_single_use(self):
        cid = self.create()
        result = self.post("/characters/play", {"character": cid})
        body = {"ticket": result["ticket"], "peer": 200}
        self.error(403, lambda: self.store.handle("POST", "/internal/redeem", body))
        self.error(403, lambda: self.store.handle("POST", "/internal/redeem", body, internal=True, ip="192.168.1.2"))
        reply = self.store.handle("POST", "/internal/redeem", body, internal=True)
        self.assertEqual("player_one", reply["userid"])
        self.error(401, lambda: self.store.handle("POST", "/internal/redeem", body, internal=True))

    def test_ticket_and_lease_expiry(self):
        cid = self.create()
        result = self.post("/characters/play", {"character": cid})
        self.now += 46
        self.error(401, lambda: self.store.handle("POST", "/internal/redeem", {"ticket": result["ticket"], "peer": 200}, internal=True))
        self.now += 46
        self.store.handle("POST", "/internal/heartbeat", internal=True)
        self.post("/characters/play", {"character": cid})

    def test_server_full_at_twelve_and_no_phantom_host(self):
        for index in range(12):
            auth = self.register("friend_%02d" % index, ip="127.0.0.%d" % (index+2))
            cid = self.create(auth["token"])
            self.play(cid, auth["token"])
        health = self.store.handle("GET", "/health")
        self.assertEqual(12, health["players"])
        self.error(409, lambda: self.play(self.create()))

    def test_save_retry_is_idempotent_and_revision_protected(self):
        cid = self.create()
        play = self.play(cid)
        body = self.payload(cid, play)
        first = self.post("/characters/save", body)
        retry = self.post("/characters/save", body)
        self.assertEqual(first["revision"], retry["revision"])
        self.assertTrue(retry["duplicate"])
        changed = copy.deepcopy(body)
        changed["save"]["hero"]["gold"] = 999
        self.error(409, lambda: self.post("/characters/save", changed))
        changed["request_id"] = "different-save-id"
        self.error(409, lambda: self.post("/characters/save", changed))

    def test_two_concurrent_saves_cannot_overwrite(self):
        cid = self.create()
        play = self.play(cid)
        barrier = threading.Barrier(2)
        results = []

        def update(request_id):
            barrier.wait()
            try:
                results.append(self.post("/characters/save", self.payload(cid, play, request_id)))
            except ApiError as error:
                results.append(error.status)

        workers = [threading.Thread(target=update, args=("request-"+str(i),)) for i in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        self.assertEqual(1, results.count(409))
        self.assertEqual(1, sum(isinstance(result, dict) for result in results))

    def test_restart_preserves_data_and_invalidates_play_sessions(self):
        cid = self.create()
        play = self.play(cid)
        self.post("/characters/save", self.payload(cid, play))
        restarted = Store(Path(self.temp.name), clock=lambda: self.now)
        restarted.handle("POST", "/internal/start", internal=True)
        result = restarted.handle("POST", "/characters/list", token=self.token)
        self.assertEqual(2, result["characters"][0]["level"])
        self.error(409, lambda: restarted.handle("POST", "/characters/save", self.payload(cid, play), token=self.token))

    def test_validated_backup_contains_committed_progress(self):
        cid = self.create()
        self.post("/characters/save", self.payload(cid, self.play(cid)))
        backup = self.store.backup()
        with contextlib.closing(sqlite3.connect(backup)) as db:
            self.assertEqual("ok", db.execute("PRAGMA integrity_check").fetchone()[0])
            self.assertEqual(2, json.loads(db.execute("SELECT data FROM characters").fetchone()[0])["hero"]["progress"]["level"])

    def test_malformed_saves_and_class_changes_are_rejected(self):
        for value in (float("nan"), float("inf"), -1, "100", True):
            data = save()
            data["hero"]["gold"] = value
            self.error(400, lambda: self.create(data=data))
        cid = self.create()
        body = self.payload(cid, self.play(cid))
        body["save"]["hero"]["class"] = "mage"
        self.error(400, lambda: self.post("/characters/save", body))

    def test_rate_limit_and_session_expiry(self):
        for _ in range(10):
            self.store.rate("test", limit=10)
        self.error(429, lambda: self.store.rate("test", limit=10))
        self.now += 24 * 3600 + 1
        self.error(401, lambda: self.post("/characters/list"))

    def test_directory_heartbeat_secret_and_expiry(self):
        room = "a" * 32
        result = self.post("/custom/register", {"room": room, "name": "Friends' Game", "players": 1})
        self.error(403, lambda: self.post("/custom/heartbeat", {"room": room, "secret": "wrong", "players": 2}))
        self.post("/custom/heartbeat", {"room": room, "secret": result["secret"], "players": 2})
        listed = self.store.handle("GET", "/custom/list")["games"]
        self.assertEqual(2, listed[0]["players"])
        self.assertNotIn("secret", listed[0])
        self.now += 46
        self.assertEqual([], self.store.handle("GET", "/custom/list")["games"])

    def test_game_offline_preserves_characters(self):
        cid = self.create()
        self.now += 26
        self.error(503, lambda: self.play(cid))
        self.assertEqual(1, len(self.post("/characters/list")["characters"]))

    def trade_pair(self):
        other_token = self.register("trade_friend")["token"]
        first, second = self.create(), self.create(other_token)
        first_play, second_play = self.play(first), self.play(second, other_token)
        trade_id = "a" * 64
        mine, theirs = {"gold": 25, "items": []}, {"gold": 5, "items": []}
        first_save, second_save = save(), save()
        first_save["hero"]["gold"], second_save["hero"]["gold"] = 80, 120
        left = {"character": first, "lease": first_play["lease"], "trade_id": trade_id,
                "other": second, "revision": 0, "mine": mine, "theirs": theirs, "save": first_save}
        right = {"character": second, "lease": second_play["lease"], "trade_id": trade_id,
                 "other": first, "revision": 0, "mine": theirs, "theirs": mine, "save": second_save}
        return other_token, left, right

    def test_trade_needs_both_owners_and_commits_both_characters_atomically(self):
        other_token, left, right = self.trade_pair()
        result = self.post("/characters/trade_prepare", left)
        self.assertEqual("pending", result["state"])
        with contextlib.closing(self.store.connect()) as db:
            self.assertEqual([100, 100], sorted(json.loads(row[0])["hero"]["gold"] for row in db.execute("SELECT data FROM characters")))
        result = self.post("/characters/trade_prepare", right, other_token)
        self.assertEqual("committed", result["state"])
        receipt = self.post("/characters/trade_status", left)
        self.assertEqual(80, receipt["save"]["hero"]["gold"])
        with contextlib.closing(self.store.connect()) as db:
            self.assertEqual([80, 120], sorted(json.loads(row[0])["hero"]["gold"] for row in db.execute("SELECT data FROM characters")))
            self.assertEqual([1, 1], [row[0] for row in db.execute("SELECT revision FROM characters")])
        self.assertEqual("committed", self.post("/characters/trade_prepare", left)["state"])

    def test_trade_rejects_unapproved_rewards_and_inventory_creation(self):
        other_token, left, right = self.trade_pair()
        forged = copy.deepcopy(left)
        forged["save"]["hero"]["gold"] += 10
        self.error(400, lambda: self.post("/characters/trade_prepare", forged))
        forged = copy.deepcopy(left)
        forged["save"]["hero"]["inventory"] = [{"base": "fake_sword", "count": 1}]
        self.error(400, lambda: self.post("/characters/trade_prepare", forged))
        self.post("/characters/trade_prepare", left)
        mismatch = copy.deepcopy(right)
        mismatch["mine"]["gold"] = 6
        mismatch["save"]["hero"]["gold"] = 119
        self.error(409, lambda: self.post("/characters/trade_prepare", mismatch, other_token))
        with contextlib.closing(self.store.connect()) as db:
            self.assertEqual([100, 100], sorted(json.loads(row[0])["hero"]["gold"] for row in db.execute("SELECT data FROM characters")))

    def test_trade_blocks_overwriting_pending_inventories_and_release_cancels(self):
        other_token, left, right = self.trade_pair()
        self.post("/characters/trade_prepare", left)
        body = {"character": left["character"], "lease": left["lease"], "revision": 0, "request_id": "save-before-trade", "save": save()}
        self.error(409, lambda: self.post("/characters/save", body))
        self.post("/characters/release", left)
        self.error(409, lambda: self.post("/characters/trade_prepare", right, other_token))

    def test_trade_expiry_changes_neither_character(self):
        other_token, left, right = self.trade_pair()
        self.post("/characters/trade_prepare", left)
        self.now += 46
        self.error(409, lambda: self.post("/characters/trade_status", left))
        with contextlib.closing(self.store.connect()) as db:
            self.assertEqual([0, 0], [row[0] for row in db.execute("SELECT revision FROM characters")])


class PasswordTests(unittest.TestCase):
    def test_production_scrypt_hash_is_salted_and_deterministic(self):
        first = password_hash(PASSWORD, b"1234567890123456")
        self.assertEqual(32, len(first))
        self.assertEqual(first, password_hash(PASSWORD, b"1234567890123456"))
        self.assertNotEqual(first, password_hash(PASSWORD, b"different-salt!!"))


if __name__ == "__main__":
    unittest.main()
