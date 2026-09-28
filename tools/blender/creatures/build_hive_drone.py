"""Hive Drone (bh-013, Builder D): a giant wasp, ~0.9 m long. Static multi-node FLOATING model animated by the game
(wisp convention + the bh-013 insect wings).

  "<blender>" -b --factory-startup --python build_hive_drone.py -- [--out game/assets/characters/hive_drone.glb]
                                                                   [--preview DIR] [--no-export]

Nodes (all meshes, no armature, origin = creature centre, Blender Z-up -> glTF Y-up, head toward -Y = Godot +Z):
  core      head (big faceted amber eyes, amber face plate, mandibles, antennae), glossy black thorax with amber
            marks, petiole, drooping amber/black striped abdomen with a long black stinger, six dangling legs
  wing_l    (child of core) left fore + hind wing, node origin = wing root on the thorax top (+X side); the wings
            spread along local +X, so the game's flap about local Z (Godot) = the body's long axis beats them up/down
  wing_r    (child of core) mirror of wing_l at the -X root
drone() is reused by build_hive_nest.py for the dormant drones clinging to the hive.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_d13_float as K  # noqa: E402
from kit_d13_float import M, P, np, blob, place  # noqa: E402

CID = "hive_drone"
PALETTE_COLORS = {
    "BH_Horn": ((0.03, 0.025, 0.025), 0.0, 0.26, None, 0.0, 1.0),                  # glossy black chitin
    "BH_Gold": ((0.95, 0.56, 0.06), 0.0, 0.36, None, 0.0, 1.0),                    # amber chitin stripes
    "BH_Aether": ((0.78, 0.79, 0.76), 0.0, 0.3, None, 0.0, 1.0),                   # pale smoky wing membrane
    "BH_Emissive": ((0.62, 0.24, 0.03), 0.0, 0.2, (1.0, 0.42, 0.05), 2.5, 1.0),   # faint deep-amber eyes
}
SCALE = 0.9
SHIFT = np.array([0.0, -0.045, 0.0])      # centre the body (mandibles .. stinger) on the origin


def _abd(t):
    return np.array([0.0, 0.40 * t, -0.01 - 0.15 * t ** 1.6])


def _abd_r(t):
    return 0.135 * max(math.sin(math.pi * (0.1 + 0.82 * t)), 0.0) ** 0.75 + 0.012


def wing_parts(fore=True, lod=1.0):
    """Left wing blade in wing-root-local space, spread along +X, leading edge toward -Y, slight dihedral."""
    L, cmax, sweep, off = (0.5, 0.13, 0.11, (0, 0, 0)) if fore else (0.32, 0.085, 0.14, (0.0, 0.055, -0.012))
    dih = math.tan(math.radians(9))

    def fn(u, v):
        c = cmax * (0.4 + 0.6 * math.sin(math.pi * min(u * 0.95 + 0.05, 1.0)) ** 0.5) * (1 - 0.65 * u ** 6)
        x = L * u
        y = -0.02 + sweep * u ** 1.4 + v * c
        z = x * dih + 0.008 * math.sin(math.pi * v)
        return (x + off[0], y + off[1], z + off[2])
    parts = [K.sheet(fn, max(5, int(9 * lod)), 3, "BH_Aether", 0.005, "wing")]
    costa = [np.array(fn(u, 0.0)) + (0, 0, 0.004) for u in np.linspace(0.0, 0.93, 6)]
    V, F = M.tube(costa, [(0.007, 0.006)] * 3 + [(0.005, 0.004)] * 2 + [(0.002, 0.002)], n=4, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Horn", "vein"))
    mid = [np.array(fn(u, 0.42)) + (0, 0, 0.005) for u in np.linspace(0.0, 0.7, 4)]
    V, F = M.tube(mid, [(0.004, 0.003)] * 3 + [(0.0015, 0.0015)], n=4, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Horn", "vein"))
    return parts


WING_ROOT = np.array([0.05, -0.2, 0.11])


def drone(lod=1.0, eye_mat="BH_Emissive", folded=False):
    """Returns (body parts, left-wing parts in wing-root space, left wing root) in unscaled, unshifted space.
    folded=True merges wings folded back over the abdomen into the body parts (for the nest's dormant drones)."""
    n16, n12, n8, n5 = (max(6, int(k * lod)) for k in (16, 12, 8, 5))
    parts = []
    # head, faceted eyes, face plate, mandibles, antennae
    parts.append(blob((0, -0.34, 0.03), (0.085, 0.075, 0.08), "BH_Horn", n12, max(6, int(8 * lod)), "head"))
    for sx in (1, -1):
        parts.append(blob((sx * 0.058, -0.352, 0.045), (0.042, 0.058, 0.068), eye_mat, 8, 6, "eye"))
        V, F = M.tube([(sx * 0.03, -0.395, -0.02), (sx * 0.036, -0.44, -0.04), (sx * 0.012, -0.462, -0.052)],
                      [(0.015, 0.012), (0.01, 0.008), (0.002, 0.002)], n=n5, up=(0, 0, 1))
        parts.append(P(V, F, "BH_Gold", "mandible"))
        V, F = M.tube([(sx * 0.025, -0.385, 0.085), (sx * 0.06, -0.44, 0.16), (sx * 0.1, -0.51, 0.2),
                       (sx * 0.13, -0.57, 0.19)], [(0.009, 0.009), (0.007, 0.007), (0.006, 0.006), (0.004, 0.004)],
                      n=n5, up=(0, 0, 1))
        parts.append(P(V, F, "BH_Horn", "antenna"))
    parts.append(blob((0, -0.405, 0.02), (0.04, 0.02, 0.05), "BH_Gold", 8, 6, "face"))
    # thorax + amber marks, petiole
    parts.append(blob((0, -0.18, 0.04), (0.1, 0.12, 0.095), "BH_Horn", n16, max(6, int(10 * lod)), "thorax"))
    for sx in (1, -1):
        parts.append(blob((sx * 0.055, -0.235, 0.105), (0.03, 0.045, 0.014), "BH_Gold", 8, 4, "mark"))
    parts.append(blob((0, -0.1, 0.11), (0.05, 0.022, 0.016), "BH_Gold", 8, 4, "scutellum"))
    V, F = M.tube([(0, -0.08, 0.01), (0, -0.035, 0.0), (0, 0.01, -0.012)], [(0.032, 0.03), (0.018, 0.017),
                                                                               (0.03, 0.028)], n=n8, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Horn", "petiole"))
    # abdomen: overlapping amber / black bands (each band flares a little at its rear edge, like tergites)
    bounds = [0.0, 0.13, 0.3, 0.37, 0.54, 0.6, 0.76, 0.82, 1.0]
    mats = ["BH_Horn", "BH_Gold", "BH_Horn", "BH_Gold", "BH_Horn", "BH_Gold", "BH_Horn", "BH_Gold"]
    for (t0, t1, mt) in zip(bounds[:-1], bounds[1:], mats):
        ts = np.linspace(t0, t1 + 0.015, 3)
        pts = [_abd(t) for t in ts]
        prof = [(_abd_r(t) * (1 + 0.05 * k), _abd_r(t) * 0.88 * (1 + 0.05 * k)) for k, t in enumerate(ts)]
        V, F = M.tube(pts, prof, n=n16, up=(0, 0, 1))
        parts.append(P(V, F, mt, "abdomen"))
    d = K.normalize(_abd(1.0) - _abd(0.9))
    V, F = M.lathe([(0, 0.0), (0.024, 0.01), (0.011, 0.08), (0, 0.18)], 6)
    parts.append(place(P(V, F, "BH_Horn", "stinger"), d, _abd(0.96)))
    # six dangling legs (black femur, amber tibia/tarsus), hind legs longer and trailing
    for k, y in enumerate((-0.235, -0.18, -0.125)):
        for sx in (1, -1):
            r = np.array([sx * 0.055, y, -0.02])
            j1 = r + (sx * (0.1 + 0.02 * k), -0.03 + 0.03 * k, -0.05)
            j2 = j1 + (sx * 0.03, 0.03 + 0.05 * k, -0.14 - 0.03 * k)
            tip = j2 + (sx * 0.005, 0.04 + 0.04 * k, -0.09 - 0.02 * k)
            V, F = M.tube([r, j1, j2], [(0.016, 0.016), (0.013, 0.013), (0.01, 0.01)], n=n5, up=(0, 0, 1))
            parts.append(P(V, F, "BH_Horn", "leg"))
            V, F = M.tube([j2, (j2 + tip) / 2, tip], [(0.009, 0.009), (0.007, 0.007), (0.003, 0.003)], n=n5,
                          up=(0, 0, 1))
            parts.append(P(V, F, "BH_Gold", "tarsus"))
    wl = wing_parts(True, lod) + wing_parts(False, lod)
    if folded:
        for sx in (1, -1):
            for p in wl:
                q = p.copy().rot(K.Rz(76)).move((0, 0, 0.012))
                if sx < 0:
                    q = q.mirrored(False)
                parts.append(q.move(WING_ROOT * (sx, 1, 1) + (0, 0, -0.03)))
        wl = []
    return parts, wl, WING_ROOT


def build():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K.MT.make_materials(CID, vertex_color=False, extra=PALETTE_COLORS)
    body, wl, root = drone()
    for p in body + wl:
        p.V = p.V * SCALE
    for p in body:
        p.V = p.V + SHIFT * SCALE
    core = K.node("core", body, mats, sharp=35, ao=(12, 0.1, 0.4))
    rl = (root + SHIFT) * SCALE
    wing_l = K.node("wing_l", wl, mats, loc=tuple(rl), parent=core, sharp=50, ao=(6, 0.05, 0.15))
    wing_r = K.node("wing_r", [p.mirrored(False) for p in wl], mats, loc=(-rl[0], rl[1], rl[2]), parent=core,
                    sharp=50, ao=(6, 0.05, 0.15))
    return [core, wing_l, wing_r]


if __name__ == "__main__":
    K.run(CID, build, dict(ground_z=-1.2, look=(0, 0, -0.1), dist=2.6, close=((0, -0.25, 0.05), 1.1, 25, 18)))
