#!/bin/bash
# Update to a new reviewed revision, with a health check and automatic rollback.
#   sudo ./server/deploy/update.sh            (run from a checkout of the new commit)
#   sudo ./server/deploy/update.sh --rollback (switch back to the previous release and restart)
#
# Order: announce a maintenance window and wait for confirmed saves -> verified backup -> stage the new release beside the old
# one -> stop -> switch the `current` link -> start -> health check -> on failure, switch back automatically.
# The data directory is never inside a release, so code can be replaced or rolled back without touching player data. The
# database schema is checked first: a release that cannot read the current database is refused.
set -euo pipefail
ROOT=/opt/beyond-heroes
STATE=/var/lib/beyond-heroes
[ "$(id -u)" = 0 ] || { echo "Run as root (sudo)."; exit 1; }

switch_to() {
    systemctl stop beyond-heroes.service
    ln -sfn "$1" "$ROOT/current"
    PROTOCOL="$(grep -m1 '^PROTOCOL' "$ROOT/current/server/service.py" | grep -o '[0-9]*')"
    sed -i "s/^BH_BUILD=.*/BH_BUILD=$(basename "$1")/; s/^BH_PROTOCOL=.*/BH_PROTOCOL=$PROTOCOL/" /etc/beyond-heroes/build.env
    install -m 0644 "$ROOT/current/server/deploy/"beyond-heroes*.service "$ROOT/current/server/deploy/"beyond-heroes*.timer /etc/systemd/system/
    systemctl daemon-reload
    systemctl start beyond-heroes.service
}
healthy() {
    set -a; . /etc/beyond-heroes/build.env; set +a
    for _ in $(seq 1 30); do
        if "$ROOT/current/.venv/bin/python" -m server.healthcheck --url "$BH_PUBLIC_URL" --expect-protocol "$BH_PROTOCOL" >/dev/null 2>&1; then return 0; fi
        sleep 4
    done
    return 1
}

PREVIOUS="$(readlink -f "$ROOT/current")"
if [ "${1:-}" = "--rollback" ]; then
    TARGET="$(ls -1dt "$ROOT"/releases/*/ | sed 's:/$::' | grep -vx "$PREVIOUS" | head -n 1)"
    [ -n "$TARGET" ] || { echo "No earlier release to go back to."; exit 1; }
    echo "Rolling back from $PREVIOUS to $TARGET"
    cd "$TARGET"
    # code can only go back if it understands the database as it is now; otherwise restore a backup into staging first
    sudo -u beyond-heroes "$TARGET/.venv/bin/python" -m server.maintenance verify "$(ls -1t "$STATE"/backups/*.sqlite3 | head -n 1)" >/dev/null
    switch_to "$TARGET"
    healthy && echo "Rollback complete: $(basename "$TARGET") is serving." || { echo "The rolled-back release is not healthy: check journalctl -u beyond-heroes"; exit 1; }
    exit 0
fi

[ -f server/service.py ] && [ -f game/project.godot ] || { echo "Run from the root of a Beyond Heroes checkout."; exit 2; }
RELEASE_ID="$(git rev-parse --short=12 HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
DEST="$ROOT/releases/$RELEASE_ID"
[ "$DEST" != "$PREVIOUS" ] || { echo "Release $RELEASE_ID is already current."; exit 0; }
echo "Players: announce the maintenance window, then confirm saves are idle. Taking a verified backup first."
sudo -u beyond-heroes "$ROOT/current/.venv/bin/python" -m server.maintenance backup --config "$STATE/server.json"
if [ ! -d "$DEST" ]; then
    install -d -o beyond-heroes -g beyond-heroes "$DEST"
    tar --exclude=.git --exclude='server/data' --exclude='output' --exclude='build' --exclude='work' --exclude='references' --exclude='audio/source' -cf - . | tar -xf - -C "$DEST"
    chown -R beyond-heroes:beyond-heroes "$DEST"
    sudo -u beyond-heroes python3 -m venv "$DEST/.venv"
    sudo -u beyond-heroes "$DEST/.venv/bin/pip" install --no-cache-dir -r "$DEST/server/requirements.lock"
    sudo -u beyond-heroes env HOME="$STATE/home" /opt/godot/godot --headless --path "$DEST/game" --import >/dev/null 2>&1 || true
fi
# the new code must read the current database before it is allowed to serve
sudo -u beyond-heroes "$DEST/.venv/bin/python" -m server.maintenance verify "$STATE/beyond_heroes.sqlite3" >/dev/null
switch_to "$DEST"
if healthy; then
    echo "Release $RELEASE_ID is serving. Previous release kept for rollback: $(basename "$PREVIOUS")"
    ls -1dt "$ROOT"/releases/*/ | tail -n +4 | xargs -r rm -rf     # keep the three newest releases
else
    echo "The new release did not become healthy; switching back to $(basename "$PREVIOUS")."
    switch_to "$PREVIOUS"
    healthy && echo "Previous release restored." || echo "Previous release is also unhealthy: see journalctl -u beyond-heroes."
    exit 1
fi
