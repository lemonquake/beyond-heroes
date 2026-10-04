"""Health check for monitoring and systemd timers. Exit 0 healthy, 1 unhealthy, 2 warning only.

    python -m server.healthcheck --url https://game.example.com --expect-protocol 20
    python -m server.healthcheck --config /var/lib/beyond-heroes/server.json      # local: loopback URL and certificate

Checks (all with normal certificate verification for a public URL):
  * the account service answers /health over HTTPS and the certificate is valid for at least --warn-days more days
  * the protocol matches what this release's game clients speak
  * the game coordinator has reported in (game_online) -- the UDP side is alive from the service's point of view
  * with --config, the loopback certificate the coordinator trusts is not about to expire
UDP reachability from the internet cannot be proven from the VM itself; verify it from another network (see deploy/README.md).
"""
import argparse
import json
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def days_left(host: str, port: int, context: ssl.SSLContext) -> float:
    with socket.create_connection((host, port), timeout=8) as raw, context.wrap_socket(raw, server_hostname=host) as tls:
        expires = ssl.cert_time_to_seconds(tls.getpeercert()["notAfter"])
    return (expires - datetime.now(timezone.utc).timestamp()) / 86400


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="public account address, e.g. https://game.example.com")
    parser.add_argument("--config", type=Path, help="server.json of a local setup (checks the loopback address and its certificate)")
    parser.add_argument("--expect-protocol", type=int, default=20)
    parser.add_argument("--warn-days", type=float, default=14.0, help="warn when a certificate expires sooner than this")
    args = parser.parse_args(argv)
    if not args.url and not args.config:
        parser.error("give --url or --config")
    problems, warnings = [], []
    context = ssl.create_default_context()
    url = args.url
    if args.config:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        context = ssl.create_default_context(cafile=config["certificate"])
        url = url or "https://127.0.0.1:%d" % config.get("api_port", 8443)
        try:
            left = days_left("127.0.0.1", config.get("api_port", 8443), context)
            if left < 60:
                warnings.append(f"the loopback certificate expires in {left:.0f} days; run `python -m server.setup_server --rotate`")
        except (OSError, ssl.SSLError, KeyError, ValueError):
            pass          # the account service being down is reported below
    parts = urllib.parse.urlsplit(url)
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health", context=context, timeout=10) as response:
            health = json.load(response)
    except ssl.SSLError as error:
        problems.append(f"certificate problem: {error}")
        health = {}
    except (urllib.error.URLError, OSError, ValueError) as error:
        problems.append(f"the account service did not answer: {getattr(error, 'reason', error)}")
        health = {}
    if health:
        if health.get("protocol") != args.expect_protocol:
            problems.append(f"protocol {health.get('protocol')} but clients speak {args.expect_protocol}")
        if not health.get("game_online"):
            problems.append("the game coordinator is offline (no heartbeat)")
        print(f"version {health.get('version')} protocol {health.get('protocol')} players {health.get('players')}/{health.get('max_players')}")
    if args.url and not args.config and parts.hostname:
        try:
            left = days_left(parts.hostname, parts.port or 443, context)
            print(f"certificate valid for {left:.0f} more days")
            if left < args.warn_days:
                warnings.append(f"the public certificate expires in {left:.0f} days; check Caddy's renewal")
        except (OSError, ssl.SSLError, KeyError, ValueError) as error:
            problems.append(f"could not read the certificate: {error}")
    for line in warnings:
        print("WARNING:", line)
    for line in problems:
        print("PROBLEM:", line)
    if problems:
        return 1
    print("healthy" + (" (with warnings)" if warnings else ""))
    return 2 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
