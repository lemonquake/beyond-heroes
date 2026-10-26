"""Copy the selected WOA bodies, retaining geometry and clips, with 1024px maps.

Run from the repository root. Source files are read only. The generated manifest
records both source and output hashes, triangle counts, and embedded map sizes.
"""
from pathlib import Path
import hashlib
import io
import json
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("A:/Python/woa/assets/characters/heroes17")
DEST = ROOT / "game/assets/characters/roles"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def port(name):
    raw = (SOURCE / f"{name}.glb").read_bytes()
    json_size = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + json_size])
    binary_start = 20 + json_size + 8
    binary = raw[binary_start:]
    image_views = {i["bufferView"] for i in doc.get("images", [])}
    chunks = bytearray()
    sizes = []
    for index, view in enumerate(doc["bufferViews"]):
        start = view.get("byteOffset", 0)
        data = binary[start:start + view["byteLength"]]
        if index in image_views:
            image = Image.open(io.BytesIO(data))
            before = list(image.size)
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            image.save(output, format="PNG", optimize=True)
            data = output.getvalue()
            sizes.append({"before": before, "after": list(image.size)})
        while len(chunks) % 4:
            chunks.append(0)
        view["byteOffset"] = len(chunks)
        view["byteLength"] = len(data)
        chunks.extend(data)
    doc["buffers"][0]["byteLength"] = len(chunks)
    while len(chunks) % 4:
        chunks.append(0)
    encoded = json.dumps(doc, separators=(",", ":")).encode()
    encoded += b" " * ((-len(encoded)) % 4)
    result = (struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(encoded) + 8 + len(chunks))
              + struct.pack("<I4s", len(encoded), b"JSON") + encoded
              + struct.pack("<I4s", len(chunks), b"BIN\0") + chunks)
    (DEST / f"{name}.glb").write_bytes(result)
    triangles = sum(doc["accessors"][p["indices"]]["count"] // 3
                    for m in doc["meshes"] for p in m["primitives"])
    return {"source": str(SOURCE / f"{name}.glb"), "source_sha256": digest(raw),
            "output_sha256": digest(result), "bytes": len(result),
            "triangles": triangles, "animations": len(doc.get("animations", [])),
            "maps": sizes}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {name: port(name) for name in ["emelrich", "azrin", "caziel"]}
    shared = (ROOT / "game/assets/characters/hero.glb").read_bytes()
    source_hero = Path("A:/Python/woa/assets/characters/hero/hero.glb").read_bytes()
    assert shared == source_hero, "Shared Blood Ranger body changed; review before porting"
    manifest["blood_ranger"] = {"source": "A:/Python/woa/assets/characters/hero/hero.glb",
                                "shared": "res://assets/characters/hero.glb",
                                "sha256": digest(shared), "bytes": len(shared)}
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
