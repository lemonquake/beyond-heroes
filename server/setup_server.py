"""Create local server configuration and the certificate the account service uses on its own loopback address.

PC / LAN (default):     python -m server.setup_server --host 192.168.1.20
Public Linux VM:        python -m server.setup_server --public-host game.example.com --data-dir /var/lib/beyond-heroes
Renew the loopback cert: python -m server.setup_server --rotate --data-dir /var/lib/beyond-heroes

PC mode writes a certificate clients must trust and copies it into game/server/ for the build. VM mode keeps everything in the
data directory: the service listens on 127.0.0.1 behind Caddy, which presents the normal public certificate to players, so no
certificate or key ever goes into a client build. Setup never overwrites an existing configuration.
"""
import argparse
import datetime
import ipaddress
import json
import os
import secrets
import socket
from pathlib import Path


def _write_private(path: Path, data: bytes) -> None:
    """Create a file readable only by its owner (never world-readable, even briefly)."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
    os.chmod(path, 0o600)


def make_identity(directory: Path, host: str, names: set, *, days=730):
    """Write server.key / server.crt: a self-signed certificate for the service's own loopback and listed names."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    alt = []
    for address in sorted(names):
        try:
            alt.append(x509.IPAddress(ipaddress.ip_address(address)))
        except ValueError:
            alt.append(x509.DNSName(address))
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - datetime.timedelta(minutes=10))
                   .not_valid_after(now + datetime.timedelta(days=days))
                   .add_extension(x509.SubjectAlternativeName(alt), critical=False)
                   .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                   .add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True,
                       content_commitment=False, data_encipherment=False, key_agreement=False,
                       key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
                   .sign(key, hashes.SHA256()))
    private_path, certificate_path = directory / "server.key", directory / "server.crt"
    _write_private(private_path, key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return private_path, certificate_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1", help="Address friends use to reach this PC")
    parser.add_argument("--public-host", help="Public host name of a Linux VM (VM mode: loopback service behind Caddy)")
    parser.add_argument("--data-dir", type=Path, help="Where configuration, certificate and database live (default: server/data)")
    parser.add_argument("--api-port", type=int, default=8443)
    parser.add_argument("--game-port", type=int, default=24680)
    parser.add_argument("--rotate", action="store_true", help="Replace the loopback certificate and key of an existing setup")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    directory = (args.data_dir or root / "server" / "data").resolve()
    config_path = directory / "server.json"
    vm = bool(args.public_host)
    if args.rotate:
        if not config_path.is_file():
            raise SystemExit("Nothing to rotate: no configuration in " + str(directory))
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("bind", "0.0.0.0") != "127.0.0.1":
            raise SystemExit("This is a PC/LAN setup: clients were built to trust its current certificate, so rotating it needs a new client build. Not done.")
        make_identity(directory, config["game_host"], {"localhost", "127.0.0.1", "::1"})
        (directory / "upstream.crt").write_bytes((directory / "server.crt").read_bytes())
        print("Loopback certificate replaced. Restart both services; on a VM also copy upstream.crt to /etc/beyond-heroes/upstream.crt and reload Caddy.")
        return
    if config_path.exists():
        raise SystemExit("Configuration already exists. Keep it to preserve server identity; see docs/OFFICIAL_SERVER.md to change its address.")
    host = (args.public_host or args.host).strip()
    if not host or any(c in host for c in "/\\:@ \r\n"):
        raise SystemExit("Use a host name or IPv4 address, without a URL or port.")
    for port in (args.api_port, args.game_port):
        if not 1024 <= port <= 65535:
            raise SystemExit("Use ports from 1024 to 65535.")
    directory.mkdir(parents=True, exist_ok=True)
    if vm:
        names = {"localhost", "127.0.0.1", "::1"}          # only the loopback address is ever verified against this certificate
    else:
        names = {host, "localhost", "127.0.0.1"}
        try:
            names.update(row[4][0] for row in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
        except OSError:
            pass
    private_path, certificate_path = make_identity(directory, host, names)
    server_key = secrets.token_urlsafe(48)
    config = {"bind": "127.0.0.1" if vm else "0.0.0.0", "api_port": args.api_port, "game_host": host,
              "game_port": args.game_port, "certificate": str(certificate_path),
              "private_key": str(private_path), "server_key": server_key}
    if vm:
        config["trusted_proxies"] = ["127.0.0.1", "::1"]
    _write_private(config_path, json.dumps(config, indent=2).encode("utf-8"))
    # The game coordinator is given only what it needs to call the service on loopback: never the TLS private key.
    _write_private(directory / "coordinator.json", json.dumps({"api_port": args.api_port, "game_port": args.game_port,
                   "certificate": str(certificate_path), "server_key": server_key}, indent=2).encode("utf-8"))
    if vm:
        (directory / "upstream.crt").write_bytes(certificate_path.read_bytes())
        (directory / "official.cfg").write_text('[server]\nurl="https://%s"\ncertificate=""\n' % host, encoding="utf-8")
        print("VM configuration created in", directory)
        print("Account address players use: https://%s (Caddy, TCP 443)" % host)
        print("Client build: copy %s to game/server/official.cfg before exporting. It holds no secret." % (directory / "official.cfg"))
        print("Caddy trusts the service through %s (public certificate only)." % (directory / "upstream.crt"))
    else:
        client = root / "game" / "server"
        client.mkdir(exist_ok=True)
        (client / "official_ca.crt").write_bytes(certificate_path.read_bytes())
        (client / "official.cfg").write_text('[server]\nurl="https://%s:%d"\ncertificate="res://server/official_ca.crt"\n' % (host, args.api_port), encoding="utf-8")
        print("Server configuration created. Keep server/data private; share only the game build or game/server public files.")
        print("Account address: https://%s:%d" % (host, args.api_port))
    print("Game port: %d UDP" % args.game_port)


if __name__ == "__main__":
    main()
