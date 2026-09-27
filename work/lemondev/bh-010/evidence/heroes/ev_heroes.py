"""Scratch evidence for bh-010 heroes. blender -b --python ev_heroes.py -- <hero|lineup> OUT FR"""
import os, sys, json
HERE = r"A:\Python\beyond-heroes\tools\blender\characters"
sys.path.insert(0, HERE)
import bpy
import bh_library as L
import bh_mesh as M
import bh_anim as A
import bh_render as RR
import preview_chars as PC
argv = sys.argv[sys.argv.index("--") + 1:]
what, OUT, FR = argv[:3]
os.makedirs(FR, exist_ok=True)
os.environ.setdefault("BH_PYTHON", "python")
LIB = {a.name: a for a in L.library()}
START = {"ranger": ("idle_bow", None, "bow"), "shadowblade": ("idle_dual", "dagger", "dagger"),
         "knight": ("idle_shield", "sword", "shield"), "mage": ("idle_staff", "staff", None)}
CLIPS = {
    "ranger": [("idle", [0, 60]), ("idle_ranger", "even:7"), ("run", "even:4"), ("bow_release", [0, 8]),
               ("bow_1", "hit"), ("cast_quick", "hit"), ("dodge_roll", [0, 6, 11, 17]), ("hit_heavy", [3, 7, 12]),
               ("death", "even:3")],
    "shadowblade": [("idle", [0, 60]), ("idle_shadowblade", "even:7"), ("run", "even:4"), ("dagger_1", "hit"),
                    ("dual_1", "hit"), ("cast_quick", "hit"), ("dodge_roll", [0, 6, 11, 17]), ("hit_heavy", [3, 7, 12]),
                    ("death", "even:3")],
}


def studio():
    w = bpy.context.scene.world
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.11, 0.115, 0.14, 1)


def hero(c):
    idle, r, l = START[c]
    st = PC.Stage(c, res=768, samples=16, weapons=["bow", "dagger", "sword"])
    studio()
    mesh = st.res["mesh"]
    zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
    info = dict(tris=M.tri_count(mesh), height=round(max(zs) - min(zs), 3),
                extra_bones=[b[0] for b in getattr(st.res["module"], "EXTRA_BONES", [])],
                materials=[m.name for m in mesh.data.materials])
    json.dump(info, open(os.path.join(OUT, f"{c}_info.json"), "w"), indent=1)
    ps, labs = [], []
    for view in ("front", "side", "back", "34"):
        st.set_props(r, l)
        st.play(LIB[idle], 0)
        st.camera(view, dist=5.0)
        ps.append(st.render(os.path.join(FR, f"{c}_{view}.png"))); labs.append(f"{view} ({idle}, starting weapons)")
    st.set_props(None, None)
    st.play(LIB["idle"], 0)
    for view, tz, d in (("front", 1.45, 2.3), ("34", 1.45, 2.3), ("back", 1.45, 2.3), ("34", 1.68, 1.0)):
        st.camera(view, target=(0, 0, tz), dist=d)
        p = st.render(os.path.join(FR, f"{c}_cu_{view}_{d}.png")); ps.append(p); labs.append(f"close {view} (no weapons)")
    PC.compose(ps, labs, os.path.join(OUT, f"{c}_turnaround.png"), cols=4, title=f"{c}: turnaround", cell=480)
    # clip sheet
    ps, labs = [], []
    for name, mode in CLIPS[c]:
        an = LIB[name]
        rr, ll = an.meta.get("props", (None, None))
        if name.startswith("dual"):
            rr, ll = "dagger", "dagger"
        st.set_props(rr, ll)
        frs = mode if isinstance(mode, list) else PC.pick_frames(an, mode)
        for f in frs:
            st.play(an, f)
            st.camera("34")
            ps.append(st.render(os.path.join(FR, f"{c}_{name}_{f:03d}.png")))
            labs.append(f"{name} f{f} ({f / 30:.2f}s)")
    PC.compose(ps, labs, os.path.join(OUT, f"{c}_clips.png"), cols=7, title=f"{c}: clip sheet (3/4 view)", cell=300)


def lineup():
    import build_chars as BC
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cam = RR.setup_scene(res=1024, samples=16)
    studio()
    bpy.data.objects["Ground"].scale = (6, 6, 1)
    order = ["knight", "mage", "ranger", "shadowblade"]
    import bh_materials as MT
    rigs = []
    for i, c in enumerate(order):
        res = BC.build_character(c, with_actions=False, preview=True)
        for m in res["mesh"].data.materials:   # keep each hero's shared-name (tintable) materials its own
            if m and "__lineup" not in m.name:
                m.name = m.name + "__lineup_" + c
        rigs.append((c, res))
    wmats = MT.make_materials("knight", vertex_color=False)
    for i, (c, res) in enumerate(rigs):
        arm = res["armature"]
        arm.location.x = (i - 1.5) * 1.15
        idle, r, l = START[c]
        act = A.bake_action(arm, res["rig"], LIB[idle], extra=getattr(res["module"], "secondary", None))
        A.assign_action(arm, act)
        for side, n in (("R", r), ("L", l)):
            if n:
                ob = PC.weapon_objects(wmats, [n])[n]
                PC.attach(arm, ob, "weapon." + side)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    ps = []
    # game camera: pitch 54, yaw 0 (front), fov 40 vertical ~ lens 33 on 24 mm; default dist 16 then zoomed crops
    for tag, dist, lens in (("game_dist16", 16.0, 33.0), ("game_zoom", 16.0, 80.0), ("near_iso", 9.0, 45.0)):
        yaw = 0 if tag != "near_iso" else 30
        RR.place_camera(cam, (0, 0, 0.9), dist, yaw, 54 if tag != "near_iso" else 35, lens=lens)
        cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = 24
        p = os.path.join(FR, f"lineup_{tag}.png"); RR.render(p); ps.append(p)
    PC.compose(ps, ["game camera (pitch 54, fov 40, dist 16)", "game camera angle, zoomed crop",
                    "3/4 elevated"], os.path.join(OUT, "heroes_lineup_iso.png"), cols=3,
               title="scale: knight | mage | ranger | shadowblade", cell=640)


if what == "lineup":
    lineup()
else:
    hero(what)
