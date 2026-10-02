"""bh-033: inspect every downloaded glTF/GLB: triangles, materials, textures (size), bounds (m), skin/joints, animations."""
import json, os, struct, sys, hashlib
ROOT = os.path.dirname(os.path.abspath(__file__))

def load(path):
    data = open(path, "rb").read()
    if path.lower().endswith(".glb"):
        ln = struct.unpack_from("<I", data, 12)[0]
        return json.loads(data[20:20 + ln]), data
    return json.loads(data.decode("utf-8")), data

def png_size(path):
    try:
        with open(path, "rb") as f:
            h = f.read(32)
        if h[:8] == b"\x89PNG\r\n\x1a\n":
            return list(struct.unpack(">II", h[16:24]))
        if h[:2] == b"\xff\xd8":
            d = open(path, "rb").read()
            i = 2
            while i < len(d):
                if d[i] != 0xFF: break
                m = d[i + 1]; ln = struct.unpack(">H", d[i + 2:i + 4])[0]
                if m in (0xC0, 0xC2):
                    hgt, w = struct.unpack(">HH", d[i + 5:i + 9]); return [w, hgt]
                i += 2 + ln
    except Exception:
        pass
    return None

def inspect(path):
    g, raw = load(path)
    acc = g.get("accessors", [])
    tris = 0; lo = [1e9] * 3; hi = [-1e9] * 3
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            if "indices" in p:
                tris += acc[p["indices"]]["count"] // 3
            else:
                tris += acc[p["attributes"]["POSITION"]]["count"] // 3
            a = acc[p["attributes"]["POSITION"]]
            if "min" in a:
                lo = [min(lo[i], a["min"][i]) for i in range(3)]; hi = [max(hi[i], a["max"][i]) for i in range(3)]
    # apply root node scale if present (Quaternius exports often scale at the node)
    scale = 1.0
    for n in g.get("nodes", []):
        if "scale" in n and n.get("mesh") is None and n.get("children"):
            scale = n["scale"][0]; break
    imgs = []
    for im in g.get("images", []):
        if "uri" in im and not im["uri"].startswith("data:"):
            imgs.append([im["uri"], png_size(os.path.join(os.path.dirname(path), im["uri"]))])
        else:
            imgs.append(["embedded", None])
    return {"file": os.path.relpath(path, ROOT).replace("\\", "/"), "triangles": tris, "materials": len(g.get("materials", [])),
        "textures": imgs, "size_m": [round((hi[i] - lo[i]) * scale, 3) for i in range(3)] if tris else None,
        "skins": len(g.get("skins", [])), "joints": sum(len(s.get("joints", [])) for s in g.get("skins", [])),
        "animations": [a.get("name", "") for a in g.get("animations", [])], "sha256": hashlib.sha256(raw).hexdigest()}

out = []
for base, _, files in os.walk(ROOT):
    for f in files:
        if f.lower().endswith((".gltf", ".glb")) and "preview_project" not in base:
            try:
                out.append(inspect(os.path.join(base, f)))
            except Exception as e:
                out.append({"file": os.path.join(base, f), "error": str(e)})
json.dump(out, open(os.path.join(ROOT, "inspection.json"), "w"), indent=1)
print(len(out), "models inspected")
