"""Aether Wisp (Builder C): static multi-node model, animated by the game.

  python3 build_wisp.py [--out game/assets/characters/aether_wisp.glb] [--preview DIR]

Nodes (all meshes, no armature, origin = creature centre, Blender Z-up -> glTF Y-up):
  core      faceted pale-cyan Aether crystal cluster, radius ~0.25 m (BH_Aether__aether_wisp)
  ring_1..3 shard rings (6/7/5 crystal shards) of radius 0.45 / 0.58 / 0.70 m. The shards lie in the node's local
            XY plane (Blender) = XZ plane (Godot); each node carries its own tilt as its transform, so spinning a
            ring node about its LOCAL up axis (Godot +Y) spins the ring in its own plane.
  ribbons   three thin trailing light-ribbon strips hanging below the core (BH_Emissive__aether_wisp)
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

PALETTE_COLORS = {
    "BH_Aether": ((0.55, 0.95, 1.0), 0.0, 0.2, (0.45, 0.92, 1.0), 9.0, 1.0),
    "BH_Stone": ((0.22, 0.36, 0.46), 0.0, 0.3, (0.15, 0.45, 0.6), 0.4, 1.0),     # crystal shards (faint glow)
    "BH_Emissive": ((0.5, 0.9, 1.0), 0.0, 0.4, (0.4, 0.85, 1.0), 6.0, 1.0),     # light ribbons
}


def crystal(length, radius, sides=6, skew=0.0):
    V, F = M.lathe([(0, -length * 0.45), (radius * 0.85, -length * 0.2), (radius, 0.0), (radius * 0.8, length * 0.25),
                    (0, length * 0.55)], sides)
    p = M.Part(V, F, "BH_Aether", name="crystal")
    p.V[:, 0] += skew * p.V[:, 2]
    return p


def core_parts():
    parts = []
    rng = np.random.default_rng(11)
    main = crystal(0.56, 0.16, sides=6)
    parts.append(main)
    for i in range(7):
        a = 2 * math.pi * i / 7 + rng.random() * 0.4
        el = (rng.random() - 0.5) * 70
        c = crystal(0.26 + 0.1 * rng.random(), 0.07 + 0.02 * rng.random(), sides=5)
        c.rot(Ry(55 + 15 * rng.random()) @ Rz(0)).rot(Rz(math.degrees(a))).rot(Rx(el * 0.3))
        d = np.array([math.cos(a), math.sin(a), el / 140.0])
        c.move(normalize(d) * 0.07)
        parts.append(c)
    V, F = M.sphere(0.1, 10, 6)
    parts.append(M.Part(V, F, "BH_Aether", name="heart"))
    return parts


def ring_parts(radius, n, size, seed):
    rng = np.random.default_rng(seed)
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n + (rng.random() - 0.5) * 0.3
        L = size * (0.8 + 0.4 * rng.random())
        c = crystal(L, L * 0.14, sides=4)
        c.mat = "BH_Stone"
        # shard points along the orbit (tangent), tipped slightly outward
        c.rot(Rx(-90)).rot(Rz(20 * (rng.random() - 0.5))).rot(Rx(15 * (rng.random() - 0.5)))
        c.rot(Rz(math.degrees(a)))
        c.move((radius * math.cos(a), radius * math.sin(a), 0.03 * (rng.random() - 0.5)))
        parts.append(c)
    return parts


def ribbon_parts():
    parts = []
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        x0, y0 = 0.08 * math.cos(a), 0.08 * math.sin(a)

        def fn(u, v, a=a, x0=x0, y0=y0, k=k):
            w = 0.07 * (1 - 0.75 * v)
            tx, ty = -math.sin(a), math.cos(a)
            sway = 0.08 * math.sin(v * 5.0 + k * 2.0) * v
            x = x0 * (1 + 1.5 * v) + (u - 0.5) * w * tx + sway * math.cos(a)
            y = y0 * (1 + 1.5 * v) + (u - 0.5) * w * ty + sway * math.sin(a)
            z = -0.12 - (0.52 + 0.08 * k) * v
            return (x, y, z)
        V, F = M.grid(fn, 3, 12)
        p = M.Part(V, F, "BH_Emissive", name="ribbon")
        p = M.solidify(p, 0.008, offset=0.0)
        parts.append(p)
    return parts


RINGS = [  # name, radius, shard count, shard length, tilt (deg about X, about Y)
    ("ring_1", 0.45, 6, 0.2, (18, 0)),
    ("ring_2", 0.58, 7, 0.22, (-10, 30)),
    ("ring_3", 0.70, 5, 0.26, (34, -24)),
]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = MT.make_materials("aether_wisp", vertex_color=False, extra=PALETTE_COLORS)
    obs = []
    ob = M.build_static("core", core_parts(), mats, sharp_angle=30)
    obs.append(ob)
    for i, (name, r, n, size, (tx, ty)) in enumerate(RINGS):
        ob = M.build_static(name, ring_parts(r, n, size, seed=20 + i), mats, sharp_angle=30)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (math.radians(tx), math.radians(ty), 0.0)
        obs.append(ob)
    obs.append(M.build_static("ribbons", ribbon_parts(), mats, sharp_angle=60))
    for ob in obs:
        MT.bake_vertex_ao(ob, rays=12, dist=0.15, strength=0.4)
    return obs


def preview(obs, out_dir):
    import preview_enemy as PE
    PE.material_colors()
    cam = PE.setup(360)
    bpy.data.objects["Ground"].location.z = -0.9
    tiles = []
    for v, pitch, dist, lens in ((0, 8, 3.4, 50), (60, 30, 3.4, 50), (150, -10, 3.4, 50), (20, 55, 26.0, 50)):
        PE.place(cam, (0, 0, 0), dist, v, pitch, lens)
        p = os.path.join(out_dir, f"_wisp_{v}_{pitch}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append(p)
    from PIL import Image
    sheet = Image.new("RGB", (360 * len(tiles), 360))
    for i, p in enumerate(tiles):
        sheet.paste(Image.open(p).convert("RGB"), (360 * i, 0))
    path = os.path.join(out_dir, "aether_wisp_rest.png")
    sheet.save(path)
    print("PREVIEW", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "game", "assets", "characters", "aether_wisp.glb"))
    ap.add_argument("--preview", default="")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    obs = build()
    for ob in obs:
        print(f"[aether_wisp] {ob.name}: {M.tri_count(ob)} tris")
    print(f"[aether_wisp] total {sum(M.tri_count(o) for o in obs)} tris")
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        preview(obs, a.preview)
    import build as BLD
    BLD.export_glb(a.out, obs, animations=False)
    print("[aether_wisp] ->", a.out)


if __name__ == "__main__":
    main()
