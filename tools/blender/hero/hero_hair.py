"""bh-023: the hero's hair and beard models (game/assets/characters/hero/hair/*.glb, .../beard/*.glb).

  blender -b --factory-startup --python tools/blender/hero/hero_hair.py -- all
  blender -b --factory-startup --python tools/blender/hero/hero_hair.py -- crop beard/long hair/long ...
  blender -b --factory-startup --python tools/blender/hero/hero_hair.py -- preview [ids]   (renders on the hero)
  blender -b --factory-startup --python tools/blender/hero/hero_hair.py -- verify [ids]    (re-imports the GLBs)
  python tools/blender/hero/hero_hair_sheets.py [ids]                                      (contact sheets, PIL)

Ids are `hair/<id>` or `beard/<id>`; a bare id selects every model of that name (`long` is both a hair and a beard).

Each GLB is one static mesh in the hero's model space (metres, Z up, facing -Y; exported Y up), material
`BH_HeroHair`, a point colour attribute `Col` (R = sway 0 at the roots .. 1 at free tips, G = clump shade 0.35..1,
B = 0, A = 1) and a shape key `length` (the game drives it 0..4).  The shapes live in hero_hair_styles.py (hair) and
hero_hair_beards.py (beards), on top of hero_hair_kit.py; they are fitted to the surface the body export writes to
work/lemondev/bh-023/scratch/hero_mesh.npz, so run `hero_body.py -- export` first.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.abspath(os.path.join(HERE, "..", "characters"))
for p in (HERE, CHARS):
    if p not in sys.path:
        sys.path.insert(0, p)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT_DIR = os.path.join(ROOT, "game", "assets", "characters", "hero")
SCRATCH = os.path.join(ROOT, "work", "lemondev", "bh-023", "scratch", "hair")
TILES = os.path.join(SCRATCH, "tiles")

import bpy  # noqa: E402

import hero_hair_beards as BD  # noqa: E402
import hero_hair_kit as K  # noqa: E402
import hero_hair_styles as ST  # noqa: E402

HAIR = ["crop", "sidepart", "slick", "spiky", "mohawk", "long", "ponytail", "topknot", "braids", "pigtails", "curly",
        "bowl", "tonsure", "wild"]
BEARD = ["moustache", "handlebar", "goatee", "full", "long", "chops", "braided"]
BUDGET = {"hair": 1800, "beard": 900}
MAT_NAME = "BH_HeroHair"
LENGTHS = (0.0, 1.0, 4.0)


def all_keys():
    return [("hair", i) for i in HAIR] + [("beard", i) for i in BEARD]


def parse_keys(args):
    out = []
    for a in args:
        if "/" in a:
            kind, i = a.split("/", 1)
            if (kind, i) not in all_keys():
                raise SystemExit("unknown id %s" % a)
            out.append((kind, i))
        else:
            hit = [k for k in all_keys() if k[1] == a]
            if not hit:
                raise SystemExit("unknown id %s" % a)
            out.extend(hit)
    return out or all_keys()


def build(kind, name, head):
    """-> K.HairMesh of one style (a fixed seed per style: the same model every run)."""
    seed = (HAIR if kind == "hair" else BEARD).index(name) + (100 if kind == "beard" else 0)
    rng = np.random.default_rng(1000 + seed)
    fn = getattr(ST if kind == "hair" else BD, name.replace("long", "long_"))
    return fn(head, rng)


def material():
    mat = bpy.data.materials.get(MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(MAT_NAME)
        mat.use_nodes = True
        b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (0.30, 0.19, 0.11, 1.0)
        b.inputs["Roughness"].default_value = 0.62
        b.inputs["Metallic"].default_value = 0.0
        mat.diffuse_color = (0.30, 0.19, 0.11, 1.0)
        mat.roughness = 0.62
    return mat


def make_object(name, hm, mat=None):
    V, F, R, G, D = hm.arrays()
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F)
    me.validate(clean_customdata=False)
    if len(me.vertices) != len(V):
        raise RuntimeError("%s: validate() changed the vertex count" % name)
    me.shade_smooth()
    col = me.attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    rgba = np.stack([R, G, np.zeros(len(V)), np.ones(len(V))], 1)
    col.data.foreach_set("color", rgba.ravel())
    me.color_attributes.active_color = me.color_attributes["Col"]
    me.color_attributes.render_color_index = me.color_attributes.find("Col")
    me.materials.append(mat or material())
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.shape_key_add(name="Basis")
    kb = ob.shape_key_add(name="length")
    kb.data.foreach_set("co", (V + D).ravel())
    kb.slider_min, kb.slider_max = 0.0, 4.0
    kb.value = 0.0
    return ob


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def export_glb(ob, path):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
        export_animations=False, export_morph=True, export_morph_normal=True, export_vertex_color="ACTIVE",
        export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True, export_tangents=False,
        export_cameras=False, export_lights=False)


def glb_path(kind, name):
    return os.path.join(OUT_DIR, kind, name + ".glb")


def stats(hm):
    V, F, R, G, D = hm.arrays()
    return dict(tris=hm.tris(), verts=len(V), lo=V.min(0), hi=V.max(0), lo4=(V + 4 * D).min(0),
                hi4=(V + 4 * D).max(0), rmax=float(R.max()), gmin=float(G.min()), gmax=float(G.max()))


def export_all(keys):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    head = K.Head()
    bad = []
    for kind, name in keys:
        hm = build(kind, name, head)
        s = stats(hm)
        ob = make_object("%s_%s" % (kind, name), hm)
        export_glb(ob, glb_path(kind, name))
        over = s["tris"] > BUDGET[kind]
        if over:
            bad.append("%s/%s" % (kind, name))
        print("[hair] %-16s %4d tris %4d verts  bbox (%.3f %.3f %.3f)..(%.3f %.3f %.3f)  at length 4 z %.2f..%.2f"
              "  sway max %.2f  shade %.2f..%.2f%s"
              % ("%s/%s" % (kind, name), s["tris"], s["verts"], *s["lo"], *s["hi"], s["lo4"][2], s["hi4"][2],
                 s["rmax"], s["gmin"], s["gmax"], "   OVER BUDGET" if over else ""))
        bpy.data.objects.remove(ob)
    if bad:
        print("[hair] OVER BUDGET:", ", ".join(bad))


def verify(keys):
    """Re-import each exported GLB and report what the game will find in it."""
    ok_all = True
    for kind, name in keys:
        path = glb_path(kind, name)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if not os.path.exists(path):
            print("[verify] %s/%s MISSING %s" % (kind, name, path))
            ok_all = False
            continue
        bpy.ops.import_scene.gltf(filepath=path)
        obs = list(bpy.context.scene.objects)
        meshes = [o for o in obs if o.type == "MESH"]
        arms = [o for o in obs if o.type == "ARMATURE"]
        o = meshes[0]
        me = o.data
        mw = np.array(o.matrix_world)
        V = np.array([v.co[:] for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
        mats = [m.name for m in me.materials]
        cols = [(a.name, a.domain, a.data_type) for a in me.color_attributes]
        keys_ = [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else []
        tris = tri_count(me)
        col_ok = False
        rng_txt = ""
        if "Col" in me.color_attributes:
            a = me.color_attributes["Col"]
            c = np.zeros(len(a.data) * 4)
            a.data.foreach_get("color", c)
            c = c.reshape(-1, 4)
            col_ok = True
            rng_txt = "R %.2f..%.2f G %.2f..%.2f B %.2f..%.2f A %.2f..%.2f" % (
                c[:, 0].min(), c[:, 0].max(), c[:, 1].min(), c[:, 1].max(), c[:, 2].min(), c[:, 2].max(),
                c[:, 3].min(), c[:, 3].max())
        dmax = 0.0
        if "length" in keys_:
            kb = me.shape_keys.key_blocks["length"]
            co = np.zeros(len(me.vertices) * 3)
            kb.data.foreach_get("co", co)
            b = np.array([v.co[:] for v in me.vertices])
            dmax = float(np.linalg.norm(co.reshape(-1, 3) - b, axis=1).max())
        ok = (len(meshes) == 1 and not arms and mats == [MAT_NAME] and col_ok and keys_ == ["Basis", "length"]
              and tris <= BUDGET[kind] and dmax > 0.005)
        ok_all &= ok
        print("[verify] %-16s %s  meshes %d armatures %d  materials %s  colour %s (%s)  keys %s (max |d| %.3f)"
              "  tris %d/%d  bbox (%.3f %.3f %.3f)..(%.3f %.3f %.3f)"
              % ("%s/%s" % (kind, name), "OK " if ok else "BAD", len(meshes), len(arms), mats, cols, rng_txt, keys_,
                 dmax, tris, BUDGET[kind], *V.min(0), *V.max(0)))
    print("[verify] %s" % ("all OK" if ok_all else "PROBLEMS FOUND"))


# ---- preview ---------------------------------------------------------------------------------------------------------

def _preview_hair_material():
    """Brown, shaded by the clump value (Col.g) as the game does, single sided so flipped faces show as holes."""
    mat = bpy.data.materials.new("hair_preview")
    mat.use_nodes = True
    nt = mat.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    att = nt.nodes.new("ShaderNodeAttribute")
    att.attribute_name = "Col"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(att.outputs["Color"], sep.inputs[0])
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    mul.inputs[0].default_value = (0.42, 0.25, 0.13)
    nt.links.new(sep.outputs[1], mul.inputs["Scale"])
    nt.links.new(mul.outputs["Vector"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    mat.use_backface_culling = True
    return mat


VIEWS = {
    # name: (camera offset direction, target, ortho scale)
    "hair": [("front", (0, -1, 0), (0, -0.03, 1.685), 0.52), ("q34", (0.62, -1, 0.16), (0, -0.03, 1.685), 0.52),
             ("side", (1, 0, 0), (0, -0.0, 1.685), 0.52), ("back", (0, 1, 0), (0, -0.03, 1.685), 0.52),
             ("iso", (0.45, -0.65, 1.0), (0, -0.03, 1.70), 0.52),
             ("bodyf", (0.62, -1, 0.12), (0, 0, 1.15), 2.9), ("bodyb", (0.8, 0.75, 0.12), (0, 0, 1.15), 2.9)],
    "beard": [("front", (0, -1, 0), (0, -0.05, 1.60), 0.40), ("q34", (0.62, -1, 0.16), (0, -0.05, 1.60), 0.40),
              ("side", (1, 0, 0), (0, -0.06, 1.60), 0.40), ("low", (0.3, -1, -0.55), (0, -0.06, 1.59), 0.40),
              ("iso", (0.45, -0.65, 1.0), (0, -0.05, 1.63), 0.46),
              ("bodyf", (0.62, -1, 0.12), (0, 0, 1.15), 2.9), ("bodys", (1, -0.05, 0.05), (0, 0, 1.15), 2.9)],
}


def preview(keys, tile=300):
    import hero_body as HB
    r = HB.build_body()
    HB._preview_material(r["ob"])
    shot = HB._stage()
    sc = bpy.context.scene
    try:
        sc.eevee.taa_render_samples = 16
    except Exception:
        pass
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
    sc.collection.objects.link(fill)
    fill.data.energy = 1.6
    fill.rotation_euler = (math.radians(-55), 0, math.radians(-20))
    os.makedirs(TILES, exist_ok=True)
    head = K.Head()
    mat = _preview_hair_material()
    for kind, name in keys:
        hm = build(kind, name, head)
        ob = make_object("%s_%s" % (kind, name), hm, mat)
        kb = ob.data.shape_keys.key_blocks["length"]
        for ln in LENGTHS:
            kb.value = ln
            for vn, d, tgt, scale in VIEWS[kind]:
                d = np.array(d, float)
                loc = np.array(tgt) + d / np.linalg.norm(d) * 8.0
                shot(os.path.join(TILES, "%s_%s_L%d_%s.png" % (kind, name, int(ln), vn)), tuple(loc), tgt, scale,
                     (tile, tile))
        print("[preview] %s/%s %d tris" % (kind, name, hm.tris()))
        bpy.data.objects.remove(ob)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        print(__doc__)
        return
    if argv[0] == "preview":
        preview(parse_keys(argv[1:]))
    elif argv[0] == "verify":
        verify(parse_keys(argv[1:]))
    elif argv[0] == "all":
        export_all(all_keys())
    else:
        export_all(parse_keys(argv))


if __name__ == "__main__":
    main()
