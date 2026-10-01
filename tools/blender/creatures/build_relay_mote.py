"""Relay Mote (bh-029, Builder M1, Zarael / Coilwood + Barrens seeker / bomber): a Wirewright relay-stone cut loose
by the Blackwire. Static multi-node floating model animated by the game, following build_wisp.py's convention
exactly (no armature, no clips, origin = creature centre, Blender Z-up -> glTF Y-up, faces -Y = Godot +Z).

  "<blender>" -b --factory-startup --python build_relay_mote.py -- [--out game/assets/characters/relay_mote.glb]
                                                                   [--evidence DIR]

Nodes, ~1.1 m across:
  core      a carved pale-limestone disc (r 0.2 m, faces -Y) bound with a copper rim: on both faces a glowing glyph
            (a stepped-fret ring round an eye-and-spiral glyph, the Blackwire in the carved channels), four copper coil
            studs round the rim, a glowing seam round the edge
  ring_1..3 copper relay rings of radius 0.33 / 0.42 / 0.51 m in the node's local XY plane (Blender) = XZ plane
            (Godot); each node carries its own tilt as its transform, so the game spins it about its LOCAL up axis.
            Coil studs (copper helices round glowing cores) sit on every ring; ring_2 carries small glyph tablets.
  ribbons   five short frayed copper wire ribbons hanging below the core, the Blackwire glowing at their ends
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
sys.path.insert(0, CHAR)
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
NAME = "relay_mote"

import numpy as np  # noqa: E402
import bpy  # noqa: E402

import bh_mesh as M  # noqa: E402
import bh_materials as MT  # noqa: E402
from bh_math import Rx, Ry, Rz, normalize  # noqa: E402
import kit_a_common as A  # noqa: E402
import kit_e_orrery as O  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402

PALETTE_COLORS = {
    "BH_Stone": ((0.5, 0.47, 0.39), 0.0, 0.88, None, 0.0, 1.0),               # pale glyph limestone
    "BH_Gold": ((0.72, 0.38, 0.18), 1.0, 0.35, None, 0.0, 1.0),                # copper rings / coils / rim
    "BH_Bronze": ((0.42, 0.25, 0.12), 1.0, 0.5, None, 0.0, 1.0),               # darker copper (studs, clamps)
    "BH_Shadow": ((0.02, 0.016, 0.016), 0.0, 0.85, None, 0.0, 1.0),            # carved grooves
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # Zarael glows are white
}
P = Z.P
R_DISC, T_DISC = 0.2, 0.09


def disc_frame(face):
    """Points on a disc face: (u, v) in the face plane -> 3D, face = -1 front (-Y) / +1 back."""
    yf = face * (T_DISC / 2 + 0.002)
    return lambda u, v: np.array([u * (-face), yf, v])        # mirror u on the back so the glyph reads the same


def glyph(face):
    """The glowing glyph carved in one face: a stepped-fret ring, an eye (lens) and a square spiral pupil."""
    f = disc_frame(face)
    nrm = np.array([0, face, 0.0])
    parts = []
    fw = Z.fret_wave(5, steps=2)
    r0, r1 = 0.125, 0.165
    pts = [f(math.cos(2 * math.pi * u) * (r0 + (r1 - r0) * v), math.sin(2 * math.pi * u) * (r0 + (r1 - r0) * v))
           for u, v in fw]
    parts += Z.channel(pts, nrm, r=0.007, broken=(17, 44))
    eye = [f(0.095 * math.cos(a), 0.055 * math.sin(a) * (1 - 0.2 * (math.sin(a) < 0))) for a in
           np.linspace(0, 2 * math.pi, 19)]
    parts += Z.channel(eye, nrm, r=0.0075)
    sp = [(0.0, 0.0), (0.02, 0.0), (0.02, 0.02), (-0.02, 0.02), (-0.02, -0.025), (0.035, -0.025), (0.035, 0.035)]
    parts += Z.channel([f(u, v) for u, v in sp], nrm, r=0.0065)
    for sx in (1, -1):        # little rays at the eye corners
        parts += Z.channel([f(sx * 0.1, 0.0), f(sx * 0.122, 0.0)], nrm, r=0.005)
    return parts


def core_parts():
    parts = []
    prof = [(0.0, -T_DISC / 2), (R_DISC - 0.02, -T_DISC / 2), (R_DISC, -T_DISC / 2 + 0.02), (R_DISC, T_DISC / 2 - 0.02),
            (R_DISC - 0.02, T_DISC / 2), (0.0, T_DISC / 2)]
    V, F = M.lathe(prof, 32)
    parts.append(P(V, F, "BH_Stone", "disc").rot(Rx(90)))
    # copper rim band + a glowing seam in it
    V, F = M.lathe([(R_DISC + 0.002, -0.026), (R_DISC + 0.014, -0.022), (R_DISC + 0.014, 0.022),
                    (R_DISC + 0.002, 0.026)], 32, cap=False)
    parts.append(P(V, F, "BH_Gold", "rim").rot(Rx(90)))
    ring = [(R_DISC + 0.016) * np.array([math.cos(a), 0, math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 33)]
    parts.append(A.tube(ring, (0.006, 0.006), "BH_Emissive", n=4, cap=False))
    for face in (-1, 1):
        parts += glyph(face)
        # raised boss in the centre of the pupil
        parts.append(A.ball((0.0, face * (T_DISC / 2 + 0.004), 0.0), 0.024, "BH_Emissive", n=8, rings=4,
                            scale=(1, 0.5, 1)))
    # four coil studs round the rim (the old relay contacts)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = np.array([math.cos(a), 0, math.sin(a)])
        a0, b0 = d * (R_DISC + 0.01), d * (R_DISC + 0.075)
        parts.append(Z.coil(a0, b0, 0.022, 4, 0.005, "BH_Gold", n=4, pts_per_turn=8))
        V, F = M.tube([a0, b0], [(0.015, 0.015)] * 2, n=8, up=(0, 1, 0))
        parts.append(P(V, F, "BH_Emissive", "studcore"))
        parts.append(A.ball(b0 + d * 0.01, 0.018, "BH_Bronze", n=8, rings=4))
    for prt in parts:               # tip the glyph face back 22 deg so it reads from the high gameplay camera
        prt.rot(Rx(-22))
    return parts


def ring_parts(radius, n_studs, seed, tablets=0, flat=0.7):
    rng = np.random.default_rng(seed)
    parts = [O.ring((0, 0, 0), (0, 0, 1), radius, 0.014, "BH_Gold", n=40, m=5, flat=flat)]
    parts.append(O.ring((0, 0, 0), (0, 0, 1), radius - 0.02, 0.005, "BH_Bronze", n=32, m=3))
    ph = rng.random() * 2 * math.pi
    for k in range(n_studs):
        a = ph + 2 * math.pi * k / n_studs
        t = np.array([-math.sin(a), math.cos(a), 0.0])
        c = radius * np.array([math.cos(a), math.sin(a), 0.0])
        parts.append(Z.coil(c - t * 0.045, c + t * 0.045, 0.026, 5, 0.0055, "BH_Gold", n=4, pts_per_turn=6))
        V, F = M.tube([c - t * 0.045, c + t * 0.045], [(0.019, 0.019)] * 2, n=8, up=(0, 0, 1))
        parts.append(P(V, F, "BH_Emissive", "core"))
        for sgn in (1, -1):
            V, F = M.lathe([(0.0, -0.006), (0.026, -0.006), (0.026, 0.006), (0.0, 0.006)], 8)
            parts.append(P(V, F, "BH_Bronze", "collar").rot(Rx(90)).rot(Rz(math.degrees(a))).move(c + t * sgn * 0.05))
    for k in range(tablets):
        a = ph + math.pi / n_studs + 2 * math.pi * k / tablets
        c = radius * np.array([math.cos(a), math.sin(a), 0.0])
        V, F = M.box(0.06, 0.03, 0.08)
        tab = M.bevel(P(V, F, "BH_Stone", "tablet"), 0.006, 1)
        tab.rot(Rz(math.degrees(a) + 90)).move(c)
        parts.append(tab)
        o = normalize(c)
        tt = np.array([-math.sin(a), math.cos(a), 0.0])
        pts = [c + o * 0.016 + tt * x + np.array([0, 0, z]) for x, z in ((-0.018, -0.025), (-0.018, 0.02),
                                                                          (0.018, 0.02), (0.018, -0.005))]
        parts += Z.channel(pts, o, r=0.0045)
    return parts


def ribbon_parts():
    parts = []
    rng = np.random.default_rng(5)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        x0, y0 = 0.07 * math.cos(a), 0.035 * math.sin(a)
        ln = 0.28 + 0.12 * rng.random()
        for w in range(2):                       # each ribbon: two twisted copper strands
            pts = []
            for t in np.linspace(0, 1, 9):
                tw = 2 * math.pi * (1.4 * t + 0.5 * w)
                r = 0.012 * (1 - 0.4 * t)
                sway = 0.05 * math.sin(t * 4.5 + k * 1.9) * t
                pts.append((x0 * (1 + 1.2 * t) + r * math.cos(tw) + sway * math.cos(a),
                            y0 * (1 + 1.2 * t) + r * math.sin(tw) + sway * math.sin(a), -0.2 - ln * t))
            parts.append(A.taper(pts, 0.0055, 0.003, "BH_Gold", n=4))
        tip = np.array(pts[-1])
        mid = np.array(pts[4])
        parts.append(A.taper([mid, (mid + tip) / 2, tip + (0, 0, -0.04)], 0.007, 0.002, "BH_Emissive", n=4))
        for i in range(3):                       # frayed ends: short splayed wires
            d = normalize(np.array([math.cos(a + i - 1), math.sin(a + i - 1), -1.6]))
            parts.append(A.taper([tip, tip + d * (0.04 + 0.02 * i)], 0.003, 0.001, "BH_Gold", n=3))
        parts.append(A.ball(tip + (0, 0, -0.045), 0.012, "BH_Emissive", n=6, rings=4))
    # a clamp under the disc where the ribbons hang from
    V, F = M.box(0.12, 0.05, 0.03)
    parts.append(M.bevel(P(V, F, "BH_Bronze", "clamp").move((0, 0, -0.205)), 0.006, 1))
    return parts


RINGS = [  # name, radius, coil studs, tablets, tilt (deg about X, about Y)
    ("ring_1", 0.33, 3, 0, (20, 0)),
    ("ring_2", 0.42, 4, 4, (-12, 34)),
    ("ring_3", 0.51, 5, 0, (38, -26)),
]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = MT.make_materials(NAME, vertex_color=False, extra=PALETTE_COLORS)
    obs = [M.build_static("core", core_parts(), mats, sharp_angle=35)]
    for i, (name, r, n, tabs, (tx, ty)) in enumerate(RINGS):
        ob = M.build_static(name, ring_parts(r, n, 40 + i, tablets=tabs), mats, sharp_angle=35)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (math.radians(tx), math.radians(ty), 0.0)
        obs.append(ob)
    obs.append(M.build_static("ribbons", ribbon_parts(), mats, sharp_angle=60))
    for ob in obs:
        MT.bake_vertex_ao(ob, rays=12, dist=0.15, strength=0.4)
    return obs


def evidence(obs, out, scratch):
    import kit_b_evidence as KB
    tiles = os.path.join(scratch, NAME)
    os.makedirs(tiles, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    KB.material_colors()
    cam = KB.setup(360)
    bpy.data.objects["Ground"].location.z = -1.2       # the game hovers it ~1.2 m above the ground
    paths, labels = [], []
    for yaw, pitch in ((0, 6), (35, 25), (90, 5), (160, -8)):
        KB.place(cam, (0, 0, 0), 3.4, yaw, pitch)
        paths.append(KB.render(os.path.join(tiles, f"rest_{yaw}_{pitch}.png")))
        labels.append(f"yaw {yaw} pitch {pitch}")
    KB.place(cam, (0, 0, 0), 1.3, 20, 8)
    paths.append(KB.render(os.path.join(tiles, "closeup.png")))
    labels.append("core close-up (glyph face)")
    # ring spin check: rotate each ring about its local up axis (Blender local Z) by 40 deg
    saved = {}
    for name, *_ in RINGS:
        ob = bpy.data.objects[name]
        saved[name] = ob.matrix_world.copy()
        from mathutils import Matrix
        ob.matrix_world = ob.matrix_world @ Matrix.Rotation(math.radians(40), 4, "Z")
    KB.place(cam, (0, 0, 0), 3.4, 35, 25)
    paths.append(KB.render(os.path.join(tiles, "spun.png")))
    labels.append("rings spun 40 deg about local up (game)")
    for name, m in saved.items():
        bpy.data.objects[name].matrix_world = m
    for dist in (16, 22):
        KB.place(cam, (0, 0, -0.6), dist, 0, 54, fov=40)
        p = KB.render(os.path.join(tiles, f"game_{dist}.png"), res=1080)
        KB.crop_center(p, 360)
        paths.append(p)
        labels.append(f"game cam {dist} m 54deg, 1.2 m hover (1:1 px @1080p)")
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = 360
    KB.compose(paths, labels, os.path.join(out, f"{NAME}_rest_iso.png"), 4, f"{NAME}: nodes / gameplay camera",
               cell=360)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "game", "assets", "characters", NAME + ".glb"))
    ap.add_argument("--evidence", default="")
    ap.add_argument("--scratch", default=os.path.join(ROOT, "work", "lemondev", "bh-029", "scratch", "m1", "ev"))
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    obs = build()
    for ob in obs:
        print(f"[{NAME}] {ob.name}: {M.tri_count(ob)} tris")
    print(f"[{NAME}] total {sum(M.tri_count(o) for o in obs)} tris")
    if not a.no_export:
        import build as BLD
        BLD.export_glb(a.out, obs, animations=False)
        print(f"[{NAME}] ->", a.out)
    if a.evidence:
        evidence(obs, a.evidence, a.scratch)


if __name__ == "__main__":
    main()
