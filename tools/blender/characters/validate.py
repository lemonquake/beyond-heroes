"""Re-import every exported GLB into a fresh Blender scene and check it against the contract.

blender -b --factory-startup --python validate.py            (or: build.py -- validate)
Writes work/lemondev/bh-002/evidence/characters/validation.txt and raises if a check fails.
Checks per hero: object named Armature, full skeleton + hierarchy, every library animation present (names from the glTF
JSON and the imported Blender actions), animation lengths == anim_meta.json lengths, triangle count 8k-25k, contract
material names only, skin weights reference deform bones only, height. Per weapon: tris 600-4000, length vs the
contract scale, origin at the grip, contract material names.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bh_skeleton as S  # noqa: E402
import bh_materials as MT  # noqa: E402

CONTRACT_MATS = set(MT.BASE)
HEROES = ("knight", "mage")
WEAPON_LEN = {"sword": 1.0, "greatsword": 1.6, "axe": 0.8, "spear": 2.2, "dagger": 0.4, "bow": 1.3, "staff": 1.8,
              "wand": 0.35, "shield": 0.9, "arrow": None, "sword_aether": 1.0, "greatsword_aether": 1.6,
              "staff_aether": 1.8, "wand_aether": 0.35}


def glb_json(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, ver, total = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "not a GLB"
    ln, typ = struct.unpack_from("<II", data, 12)
    return json.loads(data[20:20 + ln].decode("utf-8"))


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def check_hero(path, meta, required, lines):
    ok = True
    name = os.path.splitext(os.path.basename(path))[0]
    lines.append(f"== {name}.glb  ({os.path.getsize(path) / 1e6:.2f} MB)")
    js = glb_json(path)
    anims = [a["name"] for a in js.get("animations", [])]
    fresh()
    bpy.ops.import_scene.gltf(filepath=path)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    others = [o.name for o in bpy.context.scene.objects if o.type in ("CAMERA", "LIGHT")]

    def check(cond, msg):
        nonlocal ok
        lines.append(("  [ok]   " if cond else "  [FAIL] ") + msg)
        ok = ok and bool(cond)
    check(len(arms) == 1 and arms[0].name == "Armature", f"one armature object named 'Armature': {[a.name for a in arms]}")
    check(not others, f"no cameras/lights: {others}")
    arm = arms[0]
    bones = {b.name: b for b in arm.data.bones}
    missing = [b for b in S.BONE_ORDER if b not in bones]
    check(not missing, f"skeleton: {len(bones)} bones, contract bones missing: {missing}")
    bad_par = [b for b in S.BONE_ORDER if b in bones and S.PARENT[b] and
               (bones[b].parent is None or bones[b].parent.name != S.PARENT[b])]
    check(not bad_par, f"hierarchy matches contract (bad parents: {bad_par})")
    extra = sorted(set(bones) - set(S.BONE_ORDER))
    lines.append(f"  bones: {', '.join(S.BONE_ORDER)}")
    lines.append(f"  extra bones: {extra}")
    miss_a = [a for a in required if a not in anims]
    check(not miss_a, f"animations in glTF: {len(anims)} (library {len(required)}), missing: {miss_a}")
    unexpected = [a for a in anims if a not in required]
    check(not unexpected, f"no unexpected animations: {unexpected}")
    acts = [a.name for a in bpy.data.actions]
    check(len(acts) >= len(required), f"Blender actions after import: {len(acts)}")
    # lengths vs meta (glTF sampler input max)
    bad_len = []
    for a in js.get("animations", []):
        acc = js["accessors"][a["samplers"][0]["input"]]
        tmax = acc["max"][0]
        m = meta["animations"].get(a["name"])
        if m is None or abs(tmax - m["length"]) > 0.02:
            bad_len.append((a["name"], round(tmax, 3), m and m["length"]))
    check(not bad_len, f"animation lengths match anim_meta.json: mismatches {bad_len[:6]}")
    meta_missing = [a for a in required if a not in meta["animations"]]
    check(not meta_missing, f"anim_meta.json has every animation: missing {meta_missing}")
    t = sum(tris(m) for m in meshes)
    check(8000 <= t <= 25000, f"triangles: {t} (8k-25k)")
    mats = sorted({s.material.name for m in meshes for s in m.material_slots if s.material})
    check(set(mats) <= CONTRACT_MATS, f"materials: {mats}")
    check("BH_Aether" in mats, "uses BH_Aether (glowing aether channels)")
    zs = [(m.matrix_world @ Vector(c)).z for m in meshes for c in m.bound_box]
    lines.append(f"  height (rest bbox): {max(zs):.3f} m, min z {min(zs):.3f}")
    vg = sorted({g.name for m in meshes for g in m.vertex_groups})
    used = set()
    for m in meshes:
        names = {g.index: g.name for g in m.vertex_groups}
        for v in m.data.vertices:
            for ge in v.groups:
                if ge.weight > 1e-4:
                    used.add(names[ge.group])
    nd = sorted(g for g in used if g in S.DEFORM_EXCLUDE)
    check(not nd, f"skin weights on deform bones only ({len(used)} weighted bones; non-deform weighted: {nd})")
    col = any(len(m.data.color_attributes) for m in meshes)
    lines.append(f"  vertex colors (baked AO): {col}")
    lines.append(f"  animation names: {' '.join(anims)}")
    return ok, dict(tris=t, mats=mats, anims=len(anims))


def check_weapon(path, lines):
    ok = True
    name = os.path.splitext(os.path.basename(path))[0]
    fresh()
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    t = sum(tris(m) for m in meshes)
    mats = sorted({s.material.name for m in meshes for s in m.material_slots if s.material})
    P = [m.matrix_world @ Vector(c) for m in meshes for c in m.bound_box]
    xs, ys, zs = [p.x for p in P], [p.y for p in P], [p.z for p in P]
    L = max(zs) - min(zs)
    exp = WEAPON_LEN.get(name)
    good = 600 <= t <= 4000 and set(mats) <= CONTRACT_MATS and (exp is None or abs(L - exp) <= 0.08 * exp)
    good = good and min(zs) < 0 < max(zs)
    if name.endswith("_aether"):
        good = good and "BH_Aether" in mats
    ok = good
    lines.append(f"  [{'ok' if good else 'FAIL'}] {name:18s} tris {t:5d}  length(Z) {L:.3f} m (contract {exp})  "
                 f"X {min(xs):+.3f}..{max(xs):+.3f}  Y {min(ys):+.3f}..{max(ys):+.3f}  Z {min(zs):+.3f}..{max(zs):+.3f}"
                 f"  mats {mats}")
    return ok, dict(tris=t, length=round(L, 3), mats=mats)


def run(char_dir=None, wpn_dir=None, out=None):
    import bh_library as L
    char_dir = char_dir or os.path.join(ROOT, "game", "assets", "characters")
    wpn_dir = wpn_dir or os.path.join(ROOT, "game", "assets", "weapons")
    out = out or os.path.join(ROOT, "work", "lemondev", "bh-002", "evidence", "characters", "validation.txt")
    meta = json.load(open(os.path.join(char_dir, "anim_meta.json")))
    required = [a.name for a in L.library()]
    assert set(L.REQUIRED) <= set(required)
    lines = ["Beyond Heroes C6 validation (Blender re-import of the exported GLBs into a fresh scene)",
             f"Blender {bpy.app.version_string}; library: {len(required)} animations; "
             f"contract list: {len(L.REQUIRED)} names", ""]
    all_ok = True
    summary = {}
    for h in HEROES:
        p = os.path.join(char_dir, h + ".glb")
        if not os.path.exists(p):
            lines.append(f"== {h}.glb  [FAIL] missing")
            all_ok = False
            continue
        ok, s = check_hero(p, meta, required, lines)
        summary[h] = s
        all_ok &= ok
        lines.append("")
    lines.append("== weapons")
    for w in WEAPON_LEN:
        p = os.path.join(wpn_dir, w + ".glb")
        if not os.path.exists(p):
            lines.append(f"  [FAIL] {w}.glb missing")
            all_ok = False
            continue
        ok, s = check_weapon(p, lines)
        summary[w] = s
        all_ok &= ok
    lines.append("")
    lines.append("RESULT: " + ("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("[validate] ->", out)
    return all_ok, summary


if __name__ == "__main__":
    ok, _ = run()
    if not ok:
        sys.exit(1)
