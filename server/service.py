"""HTTPS account service for a small, trusted Beyond Heroes friends server.

Combat remains peer simulated. This service owns identity, character access,
durable saves, revisions, imports and exclusive play leases, not combat outcomes.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import hashlib
import hmac
import ipaddress
import json
import logging
import math
import os
import re
import secrets
import signal
import sqlite3
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

PROTOCOL = 18
SAVE_VERSION = 4
SERVER_VERSION = os.environ.get("BH_BUILD", "dev")   # a release id (git commit) set by the deployment; shown by /health
MAX_PLAYERS = 12
MAX_BODY = 2 * 1024 * 1024
SESSION_LIFE = 24 * 3600
LEASE_LIFE = 90
TICKET_LIFE = 45
USER_ID = re.compile(r"[A-Za-z0-9_]{3,32}\Z")
HASH_LIMIT = threading.BoundedSemaphore(2)


def client_address(peer, forwarded, trusted):
    """The caller's address and whether a trusted reverse proxy vouched for it.

    X-Forwarded-For is honoured only when the TCP peer is one of `trusted` (the local proxy in front of the service); the
    right-most entry is the one the proxy itself appended. From anyone else the header is ignored, so a client cannot choose
    the address its rate limits are counted against. A proxied request is never an internal (game coordinator) request."""
    if forwarded and peer in trusted:
        try:
            return str(ipaddress.ip_address(forwarded.split(",")[-1].strip())), True
        except ValueError:
            pass
    return peer, False


def audit_progress(old_hero, new_hero, seconds):
    """Names of implausible jumps between two confirmed saves of one character. Informational: the client simulates combat, so
    a modified game can claim any reward; these flags let the operator notice and review it (see docs/OFFICIAL_SERVER.md)."""
    flags = []
    old_progress, new_progress = old_hero.get("progress", {}), new_hero.get("progress", {})
    gained_levels = new_progress.get("level", 1) - old_progress.get("level", 1)
    if gained_levels > 10:
        flags.append("level+%d" % gained_levels)
    if new_progress.get("total_xp", 0) < old_progress.get("total_xp", 0) - 1:
        flags.append("xp_decreased")
    gained_gold = new_hero.get("gold", 0) - old_hero.get("gold", 0)
    if gained_gold > 20000000:
        flags.append("gold+%d" % gained_gold)
    if seconds > 0 and (new_progress.get("total_xp", 0) - old_progress.get("total_xp", 0)) / max(seconds, 1.0) > 1000000:
        flags.append("xp_rate")
    return flags


class ApiError(Exception):
    def __init__(self, status: int, message: str, code: str = "request_failed"):
        self.status, self.message, self.code = status, message, code


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password: str, salt: bytes) -> bytes:
    with HASH_LIMIT:
        return hashlib.scrypt(password.encode(), salt=salt, n=131072, r=8,
                              p=1, maxmem=256 * 1024 * 1024, dklen=32)


def check_password(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 128:
        raise ApiError(400, "Use a password with 12 to 128 characters.", "invalid_password")


def integer(value, low, high, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or int(value) != value or not low <= value <= high:
        raise ApiError(400, f"Invalid {label}.", "invalid_data")
    return int(value)


def _card_picture(hero):
    """bh-031: the picture a character card shows: the profile picture, else the ID shot of the hero's model (base64
    JPEG strings the game wrote; anything else is dropped)."""
    for key in ("profile_pic", "id_pic"):
        pic = hero.get(key)
        if isinstance(pic, str) and 0 < len(pic) <= 320000:
            return pic
    return ""


def validate_save(data):
    if not isinstance(data, dict) or data.get("version") != SAVE_VERSION or not isinstance(data.get("hero"), dict):
        raise ApiError(400, "This character needs to be upgraded by the current game before importing.", "invalid_save")
    hero = data["hero"]
    if hero.get("class") not in ("knight", "mage", "ranger", "shadowblade"):
        raise ApiError(400, "Unknown character class.", "invalid_save")
    name = hero.get("name")
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 18 or any(ord(c) < 32 for c in name):
        raise ApiError(400, "Character names must contain 2 to 18 readable characters.", "invalid_save")
    progress = hero.get("progress")
    if not isinstance(progress, dict):
        raise ApiError(400, "Character progression is missing.", "invalid_save")
    integer(progress.get("level", 1), 1, 300, "level")
    for key in ("xp", "total_xp", "free_points", "skill_points", "talent_points"):
        integer(progress.get(key, 0), 0, 2**53 - 1, key)
    integer(hero.get("gold", 0), 0, 2**53 - 1, "gold")
    integer(hero.get("difficulty", 1), 0, 3, "difficulty")
    if not isinstance(hero.get("inventory", []), list) or len(hero.get("inventory", [])) > 4096 or not isinstance(hero.get("equipment", {}), dict):
        raise ApiError(400, "Invalid inventory.", "invalid_save")
    if not isinstance(hero.get("map", "sanctuary"), str) or len(hero.get("map", "")) > 128:
        raise ApiError(400, "Invalid map.", "invalid_save")
    # Account tokens, passwords and device settings never enter character storage.
    save = {"version": SAVE_VERSION, "hero": hero}
    try:
        encoded = json.dumps(save, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    except (ValueError, TypeError, RecursionError):
        raise ApiError(400, "Invalid character data.", "invalid_save")
    if len(encoded.encode()) > MAX_BODY - 8192:
        raise ApiError(413, "Character data is too large.", "invalid_save")
    return encoded


def normalize_offer(offer):
    if not isinstance(offer, dict) or not isinstance(offer.get("items", []), list) or len(offer.get("items", [])) > 10:
        raise ApiError(400, "Invalid trade offer.")
    gold = integer(offer.get("gold", 0), 0, 100000000, "trade gold")
    items = []
    for raw in offer.get("items", []):
        if not isinstance(raw, dict) or raw.get("locked") or raw.get("favorite"):
            raise ApiError(400, "Protected items cannot be traded.")
        item = dict(raw)
        item.pop("locked", None)
        item.pop("favorite", None)
        item.pop("junk", None)
        integer(item.get("count", 1), 1, 1000000, "item count")
        items.append(item)
    items.sort(key=lambda item: json.dumps(item, sort_keys=True))
    return {"gold": gold, "items": items}


def item_counts(items):
    counts = collections.Counter()
    for raw in items:
        if raw is None:
            continue
        if not isinstance(raw, dict):
            raise ApiError(400, "Invalid trade inventory.")
        item = dict(raw)
        count = integer(item.pop("count", 1), 1, 1000000, "item count")
        for flag in ("locked", "favorite", "junk"):
            item.pop(flag, None)
        counts[json.dumps(item, sort_keys=True, separators=(",", ":"))] += count
    return counts


def validate_trade_result(before, after, mine, theirs):
    old, new = dict(before), dict(after)
    old_inventory, new_inventory = old.pop("inventory", []), new.pop("inventory", [])
    old_gold, new_gold = old.pop("gold", 0), new.pop("gold", 0)
    if old != new or old_gold < mine["gold"] or new_gold != old_gold-mine["gold"]+theirs["gold"]:
        raise ApiError(400, "A trade may only exchange the approved items and gold.", "invalid_trade")
    remaining = item_counts(old_inventory)
    offered = item_counts(mine["items"])
    eligible = item_counts([item for item in old_inventory if isinstance(item, dict) and not item.get("locked") and not item.get("favorite")])
    if any(eligible[key] < count for key, count in offered.items()):
        raise ApiError(400, "An offered item is no longer in your bag.", "invalid_trade")
    remaining.subtract(offered)
    remaining.update(item_counts(theirs["items"]))
    if +remaining != item_counts(new_inventory):
        raise ApiError(400, "Trade inventory does not match the two offers.", "invalid_trade")


class Store:
    def __init__(self, directory: Path, *, host="127.0.0.1", game_port=24680, clock=time.time):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "beyond_heroes.sqlite3"
        self.host, self.game_port, self.clock = host, game_port, clock
        self.heartbeat_at = 0
        self.lock = threading.RLock()
        self.rates = collections.OrderedDict()
        self.custom_games = {}
        self.dummy_salt = secrets.token_bytes(16)
        self.dummy_hash = password_hash("dummy-password-unused", self.dummy_salt)
        with contextlib.closing(self.connect()) as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
                INSERT INTO schema_version SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM schema_version);
                CREATE TABLE IF NOT EXISTS accounts(
                    id TEXT PRIMARY KEY, userid TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    salt BLOB NOT NULL, password BLOB NOT NULL,
                    recovery TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(
                    token TEXT PRIMARY KEY, account TEXT NOT NULL REFERENCES accounts(id), expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS characters(
                    id TEXT PRIMARY KEY, account TEXT NOT NULL REFERENCES accounts(id),
                    slot INTEGER NOT NULL, data TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0,
                    saved REAL NOT NULL, imported INTEGER NOT NULL DEFAULT 0, UNIQUE(account,slot));
                CREATE TABLE IF NOT EXISTS imports(
                    account TEXT NOT NULL REFERENCES accounts(id), source TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, character TEXT NOT NULL REFERENCES characters(id),
                    PRIMARY KEY(account,source), UNIQUE(account,fingerprint));
                CREATE TABLE IF NOT EXISTS leases(
                    id TEXT PRIMARY KEY, account TEXT NOT NULL UNIQUE REFERENCES accounts(id),
                    character TEXT NOT NULL UNIQUE REFERENCES characters(id),
                    expires REAL NOT NULL, connected INTEGER NOT NULL DEFAULT 0,
                    peer INTEGER, last_save TEXT, last_payload TEXT);
                CREATE TABLE IF NOT EXISTS tickets(
                    token TEXT PRIMARY KEY, lease TEXT NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
                    expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS audit(
                    id INTEGER PRIMARY KEY, account TEXT, event TEXT NOT NULL,
                    character TEXT, at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS trades(
                    id TEXT PRIMARY KEY, a TEXT NOT NULL REFERENCES characters(id),
                    b TEXT NOT NULL REFERENCES characters(id), state TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS trade_approvals(
                    trade_id TEXT NOT NULL REFERENCES trades(id), character TEXT NOT NULL REFERENCES characters(id),
                    account TEXT NOT NULL REFERENCES accounts(id), lease TEXT NOT NULL,
                    revision INTEGER NOT NULL, mine TEXT NOT NULL, theirs TEXT NOT NULL, data TEXT NOT NULL,
                    PRIMARY KEY(trade_id,character));
            """)
            if db.execute("SELECT version FROM schema_version").fetchone()[0] != 1:
                raise RuntimeError("Unsupported database schema; restore a compatible server version.")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @contextlib.contextmanager
    def transaction(self):
        with self.lock, contextlib.closing(self.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def rate(self, key, limit=20, window=60):
        now = self.clock()
        with self.lock:
            # Bounded table and pre-hash limits prevent unlimited KDF work/memory.
            times = self.rates.setdefault(key, collections.deque())
            self.rates.move_to_end(key)
            while times and times[0] <= now - window:
                times.popleft()
            if len(times) >= limit:
                raise ApiError(429, "Too many attempts. Wait a minute and try again.", "rate_limited")
            times.append(now)
            while len(self.rates) > 4096:
                self.rates.popitem(last=False)

    def cleanup(self, db):
        now = self.clock()
        db.execute("DELETE FROM sessions WHERE expires<=?", (now,))
        db.execute("DELETE FROM tickets WHERE expires<=?", (now,))
        db.execute("DELETE FROM leases WHERE expires<=?", (now,))
        db.execute("UPDATE trades SET state='cancelled' WHERE state='pending' AND created<?", (now-45,))

    def account(self, db, token):
        row = db.execute("SELECT a.* FROM accounts a JOIN sessions s ON s.account=a.id WHERE s.token=? AND s.expires>?", (digest(token), self.clock())).fetchone()
        if row is None:
            raise ApiError(401, "Sign in again to continue.", "unauthorized")
        return row

    def session(self, db, account):
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO sessions VALUES(?,?,?)", (digest(token), account, self.clock() + SESSION_LIFE))
        return token

    def audit(self, db, account, event, character=None):
        db.execute("INSERT INTO audit(account,event,character,at) VALUES(?,?,?,?)", (account, event, character, self.clock()))

    def character(self, db, account, cid):
        row = db.execute("SELECT * FROM characters WHERE id=? AND account=?", (cid, account)).fetchone()
        if row is None:
            raise ApiError(404, "Character not found.", "not_found")
        return row

    @staticmethod
    def summary(row):
        hero = json.loads(row["data"])["hero"]
        return {"id": row["id"], "slot": row["slot"], "name": hero["name"], "class": hero["class"],
                "level": hero["progress"].get("level", 1), "map": hero.get("map", "sanctuary"),
                "saved_at": row["saved"], "revision": row["revision"], "imported": bool(row["imported"]),
                # bh-031: the character card's picture (profile picture, else the ID shot of their model)
                "pic": _card_picture(hero)}

    def handle(self, method, path, body=None, *, token="", ip="127.0.0.1", internal=False):
        body = {} if body is None else body
        if not isinstance(body, dict):
            raise ApiError(400, "Expected a JSON object.")
        if method == "GET" and path == "/custom/list":
            self.rate(("directory", ip), 60)
            with self.lock:
                self.custom_games = {k: v for k, v in self.custom_games.items() if v["expires"] > self.clock()}
                return {"games": [{key: value for key, value in game.items() if key not in ("secret", "expires", "ip")} for game in self.custom_games.values()]}
        if method == "GET" and path == "/health":
            with self.transaction() as db:
                self.cleanup(db)
                count = db.execute("SELECT count(*) FROM leases").fetchone()[0]
            return {"name": "Official Beyond Heroes", "protocol": PROTOCOL, "save_version": SAVE_VERSION,
                    "max_players": MAX_PLAYERS, "players": count, "game_online": self.clock() - self.heartbeat_at < 25,
                    "version": SERVER_VERSION,
                    "game_host": self.host, "game_port": self.game_port, "progress_mode": "friends_test"}
        if method != "POST":
            raise ApiError(404, "Unknown request.", "not_found")
        self.rate(("requests", ip), 1200)
        if path in ("/custom/register", "/custom/heartbeat", "/custom/remove"):
            room = body.get("room", "")
            if not isinstance(room, str) or not re.fullmatch(r"[a-f0-9]{32}", room):
                raise ApiError(400, "Invalid custom room identity.")
            with self.lock:
                self.custom_games = {k: v for k, v in self.custom_games.items() if v["expires"] > self.clock()}
                if path == "/custom/register":
                    self.rate(("custom_host", ip), 5)
                    if room in self.custom_games:
                        raise ApiError(409, "This room is already listed.")
                    if sum(game["ip"] == ip for game in self.custom_games.values()) >= 5 or len(self.custom_games) >= 256:
                        raise ApiError(429, "The custom game list is full.")
                    name = body.get("name", "Custom Game")
                    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 48 or any(ord(c) < 32 for c in name):
                        raise ApiError(400, "Use a game name with 2 to 48 readable characters.")
                    secret = secrets.token_urlsafe(32)
                    self.custom_games[room] = {"room": room, "name": name.strip(), "address": ip, "ip": ip,
                        "port": integer(body.get("port", 24680), 1024, 65535, "port"), "max": MAX_PLAYERS,
                        "players": integer(body.get("players", 1), 1, MAX_PLAYERS, "players"), "bh": PROTOCOL,
                        "secret": digest(secret), "expires": self.clock()+45}
                    return {"secret": secret}
                game = self.custom_games.get(room)
                secret = body.get("secret", "")
                if game is None or not isinstance(secret, str) or not hmac.compare_digest(digest(secret), game["secret"]):
                    raise ApiError(403, "Custom room listing expired.", "forbidden")
                if path == "/custom/remove":
                    del self.custom_games[room]
                else:
                    game["players"] = integer(body.get("players", 1), 1, MAX_PLAYERS, "players")
                    game["expires"] = self.clock()+45
                return {"ok": True}
        if path.startswith("/auth/"):
            self.rate(("auth", ip), 30) # Twelve friends may share one public IP.
            userid = body.get("userid", "")
            if not isinstance(userid, str) or not USER_ID.fullmatch(userid):
                raise ApiError(400, "UserID must be 3 to 32 letters, numbers or underscores.", "invalid_userid")
            userid = userid.lower()
            self.rate(("userid", userid), 10)
            password = body.get("password", "")
            check_password(password)
            if path == "/auth/register":
                salt, recovery = secrets.token_bytes(16), secrets.token_urlsafe(24)
                hashed = password_hash(password, salt)
                with self.transaction() as db:
                    aid = secrets.token_hex(16)
                    try:
                        db.execute("INSERT INTO accounts VALUES(?,?,?,?,?,?)", (aid, userid, salt, hashed, digest(recovery), self.clock()))
                    except sqlite3.IntegrityError:
                        raise ApiError(409, "This UserID is already registered.", "userid_taken")
                    self.audit(db, aid, "registered")
                    return {"userid": userid, "token": self.session(db, aid), "recovery_code": recovery}
            with contextlib.closing(self.connect()) as db:
                row = db.execute("SELECT * FROM accounts WHERE userid=?", (userid,)).fetchone()
            if path == "/auth/login":
                hashed = password_hash(password, row["salt"] if row else self.dummy_salt)
                if row is None or not hmac.compare_digest(hashed, row["password"]):
                    raise ApiError(401, "UserID or password is incorrect.", "unauthorized")
                with self.transaction() as db:
                    current = db.execute("SELECT password FROM accounts WHERE id=?", (row["id"],)).fetchone()
                    if not hmac.compare_digest(current[0], row["password"]):
                        raise ApiError(401, "Password changed. Sign in again.", "unauthorized")
                    self.cleanup(db)
                    return {"userid": row["userid"], "token": self.session(db, row["id"])}
            if path == "/auth/recover":
                recovery = body.get("recovery_code", "")
                if not isinstance(recovery, str) or row is None or not hmac.compare_digest(digest(recovery), row["recovery"]):
                    raise ApiError(401, "UserID or recovery code is incorrect.", "unauthorized")
                salt, recovery = secrets.token_bytes(16), secrets.token_urlsafe(24)
                hashed = password_hash(password, salt)
                with self.transaction() as db:
                    # Check again inside the transaction: each recovery code is single use.
                    current = db.execute("SELECT recovery FROM accounts WHERE id=?", (row["id"],)).fetchone()
                    if not hmac.compare_digest(current[0], row["recovery"]):
                        raise ApiError(401, "Recovery code already used.", "unauthorized")
                    db.execute("UPDATE accounts SET salt=?,password=?,recovery=? WHERE id=?", (salt, hashed, digest(recovery), row["id"]))
                    db.execute("DELETE FROM sessions WHERE account=?", (row["id"],))
                    db.execute("DELETE FROM leases WHERE account=?", (row["id"],))
                    self.audit(db, row["id"], "password_recovered")
                    return {"userid": userid, "token": self.session(db, row["id"]), "recovery_code": recovery}
            raise ApiError(404, "Unknown account request.")
        if path.startswith("/internal/"):
            if not internal or not ipaddress.ip_address(ip).is_loopback:
                raise ApiError(403, "Server access required.", "forbidden")
            with self.transaction() as db:
                self.cleanup(db)
                if path == "/internal/start":
                    db.execute("DELETE FROM leases")
                    db.execute("UPDATE trades SET state='cancelled' WHERE state='pending'")
                    self.heartbeat_at = self.clock()
                    self.audit(db, None, "game_started")
                    return {"ok": True}
                if path == "/internal/heartbeat":
                    self.heartbeat_at = self.clock()
                    return {"leases": [r[0] for r in db.execute("SELECT id FROM leases WHERE connected=1")]}
                if path == "/internal/redeem":
                    ticket = body.get("ticket", "")
                    peer = integer(body.get("peer"), 2, 2**31 - 1, "peer")
                    if not isinstance(ticket, str):
                        raise ApiError(401, "Invalid game ticket.")
                    lease = db.execute("SELECT l.* FROM leases l JOIN tickets t ON t.lease=l.id WHERE t.token=? AND t.expires>?", (digest(ticket), self.clock())).fetchone()
                    if lease is None or lease["connected"]:
                        raise ApiError(401, "Game ticket expired. Select your character again.", "invalid_ticket")
                    db.execute("DELETE FROM tickets WHERE token=?", (digest(ticket),))
                    db.execute("UPDATE leases SET connected=1,peer=? WHERE id=?", (peer, lease["id"]))
                    row = self.character(db, lease["account"], lease["character"])
                    uid = db.execute("SELECT userid FROM accounts WHERE id=?", (lease["account"],)).fetchone()[0]
                    return {"lease": lease["id"], "userid": uid, "character": self.summary(row)}
                if path == "/internal/disconnect":
                    # Allow a short save window after the ENet disconnect; no new game can reuse it.
                    db.execute("UPDATE leases SET connected=0,expires=min(expires,?) WHERE id=?", (self.clock()+15, body.get("lease", "")))
                    db.execute("UPDATE trades SET state='cancelled' WHERE state='pending' AND (a IN (SELECT character FROM leases WHERE id=?) OR b IN (SELECT character FROM leases WHERE id=?))", (body.get("lease", ""), body.get("lease", "")))
                    return {"ok": True}
                raise ApiError(404, "Unknown server request.")
        with self.transaction() as db:
            self.cleanup(db)
            account = self.account(db, token)
            aid = account["id"]
            self.rate(("account_requests", aid), 240)
            if path == "/account/logout":
                db.execute("DELETE FROM sessions WHERE token=?", (digest(token),))
                return {"ok": True}
            if path == "/characters/list":
                return {"userid": account["userid"], "characters": [self.summary(r) for r in db.execute("SELECT * FROM characters WHERE account=? ORDER BY slot", (aid,))]}
            if path in ("/characters/create", "/characters/import"):
                slot = integer(body.get("slot"), 0, 7, "slot")
                data = validate_save(body.get("save"))
                if path.endswith("create"):
                    hero = json.loads(data)["hero"]
                    if hero["progress"].get("level", 1) != 1 or hero["progress"].get("total_xp", 0) != 0:
                        raise ApiError(400, "Use Import Existing Progress for an existing character.", "invalid_save")
                imported = path.endswith("import")
                source = body.get("source", "")
                if imported:
                    if not isinstance(source, str) or not 8 <= len(source) <= 128:
                        raise ApiError(400, "Local character identity is missing.", "invalid_save")
                    fingerprint = digest(json.dumps(json.loads(data), sort_keys=True, separators=(",", ":")))
                    previous = db.execute("SELECT character FROM imports WHERE account=? AND (source=? OR fingerprint=?)", (aid, source, fingerprint)).fetchone()
                    if previous:
                        return {"character": self.summary(self.character(db, aid, previous[0])), "already_imported": True}
                cid = secrets.token_hex(16)
                try:
                    db.execute("INSERT INTO characters VALUES(?,?,?,?,0,?,?)", (cid, aid, slot, data, self.clock(), int(imported)))
                except sqlite3.IntegrityError:
                    raise ApiError(409, "This official character slot is occupied. Choose an empty slot.", "slot_occupied")
                if imported:
                    db.execute("INSERT INTO imports VALUES(?,?,?,?)", (aid, source, fingerprint, cid))
                self.audit(db, aid, "character_imported" if imported else "character_created", cid)
                return {"character": self.summary(self.character(db, aid, cid)), "already_imported": False}
            cid = body.get("character", "")
            if not isinstance(cid, str):
                raise ApiError(400, "Invalid character.")
            row = self.character(db, aid, cid)
            if path == "/characters/play":
                if self.clock() - self.heartbeat_at >= 25:
                    raise ApiError(503, "The official game server is offline. Your saved characters are safe.", "game_offline")
                if db.execute("SELECT 1 FROM leases WHERE account=?", (aid,)).fetchone():
                    raise ApiError(409, "This account is already playing. Close the other game or wait 90 seconds after a lost connection.", "already_playing")
                if db.execute("SELECT count(*) FROM leases").fetchone()[0] >= MAX_PLAYERS:
                    raise ApiError(409, "The official server is full (12 players).", "server_full")
                lease, ticket = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                db.execute("INSERT INTO leases(id,account,character,expires) VALUES(?,?,?,?)", (lease, aid, cid, self.clock()+LEASE_LIFE))
                db.execute("INSERT INTO tickets VALUES(?,?,?)", (digest(ticket), lease, self.clock()+TICKET_LIFE))
                self.audit(db, aid, "play_started", cid)
                return {"lease": lease, "ticket": ticket, "revision": row["revision"], "save": json.loads(row["data"]),
                        "game_host": self.host, "game_port": self.game_port}
            lease_id = body.get("lease", "")
            lease = db.execute("SELECT * FROM leases WHERE id=? AND account=? AND character=?", (lease_id, aid, cid)).fetchone()
            if lease is None:
                raise ApiError(409, "Your play session expired. Sign in and load your last server save.", "lease_expired")
            if path == "/characters/release":
                db.execute("UPDATE trades SET state='cancelled' WHERE state='pending' AND (a=? OR b=?)", (cid, cid))
                db.execute("DELETE FROM leases WHERE id=?", (lease_id,))
                return {"ok": True}
            if path == "/characters/save":
                if lease["peer"] is None:
                    raise ApiError(409, "Connect to the official game server before saving.", "not_connected")
                if db.execute("SELECT 1 FROM trades WHERE state='pending' AND (a=? OR b=?)", (cid, cid)).fetchone():
                    raise ApiError(409, "Finish the pending trade before saving.", "trade_pending")
                request_id = body.get("request_id")
                if not isinstance(request_id, str) or not 8 <= len(request_id) <= 128:
                    raise ApiError(400, "Save request identity is missing.")
                data = validate_save(body.get("save"))
                payload = digest(data)
                if request_id == lease["last_save"]:
                    if payload != lease["last_payload"]:
                        raise ApiError(409, "A save request was reused with different data.", "revision_conflict")
                    db.execute("UPDATE leases SET expires=? WHERE id=?", (self.clock()+LEASE_LIFE, lease_id))
                    return {"revision": row["revision"], "saved_at": row["saved"], "duplicate": True}
                revision = integer(body.get("revision"), 0, 2**53-1, "revision")
                if revision != row["revision"]:
                    raise ApiError(409, "The character changed on the server. Reload it before playing again.", "revision_conflict")
                before, after = json.loads(row["data"])["hero"], json.loads(data)["hero"]
                if after["class"] != before["class"]:
                    raise ApiError(400, "Character class cannot change.", "invalid_save")
                flags = audit_progress(before, after, self.clock() - row["saved"])
                if flags:
                    self.audit(db, aid, "suspicious_progress:" + ",".join(flags), cid)
                # Never acknowledge before SQLite has committed. Returning from this
                # transaction commits before the HTTP handler serializes the reply.
                now = self.clock()
                db.execute("UPDATE characters SET data=?,revision=revision+1,saved=? WHERE id=?", (data, now, cid))
                db.execute("UPDATE leases SET expires=?,last_save=?,last_payload=? WHERE id=?", (now+LEASE_LIFE, request_id, payload, lease_id))
                return {"revision": revision+1, "saved_at": now, "duplicate": False}
            if path in ("/characters/trade_prepare", "/characters/trade_status"):
                trade_id = body.get("trade_id", "")
                if not isinstance(trade_id, str) or not re.fullmatch(r"[a-f0-9]{64}", trade_id):
                    raise ApiError(400, "Invalid trade identity.")
                trade = db.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
                if path.endswith("prepare"):
                    other = body.get("other", "")
                    if not isinstance(other, str) or other == cid:
                        raise ApiError(400, "Choose another official character.")
                    other_lease = db.execute("SELECT * FROM leases WHERE character=? AND connected=1", (other,)).fetchone()
                    if not lease["connected"] or other_lease is None:
                        raise ApiError(409, "Both characters must be connected to trade.", "trade_cancelled")
                    if trade is None:
                        if db.execute("SELECT 1 FROM trades WHERE state='pending' AND (a IN (?,?) OR b IN (?,?))", (cid, other, cid, other)).fetchone():
                            raise ApiError(409, "A character is already completing another trade.", "trade_cancelled")
                        a, b = sorted((cid, other))
                        db.execute("INSERT INTO trades VALUES(?,?,?,'pending',?)", (trade_id, a, b, self.clock()))
                        trade = db.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
                    if {trade["a"], trade["b"]} != {cid, other}:
                        raise ApiError(403, "This trade belongs to different characters.")
                    if trade["state"] == "pending":
                        revision = integer(body.get("revision"), 0, 2**53-1, "revision")
                        if revision != row["revision"]:
                            raise ApiError(409, "Your character changed. Load its server save before trading.", "revision_conflict")
                        mine, theirs = normalize_offer(body.get("mine")), normalize_offer(body.get("theirs"))
                        data = validate_save(body.get("save"))
                        validate_trade_result(json.loads(row["data"])["hero"], json.loads(data)["hero"], mine, theirs)
                        previous = db.execute("SELECT * FROM trade_approvals WHERE trade_id=? AND character=?", (trade_id, cid)).fetchone()
                        approval = (trade_id, cid, aid, lease_id, revision, json.dumps(mine, sort_keys=True), json.dumps(theirs, sort_keys=True), data)
                        if previous:
                            if tuple(previous) != approval:
                                raise ApiError(409, "Trade approval changed.", "trade_cancelled")
                        else:
                            db.execute("INSERT INTO trade_approvals VALUES(?,?,?,?,?,?,?,?)", approval)
                        approvals = db.execute("SELECT * FROM trade_approvals WHERE trade_id=? ORDER BY character", (trade_id,)).fetchall()
                        if len(approvals) == 2:
                            first, second = approvals
                            if first["mine"] != second["theirs"] or first["theirs"] != second["mine"]:
                                raise ApiError(409, "The two trade offers do not match.", "trade_cancelled")
                            for approval in approvals:
                                current = self.character(db, approval["account"], approval["character"])
                                if current["revision"] != approval["revision"]:
                                    raise ApiError(409, "A character changed during the trade.", "revision_conflict")
                                if not db.execute("SELECT 1 FROM leases WHERE id=? AND connected=1", (approval["lease"],)).fetchone():
                                    raise ApiError(409, "A character disconnected before the trade completed.", "trade_cancelled")
                            for approval in approvals:
                                db.execute("UPDATE characters SET data=?,revision=revision+1,saved=? WHERE id=?", (approval["data"], self.clock(), approval["character"]))
                                db.execute("UPDATE leases SET last_save=NULL,last_payload=NULL WHERE id=?", (approval["lease"],))
                                self.audit(db, approval["account"], "trade_committed", approval["character"])
                            db.execute("UPDATE trades SET state='committed' WHERE id=?", (trade_id,))
                            trade = db.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
                if trade is None or cid not in (trade["a"], trade["b"]):
                    raise ApiError(404, "Trade not found.")
                if trade["state"] == "cancelled":
                    raise ApiError(409, "The trade expired. Neither character was changed.", "trade_cancelled")
                current = self.character(db, aid, cid)
                result = {"state": trade["state"], "revision": current["revision"]}
                if trade["state"] == "committed":
                    result["save"] = json.loads(current["data"])
                return result
            raise ApiError(404, "Unknown character request.")

    def backup(self, keep=16, keep_days=30):
        folder = self.directory / "backups"
        folder.mkdir(exist_ok=True)
        target = folder / (time.strftime("%Y%m%d-%H%M%S", time.gmtime()) + "-" + secrets.token_hex(3) + ".sqlite3")
        with self.lock, contextlib.closing(self.connect()) as source, contextlib.closing(sqlite3.connect(target)) as destination:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
        prune_backups(folder, keep, keep_days)
        return target


def prune_backups(folder, keep=16, keep_days=30):
    """Keep the newest `keep` backups, plus the newest one of each UTC day for `keep_days` days; delete the rest.

    Names start with a UTC timestamp, so sorting by name is sorting by age. The disk use is bounded:
    at most keep + keep_days files."""
    names = sorted(Path(folder).glob("[0-9]" * 8 + "-*.sqlite3"), key=lambda p: p.name, reverse=True)
    survivors, days = set(names[:keep]), set()
    for path in names[keep:]:
        day = path.name[:8]
        if day not in days and len(days) < keep_days:
            days.add(day)
            survivors.add(path)
    for path in names:
        if path not in survivors:
            path.unlink()
    return len(survivors)


class HttpServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32

    WORKERS = 24

    def __init__(self, address, store, secret, trusted_proxies=()):
        super().__init__(address, Handler)
        self.store, self.secret = store, secret
        self.trusted_proxies = frozenset(trusted_proxies)
        self.workers = threading.BoundedSemaphore(self.WORKERS)

    def drain(self, timeout=8.0):
        """Wait for in-flight requests to finish (each is one atomic SQLite transaction); False if some did not."""
        deadline = time.monotonic() + timeout
        taken = 0
        try:
            while taken < self.WORKERS:
                if not self.workers.acquire(timeout=max(0.0, deadline - time.monotonic())):
                    return False
                taken += 1
            return True
        finally:
            for _ in range(taken):
                self.workers.release()

    def process_request(self, request, client_address):
        if not self.workers.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.workers.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.workers.release()


class Handler(BaseHTTPRequestHandler):
    server_version = "BeyondHeroes"
    sys_version = ""

    def setup(self):
        self.request.settimeout(10)
        super().setup()

    def log_message(self, *_args):
        pass  # Never log Authorization, credentials, request bodies or ticket URLs.

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PUT(self):
        self.dispatch("PUT")

    do_DELETE = do_PATCH = do_PUT

    def do_HEAD(self):
        self.dispatch("HEAD")

    do_OPTIONS = do_HEAD

    def dispatch(self, method):
        try:
            if self.headers.get("Transfer-Encoding"):
                raise ApiError(400, "Chunked requests are not supported.")
            length = self.headers.get("Content-Length", "0")
            if not length.isdigit() or int(length) > MAX_BODY:
                raise ApiError(413, "Request is too large.")
            if method == "POST" and self.headers.get_content_type() != "application/json":
                raise ApiError(415, "Use application/json.")
            raw = self.rfile.read(int(length))
            try:
                body = json.loads(raw or b"{}", parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            except (ValueError, UnicodeError, RecursionError):
                raise ApiError(400, "Invalid JSON.")
            path = urlsplit(self.path).path
            authorization = self.headers.get("Authorization", "")
            token = authorization[7:] if authorization.startswith("Bearer ") else ""
            ip, proxied = client_address(self.client_address[0], self.headers.get("X-Forwarded-For", ""), self.server.trusted_proxies)
            internal = not proxied and hmac.compare_digest(self.headers.get("X-Server-Key", ""), self.server.secret)
            result = self.server.store.handle(method, path, body, token=token, ip=ip, internal=internal)
            self.reply(200, result)
        except ApiError as error:
            self.reply(error.status, {"error": error.message, "code": error.code})
        except (TimeoutError, ConnectionError, ssl.SSLError):
            self.close_connection = True
        except Exception:
            logging.exception("Account service request failed")
            self.reply(500, {"error": "The server could not complete this request. Try again.", "code": "server_error"})

    def reply(self, status, result):
        payload = json.dumps(result, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        if status == 429:
            self.send_header("Retry-After", "60")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True


def main():
    parser = argparse.ArgumentParser(description="Beyond Heroes HTTPS accounts and character saves")
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "data" / "server.json")
    parser.add_argument("--backup", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    store = Store(args.config.parent, host=config["game_host"], game_port=config.get("game_port", 24680))
    if args.backup:
        print("Verified backup:", store.backup())
        return
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(config["certificate"], config["private_key"])
    server = HttpServer((config.get("bind", "0.0.0.0"), config.get("api_port", 8443)), store, config["server_key"],
                        config.get("trusted_proxies", []))
    server.socket = context.wrap_socket(server.socket, server_side=True, do_handshake_on_connect=False)
    stop = threading.Event()

    def backups():
        while not stop.wait(900):
            try:
                store.backup()
            except Exception:
                logging.exception("Automatic database backup failed")

    store.backup()
    threading.Thread(target=backups, daemon=True).start()
    print(f"Beyond Heroes account service {SERVER_VERSION} (protocol {PROTOCOL}) listening on HTTPS port {server.server_port}; data: {store.path}", flush=True)

    def request_stop(signum, _frame):
        # serve_forever() must be stopped from another thread; the cleanup below then runs on the main thread
        print(f"Stop requested (signal {signum}); finishing requests and saving a backup.", flush=True)
        threading.Thread(target=server.shutdown, daemon=True).start()

    for name in ("SIGTERM", "SIGINT", "SIGBREAK"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), request_stop)
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        stop.set()
        server.server_close()
        if not server.drain():
            logging.warning("Some requests were still running at shutdown; clients retry them with their save request identity")
        store.backup()
        print("Account service stopped cleanly.", flush=True)


if __name__ == "__main__":
    main()
