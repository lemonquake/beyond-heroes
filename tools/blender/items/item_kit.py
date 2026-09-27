"""Shared kit for the item models (bh-006): palette materials and small shape helpers.

Materials are exported as "<BH base>__it_<key>" so Godot's MaterialLibrary._palette_mat keeps each item's own colours
(and adds the shared detail normal maps for known bases such as BH_Steel / BH_Wood / BH_Leather).
Parts name their material by palette key ("steel", "gold", "ruby" ...), see MAT.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.abspath(os.path.join(HERE, "..", "characters"))
if CHARS not in sys.path:
    sys.path.insert(0, CHARS)

import bh_mesh as M  # noqa: E402
from bh_math import Rx, Ry, Rz  # noqa: E402,F401

# key: (godot base, rgb, metallic, roughness, emission rgb or None, emission strength)
MAT = {
    # metals
    "steel": ("BH_Steel", (0.58, 0.59, 0.62), 1.0, 0.32, None, 0),
    "bright": ("BH_Steel", (0.78, 0.8, 0.84), 1.0, 0.22, None, 0),
    "darksteel": ("BH_DarkSteel", (0.17, 0.17, 0.19), 1.0, 0.45, None, 0),
    "blued": ("BH_Steel", (0.26, 0.32, 0.45), 1.0, 0.3, None, 0),
    "iron": ("BH_Steel", (0.4, 0.39, 0.38), 1.0, 0.55, None, 0),
    "rust": ("BH_Rust", (0.32, 0.17, 0.08), 0.45, 0.82, None, 0),
    "gold": ("BH_Gold", (0.8, 0.57, 0.22), 1.0, 0.28, None, 0),
    "paleg": ("BH_Gold", (0.86, 0.74, 0.45), 1.0, 0.3, None, 0),
    "bronze": ("BH_Bronze", (0.5, 0.31, 0.14), 1.0, 0.38, None, 0),
    "copper": ("BH_Bronze", (0.72, 0.36, 0.2), 1.0, 0.35, None, 0),
    "silver": ("BH_Steel", (0.82, 0.83, 0.86), 1.0, 0.2, None, 0),
    "brass": ("BH_Gold", (0.7, 0.55, 0.28), 1.0, 0.35, None, 0),
    "blackiron": ("BH_DarkSteel", (0.09, 0.085, 0.09), 1.0, 0.5, None, 0),
    "sunsteel": ("BH_Steel", (0.85, 0.66, 0.42), 1.0, 0.25, None, 0),
    "moonsteel": ("BH_Steel", (0.72, 0.8, 0.92), 1.0, 0.18, None, 0),
    # organics
    "wood": ("BH_Wood", (0.2, 0.12, 0.065), 0.0, 0.7, None, 0),
    "darkwood": ("BH_Wood", (0.09, 0.055, 0.035), 0.0, 0.65, None, 0),
    "ash": ("BH_Wood", (0.42, 0.33, 0.22), 0.0, 0.72, None, 0),
    "redwood": ("BH_Wood", (0.3, 0.1, 0.06), 0.0, 0.6, None, 0),
    "reed": ("BH_Wood", (0.55, 0.47, 0.28), 0.0, 0.75, None, 0),
    "leather": ("BH_Leather", (0.16, 0.085, 0.045), 0.0, 0.62, None, 0),
    "darkleather": ("BH_Leather", (0.06, 0.04, 0.03), 0.0, 0.6, None, 0),
    "redleather": ("BH_Leather", (0.3, 0.06, 0.05), 0.0, 0.6, None, 0),
    "tan": ("BH_Leather", (0.42, 0.28, 0.16), 0.0, 0.7, None, 0),
    "bone": ("BH_Bone", (0.72, 0.66, 0.52), 0.0, 0.6, None, 0),
    "horn": ("BH_Horn", (0.32, 0.25, 0.17), 0.0, 0.45, None, 0),
    "fur": ("BH_Fur", (0.3, 0.22, 0.15), 0.0, 0.9, None, 0),
    "hide": ("BH_Fur", (0.38, 0.26, 0.16), 0.0, 0.85, None, 0),
    "rope": ("BH_Cloth_Secondary", (0.45, 0.38, 0.25), 0.0, 0.9, None, 0),
    "paper": ("BH_Cloth_Secondary", (0.82, 0.74, 0.56), 0.0, 0.85, None, 0),
    "wax_red": ("BH_Cloth_Secondary", (0.62, 0.06, 0.05), 0.0, 0.4, None, 0),
    "stone": ("BH_Stone", (0.4, 0.39, 0.37), 0.0, 0.85, None, 0),
    "slate": ("BH_Stone", (0.2, 0.21, 0.23), 0.0, 0.8, None, 0),
    "clay": ("BH_Stone", (0.5, 0.28, 0.16), 0.0, 0.9, None, 0),
    "ashstone": ("BH_Stone", (0.18, 0.16, 0.15), 0.0, 0.9, None, 0),
    # cloth
    "linen": ("BH_Cloth_Secondary", (0.72, 0.66, 0.54), 0.0, 0.9, None, 0),
    "wool": ("BH_Cloth_Secondary", (0.35, 0.3, 0.24), 0.0, 0.95, None, 0),
    "crimson": ("BH_Cloth_Secondary", (0.45, 0.04, 0.05), 0.0, 0.85, None, 0),
    "navy": ("BH_Cloth_Secondary", (0.06, 0.07, 0.2), 0.0, 0.85, None, 0),
    "violet": ("BH_Cloth_Secondary", (0.2, 0.08, 0.32), 0.0, 0.85, None, 0),
    "forest": ("BH_Cloth_Secondary", (0.1, 0.2, 0.1), 0.0, 0.88, None, 0),
    "ochre": ("BH_Cloth_Secondary", (0.55, 0.36, 0.1), 0.0, 0.88, None, 0),
    "silk": ("BH_Cloth_Secondary", (0.78, 0.76, 0.84), 0.0, 0.45, None, 0),
    "black": ("BH_Cloth_Secondary", (0.035, 0.03, 0.04), 0.0, 0.8, None, 0),
    "white": ("BH_Cloth_Secondary", (0.85, 0.83, 0.78), 0.0, 0.85, None, 0),
    "teal": ("BH_Cloth_Secondary", (0.05, 0.25, 0.28), 0.0, 0.85, None, 0),
    # glass, liquids, gems, energy
    "glass": ("BH_Glass", (0.62, 0.7, 0.72), 0.0, 0.08, None, 0),
    "red_liquid": ("BH_Liquid", (0.75, 0.04, 0.05), 0.0, 0.15, (0.9, 0.05, 0.06), 0.35),
    "blue_liquid": ("BH_Liquid", (0.06, 0.2, 0.85), 0.0, 0.15, (0.1, 0.3, 1.0), 0.4),
    "purple_liquid": ("BH_Liquid", (0.45, 0.12, 0.7), 0.0, 0.15, (0.6, 0.2, 1.0), 0.4),
    "green_liquid": ("BH_Liquid", (0.2, 0.7, 0.25), 0.0, 0.15, (0.25, 0.9, 0.3), 0.35),
    "amber_liquid": ("BH_Liquid", (0.85, 0.45, 0.08), 0.0, 0.15, (1.0, 0.5, 0.1), 0.4),
    "gold_liquid": ("BH_Liquid", (0.95, 0.75, 0.2), 0.0, 0.12, (1.0, 0.8, 0.25), 0.45),
    "orange_liquid": ("BH_Liquid", (0.95, 0.35, 0.05), 0.0, 0.15, (1.0, 0.4, 0.08), 0.5),
    "ice_liquid": ("BH_Liquid", (0.55, 0.85, 1.0), 0.0, 0.1, (0.5, 0.85, 1.0), 0.45),
    "yellow_liquid": ("BH_Liquid", (0.95, 0.9, 0.2), 0.0, 0.12, (1.0, 0.95, 0.3), 0.5),
    "silver_liquid": ("BH_Liquid", (0.8, 0.85, 0.9), 0.3, 0.1, (0.7, 0.8, 1.0), 0.25),
    "brown_liquid": ("BH_Liquid", (0.35, 0.18, 0.06), 0.0, 0.2, None, 0),
    "ruby": ("BH_Gem", (0.8, 0.03, 0.08), 0.0, 0.08, (0.9, 0.05, 0.1), 0.7),
    "sapphire": ("BH_Gem", (0.05, 0.2, 0.9), 0.0, 0.08, (0.1, 0.3, 1.0), 0.7),
    "emerald": ("BH_Gem", (0.05, 0.7, 0.25), 0.0, 0.08, (0.1, 0.9, 0.35), 0.7),
    "amethyst": ("BH_Gem", (0.5, 0.15, 0.85), 0.0, 0.08, (0.6, 0.25, 1.0), 0.7),
    "topaz": ("BH_Gem", (0.95, 0.65, 0.1), 0.0, 0.08, (1.0, 0.7, 0.15), 0.7),
    "onyx": ("BH_Gem", (0.03, 0.03, 0.04), 0.0, 0.1, (0.25, 0.1, 0.45), 0.5),
    "pearl": ("BH_Gem", (0.9, 0.88, 0.85), 0.0, 0.2, None, 0),
    "aether": ("BH_Aether", (0.2, 0.78, 0.95), 0.0, 0.2, (0.3, 0.85, 1.0), 1.1),
    "ember": ("BH_Emissive", (1.0, 0.4, 0.08), 0.0, 0.4, (1.0, 0.42, 0.08), 1.6),
    "ice": ("BH_Gem", (0.42, 0.72, 0.95), 0.0, 0.1, (0.35, 0.7, 1.0), 0.35),
    "storm": ("BH_Emissive", (0.85, 0.7, 0.12), 0.0, 0.3, (1.0, 0.85, 0.25), 0.9),
    "holy": ("BH_Emissive", (1.0, 0.85, 0.5), 0.0, 0.3, (1.0, 0.85, 0.5), 1.5),
    "shadow": ("BH_Emissive", (0.2, 0.05, 0.3), 0.0, 0.3, (0.55, 0.2, 0.95), 1.6),
    "tide": ("BH_Emissive", (0.1, 0.5, 0.8), 0.0, 0.3, (0.2, 0.7, 1.0), 1.5),
    "venom": ("BH_Emissive", (0.3, 0.8, 0.15), 0.0, 0.3, (0.4, 1.0, 0.2), 1.4),
    "wind": ("BH_Emissive", (0.6, 1.0, 0.8), 0.0, 0.3, (0.6, 1.0, 0.85), 1.3),
    "earth": ("BH_Emissive", (0.8, 0.5, 0.2), 0.0, 0.4, (0.9, 0.55, 0.2), 1.3),
    "portal": ("BH_Emissive", (0.55, 0.25, 1.0), 0.0, 0.3, (0.65, 0.35, 1.0), 1.9),
    "flame": ("BH_Emissive", (0.78, 0.12, 0.02), 0.0, 0.5, (1.0, 0.22, 0.02), 0.4),
    "flame_tip": ("BH_Emissive", (0.95, 0.45, 0.05), 0.0, 0.5, (1.0, 0.5, 0.06), 0.6),
    "smoke": ("BH_Stone", (0.3, 0.3, 0.32), 0.0, 0.95, None, 0),
}

# element index (Godot Elements enum) -> glow palette key
ELEMENT_GLOW = {0: None, 1: "ember", 2: "ice", 3: "storm", 4: "earth", 5: "wind", 6: "tide", 7: "holy", 8: "shadow"}


def make_materials(keys):
    """Create (or reuse) Blender materials for the palette keys used by a model. Returns {key: material}."""
    import bpy
    out = {}
    for key in keys:
        base, rgb, met, rough, erg, estr = MAT[key]
        name = f"{base}__it_{key}"
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
            m.use_nodes = True
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = (*rgb, 1.0)
            b.inputs["Metallic"].default_value = met
            b.inputs["Roughness"].default_value = rough
            if erg:
                b.inputs["Emission Color"].default_value = (*erg, 1.0)
                b.inputs["Emission Strength"].default_value = estr
            if base == "BH_Glass":
                try:
                    b.inputs["Coat Weight"].default_value = 0.6
                except KeyError:
                    pass
            m.diffuse_color = (*rgb, 1.0)
            m.metallic = met
            m.roughness = rough
        out[key] = m
    return out


# ------------------------------------------------------------------------------------------------------------------
# shape helpers (all return M.Part lists or a Part)

def P(VF, mat, name="part"):
    return M.Part(VF[0], VF[1], mat, name=name)


def lathe(profile, mat, n=16, name="lathe"):
    return P(M.lathe(profile, n), mat, name)


def band(z, r, h, mat, n=14, bulge=1.06):
    return lathe([(0, z - h / 2), (r, z - h / 2), (r * bulge, z), (r, z + h / 2), (0, z + h / 2)], mat, n, "band")


def sphere(r, center, mat, n=12, rings=8, scale=(1, 1, 1)):
    return P(M.sphere(r, n, rings, center=center, scale=scale), mat, "sphere")


def box(sx, sy, sz, center, mat, bevel=0.0):
    p = P(M.box(sx, sy, sz, center=center), mat, "box")
    return M.bevel(p, bevel, 1) if bevel > 0 else p


def tube(points, radii, mat, n=8, up=(0, -1, 0), p=2.0, cap=True, name="tube"):
    prof = [(r, r) if not isinstance(r, (tuple, list)) else r for r in radii]
    V, F = M.tube(points, prof, n=n, up=up, p=p, cap0=cap, cap1=cap)
    return M.Part(V, F, mat, name=name)


def slab(outline, depth, mat, axis="y", center=0.0, n=None, name="slab"):
    o = np.asarray(outline, float)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    if n:
        o = M.resample_closed(o, n)
    V, F = M.prism(o, depth, axis=axis, center=center)
    return M.Part(V, F, mat, name=name)


def gem(center, r, mat, facets=6, h=None, rot=(0, 0, 0)):
    h = h or r * 1.4
    V, F = M.lathe([(0, -h * 0.55), (r, 0.0), (r * 0.62, h * 0.35), (0, h * 0.45)], facets)
    return M.Part(V, F, mat, name="gem").rot(Rx(rot[0]) @ Ry(rot[1]) @ Rz(rot[2])).move(center)


def crystal(center, length, radius, mat, sides=6, rot=(0, 0, 0)):
    V, F = M.lathe([(0, -length / 2), (radius * 0.75, -length * 0.2), (radius, 0.0), (radius * 0.8, length * 0.16),
                    (0, length / 2)], sides)
    return M.Part(V, F, mat, name="crystal").rot(Rx(rot[0]) @ Ry(rot[1]) @ Rz(rot[2])).move(center)


def ring_tube(center, r, tube_r, mat, axis="z", n=24, arc=360.0, a0=0.0):
    pts = []
    full = arc >= 359.9
    k = n + (0 if full else 0)
    for i in range(k + 1):
        a = math.radians(a0 + arc * i / n)
        if axis == "z":
            pts.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a), center[2]))
        elif axis == "y":
            pts.append((center[0] + r * math.cos(a), center[1], center[2] + r * math.sin(a)))
        else:
            pts.append((center[0], center[1] + r * math.cos(a), center[2] + r * math.sin(a)))
    up = (1, 0, 0) if axis == "z" else ((0, 1, 0) if axis == "y" else (1, 0, 0))
    up = (0, 0, 1) if axis == "z" else up
    V, F = M.tube(pts, [(tube_r, tube_r)] * len(pts), n=7, up=up, cap0=not full, cap1=not full)
    return M.Part(V, F, mat, name="ring")


def spikes_on_sphere(center, r, length, mat, count=10, seed=1, base=0.02):
    rng = np.random.default_rng(seed)
    out = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(count):
        y = 1 - (i + 0.5) / count * 2
        rad = math.sqrt(max(0.0, 1 - y * y))
        th = golden * i
        d = np.array([math.cos(th) * rad, math.sin(th) * rad, y])
        p0 = np.asarray(center) + d * r * 0.9
        p1 = np.asarray(center) + d * (r + length * (0.85 + 0.3 * rng.random()))
        out.append(tube([p0, p1], [base, 0.001], mat, n=6, up=tuple(np.cross(d, (0.3, 0.7, 0.2)) + 1e-3)))
    return out


def cone_spike(p0, p1, r, mat, n=6):
    return tube([p0, p1], [r, 0.0008], mat, n=n, up=(0.3, 0.5, 0.8))


def mirror_x(parts):
    return [p.mirrored(False) for p in parts]


def rotate_all(parts, R, center=(0, 0, 0)):
    for p in parts:
        p.rot(R, center)
    return parts


def move_all(parts, t):
    for p in parts:
        p.move(t)
    return parts


def scale_all(parts, s, center=(0, 0, 0)):
    for p in parts:
        p.scale(s, center)
    return parts
