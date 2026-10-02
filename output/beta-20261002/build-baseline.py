"""Export distinctly named QA builds, with signing arguments redacted from logs."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
DESTINATION = ROOT / "build" / "beta-20261002"
GODOT = Path(r"A:\Installer\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64_console.exe")


def redact(line):
    if re.search(r"apksigner|--(?:ks|key)-pass|keystore|password", line, re.IGNORECASE):
        return "[Signing command/details omitted from QA log]\n"
    return re.sub(
        r"((?:--ks-pass|--key-pass|--ks-key-alias|--ks)\s+)(?:\"[^\"]*\"|'[^']*'|\S+)",
        r"\1<REDACTED>", line,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preset', choices=['All', 'Windows', 'Android'], default='All')
    parser.add_argument('--android-debug', action='store_true')
    args = parser.parse_args()
    DESTINATION.mkdir(parents=True, exist_ok=True)
    receipt = EVIDENCE / 'baseline-builds.json'
    result = json.loads(receipt.read_text()) if receipt.exists() else {"label": "QA baseline; unresolved test failures; not a polished beta release", "builds": []}
    android_name = 'BeyondHeroes-baseline-debug.apk' if args.android_debug else 'BeyondHeroes-baseline.apk'
    for preset, filename in (("Windows", "BeyondHeroes-baseline.exe"), ("Android", android_name)):
        if args.preset not in ('All', preset):
            continue
        target = DESTINATION / filename
        if target.exists():
            raise SystemExit(f"Refusing to overwrite existing baseline: {target}")
        debug = preset == 'Android' and args.android_debug
        command = [str(GODOT), "--headless", "--path", str(ROOT / "game"), '--export-debug' if debug else "--export-release", preset, str(target)]
        with (EVIDENCE / ("baseline-export-" + preset.lower() + ('-debug' if debug else '') + ".log")).open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in process.stdout:
                log.write(redact(line))
            code = process.wait()
        if code or not target.is_file():
            raise SystemExit(f"{preset} export failed: exit {code}; inspect sanitized export log.")
        digest = hashlib.sha256()
        with target.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        result["builds"].append({"preset": preset, "debug": debug, "path": str(target), "bytes": target.stat().st_size, "sha256": digest.hexdigest(), "export_exit": code})
        (EVIDENCE / "baseline-builds.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"{preset} baseline export complete: {target} ({target.stat().st_size} bytes)", flush=True)


if __name__ == "__main__":
    main()
