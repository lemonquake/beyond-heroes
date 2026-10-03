# Hosting the official server on a free VPS

This is the repository's implementation of [SERVER.md](SERVER.md): a **headless dedicated server build** on an always-free
cloud VM, kept running 24/7 by **systemd**, with the account service's HTTPS behind **Caddy** and the game on **UDP 24680**.
Everything below runs from two scripts:

| Where | Command | What it does |
| --- | --- | --- |
| This PC | `python tools/export_server.py` | Exports the dedicated-server builds (visuals stripped) and packs each with the account service |
| The VM | `sudo ./server/deploy/free-vps.sh` | Installs, configures, firewalls, starts and health-checks the server |
| This PC | `python tools/set_official_server.py --url https://<host>` | Points the game builds at the VM, then export the clients |

What the server does and does not decide (combat is still simulated by players' games) is unchanged by where it runs:
read "What the server decides" in [OFFICIAL_SERVER.md](OFFICIAL_SERVER.md) before inviting anyone you do not trust.

## 1. Choose a free VM

| Provider (always free) | Shape | Package to upload | Notes |
| --- | --- | --- | --- |
| **Oracle Cloud** (recommended) | `VM.Standard.A1.Flex`, Ampere ARM: up to 4 OCPU / 24 GB free. 1 OCPU / 6 GB is plenty | `linux-arm64` | Image **Ubuntu 24.04** (aarch64). Its iptables blocks new ports: the script opens them |
| **Google Cloud** | `e2-micro` in `us-west1`, `us-central1` or `us-east1`, 30 GB standard disk | `linux-x86_64` | 1 GB of memory: the script adds 2 GB of swap. Twelve busy players may be too much for it |
| Any other VPS | Ubuntu 24.04, 1 vCPU, 1 GB or more | match its CPU | Static public IPv4 needed; UDP must reach the VM (no proxy/CDN in front) |

Create the VM with your SSH key and a **public IPv4 address**. On Oracle, reserve the public IP (Networking > IP
Management > Reserved Public IPs) so it survives a stop/start; on Google, promote the external IP to static.

## 2. Open the provider's firewall (web console)

The VM's own firewall is handled by the script; the provider's cloud firewall is not reachable from inside the VM:

* **Oracle**: Networking > Virtual Cloud Networks > (your VCN) > Security Lists > Default Security List > **Add Ingress
  Rules**: source `0.0.0.0/0`, **TCP**, destination port range `80,443`; and source `0.0.0.0/0`, **UDP**, port `24680`.
* **Google**: VPC network > Firewall > **Create firewall rule**: direction ingress, targets *All instances in the network*,
  source `0.0.0.0/0`, TCP `80,443` and UDP `24680`.

Port 8443 (the account service) must **not** be opened: it listens on `127.0.0.1` only, Caddy forwards to it.

## 3. A name for the server (pick one)

The game only talks HTTPS with a certificate it can verify, so the server needs a DNS name:

* **Nothing to do**: the script uses `<your-ip-with-dashes>.sslip.io` (for 203.0.113.7: `203-0-113-7.sslip.io`), a free
  wildcard DNS that answers with the IP in the name. No account, no domain. Certificates for sslip.io names share a
  public rate limit, so if issuance ever fails, wait an hour or use one of the options below.
* **Free name you control**: create a subdomain at [duckdns.org](https://www.duckdns.org) and pass
  `--duckdns mygame --duckdns-token <token>`; the VM keeps the record pointed at itself every 5 minutes.
* **Your own domain**: add an A record to the VM's IP and pass `--host play.example.com`.

## 4. Build the package on this PC

```powershell
python tools/export_server.py --arch arm64          # Oracle (or --arch x86_64 for Google; default builds all three)
```

The packages land in `build/server/` (`beyond-heroes-server-<commit>-linux-arm64.tar.gz`, about 120 MB). They contain
the stripped server build, the `server/` Python package and these instructions, and **no** player data or secrets.
Godot's 4.7.2 export templates must be installed (they are on this PC).

## 5. Install on the VM

```bash
scp build/server/beyond-heroes-server-*-linux-arm64.tar.gz ubuntu@<vm-ip>:~
ssh ubuntu@<vm-ip>
mkdir bh && tar -xzf beyond-heroes-server-*-linux-arm64.tar.gz -C bh && cd bh
sudo ./server/deploy/free-vps.sh            # or --duckdns NAME --duckdns-token TOKEN, or --host your.domain
```

The script is safe to run again. It:

1. installs Python 3.12 (deadsnakes on older Ubuntu) and Caddy from Caddy's official repository;
2. adds a 2 GB swap file on VMs with less than 2 GB of memory and caps the service at 85 % of memory;
3. opens TCP 80/443 and UDP 24680 in the VM's firewall: `ufw` when active, and on Oracle images inserts `iptables`
   ACCEPT rules above the image's REJECT rule and saves them with `iptables-persistent`;
4. creates the `beyond-heroes` system user, installs the release into `/opt/beyond-heroes/releases/<commit>` with a
   pinned virtual environment, and points `/opt/beyond-heroes/current` at it;
5. creates the server identity once in `/var/lib/beyond-heroes` (mode 0700): configuration, internal key, loopback
   certificate, the database. It never replaces them on a re-run;
6. installs the systemd units (`beyond-heroes`, verified backups every day, a health check every 2 minutes, the journal
   cap), writes the Caddyfile for the name and starts everything on boot;
7. waits until `https://<name>/health` answers with a valid certificate, the right protocol and the coordinator online,
   and prints the result, the firewall reminder and the client step.

## 6. Point the game at it

```powershell
python tools/set_official_server.py --url https://203-0-113-7.sslip.io
python tools/export_builds.py --godot "C:\Users\Lemon PC\Desktop\Godot.exe" --label vps
```

Share the new Windows and Android builds. Players with an older build can type the address in **Server Settings**
(no certificate file: the VM's certificate is a normal public one). Game and server must have the same protocol number
(18 since bh-034); the title screen shows the server's version.

## Day to day

| Task | Command (on the VM) |
| --- | --- |
| Status, URL, recent log | `sudo ./server/deploy/free-vps.sh --status` |
| Live log | `journalctl -u beyond-heroes -f` |
| Health from anywhere | `python -m server.healthcheck --url https://<name>` |
| Update to a new package | unpack it, then `sudo ./server/deploy/free-vps.sh --update` (backup, database check, switch, health check, automatic rollback) |
| Roll back | `sudo ./server/deploy/free-vps.sh --rollback` |
| Manual backup | `sudo -u beyond-heroes /opt/beyond-heroes/current/.venv/bin/python -m server.maintenance backup --config /var/lib/beyond-heroes/server.json` (run from `/opt/beyond-heroes/current`) |
| Off-VM backups | create `/etc/beyond-heroes/offsite.env` (see `server/deploy/backup-offsite.sh`); copy backups off the VM: a free VM can be reclaimed |
| Restart | `sudo systemctl restart beyond-heroes` |

Operations, restore and rotation are the same as the general Linux guide, [server/deploy/README.md](../server/deploy/README.md).

## Moving the PC server's players to the VM

The Windows PC server's database is not copied automatically. To move it: stop the PC server (Stop Official Server.cmd
writes a final backup), copy the newest verified backup from `server/data/backups` to the VM privately (`scp`), stop the
VM service, and restore it with `python -m server.maintenance restore FILE --replace --config /var/lib/beyond-heroes/server.json --yes`.
Accounts, passwords and characters come along; players then sign in to the new address.

## What was verified, and what was not

Verified on the development PC (Windows), 3 October 2026:

* `tools/export_server.py` exports the stripped dedicated-server build (232 MB with the engine, about 120 MB packed;
  the full game is over 600 MB of imported assets).
* That exported build ran as the coordinator in the real end-to-end test, `python -m server.integration_probe
  --coordinator build/server/windows/beyond_heroes_server.exe`: twelve HTTPS/ENet clients, a thirteenth refused,
  restart and resume, shared avatars, an atomic trade, confirmed exit saves, a custom room, map hand-off, reconnect,
  protocol refusal and hostile input: all eight stages passed their checks. The probe's strict log scan flagged engine
  exit messages of the client processes ("resources still in use at exit") and a rare ENet "Unable to send packet" when a
  refused client leaves; a run with the editor as coordinator flagged the same kind of lines, so they are not caused by
  the export (run with `--allow-log-errors` to see the functional result).
* `free-vps.sh` parses (`bash -n`).

Not verified (no cloud account or Linux machine was available in this session): running `free-vps.sh` on a real
Oracle or Google VM, the Linux arm64/x86_64 builds themselves, certificate issuance for the chosen name, and players
on other networks reaching UDP 24680. Do the checklist in [server/deploy/README.md](../server/deploy/README.md),
"Verify on the VM", on the first install.
