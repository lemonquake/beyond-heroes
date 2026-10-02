"""Build the human-readable inventory, handoff appendix and creator-preview sheets."""
from pathlib import Path
import collections
import hashlib
import json
import struct
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets_src/map_design_20261003"

def main():
    manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    assets = manifest["assets"]
    assert len(assets) == 114
    assert len({a["source_sha256"] for a in assets}) == 114
    for a in assets:
        model = BASE / a["model"]
        blob = model.read_bytes()
        assert hashlib.sha256(blob).hexdigest() == a["package_model_sha256"], a["id"]
        magic, version, size = struct.unpack_from("<4sII", blob)
        assert magic == b"glTF" and version == 2 and size == len(blob), a["id"]
        chunk_size, chunk_type = struct.unpack_from("<I4s", blob, 12)
        assert chunk_type == b"JSON", a["id"]
        doc = json.loads(blob[20:20 + chunk_size])
        assert not any("uri" in b for b in doc.get("buffers", [])), a["id"]
        assert not any("uri" in i for i in doc.get("images", [])), a["id"]
        evidence = json.loads((BASE / "evidence" / f"{a['id']}.json").read_text())
        assert evidence["validation"]["passed"]
        assert evidence["package_verification"]["data"]["hashesVerified"]
    counts = collections.Counter(a["kit"] for a in assets)
    summary = {"distinct_models": len(assets), "by_kit": dict(counts),
               "dungeon_additions": sum(a["kind"] == "dungeon" for a in assets),
               "model_bytes": sum(a["bytes"] for a in assets),
               "triangles_min": min(a["triangles"] for a in assets),
               "triangles_max": max(a["triangles"] for a in assets),
               "triangles_median": sorted(a["triangles"] for a in assets)[len(assets) // 2],
               "multi_mesh_models": sum(a["meshes"] > 1 for a in assets),
               "previews": sum(bool(a["preview"]) for a in assets),
               "static_validation_passed": len(assets), "package_hashes_verified": len(assets),
               "embedded_dependencies_checked": len(assets), "runtime_integration": "Pending Claude Code",
               "models_with_embedded_sidecar_textures": sum(bool(a["embedded_textures"]) for a in assets),
               "fps_measurement": "Not performed; requires integration and device tests"}
    (BASE / "verification_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    appendix = []
    for a in assets:
        dims = " x ".join(f"{v:.3f}" for v in a["size_metres"])
        notes = "MULTI-MESH: prepare all parts before batching. " if a["meshes"] > 1 else ""
        appendix.append(
            f"{a['number']:03d}. {a['id']}\n"
            f"     Object: {a['description']}.\n"
            f"     Suggested use: {a['placement']}.\n"
            f"     Source: Kenney {a['kit']}, CC0-1.0. {a['triangles']} triangles; "
            f"{a['meshes']} mesh(es), {a['surfaces']} surfaces, {a['materials']} materials.\n"
            f"     Source bounds (X/Y/Z metres): {dims}. {notes}Restyle and scale for this game.\n"
            f"     Model: assets_src/map_design_20261003/{a['model']}\n"
            f"     Package: assets_src/map_design_20261003/{a['package']}\n")
    inventory = "\n".join(appendix)
    (BASE / "ASSET_DESCRIPTIONS.txt").write_text(inventory, encoding="utf-8")
    brief = ROOT / "docs/CLAUDE_MAP_DESIGN_AND_DUNGEON_ASSETS.txt"
    text = brief.read_text(encoding="utf-8")
    marker = "\nVERIFIED NUMBERED INVENTORY\n"
    text = text.split(marker)[0] + marker + "\n" + inventory
    brief.write_text(text, encoding="utf-8")
    sheets = BASE / "contact_sheets"
    sheets.mkdir(exist_ok=True)
    groups = [("01_nature_trees_and_plants", assets[:24]), ("02_nature_rocks_and_props", assets[24:48]),
              ("03_interior_furniture", assets[48:74]), ("04_harbour_and_coast", assets[74:94]),
              ("05_dungeon_additions", assets[94:])]
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 25)
    for name, group in groups:
        cols, width, height = 5, 280, 255
        rows = (len(group) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * width, 100 + rows * height), "#eef1f3")
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 15), name[3:].replace("_", " ").title(), font=title_font, fill="#16232e")
        draw.text((20, 53), "Kenney CC0 creator previews | Source models before Beyond Heroes material/scale preparation",
                  font=font, fill="#42515d")
        for i, a in enumerate(group):
            x, y = (i % cols) * width, 100 + (i // cols) * height
            preview = Image.open(BASE / a["preview"]).convert("RGBA")
            bounds = preview.getbbox()
            if bounds:
                preview = preview.crop(bounds)
            scale = min(250 / preview.width, 175 / preview.height)
            preview = preview.resize((max(1, round(preview.width * scale)), max(1, round(preview.height * scale))),
                                     Image.Resampling.LANCZOS)
            sheet.paste(preview, (x + (width - preview.width) // 2, y + 5), preview)
            stem = Path(a["source_model"]).stem
            draw.text((x + 10, y + 185), f"{a['number']:03d}  {stem}", font=font, fill="#16232e")
            draw.text((x + 10, y + 209), f"{a['triangles']} tris | {a['meshes']} meshes | {a['surfaces']} surfaces",
                      font=font, fill="#42515d")
            if a["meshes"] > 1:
                draw.text((x + 10, y + 231), "Combine all mesh parts before batching", font=font, fill="#7c401d")
        sheet.save(sheets / f"{name}.jpg", quality=90)
    readme = f"""# Map design asset library

Downloaded on 3 October 2026: **114 distinct GLB source objects** by Kenney, licensed CC0-1.0.
48 nature, 26 furniture, 20 coastal/harbour, and 20 additional dungeon objects (16 graveyard + 4 dungeon kit).

This library is for Claude Code's implementation of Salmonan, Zarael/Agdao, interiors and dungeon atmosphere.
Read [the complete brief](../../docs/CLAUDE_MAP_DESIGN_AND_DUNGEON_ASSETS.txt), [object descriptions](ASSET_DESCRIPTIONS.txt),
[the CSV catalog](asset_catalog.csv) and [the manifest](manifest.json).

## Verification

All 114 pass their recorded static source policies, have verified canonical package hashes,
and have self-contained GLB buffer/image dependencies. Source geometry spans {summary['triangles_min']}–{summary['triangles_max']} triangles;
the model files total {summary['model_bytes']:,} bytes (~{summary['model_bytes']/1048576:.2f} MiB).
{summary['multi_mesh_models']} models contain multiple meshes and require careful preparation for the current batching loader.
This proves source suitability and file integrity. Engine integration, artistic adaptation and FPS remain pending.

## Contents

- `canonical/.game-dev/packages/`: selected immutable models with provenance, hashes, policies and receipts.
- `licenses/`: original license documents, including permission for commercial use.
- `downloads.json`: exact original creator ZIP URLs and SHA-256 hashes.
- `manifest.json` and `asset_catalog.csv`: exact model/package paths, descriptions and intended use.
- `requests/` and `evidence/`: curation settings, inspections, validation and verification results.
- `previews/` and `contact_sheets/`: creator previews, labelled with actual source geometry counts.
- `sources/`: full downloaded archives and alternate formats, kept locally and Git-ignored.

The source previews have not been recoloured to the game. Use shared timber/stone/fabric materials,
correct scale/pivots, and a lit material treatment before integration. Do not import modern appliances.
Do not rename or overwrite existing environment objects. Unused models should stay out of runtime exports.

## Reproduce

```powershell
python tools/download_map_asset_sources.py
python tools/curate_map_assets.py --cli "<installed game-dev dist/cli.js>"
python tools/document_map_asset_curation.py
```

The downloader checks archive hashes and refuses to overwrite differing existing files.
The local Windows wrapper works around directory-fsync EPERM in game-dev 1.0.2 without changing installed tools.
The final numbered inventory is embedded in the Claude brief; only that text file is needed to start the handoff.
"""
    (BASE / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
