"""Void Rift (bh-013, Builder D): a torn portal in space, ~2.4 m tall, ~1.4 m wide. Static multi-node FLOATING model
animated by the game (wisp convention). Hovers low: the bottom of the tear is ~1.13 m below the origin.

  "<blender>" -b --factory-startup --python build_void_rift.py -- [--out game/assets/characters/void_rift.glb]
                                                                  [--preview DIR] [--no-export]

The tear is authored in the XZ plane facing -Y (= Godot +Z, the creature's front) and tilted back 20 deg (top toward
+Y) so the high gameplay camera looks into it. Nodes (all meshes, no armature, origin = creature centre):
  core      (node rotation X -20 deg) jagged vesica-shaped tear: a violet-black vortex funnel receding ~0.35 m into
            the tear, seven emissive violet / magenta spiral streaks swirling into a glowing magenta eye, a glowing
            magenta lip, a jagged obsidian crust and 10 broken obsidian shards jutting from the rim
  ring_1    9 floating obsidian shards (some violet-glowing) orbiting in the tear's plane, r 0.85 m (node rot X 70 deg:
            its local up = the tear's normal, so the game's spin about local up turns it in the tear's plane)
  ring_2    11 larger obsidian shards, r 1.15 m, rot (64, 8) deg - a few degrees off the tear plane for depth
  ring_3    8 drifting violet/magenta motes circling horizontally (rot 0) at r 0.8-1.3 m, z +-0.5 m
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_d13_float as K  # noqa: E402
from kit_d13_float import M, P, np, blob, place, orient  # noqa: E402

CID = "void_rift"
PALETTE_COLORS = {
    "BH_Shadow": ((0.02, 0.0, 0.04), 0.0, 0.9, None, 0.0, 1.0),                   # the void
    "BH_Emissive": ((0.62, 0.3, 1.0), 0.0, 0.3, (0.62, 0.25, 1.0), 8.0, 1.0),     # violet streaks, glints
    "BH_Aether": ((1.0, 0.35, 0.8), 0.0, 0.3, (1.0, 0.25, 0.72), 6.0, 1.0),       # magenta lip, streaks, eye
    "BH_Horn": ((0.05, 0.04, 0.07), 0.2, 0.12, None, 0.0, 1.0),                   # glossy obsidian
    "BH_Stone": ((0.2, 0.16, 0.28), 0.0, 0.2, None, 0.0, 1.0),                    # violet-grey obsidian facets
}
RX, RZ, N = 0.56, 0.98, 56
TILT = -20.0


def outline(t, jag=True):
    """Point on the tear rim (x across, z up) for angle t (0 = top)."""
    s = math.sin(t)
    x = RX * s * abs(s) ** 0.25
    z = RZ * math.cos(t)
    if jag:
        i = int(round(t / (2 * math.pi) * N)) % N
        h = (math.sin(i * 12.9898 + 4.1) * 43758.5453) % 1.0          # deterministic per-vertex tear jitter
        f = 1 + 0.045 * math.sin(7 * t + 1.3) + 0.03 * math.sin(13 * t) + 0.07 * (h - 0.4)
        x, z = x * f, z * f
    return np.array([x, 0.0, z])


def funnel(s, t):
    """Vortex surface: s = 1 at the rim, 0 at the deep centre (recedes toward +Y)."""
    return outline(t) * (0.96 * s) + (0, 0.36 * (1 - s ** 1.4), 0)


def core_parts():
    parts = []
    ts = [2 * math.pi * i / N for i in range(N)]
    V, F = M.grid(lambda u, v: funnel(1 - v, 2 * math.pi * u), N, 8, closed_u=True)
    parts.append(M.solidify(orient(P(V, F, "BH_Shadow", "vortex"), (0, 4.0, 0)), 0.02, offset=-1.0))
    for j in range(7):                                   # spiral streaks swirling inward
        t0 = 2 * math.pi * j / 7

        def arm(u, v, t0=t0, j=j):
            s = 0.97 - 0.9 * v
            t = t0 + 3.2 * v
            c = funnel(s, t)
            tan = funnel(s, t + 0.05) - funnel(s, t - 0.05)
            tan = tan / (np.linalg.norm(tan) + 1e-9)
            w = (0.15 * (1 - v) + 0.015) * (1.0 if j % 2 else 0.75)
            return c + tan * (u - 0.5) * w + (0, -0.02, 0)
        V, F = M.grid(arm, 2, 22)
        parts.append(orient(P(V, F, "BH_Emissive" if j % 2 else "BH_Aether", "streak"), (0, 4.0, 0)))
    parts.append(blob((0, 0.3, 0), (0.1, 0.05, 0.13), "BH_Aether", 10, 6, "eye"))
    parts.append(blob((0, 0.26, 0), (0.04, 0.03, 0.05), "BH_Emissive", 8, 5, "eye_core"))

    def lip(u, v):                                       # glowing magenta lip just inside the rim
        t = 2 * math.pi * u
        return outline(t) * (0.9 + 0.12 * v) + (0, 0.02 * (1 - v) - 0.01, 0)
    V, F = M.grid(lip, N, 2, closed_u=True)
    parts.append(M.solidify(orient(P(V, F, "BH_Aether", "lip"), (0, 4.0, 0)), 0.02, offset=0.0))

    def crust(u, v):                                     # jagged obsidian crust around the tear
        t = 2 * math.pi * u
        i = int(round(u * N)) % N
        grow = 0.1 + (0.1 if i % 3 == 0 else 0.03)
        return outline(t) * (1.0 + grow * v) + (0, -0.03 + 0.06 * v * v, 0)
    V, F = M.grid(crust, N, 3, closed_u=True)
    parts.append(M.solidify(orient(P(V, F, "BH_Horn", "crust"), (0, 4.0, 0)), 0.05, offset=0.0))
    rng = np.random.default_rng(13)
    for k in range(10):                                  # broken shards jutting from the rim
        t = 2 * math.pi * (k + 0.3 * rng.random()) / 10
        o = outline(t, False)
        d = K.normalize(o * (1, 0, 1) / np.array([RX, 1, RZ]) ** 2 + (0, -0.25 + 0.3 * rng.random(), 0))
        L = 0.16 + 0.14 * rng.random()
        sh = K.shard(L, 0.05 + 0.02 * rng.random(), sides=4, mat="BH_Horn" if k % 3 else "BH_Stone", seed=k)
        sh.V[:, 2] += L * 0.28
        parts.append(place(sh, d, o * 1.04))
    return parts


def shard_ring(radius, n, size, seed, glow_every=3):
    rng = np.random.default_rng(seed)
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n + (rng.random() - 0.5) * 0.3
        r = radius * (0.92 + 0.16 * rng.random())
        L = size * (0.7 + 0.6 * rng.random())
        sh = K.shard(L, L * 0.22, sides=4, mat="BH_Horn" if i % 2 else "BH_Stone", seed=seed + i, jitter=0.4)
        d = K.normalize(np.array([math.cos(a), math.sin(a), 0]) * rng.random() +
                        np.array([-math.sin(a), math.cos(a), 0]) + (0, 0, 0.6 * (rng.random() - 0.5)))
        c = (r * math.cos(a), r * math.sin(a), 0.05 * (rng.random() - 0.5))
        parts.append(place(sh, d, c))
        if i % glow_every == 0:
            g = K.shard(L * 0.45, L * 0.08, sides=3, mat="BH_Emissive", seed=seed + 50 + i)
            parts.append(place(g, d, np.array(c) + (0, 0, L * 0.12)))
    return parts


def mote_ring():
    rng = np.random.default_rng(7)
    parts = []
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.3 * rng.random()
        r = 0.8 + 0.5 * rng.random()
        c = (r * math.cos(a), r * math.sin(a), (rng.random() - 0.5) * 1.0)
        sz = 0.035 + 0.03 * rng.random()
        V, F = M.lathe([(0, -sz * 1.6), (sz, 0), (0, sz * 1.6)], 4, a0=45)
        parts.append(P(V, F, "BH_Aether" if i % 2 else "BH_Emissive", "mote").rot(K.Rx(30 * i)).move(c))
    return parts


def build():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K.MT.make_materials(CID, vertex_color=False, extra=PALETTE_COLORS)
    obs = [K.node("core", core_parts(), mats, rot=(TILT, 0, 0), sharp=40, ao=(10, 0.12, 0.35))]
    obs.append(K.node("ring_1", shard_ring(0.85, 9, 0.24, 21), mats, rot=(90 + TILT, 0, 0), sharp=30, ao=(4, 0.03, 0.1)))
    obs.append(K.node("ring_2", shard_ring(1.15, 11, 0.32, 41), mats, rot=(64, 8, 0), sharp=30, ao=(4, 0.03, 0.1)))
    obs.append(K.node("ring_3", mote_ring(), mats, sharp=30, ao=(4, 0.03, 0.1)))
    return obs


if __name__ == "__main__":
    K.run(CID, build, dict(ground_z=-1.2, look=(0, 0, -0.1), dist=5.6, close=((0, 0, 0.1), 2.6, 15, 25)))
