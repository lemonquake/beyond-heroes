"""Ward Eye (bh-029, Builder M3, Zarael / the Bridge of Death beam caster): the watching eye of a bridge ward pylon,
torn loose and turned. Static multi-node floating model animated by the game, following build_wisp.py's convention
exactly (no armature, no clips, origin = creature centre, Blender Z-up -> glTF Y-up, faces -Y = Godot +Z).

  "<blender>" -b --factory-startup --python build_ward_eye.py -- [--out game/assets/characters/ward_eye.glb]
                                                                 [--evidence DIR]

Nodes, ~1.75 m across:
  core      a big carved eye of pale glyph stone (r ~0.36 m): heavy upper and lower lids carved in stepped courses
            round an almond opening; inside, a stone eyeball with a white glowing iris (a dark slit pupil, carved
            rays round it); a stepped brow with a fret band, bronze bands round the back with coil studs, a cracked
            glyph seam; the eye looks -Y and is tipped back 18 deg so it reads from the high gameplay camera
  ring_1..3 bronze ward rings of radius 0.56 / 0.68 / 0.8 m in the node's local XY plane (Blender) = XZ plane
            (Godot), each with its own tilt as its transform (the game spins each about its LOCAL up axis); arc-coil
            studs (bronze helices round white cores) on every ring, glyph tablets on ring_2
  ribbons   bronze wire ribbons and a hanging glyph tablet below the eye, white at the frayed ends
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
NAME = "ward_eye"

import numpy as np  # noqa: E402
import bpy  # noqa: E402

import bh_mesh as M  # noqa: E402
import bh_materials as MT  # noqa: E402
from bh_math import Rx, Ry, Rz, normalize  # noqa: E402
import kit_a_common as A  # noqa: E402
import kit_e_orrery as O  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402
import enemy_span_warden as SW  # noqa: E402

PALETTE_COLORS = {
    "BH_Stone": ((0.5, 0.465, 0.39), 0.0, 0.88, None, 0.0, 1.0),               # pale glyph limestone
    "BH_Bronze": ((0.44, 0.28, 0.12), 1.0, 0.45, None, 0.0, 1.0),              # bronze rings / bands
    "BH_Gold": ((0.62, 0.42, 0.17), 1.0, 0.35, None, 0.0, 1.0),                # bright bronze coils / rims
    "BH_Horn": ((0.1, 0.38, 0.37), 0.0, 0.35, None, 0.0, 1.0),                 # turquoise mosaic
    "BH_DarkSteel": ((0.08, 0.075, 0.07), 0.3, 0.8, None, 0.0, 1.0),           # dark inner stone
    "BH_Shadow": ((0.018, 0.016, 0.015), 0.0, 0.85, None, 0.0, 1.0),           # grooves / pupil
    "BH_Emissive": SW.WHITE_GLOW,                                               # iris, seams, coil cores (white)
}
P = Z.P
R_LID = 0.36
R_BALL = 0.315
TILT = -18.0


def almond(x, w=0.25, h=0.13):
    """Half-height of the lid opening at x (in the eye's face plane)."""
    t = min(abs(x) / w, 1.0)
    return h * (1 - t ** 2) ** 0.85


def sph(r, az, el):
    """Sphere point: az around Z from -Y (0 = front), el = elevation."""
    return np.array([r * math.cos(el) * math.sin(az), -r * math.cos(el) * math.cos(az), r * math.sin(el)])


def lid_shell():
    """Stone lid shell (sphere r R_LID) with the almond opening cut on the front; solidified inward."""
    nu, nv = 40, 22
    V, F = [], []
    for j in range(nv + 1):
        el = -math.pi / 2 + math.pi * j / nv
        for i in range(nu):
            az = 2 * math.pi * i / nu
            V.append(sph(R_LID, az, el))
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu
            q = [j * nu + i, j * nu + i2, (j + 1) * nu + i2, (j + 1) * nu + i]
            c = np.mean([V[k] for k in q], 0)
            if c[1] < -0.12 and abs(c[2]) < almond(c[0]) + 0.012:
                continue
            F.append(tuple(q[::-1]))
    shell = M.Part(np.array(V), F, "BH_Stone", name="lid")
    return M.solidify(shell, 0.035, offset=-1.0)


def core_parts():
    parts = []
    # eyeball (stone) + the glowing iris + slit pupil + carved rays
    V, F = M.sphere(R_BALL, 24, 14)
    parts.append(P(V, F, "BH_Stone", "ball"))
    yi = -R_BALL
    prof = [(0.0, 0.03), (0.06, 0.026), (0.11, 0.014), (0.125, 0.0)]
    V, F = M.lathe([(r, d) for r, d in prof] + [(0.0, -0.01)], 24)
    parts.append(P(V, F, "BH_Emissive", "iris").rot(Rx(90)).move((0, yi + 0.012, 0)))
    V, F = M.box(0.022, 0.012, 0.11)
    parts.append(M.bevel(P(V, F, "BH_Shadow", "pupil").move((0, yi - 0.034, 0)), 0.006, 1))
    ring = [(0.135 * math.cos(a), yi + 0.012 - 0.002, 0.135 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 33)]
    parts.append(A.tube(ring, 0.01, "BH_Shadow", n=4, cap=False))
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = np.array([math.cos(a), 0, math.sin(a)])
        p0 = d * 0.15
        p1 = d * 0.19
        if abs(p1[2]) < almond(p1[0]) - 0.005:
            q0 = p0 + np.array([0, -math.sqrt(max(R_BALL ** 2 - 0.15 ** 2, 0)) - 0.002, 0])
            q1 = p1 + np.array([0, -math.sqrt(max(R_BALL ** 2 - 0.19 ** 2, 0)) - 0.002, 0])
            parts.append(A.tube([q0, q1], 0.006, "BH_Emissive", n=4))
    # lids
    parts.append(lid_shell())
    # carved lid courses (stepped ridges) round the opening, top and bottom, + a white lash seam
    for sgn in (1, -1):
        for k, (off, rr) in enumerate(((0.012, 0.022), (0.05, 0.018), (0.09, 0.015))):
            pts = []
            for x in np.linspace(-0.24, 0.24, 15):
                z = sgn * (almond(x) + off)
                y = -math.sqrt(max((R_LID + 0.008) ** 2 - x * x - z * z, 0.0))
                pts.append((x, y, z))
            parts.append(A.tube(pts, rr, "BH_Stone" if k else "BH_Gold", n=5))
        pts = []
        for x in np.linspace(-0.22, 0.22, 13):
            z = sgn * (almond(x) + 0.03)
            y = -math.sqrt(max((R_LID + 0.006) ** 2 - x * x - z * z, 0.0)) - 0.004
            pts.append((x, y, z))
        parts.append(A.tube(pts, 0.007, "BH_Emissive", n=4))
    # corners: bronze clamps
    for sx in (1, -1):
        c = sph(R_LID + 0.01, sx * math.radians(44), 0.0)
        V, F = M.box(0.06, 0.06, 0.1)
        parts.append(M.bevel(P(V, F, "BH_Bronze", "clamp").rot(Rz(-sx * 44)).move(c), 0.008, 1))
    # stepped brow above the lid with a fret band
    for k in range(3):
        el = math.radians(36 + 9 * k)
        w = 0.5 - 0.1 * k
        pts = [sph(R_LID + 0.03 - 0.008 * k, az, el) for az in np.linspace(-w, w, 11)]
        parts.append(A.tube(pts, (0.035, 0.022), "BH_Stone", n=6, up=(0, 0, 1)))
    pts = []
    for u, v in Z.fret_wave(4, steps=2):
        az = -0.42 + 0.84 * u
        el = math.radians(26 + 8 * v)
        pts.append(sph(R_LID + 0.012, az, el))
    parts.append(A.tube(pts, 0.007, "BH_Shadow", n=4))
    # turquoise mosaic band under the lower lid
    pts = [sph(R_LID + 0.008, az, math.radians(-34)) for az in np.linspace(-0.55, 0.55, 13)]
    parts.append(A.tube(pts, (0.016, 0.01), "BH_Horn", n=5))
    # bronze bands round the back (meridian + equator), coil studs on the sides and back
    for R in (Rx(90), Ry(90) @ Rx(90)):
        ring = [R @ np.array([(R_LID + 0.015) * math.cos(a), (R_LID + 0.015) * math.sin(a), 0.0])
                for a in np.linspace(0, 2 * math.pi, 41)]
        ring = [q for q in ring if q[1] > -0.12]
        parts.append(A.tube(ring, (0.026, 0.014), "BH_Bronze", n=5, cap=True))
    for az_deg, el_deg in ((90, 0), (-90, 0), (180, 0), (180, 50), (180, -50)):
        d = sph(1.0, math.radians(az_deg), math.radians(el_deg))
        a0, b0 = d * (R_LID + 0.01), d * (R_LID + 0.1)
        parts += SW.coil_stud(a0, b0, 0.03, 0.006, turns=4)
    # cracked glyph seam across the top (corruption)
    pts = [sph(R_LID + 0.003, az, math.radians(58)) for az in np.linspace(-1.2, 1.2, 9)]
    parts += SW.chan(pts, np.array([0, 0, 1.0]), 0.009, broken=(3, 6))
    pts = SW.jag(sph(R_LID + 0.004, 0.6, math.radians(70)), sph(R_LID + 0.004, 0.9, math.radians(20)), 6, 0.02,
                 np.array([1.0, 0, 0]), 3)
    parts.append(SW.crack(pts, normalize(np.mean(pts, 0)), 0.007))
    for prt in parts:
        prt.rot(Rx(TILT))
    return parts


def ring_parts(radius, n_studs, seed, tablets=0):
    rng = np.random.default_rng(seed)
    parts = [O.ring((0, 0, 0), (0, 0, 1), radius, 0.026, "BH_Bronze", n=48, m=6, flat=0.55)]
    parts.append(O.ring((0, 0, 0), (0, 0, 1), radius - 0.035, 0.008, "BH_Gold", n=40, m=4))
    parts.append(O.ring((0, 0, 0), (0, 0, 1), radius + 0.0, 0.006, "BH_Emissive", n=40, m=4, flat=1.0)
                 .move((0, 0, 0.016)))
    ph = rng.random() * 2 * math.pi
    for k in range(n_studs):
        a = ph + 2 * math.pi * k / n_studs
        t = np.array([-math.sin(a), math.cos(a), 0.0])
        c = radius * np.array([math.cos(a), math.sin(a), 0.0])
        parts += SW.coil_stud(c - t * 0.06, c + t * 0.06, 0.04, 0.007, turns=5)
    for k in range(tablets):
        a = ph + math.pi / max(n_studs, 1) + 2 * math.pi * k / tablets
        c = radius * np.array([math.cos(a), math.sin(a), 0.0])
        V, F = M.box(0.08, 0.04, 0.11)
        tab = M.bevel(P(V, F, "BH_Stone", "tablet"), 0.008, 1)
        tab.rot(Rz(math.degrees(a) + 90)).move(c)
        parts.append(tab)
        o = normalize(c)
        tt = np.array([-math.sin(a), math.cos(a), 0.0])
        pts = [c + o * 0.022 + tt * x + np.array([0, 0, z]) for x, z in ((-0.024, -0.035), (-0.024, 0.03),
                                                                          (0.024, 0.03), (0.024, -0.008))]
        parts += SW.chan(pts, o, 0.0055)
    return parts


def ribbon_parts():
    parts = []
    rng = np.random.default_rng(9)
    top_z = -R_LID - 0.01
    V, F = M.box(0.16, 0.08, 0.04)
    parts.append(M.bevel(P(V, F, "BH_Bronze", "clamp").move((0, 0.02, top_z)), 0.008, 1))
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        x0, y0 = 0.06 * math.cos(a), 0.03 * math.sin(a) + 0.02
        ln = 0.34 + 0.12 * rng.random()
        pts = []
        for t in np.linspace(0, 1, 9):
            sway = 0.05 * math.sin(t * 4 + k * 1.7) * t
            pts.append((x0 * (1 + 1.4 * t) + sway * math.cos(a), y0 * (1 + 1.4 * t) + sway * math.sin(a), top_z - ln * t))
        parts.append(K_strip(pts))
        tip = np.array(pts[-1])
        parts.append(A.taper([np.array(pts[5]), tip + (0, 0, -0.03)], 0.006, 0.002, "BH_Emissive", n=4))
        parts.append(A.ball(tip + (0, 0, -0.035), 0.013, "BH_Emissive", n=6, rings=4))
    # the hanging glyph tablet on a short chain
    chain_top = np.array([0.0, 0.02, top_z - 0.02])
    parts += SW.chain_links([chain_top, chain_top + (0, 0, -0.16)], link=0.04, r=0.006, mat="BH_Bronze", sides=6, n=3)
    V, F = M.box(0.11, 0.035, 0.15)
    parts.append(M.bevel(P(V, F, "BH_Stone", "tablet").move(chain_top + (0, 0, -0.25)), 0.01, 1))
    c = chain_top + (0, -0.019, -0.25)
    parts += SW.chan([c + (-0.03, 0, 0.05), c + (-0.03, 0, -0.04), c + (0.03, 0, -0.04), c + (0.03, 0, 0.02),
                      c + (0.0, 0, 0.02)], np.array([0, -1.0, 0]), 0.006)
    return parts


def K_strip(pts):
    """A flat bronze wire ribbon (twisted strip)."""
    pts = np.asarray(pts, float)
    ups = [(math.cos(i * 0.7), 0.0, 0.0) if i % 2 == 0 else (0.7, 0.7, 0.0) for i in range(len(pts))]
    V, F = M.tube(pts, [(0.012, 0.003)] * len(pts), n=4, up=[normalize(np.array(u)) for u in ups], p=3.0)
    return P(V, F, "BH_Gold", "ribbon")


RINGS = [  # name, radius, coil studs, tablets, tilt (deg about X, about Y)
    ("ring_1", 0.56, 3, 0, (24, 0)),
    ("ring_2", 0.68, 4, 4, (-14, 32)),
    ("ring_3", 0.8, 5, 0, (40, -24)),
]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = MT.make_materials(NAME, vertex_color=False, extra=PALETTE_COLORS)
    obs = [M.build_static("core", core_parts(), mats, sharp_angle=35)]
    for i, (name, r, n, tabs, (tx, ty)) in enumerate(RINGS):
        ob = M.build_static(name, ring_parts(r, n, 50 + i, tablets=tabs), mats, sharp_angle=35)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (math.radians(tx), math.radians(ty), 0.0)
        obs.append(ob)
    obs.append(M.build_static("ribbons", ribbon_parts(), mats, sharp_angle=60))
    for ob in obs:
        MT.bake_vertex_ao(ob, rays=12, dist=0.2, strength=0.45)
    return obs


def evidence(obs, out, scratch):
    import kit_b_evidence as KB
    from mathutils import Matrix
    tiles = os.path.join(scratch, NAME)
    os.makedirs(tiles, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    KB.material_colors()
    cam = KB.setup(360)
    bpy.data.objects["Ground"].location.z = -1.4       # the game hovers it ~1.4 m above the ground (anim_map hover)
    paths, labels = [], []
    for yaw, pitch in ((0, 6), (35, 25), (90, 5), (160, -8)):
        KB.place(cam, (0, 0, 0), 4.6, yaw, pitch)
        paths.append(KB.render(os.path.join(tiles, f"rest_{yaw}_{pitch}.png")))
        labels.append(f"yaw {yaw} pitch {pitch}")
    KB.place(cam, (0, 0, 0), 1.9, 15, 12)
    paths.append(KB.render(os.path.join(tiles, "closeup.png")))
    labels.append("core close-up (the eye)")
    saved = {}
    for name, *_ in RINGS:
        ob = bpy.data.objects[name]
        saved[name] = ob.matrix_world.copy()
        ob.matrix_world = ob.matrix_world @ Matrix.Rotation(math.radians(40), 4, "Z")
    KB.place(cam, (0, 0, 0), 4.6, 35, 25)
    paths.append(KB.render(os.path.join(tiles, "spun.png")))
    labels.append("rings spun 40 deg about local up (game)")
    for name, m in saved.items():
        bpy.data.objects[name].matrix_world = m
    for dist in (16, 22):
        KB.place(cam, (0, 0, -0.7), dist, 0, 54, fov=40)
        p = KB.render(os.path.join(tiles, f"game_{dist}.png"), res=1080)
        KB.crop_center(p, 360)
        paths.append(p)
        labels.append(f"game cam {dist} m 54deg, 1.4 m hover (1:1 px @1080p)")
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = 360
    KB.compose(paths, labels, os.path.join(out, f"{NAME}_rest_iso.png"), 4, f"{NAME}: nodes / gameplay camera",
               cell=360)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "game", "assets", "characters", NAME + ".glb"))
    ap.add_argument("--evidence", default="")
    ap.add_argument("--scratch", default=os.path.join(ROOT, "work", "lemondev", "bh-029", "scratch", "m3", "ev"))
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
