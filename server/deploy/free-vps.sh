#!/bin/bash
# Beyond Heroes official server on a free Linux VPS, in one command (docs/FREE_VPS_HOSTING.md).
#
# Upload a server package made on the development PC (python tools/export_server.py), unpack it on the VM and run, as root:
#
#   sudo ./server/deploy/free-vps.sh                          # a free name from the VM's public IP (<ip>.sslip.io)
#   sudo ./server/deploy/free-vps.sh --host play.example.com  # your own DNS name (A record -> this VM)
#   sudo ./server/deploy/free-vps.sh --duckdns mygame --duckdns-token <token>   # a free mygame.duckdns.org
#
#   sudo ./server/deploy/free-vps.sh --update    # from a newer unpacked package: backup, switch, health check, auto rollback
#   sudo ./server/deploy/free-vps.sh --rollback  # back to the previous release
#   sudo ./server/deploy/free-vps.sh --status    # what is running, the public URL and the last log lines
#
# It installs what the server needs (Python 3.12, Caddy for the public HTTPS certificate), adds swap on small VMs (the
# 1 GB Google e2-micro), opens TCP 80/443 and UDP 24680 in the VM's own firewall (Oracle images block them with
# iptables), creates the beyond-heroes service user, installs this release under /opt/beyond-heroes/releases/<id>,
# creates the server identity once (never replaced), and starts everything with systemd so it survives reboots.
# The provider's cloud firewall (Oracle security list, Google VPC firewall rule) must be opened in its web console:
# the script prints exactly what to add.
#
# Player data and secrets live only in /var/lib/beyond-heroes (mode 0700); a release never contains any.
set -euo pipefail

HOST="" DUCK="" DUCK_TOKEN="" GAME_PORT=24680 API_PORT=8443 MODE=install SWAP=auto
while [ $# -gt 0 ]; do
    case "$1" in
        --host) HOST="$2"; shift 2 ;;
        --duckdns) DUCK="$2"; shift 2 ;;
        --duckdns-token) DUCK_TOKEN="$2"; shift 2 ;;
        --game-port) GAME_PORT="$2"; shift 2 ;;
        --no-swap) SWAP=no; shift ;;
        --update) MODE=update; shift ;;
        --rollback) MODE=rollback; shift ;;
        --status) MODE=status; shift ;;
        -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
        *) echo "Unknown option $1 (see --help)"; exit 2 ;;
    esac
done

ROOT=/opt/beyond-heroes
STATE=/var/lib/beyond-heroes
ETC=/etc/beyond-heroes
PKG="$(cd "$(dirname "$0")/../.." && pwd)"
BIN=beyond_heroes_server
say() { printf '\n\033[1;33m== %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" = 0 ] || die "Run as root: sudo $0 $*"

status() {
    systemctl --no-pager status beyond-heroes.service caddy.service | sed -n '1,12p' || true
    [ -r "$ETC/build.env" ] && cat "$ETC/build.env"
    journalctl -u beyond-heroes --no-pager -n 20 || true
}
[ "$MODE" = status ] && { status; exit 0; }

# --------------------------------------------------------------------------------------------------- release switching
protocol_of() { grep -m1 '^PROTOCOL' "$1/server/service.py" | grep -o '[0-9]*'; }
switch_to() {
    systemctl stop beyond-heroes.service || true
    ln -sfn "$1" "$ROOT/current"
    sed -i "s/^BH_BUILD=.*/BH_BUILD=$(basename "$1")/; s/^BH_PROTOCOL=.*/BH_PROTOCOL=$(protocol_of "$1")/" "$ETC/build.env"
    systemctl start beyond-heroes.service
}
healthy() {
    # shellcheck disable=SC1091
    set -a; . "$ETC/build.env"; set +a
    for _ in $(seq 1 45); do
        if "$ROOT/current/.venv/bin/python" -m server.healthcheck --url "$BH_PUBLIC_URL" --expect-protocol "$BH_PROTOCOL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 4
    done
    return 1
}
if [ "$MODE" = rollback ]; then
    CUR="$(readlink -f "$ROOT/current")"
    PREV="$(ls -1dt "$ROOT"/releases/*/ | sed 's:/$::' | grep -vx "$CUR" | head -n 1 || true)"
    [ -n "$PREV" ] || die "No earlier release to go back to."
    say "Rolling back $(basename "$CUR") -> $(basename "$PREV")"
    switch_to "$PREV"
    cd "$PREV" && healthy && echo "Rollback complete." || die "The previous release is not healthy either: journalctl -u beyond-heroes"
    exit 0
fi

# --------------------------------------------------------------------------------------------------- the package itself
[ -x "$PKG/bin/$BIN" ] && [ -f "$PKG/server/service.py" ] && [ -f "$PKG/RELEASE" ] \
    || die "Run this from an unpacked server package (bin/$BIN, server/, RELEASE). Build one with tools/export_server.py."
RELEASE="$(tr -dc 'A-Za-z0-9._-' < "$PKG/RELEASE")"
# the build must match this machine: ELF e_machine 0x3e = x86_64, 0xb7 = aarch64
MACHINE="$(od -An -t x1 -j 18 -N 1 "$PKG/bin/$BIN" | tr -d ' ')"
case "$(uname -m)/$MACHINE" in
    x86_64/3e|aarch64/b7|arm64/b7) ;;
    *) die "This package was built for another CPU (binary e_machine 0x$MACHINE, this VM $(uname -m)). Use the linux-$( [ "$(uname -m)" = x86_64 ] && echo x86_64 || echo arm64) package." ;;
esac
. /etc/os-release
case "$ID" in ubuntu|debian) ;; *) die "Ubuntu 24.04 (recommended) or Debian is required; this is $PRETTY_NAME." ;; esac
export DEBIAN_FRONTEND=noninteractive

# --------------------------------------------------------------------------------------------------- update an install
if [ "$MODE" = update ]; then
    [ -L "$ROOT/current" ] && [ -f "$STATE/server.json" ] || die "No installation found; run without --update first."
    PREVIOUS="$(readlink -f "$ROOT/current")"
    DEST="$ROOT/releases/$RELEASE"
    [ "$DEST" != "$PREVIOUS" ] || { echo "Release $RELEASE is already serving."; exit 0; }
    say "Verified backup before the update"
    sudo -u beyond-heroes -H env HOME="$STATE/home" "$PREVIOUS/.venv/bin/python" -m server.maintenance backup --config "$STATE/server.json"
fi

# --------------------------------------------------------------------------------------------------- system packages
if [ "$MODE" = install ]; then
    say "System packages"
    apt-get update -qq
    apt-get install -y -qq python3 python3-venv curl ca-certificates gnupg >/dev/null
    apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https >/dev/null 2>&1 || true
fi
PY=python3
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
    if command -v python3.12 >/dev/null; then
        PY=python3.12
    elif [ "$ID" = ubuntu ]; then
        say "Python 3.12 (deadsnakes) - this Ubuntu ships an older Python"
        apt-get install -y -qq software-properties-common >/dev/null
        add-apt-repository -y ppa:deadsnakes/ppa >/dev/null
        apt-get update -qq
        apt-get install -y -qq python3.12 python3.12-venv >/dev/null
        PY=python3.12
    else
        die "Python 3.12 or newer is required. Use an Ubuntu 24.04 image."
    fi
fi

if [ "$MODE" = install ]; then
    if ! command -v caddy >/dev/null; then
        say "Caddy (public HTTPS certificate, renewed automatically)"
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
        apt-get update -qq
        apt-get install -y -qq caddy >/dev/null
    fi

    # ----------------------------------------------------------------------------------------------- memory
    MEM_MB=$(( $(awk '/MemTotal/{print $2}' /proc/meminfo) / 1024 ))
    if [ "$SWAP" = auto ] && [ "$MEM_MB" -lt 2048 ] && [ -z "$(swapon --show --noheadings)" ]; then
        say "Swap file (this VM has $MEM_MB MB of memory)"
        fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
        chmod 600 /swapfile
        mkswap /swapfile >/dev/null
        swapon /swapfile
        grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
        sysctl -q vm.swappiness=10
        echo 'vm.swappiness=10' > /etc/sysctl.d/90-beyond-heroes.conf
    fi

    # ----------------------------------------------------------------------------------------------- the public name
    PUBLIC_IP="$(curl -4 -fsS --max-time 10 https://api.ipify.org || curl -4 -fsS --max-time 10 https://ifconfig.me || true)"
    if [ -f "$ETC/build.env" ] && [ -z "$HOST" ] && [ -z "$DUCK" ]; then
        HOST="$(sed -n 's#^BH_PUBLIC_URL=https://##p' "$ETC/build.env")"     # a re-run keeps the name it already has
    fi
    if [ -n "$DUCK" ]; then
        [ -n "$DUCK_TOKEN" ] || die "--duckdns needs --duckdns-token (from duckdns.org after you sign in)."
        say "DuckDNS: $DUCK.duckdns.org -> this VM"
        install -d -m 0700 "$ETC"
        printf 'DUCK=%s\nDUCK_TOKEN=%s\n' "$DUCK" "$DUCK_TOKEN" > "$ETC/duckdns.env"
        chmod 0600 "$ETC/duckdns.env"
        curl -fsS "https://www.duckdns.org/update?domains=$DUCK&token=$DUCK_TOKEN&ip=" | grep -q OK || die "DuckDNS refused the update: check the name and token."
        HOST="$DUCK.duckdns.org"
        cat > /etc/systemd/system/beyond-heroes-duckdns.service <<UNIT
[Unit]
Description=Keep $HOST pointing at this VM
After=network-online.target
[Service]
Type=oneshot
EnvironmentFile=$ETC/duckdns.env
ExecStart=/bin/sh -c 'curl -fsS "https://www.duckdns.org/update?domains=\${DUCK}&token=\${DUCK_TOKEN}&ip=" | grep -q OK'
UNIT
        cat > /etc/systemd/system/beyond-heroes-duckdns.timer <<UNIT
[Unit]
Description=Refresh the DuckDNS address every 5 minutes
[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
UNIT
    fi
    if [ -z "$HOST" ]; then
        [ -n "$PUBLIC_IP" ] || die "Could not find this VM's public IPv4 address; pass --host or --duckdns."
        HOST="$(echo "$PUBLIC_IP" | tr . -).sslip.io"
        say "No --host given: using $HOST (sslip.io resolves it to $PUBLIC_IP)"
        echo "This works with no domain and no account. If the VM's public IP changes, run this script again."
    fi
    RESOLVED="$(getent ahostsv4 "$HOST" | awk 'NR==1{print $1}' || true)"
    if [ -n "$PUBLIC_IP" ] && [ "$RESOLVED" != "$PUBLIC_IP" ]; then
        echo "WARNING: $HOST resolves to '${RESOLVED:-nothing}', but this VM's public address is $PUBLIC_IP."
        echo "         The HTTPS certificate cannot be issued until the name points here (DNS can take a few minutes)."
    fi

    # ----------------------------------------------------------------------------------------------- the VM's firewall
    say "Opening TCP 80/443 and UDP $GAME_PORT in this VM's firewall"
    if command -v ufw >/dev/null && ufw status | grep -q 'Status: active'; then
        ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null; ufw allow "$GAME_PORT"/udp >/dev/null
        echo "ufw: allowed 80/tcp, 443/tcp, $GAME_PORT/udp"
    fi
    if iptables -S INPUT 2>/dev/null | grep -q -- '-j REJECT'; then
        # Oracle Cloud images end INPUT with a REJECT: the new rules must sit above it, and survive a reboot
        for rule in "tcp 80" "tcp 443" "udp $GAME_PORT"; do
            set -- $rule
            if ! iptables -C INPUT -p "$1" -m state --state NEW -m "$1" --dport "$2" -j ACCEPT 2>/dev/null; then
                LINE="$(iptables -L INPUT --line-numbers -n | awk '/REJECT/{print $1; exit}')"
                iptables -I INPUT "$LINE" -p "$1" -m state --state NEW -m "$1" --dport "$2" -j ACCEPT
            fi
        done
        if ! command -v netfilter-persistent >/dev/null; then
            echo "iptables-persistent iptables-persistent/autosave_v4 boolean true" | debconf-set-selections
            echo "iptables-persistent iptables-persistent/autosave_v6 boolean true" | debconf-set-selections
            apt-get install -y -qq iptables-persistent >/dev/null
        fi
        netfilter-persistent save >/dev/null
        echo "iptables: accepted 80/tcp, 443/tcp, $GAME_PORT/udp above the image's REJECT rule (saved)"
    fi
fi

# --------------------------------------------------------------------------------------------------- the release
say "Installing release $RELEASE"
id -u beyond-heroes >/dev/null 2>&1 || useradd --system --home-dir "$STATE" --shell /usr/sbin/nologin beyond-heroes
install -d -m 0755 "$ROOT" "$ROOT/releases" "$ETC"
install -d -m 0700 -o beyond-heroes -g beyond-heroes "$STATE" "$STATE/home"
DEST="$ROOT/releases/$RELEASE"
if [ ! -x "$DEST/.venv/bin/python" ]; then
    rm -rf "$DEST"
    install -d "$DEST"
    cp -a "$PKG/bin" "$PKG/server" "$PKG/RELEASE" "$DEST/"
    [ -f "$PKG/README-VPS.md" ] && cp "$PKG/README-VPS.md" "$DEST/"
    rm -rf "$DEST/server/data"
    "$PY" -m venv "$DEST/.venv"
    "$DEST/.venv/bin/pip" install --quiet --no-cache-dir -r "$DEST/server/requirements.lock"
    chown -R root:root "$DEST"
    chmod -R a+rX "$DEST"
    chmod 0755 "$DEST/bin/$BIN" "$DEST/server/deploy/"*.sh
fi

if [ "$MODE" = update ]; then
    # the new code must read the current database before it is allowed to serve
    (cd "$DEST" && sudo -u beyond-heroes -H env HOME="$STATE/home" "$DEST/.venv/bin/python" -m server.maintenance verify "$STATE/beyond_heroes.sqlite3" >/dev/null) \
        || die "Release $RELEASE cannot read the current database; nothing was changed."
    switch_to "$DEST"
    cd "$DEST"
    if healthy; then
        echo "Release $RELEASE is serving. Previous release kept for --rollback: $(basename "$PREVIOUS")"
        ls -1dt "$ROOT"/releases/*/ | tail -n +4 | xargs -r rm -rf
        exit 0
    fi
    echo "The new release did not become healthy; switching back to $(basename "$PREVIOUS")."
    switch_to "$PREVIOUS"
    cd "$PREVIOUS" && healthy && echo "Previous release restored." || echo "Previous release is also unhealthy: journalctl -u beyond-heroes"
    exit 1
fi
ln -sfn "$DEST" "$ROOT/current"

# --------------------------------------------------------------------------------------------------- identity (once)
if [ ! -f "$STATE/server.json" ]; then
    say "Server identity for $HOST (created once, never replaced)"
    (cd "$ROOT/current" && sudo -u beyond-heroes -H env HOME="$STATE/home" "$ROOT/current/.venv/bin/python" -m server.setup_server \
        --public-host "$HOST" --data-dir "$STATE" --game-port "$GAME_PORT" --api-port "$API_PORT")
fi
install -m 0644 "$STATE/upstream.crt" "$ETC/upstream.crt"
PROTOCOL="$(protocol_of "$ROOT/current")"
cat > "$ETC/build.env" <<ENV
BH_BUILD=$RELEASE
BH_PROTOCOL=$PROTOCOL
BH_PUBLIC_URL=https://$HOST
ENV

# --------------------------------------------------------------------------------------------------- services
say "systemd services and Caddy"
MEM_MB=$(( $(awk '/MemTotal/{print $2}' /proc/meminfo) / 1024 ))
MEMMAX=$(( MEM_MB * 85 / 100 )); [ "$MEMMAX" -gt 1536 ] && MEMMAX=1536
sed -e "s#^ExecStart=.*#ExecStart=$ROOT/current/.venv/bin/python -m server.run_server --stdio --exported --godot $ROOT/current/bin/$BIN --config $STATE/server.json#" \
    -e "s#^ReadOnlyPaths=.*#ReadOnlyPaths=$ROOT#" \
    -e "s#^MemoryMax=.*#MemoryMax=${MEMMAX}M#" \
    "$ROOT/current/server/deploy/beyond-heroes.service" > /etc/systemd/system/beyond-heroes.service
install -m 0644 "$ROOT/current/server/deploy/beyond-heroes-backup.service" "$ROOT/current/server/deploy/beyond-heroes-backup.timer" \
    "$ROOT/current/server/deploy/beyond-heroes-health.service" "$ROOT/current/server/deploy/beyond-heroes-health.timer" /etc/systemd/system/
install -d /etc/systemd/journald.conf.d
install -m 0644 "$ROOT/current/server/deploy/journald-beyond-heroes.conf" /etc/systemd/journald.conf.d/beyond-heroes.conf
systemd-analyze verify /etc/systemd/system/beyond-heroes.service 2>&1 | grep -v 'Unknown key\|is not executable' || true
[ -f /etc/caddy/Caddyfile ] && [ ! -f /etc/caddy/Caddyfile.before-beyond-heroes ] && cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.before-beyond-heroes
sed "s/game.example.com/$HOST/g" "$ROOT/current/server/deploy/Caddyfile.example" > /etc/caddy/Caddyfile
mkdir -p /var/log/caddy && chown caddy:caddy /var/log/caddy 2>/dev/null || true
caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 || die "The Caddyfile does not validate: caddy validate --config /etc/caddy/Caddyfile"
systemctl daemon-reload
systemctl restart systemd-journald
systemctl enable --now caddy.service >/dev/null 2>&1
systemctl reload-or-restart caddy
systemctl enable beyond-heroes.service beyond-heroes-backup.timer beyond-heroes-health.timer >/dev/null 2>&1
[ -f /etc/systemd/system/beyond-heroes-duckdns.timer ] && systemctl enable --now beyond-heroes-duckdns.timer >/dev/null 2>&1
systemctl restart beyond-heroes.service
systemctl start beyond-heroes-backup.timer beyond-heroes-health.timer

say "Waiting for https://$HOST (the first certificate can take a minute)"
cd "$ROOT/current"
if healthy; then
    OK=1
else
    OK=0
fi

cat <<DONE

==========================================================================================================
 Beyond Heroes official server, release $RELEASE, protocol $PROTOCOL
   Accounts and saves : https://$HOST          (TCP 443, Caddy; TCP 80 for the certificate)
   Game               : $HOST  UDP $GAME_PORT
   Data and secrets   : $STATE (back it up; never share it)
   Logs               : journalctl -u beyond-heroes -f        Status: sudo $0 --status
==========================================================================================================
DONE
if [ "$OK" = 1 ]; then
    echo "HEALTHY: the public URL answers with a valid certificate and the game coordinator is online."
else
    echo "NOT HEALTHY YET. The usual cause is the provider's cloud firewall (below), or DNS not pointing here yet."
    echo "Check again in a minute: sudo $0 --status ; python -m server.healthcheck --url https://$HOST"
fi
cat <<'FIREWALL'

The provider's own firewall must also allow these (in its web console; this script cannot change it):
  Oracle Cloud : Networking > Virtual Cloud Networks > your VCN > Security Lists > Default Security List >
                 Add Ingress Rules: source 0.0.0.0/0, TCP, destination ports 80,443 ; and source 0.0.0.0/0, UDP, port 24680
  Google Cloud : VPC network > Firewall > Create rule: ingress, targets "All instances", source 0.0.0.0/0,
                 TCP 80,443 and UDP 24680 (the "Allow HTTP/HTTPS traffic" boxes cover 80/443 only)
FIREWALL
cat <<CLIENT

Point the game at this server (on the development PC), then export the client builds:
  python tools/set_official_server.py --url https://$HOST
Players of an existing build can instead enter https://$HOST in Server Settings (no certificate file needed).
CLIENT
