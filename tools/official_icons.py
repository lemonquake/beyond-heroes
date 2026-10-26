"""Plan, package and audit the original Beyond Heroes icon set.

Generate with the built-in image tool, copy originals to RUN/sheets/<key>.png,
then run pack. This tool only crops/resizes generated artwork; it never draws it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
DEFAULT_RUN = ROOT / "output/official-icons-20261027"
CATEGORIES = ("skills", "items", "talents", "status", "ui", "attributes", "elements", "classes", "crystals")
STYLE = """Use case: stylized-concept. Production artwork for Beyond Heroes, a dark fantasy action RPG in Jre: old forged weapons, worn armor, dangerous elemental magic and spirits of fallen heroes. Paint dimensional subjects with crisp, strong silhouettes, deep charcoal blue backgrounds, tactile steel/leather/stone and restrained colored elemental light. Hand-painted realistic fantasy game inventory art, consistent brushwork and upper-left lighting. Physical silver and ochre; fire orange-white; ice pale cyan; lightning yellow-white; earth ochre; wind pale green; water deep blue; light warm gold; dark violet-black. Each subject fills about 75 percent of its cell, with a quiet background and a safe 10 percent margin. Readable at 32/44/64 pixels. No letters, words, numbers, logos, decorative borders, frames, interface, captions, gutters or inset squares. Every cell is a full-bleed square illustration; future icon borders are a separate layer. Distinct cells must remain distinct and mechanically faithful. Do not add a damage blast to a traversal-only action. Do not imply guaranteed execution for an ordinary critical hit."""


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def res(path):
    return "res://" + Path(path).relative_to(GAME).as_posix()


def title(identifier):
    return identifier.replace("_", " ").replace("-", " ").title()


def make_plan(run):
    catalog = read(run / "catalog.json")
    by_path = defaultdict(list)
    for row in catalog["records"]:
        if row["resolved_path"]:
            by_path[row["resolved_path"]].append(row)
    entries = {}
    identities = {"skills": {}, "tempo_skills": {}, "upgrades": {}, "signatures": {}}

    def add(category, identifier, rows, source=""):
        key = category + "/" + identifier
        if key not in entries:
            names = list(dict.fromkeys(r["name"] for r in rows))
            effects = list(dict.fromkeys(r["effect"] for r in rows if r["effect"]))
            # A shared effect symbol may serve multiple related nodes, but never borrow a different skill's mechanics.
            description = "; ".join(names[:3]) or title(identifier)
            if effects:
                description += ". " + " ".join(effects[:2])
            entries[key] = {"id": key, "category": category, "name": names[0] if names else title(identifier),
                            "subject": description, "sources": [], "output": f"res://assets/ui/official/{key}.png"}
        if source and source not in entries[key]["sources"]:
            entries[key]["sources"].append(source)
        return entries[key]["output"]

    for category in CATEGORIES:
        for source in sorted((GAME / "assets/ui/icons" / category).glob("*.svg")):
            path = res(source)
            rows = by_path[path]
            # Prefer the identity that owns this route: aliases get their own cell later.
            if category == "skills":
                stem = source.stem
                own = [r for r in rows if (r["family"] == "skills" and r["id"] == stem) or
                       (r["family"] == "tempo_skills" and "tempo_" + r["id"] == stem)]
                if own:
                    rows = own
            add(category, source.stem, rows, path)
    for row in catalog["records"]:
        family, identifier = row["family"], row["id"]
        if family == "skills":
            source = "res://assets/ui/icons/skills/" + identifier + ".svg"
            identities["skills"][identifier] = add("skills", identifier, [row], source)
        elif family == "tempo_skills":
            source = "res://assets/ui/icons/skills/tempo_" + identifier + ".svg"
            identities["tempo_skills"][identifier] = add("skills", "tempo_" + identifier, [row], source)
        elif family == "classes" and row["missing"]:
            add("classes", identifier, [row], row["requested_path"])
        elif family == "upgrades":
            identities["upgrades"][identifier] = add("upgrades", identifier, [row])
        elif family == "signature_traits":
            identities["signatures"][identifier] = add("traits", identifier, [row])

    ordered = list(entries.values())
    sheets = []
    for start in range(0, len(ordered), 36):
        group = ordered[start:start + 36]
        cells = []
        for i, entry in enumerate(group):
            subject = entry["subject"]
            if len(subject) > 400:
                subject = subject[:397].rsplit(" ", 1)[0] + "..."
            cells.append(f"Row {i // 6 + 1}, column {i % 6 + 1}: {subject}")
        for i in range(len(group), 36):
            cells.append(f"Row {i // 6 + 1}, column {i % 6 + 1}: unused; quiet dark charcoal background only.")
        sheets.append({"key": f"sheet-{len(sheets)+1:02d}", "grid": 6,
                       "ids": [entry["id"] for entry in group] + [None] * (36-len(group)),
                       "prompt": STYLE + "\nCreate EXACTLY 6 equal columns and 6 equal rows, a 6x6 contact sheet of square icons. No gaps between cells. Enforce this exact row-major mapping:\n" + "\n".join(cells)})
    retained = {}
    for row in catalog["records"]:
        path = row["resolved_path"]
        if path.endswith(".png"):
            file = GAME / path.removeprefix("res://")
            if file.is_file():
                retained[path] = {"sha256": digest(file), "reason": "Existing rendered item artwork retained"}
    registry = {"version": 1, "art_style": "Beyond Heroes painted fantasy", "entries": ordered, "identities": identities,
                "retained_artifacts": retained}
    write(run / "registry.json", registry)
    write(run / "plan.json", sheets)
    (run / "sheets").mkdir(parents=True, exist_ok=True)
    print(json.dumps({"icons": len(ordered), "sheets": len(sheets), "retained_pngs": len(retained),
                      "categories": dict(Counter(e["category"] for e in ordered))}))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def package(run, check=False):
    from PIL import Image

    plan, registry = read(run / "plan.json"), read(run / "registry.json")
    sources, hashes = {}, {}
    for sheet in plan:
        source = run / "sheets" / (sheet["key"] + ".png")
        if not source.is_file():
            raise SystemExit("Missing generated original: " + str(source))
        original = Image.open(source).convert("RGBA")
        width, height = original.size
        if abs(width-height) > 1:
            raise SystemExit("Sheet must be square: " + str(source))
        grid = sheet["grid"]
        for i, key in enumerate(sheet["ids"]):
            if key is None:
                continue
            x, y = i % grid, i // grid
            box = (round(x*width/grid), round(y*height/grid), round((x+1)*width/grid), round((y+1)*height/grid))
            image = original.crop(box).resize((256, 256), Image.Resampling.LANCZOS)
            destination = GAME / "assets/ui/official" / (key + ".png")
            if check:
                if not destination.exists() or Image.open(destination).convert("RGBA").tobytes() != image.tobytes():
                    raise SystemExit("Pixel mismatch: " + str(destination))
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                image.save(destination)
                imported = destination.with_suffix(".png.import")
                if imported.exists():
                    settings = imported.read_text(encoding="utf-8")
                    imported.write_text(settings.replace("mipmaps/generate=false", "mipmaps/generate=true"), encoding="utf-8")
            sources[key] = {"sheet": sheet["key"], "cell": i, "box": box, "sheet_sha256": digest(source)}
            hashes[key] = digest(destination)
    manifest = {"version": 1, "style": registry["art_style"], "routes": {}, **registry["identities"],
                "retained_artifacts": registry.get("retained_artifacts", {}),
                "artifacts": {}, "count": len(registry["entries"])}
    for entry in registry["entries"]:
        for path in entry["sources"]:
            manifest["routes"][path] = entry["output"]
        manifest["artifacts"][entry["id"]] = {"path": entry["output"], "sha256": hashes[entry["id"]], **sources[entry["id"]]}
    if not check:
        write(GAME / "assets/ui/official/manifest.json", manifest)
        write(run / "packaged-manifest.json", manifest)
    print(f"{'Verified' if check else 'Packaged'} {len(hashes)} icons from {len(plan)} generated originals")


def audit(run):
    from PIL import Image

    manifest = read(GAME / "assets/ui/official/manifest.json")
    registry = read(run / "registry.json")
    failures = []
    for entry in registry["entries"]:
        path = GAME / entry["output"].removeprefix("res://")
        if not path.is_file():
            failures.append("Missing " + entry["output"])
            continue
        image = Image.open(path)
        if image.size != (256, 256):
            failures.append("Incorrect dimensions " + entry["output"])
        if manifest["artifacts"].get(entry["id"], {}).get("sha256") != digest(path):
            failures.append("Hash mismatch " + entry["id"])
        for source in entry["sources"]:
            if manifest["routes"].get(source) != entry["output"]:
                failures.append("Incorrect route " + source)
    for source, record in registry.get("retained_artifacts", {}).items():
        path = GAME / source.removeprefix("res://")
        if not path.is_file() or digest(path) != record["sha256"]:
            failures.append("Retained artwork changed or missing " + source)
    result = {"expected": len(registry["entries"]), "packaged": manifest["count"],
              "retained_pngs": len(registry.get("retained_artifacts", {})), "failures": failures}
    write(run / "audit.json", result)
    print(json.dumps(result))
    if failures:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "pack", "audit"))
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.command == "plan":
        make_plan(args.run)
    elif args.command == "pack":
        package(args.run, args.check)
    else:
        audit(args.run)


if __name__ == "__main__":
    main()
