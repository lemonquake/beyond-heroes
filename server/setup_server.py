"""Create local server configuration and the public certificate used by clients."""
import argparse
import datetime
import ipaddress
import json
import os
import secrets
import socket
from pathlib import Path


def main():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="Address friends use to reach this PC")
    parser.add_argument("--api-port", type=int, default=8443)
    parser.add_argument("--game-port", type=int, default=24680)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    directory = root / "server" / "data"
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "server.json"
    if config_path.exists():
        raise SystemExit("Configuration already exists. Keep it to preserve server identity; see docs/OFFICIAL_SERVER.md to change its address.")
    host = args.host.strip()
    if not host or any(c in host for c in "/\\:@ \r\n"):
        raise SystemExit("Use a host name or IPv4 address, without a URL or port.")
    for port in (args.api_port, args.game_port):
        if not 1024 <= port <= 65535:
            raise SystemExit("Use ports from 1024 to 65535.")
    addresses = {host, "localhost", "127.0.0.1"}
    try:
        addresses.update(row[4][0] for row in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    names = []
    for address in sorted(addresses):
        try:
            names.append(x509.IPAddress(ipaddress.ip_address(address)))
        except ValueError:
            names.append(x509.DNSName(address))
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - datetime.timedelta(minutes=10))
                   .not_valid_after(now + datetime.timedelta(days=730))
                   .add_extension(x509.SubjectAlternativeName(names), critical=False)
                   .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                   .add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True,
                       content_commitment=False, data_encipherment=False, key_agreement=False,
                       key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
                   .sign(key, hashes.SHA256()))
    private_path = directory / "server.key"
    certificate_path = directory / "server.crt"
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    os.chmod(private_path, 0o600)
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    config = {"bind": "0.0.0.0", "api_port": args.api_port, "game_host": host,
              "game_port": args.game_port, "certificate": str(certificate_path),
              "private_key": str(private_path), "server_key": secrets.token_urlsafe(48)}
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    os.chmod(config_path, 0o600)
    client = root / "game" / "server"
    client.mkdir(exist_ok=True)
    (client / "official_ca.crt").write_bytes(certificate_path.read_bytes())
    (client / "official.cfg").write_text('[server]\nurl="https://%s:%d"\ncertificate="res://server/official_ca.crt"\n' % (host, args.api_port), encoding="utf-8")
    print("Server configuration created. Keep server/data private; share only the game build or game/server public files.")
    print("Account address: https://%s:%d" % (host, args.api_port))
    print("Game port: %d UDP" % args.game_port)


if __name__ == "__main__":
    main()
