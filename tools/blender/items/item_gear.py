"""Armour, shields and jewellery models (bh-006).

Conventions (Blender space, Z up; Godot receives +Y up):
  shields   hand-socket convention like bh_weapons.shield: handle at the origin, face toward -Y, Z up
  helms     upright on the rim, opening down, face toward -Y
  chest / inner garments / gloves   upright, front toward -Y (the game lays them flat when dropped)
  amulets / charms   laid flat, front facing up (+Z), bottom at z = 0
  boots     standing on the sole, toe toward -Y
  rings     standing upright on the band, stone on top
"""
import math
import os
import sys

import numpy as np

import item_kit as K
from item_kit import M, Rx, Ry, Rz

sys.path.insert(0, K.CHARS)
import bh_weapons as W  # noqa: E402


def _lay_flat(parts):
    """Upright (front -Y, up +Z) -> lying on its back (front +Z), resting on z = 0."""
    for p in parts:
        p.rot(Rx(-90))
    zmin = min(p.V[:, 2].min() for p in parts)
    for p in parts:
        p.move((0, 0, -zmin))
    return parts


def _ground(parts):
    zmin = min(p.V[:, 2].min() for p in parts)
    for p in parts:
        p.move((0, 0, -zmin))
    return parts


# ---- shields -------------------------------------------------------------------------------------------------------

def _curve_face(v, k=0.35, off=-0.06):
    return (v[0], v[1] + k * v[0] ** 2 + off, v[2])


def shield(s):
    shape = s.get("shape", "heater")
    face_m = s.get("face", "crimson")
    body_m = s.get("body", "wood")
    rim_m = s.get("rim", "steel")
    parts = []
    if shape == "heater":
        o = W.shield_outline(w=s.get("w", 0.64), top=s.get("top", 0.4), bottom=s.get("bottom", -0.5))
    elif shape == "round":
        r = s.get("r", 0.26)
        o = np.array([(r * math.cos(a), r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40, endpoint=False)])
    else:  # tower
        o = np.array(K.M.superellipse(48, s.get("w", 0.34), s.get("h", 0.62), p=5.0))
        o[:, 1] += 0.06
    k = s.get("curve", 0.35 if shape != "round" else 0.0)
    V, F = M.plate_from_outline(o, 0.0, rings=6, bulge=s.get("bulge", 0.05 if shape != "round" else 0.09), axis="y")
    face = M.Part(V, F, face_m, name="shield_face")
    face.warp(lambda v: _curve_face(v, k))
    body = M.solidify(face.copy().to(mat=body_m).move((0, 0.002, 0)), 0.022, offset=-1.0)
    parts.append(body)
    parts.append(face.scale((0.975, 1, 0.975), center=(0, 0, float(o[:, 1].mean()))))
    rim_pts = [(x, k * x * x - 0.06 - 0.005, z) for x, z in o]
    rim_pts.append(rim_pts[0])
    V, F = M.tube(rim_pts, [(0.016, 0.018)] * len(rim_pts), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(M.Part(V, F, rim_m, name="rim"))
    em = s.get("emblem")
    if em == "order":
        for p in W.emblem_parts(s.get("emblem_scale", 1.0), mat=s.get("emblem_mat", "gold")):
            p.warp(lambda v: (v[0], v[1] + k * v[0] ** 2 - 0.06 - 0.05 * (1 - min((v[0] ** 2 / 0.1 + v[2] ** 2 / 0.2), 1.5) / 1.5) - 0.006, v[2]))
            parts.append(M.bevel(p, 0.0015, 1))
    elif em == "boss":
        parts.append(K.sphere(0.07, (0, -0.06 - 0.09 * 0.9, 0.0), s.get("emblem_mat", "steel"), 16, 8, scale=(1, 0.6, 1)))
        for a in np.linspace(0, 2 * math.pi, 8, endpoint=False):
            x, z = 0.19 * math.cos(a), 0.19 * math.sin(a)
            parts.append(K.sphere(0.012, (x, -0.06 - 0.09 * (1 - (x * x + z * z) / 0.07) - 0.004, z), s.get("rivet", "gold"), 6, 4))
    elif em == "sigil":
        parts.append(K.ring_tube((0, -0.16, 0.0), 0.12, 0.008, s.get("emblem_mat", "gold"), axis="y", n=32))
        parts.append(K.gem((0, -0.17, 0.0), 0.035, s.get("gem", "sapphire"), rot=(90, 0, 0)))
        for a in range(4):
            aa = math.radians(45 + 90 * a)
            parts.append(K.cone_spike((0.13 * math.cos(aa), -0.155, 0.13 * math.sin(aa)), (0.2 * math.cos(aa), -0.14, 0.2 * math.sin(aa)), 0.012,
                                      s.get("emblem_mat", "gold")))
    elif em == "tower":
        for z in (0.45, -0.3):
            parts.append(K.box(0.62, 0.02, 0.04, (0, -0.06 - 0.02, z), s.get("emblem_mat", "iron"), 0.004).warp(lambda v: _curve_face(v, k, -0.085)))
        parts.append(K.box(0.04, 0.02, 1.1, (0, -0.1, 0.06), s.get("emblem_mat", "iron"), 0.004))
        for x in (-0.28, 0.28):
            for z in (0.45, -0.3):
                parts.append(K.sphere(0.014, (x, k * x * x - 0.11, z), s.get("rivet", "gold"), 6, 4))
    elif em == "aegis":
        for p in W.emblem_parts(1.0, mat="gold"):
            p.warp(lambda v: (v[0], v[1] + k * v[0] ** 2 - 0.06 - 0.05 * (1 - min((v[0] ** 2 / 0.1 + v[2] ** 2 / 0.2), 1.5) / 1.5) - 0.006, v[2]))
            parts.append(M.bevel(p, 0.0015, 1))
        parts.append(K.crystal((0, -0.13, 0.03), 0.09, 0.03, "aether", rot=(90, 0, 0)))
        for sx in (1, -1):
            parts.append(K.crystal((sx * 0.36, -0.02, 0.36), 0.1, 0.018, "aether", rot=(0, sx * 25, 0)))
    # back: handle at the origin + strap
    V, F = M.tube([(-0.09, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.09, -0.035, 0.0)], [(0.012, 0.04)] * 4, n=6, up=(0, 0, 1))
    parts.append(M.Part(V, F, "leather", name="handle"))
    parts.append(K.box(0.26, 0.012, 0.05, (0, -0.03, 0.18), "leather"))
    return parts


# ---- helms ---------------------------------------------------------------------------------------------------------

def _dome(r, h, z0, mat, pointed=0.0, n=20, flat_top=False):
    prof = []
    for i in range(10):
        t = i / 9
        a = t * math.pi / 2
        rr = r * math.cos(a) if not flat_top else r * (1.0 if t < 0.8 else math.cos((t - 0.8) / 0.2 * math.pi / 2))
        zz = z0 + h * math.sin(a) + pointed * t ** 6
        prof.append((max(rr, 0.0) if i < 9 else 0.0, zz))
    prof = [(r * 1.0, z0 - 0.002)] + prof
    return K.lathe(prof, mat, n, "dome")


def helm(s):
    kind = s.get("kind", "kettle")
    m = s.get("mat", "steel")
    parts = []
    R = 0.13
    if kind in ("kettle", "bascinet", "barbute", "winged"):
        pointed = 0.08 if kind == "bascinet" else 0.0
        parts.append(_dome(R, 0.17, 0.08, m, pointed))
        # lower shell (cheeks / neck)
        parts.append(K.lathe([(R * 1.02, 0.0), (R * 1.04, 0.02), (R * 1.02, 0.08), (R * 0.98, 0.085), (R * 0.96, 0.02), (R * 0.97, 0.0)], m, 20))
        parts.append(K.lathe([(R * 1.0, 0.0), (R * 0.93, 0.0), (R * 0.93, 0.06), (0, 0.06)], "black", 14).scale((0.98, 0.98, 1)))
        if kind == "kettle":
            parts.append(K.lathe([(R * 1.02, 0.07), (R * 1.7, 0.03), (R * 1.75, 0.035), (R * 1.03, 0.085)], m, 24, "brim"))
        if kind == "barbute":
            parts.append(K.box(0.03, 0.02, 0.13, (0, -R * 1.02, 0.07), "black"))
            parts.append(K.box(0.12, 0.02, 0.025, (0, -R * 1.02, 0.14), "black"))
            parts.append(K.lathe([(0.006, 0.08), (0.012, 0.25), (0.0, 0.28)], s.get("trim", "bronze"), 8).scale((0.4, 3.5, 1), (0, 0, 0.2)))
        if kind == "bascinet":
            # snouted visor
            V, F = M.lathe([(0, -0.04), (0.055, 0.0), (0.075, 0.06), (0.06, 0.12), (0, 0.14)], 12)
            vis = M.Part(V, F, m, name="visor").rot(Rx(90)).scale((1.3, 1, 1.0)).move((0, -R * 0.9, 0.12))
            parts.append(vis)
            for z in (0.12, 0.145):
                parts.append(K.box(0.07, 0.02, 0.006, (0, -R * 0.9 - 0.13, z), "black"))
        if kind == "winged":
            for sx in (1, -1):
                o = [(0.0, 0.0), (0.09, 0.05), (0.2, 0.16), (0.16, 0.08), (0.2, 0.06), (0.14, 0.02), (0.16, -0.01), (0.07, -0.02)]
                wing = K.slab([(sx * x, z) for x, z in o], 0.012, s.get("trim", "gold"), axis="x").rot(Rz(sx * 20))
                parts.append(M.bevel(wing.move((sx * R * 0.95, 0.02, 0.16)), 0.002, 1))
            parts.append(K.crystal((0, -R * 1.0, 0.22), 0.07, 0.022, "aether", rot=(90, 0, 0)))
        # nasal / crest / rivets
        if kind in ("kettle",):
            parts.append(K.box(0.02, 0.012, 0.09, (0, -R * 1.02, 0.1), s.get("trim", "iron")))
        for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
            parts.append(K.sphere(0.006, (R * 1.05 * math.cos(a), R * 1.05 * math.sin(a), 0.04), s.get("trim", "bronze"), 5, 3))
    elif kind == "greathelm":
        parts.append(K.lathe([(0.0, 0.0), (R * 1.05, 0.0), (R * 1.08, 0.12), (R * 1.04, 0.25), (R * 0.85, 0.3), (0, 0.31)], m, 20, "greathelm"))
        for z in (0.17, 0.19):
            parts.append(K.box(0.18, 0.02, 0.012, (0, -R * 1.06, z), "black"))
        for i in range(5):
            parts.append(K.box(0.008, 0.02, 0.04, (-0.04 + 0.02 * i, -R * 1.06, 0.07), "black"))
        parts.append(K.box(0.012, 0.03, 0.29, (0, -R * 1.08, 0.14), s.get("trim", "gold")))
        parts.append(K.ring_tube((0, 0, 0.26), R * 1.0, 0.006, s.get("trim", "gold"), axis="z", n=24))
    return _ground(parts)


def hood(s):
    """A rounded cowl: a head-shaped shell with a soft backward peak, a deep shadowed face opening, a shoulder mantle."""
    m = s.get("mat", "wool")
    parts = []
    rings = []
    peak = s.get("peak", 1.0)
    for i in range(14):
        t = i / 13
        z = 0.03 + 0.26 * t
        round_top = math.cos(t * math.pi / 2) ** 0.55
        rx = 0.13 * round_top + 0.004
        ry = 0.145 * round_top + 0.004
        back = 0.03 * peak * t ** 3          # soft fold of cloth toward the back
        ring = [(rx * math.cos(a), ry * math.sin(a) + back, z) for a in np.linspace(0, 2 * math.pi, 22, endpoint=False)]
        rings.append(np.array(ring))
    V, F = M.loft(rings)
    parts.append(M.Part(V, F, m, name="hood"))
    if peak > 1.2:   # a drooping point behind the head
        parts.append(K.tube([(0, 0.06, 0.26), (0, 0.13, 0.25), (0, 0.19, 0.2)], [0.045, 0.025, 0.004], m, n=10, up=(1, 0, 0)))
    # face opening: a shadowed recess framed by the cloth edge
    parts.append(K.sphere(0.07, (0, -0.118, 0.14), "black", 14, 10, scale=(1.0, 0.3, 1.25)))
    parts.append(K.ring_tube((0, -0.12, 0.14), 1.0, 0.012, s.get("trim", m), axis="y", n=26).scale((0.074, 1, 0.092), (0, -0.12, 0.14)))
    # mantle over the shoulders
    parts.append(K.lathe([(0.22, 0.0), (0.225, 0.012), (0.19, 0.05), (0.14, 0.075), (0.11, 0.06), (0.14, 0.0)], m, 24, "mantle").scale((1, 0.85, 1)))
    if s.get("trim"):
        parts.append(K.ring_tube((0, 0, 0.004), 1.0, 0.008, s["trim"], axis="z", n=30).scale((0.225, 0.19, 1), (0, 0, 0.004)))
    if s.get("gem"):
        parts.append(K.gem((0, -0.14, 0.26), 0.014, s["gem"], rot=(90, 0, 0)))
    if s.get("stars"):
        for i in range(9):
            a = i * 0.7
            parts.append(K.gem((0.13 * math.cos(a) * (1 - 0.05 * i), 0.13 * math.sin(a), 0.06 + 0.024 * i), 0.006, s["stars"]))
    return _ground(parts)


def circlet(s):
    """Seer's circlet: a thin crowned band with a brow gem and a veil falling behind."""
    mt = s.get("metal", "silver")
    parts = [K.ring_tube((0, 0, 0.03), 1.0, 0.006, mt, axis="z", n=32).scale((0.095, 0.11, 1), (0, 0, 0.03))]
    for k in range(7):
        a = math.radians(-90 + (k - 3) * 22)
        x, y = 0.095 * math.cos(a), 0.11 * math.sin(a)
        h = 0.035 - 0.008 * abs(k - 3)
        parts.append(K.cone_spike((x, y, 0.032), (x * 1.03, y * 1.03, 0.032 + h), 0.006, mt))
    parts.append(K.gem((0, -0.115, 0.045), 0.016, s.get("gem", "amethyst"), rot=(90, 0, 0)))
    parts.append(K.ring_tube((0, -0.112, 0.045), 0.018, 0.0025, mt, axis="y", n=16))
    # veil: a soft sheet hanging from the back half of the band
    rows = []
    for i in range(7):
        t = i / 6
        z = 0.03 - 0.16 * t
        pts = []
        for j in range(12):
            a = math.radians(-10 + 200 * j / 11)
            r = 1.0 + 0.35 * t
            pts.append((0.095 * r * math.cos(a), 0.11 * r * math.sin(a) + 0.02 * t, z + 0.008 * math.sin(j * 1.3 + t * 3)))
        rows.append(pts)
    V, F = M.grid(lambda u, v: np.array(rows[min(int(round(v * 6)), 6)][min(int(round(u * 11)), 11)]), 12, 7)
    veil = M.solidify(M.Part(V, F, s.get("veil", "silk"), name="veil"), 0.003, offset=0.0)
    parts.append(veil)
    return _ground(parts)


# ---- body armour --------------------------------------------------------------------------------------------------

def _torso(z0, z1, waist, chest, depth, mat, n=20, flare=0.0, name="torso"):
    rings = []
    for i in range(10):
        t = i / 9
        z = z0 + (z1 - z0) * t
        w = waist + (chest - waist) * math.sin(t * math.pi / 2) ** 1.3 - flare * (1 - t) ** 2
        w = max(w, 0.05)
        d = depth * (0.85 + 0.15 * math.sin(t * math.pi))
        if t > 0.85:
            w *= 1.0 - (t - 0.85) * 1.6
            d *= 1.0 - (t - 0.85) * 1.2
        # chest bulges forward (-Y), flatter back
        rings.append(np.array([(w * math.cos(a), d * math.sin(a) * (1.25 if math.sin(a) < 0 else 0.85), z)
                               for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]))
    V, F = M.loft(rings)
    return M.Part(V, F, mat, name=name)


def chest(s):
    kind = s.get("kind", "plate")
    m = s.get("mat", "steel")
    parts = []
    if kind in ("plate", "mail", "brigandine", "gambeson", "chain", "vest", "shirt"):
        chest_w = 0.2 if kind not in ("shirt", "vest") else 0.18
        parts.append(_torso(0.0, 0.52, 0.15, chest_w, 0.12, m))
        parts.append(K.lathe([(0.075, 0.5), (0.085, 0.51), (0.07, 0.54), (0.0, 0.54)], s.get("trim", m), 16).scale((1, 0.8, 1)))
        if kind == "plate":
            # breastplate ridge, pauldrons, fauld plates
            parts.append(K.box(0.012, 0.02, 0.36, (0, -0.125, 0.25), s.get("trim", "bright"), 0.005))
            for sx in (1, -1):
                parts.append(K.sphere(0.09, (sx * 0.2, 0, 0.46), m, 14, 8, scale=(1.05, 1.0, 0.75)))
                parts.append(K.sphere(0.092, (sx * 0.2, 0, 0.43), s.get("trim", "gold"), 14, 8, scale=(1.08, 1.03, 0.25)))
            for i in range(3):
                parts.append(K.lathe([(0.165 + 0.012 * i, -0.02 - 0.05 * i), (0.175 + 0.012 * i, 0.03 - 0.05 * i), (0.16, 0.035 - 0.05 * i)], m, 20).scale((1, 0.78, 1)))
        elif kind == "mail":
            for i in range(9):
                parts.append(K.ring_tube((0, 0, 0.03 + i * 0.055), 1.0, 0.004, "darksteel", axis="z", n=26).scale((0.16 + 0.004 * i, 0.125, 1), (0, 0, 0.03 + i * 0.055)))
            for sx in (1, -1):
                parts.append(K.tube([(sx * 0.18, 0, 0.44), (sx * 0.26, 0, 0.36), (sx * 0.3, 0, 0.24)], [0.05, 0.045, 0.04], m, n=10))
        elif kind in ("brigandine", "vest"):
            for i in range(6):
                for j in range(7):
                    a = -math.pi / 2 + (j - 3) * 0.28
                    z = 0.06 + i * 0.075
                    w = 0.17 + 0.03 * math.sin(i / 5 * math.pi / 2)
                    parts.append(K.sphere(0.008, (w * math.cos(a), 0.125 * math.sin(a) * 1.02 - 0.004, z), s.get("rivet", "gold"), 5, 3))
            parts.append(K.lathe([(0.16, 0.08), (0.165, 0.09), (0.165, 0.12), (0.16, 0.13)], "leather", 20).scale((1, 0.8, 1)))
        elif kind in ("gambeson", "chain", "shirt"):
            for i in range(1, 9):
                z = i * 0.058
                t = z / 0.52
                w = 0.15 + 0.05 * math.sin(t * math.pi / 2) ** 1.3
                parts.append(K.ring_tube((0, 0, z), 1.0, 0.006 if kind == "gambeson" else 0.003, s.get("trim", m), axis="z", n=26).scale((w + 0.004, 0.122, 1), (0, 0, z)))
            if kind != "shirt":
                for sx in (1, -1):
                    parts.append(K.tube([(sx * 0.17, 0, 0.45), (sx * 0.25, 0, 0.38), (sx * 0.28, 0, 0.3)], [0.045, 0.04, 0.035], m, n=10))
            else:
                for sx in (1, -1):
                    parts.append(K.tube([(sx * 0.16, 0, 0.45), (sx * 0.28, 0, 0.36), (sx * 0.34, 0, 0.18)], [0.045, 0.038, 0.032], m, n=10))
        if s.get("belt"):
            parts.append(K.lathe([(0.152, 0.05), (0.158, 0.055), (0.158, 0.085), (0.152, 0.09)], s["belt"], 20).scale((1, 0.82, 1)))
            parts.append(K.box(0.04, 0.02, 0.04, (0, -0.13, 0.07), "gold", 0.004))
        if s.get("glow"):
            parts.append(K.gem((0, -0.14, 0.34), 0.02, s["glow"], rot=(90, 0, 0)))
            parts += [K.ring_tube((0, -0.13, 0.34), 0.035, 0.004, "gold", axis="y", n=18)]
        if s.get("runes"):
            for i in range(5):
                parts.append(K.box(0.012, 0.01, 0.03, (-0.06 + i * 0.03, -0.125, 0.2 + 0.02 * (i % 2)), s["runes"]))
    else:  # robe / coat: long garment with sleeves and a flared hem
        L = s.get("len", 0.9)
        parts.append(_torso(0.0, L, 0.24, 0.19, 0.13, m, flare=0.0))
        rings = []
        for i in range(8):
            t = i / 7
            z = t * L * 0.55
            w = 0.3 - 0.12 * t
            rings.append(np.array([(w * math.cos(a), 0.15 * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, 22, endpoint=False)]))
        V, F = M.loft(rings)
        parts.append(M.Part(V, F, m, name="skirt"))
        for sx in (1, -1):
            parts.append(K.tube([(sx * 0.17, 0, L - 0.08), (sx * 0.3, 0, L - 0.2), (sx * 0.36, 0, L - 0.45), (sx * 0.38, 0, L - 0.52)],
                                [0.05, 0.055, 0.07, 0.08], m, n=12))
            parts.append(K.ring_tube((sx * 0.38, 0, L - 0.52), 0.08, 0.008, s.get("trim", "gold"), axis="z", n=18))
        # front trim and collar
        parts.append(K.box(0.03, 0.02, L * 0.95, (0, -0.15, L * 0.47), s.get("trim", "gold"), 0.004))
        parts.append(K.lathe([(0.08, L - 0.03), (0.1, L - 0.01), (0.09, L + 0.04), (0.0, L + 0.04)], s.get("trim", "gold"), 16).scale((1, 0.8, 1)))
        parts.append(K.ring_tube((0, 0, 0.012), 1.0, 0.01, s.get("trim", "gold"), axis="z", n=28).scale((0.3, 0.15, 1), (0, 0, 0.012)))
        if s.get("belt"):
            parts.append(K.lathe([(0.2, L * 0.55), (0.205, L * 0.555), (0.205, L * 0.6), (0.2, L * 0.605)], s["belt"], 22).scale((1, 0.68, 1)))
        if s.get("stars"):
            for i in range(10):
                a = -math.pi / 2 + (i - 5) * 0.2
                z = 0.08 + (i * 0.37 % 1.0) * L * 0.8
                w = 0.25 - 0.1 * z / L
                parts.append(K.gem((w * math.cos(a), 0.15 * math.sin(a) - 0.005, z), 0.008, s["stars"]))
        if s.get("glow"):
            parts.append(K.gem((0, -0.17, L * 0.8), 0.016, s["glow"], rot=(90, 0, 0)))
    # authored upright (front -Y); the game lays chest pieces flat on the ground (ItemModels.ground_instance)
    return _ground(parts)


# ---- gloves and boots ------------------------------------------------------------------------------------------------

def glove(s):
    m = s.get("mat", "leather")
    plate = s.get("plate")
    parts = []
    # hand (fingers along +Z, back of the hand toward -Y): wrist -> palm -> knuckles
    rings = []
    for z, w, d in ((-0.005, 0.034, 0.024), (0.03, 0.046, 0.024), (0.06, 0.05, 0.022), (0.092, 0.047, 0.019)):
        rings.append(np.array([(w * math.cos(a), d * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]))
    V, F = M.loft(rings)
    parts.append(M.Part(V, F, m, name="hand"))
    for i in range(4):
        x = -0.03 + 0.02 * i
        L = [0.075, 0.085, 0.08, 0.065][i]
        parts.append(K.tube([(x, 0, 0.09), (x, -0.004, 0.09 + L * 0.5), (x, 0.004, 0.09 + L)], [0.0095, 0.009, 0.008], m, n=8))
        if plate:
            for k in range(3):
                parts.append(K.sphere(0.011, (x, -0.008, 0.1 + L * 0.3 * k), plate, 8, 5, scale=(1.0, 0.6, 1.0)))
    parts.append(K.tube([(0.045, 0, 0.03), (0.07, -0.005, 0.07), (0.08, 0, 0.1)], [0.012, 0.01, 0.009], m, n=8))
    # cuff
    cuff_m = s.get("cuff", plate or m)
    parts.append(K.lathe([(0.0, -0.1), (0.058, -0.1), (0.056, -0.06), (0.04, 0.0), (0.0, 0.005)], cuff_m, 16, "cuff").scale((1.0, 0.72, 1.0)))
    if plate:
        parts.append(K.sphere(0.05, (0, -0.014, 0.05), plate, 12, 8, scale=(1.0, 0.35, 0.95)))
        for z in (-0.07, -0.03):
            parts.append(K.ring_tube((0, 0, z), 0.06, 0.004, s.get("trim", "gold"), axis="z", n=18).scale((1, 0.72, 1), (0, 0, z)))
    if s.get("spikes"):
        for i in range(4):
            parts.append(K.cone_spike((-0.03 + 0.02 * i, -0.02, 0.09), (-0.03 + 0.02 * i, -0.05, 0.1), 0.006, s["spikes"]))
    if s.get("runes"):
        parts.append(K.gem((0, -0.028, 0.05), 0.012, s["runes"], rot=(90, 0, 0)))
    parts.append(K.ring_tube((0, 0, -0.1), 0.056, 0.004, s.get("trim", "gold"), axis="z", n=18).scale((1, 0.72, 1), (0, 0, -0.1)))
    # upright, fingers up, back of the hand toward -Y; the game lays gloves flat on the ground
    return _ground(parts)


def boot(s):
    m = s.get("mat", "leather")
    parts = []
    H = s.get("h", 0.3)
    # shaft
    parts.append(K.lathe([(0.0, 0.05), (0.055, 0.05), (0.058, H * 0.5), (0.062 + s.get("flare", 0.0), H), (0.052, H), (0.0, H * 0.98)], m, 16, "shaft").scale((1, 1.1, 1)))
    # foot (toe toward -Y)
    rings = []
    for i in range(9):
        t = i / 8
        y = 0.04 - 0.24 * t
        w = 0.05 * (1 - 0.35 * t ** 2) + 0.01
        h = 0.09 * (1 - 0.6 * t)
        rings.append(np.array([(w * math.cos(a), y, h * 0.5 + h * 0.5 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]))
    # loft along -Y: reorder so the ring normal runs along the path
    V, F = M.loft(rings)
    foot = M.Part(V, F, m, name="foot").flip()
    parts.append(foot)
    parts.append(K.box(0.12, 0.3, 0.02, (0, -0.075, 0.01), s.get("sole", "darkleather"), 0.008))
    plate = s.get("plate")
    if plate:
        for i in range(4):
            parts.append(K.sphere(0.06 - i * 0.004, (0, -0.06 - 0.045 * i, 0.07 - 0.01 * i), plate, 12, 6, scale=(1.0, 0.8, 0.45)))
        parts.append(K.sphere(0.065, (0, -0.03, H * 0.62), plate, 12, 8, scale=(1.0, 0.55, 1.6)))
        parts.append(K.sphere(0.03, (0, -0.058, 0.13), plate, 10, 6))
    if s.get("cuff"):
        parts.append(K.lathe([(0.058, H - 0.05), (0.075, H - 0.03), (0.078, H + 0.01), (0.056, H + 0.01)], s["cuff"], 18).scale((1, 1.1, 1)))
    if s.get("straps"):
        for z in (0.12, 0.2):
            parts.append(K.ring_tube((0, 0, z), 0.06, 0.006, s["straps"], axis="z", n=18).scale((1, 1.1, 1), (0, 0, z)))
            parts.append(K.box(0.02, 0.012, 0.02, (0.06, -0.02, z), "gold", 0.003))
    if s.get("wings"):
        for sx in (1, -1):
            o = [(0.0, 0.0), (0.06, 0.06), (0.05, 0.02), (0.08, 0.03), (0.04, -0.01)]
            parts.append(K.slab([(sx * x, z) for x, z in o], 0.006, s["wings"], axis="x").move((sx * 0.06, 0.02, H * 0.7)))
    if s.get("glow"):
        parts.append(K.gem((0, -0.07, H * 0.62), 0.014, s["glow"], rot=(90, 0, 0)))
    return _ground(parts)


# ---- leggings (bh-024) ---------------------------------------------------------------------------------------------
# Upright like the chest pieces (waist on top, front -Y); the game lays them flat on the ground. Authored at the hero's
# own size (waist 0.95 m above the ankles) and scaled to sit with the other armour models.
LEG_Z = 0.95


def _leg_line(L, loose=0.0, flare=0.0):
    """(points, radii) down the LEFT leg: hip, thigh, above the knee, knee, calf, ankle."""
    zs = [L - 0.1, L - 0.28, L - 0.42, L - 0.49, L - 0.64, 0.07]
    xs = [0.092, 0.1, 0.1, 0.097, 0.095, 0.09]
    ys = [0.0, -0.004, -0.006, -0.006, 0.006, 0.002]
    rr = [(0.09, 0.092), (0.08, 0.083), (0.066, 0.068), (0.059, 0.061), (0.06, 0.065), (0.046, 0.05)]
    out = []
    for i, (rx, ry) in enumerate(rr):
        t = i / (len(rr) - 1)
        g = 1.0 + loose * (0.4 + 0.6 * t) + flare * t ** 3
        out.append((rx * g, ry * g))
    return [(x, y, z) for x, y, z in zip(xs, ys, zs)], out


def _on_leg(L, t, loose=0.0):
    """Centre and radii of the left leg at t (0 hip .. 1 ankle), by linear interpolation of _leg_line."""
    pts, rad = _leg_line(L, loose)
    zs = [p[2] for p in pts]
    z = zs[0] + (zs[-1] - zs[0]) * t
    for i in range(len(zs) - 1):
        if zs[i] >= z >= zs[i + 1]:
            k = (zs[i] - z) / max(zs[i] - zs[i + 1], 1e-9)
            c = tuple(pts[i][j] + (pts[i + 1][j] - pts[i][j]) * k for j in range(3))
            r = (rad[i][0] + (rad[i + 1][0] - rad[i][0]) * k, rad[i][1] + (rad[i + 1][1] - rad[i][1]) * k)
            return c, r
    return pts[-1], rad[-1]


def _ellipse_ring(z, w, d, n=24, cx=0.0, cy=0.0):
    return np.array([(cx + w * math.cos(a), cy + d * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)])


def _mirror(parts):
    out = []
    for p in parts:
        q = p.copy()
        q.V = q.V * np.array([-1.0, 1.0, 1.0])
        q.F = [tuple(reversed(f)) for f in q.F]
        out.append(q)
    return out


def _leg_band(L, t, mat, grow=0.006, tube=0.005, loose=0.0, tilt=0.0):
    (x, y, z), (rx, ry) = _on_leg(L, t, loose)
    b = K.ring_tube((x, y, z), 1.0, tube, mat, axis="z", n=16).scale((rx + grow, ry + grow, 1), (x, y, z))
    if tilt:
        b.rot(Rx(tilt), (x, y, z))
    return b


def legs(s):
    kind = s.get("kind", "trousers")
    if kind == "plate" and "plate" not in s:          # depth specs name the plate colour as the main material
        s = dict(s, plate=s.get("mat", "iron"), mat="darkleather")
    m = s.get("mat", "wool")
    trim = s.get("trim", "gold")
    L = LEG_Z
    loose = s.get("loose", 0.0)
    lower = s.get("hose")                 # breeches: a different cloth below the knee
    parts, left = [], []
    # the seat: waist to crotch
    rings = [_ellipse_ring(L, 0.165, 0.112), _ellipse_ring(L - 0.08, 0.178, 0.12), _ellipse_ring(L - 0.17, 0.182, 0.12)]
    V, F = M.loft(rings, cap0=True, cap1=True)
    seat = M.Part(V, F, m, name="seat")
    M.recalc_normals(seat)
    parts.append(seat)
    parts.append(K.lathe([(0.0, L + 0.002), (0.15, L + 0.002), (0.15, L - 0.004), (0.0, L - 0.004)], "black", 20).scale((1, 0.7, 1)))
    pts, rad = _leg_line(L, loose, s.get("flare", 0.0))
    if lower:
        k = 4
        left.append(K.tube(pts[:k], rad[:k], m, n=18, name="leg"))
        low_r = [_leg_line(L, 0.0)[1][i] for i in range(3, 6)]
        left.append(K.tube(pts[3:], low_r, lower, n=16, name="hose"))
        (x, y, z), (rx, ry) = _on_leg(L, 0.56, loose)
        left.append(K.ring_tube((x, y, z), 1.0, 0.009, s.get("cuff", trim), axis="z", n=22).scale((rx * 0.9 + 0.004, ry * 0.9 + 0.004, 1), (x, y, z)))
    else:
        left.append(K.tube(pts, rad, m, n=18, name="leg"))
    # ---- kinds
    if kind in ("plate", "mail"):
        plate = s.get("plate", "iron")
        if kind == "mail":
            for i in range(1, 12):
                left.append(_leg_band(L, i / 12.0, s.get("links", "darksteel"), 0.002, 0.0035))
        if kind == "plate":
            (x, y, z), (rx, ry) = _on_leg(L, 0.3)
            left.append(K.sphere(0.1, (x + 0.004, y - 0.03, z), plate, 18, 10, scale=(0.95, 0.66, 1.75)))
            for t in (0.13, 0.46):
                (bx, by, bz), (brx, bry) = _on_leg(L, t)
                left.append(K.ring_tube((bx, by - 0.012, bz), 1.0, 0.0055, trim, axis="z", n=22, arc=200, a0=170)
                            .scale((brx + 0.012, bry + 0.02, 1), (bx, by - 0.012, bz)))
            if s.get("fluted"):
                for dx in (-0.03, 0.0, 0.03):
                    left.append(K.tube([(x + dx, y - 0.093, z + 0.13), (x + dx * 1.1, y - 0.1, z), (x + dx, y - 0.09, z - 0.12)],
                                       [0.0045, 0.005, 0.004], trim, n=5))
            if s.get("rivets"):
                for t in (0.18, 0.3, 0.42):
                    (rx_, ry_, rz_), _ = _on_leg(L, t)
                    for dx in (-0.045, 0.045):
                        left.append(K.sphere(0.0065, (rx_ + dx, ry_ - 0.083, rz_), trim, 6, 4))
            if s.get("tassets"):
                for i in range(2):
                    z0 = L - 0.04 - i * 0.075
                    left.append(K.sphere(0.09, (0.1, -0.075 - 0.006 * i, z0 - 0.06), plate, 14, 8, scale=(1.05, 0.5, 0.62)))
                    left.append(K.tube([(0.02, -0.12 - 0.006 * i, z0 - 0.11), (0.1, -0.128 - 0.006 * i, z0 - 0.118), (0.18, -0.1, z0 - 0.1)], [0.0045] * 3, trim, n=5))
        # the knee cop (poleyn) with a fan on the outside
        knee = s.get("knee", s.get("plate", "iron"))
        (x, y, z), _ = _on_leg(L, 0.56)
        left.append(K.sphere(0.052, (x, y - 0.052, z), knee, 14, 8, scale=(1.05, 0.64, 0.95)))
        fan = [(0, 0), (0.055, 0.03), (0.065, -0.035), (0.025, -0.05)]
        left.append(K.slab(fan, 0.007, knee, axis="y").move((x + 0.03, y - 0.03, z)))
        left.append(K.sphere(0.009, (x, y - 0.086, z), trim, 6, 4))
        if s.get("wings"):
            o = [(0.0, 0.0), (0.05, 0.05), (0.042, 0.015), (0.07, 0.024), (0.034, -0.01)]
            left.append(K.slab(o, 0.006, s["wings"], axis="y").move((x + 0.05, y - 0.02, z + 0.01)))
        if s.get("frost"):
            for i in range(3):
                left.append(K.crystal((x + 0.03 - i * 0.03, y - 0.07, z + 0.03), 0.07 - i * 0.01, 0.012, s["frost"], rot=(20 - i * 20, 20, 0)))
    elif kind in ("trousers", "silk"):
        (x, y, z), (rx, ry) = _on_leg(L, 1.0, loose)
        cuff = s.get("cuff", trim)
        if cuff and not lower:
            left.append(K.ring_tube((x, y, z + 0.012), 1.0, 0.008, cuff, axis="z", n=22).scale((rx + 0.004, ry + 0.004, 1), (x, y, z + 0.012)))
        if s.get("stripe"):
            p2, r2 = _leg_line(L, loose, s.get("flare", 0.0))
            left.append(K.tube([(pp[0] + rr[0] + 0.001, pp[1], pp[2]) for pp, rr in zip(p2, r2)], [(0.004, 0.012)] * len(p2), s["stripe"], n=6, up=(1, 0, 0)))
        if s.get("wraps"):
            for i in range(9):
                left.append(_leg_band(L, 0.6 + i * 0.045, s["wraps"], 0.003, 0.0045, loose, tilt=12 if i % 2 else -12))
        if s.get("knee_pad"):
            (kx, ky, kz), _ = _on_leg(L, 0.56, loose)
            left.append(K.sphere(0.05, (kx, ky - 0.05, kz), s["knee_pad"], 12, 8, scale=(1.0, 0.55, 1.0)))
    elif kind in ("hide", "chaps", "wrap"):
        if kind == "hide" or s.get("lacing"):
            lace = s.get("lacing", "darkleather")
            zig = []
            for i in range(14):
                t = 0.04 + i * 0.065
                (x, y, z), (rx, ry) = _on_leg(L, t)
                zig.append((x + rx + 0.002, y + (0.012 if i % 2 else -0.012), z))
            left.append(K.tube(zig, [0.003] * len(zig), lace, n=5, up=(1, 0, 0)))
        if kind == "chaps" or s.get("guards"):
            g = s.get("guards", "tan")
            (x, y, z), _ = _on_leg(L, 0.26)
            left.append(K.sphere(0.095, (x + 0.004, y - 0.028, z), g, 16, 9, scale=(0.98, 0.7, 1.9)))
            for t in (0.12, 0.36):
                left.append(_leg_band(L, t, s.get("straps", "darkleather"), 0.012, 0.0055))
        if kind == "wrap" or s.get("wraps"):
            w = s.get("wraps", "darkleather")
            for i in range(10):
                left.append(_leg_band(L, 0.55 + i * 0.045, w, 0.003, 0.005, tilt=14 if i % 2 else -14))
        if s.get("knee_pad"):
            (x, y, z), _ = _on_leg(L, 0.56)
            left.append(K.sphere(0.05, (x, y - 0.05, z), s["knee_pad"], 12, 8, scale=(1.0, 0.55, 1.0)))
        if s.get("plates"):
            for t in (0.2, 0.33):
                (x, y, z), _ = _on_leg(L, t)
                left.append(K.sphere(0.05, (x + 0.01, y - 0.06, z), s["plates"], 10, 6, scale=(1.0, 0.45, 1.2)))
        if s.get("pouch"):
            (x, y, z), (rx, ry) = _on_leg(L, 0.16)
            left.append(K.box(0.04, 0.05, 0.07, (x + rx + 0.012, y - 0.01, z), s["pouch"], 0.008))
            left.append(K.box(0.042, 0.052, 0.018, (x + rx + 0.012, y - 0.01, z + 0.03), s.get("straps", "darkleather"), 0.004))
        if s.get("knife"):
            (x, y, z), (rx, ry) = _on_leg(L, 0.22)
            left.append(K.box(0.018, 0.028, 0.2, (x + rx + 0.008, y + 0.01, z - 0.04), "darkleather", 0.006))
            left.append(K.tube([(x + rx + 0.008, y + 0.01, z + 0.06), (x + rx + 0.008, y + 0.01, z + 0.12)], [0.009, 0.008], "wood", n=6))
            left.append(K.sphere(0.011, (x + rx + 0.008, y + 0.01, z + 0.125), s.get("trim", "iron"), 6, 4))
        if s.get("feathers"):
            (x, y, z), (rx, ry) = _on_leg(L, 0.03)
            for i in range(3):
                fy = y - 0.022 + i * 0.022
                left.append(K.tube([(x + rx + 0.004, fy, z), (x + rx + 0.012, fy, z - 0.07), (x + rx + 0.016, fy, z - 0.15 + i * 0.02)],
                                   [(0.003, 0.002), (0.013, 0.0025), (0.002, 0.001)], s["feathers"] if i != 1 else trim, n=6, up=(1, 0, 0)))
    if s.get("runes"):
        for i in range(4):
            (x, y, z), (rx, ry) = _on_leg(L, 0.12 + i * 0.1, loose)
            left.append(K.gem((x + rx * 0.72, y - ry * 0.72, z), 0.009, s["runes"], rot=(90, 0, -35)))
    if s.get("stars"):
        for i in range(5):
            (x, y, z), (rx, ry) = _on_leg(L, 0.1 + ((i * 0.37) % 1.0) * 0.8, loose)
            a = -math.pi / 2 + (i - 2) * 0.35
            left.append(K.gem((x + rx * math.cos(a) * 1.02, y + ry * math.sin(a) * 1.02, z), 0.007, s["stars"]))
    parts += left + _mirror(left)
    # waistband, buckle, hanging panel and sash
    belt = s.get("belt", "leather")
    parts.append(K.lathe([(0.166, L - 0.05), (0.173, L - 0.045), (0.173, L - 0.005), (0.166, L)], belt, 24).scale((1, 0.72, 1)))
    parts.append(K.box(0.04, 0.02, 0.045, (0, -0.126, L - 0.026), s.get("clasp", "brass"), 0.004))
    if s.get("glow"):
        parts.append(K.gem((0, -0.14, L - 0.026), 0.013, s["glow"], rot=(90, 0, 0)))
    if s.get("panel"):
        o = [(-0.09, 0.0), (0.09, 0.0), (0.11, -0.44), (0.0, -0.5), (-0.11, -0.44)]
        parts.append(K.slab(o, 0.008, s["panel"], axis="y").move((0, -0.13, L - 0.04)))
        parts.append(K.tube([(-0.105, -0.136, L - 0.47), (0.0, -0.138, L - 0.53), (0.105, -0.136, L - 0.47)], [0.005] * 3, trim, n=5))
    if s.get("sash"):
        parts.append(K.tube([(0.12, -0.1, L - 0.03), (0.16, -0.08, L - 0.2), (0.17, -0.07, L - 0.36)], [(0.03, 0.006), (0.034, 0.006), (0.036, 0.006)],
                            s["sash"], n=6, up=(0, -1, 0)))
    for p in parts:
        p.scale((0.8, 0.8, 0.8))
    return _ground(parts)


# ---- jewellery -----------------------------------------------------------------------------------------------------

def ring(s):
    m = s.get("mat", "copper")
    parts = [K.ring_tube((0, 0, 0.011), 0.011, s.get("band", 0.0022), m, axis="y", n=28)]
    kind = s.get("kind", "plain")
    top = 0.024
    if kind == "gem":
        parts.append(K.lathe([(0.0, top - 0.004), (0.006, top - 0.002), (0.007, top + 0.002), (0.0, top + 0.002)], m, 10))
        parts.append(K.gem((0, 0, top + 0.004), 0.006, s.get("gem", "sapphire")))
        for k in range(4):
            a = math.radians(45 + 90 * k)
            parts.append(K.tube([(0.005 * math.cos(a), 0.005 * math.sin(a), top), (0.006 * math.cos(a), 0.006 * math.sin(a), top + 0.007)], [0.0012, 0.0008], m, n=5))
    elif kind == "signet":
        parts.append(K.lathe([(0.0, top - 0.004), (0.009, top - 0.003), (0.009, top + 0.001), (0.0, top + 0.001)], m, 16).scale((1, 0.8, 1)))
        parts.append(K.ring_tube((0, 0, top + 0.0012), 0.0055, 0.0009, s.get("gem", "onyx"), axis="z", n=14))
        parts.append(K.box(0.0015, 0.008, 0.0012, (0, 0, top + 0.0012), s.get("gem", "onyx")))
    elif kind == "aether":
        parts.append(K.crystal((0, 0, top + 0.012), 0.024, 0.005, "aether"))
        parts.append(K.ring_tube((0, 0, top + 0.012), 0.009, 0.0007, "aether", axis="z", n=18))
        parts.append(K.lathe([(0.0, top - 0.003), (0.005, top - 0.002), (0.004, top + 0.002), (0.0, top + 0.002)], m, 10))
    elif kind == "twist":
        parts.append(K.ring_tube((0, 0, 0.011), 0.0115, 0.0012, s.get("gem", "gold"), axis="y", n=28).rot(Rz(8), (0, 0, 0.011)))
    return _ground(parts)


def _chain(points, mat, r=0.0015):
    pts = list(points)
    return K.tube(pts, [r] * len(pts), mat, n=5, up=(0, 0, 1))


def amulet(s):
    """Pendant lying flat with its chain coiled around it."""
    m = s.get("mat", "gold")
    parts = []
    cm = s.get("chain", m)
    loop = [(0.03 * math.cos(a) * 1.3, 0.03 * math.sin(a) + 0.045, 0.002) for a in np.linspace(-math.pi / 2, 1.5 * math.pi, 30)]
    parts.append(_chain(loop, cm))
    kind = s.get("kind", "medallion")
    if kind == "fang":
        parts.append(K.tube([(0, 0.012, 0.004), (0.004, -0.01, 0.004), (0.0, -0.04, 0.003)], [0.006, 0.005, 0.0005], "bone", n=6))
        parts.append(K.ring_tube((0, 0.014, 0.004), 0.004, 0.001, cm, axis="y", n=10))
        for x in (-0.012, 0.012):
            parts.append(K.sphere(0.004, (x, 0.018, 0.004), s.get("bead", "redwood"), 6, 4))
    elif kind == "medallion":
        parts.append(K.lathe([(0.0, 0.0), (0.02, 0.0), (0.022, 0.003), (0.02, 0.006), (0.0, 0.006)], m, 24))
        parts.append(K.gem((0, 0, 0.008), 0.008, s.get("gem", "ruby"), facets=8))
        parts.append(K.ring_tube((0, 0, 0.006), 0.016, 0.0012, m, axis="z", n=20))
    elif kind == "star":
        pts = []
        for i in range(10):
            a = math.pi / 2 + i * math.pi / 5
            rr = 0.024 if i % 2 == 0 else 0.01
            pts.append((rr * math.cos(a), rr * math.sin(a) - 0.005))
        parts.append(M.bevel(K.slab(pts, 0.004, m, axis="z", center=0.003), 0.001, 1))
        parts.append(K.gem((0, -0.005, 0.007), 0.006, s.get("gem", "topaz"), facets=6))
    elif kind == "cage":
        parts.append(K.crystal((0, -0.01, 0.012), 0.03, 0.009, "aether", rot=(90, 0, 0)))
        for k in range(4):
            parts.append(K.ring_tube((0, -0.01, 0.012), 0.013, 0.0012, m, axis="y", n=16).rot(Ry(45 * k), (0, -0.01, 0.012)).rot(Rx(90), (0, -0.01, 0.012)))
    return _ground(parts)


def charm(s):
    m = s.get("mat", "stone")
    parts = []
    parts.append(_chain([(0.0, 0.03, 0.002), (0.02, 0.05, 0.002), (0.0, 0.07, 0.002), (-0.02, 0.05, 0.002), (0.0, 0.03, 0.002)], s.get("cord", "leather"), 0.0018))
    kind = s.get("kind", "rune")
    if kind == "rune":
        parts.append(K.lathe([(0.0, 0.0), (0.024, 0.0), (0.026, 0.004), (0.022, 0.008), (0.0, 0.008)], m, 10).scale((1, 1.15, 1)))
        for seg in (((-0.008, -0.01), (0.0, 0.012)), ((0.0, 0.012), (0.008, -0.01)), ((-0.006, 0.0), (0.006, 0.0))):
            (a, b) = seg
            parts.append(K.tube([(a[0], a[1], 0.009), (b[0], b[1], 0.009)], [0.0016, 0.0016], s.get("glow", "tide"), n=5, up=(0, 0, 1)))
    elif kind == "talisman":
        o = [(0.0, -0.028), (0.022, -0.01), (0.026, 0.014), (0.01, 0.024), (-0.01, 0.024), (-0.026, 0.014), (-0.022, -0.01)]
        parts.append(M.bevel(K.slab(o, 0.006, m, axis="z", center=0.003), 0.001, 1))
        for sx in (1, -1):
            parts.append(K.tube([(sx * 0.02, 0.018, 0.004), (sx * 0.034, 0.03, 0.005), (sx * 0.03, 0.045, 0.006)], [0.004, 0.003, 0.0006], "horn", n=6, up=(0, 0, 1)))
        parts.append(K.gem((0, 0.0, 0.008), 0.007, s.get("gem", "ruby")))
    return _ground(parts)


GEAR = {
    # shields
    "warden_kite_shield": (shield, {"shape": "heater", "face": "crimson", "emblem": "order"}),
    "sigil_buckler": (shield, {"shape": "round", "r": 0.25, "face": "navy", "rim": "gold", "emblem": "sigil", "gem": "sapphire"}),
    "tower_shield": (shield, {"shape": "tower", "w": 0.34, "h": 0.62, "face": "forest", "rim": "iron", "emblem": "tower", "curve": 0.5}),
    "guardian_aegis": (shield, {"shape": "heater", "w": 0.68, "face": "white", "rim": "gold", "emblem": "aegis"}),
    # helms
    "iron_helm": (helm, {"kind": "kettle", "mat": "iron", "trim": "iron"}),
    "barbute_helm": (helm, {"kind": "barbute", "mat": "steel", "trim": "bronze"}),
    "visored_greathelm": (helm, {"kind": "greathelm", "mat": "bright", "trim": "gold"}),
    "guardian_helm": (helm, {"kind": "winged", "mat": "bright", "trim": "gold"}),
    "linen_hood": (hood, {"mat": "wool", "trim": "linen"}),
    "arcanist_cowl": (hood, {"mat": "navy", "trim": "gold", "peak": 1.8, "gem": "sapphire"}),
    "seers_circlet": (circlet, {"metal": "silver", "gem": "amethyst", "veil": "silk"}),
    "sage_hood": (hood, {"mat": "violet", "trim": "paleg", "stars": "holy", "peak": 1.5}),
    # chest
    "iron_hauberk": (chest, {"kind": "mail", "mat": "iron", "belt": "leather"}),
    "brigandine": (chest, {"kind": "brigandine", "mat": "crimson", "rivet": "gold", "belt": "leather", "trim": "leather"}),
    "warden_plate": (chest, {"kind": "plate", "mat": "steel", "trim": "gold", "belt": "darkleather"}),
    "guardian_plate": (chest, {"kind": "plate", "mat": "bright", "trim": "gold", "glow": "aether", "belt": "white"}),
    "apprentice_robe": (chest, {"kind": "robe", "mat": "ochre", "trim": "linen", "len": 0.85, "belt": "rope"}),
    "traveler_coat": (chest, {"kind": "robe", "mat": "forest", "trim": "tan", "len": 0.8, "belt": "leather"}),
    "magister_robe": (chest, {"kind": "robe", "mat": "navy", "trim": "gold", "len": 0.95, "glow": "sapphire", "belt": "crimson"}),
    "sage_robe": (chest, {"kind": "robe", "mat": "violet", "trim": "paleg", "len": 0.95, "stars": "holy", "belt": "paleg"}),
    # inner garments
    "padded_gambeson": (chest, {"kind": "gambeson", "mat": "wool", "trim": "linen"}),
    "silk_undershirt": (chest, {"kind": "shirt", "mat": "silk", "trim": "white"}),
    "chain_shirt": (chest, {"kind": "chain", "mat": "iron", "trim": "darksteel"}),
    "runeweave_vest": (chest, {"kind": "vest", "mat": "teal", "rivet": "tide", "runes": "tide", "trim": "silver"}),
    # gloves
    "iron_gauntlet": (glove, {"mat": "darkleather", "plate": "iron", "trim": "iron"}),
    "spiked_gauntlet": (glove, {"mat": "darkleather", "plate": "steel", "spikes": "bright", "trim": "gold"}),
    "silk_glove": (glove, {"mat": "silk", "trim": "silver"}),
    "runed_glove": (glove, {"mat": "navy", "trim": "gold", "runes": "sapphire", "cuff": "gold"}),
    "guardian_gauntlets": (glove, {"mat": "white", "plate": "bright", "trim": "gold", "runes": "aether"}),
    "sage_gloves": (glove, {"mat": "violet", "trim": "paleg", "runes": "holy"}),
    # boots
    "iron_sabaton": (boot, {"mat": "darkleather", "plate": "iron"}),
    "warden_greave": (boot, {"mat": "darkleather", "plate": "steel", "cuff": "gold", "h": 0.34}),
    "soft_boot": (boot, {"mat": "tan", "h": 0.24, "flare": 0.012}),
    "wayfarer_boot": (boot, {"mat": "leather", "h": 0.32, "cuff": "fur", "straps": "darkleather"}),
    "guardian_greaves": (boot, {"mat": "white", "plate": "bright", "cuff": "gold", "wings": "gold", "glow": "aether", "h": 0.34}),
    "sage_boots": (boot, {"mat": "violet", "h": 0.28, "cuff": "paleg", "glow": "holy", "flare": 0.015}),
    # rings, amulets, charms
    # leggings (bh-024): knights
    "iron_cuisses": (legs, {"kind": "plate", "mat": "wool", "plate": "iron", "trim": "iron", "belt": "leather"}),
    "mail_chausses": (legs, {"kind": "mail", "mat": "iron", "links": "darksteel", "knee": "iron", "trim": "iron", "belt": "leather"}),
    "riveted_legplates": (legs, {"kind": "plate", "mat": "darkleather", "plate": "steel", "trim": "brass", "rivets": True, "belt": "darkleather"}),
    "warden_cuisses": (legs, {"kind": "plate", "mat": "darkleather", "plate": "bright", "trim": "gold", "fluted": True, "wings": "gold", "belt": "darkleather"}),
    "commander_cuisses": (legs, {"kind": "plate", "mat": "crimson", "plate": "steel", "trim": "gold", "tassets": True, "fluted": True, "glow": "ruby", "belt": "darkleather", "clasp": "gold"}),
    "guardian_cuisses": (legs, {"kind": "plate", "mat": "white", "plate": "bright", "trim": "gold", "wings": "gold", "glow": "aether", "belt": "white", "clasp": "gold"}),
    "u_rimewalkers": (legs, {"kind": "plate", "mat": "navy", "plate": "moonsteel", "trim": "silver", "frost": "ice", "glow": "ice", "belt": "darkleather", "clasp": "silver"}),
    "u_oathbound_cuisses": (legs, {"kind": "plate", "mat": "darkleather", "plate": "blackiron", "trim": "gold", "fluted": True, "glow": "holy", "belt": "darkleather", "clasp": "gold"}),
    "u_echoing_legplates": (legs, {"kind": "plate", "mat": "darkleather", "plate": "bronze", "trim": "gold", "rivets": True, "tassets": True, "glow": "storm", "belt": "darkleather", "clasp": "gold"}),
    # mages
    "linen_trousers": (legs, {"kind": "trousers", "mat": "linen", "loose": 0.18, "flare": 0.15, "cuff": "linen", "trim": "rope", "belt": "rope"}),
    "scholars_breeches": (legs, {"kind": "trousers", "mat": "wool", "loose": 0.2, "hose": "linen", "cuff": "navy", "sash": "navy", "belt": "leather"}),
    "arcanist_legwraps": (legs, {"kind": "silk", "mat": "navy", "loose": 0.08, "wraps": "gold", "runes": "sapphire", "cuff": "gold", "trim": "gold", "belt": "navy", "clasp": "gold"}),
    "magister_silks": (legs, {"kind": "silk", "mat": "crimson", "loose": 0.22, "flare": 0.1, "panel": "navy", "trim": "gold", "cuff": "gold", "glow": "sapphire", "belt": "navy", "clasp": "gold"}),
    "aethersilk_trousers": (legs, {"kind": "silk", "mat": "silk", "loose": 0.16, "trim": "silver", "cuff": "silver", "runes": "aether", "glow": "aether", "stripe": "silver", "belt": "navy", "clasp": "silver"}),
    "sage_leggings": (legs, {"kind": "silk", "mat": "violet", "loose": 0.14, "trim": "paleg", "cuff": "paleg", "stars": "holy", "glow": "holy", "belt": "paleg", "clasp": "paleg"}),
    "u_stillwater_silks": (legs, {"kind": "silk", "mat": "teal", "loose": 0.24, "flare": 0.2, "trim": "silver", "cuff": "silver", "panel": "teal", "glow": "tide", "belt": "darkleather", "clasp": "silver"}),
    "u_riftwalker_legwraps": (legs, {"kind": "silk", "mat": "black", "loose": 0.06, "wraps": "silver", "runes": "portal", "cuff": "silver", "trim": "silver", "glow": "ice", "belt": "violet", "clasp": "silver"}),
    # rangers
    "hide_leggings": (legs, {"kind": "hide", "mat": "tan", "lacing": "leather", "belt": "leather"}),
    "trackers_breeches": (legs, {"kind": "hide", "mat": "leather", "lacing": "darkleather", "knee_pad": "darkleather", "pouch": "tan", "belt": "darkleather"}),
    "staghide_chaps": (legs, {"kind": "chaps", "mat": "forest", "guards": "tan", "straps": "darkleather", "belt": "leather"}),
    "longstrider_leggings": (legs, {"kind": "chaps", "mat": "forest", "guards": "leather", "straps": "darkleather", "knee_pad": "leather", "pouch": "leather", "belt": "darkleather"}),
    "windrunner_leggings": (legs, {"kind": "hide", "mat": "leather", "lacing": "tan", "feathers": "white", "guards": "tan", "straps": "darkleather", "trim": "wind", "glow": "wind", "belt": "darkleather"}),
    "u_windswift_breeches": (legs, {"kind": "hide", "mat": "tan", "lacing": "white", "feathers": "white", "trim": "wind", "glow": "wind", "knee_pad": "leather", "belt": "leather"}),
    "u_stormstriders": (legs, {"kind": "chaps", "mat": "darkleather", "guards": "leather", "straps": "gold", "runes": "storm", "trim": "gold", "glow": "storm", "belt": "darkleather", "clasp": "gold"}),
    # shadowblades
    "cutpurse_trousers": (legs, {"kind": "wrap", "mat": "black", "wraps": "darkleather", "pouch": "leather", "straps": "darkleather", "belt": "darkleather"}),
    "nightweave_leggings": (legs, {"kind": "wrap", "mat": "black", "wraps": "black", "knife": True, "trim": "darksteel", "belt": "darkleather", "clasp": "darksteel"}),
    "silentstep_breeches": (legs, {"kind": "wrap", "mat": "black", "wraps": "darkleather", "knee_pad": "darkleather", "belt": "darkleather", "clasp": "darksteel"}),
    "duskrunner_leggings": (legs, {"kind": "wrap", "mat": "black", "wraps": "leather", "plates": "darkleather", "knife": True, "trim": "darksteel", "belt": "darkleather", "clasp": "darksteel"}),
    "veilstalker_leggings": (legs, {"kind": "wrap", "mat": "violet", "wraps": "black", "plates": "blackiron", "runes": "shadow", "trim": "moonsteel", "glow": "shadow", "belt": "black", "clasp": "moonsteel"}),
    "u_bloodrunner": (legs, {"kind": "wrap", "mat": "redleather", "wraps": "black", "plates": "blackiron", "knife": True, "trim": "blackiron", "glow": "ruby", "belt": "black", "clasp": "blackiron"}),

    "copper_ring": (ring, {"mat": "copper", "kind": "plain", "band": 0.0026}),
    "silver_ring": (ring, {"mat": "silver", "kind": "gem", "gem": "sapphire"}),
    "sigil_ring": (ring, {"mat": "gold", "kind": "signet", "gem": "onyx"}),
    "u_band_of_stillness": (ring, {"mat": "moonsteel", "kind": "aether"}),
    "bone_amulet": (amulet, {"kind": "fang", "chain": "leather"}),
    "gold_amulet": (amulet, {"kind": "medallion", "mat": "gold", "gem": "ruby"}),
    "star_pendant": (amulet, {"kind": "star", "mat": "silver", "gem": "topaz", "chain": "silver"}),
    "u_heart_of_aether": (amulet, {"kind": "cage", "mat": "silver", "chain": "silver"}),
    "rune_charm": (charm, {"kind": "rune", "mat": "slate", "glow": "tide"}),
    "war_talisman": (charm, {"kind": "talisman", "mat": "bronze", "gem": "ruby"}),
}
