# Hosting the official server on a Linux VM

> **On a free VPS (Oracle Always Free, Google e2-micro)** use the packaged route instead of installing from a checkout:
> `python tools/export_server.py` on the PC, then `sudo ./server/deploy/free-vps.sh` on the VM. Step by step:
> [docs/FREE_VPS_HOSTING.md](../../docs/FREE_VPS_HOSTING.md). It runs the exported dedicated-server build (no Godot editor,
> no project import on the VM) and installs the same units, Caddyfile, data layout and backups described below.

This package runs the account service and the game coordinator on one public Linux VM. **It has not been installed on a real VM
yet**: no cloud account, hostname or budget has been supplied, and no Linux machine was available while it was written. What was
verified is listed under "Verified so far"; everything in "Verify on the VM" still has to be done and recorded.

## What the owner has to provide

| Needed | Why |
| --- | --- |
| Provider, region and monthly budget approval | Nothing is bought without it. Singapore, 2 GB RAM, 1–2 vCPU is the starting guess. |
| A host name (for example `play.example.com`) with an A record pointing at the VM | Caddy obtains the normal public certificate for it. Use DNS only: no proxy in front, UDP must reach the VM directly. |
| SSH access to the VM | To run `install.sh` and later `update.sh`. |
| The Godot 4.7.2 Linux zip and its SHA-512 from godotengine.org | `install.sh` refuses an unchecked binary. |
| An off-VM backup destination (rclone remote or an rsync target) | Backups on the VM only protect against mistakes, not against losing the VM. |

## Network

| Port | Protocol | Open to | Used for |
| --- | --- | --- | --- |
| 24680 | UDP | everyone | the game (ENet). Plain HTTP proxies and tunnels cannot carry it. |
| 443 | TCP | everyone | accounts and saves, through Caddy |
| 80 | TCP | everyone | Caddy's certificate issuance and redirect |
| 22 | TCP | the administrator only | SSH |
| 8443 | TCP | **nobody** | the account service listens on `127.0.0.1` only |

## Layout

```
/opt/beyond-heroes/releases/<commit>/   code, its own .venv with pinned dependencies, imported Godot project (read only at run time)
/opt/beyond-heroes/current              symlink to the serving release
/opt/godot/godot                        Godot 4.7.2 headless, checked against its published SHA-512
/var/lib/beyond-heroes/                 ALL player data and secrets; owned by the service user, mode 0700
    server.json (0600)                  full configuration: TLS private key path, internal key, ports, trusted proxy
    coordinator.json (0600)             what the game coordinator is given: loopback certificate and internal key, never the TLS private key
    server.key (0600) server.crt        the loopback certificate pair (self-signed, 730 days)
    upstream.crt, official.cfg          public only: the first for Caddy, the second for client builds
    beyond_heroes.sqlite3 (+ -wal)      accounts, characters, leases
    backups/                            verified SQLite backups (every 15 min recent, one per day for 30 days)
/etc/beyond-heroes/build.env            release id, protocol, public URL (no secrets)
/etc/caddy/Caddyfile                    public TLS, blocks /internal, one forwarded address per request, bounded access log
```

Two certificates, on purpose. Players see Caddy's public certificate (normal trust, renewed automatically by Caddy). The account
service and the coordinator talk to each other on `127.0.0.1` with a private self-signed certificate that only they and Caddy
trust; a public-name certificate would never match the loopback address, and turning verification off is not an option.

Secrets: the internal key lives in `server.json` and `coordinator.json` only. Caddy removes any `X-Server-Key` header and the
service refuses internal routes for anything that came through the proxy, so it cannot be used from the internet even if guessed.
Nothing under `/var/lib/beyond-heroes` goes into Git, a client build, a screenshot or a bug report.

## Install

```bash
git clone <repository> && cd beyond-heroes && git checkout <reviewed commit>
sudo ./server/deploy/install.sh --public-host play.example.com \
     --godot-zip ~/Godot_v4.7.2-stable_linux.x86_64.zip --godot-sha512 <hash>
```

The script is repeatable: it never replaces an existing configuration, certificate or database. It creates the service user,
installs the release with `server/requirements.lock`, imports the Godot project as the service user, runs
`setup_server --public-host`, installs and verifies the systemd units, writes the Caddyfile (keeping a copy of any existing one),
limits the journal, and starts everything on boot.

Then build the client: copy `/var/lib/beyond-heroes/official.cfg` to `game/server/official.cfg` (it holds only the URL; the
certificate field stays empty) and export. Players using an older build that saved another server in Server Settings must pick
the new address there.

## Operations

| Task | Command |
| --- | --- |
| State, logs | `systemctl status beyond-heroes`, `journalctl -u beyond-heroes -f` |
| Health (public) | `python -m server.healthcheck --url https://play.example.com` (also runs every 2 minutes as `beyond-heroes-health.timer`; a failing check marks the unit failed: `systemctl --failed`) |
| Manual backup | `sudo -u beyond-heroes /opt/beyond-heroes/current/.venv/bin/python -m server.maintenance backup --config /var/lib/beyond-heroes/server.json` |
| Check a backup | `python -m server.maintenance verify FILE` |
| Restore drill (safe, any time) | `python -m server.deploy.restore_drill` |
| Restore into staging | `python -m server.maintenance restore FILE --into /tmp/staging` |
| Restore for real | `systemctl stop beyond-heroes`, then `python -m server.maintenance restore FILE --replace --config /var/lib/beyond-heroes/server.json --yes`, then start. The old database is kept in `before-restore-<time>/`. |
| Update | `sudo ./server/deploy/update.sh` from a checkout of the new reviewed commit |
| Roll back | `sudo ./server/deploy/update.sh --rollback` |
| Rotate the loopback certificate (yearly) | `python -m server.setup_server --rotate --data-dir /var/lib/beyond-heroes`, copy `upstream.crt` to `/etc/beyond-heroes/`, restart both |

Backups: the service saves one on every start and stop and every 15 minutes while running (newest 16 plus one per UTC day for
30 days, so disk use is bounded), and the daily timer takes another and, when `/etc/beyond-heroes/offsite.env` names a destination,
copies the newest verified one off the VM. Logs go to the journal only, capped by `journald-beyond-heroes.conf`; Caddy's access log
rolls at 10 MB and keeps five files.

Updates: announce a window, wait for saves to go idle, then run `update.sh`. It takes a verified backup, stages the new release
beside the old, refuses a release that cannot read the current database, stops, switches, starts, waits for a healthy answer and
switches back by itself if there is none. Data is never inside a release. The service and the game must agree on the protocol
number (`PROTOCOL` in `server/service.py` and `game/src/net/net.gd`, shown by `/health` and on the game's title screen as "online
version"). The game tells a player whether their game or the server is the older one. Roll back code only when the older release
understands the database; otherwise restore the matching backup into staging first.

Shutdown: `systemctl stop` sends SIGTERM to `run_server`, which stops the coordinator, lets the account service finish requests
and write a backup, and kills anything that takes longer than 20 seconds. If either child dies, `run_server` stops the other and
exits non-zero, and systemd restarts the pair (`Restart=on-failure`, at most five times in five minutes).

## Verified so far (on the development PC, Windows)

* `python -m unittest server.test_service server.test_hardening`: database invariants, HTTP boundary (oversize, malformed JSON,
  wrong content type, `X-Forwarded-For` trusted only from the proxy, internal routes unreachable through the proxy), pruning,
  backup/verify/restore (including damaged and foreign files and a busy database), runner failure and stop-file shutdown.
* `python -m server.deploy.restore_drill`: backup, restore into staging, second service signs the account in and lists the character.
* `python -m server.integration_probe`: real HTTPS + ENet clients, twelve players and a refused thirteenth, restart and resume,
  atomic trade, custom room, map-owner hand-off, separate maps, dropped connection and reload, malformed and flooding input.
  Each stage also fails if a process log contains a script or engine error.
* Shell scripts parse (`bash -n`).

## Verify on the VM (not done)

- [ ] `systemd-analyze verify /etc/systemd/system/beyond-heroes.service`, `caddy validate`
- [ ] `https://HOST/health` from another network: valid public certificate, protocol 19, `game_online: true`
- [ ] `https://HOST/internal/start` returns 404; `nc -vz HOST 8443` fails from outside
- [ ] Two game clients on **different networks** join the server over UDP 24680, see each other and trade; one on mobile data
- [ ] `python -m server.integration_probe` against the VM with test accounts, then the log scan is clean
- [ ] `systemctl stop beyond-heroes` returns within the time-out and writes a backup; `kill -9` of the coordinator and of the account service each bring the pair back
- [ ] Reboot the VM: both services and Caddy return by themselves
- [ ] Restore drill on the VM, then a restore of the newest real backup into staging
- [ ] `update.sh` to a second commit and `--rollback`
- [ ] Certificate renewal: `caddy` log shows the issuance; `healthcheck` reports the days left
- [ ] Journal size stays under its cap after a day of use; Caddy log rotates
- [ ] Godot's headless run on Linux with a read-only project directory: confirm it does not need to write inside the release

## Known limits

* Combat and rewards are simulated by players' game clients. Hosting elsewhere does not change that; see
  `docs/OFFICIAL_SERVER.md`, "What the server decides".
* The Windows PC server (this repository's `Start Official Server.cmd`) keeps working unchanged. Nothing here copies or migrates
  its player database; any migration needs the destination, a private transfer path and a staging restore first.
* Public IP rate limits depend on Caddy passing exactly one forwarded address (`header_up X-Forwarded-For {remote_host}`); keep that
  line when editing the Caddyfile.
