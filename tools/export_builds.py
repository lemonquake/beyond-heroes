"""Export Windows and Android builds and record checksums without logging signing secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def redact(line):
    if re.search(r"apksigner|--(?:ks|key)-pass|keystore|password", line, re.IGNORECASE):
        return "[Signing details omitted]\n"
    return line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", required=True)
    parser.add_argument("--preset", choices=["Windows", "Android", "All"], default="All")
    parser.add_argument("--label", default="balance-20261003")
    args = parser.parse_args()
    evidence = ROOT / "output" / args.label
    evidence.mkdir(parents=True, exist_ok=True)
    receipt = evidence / "builds.json"
    result = json.loads(receipt.read_text()) if receipt.exists() else {"builds": {}}
    result["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for preset, filename in [("Windows", "windows/BeyondHeroes.exe"), ("Android", "BeyondHeroes.apk")]:
        if args.preset not in ["All", preset]:
            continue
        destination = ROOT / "build" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        # The project's Android preset uses the installed debug keystore.
        mode = "--export-debug" if preset == "Android" else "--export-release"
        command = [args.godot, "--headless", "--path", str(ROOT / "game"), mode, preset, str(destination)]
        errors = []
        with (evidence / f"export-{preset.lower()}.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding="utf-8", errors="replace")
            for line in process.stdout:
                log.write(redact(line))
                if "SCRIPT ERROR:" in line or "Parse Error:" in line:
                    errors.append(line.strip())
            code = process.wait()
        if code or errors or not destination.is_file():
            raise SystemExit(f"{preset} export failed: exit {code}, script errors {len(errors)}; inspect sanitized log")
        digest = hashlib.sha256()
        with destination.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        result["builds"][preset] = {"path": str(destination), "bytes": destination.stat().st_size,
                                   "sha256": digest.hexdigest(), "mode": mode, "export_exit": code}
        receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"{preset} complete: {destination} ({destination.stat().st_size} bytes)", flush=True)


if __name__ == "__main__":
    main()
