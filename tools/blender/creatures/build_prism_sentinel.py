"""Prism Sentinel (bh-013, Builder D): floating crystal construct, ~1.8 m. Static multi-node FLOATING model animated by
the game (wisp convention, same as build_ice_wraith.py).

  "<blender>" -b --factory-startup --python build_prism_sentinel.py -- [--out game/assets/characters/prism_sentinel.glb]
                                                                       [--preview DIR] [--no-export]

Nodes (all meshes, no armature, origin = creature centre, Blender Z-up -> glTF Y-up, front toward -Y = Godot +Z):
  core      a large faceted double-pyramid crystal (1.3 m tall, 8 facets, alternating cyan / pale-cyan glow) clamped
            top and bottom by bronze collars and weathered stone prongs with bronze finial spikes (+-0.92 m), and one
            big lens-eye on the front facet (bronze bezel, dark iris ring, blazing white-cyan lens) at about (0, -0.40, 0):
            the beam origin. Forward = -Y (Blender) = +Z (Godot), like ice_wraith.
  ring_1    bronze gyroscope band r 0.76 m, near-vertical (tilt 70, 0 deg), 4 stone clamps each carrying a cyan prism shard
  ring_2    bronze gyroscope band r 0.86 m, tilted (18, 52) deg, 5 stone clamps + prism shards
  ring_3    three small orbiting lens crystals (bronze rims) at r 1.0 m, tilt (-10, 0) deg
Each ring lies in its node's local XY plane (Blender) = XZ (Godot) and is spun by the game about its LOCAL up axis.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_d13_float as K  # noqa: E402
from kit_d13_float import M, P, np, blob, place  # noqa: E402

CID = "prism_sentinel"
PALETTE_COLORS = {
    "BH_Bronze": ((0.6, 0.38, 0.16), 0.9, 0.35, None, 0.0, 1.0),                  # gyroscope rings, collars
    "BH_Stone": ((0.5, 0.48, 0.44), 0.0, 0.85, None, 0.0, 1.0),                   # weathered stone prongs / clamps
    "BH_Aether": ((0.55, 0.9, 1.0), 0.0, 0.15, (0.45, 0.88, 1.0), 3.0, 1.0),      # cyan crystal facets, shards
    "BH_Ichor": ((0.8, 0.97, 1.0), 0.0, 0.1, (0.7, 0.95, 1.0), 1.5, 1.0),         # pale crystal facets, lenses
    "BH_Emissive": ((0.9, 1.0, 1.0), 0.0, 0.2, (0.8, 1.0, 1.0), 12.0, 1.0),       # the lens-eye
    "BH_Shadow": ((0.02, 0.03, 0.05), 0.0, 0.6, None, 0.0, 1.0),                  # iris ring
}
CRYSTAL = [(0, -0.54), (0.2, -0.24), (0.28, 0.0), (0.2, 0.25), (0, 0.54)]


def core_parts():
    parts = []
    for k in range(8):                                   # faceted double pyramid, alternating facet tones
        a0 = 22.5 + 45 * k
        V, F = M.lathe(CRYSTAL, 2, a0=a0, a1=a0 + 45, cap=False)
        parts.append(P(V, F, "BH_Aether" if k % 2 == 0 else "BH_Ichor", "facet"))
    for sz in (1, -1):                                   # clamps: bronze collar, stone prongs, finial spike
        prof = [(0.135, 0.33), (0.165, 0.35), (0.165, 0.4), (0.12, 0.43), (0.06, 0.45)]
        V, F = M.lathe([(r, sz * z) for r, z in prof] if sz > 0 else [(r, sz * z) for r, z in prof[::-1]], 12)
        parts.append(P(V, F, "BH_Bronze", "collar"))
        for j in range(4):
            a = math.radians(45 + 90 * j)
            d = np.array([math.cos(a), math.sin(a), 0.0])
            base = d * 0.15 + (0, 0, sz * 0.36)
            tip = d * 0.07 + (0, 0, sz * 0.56)
            V, F = M.tube([base - (0, 0, sz * 0.05), base + d * 0.03 + (0, 0, sz * 0.08), tip],
                          [(0.035, 0.03, 4), (0.03, 0.026, 4), (0.012, 0.012, 4)], n=6, up=tuple(d))
            parts.append(P(V, F, "BH_Stone", "prong"))
        V, F = M.lathe([(0, sz * 0.44), (0.05, sz * 0.46), (0.04, sz * 0.52), (0.02, sz * 0.6), (0, sz * 0.77)]
                       if sz > 0 else [(0, -0.77), (0.02, -0.6), (0.04, -0.52), (0.05, -0.46), (0, -0.44)], 8)
        parts.append(P(V, F, "BH_Bronze", "finial"))
        parts.append(blob((0, 0, sz * 0.6), (0.055, 0.055, 0.03), "BH_Stone", 8, 4, "finial_stone"))
    # the lens-eye on the front facet (-Y)
    fy = -0.28 * math.cos(math.radians(22.5))
    ring = [(0.13 * math.cos(t), 0, 0.13 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 25)]
    V, F = M.tube([np.array(p) + (0, fy - 0.03, 0) for p in ring], [(0.022, 0.03, 4)] * 25, n=6, up=(0, -1, 0))
    parts.append(P(V, F, "BH_Bronze", "bezel"))
    V, F = M.lathe([(0.12, 0.0), (0.115, 0.02), (0.088, 0.03)], 20, cap=False)
    parts.append(place(P(V, F, "BH_Shadow", "iris"), (0, -1, 0), (0, fy - 0.02, 0)))
    V, F = M.lathe([(0.09, 0.02), (0.075, 0.045), (0.045, 0.062), (0, 0.068)], 20)
    parts.append(place(P(V, F, "BH_Emissive", "lens"), (0, -1, 0), (0, fy - 0.02, 0)))
    for j in range(4):
        a = math.radians(45 + 90 * j)
        c = np.array([0.15 * math.cos(a), fy - 0.035, 0.15 * math.sin(a)])
        V, F = M.box(0.04, 0.05, 0.04, center=c)
        parts.append(P(V, F, "BH_Bronze", "bezel_tooth").rot(K.Ry(-math.degrees(a)), center=c))
    return parts


def gyro_ring(radius, n_clamps, seed):
    rng = np.random.default_rng(seed)
    parts = []
    pts = [(radius * math.cos(t), radius * math.sin(t), 0) for t in np.linspace(0, 2 * math.pi, 49)]
    V, F = M.tube(pts, [(0.024, 0.06, 4)] * 49, n=8, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Bronze", "band"))
    for s in (1, -1):                                    # raised rims on both faces of the band
        V, F = M.tube([(p[0] * 1.0, p[1], s * 0.05) for p in pts], [(0.03, 0.012)] * 49, n=6, up=(0, 0, 1))
        parts.append(P(V, F, "BH_Bronze", "rim"))
    for i in range(n_clamps):
        a = 2 * math.pi * i / n_clamps + 0.3
        d = np.array([math.cos(a), math.sin(a), 0.0])
        V, F = M.box(0.1, 0.13, 0.13)
        blk = P(V, F, "BH_Stone", "clamp").rot(K.Rz(math.degrees(a))).move(d * radius)
        parts.append(blk)
        L = 0.2 + 0.06 * rng.random()
        sh = K.shard(L, 0.045, sides=6, mat="BH_Aether", seed=seed * 10 + i, jitter=0.12)
        sh.V[:, 2] += L * 0.3
        parts.append(place(sh, d + (0, 0, 0.15 * (rng.random() - 0.5)), d * (radius + 0.04)))
    for i in range(12):                                  # bronze studs between the clamps
        a = 2 * math.pi * (i + 0.5) / 12
        parts.append(blob((radius * math.cos(a), radius * math.sin(a), 0), (0.03, 0.03, 0.075), "BH_Bronze", 6, 3,
                          "stud"))
    return parts


def lens_ring(radius=1.0, n=3):
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = np.array([math.cos(a), math.sin(a), 0.0])
        c = d * radius
        V, F = M.sphere(1.0, 12, 6, scale=(0.075, 0.075, 0.025))
        parts.append(place(P(V, F, "BH_Ichor", "lens"), d, c))
        rim = [(0.08 * math.cos(t), 0.08 * math.sin(t), 0) for t in np.linspace(0, 2 * math.pi, 17)]
        V, F = M.tube(rim, [(0.012, 0.018)] * 17, n=5, up=(0, 0, 1))
        parts.append(place(P(V, F, "BH_Bronze", "lens_rim"), d, c))
        V, F = M.lathe([(0, -0.1), (0.018, -0.02), (0.0, 0.06)], 6)
        parts.append(place(P(V, F, "BH_Aether", "lens_shard"), d, c - d * 0.02 + (0, 0, 0.0)).move((0, 0, 0)))
    return parts


CORE_SCALE = 1.2        # authored small, scaled up: crystal 1.3 m tall, finials +-0.92 m, lens at y -0.39
RINGS = [("ring_1", 0.76, 4, (70, 0, 0)), ("ring_2", 0.86, 5, (18, 52, 0))]


def build():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K.MT.make_materials(CID, vertex_color=False, extra=PALETTE_COLORS)
    cp = core_parts()
    for p in cp:
        p.V = p.V * CORE_SCALE
    obs = [K.node("core", cp, mats, sharp=30, ao=(12, 0.12, 0.35))]
    for i, (name, r, nc, rot) in enumerate(RINGS):
        obs.append(K.node(name, gyro_ring(r, nc, 60 + i), mats, rot=rot, sharp=30, ao=(8, 0.08, 0.3)))
    obs.append(K.node("ring_3", lens_ring(), mats, rot=(-10, 0, 0), sharp=30, ao=(6, 0.05, 0.2)))
    return obs


if __name__ == "__main__":
    K.run(CID, build, dict(ground_z=-1.2, look=(0, 0, -0.1), dist=5.2, close=((0, -0.3, 0.0), 1.6, 25, 12)))
