# Off-PC hosting draft

This package is prepared for a Linux VM with public IPv4 and UDP support. It has not been installed or verified on Linux for this request. The local server remains on the user's PC. Claude should review the lifecycle and rate-limit issues below before community use.

## Host and network

Start with a Singapore VM, 2 GB RAM and 1-2 vCPUs, then size from representative load. DigitalOcean currently lists US$12/month for 2 GB/1 vCPU and US$18/month for 2 GB/2 vCPUs: [official pricing](https://www.digitalocean.com/pricing/droplets). Domain registration, backups and other extras are separate choices. No cloud purchase has been made.

Use a DNS-only public hostname that resolves directly to the VM. The account API uses public HTTPS TCP 443 through Caddy. Game traffic uses UDP 24680 directly; ordinary HTTP proxies/tunnels cannot carry ENet. TCP 80 supports certificate issuance/redirects. Keep TCP 8443 bound to loopback. Limit administrative access to the administrator's chosen route. These instructions apply to the new VM; they do not change the current PC's firewall or network settings.

## Connection design

The existing Godot coordinator connects to `https://127.0.0.1:8443` and verifies the configured local certificate. Keep that self-signed loopback certificate with localhost/127.0.0.1 SANs. Caddy serves the public hostname using its managed public certificate, then verifies the private upstream with the public part of that local certificate. This avoids replacing the coordinator's loopback identity with a public-domain certificate.

`Caddyfile.example` blocks public `/internal` routes and removes incoming `X-Server-Key` headers. `official.cfg.example` uses normal public certificate trust for clients. The TLS trust-pool and server-name settings follow [Caddy's reverse proxy reference](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy). Public DNS/port prerequisites and renewal follow [automatic HTTPS documentation](https://caddyserver.com/docs/automatic-https).

## Prepare a fresh server

1. Obtain the user's chosen VM/hostname and confirm its actual cost before provisioning. Install Python 3.12+, matching Godot 4.7.2 for the VM architecture, and current Caddy from their official distributions.
2. Create a service user `beyond-heroes` with its home/data directory at `/var/lib/beyond-heroes`. Install a reviewed revision in `/opt/beyond-heroes/releases/<commit>` and point `/opt/beyond-heroes/current` to it. Preserve this path and service ownership when updating.
3. Create `.venv` in the release, install `server/requirements.txt`, and save the resolved dependency versions. Import the Godot project on Linux under the service user's identity before startup; Windows import caches are not a substitute. Confirm the engine can load the project headlessly.
4. On this fresh VM checkout only, run `server.setup_server` with the real public hostname. Never run it again in the configured PC checkout or over an existing server identity. Transfer the newly generated configuration/certificate/key to the persistent data directory, update their absolute paths, and set `bind` to `127.0.0.1`. Set `game_host` to the directly reachable VM hostname and `game_port` to 24680.
5. Keep `server.json`, the TLS private key, SQLite database, WAL files and backups accessible only to the service identity. Copy only the public upstream certificate to `/etc/beyond-heroes/upstream.crt` for Caddy. Do not give Caddy the private key or internal server key.
6. Replace placeholder paths/hostname in the examples. Validate with `systemd-analyze verify` and `caddy validate` on the actual host. Install/enable the service and Caddy only after these checks. Review/restrict journal retention on the VM and preserve Caddy's certificate storage.
7. Build clients with the public `official.cfg`, keeping `certificate=""`. Existing testers who saved a different endpoint need to select the new hostname and clear the old certificate path in Server Settings. Do not replace an intentionally selected custom server without explanation.

## Verification before publishing the address

- HTTPS health reports protocol 16 and game_online=true with normal certificate validation.
- Public `/internal/start` and the other internal routes return 404; TCP 8443 is not publicly reachable.
- Two independent internet clients register/join, exchange gameplay and resume confirmed progress. Check actual UDP connectivity from another network, not only HTTP health on the VM.
- Repeat the twelve-client probe with test data, inspect script errors, then exercise disconnects/restarts and map-owner handoffs interactively.
- Reboot the VM and verify both services recover. Deliberately stop each child in a staging test and verify the parent/restart behavior.
- Produce a verified SQLite backup with the application's backup command, restore it into a separate staging directory, check integrity and character/trade state, then test reconnect.
- Verify certificate renewal, bounded disk/log growth and client version rejection.

## Known implementation gaps

The supervisor uses `Restart=always` because `server.run_server` currently returns zero after a child stops. SIGINT allows the Python parent to reach its existing backup/cleanup path. A child shutdown timeout can still skip later cleanup; fix and test that path before declaring supervised shutdown reliable.

The reverse proxy causes the account service to see loopback as the source IP. Its per-account/user limits remain, but IP rate limits become shared. Claude should add explicit trusted-proxy handling with a configured loopback trust boundary, or validate an equivalent proxy-side limit. Never trust arbitrary client-supplied forwarding headers.

Current automatic backups run every fifteen minutes and retain fourteen files on the same machine. That is a short recovery window, not off-site protection. Choose an authorized off-VM backup destination and longer retention, then test restoration before opening community access.

Combat remains client simulated. Hosting this package elsewhere does not establish cheat-resistant gameplay or persistent world simulation.

## Update, rollback and existing data

Keep the private data directory outside versioned releases. Before an update, announce a maintenance window, wait for confirmed saves, stop the supervised service, verify a backup, install the reviewed revision, update the `current` link and restart. Check health and two-client behavior before reopening testing. Roll back code only if the old revision supports the current database schema; otherwise restore the corresponding verified backup into staging first.

The current PC's player database has not been copied or migrated. Any migration needs the actual destination, a private transfer path and a staging restore check. Keep the PC's source data intact until that succeeds. No private data belongs in Git, public downloads or screenshots.
