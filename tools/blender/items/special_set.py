"""bh-026: the Ember Dragon set — item models and icons from the sculpts in models/special_weapons/.

  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --factory-startup --python tools/blender/items/special_set.py -- [models] [icons]

  ember_dragonslayer   dragonforge_ember_dragonslayer.obj   sword: hand-socket convention (origin at the grip centre,
                                                            blade along +Z, flats +-Y), GRIP_TOTAL long
  aegis_of_fragnir     dragonforge_aegis_of_fragnir.zip     shield: face -Y, handle at the origin, SHIELD_HEIGHT tall;
                                                            the 1.9 M-triangle sculpt reduced to SHIELD_TRIS
  ember_dragonhide     dragonforge_ember_dragonhide.obj     the cuirass as fitted to the hero in the idle pose
                                                            (tools/blender/hero/hero_wear_special.py), origin at the
                                                            chest joint so a Tempo can wear the same model on its chest

The sword and the shield keep the sculpts' painted colours as vertex colours; their material is BH_Baked__it_<id>,
which the game draws with the vertex colour as albedo (MaterialLibrary). The cuirass uses the worn piece's two palettes
(dragon-scale plates, bronze trim). Icons: 256 px studio renders (build_items._studio / _pose_for) composed into the
128 px game icons (icons_post.game_icon) at game/assets/ui/icons/items3d/<id>.png.
"""
import math
import os
import sys
import tempfile
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
HERO = os.path.join(ROOT, "tools", "blender", "hero")
for _p in (HERE, HERO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_items as BI  # noqa: E402
import item_kit as K  # noqa: E402
import hero_wear_kit as WK  # noqa: E402
import hero_wear_special as HS  # noqa: E402

SRC = os.path.join(ROOT, "models", "special_weapons")
OUT_DIR = os.path.join(ROOT, "game", "assets", "items")
ICON_RAW = os.path.join(ROOT, "work", "lemondev", "bh-026", "scratch", "icons_raw")

GRIP_TOTAL = 1.12          # sword, pommel to tip (m)
SHIELD_HEIGHT = 0.84       # shield, top to bottom (m): the boss shields are 0.76, the heaters 0.9
SHIELD_TRIS = 12000
SHIELD_BACK = -0.028       # where the middle of the shield's back sits (y; the forearm is behind, +Y)

ITEMS = {
    "ember_dragonslayer": {"category": "weapon", "weapon_type": "sword"},
    "aegis_of_fragnir": {"category": "shield", "weapon_type": ""},
    "ember_dragonhide": {"category": "armor", "weapon_type": ""},
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _import_obj(path):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=path)
    ob = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


def _decimate(ob, tris):
    have = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if have <= tris:
        return
    mod = ob.modifiers.new("reduce", "DECIMATE")
    mod.ratio = tris / have * 0.99
    mod.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


def _verts(ob):
    V = np.zeros(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", V)
    return V.reshape(-1, 3)


def _set_verts(ob, V):
    ob.data.vertices.foreach_set("co", np.asarray(V, float).ravel())
    ob.data.update()


def _baked_material(ob, iid):
    """BH_Baked__it_<id>: the painted colours ride the vertex colour (exported as COLOR_0)."""
    m = bpy.data.materials.new("BH_Baked__it_" + iid)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = ob.data.color_attributes[0].name
    nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.35
    bsdf.inputs["Roughness"].default_value = 0.45
    ob.data.materials.clear()
    ob.data.materials.append(m)
    ob.data.color_attributes.active_color = ob.data.color_attributes[0]
    for p in ob.data.polygons:
        p.use_smooth = True


# ---- the three pieces -------------------------------------------------------------------------------------------------
def dragonslayer():
    ob = _import_obj(os.path.join(SRC, "dragonforge_ember_dragonslayer.obj"))
    ob.name = "ember_dragonslayer"
    V = _verts(ob)
    V = V * np.array([-1.0, 1.0, -1.0])                 # the sculpt's tip points down: turn it tip up, flats stay +-Y
    lo, hi = V.min(0), V.max(0)
    V = (V - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * (GRIP_TOTAL / (hi[2] - lo[2]))
    # the grip: the longest run of narrow slices in the lower third (between pommel and guard)
    zs = np.arange(0.0, GRIP_TOTAL * 0.34, 0.008)
    width = np.array([np.ptp(V[np.abs(V[:, 2] - z) < 0.006, 0]) if (np.abs(V[:, 2] - z) < 0.006).sum() > 2 else 9.0
                      for z in zs])
    narrow = width < max(0.05, np.median(width[width < 9.0]) * 0.9)
    best, run, start = (0, 0), 0, 0
    for i, n in enumerate(narrow):
        if n:
            if run == 0:
                start = i
            run += 1
            if run > best[1] - best[0]:
                best = (start, i + 1)
        else:
            run = 0
    g0, g1 = zs[best[0]], zs[max(best[1] - 1, best[0])]
    grip = 0.5 * (g0 + g1)
    print("[special] dragonslayer grip %.3f..%.3f m from the pommel" % (g0, g1))
    V[:, 2] -= grip
    _set_verts(ob, V)
    _baked_material(ob, "ember_dragonslayer")
    return ob


def aegis():
    tmp = tempfile.mkdtemp(prefix="bh026_")
    with zipfile.ZipFile(os.path.join(SRC, "dragonforge_aegis_of_fragnir.zip")) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".obj"))
        z.extract(name, tmp)
    ob = _import_obj(os.path.join(tmp, name))
    ob.name = "aegis_of_fragnir"
    _decimate(ob, SHIELD_TRIS)
    V = _verts(ob)
    lo, hi = V.min(0), V.max(0)
    V = (V - np.array([(lo[0] + hi[0]) / 2, 0.0, (lo[2] + hi[2]) / 2])) * (SHIELD_HEIGHT / (hi[2] - lo[2]))
    V[:, 2] -= 0.04                                     # the handle a little above the middle, as on the heaters
    mid = (np.abs(V[:, 0]) < 0.10) & (np.abs(V[:, 2] + 0.04) < 0.12)
    V[:, 1] += SHIELD_BACK - float(V[mid, 1].max())
    _set_verts(ob, V)
    _baked_material(ob, "aegis_of_fragnir")
    return ob


def dragonhide():
    h = HS.dragonhide()
    scale_m, trim_m = HS.palettes()
    chest = np.array(WK.J["chest"][0], float)
    V = h["posed"] - chest
    mats = K.make_materials([scale_m, trim_m])
    me = bpy.data.meshes.new("ember_dragonhide")
    me.from_pydata(V.tolist(), [], h["F"])
    me.validate()
    me.materials.append(mats[scale_m])
    me.materials.append(mats[trim_m])
    me.polygons.foreach_set("material_index", [1 if t else 0 for t in h["trim"]][:len(me.polygons)])
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(42.0))
    except Exception:
        pass
    ob = bpy.data.objects.new("ember_dragonhide", me)
    bpy.context.scene.collection.objects.link(ob)
    WK.box_uv(ob)
    return ob


BUILDERS = {"ember_dragonslayer": dragonslayer, "aegis_of_fragnir": aegis, "ember_dragonhide": dragonhide}


def models(ids):
    from build import export_glb
    os.makedirs(OUT_DIR, exist_ok=True)
    for iid in ids:
        reset()
        HS._CACHE.clear()
        ob = BUILDERS[iid]()
        export_glb(os.path.join(OUT_DIR, iid + ".glb"), [ob], animations=False)
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        lo = np.array([min(v[i] for v in ob.bound_box) for i in range(3)])
        hi = np.array([max(v[i] for v in ob.bound_box) for i in range(3)])
        print("[special] %-20s %6d tris  %.3f x %.3f x %.3f m" % (iid, tris, *(hi - lo)))


def icons(ids):
    os.makedirs(ICON_RAW, exist_ok=True)
    for iid in ids:
        reset()
        HS._CACHE.clear()
        ob = BUILDERS[iid]()
        if ob.data.color_attributes:
            # EEVEE draws the vertex colours through the material's node; nothing else to do
            pass
        cam = BI._studio()
        pitch, yaw = BI._pose_for(dict(ITEMS[iid], id=iid), ob)
        bpy.context.view_layer.update()
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        ob.location -= sum(bb, Vector()) / 8.0
        bpy.context.view_layer.update()
        p, y = math.radians(pitch), math.radians(yaw)
        d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
        cam.location = d * 10.0
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        pts = [inv @ (ob.matrix_world @ Vector(v.co)) for v in ob.data.vertices]
        ext = max(max(q.x for q in pts) - min(q.x for q in pts), max(q.y for q in pts) - min(q.y for q in pts))
        cam.data.ortho_scale = ext * 1.08
        cx = (max(q.x for q in pts) + min(q.x for q in pts)) / 2
        cy = (max(q.y for q in pts) + min(q.y for q in pts)) / 2
        cam.location = cam.matrix_world @ Vector((cx, cy, 0.0))
        cam.data.clip_start = 0.01
        cam.data.clip_end = 100
        raw = os.path.join(ICON_RAW, iid + ".png")
        bpy.context.scene.render.filepath = raw
        bpy.ops.render.render(write_still=True)
        print("[special] icon", iid)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    targets = [a for a in argv if a in ("models", "icons")] or ["models", "icons"]
    ids = [a for a in argv if a in BUILDERS] or list(BUILDERS)
    if "models" in targets:
        models(ids)
    if "icons" in targets:
        icons(ids)


if __name__ == "__main__":
    main()
