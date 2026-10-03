"""Build the dedicated-server packages for hosting the official server on a (free) Linux VPS.

    python tools/export_server.py [--godot PATH] [--arch arm64,x86_64,windows]

For each architecture Godot exports a *dedicated server* build (export mode "dedicated server": textures, meshes and
other visuals are stripped, so the VPS needs neither the 900 MB of game assets nor a GPU, nor to import the project),
then the build and the account service are packed into one upload:

    build/server/beyond-heroes-server-<commit>-linux-arm64.tar.gz    Oracle Cloud Always Free (Ampere A1)
    build/server/beyond-heroes-server-<commit>-linux-x86_64.tar.gz   Google Cloud e2-micro, most other VPS
    build/server/beyond-heroes-server-<commit>-windows.zip           local testing (server.integration_probe --coordinator)

A package holds bin/beyond_heroes_server(.exe), the server/ Python package (no player data, no secrets) and
server/deploy/free-vps.sh, which installs everything on the VM (docs/FREE_VPS_HOSTING.md).

The presets "Server Linux arm64", "Server Linux x86_64" and "Server Windows" are added to game/export_presets.cfg
(ignored by Git) when they are missing. The Godot 4.7.2 export templates must be installed.
"""
import argparse
import io
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PRESETS = GAME / "export_presets.cfg"
OUT = ROOT / "build" / "server"
DEFAULT_GODOT = r"C:\Users\Lemon PC\Desktop\Godot.exe"

TARGETS = {
    "arm64": ("Server Linux arm64", "Linux", "arm64", "beyond_heroes_server"),
    "x86_64": ("Server Linux x86_64", "Linux", "x86_64", "beyond_heroes_server"),
    "windows": ("Server Windows", "Windows Desktop", "x86_64", "beyond_heroes_server.exe"),
}
# server files that never go into a package: player data and secrets, caches, the Windows-only desktop launchers
TEXT = {".sh", ".py", ".service", ".timer", ".conf", ".example", ".md", ".lock", ".txt", ".cfg"}
CRLF, LF = bytes((13, 10)), bytes((10,))
SKIP = re.compile(r"(^data/|__pycache__|\.pyc$|^test_|\.ps1$|^control\.py$)")


def preset_block(index: int, name: str, platform: str, arch: str) -> str:
    return f"""
[preset.{index}]

name="{name}"
platform="{platform}"
runnable=false
advanced_options=false
dedicated_server=true
custom_features="dedicated_server"
export_filter="customized"
customized_files={{
"res://": "strip",
"res://tests": "remove"
}}
include_filter="server/*.cfg"
exclude_filter="tests/*"
export_path=""
patches=PackedStringArray()
encryption_include_filters=""
encryption_exclude_filters=""
seed=0
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.{index}.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=0
binary_format/embed_pck=true
texture_format/s3tc_bptc=true
texture_format/etc2_astc=false
binary_format/architecture="{arch}"
"""


def ensure_presets(wanted):
    text = PRESETS.read_text(encoding="utf-8") if PRESETS.exists() else ""
    names = set(re.findall(r'^name="([^"]+)"', text, re.M))
    indices = [int(i) for i in re.findall(r"^\[preset\.(\d+)\]", text, re.M)]
    nxt = max(indices) + 1 if indices else 0
    added = []
    for key in wanted:
        name, platform, arch, _ = TARGETS[key]
        if name in names:
            continue
        text += preset_block(nxt, name, platform, arch)
        added.append(name)
        nxt += 1
    if added:
        PRESETS.write_text(text, encoding="utf-8", newline="\n")
        print("Added export presets:", ", ".join(added))


def commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short=10", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "local"


def server_files():
    """(path on disk, name in the package) for the server package."""
    out = []
    for p in sorted((ROOT / "server").rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT / "server").as_posix()
        if SKIP.search(rel):
            continue
        out.append((p, "server/" + rel))
    return out


def export(godot: str, key: str) -> Path:
    name, _platform, _arch, binary = TARGETS[key]
    dest = OUT / key / binary
    dest.parent.mkdir(parents=True, exist_ok=True)
    log = OUT / f"export-{key}.log"
    cmd = [godot, "--headless", "--path", str(GAME), "--export-release", name, str(dest)]
    print("Exporting", name, "->", dest, flush=True)
    with log.open("w", encoding="utf-8") as f:
        code = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=3600)
    errors = [ln for ln in log.read_text(encoding="utf-8", errors="replace").splitlines() if "SCRIPT ERROR" in ln or "Parse Error" in ln]
    if code != 0 or not dest.exists() or errors:
        raise SystemExit(f"{name} export failed (exit {code}, {len(errors)} script errors); see {log}")
    return dest


def package(key: str, binary: Path, tag: str) -> Path:
    files = server_files()
    readme = (ROOT / "docs" / "FREE_VPS_HOSTING.md").read_bytes() if (ROOT / "docs" / "FREE_VPS_HOSTING.md").exists() else b""
    version = f"{tag}\n".encode()
    if key == "windows":
        path = OUT / f"beyond-heroes-server-{tag}-windows.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(binary, "bin/" + binary.name)
            for src, name in files:
                z.write(src, name)
            z.writestr("README-VPS.md", readme)
            z.writestr("RELEASE", version)
        return path
    path = OUT / f"beyond-heroes-server-{tag}-linux-{key}.tar.gz"
    with tarfile.open(path, "w:gz") as t:
        def add(src, name, mode):
            info = t.gettarinfo(str(src), name)
            info.mode, info.uid, info.gid, info.uname, info.gname = mode, 0, 0, "root", "root"
            with open(src, "rb") as f:
                t.addfile(info, f)

        def add_bytes(data, name):
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), 0o644
            t.addfile(info, io.BytesIO(data))
        add(binary, "bin/" + binary.name, 0o755)
        for src, name in files:
            if src.suffix in TEXT or src.name.startswith("Caddyfile"):
                # a Windows checkout has CRLF line endings; on Linux a shebang ending in CR is a bad interpreter
                data = src.read_bytes().replace(CRLF, LF)
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(data), 0o755 if name.endswith(".sh") else 0o644
                t.addfile(info, io.BytesIO(data))
            else:
                add(src, name, 0o755 if name.endswith(".sh") else 0o644)
        add_bytes(readme.replace(CRLF, LF), "README-VPS.md")
        add_bytes(version, "RELEASE")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--godot", default=DEFAULT_GODOT)
    ap.add_argument("--arch", default="arm64,x86_64,windows")
    args = ap.parse_args()
    wanted = [a for a in args.arch.split(",") if a]
    for a in wanted:
        if a not in TARGETS:
            raise SystemExit(f"unknown architecture {a} (choose from {', '.join(TARGETS)})")
    ensure_presets(wanted)
    tag = commit()
    for key in wanted:
        binary = export(args.godot, key)
        pkg = package(key, binary, tag)
        print(f"{key}: {pkg} ({pkg.stat().st_size / 1e6:.1f} MB; server binary {binary.stat().st_size / 1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
