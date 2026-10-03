"""Point the game builds at an official server: writes the public client endpoint game/server/official.cfg.

    python tools/set_official_server.py --url https://203-0-113-7.sslip.io     # a VPS (public certificate)
    python tools/set_official_server.py --local                                  # back to this PC's testing server

A VPS behind Caddy has a normal public certificate, so the certificate field is left empty (the game then trusts the
standard certificate authorities). The local testing server uses its own certificate, game/server/official_ca.crt.
Export the Windows and Android clients afterwards (python tools/export_builds.py --godot <Godot 4.7.2>). A player whose Server Settings
already name another server keeps that choice; they can type the new address there.
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "game" / "server" / "official.cfg"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="https://host of the server (no port: Caddy serves 443)")
    g.add_argument("--local", action="store_true", help="the testing server on this PC")
    args = ap.parse_args()
    if args.local:
        url, cert = "https://127.0.0.1:8443", "res://server/official_ca.crt"
    else:
        url = args.url.strip().rstrip("/")
        if not re.fullmatch(r"https://[A-Za-z0-9.-]+(:\d{1,5})?", url):
            raise SystemExit("Use an https:// address with a host name, for example https://play.example.com")
        cert = ""
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_text('[server]\nurl="%s"\ncertificate="%s"\n' % (url, cert), encoding="utf-8", newline="\n")
    print(f"{CFG.relative_to(ROOT)} -> {url}" + ("" if cert else " (public certificate)"))
    print("Now export the clients: python tools/export_builds.py --godot <path to Godot 4.7.2>")


if __name__ == "__main__":
    main()
