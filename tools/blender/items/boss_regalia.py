"""bh-022: the fifteen boss collections rebuilt as fitted, textured regalia.

Every non-weapon piece (helm, vestment, armour, both gauntlets and greaves, signet, seal, pendant, brooch) and the seven
shields are authored in the model space of the standard hero skeleton (T-pose, 1.9 m, front -Y, left +X, Z up), so one
GLB is both the worn piece and the dropped item:

  * the piece's main object is exported in the frame BossSetVisuals.wear() attaches it with (slot origin + basis);
  * parts that must follow another bone (pauldrons on the upper arms, gauntlet hand plates, sabatons, tassets) are
    separate objects named "at_<bone>" — wear() re-parents each one to its own BoneAttachment;
  * materials are "<legend base>__it_boss_<set>_<role>": Godot's MaterialLibrary lays the bh-021 legend texture sets
    (engraved plate, dragon scale, mail, worn leather, storm wool, tyrant bone) on them through a box-projected UV map
    (legend_kit.finish_mesh); glows keep their palette emission.

Shields keep the hand-socket convention of item_gear.shield (handle at the origin, face -Y).

  blender -b --factory-startup --python tools/blender/items/boss_regalia.py -- [models] [icons] [set ids...]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import item_kit as K  # noqa: E402
from item_kit import M, Rx, Ry, Rz  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

# ------------------------------------------------------------------------------------------------------------ the sets
# plate/trim/cloth/leather/glow: (legend base, sRGB hex, metallic, roughness); glow: sRGB hex of the emission.
# style: helm, torso ("plate" | "brigandine" | "mantle" | "harness"), skirt, motif (emblem + ornaments).
SETS = {
    "dragonforge": dict(cls="knight", helm="great", torso="plate", skirt="tassets", motif="dragon", cape="tattered",
                        plate=("BH_DragonPlate", "6e2418", 0.85, 0.42), trim=("BH_Gold", "d9a553", 1.0, 0.3),
                        cloth=("BH_Cloth_Primary", "4a1410", 0.0, 0.9), leather=("BH_Leather", "3a2016", 0.0, 0.7),
                        glow="ff6a24", horn=("BH_Horn", "2a2220", 0.0, 0.45)),
    "truth_of_raikuru": dict(cls="ranger", helm="sallet", torso="brigandine", skirt="leather", motif="bolt", cape="split",
                             plate=("BH_HolyPlate", "d8e2e8", 1.0, 0.25), trim=("BH_Gold", "c9a45a", 1.0, 0.3),
                             cloth=("BH_Cloth_Primary", "243650", 0.0, 0.9), leather=("BH_Leather", "2c3440", 0.0, 0.7),
                             glow="6fe4ff", horn=("BH_Bone", "d6d2c4", 0.0, 0.5)),
    "crimson_glory": dict(cls="knight", helm="great", torso="plate", skirt="tassets", motif="sun", cape="long",
                          plate=("BH_Crimson", "8e1830", 0.9, 0.35), trim=("BH_Gold", "f0c060", 1.0, 0.26),
                          cloth=("BH_Cloth_Primary", "f0e6d0", 0.0, 0.88), leather=("BH_Leather", "3a1a14", 0.0, 0.7),
                          glow="ffb060", horn=("BH_Bone", "e8dcc0", 0.0, 0.5)),
    "grievance_of_the_fairy": dict(cls="ranger", helm="circlet", torso="brigandine", skirt="leaves", motif="leaf", cape="wings",
                                   plate=("BH_Steel", "4e7a62", 0.85, 0.4), trim=("BH_Silver", "c8d8cc", 1.0, 0.28),
                                   cloth=("BH_Cloth_Primary", "234832", 0.0, 0.9), leather=("BH_Leather", "3a3020", 0.0, 0.7),
                                   glow="b8ff8a", horn=("BH_Horn", "5a4630", 0.0, 0.5)),
    "wailing_mistress": dict(cls="mage", helm="hood", torso="mantle", skirt="robe", motif="tear", cape="tattered",
                             plate=("BH_Silver", "a89cc0", 1.0, 0.3), trim=("BH_Silver", "d8d0e8", 1.0, 0.24),
                             cloth=("BH_Cloth_Primary", "2e2142", 0.0, 0.9), leather=("BH_Leather", "221a2a", 0.0, 0.7),
                             glow="c490ff", horn=("BH_Bone", "d8d0e0", 0.0, 0.5)),
    "winter_court": dict(cls="mage", helm="crown", torso="mantle", skirt="robe", motif="snow", cape="fur",
                         plate=("BH_Silver", "b8d4ec", 1.0, 0.22), trim=("BH_Silver", "eef6ff", 1.0, 0.2),
                         cloth=("BH_Cloth_Primary", "3e5a80", 0.0, 0.88), leather=("BH_Leather", "2a3444", 0.0, 0.7),
                         glow="8eeaff", horn=("BH_Bone", "f4f8ff", 0.0, 0.45)),
    "sunken_crown": dict(cls="knight", helm="great", torso="plate", skirt="tassets", motif="trident", cape="long",
                         plate=("BH_Steel", "3a7470", 0.8, 0.45), trim=("BH_Gold", "b8955a", 1.0, 0.34),
                         cloth=("BH_Cloth_Primary", "1c3c48", 0.0, 0.9), leather=("BH_Leather", "2a2a22", 0.0, 0.7),
                         glow="62f0d8", horn=("BH_Bone", "e8b8a8", 0.0, 0.5)),
    "thunder_abbot": dict(cls="mage", helm="hood", torso="mantle", skirt="robe", motif="orbs", cape="long",
                          plate=("BH_Gold", "c89a58", 1.0, 0.3), trim=("BH_Gold", "e8c070", 1.0, 0.26),
                          cloth=("BH_Cloth_Primary", "1e3068", 0.0, 0.9), leather=("BH_Leather", "2a2030", 0.0, 0.7),
                          glow="88c0ff", horn=("BH_Bone", "e8dcc0", 0.0, 0.5)),
    "ashfall_pilgrim": dict(cls="mage", helm="mitre", torso="mantle", skirt="robe", motif="flame", cape="tattered",
                            plate=("BH_DarkSteel", "5a524c", 0.9, 0.5), trim=("BH_Gold", "a8784a", 1.0, 0.36),
                            cloth=("BH_Cloth_Primary", "5c5854", 0.0, 0.92), leather=("BH_Leather", "3a2a20", 0.0, 0.7),
                            glow="ff7040", horn=("BH_Bone", "d0c8b8", 0.0, 0.5)),
    "starfall_hunter": dict(cls="ranger", helm="sallet", torso="brigandine", skirt="leather", motif="star", cape="split",
                            plate=("BH_DarkSteel", "2a3656", 0.9, 0.36), trim=("BH_Gold", "e0c078", 1.0, 0.26),
                            cloth=("BH_Cloth_Primary", "1a2240", 0.0, 0.9), leather=("BH_Leather", "2a2430", 0.0, 0.7),
                            glow="aebcff", horn=("BH_Bone", "e8e0c8", 0.0, 0.5)),
    "gale_nomad": dict(cls="ranger", helm="wrap", torso="brigandine", skirt="scarves", motif="feather", cape="scarf",
                       plate=("BH_Steel", "8aa4a4", 0.85, 0.34), trim=("BH_Silver", "d8e0d8", 1.0, 0.28),
                       cloth=("BH_Cloth_Primary", "c8b890", 0.0, 0.92), leather=("BH_Leather", "5a4430", 0.0, 0.7),
                       glow="8af4f4", horn=("BH_Bone", "e0d8c0", 0.0, 0.5)),
    "obsidian_oath": dict(cls="knight", helm="great", torso="plate", skirt="tassets", motif="shard", cape="tattered",
                          plate=("BH_DarkSteel", "24222c", 1.0, 0.3), trim=("BH_Crimson", "b87058", 1.0, 0.3),
                          cloth=("BH_Cloth_Primary", "1a1418", 0.0, 0.9), leather=("BH_Leather", "1e1818", 0.0, 0.7),
                          glow="ec8ad0", horn=("BH_Horn", "18161c", 0.0, 0.35)),
    "pale_requiem": dict(cls="shadowblade", helm="hood", torso="harness", skirt="leather", motif="antler", cape="tattered",
                         plate=("BH_Silver", "a8b4c8", 1.0, 0.3), trim=("BH_Silver", "dcdcd0", 1.0, 0.26),
                         cloth=("BH_Cloth_Primary", "3e4a62", 0.0, 0.9), leather=("BH_Leather", "2a2e3a", 0.0, 0.7),
                         glow="90c0ff", horn=("BH_Bone", "e0dccc", 0.0, 0.5)),
    "serpent_veil": dict(cls="shadowblade", helm="cobra", torso="harness", skirt="leather", motif="serpent", cape="split",
                         plate=("BH_DragonPlate", "2a5a48", 0.7, 0.4), trim=("BH_Gold", "c8a868", 1.0, 0.3),
                         cloth=("BH_Cloth_Primary", "163a30", 0.0, 0.9), leather=("BH_Leather", "1e2a22", 0.0, 0.7),
                         glow="a8f878", horn=("BH_Horn", "302a20", 0.0, 0.45)),
    "eclipse_dancer": dict(cls="shadowblade", helm="hood", torso="harness", skirt="scarves", motif="crescent", cape="scarf",
                           plate=("BH_Silver", "5c4a80", 0.9, 0.3), trim=("BH_Silver", "d0d2e6", 1.0, 0.24),
                           cloth=("BH_Cloth_Primary", "34264e", 0.0, 0.9), leather=("BH_Leather", "221a2e", 0.0, 0.7),
                           glow="c49aff", horn=("BH_Bone", "e0dcec", 0.0, 0.5)),
}
ORDER = list(SETS.keys())
SHIELDED = {"dragonforge": "heater", "crimson_glory": "tower", "winter_court": "kite", "ashfall_pilgrim": "round",
            "pale_requiem": "heater", "serpent_veil": "round", "eclipse_dancer": "round"}
SLOTS = ["helm", "inner_garment", "armor", "leggings", "gloves_1", "gloves_2", "boots_1", "boots_2",
         "accessory_1", "accessory_2", "accessory_3", "accessory_4"]

# attachment frames of BossSetVisuals.wear() in Blender model space: origin, and R (local -> model)
I3 = np.eye(3)
FRAMES = {
    "helm": ((0.0, 0.0, 1.73), I3), "armor": ((0.0, 0.0, 1.30), I3), "inner_garment": ((0.0, 0.0, 0.93), I3),
    "leggings": ((0.0, 0.0, 0.93), I3),
    "gloves_1": ((0.639, 0.0, 1.44), Ry(-90)), "gloves_2": ((-0.639, 0.0, 1.44), Ry(90)),
    "boots_1": ((0.1, 0.0, 0.2305), I3), "boots_2": ((-0.1, 0.0, 0.2305), I3),
    "accessory_1": ((0.73, -0.06, 1.40), I3), "accessory_2": ((-0.73, -0.06, 1.40), I3),
    "accessory_3": ((0.0, -0.29, 1.28), I3), "accessory_4": ((-0.23, -0.22, 1.41), I3),
}


def srgb(h):
    return tuple((int(h[i:i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4))


def palette(sid):
    """Register this set's palette in item_kit.MAT; returns role -> key."""
    s = SETS[sid]
    keys = {}
    for role in ("plate", "trim", "cloth", "leather", "horn"):
        base, hx, met, rough = s[role]
        k = "boss_%s_%s" % (sid, role)
        K.MAT[k] = (base, srgb(hx), met, rough, None, 0)
        keys[role] = k
    k = "boss_%s_mail" % sid
    K.MAT[k] = ("BH_Mail", srgb("8a8c90"), 1.0, 0.45, None, 0)
    keys["mail"] = k
    k = "boss_%s_dark" % sid
    K.MAT[k] = ("BH_Leather", srgb("141214"), 0.0, 0.8, None, 0)
    keys["dark"] = k
    g = srgb(s["glow"])
    k = "boss_%s_glow" % sid
    K.MAT[k] = ("BH_Emissive", g, 0.0, 0.25, g, 2.2)
    keys["glow"] = k
    k = "boss_%s_gem" % sid
    K.MAT[k] = ("BH_Gem", tuple(c * 0.7 for c in g), 0.0, 0.08, g, 1.1)
    keys["gem"] = k
    return keys


# ------------------------------------------------------------------------------------------------------------ helpers
def P(VF, mat, name="part"):
    return M.Part(VF[0], VF[1], mat, name=name)


def srow(z, w, front, back, n, p=2.3, cx=0.0, cy=0.0, a0=0.0, a1=360.0):
    """One ring of a superelliptic body section; front = depth toward -Y, back = toward +Y."""
    full = abs(a1 - a0) >= 359.9
    out = []
    for a in np.radians(np.linspace(a0, a1, n, endpoint=not full)):
        c, s = math.cos(a), math.sin(a)
        x = w * np.sign(c) * abs(c) ** (2.0 / p)
        d = front if s < 0 else back
        y = d * np.sign(s) * abs(s) ** (2.0 / p)
        out.append((cx + x, cy + y, z))
    return np.array(out)


def shell(rows, mat, n=32, p=2.3, a0=0.0, a1=360.0, thick=0.012, bevel=0.0025, name="shell", caps=False):
    """Loft of body sections rows=[(z, w, front, back[, cx, cy])], solidified outward into a plate."""
    rings = [srow(r[0], r[1], r[2], r[3], n, p, r[4] if len(r) > 4 else 0.0, r[5] if len(r) > 5 else 0.0, a0, a1) for r in rows]
    full = abs(a1 - a0) >= 359.9
    V, F = M.loft(rings, cap0=caps, cap1=caps, closed=full)
    part = M.Part(V, F, mat, name=name)
    M.recalc_normals(part)
    if thick > 0:
        part = M.solidify(part, thick, offset=1.0, bevel_w=bevel, segs=1)
    return part


def band_trim(z, w, front, back, mat, r=0.006, n=40, p=2.3, cx=0.0, cy=0.0, a0=0.0, a1=360.0):
    pts = srow(z, w, front, back, n, p, cx, cy, a0, a1)
    full = abs(a1 - a0) >= 359.9
    pts = list(pts) + ([pts[0]] if full else [])
    return K.tube(pts, [r] * len(pts), mat, n=6, up=(0, 0, 1), cap=not full, name="trim")


def rivets(z, w, front, back, mat, count=10, r=0.006, p=2.3, a0=200.0, a1=340.0, cx=0.0, cy=0.0, out=0.004):
    parts = []
    for a in np.radians(np.linspace(a0, a1, count)):
        c, s = math.cos(a), math.sin(a)
        x = w * np.sign(c) * abs(c) ** (2.0 / p)
        d = front if s < 0 else back
        y = d * np.sign(s) * abs(s) ** (2.0 / p)
        n = np.array([x / max(w, 1e-4) ** 2, y / max(d, 1e-4) ** 2, 0.0])
        n = n / (np.linalg.norm(n) + 1e-9)
        parts.append(K.sphere(r, (cx + x + n[0] * out, cy + y + n[1] * out, z), mat, 8, 5))
    return parts


def slab(outline, depth, mat, bevel=0.002, axis="y"):
    p = K.slab(outline, depth, mat, axis=axis)
    return M.bevel(p, bevel, 1) if bevel > 0 else p


def xform(parts, R=None, t=(0, 0, 0), s=None):
    for p in parts:
        if s is not None:
            p.scale(s)
        if R is not None:
            p.rot(R)
        p.move(t)
    return parts


def curve(points, steps=6):
    pts = [np.array(p, float) for p in points]
    pad = [pts[0]] + pts + [pts[-1]]
    out = []
    for j in range(len(pts) - 1):
        a, b, c, d = pad[j:j + 4]
        for i in range(steps):
            t = i / steps
            out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3))
    out.append(pts[-1])
    return out


def horn(points, r0, mat, n=8, tip=0.0015):
    pts = curve(points, 5)
    k = len(pts)
    radii = [r0 * (1 - i / (k - 1)) ** 0.85 + tip for i in range(k)]
    return K.tube(pts, radii, mat, n=n, up=(0.2, 0.3, 0.9), name="horn")


def leaf_outline(L, W, n=14, tip=1.0, notch=0.0):
    """Lanceolate blade from (0,0) to (0,L) in (u, v); `notch` serrates the edge (feathers, leaves)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        w = W * math.sin(math.pi * t) ** 0.8 * (1 - 0.25 * t)
        if notch and 0.15 < t < 0.9:
            w *= 1 - notch * (i % 2)
        pts.append((w, t * L))
    left = [(-u, v) for u, v in reversed(pts[1:-1])]
    return pts + left


def star_outline(r_out, r_in, k=5, rot=90.0):
    pts = []
    for i in range(2 * k):
        a = math.radians(rot + i * 180.0 / k)
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def crescent_outline(r, thick=0.45, n=24):
    outer = [(r * math.cos(a), r * math.sin(a)) for a in np.radians(np.linspace(40, 320, n))]
    inner = [(r * 0.62 * math.cos(a) + r * thick * 0.55, r * 0.72 * math.sin(a)) for a in np.radians(np.linspace(300, 60, n))]
    return outer + inner


def bolt_outline(h, w):
    return [(-w * 0.2, h * 0.5), (w * 0.55, h * 0.5), (w * 0.05, h * 0.08), (w * 0.5, h * 0.08), (-w * 0.45, -h * 0.5),
            (-w * 0.05, -h * 0.06), (-w * 0.5, -h * 0.06)]


def drop_outline(r, L, n=16):
    pts = [(0.0, -L)]
    for a in np.radians(np.linspace(-150, 150, n)):
        pts.append((r * math.sin(a + math.pi), r * math.cos(a + math.pi) * -1 + 0.0))
    return pts


def flame_outline(h, w):
    pts = []
    for i in range(13):
        t = i / 12
        pts.append((w * math.sin(math.pi * t) ** 0.7 * (1 - 0.6 * t) + 0.12 * w * math.sin(t * 9), t * h))
    return pts + [(-u * 0.9, v * 0.94) for u, v in reversed(pts[1:-1])]


# ------------------------------------------------------------------------------------------------------------ emblems
def emblem(motif, size, mats, depth=0.012, relief=True):
    """The set's emblem, flat in the XZ plane (facing -Y), centred on the origin, `size` = overall height."""
    s = size
    T, G, W = mats["trim"], mats["glow"], mats["gem"]
    out = []
    if motif == "dragon":
        for sx in (-1, 1):
            wing = [(0.0, 0.05), (sx * 0.2, 0.28), (sx * 0.5, 0.42), (sx * 0.42, 0.18), (sx * 0.5, 0.1), (sx * 0.34, -0.02),
                    (sx * 0.42, -0.14), (sx * 0.2, -0.08), (0.0, -0.1)]
            if sx < 0:
                wing = wing[::-1]
            out.append(slab([(u * s, v * s) for u, v in wing], depth, T))
        out.append(slab([(0, 0.34 * s), (0.09 * s, 0.1 * s), (0.05 * s, -0.36 * s), (-0.05 * s, -0.36 * s), (-0.09 * s, 0.1 * s)], depth * 1.6, T))
        for sx in (-1, 1):
            out.append(K.cone_spike((sx * 0.05 * s, -depth, 0.28 * s), (sx * 0.16 * s, -depth, 0.5 * s), 0.02 * s, mats["horn"]))
        out.append(K.gem((0, -depth * 1.4, 0.12 * s), 0.07 * s, W, rot=(90, 0, 0)))
    elif motif == "bolt":
        out.append(K.ring_tube((0, 0, 0), 0.42 * s, 0.03 * s, T, axis="y", n=32))
        out.append(slab([(u * s, v * s) for u, v in bolt_outline(0.8, 0.5)], depth * 1.4, G))
    elif motif == "sun":
        out.append(K.sphere(0.2 * s, (0, 0, 0), T, 18, 8, scale=(1, 0.35, 1)))
        for i in range(12):
            a = math.radians(i * 30)
            L = 0.5 if i % 2 == 0 else 0.36
            ray = [(-0.05 * s, 0.18 * s), (0.05 * s, 0.18 * s), (0.0, L * s)]
            out.append(xform([slab(ray, depth, T)], Ry(-i * 30))[0])
        out.append(K.gem((0, -0.06 * s, 0), 0.1 * s, W, rot=(90, 0, 0)))
    elif motif == "leaf":
        for ang in (-38, 0, 38):
            lf = slab([(u * s, v * s) for u, v in leaf_outline(0.5, 0.13)], depth, T)
            out.append(xform([lf], Ry(ang), (0, 0, -0.18 * s))[0])
        for sx in (-1, 1):
            wing = slab([(u * s, v * s) for u, v in leaf_outline(0.4, 0.14)], depth * 0.6, G)
            out.append(xform([wing], Ry(sx * 115), (sx * 0.05 * s, 0.004, 0.05 * s))[0])
        out.append(K.gem((0, -depth * 1.2, -0.16 * s), 0.05 * s, W, rot=(90, 0, 0)))
    elif motif == "tear":
        out.append(K.ring_tube((0, 0, 0.1 * s), 0.3 * s, 0.025 * s, T, axis="y", n=28))
        drop = [(0.0, -0.46 * s)] + [(0.16 * s * math.sin(a), 0.16 * s * math.cos(a) - 0.1 * s) for a in np.radians(np.linspace(-140, 140, 15))]
        out.append(slab(drop[::-1], depth * 1.4, G))
        for sx in (-1, 1):
            d2 = [(sx * 0.3 * s + u * 0.45, v * 0.45 - 0.05 * s) for u, v in drop]
            out.append(slab(d2[::-1], depth, W))
    elif motif == "snow":
        for i in range(6):
            arm = [slab([(-0.025 * s, 0), (0.025 * s, 0), (0.02 * s, 0.46 * s), (0, 0.5 * s), (-0.02 * s, 0.46 * s)], depth, T)]
            for k, f in enumerate((0.22, 0.34)):
                for sx in (-1, 1):
                    arm.append(xform([slab([(-0.015 * s, 0), (0.015 * s, 0), (0.0, 0.14 * s * (1 - k * 0.3))], depth, T)],
                                     Ry(sx * 50), (0, 0, f * s))[0])
            out += xform(arm, Ry(i * 60))
        out.append(K.gem((0, -depth, 0), 0.08 * s, W, facets=6, rot=(90, 0, 0)))
    elif motif == "trident":
        out.append(slab([(-0.03 * s, -0.5 * s), (0.03 * s, -0.5 * s), (0.03 * s, 0.1 * s), (-0.03 * s, 0.1 * s)], depth, T))
        out.append(slab([(-0.24 * s, 0.05 * s), (0.24 * s, 0.05 * s), (0.2 * s, 0.13 * s), (-0.2 * s, 0.13 * s)], depth, T))
        for x in (-0.22, 0.0, 0.22):
            tine = [(x * s - 0.035 * s, 0.1 * s), (x * s + 0.035 * s, 0.1 * s), (x * s + 0.02 * s, 0.38 * s), (x * s, 0.5 * s),
                    (x * s - 0.02 * s, 0.38 * s)]
            out.append(slab(tine, depth, T))
        out.append(K.ring_tube((0, 0, 0.02 * s), 0.36 * s, 0.02 * s, T, axis="y", n=28, arc=200, a0=170))
        out.append(K.gem((0, -depth, 0.09 * s), 0.05 * s, W, rot=(90, 0, 0)))
    elif motif == "orbs":
        for r in (0.3, 0.44):
            out.append(K.ring_tube((0, 0, 0), r * s, 0.018 * s, T, axis="y", n=36))
        for i in range(6):
            a = math.radians(i * 60 + 30)
            out.append(K.sphere(0.055 * s, (0.44 * s * math.cos(a), -0.01, 0.44 * s * math.sin(a)), G, 12, 8))
        out.append(slab([(u * s, v * s) for u, v in bolt_outline(0.46, 0.3)], depth * 1.4, G))
    elif motif == "flame":
        out.append(slab([(u * s, v * s - 0.42 * s) for u, v in flame_outline(0.84, 0.32)], depth * 1.3, G))
        out.append(slab([(u * s * 0.55, v * s * 0.55 - 0.4 * s) for u, v in flame_outline(0.84, 0.32)], depth * 2.0, W))
        out.append(K.ring_tube((0, 0, -0.44 * s), 0.2 * s, 0.022 * s, T, axis="y", n=24, arc=180, a0=180))
    elif motif == "star":
        out.append(slab([(u * s, v * s) for u, v in star_outline(0.48, 0.2)], depth * 1.3, T))
        out.append(slab([(u * s, v * s) for u, v in star_outline(0.26, 0.11)], depth * 2.2, G))
    elif motif == "feather":
        for ang in (-35, 0, 35):
            fe = slab([(u * s, v * s) for u, v in leaf_outline(0.55, 0.11, n=18, notch=0.25)], depth, T)
            out.append(xform([fe], Ry(ang), (0, 0, -0.26 * s))[0])
        out.append(K.ring_tube((0, 0, -0.24 * s), 0.07 * s, 0.018 * s, T, axis="y", n=18))
        out.append(K.gem((0, -depth, -0.24 * s), 0.045 * s, W, rot=(90, 0, 0)))
    elif motif == "shard":
        for i, (x, h) in enumerate(((-0.3, 0.3), (-0.15, 0.46), (0.0, 0.6), (0.15, 0.46), (0.3, 0.3))):
            sh = [(x * s - 0.07 * s, -0.25 * s), (x * s + 0.07 * s, -0.25 * s), (x * s + 0.03 * s, h * s * 0.7), (x * s, h * s),
                  (x * s - 0.04 * s, h * s * 0.6)]
            out.append(slab(sh, depth * (1.6 if i == 2 else 1.1), mats["horn"]))
        out.append(slab([(-0.4 * s, -0.3 * s), (0.4 * s, -0.3 * s), (0.36 * s, -0.2 * s), (-0.36 * s, -0.2 * s)], depth, T))
        out.append(K.gem((0, -depth * 1.8, 0.02 * s), 0.06 * s, W, rot=(90, 0, 0)))
    elif motif == "antler":
        for sx in (-1, 1):
            main = [(sx * 0.03 * s, -0.3 * s, 0), (sx * 0.12 * s, -0.05 * s, 0), (sx * 0.28 * s, 0.2 * s, 0), (sx * 0.32 * s, 0.45 * s, 0)]
            pts = [(x, 0.0, z) for x, z, _ in main]
            out.append(horn([(x, -0.004, z) for x, z, _ in main], 0.04 * s, mats["horn"], n=7))
            for f, L in ((0.35, 0.18), (0.62, 0.15)):
                a = np.array(pts[1]) * (1 - f) + np.array(pts[3]) * f
                out.append(horn([tuple(a), tuple(a + np.array((-sx * 0.06 * s, 0, 0.1 * s))), tuple(a + np.array((-sx * 0.05 * s, 0, L * s)))],
                                0.022 * s, mats["horn"], n=6))
        out.append(K.gem((0, -depth, -0.3 * s), 0.06 * s, W, rot=(90, 0, 0)))
    elif motif == "serpent":
        pts = [(0.18 * s * math.sin(t * 2.2), -0.004, -0.42 * s + t * 0.8 * s) for t in np.linspace(0, 1, 16)]
        radii = [0.045 * s * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.6) for t in np.linspace(0, 1, 16)]
        out.append(K.tube(pts, radii, T, n=8, up=(0, -1, 0), name="serpent"))
        hd = pts[-1]
        out.append(K.sphere(0.07 * s, (hd[0], -0.01, hd[2] + 0.03 * s), T, 12, 8, scale=(1.2, 0.6, 1.0)))
        for sx in (-1, 1):
            out.append(K.gem((hd[0] + sx * 0.04 * s, -0.05 * s, hd[2] + 0.05 * s), 0.018 * s, W, rot=(90, 0, 0)))
        out.append(K.ring_tube((0, 0, 0), 0.4 * s, 0.018 * s, T, axis="y", n=30))
    else:  # crescent / eclipse
        out.append(slab([(u * s, v * s) for u, v in crescent_outline(0.46)], depth * 1.2, T))
        out.append(K.sphere(0.2 * s, (0.08 * s, 0.005, 0), mats["dark"], 18, 10, scale=(1, 0.25, 1)))
        out.append(K.ring_tube((0.08 * s, -0.004, 0), 0.21 * s, 0.012 * s, G, axis="y", n=28))
    return out


def front_emblem(motif, size, mats, center, depth=0.012, R=None):
    """The emblem placed on a surface facing -Y at `center` (optionally turned by R first)."""
    return xform(emblem(motif, size, mats, depth), R, center)


def arm_arch(x0, x1, rows, mat, zc=1.455, arc=230.0, thick=0.01, n=18, name="arch"):
    """Plates wrapped around the upper arm (axis along X at y=0, z=zc), open underneath: rows=[(t, r, lift)] with
    t 0..1 from x0 to x1. `arc` degrees centred on the top."""
    rings = []
    for t, r, lift in rows:
        x = x0 + (x1 - x0) * t
        ring = []
        for a in np.radians(np.linspace(90 - arc / 2, 90 + arc / 2, n)):
            ring.append((x, -r * math.cos(a), zc + lift + r * math.sin(a)))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    p = M.Part(V, F, mat, name=name)
    M.recalc_normals(p)
    return M.solidify(p, thick, offset=1.0, bevel_w=0.002)


def arm_tube(x0, x1, radii, mat, zc=1.44, n=20, thick=0.008, arc=360.0, yc=0.0, name="bracer"):
    """A sleeve around an arm along X: radii=[(t, ry, rz)]."""
    rings = []
    for t, ry, rz in radii:
        x = x0 + (x1 - x0) * t
        full = arc >= 359.9
        angs = np.radians(np.linspace(90 - arc / 2, 90 + arc / 2, n, endpoint=not full))
        rings.append(np.array([(x, yc - ry * math.cos(a), zc + rz * math.sin(a)) for a in angs]))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=arc >= 359.9)
    p = M.Part(V, F, mat, name=name)
    M.recalc_normals(p)
    return M.solidify(p, thick, offset=1.0, bevel_w=0.002) if thick > 0 else p


def arm_ring(x, r, mat, zc=1.44, tube=0.006, yc=0.0):
    return K.ring_tube((x, yc, zc), r, tube, mat, axis="x", n=26)


# ------------------------------------------------------------------------------------------------------------ helms
HEAD_C = (0.0, 0.01, 1.74)


def _helm_great(s, m, parts):
    rows = [(1.555, 0.132, 0.15, 0.16), (1.6, 0.15, 0.17, 0.176), (1.66, 0.16, 0.18, 0.182), (1.74, 0.163, 0.182, 0.185),
            (1.82, 0.157, 0.172, 0.178), (1.88, 0.142, 0.152, 0.162), (1.93, 0.112, 0.118, 0.128), (1.965, 0.07, 0.07, 0.08),
            (1.985, 0.02, 0.02, 0.025)]
    parts.append(shell(rows, m["plate"], n=36, p=2.2, thick=0.012, name="greathelm"))
    # eye slit and breaths
    slit = m["glow"] if s["motif"] in ("dragon", "shard") else m["dark"]
    for sx in (-1, 1):
        parts.append(K.box(0.075, 0.02, 0.016, (sx * 0.05, -0.19, 1.765), slit, 0.004).rot(Rz(-sx * 6), (sx * 0.05, -0.19, 1.765)))
    for i in range(3):
        for j in range(2):
            parts.append(K.sphere(0.006, (0.06 + j * 0.022, -0.185 + j * 0.008, 1.66 - i * 0.022), m["dark"], 6, 4))
    # keel down the face, brow and rim trims, rivets
    keel = [(0, -0.2, 1.6), (0, -0.203, 1.7), (0, -0.2, 1.8), (0, -0.175, 1.9), (0, -0.1, 1.965), (0, 0.0, 1.99)]
    parts.append(K.tube(curve(keel, 4), [0.009] * (5 * 4 + 1), m["trim"], n=6, up=(1, 0, 0)))
    parts.append(band_trim(1.8, 0.163, 0.18, 0.183, m["trim"], 0.008, p=2.2))
    parts.append(band_trim(1.585, 0.147, 0.168, 0.174, m["trim"], 0.009, p=2.2))
    parts += rivets(1.605, 0.155, 0.176, 0.182, m["trim"], 14, 0.006, 2.2, 0, 360)


def _helm_sallet(s, m, parts):
    rows = [(1.62, 0.145, 0.15, 0.25, 0, 0.03), (1.66, 0.152, 0.17, 0.22, 0, 0.02), (1.74, 0.16, 0.18, 0.2),
            (1.82, 0.155, 0.17, 0.19), (1.89, 0.135, 0.145, 0.165), (1.94, 0.1, 0.1, 0.12), (1.975, 0.04, 0.04, 0.05)]
    parts.append(shell(rows, m["plate"], n=36, p=2.1, a0=300, a1=600, thick=0.011, name="sallet"))
    # visor across the brow with a sight slit, cheek guards
    parts.append(shell([(1.74, 0.162, 0.188, 0.1), (1.79, 0.164, 0.192, 0.1), (1.83, 0.158, 0.18, 0.1)], m["plate"], n=24,
                       p=2.2, a0=205, a1=335, thick=0.012, name="visor"))
    parts.append(band_trim(1.765, 0.166, 0.196, 0.1, m["dark"], 0.006, p=2.2, a0=215, a1=325))
    parts.append(band_trim(1.83, 0.16, 0.184, 0.1, m["trim"], 0.006, p=2.2, a0=205, a1=335))
    parts.append(band_trim(1.625, 0.147, 0.155, 0.253, m["trim"], 0.007, p=2.1, cy=0.03, a0=300, a1=600))
    for sx in (-1, 1):
        cheek = [(0.0, 0.0), (0.03, -0.1), (0.075, -0.13), (0.09, -0.02)]
        parts.append(xform([slab(cheek, 0.01, m["plate"], axis="x")], Rz(sx * 18), (sx * 0.15, -0.09, 1.72))[0])


def _hood(s, m, parts, peak=0.06, drape=True):
    rows = [(1.5, 0.2, 0.2, 0.2), (1.56, 0.172, 0.19, 0.2), (1.64, 0.172, 0.2, 0.205), (1.74, 0.174, 0.2, 0.21),
            (1.83, 0.166, 0.188, 0.206), (1.9, 0.152, 0.165, 0.2, 0, 0.01), (1.95, 0.124, 0.132, 0.18, 0, 0.02 + peak * 0.2),
            (1.985, 0.075, 0.08, 0.13, 0, 0.03 + peak * 0.4), (2.0, 0.025, 0.025, 0.05, 0, 0.04 + peak * 0.5)]
    parts.append(shell(rows, m["cloth"], n=36, p=2.0, a0=306, a1=594, thick=0.012, name="hood"))
    # a stiffened edge that follows the hood's opening around the face
    edge = []
    for a in (306.0, 234.0):
        side = [srow(r[0], r[1], r[2], r[3], 1, 2.0, r[4] if len(r) > 4 else 0.0, r[5] if len(r) > 5 else 0.0, a, a)[0] for r in rows[:-1]]
        edge.append(side)
    rim = edge[0][::-1] + edge[1][1:]
    rim = [(x, y - 0.006, z) for x, y, z in rim]
    parts.append(K.tube(curve(rim, 3), [0.01] * (3 * (len(rim) - 1) + 1), m["trim"], n=6, up=(0, -1, 0), name="hood_rim"))
    if drape:
        parts += mantle_shell(m, 0.29, 1.56, 0.06)


def mantle_shell(m, w=0.3, z_top=1.57, drop=0.08, n=48, nv=6, mat=None, trim=True):
    """A soft poncho-like mantle over the shoulders: longer at the front and back, a gently scalloped hem."""
    rings = []
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for a in np.radians(np.linspace(0, 360, n, endpoint=False)):
            c, sn = math.cos(a), math.sin(a)
            rr = 0.15 + (w - 0.15) * math.sin(v * math.pi / 2) ** 0.8
            ry = rr * (0.95 + 0.1 * abs(sn))
            z = z_top - v * (0.17 + drop * abs(sn)) + (0.012 * math.sin(8 * a) * v ** 3)
            ring.append((rr * c, ry * sn * (1.0 if sn < 0 else 0.98), z))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False)
    p = M.Part(V, F, mat or m["cloth"], name="mantle")
    M.recalc_normals(p)
    out = [M.solidify(p, 0.012, offset=1.0, bevel_w=0.002)]
    if trim:
        hem = list(rings[-1]) + [rings[-1][0]]
        out.append(K.tube(hem, [0.008] * len(hem), m["trim"], n=6, up=(0, 0, 1), cap=False, name="hem"))
    return out[0] if len(out) == 1 else out


def helm(sid, m):
    s = SETS[sid]
    parts = []
    st, mo = s["helm"], s["motif"]
    if st == "great":
        _helm_great(s, m, parts)
    elif st == "sallet":
        _helm_sallet(s, m, parts)
    elif st in ("hood", "mitre", "cobra"):
        _hood(s, m, parts, peak=0.02 if st != "hood" else 0.08)
    elif st == "wrap":
        # a desert turban: a snug cap under full wraps, a veil across the lower face, the tail over the shoulder
        parts.append(shell([(1.72, 0.152, 0.172, 0.182), (1.82, 0.156, 0.176, 0.186), (1.9, 0.14, 0.155, 0.17), (1.95, 0.1, 0.11, 0.13),
                            (1.975, 0.04, 0.04, 0.05)], m["cloth"], n=32, p=2.0, thick=0.01, name="cap"))
        parts.append(shell([(1.6, 0.14, 0.168, 0.15), (1.66, 0.15, 0.176, 0.16), (1.7, 0.15, 0.176, 0.16)], m["leather"], n=26, p=2.0,
                           a0=200, a1=340, thick=0.008, name="veil"))
        for i in range(3):
            z = 1.76 + i * 0.05
            w = 0.172 - i * 0.018
            parts.append(K.ring_tube((0, 0.01, z), 1.0, 0.034, m["cloth"], axis="z", n=34).scale((w, w * 1.1, 1), (0, 0.01, z))
                         .rot(Rx(8 - i * 5), (0, 0, z)))
        tail = [(0.06, 0.17, 1.86), (0.12, 0.26, 1.75), (0.16, 0.3, 1.6), (0.2, 0.32, 1.45)]
        parts.append(K.tube(curve(tail, 4), [(0.05, 0.008)] * 13, m["cloth"], n=6, up=(0, 1, 0)))
        parts.append(K.ring_tube((0, 0.01, 1.87), 1.0, 0.007, m["trim"], axis="z", n=30).scale((0.186, 0.2, 1), (0, 0.01, 1.87)))
    elif st in ("circlet", "crown"):
        parts.append(K.ring_tube((0, 0.01, 1.83), 1.0, 0.011, m["trim"], axis="z", n=40).scale((0.152, 0.172, 1), (0, 0.01, 1.83)))
        parts.append(K.ring_tube((0, 0.01, 1.855), 1.0, 0.007, m["plate"], axis="z", n=40).scale((0.15, 0.17, 1), (0, 0.01, 1.855)))
    # ---- ornaments by motif
    if mo == "dragon":
        for sx in (-1, 1):
            parts.append(horn([(sx * 0.13, 0.03, 1.86), (sx * 0.22, 0.09, 1.92), (sx * 0.27, 0.2, 2.02), (sx * 0.24, 0.31, 2.14)], 0.042, m["horn"]))
            parts.append(horn([(sx * 0.155, 0.08, 1.7), (sx * 0.21, 0.16, 1.68), (sx * 0.25, 0.25, 1.72)], 0.022, m["horn"]))
        for i in range(6):
            t = i / 5
            y = -0.12 + 0.3 * t
            z = 1.97 - 0.2 * t ** 2
            parts.append(K.cone_spike((0, y, z), (0, y + 0.05, z + 0.08 - 0.03 * t), 0.02, m["horn"]))
    elif mo == "sun":
        for i in range(11):
            a = math.radians(-100 + i * 20)
            base = (0.14 * math.cos(a), 0.15 * math.sin(a) + 0.01, 1.9)
            L = 0.2 if i % 2 == 0 else 0.13
            tip = (0.2 * math.cos(a) * 1.25, 0.2 * math.sin(a) * 1.25 + 0.01, 1.9 + L)
            parts.append(K.cone_spike(base, tip, 0.02, m["trim"]))
        parts.append(K.ring_tube((0, 0.01, 1.9), 1.0, 0.01, m["trim"], axis="z", n=36).scale((0.145, 0.155, 1), (0, 0.01, 1.9)))
        parts += front_emblem("sun", 0.1, m, (0, -0.19, 1.86))
    elif mo == "bolt":
        parts.append(K.ring_tube((0, 0.2, 1.84), 0.22, 0.012, m["trim"], axis="y", n=40))
        for i in range(6):
            a = math.radians(i * 60 + 30)
            c = (0.24 * math.cos(a), 0.2, 1.84 + 0.24 * math.sin(a))
            parts.append(K.cone_spike((0.22 * math.cos(a), 0.2, 1.84 + 0.22 * math.sin(a)), (0.29 * math.cos(a), 0.2, 1.84 + 0.29 * math.sin(a)),
                                      0.012, m["trim"]))
        parts += xform([slab([(u * 0.12, v * 0.12) for u, v in bolt_outline(1.0, 0.5)], 0.01, m["glow"])], None, (0, 0.2, 1.84))
        for sx in (-1, 1):
            wing = [(0, 0), (0.05, 0.05), (0.14, 0.16), (0.1, 0.07), (0.15, 0.08), (0.09, 0.01)]
            parts.append(xform([slab([(sx * u, v) for u, v in wing], 0.008, m["trim"], axis="x")], None, (sx * 0.16, 0.02, 1.8))[0])
    elif mo == "leaf":
        for i in range(9):
            a = math.radians(-90 + (i - 4) * 24)
            base = (0.155 * math.cos(a), 0.17 * math.sin(a) + 0.01, 1.84)
            L = 0.11 + 0.05 * (1 - abs(i - 4) / 4)
            leaf = xform([slab([(u, v) for u, v in leaf_outline(L, 0.028)], 0.006, m["plate"])], Rz(math.degrees(a) + 90) @ Rx(-12), base)
            parts += leaf
        for sx in (-1, 1):
            parts.append(horn([(sx * 0.12, 0.08, 1.86), (sx * 0.17, 0.12, 1.97), (sx * 0.2, 0.18, 2.05)], 0.014, m["horn"], n=6))
            parts.append(horn([(sx * 0.17, 0.12, 1.97), (sx * 0.24, 0.12, 2.0)], 0.009, m["horn"], n=5))
            for k, (ang, L) in enumerate(((35, 0.26), (70, 0.2))):
                w = slab([(u, v) for u, v in leaf_outline(L, 0.07)], 0.004, m["glow"], bevel=0.0012)
                parts += xform([w], Ry(sx * ang) @ Rx(-20), (sx * 0.05, 0.19, 1.8 - k * 0.04))
        parts.append(K.gem((0, -0.18, 1.845), 0.02, m["gem"], rot=(90, 0, 0)))
    elif mo == "tear":
        parts.append(K.ring_tube((0, 0.16, 1.92), 0.2, 0.012, m["trim"], axis="y", n=40))
        for i in range(7):
            x = -0.09 + i * 0.03
            L = 0.06 + 0.05 * (1 - abs(i - 3) / 3)
            z0 = 1.83
            parts.append(K.tube([(x, -0.205, z0), (x, -0.215, z0 - L)], [0.002, 0.002], m["trim"], n=4))
            parts.append(K.sphere(0.011, (x, -0.215, z0 - L - 0.012), m["glow"], 8, 6, scale=(1, 1, 1.5)))
        parts.append(K.ring_tube((0, 0.01, 1.84), 1.0, 0.008, m["trim"], axis="z", n=36).scale((0.17, 0.205, 1), (0, 0.01, 1.84)))
        parts.append(K.gem((0, -0.21, 1.86), 0.022, m["gem"], rot=(90, 0, 0)))
    elif mo == "snow":
        for i in range(13):
            a = math.radians(-90 + (i - 6) * 20)
            base = (0.15 * math.cos(a), 0.17 * math.sin(a) + 0.01, 1.85)
            L = 0.08 + 0.12 * (1 - abs(i - 6) / 6) ** 1.5
            parts.append(K.crystal((base[0] * 1.04, base[1] * 1.04, base[2] + L / 2), L, 0.018, m["glow"], rot=(0, 0, 0)))
        parts.append(K.crystal((0, -0.17, 2.02), 0.28, 0.03, m["glow"]))
        parts.append(K.gem((0, -0.18, 1.845), 0.022, m["gem"], rot=(90, 0, 0)))
    elif mo == "trident":
        for x, h in ((-0.07, 0.14), (0.0, 0.2), (0.07, 0.14)):
            parts.append(K.cone_spike((x, -0.12, 1.92), (x * 1.3, -0.14, 1.92 + h), 0.018, m["trim"]))
        parts.append(K.ring_tube((0, 0.01, 1.915), 1.0, 0.011, m["trim"], axis="z", n=36).scale((0.13, 0.14, 1), (0, 0.01, 1.915)))
        for sx in (-1, 1):
            coral = [(sx * 0.16, 0.02, 1.82), (sx * 0.22, 0.04, 1.9), (sx * 0.25, 0.08, 2.0)]
            parts.append(horn(coral, 0.02, m["horn"], n=6))
            parts.append(horn([coral[1], (sx * 0.28, 0.02, 1.95)], 0.012, m["horn"], n=5))
            fin = [(0, 0), (0.02, 0.12), (0.1, 0.16), (0.06, 0.06), (0.08, 0.0)]
            parts.append(xform([slab([(v, u) for u, v in fin], 0.008, m["plate"], axis="x")], None, (sx * 0.165, 0.04, 1.66))[0])
    elif mo == "orbs":
        for tilt, r in ((12, 0.24), (-18, 0.3)):
            ring = K.ring_tube((0, 0.03, 1.86), r, 0.009, m["trim"], axis="z", n=48).rot(Rx(tilt), (0, 0.03, 1.86))
            parts.append(ring)
        for i in range(6):
            a = math.radians(i * 60 + 15)
            p = np.array((0.3 * math.cos(a), 0.3 * math.sin(a) + 0.03, 1.86))
            p = (Rx(-18) @ (p - np.array((0, 0.03, 1.86)))) + np.array((0, 0.03, 1.86))
            parts.append(K.sphere(0.022, tuple(p), m["glow"], 10, 8))
        parts.append(K.gem((0, -0.2, 1.84), 0.02, m["gem"], rot=(90, 0, 0)))
    elif mo == "flame":
        # the pilgrim's wide-brimmed hat over the hood, a bronze band and an ember badge on the turned-up brim
        parts.append(K.lathe([(0.0, 1.985), (0.2, 1.93), (0.33, 1.9), (0.345, 1.895), (0.34, 1.885), (0.2, 1.915), (0.0, 1.965)], m["leather"], 40, "brim"))
        parts.append(K.lathe([(0.0, 2.09), (0.1, 2.085), (0.14, 2.04), (0.15, 1.93), (0.0, 1.93)], m["leather"], 32, "crown"))
        parts.append(K.ring_tube((0, 0, 1.95), 0.152, 0.012, m["trim"], axis="z", n=32))
        parts.append(K.ring_tube((0, 0, 1.893), 0.343, 0.006, m["trim"], axis="z", n=48))
        parts += xform(emblem("flame", 0.08, m, 0.01), None, (0, -0.16, 1.99))
        for i in range(5):
            a2 = math.radians(200 + i * 35)
            parts.append(K.sphere(0.012, (0.3 * math.cos(a2), 0.3 * math.sin(a2), 1.88), m["glow"], 8, 6))
    elif mo == "star":
        parts += front_emblem("star", 0.12, m, (0, -0.205, 1.86))
        for i, (x, z, r) in enumerate(((-0.12, 1.9, 0.03), (0.12, 1.9, 0.03), (0.0, 1.97, 0.035))):
            parts.append(xform([slab(star_outline(r, r * 0.42), 0.006, m["trim"], axis="z")], None, (x, 0.05, z))[0])
        plume = [(0, 0.1, 1.95), (0, 0.22, 2.0), (0, 0.32, 1.96), (0, 0.4, 1.86)]
        parts.append(K.tube(curve(plume, 4), [0.03, 0.035, 0.032, 0.028, 0.025, 0.022, 0.02, 0.018, 0.016, 0.014, 0.012, 0.01, 0.006],
                            m["cloth"], n=8, up=(1, 0, 0)))
    elif mo == "feather":
        for i, (ang, L) in enumerate(((20, 0.34), (35, 0.3), (50, 0.26))):
            fe = slab([(u, v) for u, v in leaf_outline(L, 0.04, n=18, notch=0.3)], 0.005, m["trim"] if i % 2 else m["glow"], bevel=0.0012)
            parts += xform([fe], Rx(-(90 - ang)) @ Rz(12 - i * 12), (0.08 - i * 0.04, 0.12, 1.92))
        parts += front_emblem("feather", 0.08, m, (0, -0.2, 1.9))
    elif mo == "shard":
        heights = [0.1, 0.16, 0.12, 0.22, 0.14, 0.26, 0.14, 0.22, 0.12, 0.16, 0.1]
        for i, h in enumerate(heights):
            a = math.radians(-90 + (i - 5) * 22)
            base = (0.13 * math.cos(a), 0.14 * math.sin(a) + 0.01, 1.9)
            shard = [(-0.022, 0.0), (0.022, 0.0), (0.012, h * 0.7), (0.0, h), (-0.016, h * 0.55)]
            parts += xform([slab(shard, 0.012, m["horn"])], Rz(math.degrees(a) + 90) @ Rx(12), base)
        parts.append(K.gem((0, -0.2, 1.87), 0.022, m["gem"], rot=(90, 0, 0)))
    elif mo == "antler":
        for sx in (-1, 1):
            main = [(sx * 0.14, 0.02, 1.86), (sx * 0.22, 0.04, 1.96), (sx * 0.28, 0.07, 2.08), (sx * 0.3, 0.1, 2.2)]
            parts.append(horn(main, 0.026, m["horn"], n=7))
            for f, d in ((0.4, (-0.02, 0.0, 0.12)), (0.7, (sx * 0.08, -0.02, 0.08))):
                a = np.array(main[1]) * (1 - f) + np.array(main[3]) * f
                parts.append(horn([tuple(a), tuple(a + np.array(d) * 0.6), tuple(a + np.array(d))], 0.014, m["horn"], n=6))
        parts.append(K.gem((0, -0.2, 1.87), 0.02, m["gem"], rot=(90, 0, 0)))
    elif mo == "serpent":
        # a cobra's hood flared behind the head, scaled, and the serpent's head over the brow
        hood_o = [(-0.02, 0.0)] + [(0.28 * math.sin(t * math.pi) ** 0.8 * (1.0 - 0.3 * t), t * 0.46) for t in np.linspace(0.05, 0.95, 12)] + [(0.0, 0.5)]
        full = hood_o + [(-u, v) for u, v in reversed(hood_o[1:-1])]
        cobra = slab(full, 0.02, m["plate"], bevel=0.004)
        cobra.warp(lambda v: (v[0], v[1] + 0.22 * (v[0] / 0.3) ** 2, v[2]))
        parts += xform([cobra], Rx(-8), (0, 0.2, 1.55))
        parts.append(K.tube(curve([(0, 0.1, 1.97), (0, -0.05, 1.99), (0, -0.16, 1.93), (0, -0.2, 1.86)], 4),
                            [0.028 - 0.0012 * i for i in range(13)], m["plate"], n=10, up=(1, 0, 0)))
        parts.append(K.sphere(0.036, (0, -0.215, 1.85), m["plate"], 12, 8, scale=(1.2, 1.4, 0.8)))
        for sx in (-1, 1):
            parts.append(K.gem((sx * 0.024, -0.245, 1.86), 0.009, m["gem"], rot=(90, 0, 0)))
    elif mo == "crescent":
        parts += xform([slab(crescent_outline(0.2), 0.012, m["trim"])], Ry(-30), (0, 0.19, 1.93))
        parts.append(K.ring_tube((0.03, 0.2, 1.93), 0.24, 0.008, m["glow"], axis="y", n=44))
        parts.append(K.sphere(0.12, (0.05, 0.215, 1.93), m["dark"], 20, 10, scale=(1, 0.2, 1)))
        parts.append(K.gem((0, -0.21, 1.87), 0.02, m["gem"], rot=(90, 0, 0)))
    return parts


# ------------------------------------------------------------------------------------------------------------ body
TORSO_PLATE = [(1.05, 0.212, 0.172, 0.168), (1.12, 0.222, 0.186, 0.175), (1.2, 0.232, 0.212, 0.18), (1.28, 0.242, 0.232, 0.186),
               (1.36, 0.248, 0.236, 0.188), (1.43, 0.236, 0.214, 0.182), (1.49, 0.2, 0.186, 0.168), (1.53, 0.142, 0.15, 0.14)]
TORSO_SOFT = [(1.04, 0.208, 0.166, 0.165), (1.12, 0.216, 0.178, 0.17), (1.2, 0.224, 0.2, 0.176), (1.28, 0.232, 0.22, 0.18),
              (1.36, 0.238, 0.224, 0.182), (1.43, 0.228, 0.205, 0.178), (1.49, 0.19, 0.18, 0.165), (1.53, 0.138, 0.146, 0.138)]


def pauldron(sid, m, big=True):
    """The left pauldron over the shoulder and upper arm (bone upper_arm.L); mirrored for the right."""
    s = SETS[sid]
    mo = s["motif"]
    parts = []
    if big:
        parts.append(arm_arch(0.17, 0.36, [(0.0, 0.13, 0.03), (0.2, 0.15, 0.03), (0.55, 0.155, 0.015), (0.85, 0.145, 0.0), (1.0, 0.13, -0.01)],
                              m["plate"], arc=235, thick=0.012, name="pauldron"))
        for i, x in enumerate((0.345, 0.39, 0.43)):
            r = 0.125 - i * 0.012
            parts.append(arm_arch(x, x + 0.05, [(0.0, r, -0.012 - i * 0.004), (1.0, r - 0.006, -0.016 - i * 0.004)], m["plate"], arc=200,
                                  thick=0.008, name="lame"))
            parts.append(K.ring_tube((x + 0.05, 0.0, 1.455 - 0.016 - i * 0.004), r - 0.004, 0.0045, m["trim"], axis="x", n=20, arc=200, a0=-10))
        parts.append(K.ring_tube((0.172, 0.0, 1.485), 0.13, 0.008, m["trim"], axis="x", n=24, arc=235, a0=-27.5))
        for a in np.radians(np.linspace(20, 160, 6)):
            parts.append(K.sphere(0.007, (0.19, -0.152 * math.cos(a), 1.485 + 0.152 * math.sin(a)), m["trim"], 6, 4))
    else:
        parts.append(arm_arch(0.19, 0.33, [(0.0, 0.11, 0.02), (0.4, 0.125, 0.015), (1.0, 0.11, 0.0)], m["plate"], arc=200,
                              thick=0.009, name="spaulder"))
        parts.append(K.ring_tube((0.33, 0.0, 1.455), 0.108, 0.005, m["trim"], axis="x", n=20, arc=200, a0=-10))
        parts.append(K.ring_tube((0.19, 0.0, 1.475), 0.11, 0.005, m["trim"], axis="x", n=20, arc=200, a0=-10))
    top = 1.62 if big else 1.59
    if mo == "dragon":
        for i in range(4):
            x = 0.2 + i * 0.05
            parts.append(K.cone_spike((x, 0.0, top - 0.01 - i * 0.012), (x + 0.07, 0.02, top + 0.11 - i * 0.03), 0.022, m["horn"]))
        parts.append(horn([(0.2, -0.1, 1.55), (0.26, -0.16, 1.6), (0.33, -0.2, 1.7)], 0.02, m["horn"], n=6))
    elif mo == "sun":
        for i in range(7):
            a = math.radians(-60 + i * 20)
            b = np.array((0.26, 0.0, 1.46))
            d = np.array((0.02, math.sin(a) * 0.6, math.cos(a)))
            parts.append(K.cone_spike(tuple(b + d * 0.15), tuple(b + d * (0.27 if i % 2 == 0 else 0.22)), 0.018, m["trim"]))
        parts += xform(emblem("sun", 0.1, m, 0.01), None, (0.27, -0.168, 1.47))
    elif mo == "trident":
        for i in range(3):
            fin = [(0, 0), (0.03, 0.1 + i * 0.02), (0.1, 0.15 + i * 0.02), (0.07, 0.05), (0.1, 0.0)]
            parts.append(xform([slab([(u, v) for u, v in fin], 0.01, m["trim"], axis="y")], None, (0.2 + i * 0.06, 0.0, top - 0.03 - i * 0.012))[0])
        parts.append(horn([(0.3, -0.12, 1.52), (0.34, -0.17, 1.6), (0.33, -0.16, 1.68)], 0.016, m["horn"], n=5))
    elif mo == "shard":
        for i, h in enumerate((0.16, 0.22, 0.14, 0.18)):
            x = 0.2 + i * 0.045
            sh = [(-0.02, 0), (0.025, 0), (0.012, h * 0.7), (0.0, h), (-0.012, h * 0.5)]
            parts += xform([slab(sh, 0.014, m["horn"])], Ry(-20 - i * 8), (x, 0.0, top - 0.02))
    elif mo == "bolt":
        parts += xform([slab([(u * 0.16, v * 0.16) for u, v in bolt_outline(1.0, 0.5)], 0.01, m["glow"])], None, (0.26, -0.135, 1.47))
    elif mo == "leaf":
        for i in range(4):
            lf = slab(leaf_outline(0.16 - i * 0.015, 0.04), 0.006, m["plate"])
            parts += xform([lf], Ry(-60 - i * 12) @ Rx(-10), (0.22 + i * 0.03, 0.02, 1.54))
    elif mo == "star":
        parts.append(xform([slab(star_outline(0.06, 0.025), 0.01, m["trim"])], None, (0.26, -0.135, 1.47))[0])
    elif mo == "feather":
        for i in range(3):
            fe = slab(leaf_outline(0.18, 0.035, notch=0.3), 0.005, m["trim"], bevel=0.001)
            parts += xform([fe], Ry(-70 + i * 12), (0.26 + i * 0.03, 0.04, 1.55))
    elif mo == "antler":
        parts.append(horn([(0.24, 0.0, 1.57), (0.3, 0.02, 1.64), (0.34, 0.05, 1.72)], 0.016, m["horn"], n=6))
        parts.append(horn([(0.28, 0.01, 1.61), (0.34, 0.0, 1.62)], 0.01, m["horn"], n=5))
    elif mo == "serpent":
        coil = [(0.22 + 0.13 * t, -0.13 * math.cos(t * 9), 1.455 + 0.13 * math.sin(t * 9)) for t in np.linspace(0, 1, 30)]
        parts.append(K.tube(coil, [0.014] * len(coil), m["trim"], n=6, up=(1, 0, 0)))
    elif mo == "crescent":
        parts += xform([slab(crescent_outline(0.09), 0.01, m["trim"])], None, (0.26, -0.14, 1.47))
    for p in parts:
        p.bone = "upper_arm.L"
    return parts


def cape(sid, m, kind):
    """A cloak hanging behind the shoulders (chest bone)."""
    parts = []
    if kind in ("none",):
        return parts
    if kind == "wings":
        # the fairy's four wings: dim jewel membranes with glowing veins, angled out behind the shoulders
        for sx in (-1, 1):
            for k, (ang, L, W) in enumerate(((34, 0.46, 0.15), (70, 0.34, 0.11))):
                R = Ry(sx * ang) @ Rz(sx * 18) @ Rx(-8)
                org = (sx * 0.05, 0.215, 1.42 - k * 0.08)
                parts += xform([slab(leaf_outline(L, W, n=16), 0.004, m["gem"], bevel=0.0012)], R, org)
                for f in (0.0, -0.35, 0.35):
                    vein = [(0, -0.003, 0.0), (W * f * 0.5, -0.003, L * 0.45), (W * f * 0.6, -0.003, L * 0.85)]
                    parts += xform([K.tube(vein, [0.003, 0.0025, 0.001], m["glow"], n=4)], R, org)
        return parts
    if kind in ("scarf",):
        for sx, L in ((-1, 0.78), (1, 0.62)):
            pts = [(sx * 0.1, 0.17, 1.5), (sx * 0.14, 0.24, 1.3), (sx * 0.17, 0.3, 1.08), (sx * 0.2, 0.34, 1.5 - L)]
            parts.append(K.tube(curve(pts, 4), [(0.06, 0.008)] * 13, m["cloth"], n=8, up=(0, 1, 0), name="scarf"))
        parts.append(K.ring_tube((0, 0.0, 1.52), 1.0, 0.03, m["cloth"], axis="z", n=30).scale((0.16, 0.17, 1), (0, 0, 1.52)))
        return parts
    split = kind == "split"
    length = {"long": 1.2, "tattered": 1.05, "split": 0.95, "fur": 1.15}.get(kind, 1.0)
    halves = (-1, 1) if split else (0,)
    for h in halves:
        nu, nv = 9, 12
        def fn(u, v, h=h):
            if split:
                x0, x1 = (-0.2, -0.015) if h < 0 else (0.015, 0.2)
            else:
                x0, x1 = -0.2, 0.2
            x = x0 + (x1 - x0) * u
            flare = 1.0 + 0.5 * v
            z = 1.5 - v * length
            y = 0.19 + 0.05 * v + 0.03 * math.sin(u * math.pi * 3 + v) * v - 0.04 * (1 - abs(2 * u - 1)) * (1 - v)
            hem = 0.0
            if kind == "tattered" and v > 0.92:
                hem = 0.05 * (abs(math.sin(u * 23.0)) - 0.5)
            return (x * flare, y, z + hem)
        V, F = M.grid(fn, nu, nv)
        cl = M.Part(V, F, m["cloth"], name="cape")
        M.recalc_normals(cl)
        parts.append(M.solidify(cl, 0.012, offset=0.0))
    parts.append(K.tube(curve([(-0.2, 0.19, 1.5), (0.0, 0.16, 1.53), (0.2, 0.19, 1.5)], 4), [0.012] * 9, m["trim"], n=6, up=(0, 0, 1)))
    if kind == "fur":
        for i in range(18):
            a = math.radians(i * 20)
            parts.append(K.sphere(0.05, (0.2 * math.cos(a), 0.18 * math.sin(a), 1.52), m["horn"], 8, 6, scale=(1.3, 1.3, 0.8)))
    return parts


def armor(sid, m):
    s = SETS[sid]
    mo, st = s["motif"], s["torso"]
    parts = []
    if st == "plate":
        parts.append(shell(TORSO_PLATE, m["plate"], n=40, p=2.4, thick=0.014, name="cuirass"))
        keel = [(0, -0.188, 1.08), (0, -0.216, 1.2), (0, -0.24, 1.32), (0, -0.22, 1.44), (0, -0.19, 1.5)]
        parts.append(K.tube(curve(keel, 4), [0.009] * 17, m["trim"], n=6, up=(1, 0, 0)))
        for z, w, f, b in ((1.49, 0.2, 0.188, 0.17), (1.43, 0.238, 0.217, 0.185)):
            parts.append(band_trim(z, w, f, b, m["trim"], 0.008, p=2.4))
        # the fauld: three lames over the belly
        for i in range(3):
            z = 1.06 - i * 0.04
            parts.append(shell([(z - 0.045, 0.212 + i * 0.006, 0.172 + i * 0.004, 0.1), (z, 0.214 + i * 0.006, 0.176 + i * 0.004, 0.1)],
                               m["plate"], n=24, p=2.4, a0=195, a1=345, thick=0.009, name="fauld"))
            parts.append(band_trim(z - 0.044, 0.216 + i * 0.006, 0.178 + i * 0.004, 0.1, m["trim"], 0.005, p=2.4, a0=195, a1=345))
        # gorget
        for i in range(2):
            z = 1.53 + i * 0.03
            parts.append(shell([(z, 0.15 - i * 0.012, 0.158 - i * 0.012, 0.148 - i * 0.01), (z + 0.035, 0.13 - i * 0.012, 0.14 - i * 0.012, 0.13 - i * 0.01)],
                               m["plate"], n=30, p=2.2, thick=0.008, name="gorget"))
        parts += rivets(1.36, 0.25, 0.238, 0.19, m["trim"], 12, 0.006, 2.4, 200, 340)
        parts += front_emblem(mo, 0.16, m, (0, -0.248, 1.3))
        pl = pauldron(sid, m, True)
        parts += pl + [p.mirrored(False).to(bone="upper_arm.R") for p in pl]
    elif st == "brigandine":
        parts.append(shell(TORSO_SOFT, m["leather"], n=40, p=2.3, thick=0.012, name="jerkin"))
        # riveted plates stitched on the front: two columns of overlapping lames
        for i in range(5):
            z = 1.1 + i * 0.07
            parts.append(shell([(z, 0.2, 0.2 + 0.006 * i, 0.1), (z + 0.06, 0.205, 0.206 + 0.006 * i, 0.1)], m["plate"], n=20, p=2.3,
                               a0=205, a1=335, thick=0.007, name="plates"))
            parts += rivets(z + 0.03, 0.205, 0.216 + 0.006 * i, 0.1, m["trim"], 7, 0.0045, 2.3, 210, 330)
        parts.append(K.box(0.03, 0.02, 0.4, (0, -0.228, 1.29), m["trim"], 0.004))
        parts.append(shell([(1.5, 0.19, 0.185, 0.17), (1.57, 0.15, 0.155, 0.15)], m["leather"], n=30, p=2.2, thick=0.012, name="collar"))
        parts.append(band_trim(1.57, 0.152, 0.158, 0.152, m["trim"], 0.006, p=2.2))
        pl = pauldron(sid, m, False)
        parts += pl + [p.mirrored(False).to(bone="upper_arm.R") for p in pl]
        # a baldric across the chest
        bal = [(0.2, -0.17, 1.48), (0.1, -0.235, 1.34), (-0.08, -0.232, 1.16), (-0.2, -0.17, 1.06)]
        parts.append(K.tube(curve(bal, 4), [(0.022, 0.005)] * 13, m["leather"], n=6, up=(0, -1, 0)))
    elif st == "mantle":
        # a robe's bodice under a layered mantle, a stole down the front, a clasp
        parts.append(shell(TORSO_SOFT, m["cloth"], n=40, p=2.2, thick=0.01, name="bodice"))
        parts += mantle_shell(m, 0.33, 1.58, 0.1)
        parts.append(shell([(1.36, 0.27, 0.23, 0.23), (1.44, 0.24, 0.21, 0.21), (1.5, 0.2, 0.19, 0.19)], m["plate"], n=40, p=2.0,
                           thick=0.008, name="collar_plate"))
        parts.append(band_trim(1.36, 0.272, 0.232, 0.232, m["trim"], 0.006, p=2.0))
        parts += front_emblem(mo, 0.13, m, (0, -0.245, 1.44))
        if mo == "snow":
            for i in range(22):
                a = math.radians(i * 16.4)
                parts.append(K.sphere(0.045, (0.3 * math.cos(a), 0.26 * math.sin(a), 1.33), m["horn"], 8, 6, scale=(1.2, 1.2, 0.8)))
            for sx in (-1, 1):
                for i in range(3):
                    parts.append(K.crystal((sx * (0.24 + i * 0.04), 0.0, 1.5 + i * 0.03), 0.16 - i * 0.03, 0.02, m["glow"], rot=(0, sx * (30 + i * 10), 0)))
        elif mo == "orbs":
            for sx in (-1, 1):
                parts.append(K.ring_tube((sx * 0.27, 0.0, 1.48), 0.09, 0.008, m["trim"], axis="x", n=24))
                parts.append(K.sphere(0.03, (sx * 0.27, 0.0, 1.48), m["glow"], 12, 8))
            for i in range(14):
                a = math.radians(190 + i * 11.5)
                parts.append(K.sphere(0.012, (0.18 * math.cos(a), 0.2 * math.sin(a) - 0.02, 1.47 - 0.1 * abs(math.cos(a / 2))), m["horn"], 8, 5))
        elif mo == "flame":
            for sx in (-1, 1):
                parts.append(K.lathe([(0.0, 0.0), (0.03, -0.005), (0.04, -0.05), (0.035, -0.06), (0.0, -0.055)], m["trim"], 12).move((sx * 0.3, -0.12, 1.33)))
                parts.append(K.sphere(0.012, (sx * 0.3, -0.12, 1.265), m["glow"], 8, 6))
        elif mo == "tear":
            for sx in (-1, 1):
                for i in range(4):
                    x = sx * (0.2 + i * 0.035)
                    parts.append(K.tube([(x, -0.2, 1.33), (x, -0.21, 1.25 - i * 0.02)], [0.0025, 0.0025], m["trim"], n=4))
                    parts.append(K.sphere(0.01, (x, -0.21, 1.235 - i * 0.02), m["glow"], 8, 6, scale=(1, 1, 1.5)))
    else:  # harness: fitted leather, crossed straps, one layered pauldron
        parts.append(shell(TORSO_SOFT, m["leather"], n=40, p=2.3, thick=0.011, name="harness"))
        parts.append(shell([(1.12, 0.214, 0.186, 0.18), (1.34, 0.236, 0.228, 0.186), (1.44, 0.226, 0.21, 0.182)], m["plate"], n=30,
                           p=2.3, a0=215, a1=325, thick=0.008, name="breast"))
        for sx in (-1, 1):
            strap = [(sx * 0.2, -0.17, 1.48), (sx * 0.05, -0.238, 1.3), (-sx * 0.1, -0.232, 1.16), (-sx * 0.2, -0.17, 1.06)]
            parts.append(K.tube(curve(strap, 4), [(0.018, 0.005)] * 13, m["dark"], n=6, up=(0, -1, 0)))
        parts.append(shell([(1.49, 0.185, 0.18, 0.165), (1.6, 0.13, 0.13, 0.13)], m["cloth"], n=30, p=2.1, thick=0.012, name="cowl"))
        pl = pauldron(sid, m, True)
        parts += pl
        sp = pauldron(sid, m, False)
        parts += [p.mirrored(False).to(bone="upper_arm.R") for p in sp]
    parts += cape(sid, m, s["cape"])
    return parts


# ------------------------------------------------------------------------------------------------------------ hips
def _panel(x0, x1, z0, z1, y0, mat, bulge=0.02, flare=0.2, hem=None, thick=0.01, nu=6, nv=8, back=False):
    """A hanging panel (tabard / tasset) at y = y0, bulging outward (-Y for the front, +Y for the back), z0 down to z1."""
    out = 1.0 if back else -1.0

    def fn(u, v):
        xm = (x0 + x1) / 2
        x = xm + (x0 + (x1 - x0) * u - xm) * (1 + flare * v)
        z = z0 + (z1 - z0) * v
        if hem == "point":
            z -= (z0 - z1) * 0.18 * (1 - abs(2 * u - 1)) * v ** 4
        elif hem == "round":
            z -= (z0 - z1) * 0.1 * (1 - (2 * u - 1) ** 2) * v ** 4
        y = y0 + out * bulge * math.sin(math.pi * u) * (0.4 + 0.6 * v)
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = M.Part(V, F, mat, name="panel")
    M.recalc_normals(p)
    return M.solidify(p, thick, offset=0.0, bevel_w=0.002)


def inner_garment(sid, m):
    s = SETS[sid]
    mo, sk, cls = s["motif"], s["skirt"], s["cls"]
    parts = []
    # belt and buckle
    parts.append(shell([(0.975, 0.222, 0.18, 0.176), (1.03, 0.222, 0.182, 0.178)], m["leather"], n=36, p=2.3, thick=0.01, name="belt"))
    parts.append(band_trim(0.975, 0.224, 0.183, 0.18, m["trim"], 0.005, p=2.3))
    parts.append(band_trim(1.03, 0.224, 0.185, 0.182, m["trim"], 0.005, p=2.3))
    parts += front_emblem(mo, 0.075, m, (0, -0.2, 1.0))
    if cls == "knight":
        parts.append(shell([(0.84, 0.25, 0.2, 0.2), (0.9, 0.236, 0.19, 0.19), (0.975, 0.222, 0.18, 0.178)], m["mail"], n=36, p=2.2,
                           thick=0.008, name="mail_skirt"))
        # tassets on the thighs
        for sx, bone in ((1, "thigh.L"), (-1, "thigh.R")):
            for i in range(3):
                z0 = 0.965 - i * 0.075
                tp = _panel(min(sx * 0.02, sx * 0.21), max(sx * 0.02, sx * 0.21), z0, z0 - 0.1, -0.2 - 0.004 * i, m["plate"], bulge=0.03,
                            flare=0.1, thick=0.009)
                tp.bone = bone
                parts.append(tp)
                tr = K.tube([(sx * 0.02, -0.205 - 0.004 * i, z0 - 0.1), (sx * 0.115, -0.235 - 0.004 * i, z0 - 0.1), (sx * 0.21, -0.2 - 0.004 * i, z0 - 0.1)],
                            [0.005] * 3, m["trim"], n=5)
                tr.bone = bone
                parts.append(tr)
        bp = _panel(-0.18, 0.18, 0.96, 0.66, 0.2, m["cloth"], bulge=0.02, flare=0.3, hem="point", back=True)
        parts.append(bp)
    elif sk in ("robe",):
        fp = _panel(-0.12, 0.12, 0.99, 0.3, -0.215, m["cloth"], bulge=0.02, flare=0.55, hem="point")
        parts.append(fp)
        parts.append(K.tube([(-0.12, -0.222, 0.99), (-0.19, -0.225, 0.31)], [0.008, 0.008], m["trim"], n=5))
        parts.append(K.tube([(0.12, -0.222, 0.99), (0.19, -0.225, 0.31)], [0.008, 0.008], m["trim"], n=5))
        parts += front_emblem(mo, 0.12, m, (0, -0.245, 0.62))
        parts.append(_panel(-0.18, 0.18, 0.99, 0.3, 0.215, m["cloth"], bulge=0.02, flare=0.5, hem="round", back=True))
    elif sk == "leaves":
        for sx, bone in ((1, "thigh.L"), (-1, "thigh.R")):
            for i in range(4):
                lf = slab(leaf_outline(0.26 - i * 0.02, 0.06), 0.008, m["plate"] if i % 2 == 0 else m["leather"])
                lf = xform([lf], Rx(180) @ Ry(sx * (8 + i * 14)), (sx * (0.05 + i * 0.05), -0.2 + i * 0.03, 0.98))[0]
                lf.bone = bone
                parts.append(lf)
        for i in range(5):
            lf = slab(leaf_outline(0.3, 0.07), 0.008, m["leather"])
            parts += xform([lf], Rx(180) @ Ry(-40 + i * 20), (-0.16 + i * 0.08, 0.19, 0.98))
    elif sk == "scarves":
        for i, (x, L) in enumerate(((-0.1, 0.5), (0.02, 0.62), (0.12, 0.44))):
            sc = K.tube(curve([(x, -0.2, 0.99), (x * 1.3, -0.23, 0.8), (x * 1.6, -0.22, 0.99 - L)], 4), [(0.045, 0.006)] * 9,
                        m["cloth"] if i % 2 == 0 else m["leather"], n=6, up=(0, -1, 0))
            parts.append(sc)
        parts.append(_panel(-0.16, 0.16, 0.99, 0.55, 0.2, m["cloth"], bulge=0.02, flare=0.4, hem="point", back=True))
        for sx, bone in ((1, "thigh.L"), (-1, "thigh.R")):
            tp = _panel(min(sx * 0.06, sx * 0.21), max(sx * 0.06, sx * 0.21), 0.965, 0.76, -0.2, m["leather"], bulge=0.03, flare=0.15, thick=0.008)
            tp.bone = bone
            parts.append(tp)
    else:  # leather tassets and a back flap
        for sx, bone in ((1, "thigh.L"), (-1, "thigh.R")):
            for i in range(2):
                z0 = 0.965 - i * 0.1
                tp = _panel(min(sx * 0.05, sx * 0.19), max(sx * 0.05, sx * 0.19), z0, z0 - 0.15, -0.2 - 0.006 * i, m["leather"], bulge=0.035,
                            flare=0.12, hem="round", thick=0.009, nu=8)
                edge = [(sx * 0.05 * 1.12, -0.21 - 0.006 * i, z0 - 0.15), (sx * 0.12, -0.245 - 0.006 * i, z0 - 0.165), (sx * 0.19 * 1.12, -0.21 - 0.006 * i, z0 - 0.15)]
                et = K.tube(curve(edge, 4), [0.004] * 9, m["trim"], n=5)
                et.bone = bone
                parts.append(et)
                tp.bone = bone
                parts.append(tp)
                for r in rivets(z0 - 0.02, 0.2, 0.2, 0.1, m["trim"], 3, 0.004, 2.3, 245 if sx < 0 else 285, 265 if sx < 0 else 305):
                    r.bone = bone
                    parts.append(r)
        parts.append(_panel(-0.15, 0.15, 0.97, 0.66, 0.2, m["cloth"], bulge=0.02, flare=0.35, hem="point", back=True))
    return parts


# ------------------------------------------------------------------------------------------------------------ hands
def gauntlet(sid, m):
    """Left gauntlet: vambrace on the forearm (x 0.49..0.72) and a plated hand (bone hand.L)."""
    s = SETS[sid]
    mo, cls = s["motif"], s["cls"]
    parts = []
    mage = cls == "mage"
    body = m["cloth"] if mage else (m["plate"] if cls == "knight" else m["leather"])
    if mage:
        # a bell sleeve with an embroidered hem and a jewelled bracelet
        parts.append(arm_tube(0.5, 0.71, [(0.0, 0.07, 0.07), (0.5, 0.078, 0.078), (1.0, 0.105, 0.1)], m["cloth"], zc=1.44, thick=0.007, name="sleeve"))
        parts.append(arm_ring(0.708, 0.105, m["trim"], tube=0.007))
        parts.append(arm_ring(0.66, 0.088, m["trim"], tube=0.004))
        parts.append(arm_ring(0.735, 0.058, m["plate"], tube=0.009))
        parts.append(K.gem((0.735, -0.06, 1.44), 0.011, m["gem"], rot=(90, 0, 0)))
    else:
        parts.append(arm_tube(0.48, 0.72, [(0.0, 0.092, 0.09), (0.12, 0.078, 0.078), (0.6, 0.068, 0.07), (0.92, 0.07, 0.07), (1.0, 0.08, 0.08)],
                              body, zc=1.44, thick=0.01, name="vambrace"))
        parts.append(arm_ring(0.482, 0.092, m["trim"], tube=0.007))
        parts.append(arm_ring(0.716, 0.08, m["trim"], tube=0.006))
        parts.append(arm_tube(0.52, 0.7, [(0.0, 0.08, 0.082), (1.0, 0.075, 0.078)], m["plate"], zc=1.44, thick=0.008, arc=150, name="vplate"))
        for x in (0.56, 0.64):
            parts.append(arm_ring(x, 0.086, m["trim"], tube=0.004))
    # motif on the outer (top) face
    top = 1.44 + 0.085
    if mo == "dragon" or mo == "shard":
        for i in range(3):
            x = 0.52 + i * 0.06
            if mo == "dragon":
                parts.append(K.cone_spike((x, 0.0, top - 0.005), (x - 0.04, 0.0, top + 0.07 - i * 0.01), 0.018, m["horn"]))
            else:
                sh = [(-0.016, 0), (0.018, 0), (0.008, 0.07), (0.0, 0.1 - i * 0.015), (-0.01, 0.05)]
                parts += xform([slab(sh, 0.012, m["horn"], axis="x")], Rx(-10), (x, 0.0, top - 0.01))
    elif mo in ("sun", "star", "crescent", "bolt", "snow", "tear", "orbs", "flame", "trident", "feather", "leaf", "serpent", "antler"):
        parts += xform(emblem(mo, 0.08, m, 0.008), Rx(-90), (0.6, 0.0, top + 0.004))
        if mo in ("leaf", "feather"):
            fin = slab(leaf_outline(0.16, 0.035, notch=0.3 if mo == "feather" else 0.0), 0.005, m["trim"], bevel=0.001)
            parts += xform([fin], Ry(-90) @ Rx(0), (0.5, 0.0, top))
    # the hand: back plate, knuckle ridge, cuff flare
    if not mage:
        hp = []
        hp.append(arm_tube(0.72, 0.815, [(0.0, 0.066, 0.062), (0.5, 0.062, 0.058), (1.0, 0.055, 0.05)], m["plate"], zc=1.43, thick=0.008,
                           arc=170, name="handplate"))
        hp.append(K.tube([(0.8, -0.05, 1.46), (0.805, 0.0, 1.487), (0.8, 0.05, 1.46)], [0.009] * 3, m["trim"], n=6, up=(1, 0, 0)))
        for y in (-0.03, -0.01, 0.01, 0.03):
            hp.append(K.sphere(0.008, (0.808, y, 1.482), m["trim"], 6, 4))
        if mo in ("dragon", "shard", "serpent"):
            for y in (-0.03, 0.0, 0.03):
                hp.append(K.cone_spike((0.81, y, 1.47), (0.86, y, 1.46), 0.007, m["horn"]))
        hp.append(K.gem((0.765, 0.0, 1.49), 0.012, m["gem"], rot=(0, 0, 0)))
        for p in hp:
            p.bone = "hand.L"
        parts += hp
    return parts


# ------------------------------------------------------------------------------------------------------------ legs
def greave(sid, m):
    """Left greave (shin x = 0.1) with a knee cop, and a sabaton on the foot (bone foot.L)."""
    s = SETS[sid]
    mo, cls = s["motif"], s["cls"]
    parts = []
    X = 0.1
    mage = cls == "mage"
    body = m["plate"] if cls == "knight" else (m["leather"] if not mage else m["leather"])
    rows = [(0.1, 0.072, 0.1, 0.08), (0.16, 0.074, 0.098, 0.082), (0.26, 0.078, 0.1, 0.09), (0.36, 0.08, 0.103, 0.094),
            (0.44, 0.078, 0.1, 0.09), (0.5, 0.08, 0.1, 0.088)]
    parts.append(shell([(z, w, f, b, X, 0.0) for z, w, f, b in rows], body, n=28, p=2.2, thick=0.01, name="greave"))
    if not mage:
        parts.append(shell([(z, w + 0.004, f + 0.006, b, X, 0.0) for z, w, f, b in rows[1:5]], m["plate"], n=20, p=2.2, a0=200, a1=340,
                           thick=0.008, name="shinplate"))
    parts.append(band_trim(0.5, 0.082, 0.104, 0.09, m["trim"], 0.006, p=2.2, cx=X))
    parts.append(band_trim(0.1, 0.075, 0.104, 0.083, m["trim"], 0.006, p=2.2, cx=X))
    # knee cop with a fan
    parts.append(K.sphere(0.052, (X, -0.098, 0.53), m["plate"] if not mage else m["trim"], 16, 8, scale=(1.05, 0.42, 0.9)))
    for sx in (-1, 1):
        fan = [(0, 0), (0.07, 0.03), (0.08, -0.05), (0.03, -0.06)]
        parts.append(xform([slab([(sx * u, v) for u, v in fan], 0.008, m["plate"] if not mage else m["trim"])], None, (X + sx * 0.03, -0.09, 0.54))[0])
    parts.append(K.gem((X, -0.135, 0.535), 0.013, m["gem"], rot=(90, 0, 0)))
    if mo in ("sun", "star", "crescent", "bolt", "snow", "tear", "orbs", "flame", "trident", "feather", "leaf", "serpent", "antler"):
        parts += xform(emblem(mo, 0.07, m, 0.007), None, (X, -0.115, 0.32))
    elif mo in ("dragon", "shard"):
        for i in range(3):
            z = 0.2 + i * 0.09
            parts.append(K.cone_spike((X + 0.075, 0.0, z), (X + 0.13, 0.0, z + 0.04), 0.016, m["horn"]))
    # sabaton over the foot (foot bone), toes toward -Y
    fp = []
    frows = []
    for i in range(8):
        t = i / 7
        y = 0.075 - 0.33 * t
        w = 0.066 - 0.012 * t ** 2
        h = 0.13 - 0.07 * t ** 1.3
        frows.append((y, w, h))
    rings = [np.array([(X + w * math.cos(a), y, 0.005 + h * 0.5 * (1 + math.sin(a))) for a in np.radians(np.linspace(0, 360, 22, endpoint=False))])
             for y, w, h in frows]
    V, F = M.loft(rings, cap0=True, cap1=True)
    foot = M.Part(V, F, body if not mage else m["leather"], name="foot")
    M.recalc_normals(foot)
    fp.append(foot)
    for i in range(4):
        y = -0.07 - i * 0.045
        fp.append(K.ring_tube((X, y, 0.06 - i * 0.008), 1.0, 0.005, m["trim"], axis="y", n=20, arc=180, a0=0)
                  .scale((0.067 - i * 0.003, 1, 0.07 - i * 0.008), (X, y, 0.0)))
    fp.append(K.box(0.14, 0.34, 0.018, (X, -0.09, 0.009), m["dark"], 0.006))
    if mo in ("dragon", "shard"):
        fp.append(K.cone_spike((X, -0.25, 0.04), (X, -0.31, 0.03), 0.018, m["horn"]))
    for p in fp:
        p.bone = "foot.L"
    parts += fp
    return parts


# ------------------------------------------------------------------------------------------------------------ thighs
# bh-024: the Legguards. Unlike the rest of the regalia they are authored on the hero's own legs (BossSetVisuals.HERO_FIT
# leaves them as they are and scales them up about each thigh for the armoured class bodies): the thigh pieces follow
# thigh.L / thigh.R, the fauld or apron at the front of the hips is the piece itself (the hips).
THIGH = [(0.585, 0.083, 0.090, 0.080, 0.099, 0.010), (0.68, 0.095, 0.103, 0.088, 0.106, -0.004),
         (0.78, 0.106, 0.113, 0.094, 0.108, -0.018), (0.87, 0.112, 0.118, 0.098, 0.109, -0.027)]


def _thigh_rows(z0, z1, grow=0.0):
    zs = np.array([r[0] for r in THIGH])
    out = []
    for z in np.linspace(z0, z1, 4):
        vals = [float(np.interp(z, zs, [r[k] for r in THIGH])) for k in range(1, 6)]
        out.append((z, vals[0] + grow, vals[1] + grow, vals[2] + grow, vals[3], vals[4]))
    return out


def _on_thigh(z, a, grow=0.0):
    """A point on the left thigh's section at height z and angle a (270 = front), `grow` outside it."""
    (zz, w, f, b, cx, cy), = _thigh_rows(z, z, grow)[:1]
    return srow(z, w, f, b, 3, 2.3, cx, cy, a, a + 0.001)[0]


def legguard(sid, m):
    s = SETS[sid]
    mo, cls = s["motif"], s["cls"]
    left, hips = [], []
    if cls == "knight":
        # cuisses: three lames down the front and outside of each thigh, each with a trim and rivets
        for i, (z0, z1, g) in enumerate(((0.79, 0.88, 0.028), (0.69, 0.795, 0.024), (0.59, 0.70, 0.020))):
            left.append(shell(_thigh_rows(z0, z1, g), m["plate"], n=16, p=2.3, a0=195, a1=355, thick=0.008, bevel=0.0, name="cuisse"))
            r = _thigh_rows(z0 + 0.004, z0 + 0.004, g + 0.004)[0]
            left.append(band_trim(r[0], r[1], r[2], r[3], m["trim"], 0.005, 18, 2.3, r[4], r[5], 195, 355))
            left += rivets(z1 - 0.018, r[1], r[2], r[3], m["trim"], 3, 0.005, 2.3, 230, 320, r[4], r[5], 0.006)
        left += xform(emblem(mo, 0.07, m, 0.007), None, tuple(_on_thigh(0.745, 285.0, 0.036)))
        if mo in ("dragon", "shard"):
            for i in range(3):
                p0 = _on_thigh(0.62 + i * 0.09, 350.0, 0.028)
                left.append(K.cone_spike(tuple(p0), (p0[0] + 0.05, p0[1] + 0.005, p0[2] + 0.03), 0.014, m["horn"]))
        # the fauld: two lames across the front of the hips
        for i in range(2):
            z = 0.935 - i * 0.045
            hips.append(shell([(z - 0.045, 0.2 + 0.008 * i, 0.158 + 0.006 * i, 0.1), (z, 0.196 + 0.008 * i, 0.152 + 0.006 * i, 0.1)],
                              m["plate"], n=24, p=2.4, a0=205, a1=335, thick=0.008, name="fauld"))
            hips.append(band_trim(z - 0.044, 0.202 + 0.008 * i, 0.162 + 0.006 * i, 0.1, m["trim"], 0.0045, p=2.4, a0=205, a1=335))
    elif cls == "mage":
        # silk wraps round each thigh under a hanging embroidered panel on the outside
        left.append(shell(_thigh_rows(0.60, 0.86, 0.018), m["cloth"], n=24, p=2.2, thick=0.004, name="wrap"))
        for z in (0.63, 0.72, 0.81):
            r = _thigh_rows(z, z, 0.022)[0]
            left.append(band_trim(r[0], r[1], r[2], r[3], m["trim"], 0.004, 28, 2.2, r[4], r[5]))
        c = _on_thigh(0.75, 330.0, 0.03)
        pn = _panel(-0.05, 0.05, 0.16, -0.16, 0.0, m["cloth"], bulge=0.012, flare=0.25, hem="point", thick=0.006)
        pn.rot(Rz(60.0))
        pn.move(tuple(c))
        left.append(pn)
        left.append(K.gem(tuple(_on_thigh(0.80, 290.0, 0.04)), 0.013, m["gem"], rot=(90, 0, 0)))
        # an apron at the front of the hips, hemmed and gemmed
        hips.append(_panel(-0.1, 0.1, 0.95, 0.62, -0.15, m["cloth"], bulge=0.02, flare=0.4, hem="point", thick=0.006))
        hips.append(K.tube([(-0.1, -0.158, 0.95), (-0.14, -0.16, 0.63)], [0.006, 0.006], m["trim"], n=5))
        hips.append(K.tube([(0.1, -0.158, 0.95), (0.14, -0.16, 0.63)], [0.006, 0.006], m["trim"], n=5))
        hips += front_emblem(mo, 0.08, m, (0.0, -0.172, 0.8))
    else:
        # rangers and shadowblades: a leather guard on the front and outside of each thigh, strapped on, with a plate
        left.append(shell(_thigh_rows(0.60, 0.87, 0.02), m["leather"], n=24, p=2.3, a0=190, a1=360, thick=0.008, name="guard"))
        for z in (0.64, 0.83):
            r = _thigh_rows(z, z, 0.03)[0]
            left.append(band_trim(r[0], r[1], r[2], r[3], m["dark"], 0.0055, 28, 2.3, r[4], r[5]))
        left.append(shell(_thigh_rows(0.68, 0.79, 0.03), m["plate"], n=18, p=2.3, a0=240, a1=320, thick=0.007, name="plate"))
        r = _thigh_rows(0.79, 0.79, 0.036)[0]
        left.append(band_trim(r[0], r[1], r[2], r[3], m["trim"], 0.004, 16, 2.3, r[4], r[5], 240, 320))
        left += xform(emblem(mo, 0.055, m, 0.006), None, tuple(_on_thigh(0.735, 280.0, 0.044)))
        if cls == "shadowblade":
            # a knife sheathed on the outside of the thigh
            c = _on_thigh(0.72, 358.0, 0.036)
            left.append(K.box(0.016, 0.03, 0.2, (c[0], c[1], c[2] - 0.02), m["dark"], 0.006))
            left.append(K.tube([(c[0], c[1], c[2] + 0.08), (c[0], c[1], c[2] + 0.14)], [0.009, 0.008], m["leather"], n=6))
            left.append(K.sphere(0.012, (c[0], c[1], c[2] + 0.145), m["trim"], 8, 5))
        else:
            # a quiver of spare bolts on the outer thigh
            c = _on_thigh(0.74, 358.0, 0.04)
            left.append(K.tube([(c[0], c[1] + 0.01, c[2] - 0.1), (c[0], c[1] + 0.01, c[2] + 0.08)], [(0.024, 0.018)] * 2, m["leather"], n=10))
            for k in range(4):
                left.append(K.tube([(c[0] - 0.012 + 0.008 * k, c[1] + 0.01, c[2] + 0.08), (c[0] - 0.012 + 0.008 * k, c[1] + 0.01, c[2] + 0.14)],
                                   [0.0022, 0.0022], m["horn"], n=4))
        hips.append(band_trim(0.95, 0.19, 0.152, 0.1, m["dark"], 0.009, 24, 2.3, 0.0, 0.0, 195, 345))
        hips.append(K.lathe([(0.0, 0.0), (0.03, 0.0), (0.034, 0.008), (0.0, 0.01)], m["trim"], 18).rot(Rx(90)).move((0.0, -0.165, 0.95)))
        hips += front_emblem(mo, 0.05, m, (0.0, -0.178, 0.95))
    for p in left:
        p.bone = "thigh.L"
    right = [p.mirrored(False).to(bone="thigh.R") for p in left]
    return hips + left + right


# ------------------------------------------------------------------------------------------------------------ jewellery
def jewel(sid, m, slot):
    s = SETS[sid]
    mo = s["motif"]
    parts = []
    if slot == "accessory_1":   # signet: a band over the knuckles, a raised bezel with the emblem
        parts.append(K.ring_tube((0.785, 0.0, 1.43), 0.064, 0.009, m["trim"], axis="x", n=28).scale((1, 1, 0.9), (0.785, 0, 1.43)))
        parts.append(K.lathe([(0.0, 0.0), (0.03, 0.0), (0.034, 0.01), (0.03, 0.018), (0.0, 0.018)], m["trim"], 18).move((0.785, 0.0, 1.48)))
        parts += xform(emblem(mo, 0.05, m, 0.006), Rx(-90), (0.785, 0.0, 1.5))
    elif slot == "accessory_2":  # seal: a heavy band and a flat round seal with the emblem in relief (mirrored to the right hand)
        parts.append(K.ring_tube((0.785, 0.0, 1.43), 0.064, 0.012, m["plate"], axis="x", n=28).scale((1, 1, 0.9), (0.785, 0, 1.43)))
        parts.append(K.ring_tube((0.785, 0.0, 1.43), 0.066, 0.004, m["trim"], axis="x", n=28).scale((1, 1, 0.9), (0.772, 0, 1.43)))
        parts.append(K.lathe([(0.0, 0.0), (0.04, 0.0), (0.042, 0.008), (0.0, 0.008)], m["plate"], 24).move((0.785, 0.0, 1.485)))
        parts.append(K.ring_tube((0.785, 0.0, 1.494), 0.038, 0.004, m["trim"], axis="z", n=24))
        parts += xform(emblem(mo, 0.055, m, 0.005), Rx(-90), (0.785, 0.0, 1.497))
        parts = [p.mirrored(False) for p in parts]
    elif slot == "accessory_3":  # pendant on a chain around the neck
        chain = []
        for a in np.radians(np.linspace(0, 360, 29)):
            y = 0.17 * math.sin(a)
            z = 1.55 - (0.13 if math.sin(a) < 0 else 0.0) * abs(math.sin(a)) ** 3
            chain.append((0.16 * math.cos(a), y - (0.06 * abs(math.sin(a)) ** 4 if math.sin(a) < 0 else 0.0), z))
        for i in range(len(chain) - 1):
            a, b = np.array(chain[i]), np.array(chain[i + 1])
            parts.append(K.ring_tube(tuple((a + b) / 2), 0.011, 0.0028, m["trim"], axis="y" if i % 2 else "x", n=7))
        parts.append(K.lathe([(0.0, 0.0), (0.046, 0.0), (0.05, 0.008), (0.046, 0.014), (0.0, 0.014)], m["plate"], 28).rot(Rx(90)).move((0, -0.265, 1.33)))
        parts.append(K.ring_tube((0, -0.272, 1.33), 0.048, 0.005, m["trim"], axis="y", n=28))
        parts += xform(emblem(mo, 0.075, m, 0.007), None, (0, -0.28, 1.33))
        parts.append(K.ring_tube((0, -0.265, 1.405), 0.012, 0.004, m["trim"], axis="x", n=12))
    else:  # brooch: the cloak clasp on the right shoulder
        c = (-0.2, -0.235, 1.43)
        parts.append(K.lathe([(0.0, 0.0), (0.055, 0.0), (0.06, 0.01), (0.052, 0.016), (0.0, 0.016)], m["trim"], 28).rot(Rx(90)).move(c))
        parts += xform(emblem(mo, 0.08, m, 0.008), None, (c[0], c[1] - 0.018, c[2]))
        parts.append(K.tube([(c[0] - 0.08, c[1] + 0.005, c[2] - 0.02), (c[0] + 0.08, c[1] + 0.005, c[2] + 0.02)], [0.004, 0.003], m["trim"], n=5))
        for i in range(5):
            parts.append(K.sphere(0.009, (c[0] + 0.07 * math.cos(math.radians(200 + i * 35)), c[1], c[2] + 0.07 * math.sin(math.radians(200 + i * 35))),
                                  m["gem"] if i % 2 else m["trim"], 8, 6))
    return parts


# ------------------------------------------------------------------------------------------------------------ shields
def shield(sid, m):
    """Hand-socket convention: handle at the origin, face toward -Y (item_gear.shield)."""
    s = SETS[sid]
    mo = s["motif"]
    shape = SHIELDED[sid]
    if shape == "heater":
        o = [(-0.3, 0.36), (0.3, 0.36), (0.3, 0.12), (0.24, -0.14), (0.12, -0.34), (0.0, -0.44), (-0.12, -0.34), (-0.24, -0.14), (-0.3, 0.12)]
    elif shape == "kite":
        o = [(-0.26, 0.34), (0.0, 0.42), (0.26, 0.34), (0.28, 0.1), (0.16, -0.24), (0.0, -0.56), (-0.16, -0.24), (-0.28, 0.1)]
    elif shape == "tower":
        o = [(x, z) for x, z in M.superellipse(40, 0.3, 0.56, p=5.0)]
    else:
        o = [(0.32 * math.cos(a), 0.32 * math.sin(a)) for a in np.radians(np.linspace(0, 360, 40, endpoint=False))]
    o = M.resample_closed(np.array(o, float), 48)
    k = 0.3 if shape != "round" else 0.0
    V, F = M.plate_from_outline(o, 0.0, rings=6, bulge=0.06 if shape != "round" else 0.1, axis="y")
    face = M.Part(V, F, m["plate"], name="shield_face")
    face.warp(lambda v: (v[0], v[1] + k * v[0] ** 2 - 0.06, v[2]))
    M.recalc_normals(face)
    parts = [M.solidify(face, 0.028, offset=1.0, bevel_w=0.004)]
    rim = [(x, k * x * x - 0.06 - 0.004, z) for x, z in o] + [(o[0][0], k * o[0][0] ** 2 - 0.064, o[0][1])]
    parts.append(K.tube(rim, [(0.018, 0.022)] * len(rim), m["trim"], n=6, up=(0, -1, 0), cap=False, name="rim"))
    # inner border and rivets
    inner = [(x * 0.86, z * 0.86 + (0.0 if shape != "kite" else 0.03)) for x, z in o]
    ib = [(x, k * x * x - 0.06 - 0.06 * 0.6 - 0.006, z) for x, z in inner] + [(inner[0][0], k * inner[0][0] ** 2 - 0.102, inner[0][1])]
    parts.append(K.tube(ib, [0.007] * len(ib), m["trim"], n=5, up=(0, -1, 0), cap=False))
    for i in range(0, 48, 4):
        x, z = o[i]
        parts.append(K.sphere(0.012, (x * 0.93, k * (x * 0.93) ** 2 - 0.085, z * 0.93), m["trim"], 6, 4))
    size = 0.46 if shape != "round" else 0.4
    cz = 0.03 if shape in ("heater", "kite") else 0.0
    parts += xform(emblem(mo, size, m, 0.02), None, (0, -0.16, cz))
    if mo == "dragon":
        for sx in (-1, 1):
            for j in range(3):
                parts.append(K.cone_spike((sx * 0.29, -0.05, 0.34 - j * 0.1), (sx * (0.38 + j * 0.01), -0.04, 0.4 - j * 0.1), 0.022, m["horn"]))
    elif mo == "snow":
        for j in range(8):
            x, z = o[j * 6]
            parts.append(K.crystal((x * 1.05, k * x * x - 0.06, z * 1.05), 0.14, 0.018, m["glow"], rot=(0, -math.degrees(math.atan2(z, x)) + 90, 0)))
    elif mo == "sun":
        for j in range(10):
            a = math.radians(j * 36)
            parts.append(K.cone_spike((0.2 * math.cos(a), -0.13, 0.2 * math.sin(a)), (0.27 * math.cos(a), -0.11, 0.27 * math.sin(a)), 0.014, m["trim"]))
    # back: grip at the origin and an arm strap
    V, F = M.tube([(-0.09, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.09, -0.035, 0.0)], [(0.012, 0.04)] * 4, n=6, up=(0, 0, 1))
    parts.append(M.Part(V, F, m["leather"], name="handle"))
    parts.append(K.box(0.26, 0.012, 0.05, (0, -0.03, 0.18), m["leather"]))
    return parts


# ------------------------------------------------------------------------------------------------------------ build
def swap_bone(b):
    if b is None:
        return None
    return b[:-2] + (".R" if b.endswith(".L") else ".L") if b[-2:] in (".L", ".R") else b


def piece_parts(sid, slot, m):
    if slot == "helm":
        return helm(sid, m)
    if slot == "armor":
        return armor(sid, m)
    if slot == "inner_garment":
        return inner_garment(sid, m)
    if slot == "leggings":
        return legguard(sid, m)
    if slot.startswith("gloves"):
        parts = gauntlet(sid, m)
    elif slot.startswith("boots"):
        parts = greave(sid, m)
    elif slot.startswith("accessory"):
        return jewel(sid, m, slot)
    elif slot == "sub_weapon":
        return shield(sid, m)
    else:
        raise KeyError(slot)
    if slot.endswith("_2"):
        parts = [p.mirrored(False) for p in parts]
        for p in parts:
            p.bone = swap_bone(p.bone)
    return parts


def to_frame(parts, slot):
    """Model space -> the slot's attachment frame (wear() puts it back)."""
    if slot not in FRAMES:
        return parts
    o, R = FRAMES[slot]
    o = np.asarray(o, float)
    for p in parts:
        p.V = (p.V - o) @ np.asarray(R, float)
    return parts


def finish_uv(ob, tile=1.0):
    """legend_kit.finish_mesh: consistent normals + a box-projected UV map (1 UV unit = `tile` m)."""
    import bmesh
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    uv = bm.loops.layers.uv.verify()
    k = 1.0 / tile
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        sgn = 1.0 if n[ax] >= 0 else -1.0
        for lp in f.loops:
            x, y, z = lp.vert.co
            if ax == 0:
                u, v = -sgn * y, z
            elif ax == 1:
                u, v = sgn * x, z
            else:
                u, v = x, sgn * y
            lp[uv].uv = (u * k + 0.13 * ax, v * k + 0.29 * ax)
    bm.to_mesh(me)
    bm.free()
    me.update()


def objects_for(iid, parts, textured=False):
    """One object for the piece and one "AT_<bone>" object per other bone; returns the Blender objects."""
    groups = {}
    for p in parts:
        groups.setdefault(p.bone, []).append(p)
    keys = sorted({p.mat for p in parts})
    mats = K.make_materials(keys)
    if textured:
        texture_materials(mats)
    obs = []
    for bone in sorted(groups, key=lambda b: (b is not None, b or "")):
        name = iid if bone is None else "AT_" + bone.replace(".", "_")
        for p in groups[bone]:
            p.bone = None
            p.wfn = None
        ob = M.build_static(name, groups[bone], mats, sharp_angle=40.0)
        finish_uv(ob)
        obs.append(ob)
    return obs


# the bh-021 texture sets, as MaterialLibrary.LEGEND maps them (base -> set, metres per repeat, normal strength)
LEGEND = {"BH_DragonPlate": ("dragon_scale", 0.3, 1.0), "BH_HolyPlate": ("engraved_plate", 0.8, 0.35),
          "BH_Crimson": ("engraved_plate", 0.3, 0.8), "BH_Gold": ("engraved_plate", 0.45, 0.4),
          "BH_DarkSteel": ("engraved_plate", 0.55, 0.6), "BH_Mail": ("chainmail", 0.22, 1.0),
          "BH_Leather": ("leather_worn", 0.45, 0.8), "BH_Cloth_Primary": ("storm_wool", 0.3, 0.6),
          "BH_Cloth_Secondary": ("storm_wool", 0.3, 0.6), "BH_Horn": ("tyrant_bone", 0.3, 0.8),
          "BH_Bone": ("tyrant_bone", 0.3, 0.8), "BH_Steel": ("engraved_plate", 0.5, 0.5),
          "BH_Silver": ("engraved_plate", 0.4, 0.5)}
TEX_DIR = os.path.join(ROOT, "game", "assets", "textures", "legend")


def texture_materials(mats):
    """For icon renders only: the same texture sets the game lays on these materials (never exported)."""
    import bpy
    for key, mat in mats.items():
        base = K.MAT[key][0]
        if base not in LEGEND or mat.get("bh_tex"):
            continue
        tset, metres, strength = LEGEND[base]
        nt = mat.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0 / metres, 1.0 / metres, 1.0)
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

        def img(kind, color):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = bpy.data.images.load(os.path.join(TEX_DIR, "%s_%s.png" % (tset, kind)), check_existing=True)
            n.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
            nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
            return n
        alb = img("albedo", True)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs[6].default_value = bsdf.inputs["Base Color"].default_value
        nt.links.new(alb.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        nrm = img("normal", False)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = strength
        nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        rough = img("rough", False)
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = min(1.0, max(0.2, bsdf.inputs["Roughness"].default_value / 0.45))
        nt.links.new(rough.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs[0], bsdf.inputs["Roughness"])
        mat["bh_tex"] = True


def items_for(sids):
    out = []
    for sid in sids:
        slots = list(SLOTS) + (["sub_weapon"] if sid in SHIELDED else [])
        for slot in slots:
            out.append((sid, slot, "boss_%s_%s" % (sid, slot)))
    return out


def _export(path, obs):
    """export_glb with retries: an open Godot editor re-imports each new GLB and can hold the file for a moment."""
    import time
    sys.path.insert(0, K.CHARS)
    from build import export_glb
    for attempt in range(8):
        try:
            export_glb(path, obs, animations=False)
            return
        except Exception as e:  # noqa: BLE001
            print("[regalia] retry %s (%s)" % (os.path.basename(path), str(e).splitlines()[-1][:80]))
            time.sleep(1.5 + attempt)
    raise RuntimeError("could not write " + path)


def export_models(sids, log=print):
    sys.path.insert(0, K.CHARS)
    from build import reset
    report = []
    only = [x for x in os.environ.get("BH_REGALIA_SLOTS", "").split(",") if x]
    for sid, slot, iid in items_for(sids):
        if only and slot not in only:
            continue
        reset()
        m = palette(sid)
        parts = piece_parts(sid, slot, m)
        parts = to_frame(parts, slot)
        obs = objects_for(iid, parts)
        path = os.path.join(ROOT, "game", "assets", "items", iid + ".glb")
        _export(path, obs)
        tris = sum(M.tri_count(o) for o in obs)
        report.append({"id": iid, "tris": tris, "objects": [o.name for o in obs]})
        log("[regalia] %-44s %6d tris  %s" % (iid, tris, ",".join(o.name for o in obs[1:])))
    # the signature weapons (boss_weapons designs) with the same UV map, so the game can texture them too
    import boss_weapons as BW
    for sid in (sids if not only or "main_weapon" in only else []):
        iid = "boss_%s_main_weapon" % sid
        reset()
        fn, theme = BW.SPECS[iid]
        obs = objects_for(iid, fn(theme))
        _export(os.path.join(ROOT, "game", "assets", "items", iid + ".glb"), obs)
        log("[regalia] %-44s %6d tris" % (iid, sum(M.tri_count(o) for o in obs)))
    return report


# ------------------------------------------------------------------------------------------------------------ icons
ICON_VIEW = {  # slot -> (pitch, yaw, rotation applied to the model-space piece)
    "helm": (10.0, 28.0, None), "armor": (6.0, 20.0, None), "inner_garment": (10.0, 20.0, None), "leggings": (8.0, 24.0, None),
    "gloves_1": (18.0, 0.0, Ry(-32)), "gloves_2": (18.0, 0.0, Ry(32)),
    "boots_1": (12.0, 30.0, None), "boots_2": (12.0, -30.0, None),
    "accessory_1": (40.0, 24.0, None), "accessory_2": (40.0, -24.0, None), "accessory_3": (8.0, 12.0, None),
    "accessory_4": (8.0, -14.0, None), "sub_weapon": (10.0, 0.0, Rz(8) @ Ry(-12)), "main_weapon": (8.0, 0.0, None),
}


def render_icons(sids, raw_dir, weapons=True, log=print):
    import bpy
    from mathutils import Vector
    sys.path.insert(0, K.CHARS)
    from build import reset
    import build_items as B
    os.makedirs(raw_dir, exist_ok=True)
    todo = items_for(sids)
    only = [x for x in os.environ.get("BH_REGALIA_SLOTS", "").split(",") if x]
    if only:
        todo = [t for t in todo if t[1] in only]
        weapons = weapons and "main_weapon" in only
    if weapons:
        todo += [(sid, "main_weapon", "boss_%s_main_weapon" % sid) for sid in sids]
    for sid, slot, iid in todo:
        reset()
        if slot == "main_weapon":
            import boss_weapons as BW
            fn, theme = BW.SPECS[iid]
            parts = fn(theme)
            for p in parts:
                p.bone = None
        else:
            m = palette(sid)
            parts = piece_parts(sid, slot, m)
            if slot == "armor":   # the icon shows the armour itself, not the cloak behind it
                parts = [p for p in parts if p.name not in ("cape", "scarf")]
        pitch, yaw, R = ICON_VIEW[slot]
        if R is not None:
            c = np.mean(np.vstack([p.V for p in parts]), 0)
            for p in parts:
                p.rot(R, c)
        obs = objects_for(iid, parts, textured=True)
        cam = B._studio(256)
        if slot == "main_weapon":
            wt = next(t[5] for t in BW.THEMES if t[0] == sid)
            pitch, yaw = B._pose_for({"category": "weapon", "weapon_type": wt, "id": iid}, obs[0])
        bpy.context.view_layer.update()
        pts = [o.matrix_world @ Vector(cc) for o in obs for cc in o.bound_box]
        c = sum(pts, Vector()) / len(pts)
        for o in obs:
            o.location -= c
        bpy.context.view_layer.update()
        p_, y_ = math.radians(pitch), math.radians(yaw)
        d = Vector((math.sin(y_) * math.cos(p_), -math.cos(y_) * math.cos(p_), math.sin(p_)))
        cam.location = d * 10.0
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        q = [inv @ (o.matrix_world @ Vector(cc)) for o in obs for cc in o.bound_box]
        ext = max(max(v.x for v in q) - min(v.x for v in q), max(v.y for v in q) - min(v.y for v in q))
        cam.data.ortho_scale = ext * 1.1
        cx = (max(v.x for v in q) + min(v.x for v in q)) / 2
        cy = (max(v.y for v in q) + min(v.y for v in q)) / 2
        cam.location = cam.matrix_world @ Vector((cx, cy, 0.0))
        cam.data.clip_start = 0.01
        cam.data.clip_end = 100
        bpy.context.scene.render.filepath = os.path.join(raw_dir, iid + ".png")
        bpy.ops.render.render(write_still=True)
        log("[icon] %s" % iid)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    targets = [a for a in argv if a in ("models", "icons")] or ["models"]
    sids = [a for a in argv if a in SETS] or ORDER
    raw = os.environ.get("BH_REGALIA_RAW", os.path.join(ROOT, "work", "lemondev", "bh-022", "scratch", "icons_raw"))
    if "models" in targets:
        export_models(sids)
    if "icons" in targets:
        render_icons(sids, raw, weapons="noweapons" not in argv)
    print("[regalia] done", len(sids), "sets")


if __name__ == "__main__":
    main()
