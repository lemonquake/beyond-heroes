"""Waxen Hive (bh-013, Builder D, id hive_nest): a static ground structure, ~2.4 m tall, ~2.2 m wide, origin at ground
level under the mound's centre (like war_totem). Static node model animated by the game (float_hover = 0).

  "<blender>" -b --factory-startup --python build_hive_nest.py -- [--out game/assets/characters/hive_nest.glb]
                                                                  [--preview DIR] [--no-export]

Nodes (all meshes, no armature, Blender Z-up -> glTF Y-up, front toward -Y = Godot +Z):
  core      the whole living mound (node origin at ground level, so the game's core pulse swells it upward from its
            footprint): lumpy tiered wax body in ochre / pale-amber bands, 4 patches of hexagonal comb cells (honey-filled,
            wax-capped or empty), 6 raised round entrance holes with a dark throat and a warm amber glow (BH_Emissive),
            9 dripping honey ribs with drop bulbs, two dormant hive drones clinging to it (wings folded)
  base      dead roots and stones around the foot (static, not pulsed)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_d13_float as K  # noqa: E402
from kit_d13_float import M, P, np, blob, place, orient  # noqa: E402
import build_hive_drone as D  # noqa: E402

CID = "hive_nest"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.62, 0.4, 0.14), 0.0, 0.7, None, 0.0, 1.0),           # ochre wax
    "BH_Cloth_Secondary": ((0.88, 0.66, 0.3), 0.0, 0.55, None, 0.0, 1.0),        # pale amber wax, comb walls, collars
    "BH_Ichor": ((0.85, 0.45, 0.04), 0.0, 0.12, None, 0.0, 1.0),                 # glossy honey
    "BH_Shadow": ((0.03, 0.015, 0.005), 0.0, 0.9, None, 0.0, 1.0),               # empty cells, entrance throats
    "BH_Emissive": ((1.0, 0.6, 0.15), 0.0, 0.3, (1.0, 0.52, 0.1), 6.0, 1.0),     # warm glow inside the entrances
    "BH_Wood": ((0.22, 0.17, 0.12), 0.0, 0.9, None, 0.0, 1.0),                   # dead roots
    "BH_Stone": ((0.4, 0.37, 0.33), 0.0, 0.9, None, 0.0, 1.0),                   # stones
    "BH_Horn": D.PALETTE_COLORS["BH_Horn"],                                      # drones: black chitin
    "BH_Gold": D.PALETTE_COLORS["BH_Gold"],                                      # drones: amber chitin
    "BH_Aether": D.PALETTE_COLORS["BH_Aether"],                                  # drones: folded wings
}
PZ = [0.0, 0.15, 0.5, 0.9, 1.3, 1.7, 2.0, 2.22, 2.36]
PR = [1.0, 1.08, 1.06, 0.97, 0.84, 0.66, 0.46, 0.24, 0.07]
_rng = np.random.default_rng(5)
LUMPS = [(_rng.random() * 2 * math.pi, 0.2 + 1.9 * _rng.random(), 0.07 + 0.09 * _rng.random()) for _ in range(16)]


def surf(a, v):
    """Mound surface point for angle a (0 = front -Y) and height parameter v in [0, 1]."""
    z = float(np.interp(v, np.linspace(0, 1, len(PZ)), PZ))
    r = float(np.interp(z, PZ, PR))
    r += 0.05 * math.sin(z * 10.5 + 0.6 * math.sin(3 * a)) * min(1.0, z * 3)     # wax tiers
    for (la, lz, amp) in LUMPS:
        da = math.atan2(math.sin(a - la), math.cos(a - la))
        r += amp * math.exp(-(da / 0.45) ** 2 - ((z - lz) / 0.3) ** 2) * min(1.0, r)
    x, y = r * math.sin(a), -r * math.cos(a)
    return np.array([x + 0.05 * z * z * 0.2, y + 0.04 * z, z])


def surf_n(a, v):
    e = 1e-3
    da = surf(a + e, v) - surf(a - e, v)
    dv = surf(a, min(v + e, 1)) - surf(a, max(v - e, 0))
    return K.normalize(np.cross(da, dv))


def v_of(z):
    return float(np.interp(z, PZ, np.linspace(0, 1, len(PZ))))


def mound_parts():
    parts = []
    bands = [0.0, 0.14, 0.3, 0.46, 0.62, 0.8, 1.0]
    for k, (v0, v1) in enumerate(zip(bands[:-1], bands[1:])):
        nv = max(2, int(round((v1 - v0) * 22)) + 1)
        V, F = M.grid(lambda u, v, v0=v0, v1=v1: surf(2 * math.pi * u, v0 + (v1 - v0) * v), 34, nv, closed_u=True)
        parts.append(orient(P(V, F, "BH_Cloth_Primary" if k % 2 == 0 else "BH_Cloth_Secondary", "mound"),
                            (0, 0, 1.0)))
    parts.append(blob((0.0, 0.09, 2.36), (0.12, 0.12, 0.08), "BH_Cloth_Secondary", 10, 5, "cap"))
    return parts


def comb_parts():
    parts = []
    rng = np.random.default_rng(9)
    ro, ri = 0.075, 0.058
    patches = [(-0.55, 0.95, 0.36), (1.05, 1.45, 0.3), (2.6, 1.0, 0.34), (-2.1, 1.65, 0.26), (0.35, 1.95, 0.22)]
    for (ac, zc, pr) in patches:
        rc = float(np.interp(zc, PZ, PR))
        dx, dz = 2 * ro * math.cos(math.radians(30)), 1.5 * ro
        for row in range(-6, 7):
            for col in range(-6, 7):
                sx = (col + 0.5 * (row % 2)) * dx
                sz = row * dz
                if sx * sx + sz * sz > pr * pr * (0.8 + 0.4 * rng.random()):
                    continue
                a, z = ac + sx / rc, zc + sz
                v = v_of(z)
                c, n = surf(a, v), surf_n(a, v)
                up = surf(a, min(v + 0.01, 1)) - c
                roll = rng.random()
                fz = -0.018 if roll < 0.75 else 0.02
                # lathe normals: a profile going up faces outward, going down faces the axis
                V, F = M.lathe([(ro, -0.04), (ro, 0.035), (ri * 0.9, fz)], 6, a0=30, cap=False)
                w = P(V, F, "BH_Cloth_Secondary", "cell_wall")
                mat = "BH_Ichor" if roll < 0.5 else ("BH_Shadow" if roll < 0.75 else "BH_Cloth_Secondary")
                V, F = M.lathe([(ri * 0.9, fz), (0, fz + (0.012 if fz > 0 else 0.0))], 6, a0=30, cap=False)
                fl = P(V, F, mat, "cell_floor")
                for p in (w, fl):
                    parts.append(place(p, n, c + n * 0.03, up_hint=up))
    return parts


ENTRANCES = [(0.1, 0.55, 0.19), (1.35, 1.05, 0.15), (-1.45, 0.8, 0.16), (2.75, 0.6, 0.16), (-0.6, 1.62, 0.12),
             (3.9, 1.55, 0.12)]


def entrance_parts():
    parts = []
    for (a, z, R) in ENTRANCES:
        v = v_of(z)
        c, n = surf(a, v), surf_n(a, v)
        n = K.normalize(n + (0, 0, 0.25))                  # holes look slightly upward (the camera is high)
        V, F = M.lathe([(R + 0.07, -0.16), (R + 0.075, 0.03), (R + 0.045, 0.1), (R + 0.005, 0.11)], 14, cap=False)
        parts.append(place(P(V, F, "BH_Cloth_Secondary", "collar"), n, c))
        # the mound surface closes the hole, so the throat / glow / dark centre sit inside the raised collar
        V, F = M.lathe([(R + 0.005, 0.11), (R * 0.93, 0.08), (R * 0.88, 0.035)], 14, cap=False)
        parts.append(place(P(V, F, "BH_Shadow", "throat"), n, c))
        V, F = M.lathe([(R * 0.88, 0.035), (R * 0.5, 0.03)], 14, cap=False)
        parts.append(place(P(V, F, "BH_Emissive", "glow"), n, c))
        V, F = M.lathe([(R * 0.5, 0.03), (0, 0.028)], 14, cap=False)
        parts.append(place(P(V, F, "BH_Shadow", "hole"), n, c))
    return parts


def rib_parts():
    parts = []
    rng = np.random.default_rng(3)
    for k in range(9):
        a0 = 2 * math.pi * k / 9 + 0.3 * rng.random()
        z0 = 1.25 + 0.9 * rng.random()
        z1 = max(0.3, z0 - 0.7 - 0.6 * rng.random())
        pts, prof = [], []
        for i, z in enumerate(np.linspace(z0, z1, 9)):
            a = a0 + 0.05 * math.sin(z * 7 + k)
            v = v_of(z)
            pts.append(surf(a, v) + surf_n(a, v) * 0.03)
            r = 0.045 - 0.015 * i / 8
            prof.append((r, r * 0.8))
        V, F = M.tube(pts, prof, n=6, up=list(surf_n(a0, v_of(z)) for z in np.linspace(z0, z1, 9)))
        parts.append(P(V, F, "BH_Ichor", "rib"))
        end = pts[-1] + (0, 0, -0.03)
        parts.append(blob(tuple(end), (0.05, 0.05, 0.065), "BH_Ichor", 8, 5, "drop"))
    return parts


def drone_parts():
    parts = []
    body, _, _ = D.drone(lod=0.45, eye_mat="BH_Ichor", folded=True)
    for (a, z, head_up, s) in ((0.95, 0.72, True, 0.62), (-2.35, 1.3, False, 0.58)):
        v = v_of(z)
        c, n = surf(a, v), surf_n(a, v)
        t = K.normalize(surf(a, min(v + 0.02, 1)) - c) * (1 if head_up else -1)
        t = K.normalize(t + np.cross(n, t) * 0.4)          # a little askew
        R = np.stack([np.cross(-t, n), -t, n], 1)
        for p in body:
            q = p.copy()
            q.V = (q.V * s) @ R.T + c + n * 0.13 * s
            parts.append(q)
    return parts


def base_parts():
    parts = []
    rng = np.random.default_rng(11)
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.4 * rng.random()
        L = 1.35 + 0.35 * rng.random()
        pts = []
        for i, t in enumerate(np.linspace(0, 1, 7)):
            r = 0.75 + (L - 0.75) * t
            aa = a + 0.12 * math.sin(t * 5 + k)
            pts.append((r * math.sin(aa), -r * math.cos(aa), 0.12 * (1 - t) + 0.035 + 0.02 * math.sin(t * 9 + k)))
        V, F = M.tube(pts, [(0.07 - 0.055 * t, 0.055 - 0.043 * t) for t in np.linspace(0, 1, 7)], n=5, up=(0, 0, 1))
        parts.append(P(V, F, "BH_Wood", "root"))
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8 + 0.3 * rng.random()
        r = 1.05 + 0.3 * rng.random()
        s = 0.09 + 0.08 * rng.random()
        st = blob((r * math.sin(a), -r * math.cos(a), s * 0.35), (s * 1.2, s, s * 0.7), "BH_Stone", 7, 4, "stone")
        st.V += (rng.random(st.V.shape) - 0.5) * s * 0.35
        parts.append(st)
    return parts


def build():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K.MT.make_materials(CID, vertex_color=False, extra=PALETTE_COLORS)
    core = mound_parts() + comb_parts() + entrance_parts() + rib_parts() + drone_parts()
    obs = [K.node("core", core, mats, sharp=40, ao=(10, 0.25, 0.45))]
    obs.append(K.node("base", base_parts(), mats, sharp=40, ao=(8, 0.15, 0.3)))
    return obs


if __name__ == "__main__":
    K.run(CID, build, dict(ground_z=0.0, look=(0, 0, 1.0), dist=6.0, close=((0, -0.6, 0.8), 2.4, 20, 18),
                           game_look=(0, 0, 0.9)))
