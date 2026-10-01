"""Heartwire Wraith (bh-029, Builder M4, Zarael / the Heart Citadel caster): a knot of corrupted current that has
gathered round an old carved mask - a Wirewright face-stone torn from some wall. Static multi-node floating model
animated by the game, following build_wisp.py's convention exactly (no armature, no clips, origin = creature centre,
Blender Z-up -> glTF Y-up, faces -Y = Godot +Z).

  "<blender>" -b --factory-startup --python build_heartwire_wraith.py -- [--out game/assets/characters/heartwire_wraith.glb]
                                                                         [--evidence DIR] [--no-export]

Nodes (~1.5 m tall overall: the knot ~0.6 m across, ribbons trailing ~0.95 m below the centre):
  core      a cracked carved mask of pale stone (brow ridge, hollow eyes and mouth slit burning white, a carved fret band
            on the forehead, stepped cheek carvings, a crack splitting it from crown to chin with the light inside),
            caught in a knot of wire: two white-glowing wire loops (torus knots) and two dark copper ones tangled
            round it, plus loose frayed wire ends
  ring_1..3 loose wire rings (radius 0.36 / 0.48 / 0.6 m) in the node's local XY plane (Blender) = XZ (Godot), each
            tilted by its own node transform (the game spins it about its LOCAL up axis): ring_1 a twisted pair of copper
            and white wire, ring_2 a copper ring carrying four orbiting mask fragments, ring_3 three broken white arcs
  ribbons   six long ribbons of wire trailing below the mask: flat bands of twisted copper strands with a white core,
            fraying at the ends
Glow rule (bh-029): every glow is pure white BH_Emissive.
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
NAME = "heartwire_wraith"

import numpy as np  # noqa: E402
import bpy  # noqa: E402

import bh_mesh as M  # noqa: E402
import bh_materials as MT  # noqa: E402
from bh_math import Rx, Ry, Rz, normalize  # noqa: E402
import kit_a_common as A  # noqa: E402
import kit_e_orrery as O  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402

PALETTE_COLORS = {
    "BH_Stone": ((0.5, 0.47, 0.4), 0.0, 0.85, None, 0.0, 1.0),                # pale carved mask stone
    "BH_Gold": ((0.5, 0.27, 0.13), 1.0, 0.4, None, 0.0, 1.0),                 # copper wire
    "BH_Bronze": ((0.25, 0.14, 0.07), 1.0, 0.5, None, 0.0, 1.0),              # dark old copper
    "BH_Shadow": ((0.012, 0.01, 0.012), 0.0, 0.85, None, 0.0, 1.0),           # hollows, grooves
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),    # the current (white)
}
P = Z.P
GLOW = "BH_Emissive"
TILT = -18          # the face tips back so it reads from the high gameplay camera


# ------------------------------------------------------------------------------------------------ core
def mask_surface(u, v):
    """Mask front surface: u, v in [-1, 1] (x across, z up); faces -Y, convex."""
    x = 0.155 * u
    z = 0.205 * v
    y = -0.05 + 0.045 * (u * u) + 0.03 * (v * v) - 0.012 * max(0.0, 1 - abs(u) * 3) * (v < 0.15)
    return np.array([x, y, z])


def mask_parts():
    parts = []
    nu, nv = 11, 13

    def fn(i, j):
        u = -1 + 2 * i
        v = -1 + 2 * j
        w = 0.22 + 0.78 * math.sqrt(max(1 - (v * 0.93) ** 2, 0.0))   # oval outline
        w *= 1.0 - 0.15 * max(-v, 0.0)                                  # narrower chin
        return mask_surface(u * w, v)
    V, F = M.grid(lambda a, b: tuple(fn(a, b)), nu, nv)
    face = P(np.asarray(V, float), F, "BH_Stone", "mask")
    shell = M.solidify(face.copy(), 0.03, offset=1.0)
    if shell.V[:, 1].min() < -0.056:          # thickness must go back (+Y), keeping the carved front surface
        shell = M.solidify(face, 0.03, offset=-1.0)
    parts.append(shell)

    def on(u, v, out=0.0):
        q = mask_surface(u, v)
        return q + np.array([0, -1.0, 0]) * out
    # brow ridge, nose ridge
    parts.append(A.tube([on(-0.85, 0.32, 0.012), on(-0.35, 0.42, 0.02), on(0.0, 0.36, 0.022), on(0.35, 0.42, 0.02),
                         on(0.85, 0.32, 0.012)], (0.018, 0.014), "BH_Stone", n=5))
    parts.append(A.tube([on(0.0, 0.32, 0.018), on(0.0, 0.05, 0.03), on(0.0, -0.08, 0.026)], [(0.016, 0.012),
                         (0.02, 0.016), (0.02, 0.012)], "BH_Stone", n=5, up=(0, -1, 0)))
    # hollow eyes (dark, white light inside) and the mouth slit
    for sx in (1, -1):
        c = on(sx * 0.42, 0.18, -0.002)
        parts.append(A.ball(c, 0.032, "BH_Shadow", n=8, rings=5, scale=(1.3, 0.5, 0.8)))
        parts.append(A.ball(c + (0, -0.006, 0), 0.018, GLOW, n=8, rings=4, scale=(1.4, 0.5, 0.75)))
        # stepped cheek carvings (grooves)
        pts = [on(sx * (0.45 + 0.35 * uu), -0.15 - 0.3 * vv, 0.002) for uu, vv in Z.fret_wave(1, steps=2)]
        parts.append(A.tube(pts, 0.005, "BH_Shadow", n=4))
    m = [on(-0.38, -0.5, 0.0), on(-0.15, -0.46, 0.002), on(0.15, -0.46, 0.002), on(0.38, -0.5, 0.0)]
    parts.append(A.tube(m, (0.011, 0.016), "BH_Shadow", n=5))
    parts.append(A.tube(m[1:3], (0.006, 0.009), GLOW, n=4))
    # carved fret band on the forehead (white in the channel, broken where the crack runs)
    pts = [on(-0.7 + 1.4 * uu, 0.58 + 0.2 * vv, 0.0) for uu, vv in Z.fret_wave(3, steps=2)]
    parts += Z.channel(pts, (0, -1, 0.1), r=0.0055, broken=(11, 12))
    # the crack: crown to chin through the right eye, light burning in it
    ck = [on(0.12, 1.0, 0.0), on(0.2, 0.75, 0.0), on(0.1, 0.55, 0.0), on(0.3, 0.38, 0.0), on(0.38, 0.18, 0.0),
          on(0.28, -0.1, 0.0), on(0.4, -0.35, 0.0), on(0.3, -0.62, 0.0), on(0.36, -0.95, 0.0)]
    parts += Z.channel(ck, (0, -1, 0), r=0.007)
    # a back plate: rough broken stone with copper staples
    V, F = M.sphere(1.0, 10, 6)
    V = np.asarray(V) * np.array([0.14, 0.035, 0.19]) + np.array([0, 0.0, 0])
    parts.append(P(V, F, "BH_Stone", "back"))
    for z in (0.1, -0.08):
        parts.append(A.tube([(-0.1, 0.0, z), (-0.1, 0.03, z), (0.1, 0.03, z), (0.1, 0.0, z)], 0.006, "BH_Bronze", n=4))
    for p in parts:
        p.rot(Rx(TILT))
    return parts


def torus_knot(p, q, R, r, n=90, rot=np.eye(3), squash=(1.0, 1.0, 1.0)):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        rr = R + r * math.cos(q * t)
        pts.append(rot @ (np.array([rr * math.cos(p * t), rr * math.sin(p * t), r * math.sin(q * t)]) *
                          np.asarray(squash)))
    return np.array(pts)


def core_parts():
    parts = mask_parts()
    # the knot: torus-knot loops round the mask (white current + dark copper)
    specs = [(2, 3, 0.29, 0.07, Rx(90) @ Rz(10), (1.0, 1.25, 1.0), GLOW, 0.012),
             (3, 5, 0.31, 0.06, Rx(90) @ Ry(25) @ Rz(40), (1.0, 1.2, 1.0), GLOW, 0.009),
             (2, 5, 0.3, 0.05, Rx(90) @ Ry(-28) @ Rz(70), (1.0, 1.2, 1.0), "BH_Gold", 0.008),
             (3, 4, 0.27, 0.06, Ry(90) @ Rz(25), (1.0, 1.0, 1.0), "BH_Bronze", 0.007)]
    for p, q, R, r, rot, sq, mat, w in specs:
        pts = torus_knot(p, q, R, r, n=96 if mat == GLOW else 80, rot=rot, squash=sq)
        V, F = M.tube(pts, [(w, w)] * len(pts), n=4 if mat == GLOW else 4, up=(0, 0, 1), cap0=False, cap1=False)
        parts.append(P(V, F, mat, "knot"))
    # loose frayed ends sticking out of the knot
    rng = np.random.default_rng(3)
    for k in range(9):
        d = normalize(rng.normal(size=3) + np.array([0, 0.5, 0]))
        b = d * 0.3
        mid = b + d * 0.08 + rng.normal(size=3) * 0.02
        tip = b + d * (0.15 + 0.06 * rng.random())
        parts.append(A.taper([b, mid, tip], 0.006, 0.0015, GLOW if k % 2 == 0 else "BH_Gold", n=4))
        if k % 2 == 0:
            parts.append(A.ball(tip, 0.012, GLOW, n=6, rings=3))
    return parts


# ------------------------------------------------------------------------------------------------ rings / ribbons
def ring1_parts(radius=0.36):
    """A twisted pair: copper wire and a white wire wound round each other."""
    parts = []
    n = 120
    for w, (mat, rr) in enumerate((("BH_Gold", 0.008), (GLOW, 0.0075))):
        pts = []
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            tw = a * 9 + math.pi * w
            c = np.array([radius * math.cos(a), radius * math.sin(a), 0.0])
            o = np.array([math.cos(a), math.sin(a), 0.0])
            pts.append(c + (o * math.cos(tw) + np.array([0, 0, 1.0]) * math.sin(tw)) * 0.014)
        V, F = M.tube(np.array(pts), [(rr, rr)] * (n + 1), n=4, up=(0, 0, 1), cap0=False, cap1=False)
        parts.append(P(V, F, mat, "pair"))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        c = radius * np.array([math.cos(a), math.sin(a), 0.0])
        t = np.array([-math.sin(a), math.cos(a), 0.0])
        V, F = M.tube([c - t * 0.03, c + t * 0.03], [(0.02, 0.02)] * 2, n=8, up=(0, 0, 1))
        parts.append(P(V, F, "BH_Bronze", "clamp"))
    return parts


def ring2_parts(radius=0.48):
    """A copper ring carrying four orbiting fragments of the mask (white light in their broken edges)."""
    parts = [O.ring((0, 0, 0), (0, 0, 1), radius, 0.008, "BH_Gold", n=40, m=4)]
    rng = np.random.default_rng(8)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.3
        c = radius * np.array([math.cos(a), math.sin(a), 0.0])
        V, F = M.box(0.07 + 0.02 * rng.random(), 0.025, 0.09 + 0.02 * rng.random())
        fr = M.bevel(P(V, F, "BH_Stone", "fragment"), 0.006, 1)
        fr.V += rng.normal(size=fr.V.shape) * 0.006
        fr.rot(Rz(math.degrees(a) + 90)).rot(Rx(10), center=(0, 0, 0)).move(c)
        parts.append(fr)
        o = normalize(c)
        parts.append(A.tube([c - o * 0.03 + (0, 0, -0.045), c + o * 0.0 + (0, 0, -0.05), c + o * 0.03 + (0, 0, -0.04)],
                            0.0055, GLOW, n=4))
        parts.append(Z.coil(c - o * 0.04, c + o * 0.04, 0.02, 3, 0.004, "BH_Bronze", n=4, pts_per_turn=6))
    return parts


def ring3_parts(radius=0.6):
    """Three broken arcs of white current with copper ends."""
    parts = []
    for k in range(3):
        a0 = 120 * k + 10
        a1 = a0 + 80
        parts.append(O.ring((0, 0, 0), (0, 0, 1), radius, 0.007, GLOW, n=16, m=4, arc=(a0, a1)))
        for a in (a0, a1):
            r_ = math.radians(a)
            c = radius * np.array([math.cos(r_), math.sin(r_), 0.0])
            parts.append(A.ball(c, 0.016, "BH_Gold", n=6, rings=4))
    return parts


def ribbon_parts():
    parts = []
    rng = np.random.default_rng(5)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.25
        x0, y0 = 0.09 * math.cos(a), 0.06 * math.sin(a)
        ln = 0.6 + 0.25 * rng.random()
        pts = []
        for t in np.linspace(0, 1, 10):
            sway = 0.08 * math.sin(t * 4.0 + k * 1.7) * t
            pts.append((x0 * (1 + 1.6 * t) + sway * math.cos(a), y0 * (1 + 1.6 * t) + sway * math.sin(a) + 0.04 * t,
                        -0.16 - ln * t))
        pts = np.array(pts)
        # flat band: a dark copper ribbon with the white core running down it
        widths = [0.03 * (1 - 0.6 * t) + 0.004 for t in np.linspace(0, 1, 10)]
        V, F = M.tube(pts, [(w, 0.003) for w in widths], n=4, up=(math.cos(a), math.sin(a), 0), p=3.0)
        parts.append(P(V, F, "BH_Bronze", "band"))
        V, F = M.tube(pts + np.array([math.cos(a), math.sin(a), 0]) * 0.004,
                      [(0.006 * (1 - 0.5 * t) + 0.002, 0.006 * (1 - 0.5 * t) + 0.002) for t in np.linspace(0, 1, 10)],
                      n=4, up=(0, 0, 1))
        parts.append(P(V, F, GLOW, "core"))
        tip = pts[-1]
        for i in range(3):            # frayed strands
            d = normalize(np.array([math.cos(a + i - 1) * 0.6, math.sin(a + i - 1) * 0.6, -1.6]))
            parts.append(A.taper([tip, tip + d * (0.05 + 0.03 * i)], 0.003, 0.001, "BH_Gold", n=3))
        parts.append(A.ball(tip + (0, 0, -0.02), 0.01, GLOW, n=6, rings=3))
    # the knot's underside where the ribbons leave it
    parts.append(A.ball((0, 0.0, -0.17), 0.045, "BH_Bronze", n=8, rings=5, scale=(1.2, 1.0, 0.6)))
    return parts


RINGS = [  # name, builder, tilt (deg about X, about Y)
    ("ring_1", ring1_parts, (24, 0)),
    ("ring_2", ring2_parts, (-14, 30)),
    ("ring_3", ring3_parts, (40, -28)),
]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = MT.make_materials(NAME, vertex_color=False, extra=PALETTE_COLORS)
    obs = [M.build_static("core", core_parts(), mats, sharp_angle=35)]
    for name, fn, (tx, ty) in RINGS:
        ob = M.build_static(name, fn(), mats, sharp_angle=35)
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
        KB.place(cam, (0, 0, -0.2), 3.6, yaw, pitch)
        paths.append(KB.render(os.path.join(tiles, f"rest_{yaw}_{pitch}.png")))
        labels.append(f"yaw {yaw} pitch {pitch}")
    KB.place(cam, (0, 0, 0), 1.2, 20, 8)
    paths.append(KB.render(os.path.join(tiles, "closeup.png")))
    labels.append("core close-up (mask in the knot)")
    saved = {}
    from mathutils import Matrix
    for name, *_ in RINGS:
        ob = bpy.data.objects[name]
        saved[name] = ob.matrix_world.copy()
        ob.matrix_world = ob.matrix_world @ Matrix.Rotation(math.radians(40), 4, "Z")
    KB.place(cam, (0, 0, -0.2), 3.6, 35, 25)
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
    ap.add_argument("--scratch", default=os.path.join(ROOT, "work", "lemondev", "bh-029", "scratch", "m4", "ev"))
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
