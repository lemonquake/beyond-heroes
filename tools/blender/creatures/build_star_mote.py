"""Starmote (bh-012, Builder E; The Shattered Orrery seeker / bomber): static multi-node floating model animated by
the game, following build_wisp.py's node convention exactly.

  "<blender>" -b --factory-startup --python build_star_mote.py -- [--out game/assets/characters/star_mote.glb]
                                                                  [--preview DIR]

Nodes (all meshes, no armature, origin = creature centre, Blender Z-up -> glTF Y-up), ~1.1 m across:
  core      a blazing violet-white star crystal (eight-point faceted star + inner heart, BH_Emissive) inside a small
            brass cage (three crossing hoops, gold pole finials), radius ~0.2 m
  ring_1..3 thin polished-brass orrery rings of radius 0.32 / 0.43 / 0.54 m with graduation studs; ring_1 carries a
            starglass planet bead, ring_2 a tarnished-brass planet with its own little gold ring and a starglass
            bead, ring_3 a tiny glowing moon (BH_Aether palette entry = pale moon glow) and a gold bead. The rings lie
            in the node's local XY plane (Blender) = XZ plane (Godot); each node carries its own tilt as its
            transform, so the game spins it about its LOCAL up axis (Godot +Y) in its own plane.
  ribbons   four trailing strands of star-dust sparks hanging below the core (faint violet strand + spark specks)
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
sys.path.insert(0, CHAR)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

import numpy as np  # noqa: E402
import bpy  # noqa: E402

import bh_mesh as M  # noqa: E402
import bh_materials as MT  # noqa: E402
from bh_math import Rx, Ry, Rz, normalize  # noqa: E402
import kit_e_orrery as O  # noqa: E402

PALETTE = "star_mote"
PALETTE_COLORS = {
    "BH_Emissive": ((0.8, 0.62, 1.0), 0.0, 0.3, (0.78, 0.58, 1.0), 9.0, 1.0),   # star crystal, sparks
    "BH_Bronze": O.BRASS,                                                       # rings, cage
    "BH_Horn": O.BRASS_OLD,                                                     # tarnished planet
    "BH_Gold": O.GOLD,
    "BH_Stone": O.STARGLASS,                                                    # starglass planet beads
    "BH_Aether": ((0.92, 0.9, 1.0), 0.0, 0.3, (0.85, 0.82, 1.0), 5.0, 1.0),     # the little moon
}


def star_crystal(r=0.13):
    """Eight-point faceted star: six axis spikes + eight diagonal short spikes around an inner heart."""
    parts = []
    dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    for d in dirs:
        V, F = M.lathe([(0.0, 0.0), (r * 0.32, r * 0.25), (0.0, r * 1.25)], 4)
        parts.append(O.orient(O.P(V, F, "BH_Emissive", "spike"), (0, 0, 0), d, up=(0.3, 0.4, 0.8)))
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                V, F = M.lathe([(0.0, 0.0), (r * 0.24, r * 0.2), (0.0, r * 0.8)], 4)
                parts.append(O.orient(O.P(V, F, "BH_Emissive", "spike"), (0, 0, 0), (sx, sy, sz), up=(0, 0, 1)))
    V, F = M.sphere(r * 0.45, 10, 6)
    parts.append(O.P(V, F, "BH_Emissive", "heart"))
    return parts


def core_parts():
    parts = star_crystal(0.16)
    rc = 0.22
    for nrm in ((0, 0, 1), (1, 0, 0.0), (0, 1, 0.0)):
        parts.append(O.ring((0, 0, 0), nrm, rc, 0.009, "BH_Bronze", n=26, m=5))
    parts.append(O.ring((0, 0, 0), (0.6, -0.6, 0.5), rc * 0.93, 0.005, "BH_Gold", n=24, m=4))
    for sz in (1, -1):
        parts.append(O.ball((0, 0, sz * rc), 0.022, "BH_Gold", n=8, rings=5))
        parts.append(O.taper([(0, 0, sz * (rc + 0.015)), (0, 0, sz * (rc + 0.07))], 0.01, 0.002, "BH_Gold", n=5))
    return parts


def ring_parts(radius, beads, seed):
    rng = np.random.default_rng(seed)
    parts = [O.ring((0, 0, 0), (0, 0, 1), radius, 0.015, "BH_Bronze", n=44, m=5, flat=0.7)]
    for p in O.ring_points((0, 0, 0), (0, 0, 1), radius + 0.012, 12, phase=rng.random()):
        parts.append(O.ball(p, 0.008, "BH_Gold", n=6, rings=3))
    for (ang, r, mat, sub) in beads:
        a = math.radians(ang)
        c = np.array([radius * math.cos(a), radius * math.sin(a), 0.0])
        parts.append(O.ball(c, r, mat, n=12, rings=8))
        # little arm clasping the bead to the ring
        parts.append(O.ring(c, (math.cos(a), math.sin(a), 0.0), r + 0.006, 0.004, "BH_Gold", n=14, m=4))
        if sub:
            parts.append(O.ring(c, (0.3, 0.2, 1.0), r * 1.7, 0.004, "BH_Gold", n=18, m=4))
        if mat == "BH_Aether":
            for k in range(4):
                d = np.array([math.cos(k * math.pi / 2), math.sin(k * math.pi / 2), 0.0])
                parts.append(O.taper([c + d * r * 0.9, c + d * r * 1.9], 0.006, 0.001, "BH_Aether", n=4))
    return parts


def ribbon_parts():
    parts = []
    rng = np.random.default_rng(7)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.3
        pts = []
        for t in np.linspace(0, 1, 9):
            r = 0.06 + 0.12 * t
            sway = 0.06 * math.sin(t * 5 + k * 1.7) * t
            pts.append((r * math.cos(a) + sway * math.cos(a + 1.5), r * math.sin(a) + sway * math.sin(a + 1.5),
                        -0.14 - (0.5 + 0.06 * k) * t))
        pts = np.array(pts)
        parts.append(O.taper(pts, 0.006, 0.0015, "BH_Emissive", n=4))
        for i in range(14):
            t = rng.random()
            j = min(int(t * 8), 7)
            u = t * 8 - j
            p = pts[j] * (1 - u) + pts[j + 1] * u + rng.normal(size=3) * 0.02 * (0.3 + t)
            size = 0.02 * (1 - 0.7 * t) + 0.004
            if i % 4 == 0:
                parts.append(O.star4(p, size * 1.6, normalize(rng.normal(size=3)), "BH_Emissive", thick=0.003))
            else:
                parts.append(O.speck(p, size, "BH_Emissive", seed=k * 100 + i))
    return parts


RINGS = [  # name, radius, beads (angle, radius, material, has sub-ring), tilt (deg about X, about Y)
    ("ring_1", 0.32, [(40, 0.035, "BH_Stone", False)], (22, 0)),
    ("ring_2", 0.43, [(160, 0.05, "BH_Horn", True), (300, 0.028, "BH_Stone", False)], (-14, 32)),
    ("ring_3", 0.54, [(250, 0.042, "BH_Aether", False), (80, 0.024, "BH_Gold", False)], (38, -26)),
]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = MT.make_materials(PALETTE, vertex_color=False, extra=PALETTE_COLORS)
    obs = [M.build_static("core", core_parts(), mats, sharp_angle=30)]
    for i, (name, r, beads, (tx, ty)) in enumerate(RINGS):
        ob = M.build_static(name, ring_parts(r, beads, seed=30 + i), mats, sharp_angle=40)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (math.radians(tx), math.radians(ty), 0.0)
        obs.append(ob)
    obs.append(M.build_static("ribbons", ribbon_parts(), mats, sharp_angle=60))
    for ob in obs:
        MT.bake_vertex_ao(ob, rays=12, dist=0.12, strength=0.35)
    return obs


def preview(obs, out_dir):
    import preview_enemy as PE
    PE.material_colors()
    cam = PE.setup(360)
    bpy.data.objects["Ground"].location.z = -1.2
    tiles = []
    for v, pitch, dist, lens in ((0, 8, 3.2, 50), (60, 30, 3.2, 50), (150, -10, 3.2, 50), (20, 54, 16.0, 50),
                                 (20, 54, 22.0, 50)):
        PE.place(cam, (0, 0, 0), dist, v, pitch, lens)
        p = os.path.join(out_dir, f"_mote_{v}_{pitch}_{int(dist)}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append(p)
    try:
        from PIL import Image, ImageDraw
    except ImportError:          # Blender's bundled Python has no PIL: compose with system Python (tiles listed)
        print("TILES", ";".join(tiles))
        return
    sheet = Image.new("RGB", (360 * len(tiles), 380), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    labels = ["front", "yaw 60 pitch 30", "below-back", "game cam 54deg 16 m", "game cam 54deg 22 m"]
    for i, p in enumerate(tiles):
        sheet.paste(Image.open(p).convert("RGB"), (360 * i, 20))
        d.text((360 * i + 4, 4), "star_mote " + labels[i], fill=(255, 255, 210))
    path = os.path.join(out_dir, "star_mote_rest_iso.png")
    sheet.save(path)
    print("PREVIEW", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "game", "assets", "characters", "star_mote.glb"))
    ap.add_argument("--preview", default="")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    obs = build()
    for ob in obs:
        print(f"[star_mote] {ob.name}: {M.tri_count(ob)} tris")
    print(f"[star_mote] total {sum(M.tri_count(o) for o in obs)} tris")
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        preview(obs, a.preview)
    import build as BLD
    BLD.export_glb(a.out, obs, animations=False)
    print("[star_mote] ->", a.out)


if __name__ == "__main__":
    main()
