"""bh-021 legend weapons (static GLBs, grip at the origin, +Z along the blade/haft, flats +-Y, strike face +X):

  dusk_piercer        Aljay's lance: 3.6 m of black Tyrant-steel, a winged vamplate, a crimson vein spiralling the shaft,
                      a barbed leaf head flanked by two Tyrant fangs.
  dusk_piercer_broken the same lance snapped a hand below the head (the head stayed in Kethrax's chest).
  dawnmaul            Roydo's warhammer: white-gold engraved head, sun discs on both faces, a crown spike, gold bands.
  stormwake           Paul David's longsword: long straight blade, azure fuller light, winged silver guard, sapphire pommel.
  kethrax_mace        Kethrax's chain-mace: a flanged iron head with violet rune slots on a chained haft.

  blender -b --factory-startup --python legend_weapons.py -- [names]      -> game/assets/weapons/legend/<name>.glb
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "weapons", "legend")

import bh_mesh as M  # noqa: E402
from bh_math import normalize, R_axis, Rz  # noqa: E402
from town_matron import P_, outward  # noqa: E402
import legend_kit as LK  # noqa: E402

PALETTES = {
    "dusk_piercer": {
        "BH_DragonPlate": LK.mat((0.045, 0.038, 0.042), 0.8, 0.4),
        "BH_DarkSteel": LK.mat((0.05, 0.045, 0.05), 0.75, 0.42),
        "BH_Crimson": LK.mat((0.45, 0.03, 0.035), 0.85, 0.3),
        "BH_Horn": LK.mat((0.05, 0.035, 0.034), 0.0, 0.35),
        "BH_Leather": LK.mat((0.07, 0.03, 0.025), 0.0, 0.6),
        "BH_Emissive": LK.mat((1.0, 0.12, 0.07), 0.0, 0.4, (1.0, 0.06, 0.025), 9.0),
        "BH_Steel": LK.mat((0.1, 0.09, 0.095), 1.0, 0.25),
    },
    "dawnmaul": {
        "BH_HolyPlate": LK.mat((0.86, 0.84, 0.78), 1.0, 0.3),
        "BH_Gold": LK.mat((0.95, 0.68, 0.26), 1.0, 0.28),
        "BH_Leather": LK.mat((0.8, 0.74, 0.62), 0.0, 0.6),
        "BH_Emissive": LK.mat((1.0, 0.85, 0.45), 0.0, 0.3, (1.0, 0.78, 0.35), 7.0),
    },
    "stormwake": {
        "BH_Steel": LK.mat((0.72, 0.74, 0.78), 1.0, 0.22),
        "BH_Silver": LK.mat((0.78, 0.8, 0.84), 1.0, 0.3),
        "BH_Leather": LK.mat((0.05, 0.07, 0.13), 0.0, 0.55),
        "BH_Emissive": LK.mat((0.4, 0.75, 1.0), 0.0, 0.3, (0.35, 0.75, 1.0), 6.0),
    },
    "kethrax_mace": {
        "BH_ForsakenIron": LK.mat((0.8, 0.8, 0.8), 0.85, 0.55),
        "BH_DarkSteel": LK.mat((0.06, 0.055, 0.065), 0.8, 0.45),
        "BH_Leather": LK.mat((0.06, 0.04, 0.035), 0.0, 0.65),
        "BH_Emissive": LK.mat((0.62, 0.35, 1.0), 0.0, 0.4, (0.6, 0.3, 1.0), 7.0),
    },
}
PALETTES["dusk_piercer_broken"] = PALETTES["dusk_piercer"]
PALETTES["dusk_piercer_tip"] = PALETTES["dusk_piercer"]


def ring(z, r, t, mat, n=16):
    V, F = M.lathe([(r - t, z - t), (r + 0.002, z - t), (r + t * 0.6, z), (r + 0.002, z + t), (r - t, z + t)], n)
    return outward(P_(V, F, mat, "ring"))


def helix(z0, z1, r_of, turns, rad, mat, n=90, phase=0.0):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        z = z0 + (z1 - z0) * t
        a = phase + t * turns * 2 * math.pi
        r = r_of(z)
        pts.append((r * math.cos(a), r * math.sin(a), z))
    V, F = M.tube(pts, [(rad, rad)] * n, n=5, up=(0, 0, 1))
    return P_(V, F, mat, "helix")


# ------------------------------------------------------------------------------------------------------------ lance
def dusk_piercer(broken=False):
    parts = []
    # butt spike and pommel ring
    parts.append(LK.lathe_part([(0.0, -0.86), (0.012, -0.8), (0.03, -0.66), (0.034, -0.6), (0.03, -0.58), (0.0, -0.58)],
                               12, "BH_DarkSteel", "butt"))
    parts.append(ring(-0.6, 0.036, 0.012, "BH_Crimson"))
    # grip
    V, F = M.lathe([(0.0, -0.58), (0.026, -0.58), (0.024, 0.34), (0.0, 0.34)], 12)
    parts.append(outward(P_(V, F, "BH_Leather", "grip")))
    for z in (-0.4, -0.12, 0.16):
        parts.append(ring(z, 0.027, 0.008, "BH_Crimson"))
    # vamplate: a flared cone guard with four wing blades raking back over the hand
    parts.append(LK.lathe_part([(0.0, 0.32), (0.03, 0.32), (0.06, 0.36), (0.12, 0.44), (0.165, 0.52), (0.15, 0.54),
                                (0.07, 0.56), (0.0, 0.56)], 24, "BH_DragonPlate", "vamplate"))
    parts.append(ring(0.52, 0.16, 0.01, "BH_Crimson", 24))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        d = np.array([math.cos(a), math.sin(a), 0.0])
        base = d * 0.14 + np.array([0, 0, 0.5])
        parts.append(LK.fin(base, d * 0.6 + np.array([0, 0, -0.8]), 0.24, 0.05, 0.007, np.cross(d, (0, 0, 1)), -25,
                            n=8, mat="BH_DragonPlate", up=tuple(np.cross(d, (0, 0, 1)))))
    # shaft: a long tapering cone of Tyrant steel, bone rings, a crimson vein spiralling up it
    top = 1.9 if broken else 2.62

    def r_of(z):
        return 0.075 - (0.075 - 0.03) * (z - 0.56) / (2.62 - 0.56)
    prof = [(r_of(z), z) for z in np.linspace(0.56, top, 12)]
    V, F = M.lathe([(0.0, 0.56)] + prof + [(0.0, top)], 16)
    parts.append(outward(P_(V, F, "BH_DragonPlate", "shaft")))
    if broken:
        # a jagged snapped end
        for k in range(7):
            a = k * 2 * math.pi / 7
            parts.append(LK.spike((r_of(top) * 0.7 * math.cos(a), r_of(top) * 0.7 * math.sin(a), top - 0.005),
                                  (math.cos(a) * 0.3, math.sin(a) * 0.3, 1.0), 0.03 + 0.03 * (k % 3 == 0), 0.012,
                                  "BH_DragonPlate"))
    parts.append(helix(0.6, top - 0.04, lambda z: r_of(z) + 0.002, 3.5, 0.006, "BH_Emissive"))
    for z in (0.95, 1.5, 2.1):
        if z < top:
            parts.append(ring(z, r_of(z) + 0.004, 0.018, "BH_Horn", 16))
    if broken:
        return parts
    # socket, fangs, head
    parts.append(LK.lathe_part([(0.0, 2.6), (0.036, 2.6), (0.05, 2.66), (0.04, 2.72), (0.0, 2.73)], 14, "BH_DarkSteel", "socket"))
    for sx in (1, -1):
        parts.append(LK.horn((sx * 0.04, 0.0, 2.67), (sx * 0.8, 0.0, 0.6), 0.2, 0.022, (0, 1, 0), -sx * 55, n=9, mat="BH_Horn",
                             up=(0, 1, 0)))
    rings = []
    for z, w in ((2.71, 0.05), (2.78, 0.1), (2.88, 0.13), (3.0, 0.11), (3.12, 0.07), (3.22, 0.03), (3.28, 0.004)):
        hw = w / 2
        th = 0.022 * (w / 0.13) + 0.004
        rings.append(np.array([(hw, 0, z), (hw * 0.4, th * 0.6, z), (0, th, z), (-hw * 0.4, th * 0.6, z), (-hw, 0, z),
                               (-hw * 0.4, -th * 0.6, z), (0, -th, z), (hw * 0.4, -th * 0.6, z)]))
    V, F = M.loft(rings)
    parts.append(outward(P_(V, F, "BH_Steel", "head")))
    # crimson edge light and barbs raking back
    for sx in (1, -1):
        edge = [(sx * w / 2 * 1.02, 0, z) for z, w in ((2.74, 0.07), (2.88, 0.13), (3.0, 0.11), (3.12, 0.07), (3.25, 0.012))]
        parts.append(LK.edge_tube(edge, 0.0035, "BH_Emissive", name="edge"))
        for z, w in ((2.8, 0.11), (2.92, 0.13), (3.04, 0.1)):
            parts.append(LK.spike((sx * w / 2, 0, z), (sx * 0.7, 0, -0.7), 0.05, 0.008, "BH_DarkSteel"))
    V, F = M.tube([(0, 0.0, 2.72), (0, 0.0, 3.2)], [(0.004, 0.03), (0.002, 0.004)], n=6, up=(1, 0, 0))
    parts.append(P_(V, F, "BH_Emissive", "fuller"))
    return parts


# ------------------------------------------------------------------------------------------------------------ hammer
def dawnmaul():
    parts = []
    parts.append(LK.lathe_part([(0.0, -0.5), (0.03, -0.49), (0.05, -0.45), (0.045, -0.41), (0.028, -0.38), (0.0, -0.38)],
                               16, "BH_Gold", "pommel"))
    parts.append(LK.gem((0, 0, -0.515), 0.022, scale=(1, 1, 1), name="pommel_sun"))
    V, F = M.lathe([(0.0, -0.38), (0.03, -0.38), (0.028, 0.5), (0.034, 1.05), (0.0, 1.05)], 14)
    parts.append(outward(P_(V, F, "BH_Leather", "haft")))
    for z in (-0.36, 0.0, 0.3, 0.52, 0.72, 0.9):
        parts.append(ring(z, 0.034, 0.012, "BH_Gold"))
    # langets: gold straps running up to the head
    for sy in (1, -1):
        V, F = M.box(0.02, 0.008, 0.36, center=(0, sy * 0.034, 0.88))
        parts.append(P_(V, F, "BH_Gold", "langet"))
    # the head: an octagonal block along X, both faces carrying a sun disc
    zc = 1.2
    oct_r = 0.15
    rings = []
    for x, s in ((-0.3, 0.92), (-0.28, 1.0), (-0.1, 0.9), (0.0, 0.86), (0.1, 0.9), (0.28, 1.0), (0.3, 0.92)):
        pts = []
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            pts.append((x, oct_r * s * math.cos(a), zc + oct_r * s * math.sin(a)))
        rings.append(np.array(pts))
    V, F = M.loft(rings)
    parts.append(outward(M.bevel(P_(V, F, "BH_HolyPlate", "head"), 0.008, 2, angle=30)))
    for x in (-0.19, 0.0, 0.19):
        pts = []
        for k in range(9):
            a = k * math.pi / 4 + math.pi / 8
            pts.append((x, oct_r * 0.95 * math.cos(a), zc + oct_r * 0.95 * math.sin(a)))
        V, F = M.tube(pts, [(0.012, 0.012)] * 9, n=6, up=(1, 0, 0), cap0=False, cap1=False)
        parts.append(P_(V, F, "BH_Gold", "band"))
    for sx in (1, -1):
        x = sx * 0.3
        V, F = M.lathe([(0.0, 0.0), (0.12, 0.0), (0.125, 0.012), (0.09, 0.03), (0.04, 0.045), (0.0, 0.05)], 24)
        disc = outward(P_(V, F, "BH_Gold", "sun")).rot(R_axis((0, 1, 0), sx * 90)).move((x, 0, zc))
        parts.append(disc)
        parts.append(LK.gem((x + sx * 0.05, 0, zc), 0.035, scale=(0.6, 1, 1), name="sun_core"))
        for k in range(12):   # rays
            a = k * math.pi / 6
            d = np.array([0, math.cos(a), math.sin(a)])
            base = np.array([x + sx * 0.012, 0, zc]) + d * 0.11
            parts.append(LK.spike(base, d + np.array([sx * 0.15, 0, 0]), 0.06 if k % 2 == 0 else 0.035, 0.012, "BH_Gold"))
    # crown spike
    parts.append(LK.lathe_part([(0.0, zc + 0.12), (0.05, zc + 0.12), (0.04, zc + 0.2), (0.0, zc + 0.34)], 8, "BH_HolyPlate", "crown"))
    parts.append(ring(zc + 0.14, 0.05, 0.01, "BH_Gold", 8))
    return parts


# ------------------------------------------------------------------------------------------------------------ sword
def stormwake():
    parts = []
    parts.append(LK.lathe_part([(0.0, -0.24), (0.03, -0.235), (0.036, -0.21), (0.03, -0.185), (0.0, -0.18)], 12, "BH_Silver", "pommel"))
    parts.append(LK.gem((0, 0, -0.21), 0.024, name="sapphire", scale=(0.7, 1.3, 1.0)))
    V, F = M.lathe([(0.0, -0.19), (0.019, -0.19), (0.021, -0.05), (0.019, 0.08), (0.0, 0.08)], 10)
    parts.append(outward(P_(V, F, "BH_Leather", "grip")))
    for z in (-0.15, -0.06, 0.03):
        parts.append(ring(z, 0.021, 0.005, "BH_Silver", 10))
    # winged guard
    for sx in (1, -1):
        parts.append(LK.fin((sx * 0.02, 0, 0.1), (sx, 0, 0.35), 0.19, 0.03, 0.012, (0, 1, 0), -sx * 40, n=8,
                            mat="BH_Silver", up=(0, 1, 0), tip=0.8))
    V, F = M.box(0.07, 0.04, 0.05, center=(0, 0, 0.1))
    parts.append(M.bevel(P_(V, F, "BH_Silver", "guard_block"), 0.01, 2))
    parts.append(LK.gem((0, -0.021, 0.1), 0.012, name="guard_stone", scale=(1, 0.6, 1)))
    parts.append(LK.gem((0, 0.021, 0.1), 0.012, name="guard_stone", scale=(1, 0.6, 1)))
    # blade
    rings = []
    for z, w in ((0.12, 0.062), (0.4, 0.058), (0.8, 0.052), (1.02, 0.045), (1.1, 0.03), (1.15, 0.006)):
        hw, th = w / 2, 0.0065
        rings.append(np.array([(hw, 0, z), (hw * 0.5, th, z), (0, th * 0.7, z), (-hw * 0.5, th, z), (-hw, 0, z),
                               (-hw * 0.5, -th, z), (0, -th * 0.7, z), (hw * 0.5, -th, z)]))
    V, F = M.loft(rings)
    parts.append(outward(P_(V, F, "BH_Steel", "blade")))
    for sy in (1, -1):
        V, F = M.tube([(0, sy * 0.0055, 0.14), (0, sy * 0.0055, 0.98)], [(0.006, 0.0012), (0.003, 0.0012)], n=6, up=(0, 1, 0))
        parts.append(P_(V, F, "BH_Emissive", "fuller"))
    return parts


# ------------------------------------------------------------------------------------------------------------ mace
def kethrax_mace():
    parts = []
    parts.append(LK.lathe_part([(0.0, -0.36), (0.045, -0.34), (0.05, -0.3), (0.03, -0.27), (0.0, -0.27)], 8, "BH_ForsakenIron", "pommel"))
    V, F = M.lathe([(0.0, -0.27), (0.03, -0.27), (0.032, 0.72), (0.0, 0.72)], 10)
    parts.append(outward(P_(V, F, "BH_DarkSteel", "haft")))
    V, F = M.lathe([(0.0, -0.24), (0.034, -0.24), (0.034, 0.2), (0.0, 0.2)], 10)
    parts.append(outward(P_(V, F, "BH_Leather", "wrap")))
    # chain wound round the haft
    parts.append(helix(0.22, 0.66, lambda z: 0.036, 4.0, 0.009, "BH_ForsakenIron", n=70))
    # flanged head
    zc = 0.86
    parts.append(LK.lathe_part([(0.0, 0.7), (0.07, 0.72), (0.1, 0.8), (0.1, 0.94), (0.06, 1.0), (0.0, 1.02)], 12,
                               "BH_ForsakenIron", "core"))
    for k in range(7):
        a = k * 2 * math.pi / 7
        d = np.array([math.cos(a), math.sin(a), 0.0])
        outline = [(0.0, 0.0), (0.12, 0.03), (0.15, 0.12), (0.1, 0.26), (0.0, 0.3)]
        pts = []
        for u, v in outline:
            pts.append(d * (0.05 + u) + np.array([0, 0, 0.72 + v]))
        # plate in the (d, z) plane with thickness along the tangent
        V, F = M.prism([(p @ d, p[2]) for p in pts], 0.022, axis="y")
        fl = P_(V, F, "BH_ForsakenIron", "flange")
        fl.V = np.array([d * v[0] + np.cross((0, 0, 1), d) * v[1] + np.array([0, 0, v[2]]) for v in fl.V])
        parts.append(outward(fl))
        parts.append(LK.spike(d * 0.19 + np.array([0, 0, zc]), d + np.array([0, 0, 0.1]), 0.07, 0.012, "BH_DarkSteel"))
        V, F = M.box(0.012, 0.012, 0.12, center=(0, 0, 0))
        rs = P_(V, F, "BH_Emissive", "rune")
        rs.move(d * 0.103 + np.array([0, 0, zc]))
        parts.append(rs)
    parts.append(LK.spike((0, 0, 1.0), (0, 0, 1), 0.14, 0.03, "BH_DarkSteel"))
    # a short hanging chain with a hook
    links = []
    p0 = np.array([0.03, 0.0, 0.7])
    for i in range(5):
        c = p0 + np.array([0.012 * i, 0.0, -0.05 * i])
        axis = (0, 1, 0) if i % 2 == 0 else (1, 0, 0)
        pts = LK.curve_pts(c + np.array([0, 0, 0.022]), (0, 0, -1), 0.0001, None, 0, 2)
        ring_pts = [c + R_axis(axis, a) @ np.array([0, 0, 0.026]) * np.array([1, 1, 1]) for a in np.linspace(0, 360, 13)]
        V, F = M.tube(ring_pts, [(0.006, 0.006)] * 13, n=5, up=axis, cap0=False, cap1=False)
        links.append(P_(V, F, "BH_ForsakenIron", "link"))
    parts += links
    parts.append(LK.horn(p0 + np.array([0.06, 0, -0.27]), (0, 0, -1), 0.1, 0.012, (0, 1, 0), 160, n=8, mat="BH_DarkSteel"))
    return parts


def dusk_piercer_tip():
    """The Dusk-Piercer Shard: the broken head of the lance (socket stub, fangs, barbed blade), resting on a palm.
    Origin at its middle, +Z toward the point; about 0.5 m long."""
    parts = [p for p in dusk_piercer() if p.name in ("socket", "horn", "head", "edge", "spike", "fuller")]
    out = []
    for p in parts:
        c = p.V[:, 2].mean() if len(p.V) else 0.0
        if c < 2.55:
            continue
        q = p.copy()
        q.V = q.V - np.array([0.0, 0.0, 2.9])
        out.append(q)
    # the jagged break below the socket
    for k in range(6):
        a = k * 2 * math.pi / 6
        out.append(LK.spike((0.028 * math.cos(a), 0.028 * math.sin(a), -0.3), (math.cos(a) * 0.4, math.sin(a) * 0.4, -1.0),
                            0.04 + 0.02 * (k % 2), 0.012, "BH_DragonPlate"))
    return out


WEAPONS = {"dusk_piercer_tip": dusk_piercer_tip, "dusk_piercer": dusk_piercer, "dusk_piercer_broken": lambda: dusk_piercer(True), "dawnmaul": dawnmaul,
           "stormwake": stormwake, "kethrax_mace": kethrax_mace}


def build(name):
    import bh_materials as MT
    mats = MT.make_materials(name, vertex_color=False, extra=PALETTES[name])
    ob = M.build_static(name, WEAPONS[name](), mats)
    LK.finish_mesh(ob)
    MT.bake_vertex_ao(ob, rays=16, dist=0.12, strength=0.5)
    return ob


def main():
    import bpy
    import build as B
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = [a for a in argv if a in WEAPONS] or list(WEAPONS)
    os.makedirs(OUT, exist_ok=True)
    for n in names:
        B.reset()
        ob = build(n)
        path = os.path.join(OUT, n + ".glb")
        B.export_glb(path, [ob], animations=False)
        print(f"[legend weapon] {n}: {M.tri_count(ob)} tris -> {path}")


if __name__ == "__main__":
    main()
