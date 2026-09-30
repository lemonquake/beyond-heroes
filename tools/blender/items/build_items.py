"""Beyond Heroes item models (bh-006): one GLB per item base + icon renders.

  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --factory-startup --python build_items.py -- [targets] [ids...]
targets: models (default) | icons | all ; optional item ids restrict the run.

Reads items.json (written by game/tests/tools/dump_items.tscn), builds each base with the builder registered in
item_weapons.SPECS / item_gear.GEAR / item_goods.GOODS and exports res://assets/items/<id>.glb (+ gold_pile.glb).
`icons` renders a transparent 256 px studio shot of every model to work/lemondev/bh-006/evidence/icons/raw/; the
icon compositor (icons_post.py, system Python + PIL) turns those into the game icons.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT_DIR = os.path.join(ROOT, "game", "assets", "items")
EVID_DIR = os.environ.get("BH_ITEM_EVIDENCE", os.path.join(ROOT, "work", "lemondev", "bh-006", "evidence"))
RAW_DIR = os.path.join(EVID_DIR, "icons", "raw")

import bpy  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

import item_kit as K  # noqa: E402
from item_kit import M  # noqa: E402
import item_weapons as IW  # noqa: E402
import artisan_weapons as AW  # noqa: E402
import item_gear as IG  # noqa: E402
import item_goods as IGo  # noqa: E402
import item_crystals as IC  # noqa: E402  (bh-018 socket crystals; not in items.json)

sys.path.insert(0, K.CHARS)
from build import export_glb, reset  # noqa: E402

# Fallback builders per weapon type / category for any base without an explicit spec.
TYPE_FALLBACK = {
    "sword": (IW.sword, {}), "greatsword": (IW.sword, {"len": 1.18, "z0": 0.135, "guard_half": 0.18, "grip_len": 0.32}),
    "axe": (IW.axe, {}), "greataxe": (IW.axe, {"two_handed": True}), "spear": (IW.spear, {}), "javelin": (IW.javelin, {}),
    "club": (IW.club, {}), "dagger": (IW.dagger, {}), "claw": (IW.claw, {}), "knuckles": (IW.knuckles, {}), "bow": (IW.bow, {}),
    "staff": (IW.staff, {}), "wand": (IW.wand, {}),
}


with open(os.path.join(HERE, "depth_specs.json"), encoding="utf-8") as f:
    DEPTH_SPECS = json.load(f)


def spec_for(item):
    iid = item["id"]
    if iid in AW.SPECS:
        fn, spec = AW.SPECS[iid]
        return fn, dict(spec), False
    if iid in DEPTH_SPECS:
        name, spec = DEPTH_SPECS[iid]
        return getattr(IW, name, None) or getattr(IG, name), dict(spec), False
    for table in (IW.SPECS, IG.GEAR, IGo.GOODS):
        if iid in table:
            fn, s = table[iid]
            return fn, dict(s), False
    if item.get("category") == "weapon" and item.get("weapon_type") in TYPE_FALLBACK:
        fn, s = TYPE_FALLBACK[item["weapon_type"]]
        return fn, dict(s), True
    return None, None, True


def build_parts(item):
    if item["id"].startswith("boss_") and item["id"].endswith(("_main_weapon", "_sub_weapon")):
        import boss_weapons
        if item["id"] in boss_weapons.SPECS:
            fn, theme = boss_weapons.SPECS[item["id"]]
            return fn(theme), False
    if IC.is_crystal(item["id"]):
        return IC.build_parts(item["id"]), False
    fn, s, fallback = spec_for(item)
    if fn is None:
        raise KeyError(f"no builder for {item['id']}")
    el = int(item.get("element", 0))
    if item.get("category") == "weapon" and "glow" not in s and el and float(item.get("element_share", 0)) > 0 and fn is not IW.bow:
        s["glow"] = K.ELEMENT_GLOW.get(el)
    parts = fn(s)
    return parts, fallback


def build_object(iid, parts):
    if IC.is_crystal(iid):
        return IC.build_object(iid, parts)
    for p in parts:
        try:
            M.recalc_normals(p)
        except Exception:
            pass
    keys = sorted({p.mat for p in parts})
    mats = K.make_materials(keys)
    return M.build_static(iid, parts, mats, sharp_angle=40.0)


def load_items(ids=None):
    with open(os.path.join(HERE, "items.json"), encoding="utf-8") as f:
        items = json.load(f)
    known = {it["id"] for it in items}
    items.extend(it for it in AW.MANIFEST if it["id"] not in known)
    items.append({"id": "gold_pile", "category": "gold", "weapon_type": "", "element": 0})
    if ids and all(i == "crystals" or IC.is_crystal(i) for i in ids):   # crystals only ("crystals" = all 32)
        return IC.items(None if "crystals" in ids else ids)
    if ids:
        items = [it for it in items if it["id"] in ids]
    return items


def export_models(items, log=print):
    os.makedirs(OUT_DIR, exist_ok=True)
    report = []
    for it in items:
        reset()
        parts, fb = build_parts(it)
        ob = build_object(it["id"], parts)
        path = os.path.join(OUT_DIR, it["id"] + ".glb")
        export_glb(path, [ob], animations=False)
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        size = [max(v[i] for v in bb) - min(v[i] for v in bb) for i in range(3)]
        tris = M.tri_count(ob)
        report.append({"id": it["id"], "tris": tris, "size": [round(x, 3) for x in size], "fallback": fb})
        log(f"[item] {it['id']:28s} {tris:6d} tris  size {size[0]:.3f} x {size[1]:.3f} x {size[2]:.3f}{'  (fallback builder)' if fb else ''}")
    rp = IC.REPORT if report and all(IC.is_crystal(r["id"]) for r in report) else os.path.join(EVID_DIR, "models_report.json")
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    return report


# ---- icon renders ------------------------------------------------------------------------------------------------------

def _studio(res=256):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.film_transparent = True
    try:
        sc.eevee.taa_render_samples = 32
    except Exception:
        pass
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Punchy", "AgX - Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except Exception:
            continue
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.32, 0.3, 0.34, 1)
    bg.inputs[1].default_value = 0.9
    for name, loc, energy, color, size in (
            ("Key", (-2.2, -3.2, 3.6), 520, (1.0, 0.9, 0.78), 2.2),
            ("Rim", (2.6, 2.6, 2.4), 700, (0.6, 0.75, 1.0), 1.6),
            ("Fill", (3.0, -2.6, 0.6), 160, (0.85, 0.85, 0.95), 3.0)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        d = Vector((0, 0, 0)) - lo.location
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.type = "ORTHO"
    return cam


LAY_FLAT = set()


def _pose_for(item, ob):
    """Orient the object for its icon: weapons diagonal (bottom-left grip, top-right tip), flats to the camera."""
    cat = item.get("category")
    wt = item.get("weapon_type", "")
    ob.rotation_mode = "XYZ"
    if cat == "weapon":
        if wt == "bow":
            ob.rotation_euler = (0, math.radians(-40), math.radians(180))
        elif wt == "crossbow":
            ob.rotation_euler = (math.radians(18), math.radians(35), math.radians(-8))
        elif wt == "claw":
            ob.rotation_euler = (0, math.radians(40), 0)
        elif wt == "knuckles":
            ob.rotation_euler = (math.radians(10), math.radians(35), math.radians(15))
        else:
            ob.rotation_euler = (0, math.radians(45), 0)
        return 8.0, 0.0      # camera pitch, yaw
    if cat == "shield":
        ob.rotation_euler = (0, math.radians(-12), math.radians(8))
        return 10.0, 0.0
    if cat in LAY_FLAT or item["id"] in ("bone_amulet", "gold_amulet", "star_pendant", "u_heart_of_aether", "rune_charm", "war_talisman"):
        return 58.0, 12.0
    if cat in ("helm", "boots"):
        return 16.0, 28.0
    if cat in ("armor", "inner_garment", "gloves", "leggings"):
        return 10.0, 18.0
    if cat == "accessory":
        return 18.0, 20.0
    return 24.0, 22.0


def render_icons(items, log=print):
    os.makedirs(RAW_DIR, exist_ok=True)
    for it in items:
        reset()
        parts, _ = build_parts(it)
        ob = build_object(it["id"], parts)
        cam = _studio()
        pitch, yaw = _pose_for(it, ob)
        bpy.context.view_layer.update()
        # centre the model on the origin
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        c = sum(bb, Vector()) / 8.0
        ob.location -= c
        bpy.context.view_layer.update()
        p, y = math.radians(pitch), math.radians(yaw)
        d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
        cam.location = d * 10.0
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        # ortho scale from the projected bounds
        inv = cam.matrix_world.inverted()
        pts = [inv @ (ob.matrix_world @ Vector(cc)) for cc in ob.bound_box]
        ext = max(max(q.x for q in pts) - min(q.x for q in pts), max(q.y for q in pts) - min(q.y for q in pts))
        cam.data.ortho_scale = ext * 1.12
        cx = (max(q.x for q in pts) + min(q.x for q in pts)) / 2
        cy = (max(q.y for q in pts) + min(q.y for q in pts)) / 2
        cam.location = cam.matrix_world @ Vector((cx, cy, 0.0))
        cam.data.clip_start = 0.01
        cam.data.clip_end = 100
        bpy.context.scene.render.filepath = os.path.join(RAW_DIR, it["id"] + ".png")
        bpy.ops.render.render(write_still=True)
        log(f"[icon] {it['id']}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    targets = [a for a in argv if a in ("models", "icons", "all")] or ["models"]
    ids = [a for a in argv if a not in ("models", "icons", "all")]
    items = load_items(ids)
    t0 = time.time()
    if "models" in targets or "all" in targets:
        export_models(items)
    if "icons" in targets or "all" in targets:
        cr = [it["id"] for it in items if IC.is_crystal(it["id"])]
        if cr:
            IC.render_icons(cr)
        render_icons([it for it in items if not IC.is_crystal(it["id"])])
    print(f"[build_items] {len(items)} items done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
