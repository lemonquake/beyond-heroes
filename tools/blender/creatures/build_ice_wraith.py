"""Ice Wraith (bh-012, Builder D, Rimeglass Barrow caster): static multi-node floating model, animated by the game
(same convention as build_wisp.py).

  blender -b --factory-startup --python build_ice_wraith.py -- [--out game/assets/characters/ice_wraith.glb]
                                                               [--preview DIR]   (tiles + manifest.json for ev_compose)

Nodes (all meshes, no armature, origin = creature centre, Blender Z-up -> glTF Y-up), ~1.8 m tall overall
(hood crest +0.62 m, ribbon tips -1.18 m):
  core      hooded veil of frost (open at the front, -Y) around a skull-like ice mask with two blue eye-lights and an
            icicle jaw, a ragged frost mantle below the hood, frost crystals on the crown (BH_Cloth_Primary / BH_Stone /
            BH_Emissive / BH_Shadow __ice_wraith)
  ring_1..3 circles of floating icicle shards (9 / 11 / 7 shards, radius 0.5 / 0.64 / 0.8 m, each ring its own
            size and tilt). Shards lie in the node's local XY plane (Blender) = XZ (Godot); spinning a ring node about
            its LOCAL up axis (Godot +Y) spins it in its own plane.
  ribbons   six long tattered frost-cloth tails trailing below the mantle (BH_Cloth_Primary / BH_Cloth_Secondary)
"""
import argparse
import json
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

CID = "ice_wraith"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.74, 0.84, 0.92), 0.0, 0.55, (0.12, 0.24, 0.34), 0.3, 1.0),   # frost veil (pale)
    "BH_Cloth_Secondary": ((0.3, 0.44, 0.6), 0.0, 0.6, (0.08, 0.18, 0.3), 0.3, 1.0),      # deeper blue inner tails
    "BH_Stone": ((0.7, 0.9, 1.0), 0.0, 0.08, (0.2, 0.45, 0.6), 0.6, 1.0),                 # ice shards / mask
    "BH_Shadow": ((0.01, 0.02, 0.04), 0.0, 0.8, None, 0.0, 1.0),                          # hood interior, sockets
    "BH_Emissive": ((0.55, 0.88, 1.0), 0.0, 0.3, (0.45, 0.8, 1.0), 9.0, 1.0),             # eye-lights, core glow
}


def P(V, F, mat, name="part"):
    return M.Part(V, F, mat, name=name)


def crystal(length, radius, sides=5, mat="BH_Stone"):
    """Icicle shard along +Z centred near its thick point: long sharp tip up, short blunt tail down."""
    V, F = M.lathe([(0, -length * 0.25), (radius * 0.8, -length * 0.12), (radius, 0.0), (radius * 0.7, length * 0.3),
                    (0, length * 0.75)], sides)
    return P(V, F, mat, "shard")


def orient(p, center, inward=False):
    F = []
    c0 = np.asarray(center, float)
    for f in p.F:
        a, b, c = p.V[f[0]], p.V[f[1]], p.V[f[2]]
        n = np.cross(b - a, c - a)
        out = np.dot(n, p.V[list(f)].mean(0) - c0) >= 0
        F.append(f if out != inward else tuple(reversed(f)))
    p.F = F
    return p


def rag(u, seed, amp, teeth=5):
    v = 0.5 + 0.5 * math.sin(u * math.pi * 2 * teeth + seed) * math.cos(u * math.pi * 3.3 + 1.7 * seed)
    tooth = abs(((u * teeth * 2.0 + seed * 0.37) % 2.0) - 1.0)
    return amp * (0.55 * v + 0.45 * tooth)


# ------------------------------------------------------------------------------------------------ core
def core_parts():
    parts = []
    # hood: open at the front, peaked crown, falls to the shoulders; outer frost veil + dark lining
    RP = [(0.0, 0.02), (0.12, 0.11), (0.3, 0.19), (0.55, 0.205), (0.78, 0.18), (1.0, 0.23)]

    def hood(u, v, inner=False):
        op = 12 + 40 * math.sin(math.pi * min(max((v - 0.08) / 0.8, 0.0), 1.0)) ** 0.7   # pointed-arch opening
        a = math.radians(op + (360 - 2 * op) * u)       # 0 = front (-Y)
        z = 0.58 - 0.74 * v
        r = float(np.interp(v, [q[0] for q in RP], [q[1] for q in RP]))
        r *= 1.0 + 0.04 * math.sin(a * 5 + v * 7) * v
        if inner:
            r *= 0.88
        x = r * math.sin(a)
        y = -r * math.cos(a) + 0.05 * (1 - v) ** 2
        return (x, y, z)
    V, F = M.grid(hood, 18, 12)
    parts.append(M.solidify(orient(P(V, F, "BH_Cloth_Primary", "hood"), (0, 0.02, 0.2)), 0.012, offset=1.0))
    V, F = M.grid(lambda u, v: hood(u, v, True), 18, 9)
    parts.append(orient(P(V, F, "BH_Shadow", "lining"), (0, 0.02, 0.2), inward=True))
    # mantle below the hood: flares out, ragged hem
    def mantle(u, v):
        a = 2 * math.pi * u
        r = 0.22 + 0.2 * v ** 0.8
        z = -0.12 - (0.26 + rag(u, 1.3, 0.22, 7)) * v
        return (r * math.sin(a), -r * math.cos(a), z)
    V, F = M.grid(mantle, 24, 6)
    parts.append(M.solidify(orient(P(V, F, "BH_Cloth_Primary", "mantle"), (0, 0, 0.0)), 0.01, offset=1.0))
    # skull-like ice mask in the hood opening
    V, F = M.sphere(0.12, 12, 8, center=(0, -0.1, 0.2), scale=(0.85, 0.8, 1.05))
    mask = P(V, F, "BH_Stone", "mask")
    for sx in (1, -1):                                # hollow cheeks
        c = np.array([sx * 0.06, -0.17, 0.14])
        d2 = np.sum((mask.V - c) ** 2, 1)
        mask.V += np.array([-sx * 0.3, 1.0, 0.0])[None] * (0.018 * np.exp(-d2 / 0.03 ** 2))[:, None]
    parts.append(mask)
    for sx in (1, -1):
        V, F = M.sphere(0.03, 8, 5, center=(sx * 0.04, -0.188, 0.23), scale=(1.2, 0.6, 0.9))
        parts.append(P(V, F, "BH_Shadow", "socket"))
        V, F = M.sphere(0.017, 8, 5, center=(sx * 0.04, -0.2, 0.228), scale=(1.3, 0.7, 0.9))
        parts.append(P(V, F, "BH_Emissive", "eye"))
    V, F = M.prism([(-0.014, 0.0), (0.014, 0.0), (0.0, 0.03)], 0.02, axis="y")
    parts.append(P(V, F, "BH_Shadow", "nose").move((0, -0.195, 0.165)))
    # icicle jaw / fangs
    for k, x in enumerate(np.linspace(-0.055, 0.055, 6)):
        ln = 0.08 + 0.05 * (1 - abs(x) / 0.055) + 0.02 * (k % 2)
        V, F = M.lathe([(0, 0.0), (0.011, -0.01), (0.0, -ln)], 4)
        parts.append(P(V, F, "BH_Stone", "fang").move((x, -0.16 + 0.25 * x * x, 0.12)))
    # glowing core behind the mask (shows through the veil opening at the throat)
    V, F = M.sphere(0.05, 8, 5, center=(0, -0.07, 0.02))
    parts.append(P(V, F, "BH_Emissive", "heart"))
    # frost crystals on the hood crown + shoulders
    rng = np.random.default_rng(4)
    for (c, d, ln) in (((0.0, 0.08, 0.58), (0, 0.3, 1), 0.22), ((0.08, 0.06, 0.5), (0.6, 0.2, 1), 0.16),
                       ((-0.08, 0.06, 0.5), (-0.6, 0.2, 1), 0.16), ((0.24, 0.0, -0.1), (1, 0, 0.8), 0.14),
                       ((-0.24, 0.0, -0.1), (-1, 0, 0.8), 0.14), ((0.0, 0.26, -0.05), (0, 1, 0.6), 0.13)):
        p = crystal(ln, ln * 0.16, sides=4)
        p.V[:, 2] += ln * 0.25
        d = normalize(d)
        from bh_body import M_align_z
        p.V = p.V @ M_align_z(d).T + np.asarray(c, float)
        parts.append(p)
    return parts


# ------------------------------------------------------------------------------------------------ rings / ribbons
def ring_parts(radius, n, size, seed, glow_every=3):
    rng = np.random.default_rng(seed)
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n + (rng.random() - 0.5) * 0.25
        L = size * (0.75 + 0.5 * rng.random())
        c = crystal(L, L * 0.12, sides=4, mat="BH_Emissive" if i % glow_every == 0 else "BH_Stone")
        # icicle along the orbit tangent, tip leading, tipped a little outward / off-plane
        c.rot(Rx(-90)).rot(Rz(18 * (rng.random() - 0.5))).rot(Rx(20 * (rng.random() - 0.5)))
        c.rot(Rz(math.degrees(a)))
        c.move((radius * math.cos(a), radius * math.sin(a), 0.04 * (rng.random() - 0.5)))
        parts.append(c)
    return parts


def ribbon_parts():
    parts = []
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        x0, y0 = 0.2 * math.cos(a), 0.2 * math.sin(a)
        ln = 0.62 + 0.14 * ((k * 7) % 3) / 2

        def fn(u, v, a=a, x0=x0, y0=y0, k=k, ln=ln):
            w = 0.17 * (1 - 0.5 * v)
            tx, ty = -math.sin(a), math.cos(a)
            sway = 0.1 * math.sin(v * 4.5 + k * 1.7) * v
            x = x0 * (1 + 0.5 * v) + (u - 0.5) * w * tx + sway * math.cos(a)
            y = y0 * (1 + 0.5 * v) + 0.25 * v * v + (u - 0.5) * w * ty + sway * math.sin(a)
            z = -0.25 - ln * v - (rag(u, k + 0.5, 0.08, 2) if v > 0.99 else 0.0)
            return (x, y, z)
        V, F = M.grid(fn, 4, 12)
        p = P(V, F, "BH_Cloth_Primary" if k % 2 == 0 else "BH_Cloth_Secondary", "ribbon")
        parts.append(M.solidify(p, 0.008, offset=0.0))
        tip = np.array(fn(0.5, 1.0))
        V, F = M.lathe([(0, 0.0), (0.012, -0.01), (0.0, -0.1)], 4)
        parts.append(P(V, F, "BH_Stone", "icicle").move(tip + (0, 0, 0.01)))
    return parts


RINGS = [  # name, radius, shard count, shard length, tilt (deg about X, about Y)
    ("ring_1", 0.5, 9, 0.2, (14, 0)),
    ("ring_2", 0.64, 11, 0.26, (-12, 28)),
    ("ring_3", 0.8, 7, 0.34, (32, -20)),
]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = MT.make_materials(CID, vertex_color=False, extra=PALETTE_COLORS)
    obs = [M.build_static("core", core_parts(), mats, sharp_angle=35)]
    for i, (name, r, n, size, (tx, ty)) in enumerate(RINGS):
        ob = M.build_static(name, ring_parts(r, n, size, seed=40 + i), mats, sharp_angle=30)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (math.radians(tx), math.radians(ty), 0.0)
        obs.append(ob)
    obs.append(M.build_static("ribbons", ribbon_parts(), mats, sharp_angle=60))
    for ob in obs:
        MT.bake_vertex_ao(ob, rays=12, dist=0.15, strength=0.4)
    return obs


def preview(obs, out_dir):
    """Workbench tiles + a manifest for evidence/models_rime/tools/ev_compose.py (Blender has no PIL)."""
    import preview_enemy as PE
    PE.material_colors()
    cam = PE.setup(400)
    bpy.data.objects["Ground"].location.z = -1.2
    tiles = os.path.join(out_dir, "_tiles_" + CID)
    os.makedirs(tiles, exist_ok=True)
    row1, row2 = [], []
    for v, pitch, dist in ((0, 6, 4.4), (60, 20, 4.4), (150, 8, 4.4), (270, 6, 4.4)):
        PE.place(cam, (0, 0, -0.25), dist, v, pitch)
        p = os.path.join(tiles, f"v{v}_{pitch}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        row1.append(dict(path=p, label=f"yaw {v} pitch {pitch}"))
    PE.place(cam, (0, 0, 0.1), 1.6, 20, 8)
    p = os.path.join(tiles, "face.png")
    bpy.context.scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    row2.append(dict(path=p, label="mask close-up"))
    for dist in (16, 22):       # gameplay camera (54 deg, 40 deg vFOV), hovering 1.2 m above the ground
        from mathutils import Vector
        c = Vector((0, 0, 0))
        pit = math.radians(54)
        cam.location = c + Vector((0, -math.cos(pit), math.sin(pit))) * dist
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.sensor_fit = "VERTICAL"
        cam.data.angle_y = math.radians(40)
        p = os.path.join(tiles, f"game_{dist}.png")
        bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1920, 1080
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        row2.append(dict(path=p, label=f"game cam 54deg {dist} m (1080p crop 1:1)", crop=[780, 360, 1140, 720]))
    man = os.path.join(out_dir, f"{CID}_rest.json")
    with open(man, "w") as f:
        json.dump(dict(character=CID, res=400, rows=[row1, row2]), f, indent=1)
    print("MANIFEST", man)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "game", "assets", "characters", CID + ".glb"))
    ap.add_argument("--preview", default="")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    obs = build()
    for ob in obs:
        print(f"[{CID}] {ob.name}: {M.tri_count(ob)} tris")
    print(f"[{CID}] total {sum(M.tri_count(o) for o in obs)} tris")
    import build as BLD
    BLD.export_glb(a.out, obs, animations=False)
    print(f"[{CID}] ->", a.out)
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        preview(obs, a.preview)


if __name__ == "__main__":
    main()
