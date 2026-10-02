#!/bin/bash
# First-time install on a fresh Ubuntu/Debian VM (systemd, Python 3.12+). Run as root from a checkout of the reviewed commit:
#
#   sudo ./server/deploy/install.sh --public-host game.example.com \
#        --godot-zip /root/Godot_v4.7.2-stable_linux.x86_64.zip --godot-sha512 <hash from godotengine.org>
#
# It never overwrites an existing configuration, database or certificate, so running it again on a configured VM is safe.
# Not yet verified on a real VM from this repository: follow deploy/README.md "Verification" and record the results.
set -euo pipefail

PUBLIC_HOST="" GODOT_ZIP="" GODOT_SHA512="" API_PORT=8443 GAME_PORT=24680
while [ $# -gt 0 ]; do
    case "$1" in
        --public-host) PUBLIC_HOST="$2"; shift 2 ;;
        --godot-zip) GODOT_ZIP="$2"; shift 2 ;;
        --godot-sha512) GODOT_SHA512="$2"; shift 2 ;;
        --game-port) GAME_PORT="$2"; shift 2 ;;
        *) echo "Unknown option $1"; exit 2 ;;
    esac
done
[ "$(id -u)" = 0 ] || { echo "Run as root (sudo)."; exit 1; }
[ -n "$PUBLIC_HOST" ] || { echo "--public-host is required (the DNS name players will use)."; exit 2; }
[ -f server/service.py ] && [ -f game/project.godot ] || { echo "Run from the root of a Beyond Heroes checkout."; exit 2; }
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' || { echo "Python 3.12 or newer is required."; exit 1; }
command -v caddy >/dev/null || { echo "Install Caddy first (https://caddyserver.com/docs/install) so it can obtain the public certificate."; exit 1; }

RELEASE_ID="$(git rev-parse --short=12 HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
ROOT=/opt/beyond-heroes
STATE=/var/lib/beyond-heroes
id -u beyond-heroes >/dev/null 2>&1 || useradd --system --home-dir "$STATE" --shell /usr/sbin/nologin beyond-heroes
install -d -m 0755 "$ROOT" "$ROOT/releases" /etc/beyond-heroes /opt/godot
install -d -m 0700 -o beyond-heroes -g beyond-heroes "$STATE" "$STATE/home"

# Godot headless, from a file the administrator downloaded and checked
if [ ! -x /opt/godot/godot ]; then
    [ -f "$GODOT_ZIP" ] && [ -n "$GODOT_SHA512" ] || { echo "Provide --godot-zip and --godot-sha512 (download from godotengine.org, version 4.7.2)."; exit 1; }
    echo "$GODOT_SHA512  $GODOT_ZIP" | sha512sum -c -
    unzip -o -j "$GODOT_ZIP" -d /opt/godot >/dev/null
    mv /opt/godot/Godot_v4.7.2-stable_linux.x86_64 /opt/godot/godot
    chmod 0755 /opt/godot/godot
fi
[ "$(/opt/godot/godot --version | cut -d. -f1-3)" = "4.7.2" ] || { echo "Godot must be 4.7.2: got $(/opt/godot/godot --version)"; exit 1; }

# the release: a copy of this checkout (no .git, no private data), pinned dependencies, imported project
DEST="$ROOT/releases/$RELEASE_ID"
if [ ! -d "$DEST" ]; then
    install -d -o beyond-heroes -g beyond-heroes "$DEST"
    tar --exclude=.git --exclude='server/data' --exclude='output' --exclude='build' --exclude='work' --exclude='references' --exclude='audio/source' -cf - . | tar -xf - -C "$DEST"
    chown -R beyond-heroes:beyond-heroes "$DEST"
    sudo -u beyond-heroes python3 -m venv "$DEST/.venv"
    sudo -u beyond-heroes "$DEST/.venv/bin/pip" install --no-cache-dir -r "$DEST/server/requirements.lock"
    sudo -u beyond-heroes env HOME="$STATE/home" /opt/godot/godot --headless --path "$DEST/game" --import >/dev/null 2>&1 || true
    [ -f "$DEST/game/.godot/global_script_class_cache.cfg" ] || { echo "The Godot project import failed; run it by hand to see the error."; exit 1; }
fi
ln -sfn "$DEST" "$ROOT/current"

# identity and configuration: created once, never replaced
if [ ! -f "$STATE/server.json" ]; then
    sudo -u beyond-heroes "$ROOT/current/.venv/bin/python" -m server.setup_server --public-host "$PUBLIC_HOST" --data-dir "$STATE" --game-port "$GAME_PORT" --api-port "$API_PORT"
    install -m 0644 "$STATE/upstream.crt" /etc/beyond-heroes/upstream.crt
fi
PROTOCOL="$(grep -m1 '^PROTOCOL' "$ROOT/current/server/service.py" | grep -o '[0-9]*')"
cat > /etc/beyond-heroes/build.env <<EOF
BH_BUILD=$RELEASE_ID
BH_PROTOCOL=$PROTOCOL
BH_PUBLIC_URL=https://$PUBLIC_HOST
EOF

# units, journal limits, firewall hint, Caddy
install -m 0644 "$ROOT/current/server/deploy/"beyond-heroes*.service "$ROOT/current/server/deploy/"beyond-heroes*.timer /etc/systemd/system/
install -d /etc/systemd/journald.conf.d
install -m 0644 "$ROOT/current/server/deploy/journald-beyond-heroes.conf" /etc/systemd/journald.conf.d/beyond-heroes.conf
chmod 0755 "$ROOT/current/server/deploy/"*.sh
systemd-analyze verify /etc/systemd/system/beyond-heroes.service
if [ ! -f /etc/caddy/Caddyfile.beyond-heroes-installed ]; then
    [ -f /etc/caddy/Caddyfile ] && cp -n /etc/caddy/Caddyfile /etc/caddy/Caddyfile.before-beyond-heroes
    sed "s/game.example.com/$PUBLIC_HOST/g" "$ROOT/current/server/deploy/Caddyfile.example" > /etc/caddy/Caddyfile
    touch /etc/caddy/Caddyfile.beyond-heroes-installed
    mkdir -p /var/log/caddy && chown caddy:caddy /var/log/caddy 2>/dev/null || true
    caddy validate --config /etc/caddy/Caddyfile
fi
systemctl daemon-reload
systemctl restart systemd-journald
systemctl enable --now beyond-heroes.service beyond-heroes-backup.timer beyond-heroes-health.timer
systemctl reload-or-restart caddy

echo
echo "Installed release $RELEASE_ID. Next, from a DIFFERENT network:"
echo "  1. open https://$PUBLIC_HOST/health  -> protocol $PROTOCOL, game_online true, a valid certificate"
echo "  2. open UDP $GAME_PORT in the cloud firewall and run the two-client connection test in deploy/README.md"
echo "Copy $STATE/official.cfg to game/server/official.cfg before exporting the client build."
