"""Restore the original CC0 source packs, enforcing the recorded archive hashes."""
from pathlib import Path
import hashlib
import json
import shutil
import stat
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets_src/map_design_20261003"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source_dir = BASE / "sources"
    source_dir.mkdir(exist_ok=True)
    for entry in json.loads((BASE / "downloads.json").read_text(encoding="utf-8")):
        kit = entry["kit"]
        assert kit in {"nature-kit", "furniture-kit", "pirate-kit", "graveyard-kit", "modular-dungeon-kit"}
        archive = source_dir / f"{kit}.zip"
        if archive.exists():
            if digest(archive) != entry["archive_sha256"]:
                raise RuntimeError(f"Existing {archive} has a different hash; preserve it and investigate")
        else:
            temporary = source_dir / f"{kit}.zip.part"
            with urllib.request.urlopen(entry["download_url"], timeout=60) as response, temporary.open("xb") as output:
                shutil.copyfileobj(response, output)
            if digest(temporary) != entry["archive_sha256"]:
                raise RuntimeError(f"Download hash changed for {kit}; retained {temporary} for review")
            temporary.rename(archive)
        destination = (source_dir / kit).resolve()
        with zipfile.ZipFile(archive) as bundle:
            corrupt = bundle.testzip()
            if corrupt:
                raise RuntimeError(f"Bad ZIP member: {corrupt}")
            for member in bundle.infolist():
                relative = Path(member.filename)
                target = (destination / relative).resolve()
                if not target.is_relative_to(destination) or relative.is_absolute() or ":" in member.filename:
                    raise RuntimeError(f"Unsafe ZIP path: {member.filename}")
                if stat.S_ISLNK(member.external_attr >> 16):
                    raise RuntimeError(f"ZIP symlink refused: {member.filename}")
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                data = bundle.read(member)
                if target.exists():
                    if target.read_bytes() != data:
                        raise RuntimeError(f"Existing source differs: {target}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        page = source_dir / f"{kit}.html"
        if not page.exists():
            with urllib.request.urlopen(entry["source_page"], timeout=60) as response:
                page.write_bytes(response.read())
        print(f"Verified and restored {kit}", flush=True)

if __name__ == "__main__":
    main()
