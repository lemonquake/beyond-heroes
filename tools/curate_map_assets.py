"""Curate downloaded CC0 sources into verified Game Development Studio packages.

Run from the repository root after downloading the three source ZIPs described
in assets_src/map_design_20261003/downloads.json. No gameplay files are modified.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import struct

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets_src/map_design_20261003"

# Every row describes one distinct source mesh, not recolours or file formats.
# kind | source stem | description | authored placement purpose
SELECTION = {
    "nature-kit": """
tree|tree_oak|Broad oak with a rounded crown|Malasugue outskirts and Olivar lakeside shade
tree|tree_default|Compact broadleaf tree|Residential gardens and Westreach hedgerow breaks
tree|tree_detailed|Branching broadleaf tree|A few focal trees beside town courtyards
tree|tree_thin|Narrow broadleaf tree|Olivar lanes where wide crowns obstruct the camera
tree|tree_small|Small broadleaf tree|Gardens behind houses, away from door approaches
tree|tree_pineDefaultA|Straight layered conifer|Ruined Forest silhouette and high ground
tree|tree_pineRoundA|Round tiered conifer|Forest borders with a different crown silhouette
tree|tree_pineTallA|Tall conifer|Distant tree line and selected forest landmarks
tree|tree_palm|Straight palm|Agdao harbour gardens and Tideglass Cove
tree|tree_palmBend|Leaning palm|Agdao waterfront silhouette, leaning away from walkways
tree|tree_palmShort|Low palm|Agdao small planted courtyards
tree|tree_palmDetailedTall|Detailed tall palm|Sparse focal trees beside the harbour approach
foliage|plant_bush|Rounded shrub|House foundations and village lot boundaries
foliage|plant_bushLarge|Large shrub mass|Olivar garden corners and Agdao hill edges
foliage|plant_bushSmall|Small shrub|Low edging beside stairs and houses
foliage|plant_flatTall|Tall leafy plant|Agdao planters and Coilwood trail margins
foliage|grass|Small grass tuft|Sparse path-to-ground transitions
foliage|grass_large|Large grass tuft|Grouped banks, avoiding central travel lanes
foliage|grass_leafs|Broad leaf ground plant|Agdao jungle edge and Coilwood undergrowth
foliage|flower_yellowA|Yellow flowering stem|Olivar gardens and domestic planted beds
foliage|flower_purpleA|Purple flowering stem|Malasugue house garden accents
foliage|mushroom_tanGroup|Cluster of pale mushrooms|Damp forest logs and crypt threshold edges
foliage|lily_large|Large lily pad|Olivar sheltered lake edge and marsh pools
foliage|hanging_moss|Hanging moss strands|Sparse damp ruin details; test opacity and overdraw
rock|rock_largeA|Large irregular boulder|Westreach coastal clusters and Agdao shore anchors
rock|rock_largeB|Second large boulder silhouette|Asymmetric rock clusters beside broad walking spaces
rock|rock_largeC|Third large boulder silhouette|Cliff foot and forest clearing boundary
rock|rock_smallA|Small irregular rock|Transition scatter around larger rocks
rock|rock_smallB|Second small rock silhouette|Shore and farm-edge accents
rock|rock_smallFlatA|Flat low rock|Ground transitions and stream banks
rock|rock_tallA|Tall narrow rock|Sparse rocky coast silhouettes
rock|stone_largeA|Large stone boulder|Pale inland rock and terrace garden anchors
rock|stone_smallFlatA|Flat pale stone|Olivar shore, ruin floor edges and garden trim
prop|stump_old|Weathered tree stump|Ruined Forest logging remnants
prop|stump_roundDetailed|Cut stump with irregular surface|Westreach woodcutting patch and Wyman firewood corner
prop|log|Fallen log|Forest floor composition and simple camp seating
prop|log_stack|Stacked cut timber|Wyman supply corner and Malasugue forge fuel
prop|fence_planks|Plank fence span|Westreach farm boundaries and house lots
prop|fence_gate|Farm fence gate|Garden and field entrances with a clear passage
prop|pot_small|Small earthen pot|Herbs, kitchen storage and market table grouping
prop|pot_large|Large earthen pot|Agdao courtyard planters and town storage
prop|crop_carrot|Carrot produce|Westreach farm beds and market produce display
prop|crop_pumpkin|Pumpkin produce|Market baskets and farm storage clusters
prop|crops_wheatStageB|Mature wheat patch|Small authored Westreach farm beds
prop|crops_bambooStageB|Mature bamboo patch|Sparse Agdao back gardens and Coilwood framing
prop|tent_smallOpen|Small open tent|Wyman and survivor camp edge, preserve entrances
prop|campfire_stones|Stone campfire ring|Camp seating group; reuse existing fire effects
prop|canoe|Simple canoe hull|Olivar dock or cove mooring, not a new travel mechanic
""",
    "furniture-kit": """
furniture|bench|Plain bench|Town resting corners, harbour seating and tavern wall
furniture|chair|Plain timber chair|Tavern tables and domestic interiors
furniture|chairRounded|Rounded-back chair|Council and guild meeting rooms after timber restyle
furniture|stoolBarSquare|Square stool|Tavern counter and smithy work corner
furniture|table|Rectangular table|Tavern eating group and netmender work area
furniture|tableRound|Round table|Small tavern seating groups
furniture|tableCross|Cross-braced table|Guild meeting table and workshop
furniture|tableCloth|Cloth-covered table|Market or domestic dining after linen recolour
furniture|sideTable|Small side table|Bedside storage and document corner
furniture|sideTableDrawers|Drawer side table|Keeper and cartographer storage
furniture|desk|Writing desk|Cartographer and guild administration
furniture|bookcaseOpen|Tall open bookcase|Cartographer and Lantern House library wall
furniture|bookcaseOpenLow|Low open bookcase|Guild room divider without camera obstruction
furniture|bookcaseClosed|Closed timber bookcase|Keeper house and council archives
furniture|bookcaseClosedWide|Wide closed bookcase|Guild House archival wall
prop|books|Small stack of books|Cartographer desk and council reading table
furniture|bedSingle|Single bed|Existing domestic interiors after linen and wood restyle
furniture|bedDouble|Double bed|Hald house sleeping corner; verify room clearance
furniture|bedBunk|Bunk bed|Wyman lodging only if an existing interior supports it
prop|pillow|Simple pillow|Existing beds; remove modern-looking material gloss
prop|rugRectangle|Rectangular rug|Tavern and guild seating area anchor
prop|rugRound|Round rug|Council seating group and domestic corner
prop|coatRackStanding|Standing coat rack|Tavern vestibule and guild reception
prop|plantSmall1|Small potted plant|House windows and Agdao market counters
prop|plantSmall2|Second small potted plant|Apothecary herb display and house shelves
prop|pottedPlant|Tall potted plant|Agdao courtyard and council entrance
""",
    "pirate-kit": """
prop|barrel|Wooden barrel|Harbour cargo, tavern cellar edge and Wyman stores
prop|crate|Wooden cargo crate|Agdao pier handling area and Westreach stolen cargo
prop|crate-bottles|Crate holding bottles|Tavern stock and merchant delivery scene
prop|bottle|Small bottle|Tavern tables and apothecary shelves
prop|bottle-large|Large bottle|Grouped apothecary and market storage
prop|chest|Wooden chest|House storage; keep existing loot chest logic intact
prop|tool-shovel|Hand shovel|Farm shed and garden work corner
prop|tool-paddle|Wooden paddle|Olivar boathouse and harbour boat-rest area
vehicle|boat-row-small|Small rowing boat|Agdao quay secondary mooring
vehicle|boat-row-large|Larger rowing boat|Olivar landing; static decoration or shared gentle bob
landmark|ship-wreck|Broken ship hull|Tideglass Cove story vignette, no collision across approach
rock|rocks-a|Grouped shoreline rocks|Agdao harbour mouth and cove shore
rock|rocks-b|Second grouped shoreline rocks|Coastal silhouette variety
rock|rocks-c|Third grouped shoreline rocks|Cliff-to-water boundary
prop|platform-planks|Plank deck piece|Dock repair vignette, visual only unless navigation updated
prop|structure-fence|Timber rail span|Harbour railing repairs beside existing geometry
prop|structure-platform-dock-small|Small dock platform|Supplemental mooring beside existing traversable pier
prop|structure-roof|Small timber canopy roof|Cargo shelter; restyle and preserve camera visibility
prop|flag-pennant|Plain pennant flag|Town accents with canon colours and no pirate markings
prop|mast-ropes|Rope-equipped mast|Harbour rigging vignette, static mesh and no new sail physics
""",
    "graveyard-kit": """
dungeon|altar-stone|Stone ritual altar|Catacomb ritual room, temple side chapel and Jade tomb niche
dungeon|altar-wood|Timber ritual altar|Forest cult shelter and abandoned dungeon chapel
dungeon|coffin-old|Weathered coffin|Blackvault Ossuary and drowned crypt wall alcoves
dungeon|coffin|Intact coffin|Burial room rows, retaining broad central combat space
dungeon|candle-multiple|Cluster of candles|Tomb and ritual staging; share capped existing flame effects
dungeon|lantern-candle|Candle lantern housing|Crypt route accents and flooded cistern pier
dungeon|fire-basket|Iron fire basket|Emberforge work alcove and Obsidian Engine service room
dungeon|urn-round|Round funerary urn|Catacomb niches and Jade Sepulchre memorial corners
dungeon|urn-square|Square funerary urn|Burial chamber silhouette variation
dungeon|detail-chalice|Ritual chalice|Altar grouping and ruined temple offering table
dungeon|detail-bowl|Offering bowl|Temple and tomb ritual table composition
dungeon|debris|Stone debris pile|Collapsed crypt wall or exhausted mine edge
dungeon|debris-wood|Broken timber debris|Flooded Deeps wreck edge and abandoned storeroom
dungeon|gravestone-broken|Broken headstone|Ruined Forest graveyard and Blackvault threshold
dungeon|column-large|Large stone column|Ruined Temple side arcade and sparse tomb focal structure
dungeon|pillar-obelisk|Stone obelisk|Crypt or Jade chamber landmark after canon glyph treatment
""",
    "modular-dungeon-kit": """
dungeon|gate-metal-bars|Metal barred gate|Visual side-cell gate, preserve existing sealed-door state logic
dungeon|template-wall-half|Half-height stone wall|Cutaway dungeon side alcoves after scale and collision audit
dungeon|template-floor-layer-raised|Raised stone floor insert|Dry island in damp crypt or small ritual plinth
dungeon|template-floor-detail-a|Detailed stone floor insert|Sparse threshold accent and repaired temple paving
""",
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def portable_model(source, stable_id):
    """Embed external PNG/JPEG image bytes without modifying geometry or source."""
    blob = source.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", blob)
    assert magic == b"glTF" and version == 2 and length == len(blob)
    json_length, json_type = struct.unpack_from("<I4s", blob, 12)
    assert json_type == b"JSON"
    doc = json.loads(blob[20:20 + json_length])
    external = [i for i in doc.get("images", []) if "uri" in i]
    if not external:
        return source, []
    assert len(doc.get("buffers", [])) == 1 and "uri" not in doc["buffers"][0]
    bin_header = 20 + json_length
    bin_length, bin_type = struct.unpack_from("<I4s", blob, bin_header)
    assert bin_type == b"BIN\x00"
    binary = bytearray(blob[bin_header + 8:bin_header + 8 + bin_length])
    dependencies = []
    import urllib.parse
    for image in external:
        uri = image.pop("uri")
        assert not urllib.parse.urlparse(uri).scheme and not Path(uri).is_absolute(), uri
        texture = (source.parent / urllib.parse.unquote(uri)).resolve()
        assert texture.is_relative_to(source.parent.resolve()), texture
        content = texture.read_bytes()
        assert content.startswith(b"\x89PNG\r\n\x1a\n") or content.startswith(b"\xff\xd8"), texture
        while len(binary) % 4:
            binary.append(0)
        view = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(content)}
        image["bufferView"] = len(doc.setdefault("bufferViews", []))
        doc["bufferViews"].append(view)
        image["mimeType"] = "image/png" if content.startswith(b"\x89PNG") else "image/jpeg"
        binary.extend(content)
        dependencies.append({"uri": uri, "sha256": digest(texture), "bytes": len(content)})
    doc["buffers"][0]["byteLength"] = len(binary)
    while len(binary) % 4:
        binary.append(0)
    json_chunk = json.dumps(doc, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    json_chunk += b" " * (-len(json_chunk) % 4)
    result = struct.pack("<4sII", b"glTF", 2, 28 + len(json_chunk) + len(binary))
    result += struct.pack("<I4s", len(json_chunk), b"JSON") + json_chunk
    result += struct.pack("<I4s", len(binary), b"BIN\x00") + binary
    prepared = BASE / ".preparation" / f"{stable_id}.glb"
    prepared.parent.mkdir(exist_ok=True)
    prepared.write_bytes(result)
    return prepared, dependencies

def run_cli(cli, args):
    result = subprocess.run(["node", str(ROOT / "tools/game_dev_windows.mjs"), str(cli), *map(str, args)], capture_output=True,
                            text=True, encoding="utf-8", timeout=90,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"CLI did not return JSON: {result.stderr[:500]} {result.stdout[:500]}")
    if result.returncode or not data.get("ok"):
        raise RuntimeError(json.dumps(data))
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", type=Path, required=True)
    args = parser.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    for folder in ("licenses", "previews", "requests", "evidence"):
        (BASE / folder).mkdir(exist_ok=True)
    records = []
    downloads = []
    download_file = BASE / "downloads.json"
    recorded_downloads = {r["kit"]: r for r in json.loads(download_file.read_text())} if download_file.exists() else {}
    for kit, rows in SELECTION.items():
        source_root = BASE / "sources" / kit
        archive = BASE / "sources" / f"{kit}.zip"
        license_source = source_root / "License.txt"
        license_text = license_source.read_text(encoding="utf-8-sig")
        assert "CC0" in license_text and "Kenney" in license_text
        shutil.copy2(license_source, BASE / "licenses" / f"{kit}.txt")
        html = (BASE / "sources" / f"{kit}.html").read_text(encoding="utf-8-sig")
        import re
        urls = re.findall(r'https://kenney.nl/[^"\s<>]+\.zip', html)
        if kit in recorded_downloads:
            recorded = recorded_downloads[kit]
            assert digest(archive) == recorded["archive_sha256"], f"Original archive changed: {kit}"
            urls = [recorded["download_url"]]
        assert urls, kit
        downloads.append({"kit": kit, "source_page": f"https://kenney.nl/assets/{kit}",
                          "download_url": urls[0], "archive_sha256": digest(archive),
                          "archive_bytes": archive.stat().st_size, "license": "CC0-1.0",
                          "license_file": f"licenses/{kit}.txt", "downloaded": "2026-10-03"})
        for row in rows.strip().splitlines():
            kind, stem, description, placement = row.split("|")
            candidates = list(source_root.rglob(stem + ".glb"))
            assert len(candidates) == 1, (kit, stem, candidates)
            source = candidates[0]
            stable_id = "kenney_" + kit.replace("-kit", "") + "_" + stem.replace("-", "_").lower()
            package_input, dependencies = portable_model(source, stable_id)
            inspection = run_cli(args.cli, ["asset", "inspect", package_input, "--json"])["data"]
            # Source suitability gate; the stricter runtime budgets live in the handoff.
            policy = {"requireUVs": True, "requireNormals": True,
                      "requireTangentsWithNormalMap": True, "requireBaseColorTexture": False,
                      "maxTriangles": 6000 if kind in ("vehicle", "landmark") else 2500,
                      "maxMaterials": 4, "minTextureSize": 128,
                      "requirePowerOfTwoTextures": True, "maxDimensionMeters": 100,
                      "minDimensionMeters": 0.001}
            validation = run_cli(args.cli, ["asset", "validate", package_input, "--request",
                                write_json(BASE / "requests" / f"{stable_id}_policy.json", policy), "--json"])["data"]
            if not validation["passed"]:
                raise RuntimeError(f"Source fails policy: {stable_id}: {validation}")
            metadata = {"description": description + ". Intended use: " + placement,
                        "category": "foliage" if kind in ("tree", "foliage") else "environment_prop",
                        "policy": policy,
                        "provenance": {"origin": "imported", "provider": "Kenney",
                            "sourceUri": f"https://kenney.nl/assets/{kit}",
                            "downloadUri": urls[0], "originalArchiveSha256": digest(archive),
                            "originalModelSha256": digest(source),
                            "originalRelativePath": source.relative_to(BASE).as_posix(),
                            "licenseEvidence": f"licenses/{kit}.txt",
                            "transformations": (["Embedded external image bytes in GLB; geometry/material values unchanged"] if dependencies else []),
                            "originalTextureDependencies": dependencies, "downloadDate": "2026-10-03"}}
            request_path = write_json(BASE / "requests" / f"{stable_id}.json", metadata)
            built = run_cli(args.cli, ["package", "build", package_input, "--name", stable_id,
                                "--version", "1.1.0", "--license", "CC0-1.0", "--request", request_path,
                                "--output-dir", BASE / "canonical", "--json"])["data"]
            package_path = Path(built["packagePath"])
            verification = run_cli(args.cli, ["package", "verify", package_path, "--json"])
            assert verification["data"]["hashesVerified"], stable_id
            preview_options = [source_root / "Isometric" / f"{stem}_NE.png",
                               source_root / "Previews" / f"{stem}.png"]
            preview = next((p for p in preview_options if p.is_file()), None)
            preview_relative = None
            if preview:
                preview_dest = BASE / "previews" / f"{stable_id}.png"
                shutil.copy2(preview, preview_dest)
                preview_relative = preview_dest.relative_to(BASE).as_posix()
            record = {"number": len(records) + 1, "id": stable_id, "kit": kit, "kind": kind,
                      "source_model": source.relative_to(BASE).as_posix(),
                      "model": (package_path / "model.glb").relative_to(BASE).as_posix(),
                      "package": package_path.relative_to(BASE).as_posix(),
                      "package_id": json.loads((package_path / "manifest.json").read_text())["packageId"], "description": description,
                      "placement": placement, "source_sha256": digest(source),
                      "package_model_sha256": digest(package_input), "embedded_textures": dependencies,
                      "triangles": inspection["triangleCount"], "meshes": inspection["meshCount"],
                      "surfaces": inspection["primitiveCount"], "materials": inspection["materialCount"],
                      "size_metres": inspection["boundingBox"]["sizeMeters"],
                      "bytes": package_input.stat().st_size, "source_bytes": source.stat().st_size, "preview": preview_relative,
                      "license": "CC0-1.0", "source_validation_passed": validation["passed"],
                      "warnings": inspection["warnings"], "runtime_integrated": False}
            write_json(BASE / "evidence" / f"{stable_id}.json",
                       {"inspection": inspection, "validation": validation, "package_verification": verification,
                        "original_source_sha256": digest(source), "embedded_textures": dependencies})
            records.append(record)
            print(f"{record['number']:03d} {stable_id}: {record['triangles']} triangles, verified", flush=True)
    write_json(BASE / "downloads.json", downloads)
    write_json(BASE / "manifest.json", {"date": "2026-10-03", "count": len(records), "assets": records})
    with (BASE / "asset_catalog.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["number", "id", "kind", "description", "placement", "triangles", "meshes", "surfaces",
                  "materials", "bytes", "model", "package", "license", "source_sha256"]
        writer = csv.DictWriter(f, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    assert len(records) >= 50
    assert len({r["source_sha256"] for r in records}) == len(records), "Duplicate source bytes"
    print(json.dumps({"count": len(records), "model_bytes": sum(r["bytes"] for r in records),
                      "max_triangles": max(r["triangles"] for r in records)}, indent=2))

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path

if __name__ == "__main__":
    main()
