"""Consumables, crafting materials, quest items and the gold pile (bh-006). Everything stands upright on z = 0."""
import math

import numpy as np

import item_kit as K
from item_kit import M, Rx, Ry, Rz


def _ground(parts):
    zmin = min(p.V[:, 2].min() for p in parts)
    for p in parts:
        p.move((0, 0, -zmin))
    return parts


# ---- bottles -------------------------------------------------------------------------------------------------------

BOTTLES = {
    # (body profile r,z pairs from the base up to the shoulder), neck radius, neck top
    "round": ([(0.0, 0.0), (0.03, 0.0), (0.045, 0.015), (0.052, 0.045), (0.048, 0.075), (0.03, 0.095), (0.014, 0.105)], 0.013, 0.14),
    "vial": ([(0.0, 0.0), (0.018, 0.0), (0.022, 0.01), (0.022, 0.1), (0.018, 0.115), (0.01, 0.12)], 0.0095, 0.145),
    "tall": ([(0.0, 0.0), (0.03, 0.0), (0.034, 0.01), (0.034, 0.1), (0.026, 0.125), (0.013, 0.135)], 0.012, 0.175),
    "flask": ([(0.0, 0.0), (0.04, 0.0), (0.045, 0.012), (0.045, 0.045), (0.03, 0.07), (0.014, 0.08)], 0.012, 0.13),
    "heart": ([(0.0, 0.0), (0.012, 0.004), (0.04, 0.035), (0.05, 0.07), (0.042, 0.095), (0.02, 0.105)], 0.011, 0.14),
    "gourd": ([(0.0, 0.0), (0.035, 0.0), (0.046, 0.03), (0.036, 0.06), (0.025, 0.075), (0.032, 0.1), (0.022, 0.125), (0.012, 0.13)], 0.011, 0.155),
    "bulb": ([(0.0, 0.0), (0.02, 0.0), (0.028, 0.02), (0.05, 0.06), (0.05, 0.085), (0.03, 0.11), (0.012, 0.118)], 0.011, 0.16),
    "facet": ([(0.0, 0.0), (0.035, 0.0), (0.05, 0.03), (0.05, 0.09), (0.035, 0.12), (0.013, 0.13)], 0.013, 0.17),
    "jug": ([(0.0, 0.0), (0.04, 0.0), (0.05, 0.03), (0.05, 0.08), (0.04, 0.1), (0.028, 0.11)], 0.024, 0.13),
}


def bottle(s):
    kind = s.get("shape", "round")
    prof, nr, top = BOTTLES[kind]
    sides = 6 if kind == "facet" else 20
    glass = s.get("glass", "glass")
    liq = s.get("liquid", "red_liquid")
    parts = []
    # the body reads as the potion itself up to the fill line (the game's materials are opaque); clear glass above it
    fill = s.get("fill", 0.8)
    zs = [z for _, z in prof]
    rs = [r for r, _ in prof]
    zf = prof[-1][1] * fill
    rf = float(np.interp(zf, zs, rs))
    lower = [(r, z) for r, z in prof if z < zf - 1e-4]
    parts.append(K.lathe(lower + [(rf, zf), (0.0, zf)], liq, sides, "liquid"))
    upper = [(0.0, zf - 0.001), (rf * 0.99, zf - 0.001)] + [(r, z) for r, z in prof if z > zf + 1e-4]
    upper += [(nr, prof[-1][1] + 0.005), (nr, top - 0.012), (nr * 1.35, top - 0.008), (nr * 1.3, top), (0.0, top)]
    parts.append(K.lathe(upper, glass, sides, "glass"))
    parts.append(K.ring_tube((0, 0, zf), rf * 1.01, 0.0018, glass, axis="z", n=sides if sides > 8 else 12))
    # stopper
    st = s.get("stopper", "cork")
    if st == "cork":
        parts.append(K.lathe([(0, top - 0.01), (nr * 0.95, top - 0.01), (nr * 1.05, top + 0.012), (nr * 0.9, top + 0.018), (0, top + 0.018)], "tan", 10))
    elif st == "wax":
        parts.append(K.lathe([(0, top - 0.008), (nr * 1.4, top - 0.01), (nr * 1.5, top + 0.008), (nr * 1.1, top + 0.016), (0, top + 0.018)], s.get("wax", "wax_red"), 12))
    elif st == "gem":
        parts.append(K.lathe([(0, top - 0.004), (nr * 1.1, top - 0.004), (nr * 1.1, top + 0.004), (0, top + 0.004)], s.get("metal", "gold"), 12))
        parts.append(K.gem((0, 0, top + 0.014), nr * 1.2, s.get("gem", "ruby")))
    elif st == "metal":
        parts.append(K.lathe([(0, top - 0.01), (nr * 1.1, top - 0.01), (nr * 1.2, top + 0.01), (nr * 0.6, top + 0.02), (0, top + 0.03)], s.get("metal", "silver"), 10))
    # neck string / band / label
    parts.append(K.band(top - 0.02, nr * 1.08, 0.006, s.get("tie", "rope"), n=10))
    if s.get("label"):
        r_mid = max(r for r, _ in prof)
        z_mid = prof[len(prof) // 2][1]
        parts.append(K.lathe([(r_mid * 1.05, z_mid - 0.018), (r_mid * 1.07, z_mid - 0.017), (r_mid * 1.07, z_mid + 0.017), (r_mid * 1.05, z_mid + 0.018)],
                             s["label"], sides))
    if s.get("filigree"):
        for a in np.linspace(0, 2 * math.pi, 6, endpoint=False):
            pts = []
            for i in range(8):
                t = i / 7
                z = prof[1][1] + (prof[-1][1] - prof[1][1]) * t
                r = np.interp(z, [p[1] for p in prof], [p[0] for p in prof]) * 1.06
                aa = a + 0.4 * math.sin(t * math.pi)
                pts.append((r * math.cos(aa), r * math.sin(aa), z))
            parts.append(K.tube(pts, [0.0022] * 8, s["filigree"], n=5, up=(0, 0, 1)))
    if s.get("feather"):
        parts.append(_feather(top + 0.01, 0.1, s["feather"], s.get("feather_tip", s["feather"])).__iter__().__next__())
    if s.get("emboss"):
        r_mid = max(r for r, _ in prof)
        z_mid = prof[len(prof) // 2][1]
        parts.append(K.lathe([(0.0, -0.001), (0.014, 0.0), (0.015, 0.003), (0.0, 0.004)], s["emboss"], 16).rot(Rx(90)).move((0, -r_mid * 1.04, z_mid)))
    if s.get("wing"):
        for sx in (1, -1):
            o = [(0.0, 0.0), (0.03, 0.02), (0.05, 0.05), (0.035, 0.03), (0.045, 0.025), (0.02, 0.005)]
            r_mid = max(r for r, _ in prof)
            parts.append(K.slab([(sx * x, z) for x, z in o], 0.003, s["wing"], axis="y").move((sx * r_mid * 0.95, 0, prof[len(prof) // 2][1])))
    return _ground(parts)


def _feather(z0, length, mat, tip_mat):
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((0.012 * math.sin(t * 2.5), 0.0, z0 + length * t))
    vane = []
    for i in range(12):
        t = i / 11
        w = 0.02 * math.sin(math.pi * min(t * 1.1, 1.0)) + 0.002
        vane.append(np.array([(0.012 * math.sin(t * 2.5) - w, 0.0, z0 + length * t), (0.012 * math.sin(t * 2.5) + w, 0.0, z0 + length * t),
                              (0.012 * math.sin(t * 2.5) + w, 0.002, z0 + length * t), (0.012 * math.sin(t * 2.5) - w, 0.002, z0 + length * t)]))
    V, F = M.loft(vane)
    yield M.Part(V, F, mat, name="vane")


def feather(s):
    parts = []
    L = 0.3
    # quill + vanes with barbs, laid on the ground with a slight arch
    quill = [(0.0, -0.04 + 0.0 * t, 0.004 + 0.02 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 2)]
    pts = []
    for i in range(12):
        t = i / 11
        pts.append((0.03 * math.sin(t * 2.2), -0.02 + L * t, 0.006 + 0.025 * math.sin(math.pi * t)))
    parts.append(K.tube(pts, [0.003 * (1 - 0.7 * t) + 0.0008 for t in np.linspace(0, 1, 12)], "bone", n=6, up=(0, 0, 1)))
    for side in (1, -1):
        for i in range(2, 12):
            t = i / 11
            c = np.array(pts[i])
            w = (0.05 * math.sin(math.pi * min((t - 0.1) * 1.15, 1.0)) + 0.006) * (1.0 if side > 0 else 0.8)
            tipc = c + np.array([side * w, 0.03 * w / 0.05 + 0.008, -0.004])
            mat = s.get("tip", "flame_tip") if t > 0.75 else s.get("mat", "flame")
            parts.append(K.tube([c, (c + tipc) / 2 + np.array([0, 0, 0.002]), tipc], [0.006, 0.005, 0.001], mat, n=5, up=(0, 0, 1)).scale((1, 1, 0.35), tuple(c)))
    return _ground(parts)


# ---- scrolls, pouches, pots ------------------------------------------------------------------------------------------

def scroll(s):
    parts = []
    L = 0.2
    paper = s.get("paper", "paper")
    # the rolled sheet (lying along X) with a curled edge
    parts.append(K.lathe([(0, -L / 2), (0.024, -L / 2), (0.026, -L / 2 + 0.01), (0.026, L / 2 - 0.01), (0.024, L / 2), (0, L / 2)], paper, 18).rot(Ry(90)).move((0, 0, 0.026)))
    parts.append(K.box(0.16, 0.05, 0.002, (0.0, -0.045, 0.001), paper).rot(Rz(4)))
    for x in (-L / 2 - 0.012, L / 2 + 0.012):
        parts.append(K.lathe([(0, -0.012), (0.01, -0.012), (0.012, 0.0), (0.01, 0.012), (0, 0.012)], s.get("rod", "darkwood"), 10).rot(Ry(90)).move((x, 0, 0.026)))
    parts.append(K.band(0.0, 0.028, 0.012, s.get("ribbon", "crimson"), n=18).rot(Ry(90)).move((0.02, 0, 0.026)))
    seal = s.get("seal", "wax_red")
    big = 1.6 if s.get("glow") else 1.0
    parts.append(K.lathe([(0, -0.004), (0.014 * big, -0.004), (0.016 * big, 0.0), (0.012 * big, 0.004), (0, 0.005)], seal, 16).rot(Rx(90)).move((0.02, -0.03, 0.026)))
    if s.get("glow"):
        # a swirling rift sigil pressed into the seal, with sparks of torn space around it
        pts = []
        for i in range(24):
            t = i / 23
            a = t * 3.5 * math.pi
            r = 0.004 + 0.016 * t
            pts.append((0.02 + r * math.cos(a), -0.037, 0.026 + r * math.sin(a)))
        parts.append(K.tube(pts, [0.0014] * len(pts), "black", n=4, up=(0, 1, 0)))
        parts.append(K.ring_tube((0.02, -0.036, 0.026), 0.027, 0.0018, s["glow"], axis="y", n=20))
        for k in range(8):
            a = math.radians(k * 45 + 10)
            parts.append(K.gem((0.02 + 0.034 * math.cos(a), -0.034, 0.026 + 0.034 * math.sin(a)), 0.0035, s["glow"]))
    return _ground(parts)


def pouch(s):
    m = s.get("mat", "tan")
    parts = []
    prof = [(0.0, 0.0), (0.035, 0.002), (0.05, 0.02), (0.052, 0.045), (0.04, 0.065), (0.018, 0.075), (0.014, 0.085), (0.024, 0.1), (0.0, 0.1)]
    parts.append(K.lathe(prof, m, 16, "pouch").warp(lambda v: (v[0] * (1 + 0.08 * math.sin(v[2] * 90)), v[1], v[2])))
    parts.append(K.band(0.078, 0.017, 0.008, s.get("tie", "rope"), n=12))
    if s.get("spill"):
        parts.append(K.sphere(0.03, (0.05, -0.03, 0.0), s["spill"], 10, 6, scale=(1.4, 1.1, 0.3)))
        for k in range(8):
            a = k * 0.8
            parts.append(K.gem((0.05 + 0.03 * math.cos(a), -0.03 + 0.025 * math.sin(a), 0.005), 0.003, s["spill"]))
    if s.get("pellets"):
        for k in range(4):
            a = k * 1.6
            parts.append(K.sphere(0.012, (0.055 + 0.018 * math.cos(a), 0.018 * math.sin(a), 0.012), s["pellets"], 8, 6))
    return _ground(parts)


def bomb(s):
    parts = []
    kind = s.get("kind", "pot")
    if kind == "pot":
        parts.append(K.lathe([(0, 0.0), (0.035, 0.002), (0.055, 0.04), (0.05, 0.075), (0.028, 0.095), (0.022, 0.1), (0.026, 0.108), (0.0, 0.108)], "clay", 16))
        parts.append(K.band(0.06, 0.054, 0.01, "rope", n=16))
        parts.append(K.tube([(0.0, 0, 0.1), (0.01, 0, 0.13), (0.02, 0.005, 0.15)], [0.006, 0.005, 0.004], "rope", n=6))
        parts.append(K.sphere(0.008, (0.021, 0.005, 0.152), "flame", 8, 6))
        parts.append(K.sphere(0.02, (0, -0.05, 0.05), "ember", 10, 6, scale=(1, 0.2, 1)))
    else:   # frost flask: faceted icy bottle with frost spikes
        parts += bottle({"shape": "facet", "liquid": "ice_liquid", "glass": "ice", "stopper": "metal", "metal": "silver", "fill": 0.9})
        for k in range(6):
            a = math.radians(k * 60)
            parts.append(K.crystal((0.052 * math.cos(a), 0.052 * math.sin(a), 0.03 + 0.02 * (k % 2)), 0.05, 0.008, "ice", rot=(0, 20 * math.cos(a), 0)))
    return _ground(parts)


def jar(s):
    parts = []
    glass = s.get("glass", "glass")
    body = s.get("inner", "storm") if s.get("bolt") else glass
    parts.append(K.lathe([(0, 0), (0.04, 0), (0.045, 0.01), (0.045, 0.085), (0.035, 0.095), (0.035, 0.1), (0.0, 0.1)], body, 18))
    for z in (0.012, 0.05, 0.088):
        parts.append(K.band(z, 0.046, 0.006, s.get("lid", "brass"), n=18))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        parts.append(K.box(0.006, 0.006, 0.09, (0.046 * math.cos(a), 0.046 * math.sin(a), 0.05), s.get("lid", "brass")))
    parts.append(K.lathe([(0, 0.098), (0.038, 0.098), (0.04, 0.115), (0.0, 0.118)], s.get("lid", "brass"), 16))
    inner = s.get("inner", "storm")
    if s.get("bolt"):
        for k in range(3):
            pts = [(0.0, 0.0, 0.015)]
            rng = np.random.default_rng(k + 4)
            for i in range(1, 6):
                pts.append((0.02 * (rng.random() - 0.5), 0.02 * (rng.random() - 0.5), 0.015 + 0.014 * i))
            parts.append(K.tube(pts, [0.002] * len(pts), inner, n=4))
        parts.append(K.sphere(0.018, (0, 0, 0.05), inner, 10, 6))
    else:
        parts.append(K.lathe([(0, 0.004), (0.038, 0.004), (0.038, 0.06), (0, 0.06)], inner, 16))
    return _ground(parts)


def stone_bar(s):
    parts = [M.bevel(K.box(0.14, 0.045, 0.028, (0, 0, 0.014), s.get("mat", "slate")), 0.008, 2)]
    if s.get("wrap"):
        parts.append(K.box(0.03, 0.05, 0.032, (0.03, 0, 0.014), s["wrap"], 0.004))
    return _ground(parts)


def tin(s):
    parts = [K.lathe([(0, 0), (0.045, 0), (0.047, 0.005), (0.047, 0.075), (0.045, 0.08), (0, 0.08)], s.get("mat", "redwood"), 24)]
    parts.append(K.lathe([(0, 0.075), (0.049, 0.075), (0.05, 0.095), (0.035, 0.1), (0, 0.102)], s.get("lid", "brass"), 24))
    parts.append(K.lathe([(0.0475, 0.02), (0.049, 0.02), (0.049, 0.055), (0.0475, 0.055)], s.get("label", "paper"), 24))
    parts.append(K.sphere(0.009, (0, 0, 0.103), s.get("lid", "brass"), 8, 6))
    return _ground(parts)


def stein(s):
    parts = [K.lathe([(0, 0), (0.045, 0), (0.048, 0.01), (0.045, 0.1), (0.048, 0.11), (0.0, 0.11)], s.get("mat", "stone"), 18)]
    for z in (0.02, 0.09):
        parts.append(K.band(z, 0.048, 0.01, s.get("band", "iron"), n=18))
    parts.append(K.tube([(0.045, 0, 0.085), (0.075, 0, 0.08), (0.08, 0, 0.05), (0.075, 0, 0.025), (0.045, 0, 0.02)], [0.008] * 5, s.get("band", "iron"), n=6, up=(0, 1, 0)))
    parts.append(K.lathe([(0, 0.105), (0.043, 0.105), (0.043, 0.112), (0, 0.112)], s.get("liquid", "brown_liquid"), 18))
    parts.append(K.lathe([(0.0, 0.11), (0.047, 0.11), (0.05, 0.125), (0.02, 0.135), (0.0, 0.14)], s.get("lid", "iron"), 18))
    return _ground(parts)


# ---- materials ---------------------------------------------------------------------------------------------------------

def shards(s):
    rng = np.random.default_rng(s.get("seed", 2))
    parts = []
    for k in range(s.get("count", 4)):
        a = rng.random() * 6.28
        d = 0.02 + 0.03 * rng.random()
        o = [(0.0, 0.0), (0.03 + 0.02 * rng.random(), 0.01), (0.02, 0.05 + 0.02 * rng.random()), (-0.01, 0.03)]
        p = K.slab(o, 0.008, s.get("mat", "iron"), axis="y")
        p.rot(Rx(70 + 30 * rng.random())).rot(Rz(math.degrees(a))).move((d * math.cos(a), d * math.sin(a), 0.004))
        parts.append(M.bevel(p, 0.0015, 1))
    return _ground(parts)


def cluster(s):
    parts = []
    rng = np.random.default_rng(s.get("seed", 5))
    m = s.get("mat", "ice")
    parts.append(K.sphere(0.035, (0, 0, 0.01), s.get("base", "stone"), 10, 6, scale=(1.3, 1.1, 0.5)))
    for k in range(s.get("count", 6)):
        a = rng.random() * 6.28
        tilt = 10 + 30 * rng.random()
        L = 0.06 + 0.07 * rng.random() * s.get("scale", 1.0)
        parts.append(K.crystal((0.015 * math.cos(a), 0.015 * math.sin(a), L * 0.45), L, L * 0.18, m,
                               rot=(tilt * math.sin(a), -tilt * math.cos(a), math.degrees(a))))
    return _ground(parts)


def core(s):
    parts = [K.sphere(0.035, (0, 0, 0.035), s.get("glow", "ember"), 14, 10)]
    rng = np.random.default_rng(9)
    for k in range(9):   # cracked crust plates around the glowing heart
        th = rng.random() * 6.28
        ph = rng.random() * 3.0 - 1.5
        d = np.array([math.cos(th) * math.cos(ph), math.sin(th) * math.cos(ph), math.sin(ph)])
        parts.append(K.sphere(0.022, tuple(np.array([0, 0, 0.035]) + d * 0.03), s.get("crust", "ashstone"), 8, 5, scale=(1.0, 1.0, 0.45)))
    return _ground(parts)


def bone(s):
    parts = [K.tube([(-0.06, 0, 0.012), (0.0, 0.004, 0.012), (0.06, 0, 0.012)], [0.01, 0.008, 0.01], "bone", n=10, up=(0, 0, 1))]
    for x in (-0.066, 0.066):
        for dy in (-0.009, 0.009):
            parts.append(K.sphere(0.011, (x, dy, 0.012), "bone", 8, 6))
    if s.get("broken"):
        parts.append(K.cone_spike((0.02, 0.03, 0.006), (0.05, 0.05, 0.008), 0.007, "bone"))
    return _ground(parts)


def bundle(s):
    """Folded cloth / rolled hide."""
    m = s.get("mat", "black")
    parts = []
    if s.get("roll"):
        parts.append(K.lathe([(0, -0.07), (0.028, -0.07), (0.03, -0.06), (0.03, 0.06), (0.028, 0.07), (0, 0.07)], m, 16).rot(Ry(90)).move((0, 0, 0.03)))
        parts.append(K.box(0.14, 0.06, 0.004, (0, -0.045, 0.002), m).rot(Rz(-5)))
        for x in (-0.035, 0.035):
            parts.append(K.band(0.0, 0.032, 0.008, s.get("tie", "rope"), n=14).rot(Ry(90)).move((x, 0, 0.03)))
    else:
        for i in range(3):
            parts.append(M.bevel(K.box(0.12 - 0.01 * i, 0.08 - 0.006 * i, 0.012, (0.004 * i, -0.002 * i, 0.006 + 0.012 * i), m), 0.004, 2))
        parts.append(K.band(0.0, 1.0, 0.01, s.get("tie", "silver"), n=4).scale((0.065, 0.045, 1)).rot(Rx(90)).move((0.02, 0, 0.02)))
        if s.get("sheen"):
            parts.append(K.box(0.1, 0.004, 0.03, (0.0, -0.041, 0.02), s["sheen"]))
    return _ground(parts)


# ---- quest items -----------------------------------------------------------------------------------------------------

def seal_key(s):
    parts = [K.lathe([(0, 0), (0.045, 0), (0.05, 0.004), (0.05, 0.012), (0.045, 0.016), (0, 0.016)], "bronze", 28)]
    parts.append(K.ring_tube((0, 0, 0.017), 0.036, 0.003, "gold", axis="z", n=28))
    for k in range(8):
        a = math.radians(k * 45)
        parts.append(K.box(0.008, 0.012, 0.004, (0.028 * math.cos(a), 0.028 * math.sin(a), 0.018), "gold").rot(Rz(k * 45), (0.028 * math.cos(a), 0.028 * math.sin(a), 0.018)))
    parts.append(K.gem((0, 0, 0.022), 0.012, "topaz"))
    parts.append(K.box(0.018, 0.09, 0.01, (0, 0.085, 0.008), "bronze", 0.003))
    for y in (0.11, 0.125):
        parts.append(K.box(0.03, 0.008, 0.01, (0.01, y, 0.008), "bronze", 0.002))
    return _ground(parts)


def tablet(s):
    parts = [M.bevel(K.box(0.14, 0.2, 0.03, (0, 0, 0.015), "ashstone"), 0.006, 2)]
    rng = np.random.default_rng(12)
    for i in range(7):
        for j in range(4):
            if rng.random() < 0.75:
                parts.append(K.box(0.018, 0.006, 0.003, (-0.045 + j * 0.03, -0.07 + i * 0.022, 0.031), "ember"))
    parts.append(K.box(0.05, 0.03, 0.03, (0.06, 0.09, 0.015), "ashstone").rot(Rz(25), (0.06, 0.09, 0.015)))
    return _ground(parts)


def crown_fragment(s):
    parts = []
    pts = [(0.06 * math.cos(a), 0.06 * math.sin(a), 0.02) for a in np.linspace(math.radians(-40), math.radians(110), 14)]
    parts.append(K.tube(pts, [(0.004, 0.018)] * len(pts), "gold", n=6, up=(0, 0, 1)))
    for a in np.linspace(math.radians(-30), math.radians(100), 4):
        c = (0.06 * math.cos(a), 0.06 * math.sin(a), 0.035)
        parts.append(K.cone_spike(c, (c[0] * 1.02, c[1] * 1.02, 0.075), 0.01, "gold"))
        parts.append(K.gem((c[0] * 1.08, c[1] * 1.08, 0.022), 0.006, "aether"))
    for p in parts:
        p.rot(Rx(-70))
    return _ground(parts)


def coins(s):
    parts = []
    rng = np.random.default_rng(7)
    z = 0.0
    for stack in range(3):
        cx, cy = [(0, 0), (0.032, 0.012), (-0.02, 0.028)][stack]
        n = [5, 3, 2][stack]
        for i in range(n):
            parts.append(K.lathe([(0, 0), (0.016, 0), (0.017, 0.002), (0.016, 0.004), (0, 0.004)], "gold", 14).move((cx + 0.002 * rng.random(), cy + 0.002 * rng.random(), i * 0.0042)))
    for k in range(5):
        a = rng.random() * 6.28
        d = 0.04 + 0.03 * rng.random()
        parts.append(K.lathe([(0, 0), (0.016, 0), (0.017, 0.002), (0.016, 0.004), (0, 0.004)], "gold", 14).rot(Rx(10 * rng.random())).move((d * math.cos(a), d * math.sin(a), 0.0)))
    return _ground(parts)


GOODS = {
    # the original consumables
    "health_potion": (bottle, {"shape": "round", "liquid": "red_liquid"}),
    "greater_health_potion": (bottle, {"shape": "bulb", "liquid": "red_liquid", "stopper": "wax", "filigree": "gold"}),
    "mana_potion": (bottle, {"shape": "tall", "liquid": "blue_liquid"}),
    "greater_mana_potion": (bottle, {"shape": "bulb", "liquid": "blue_liquid", "stopper": "wax", "wax": "navy", "filigree": "silver"}),
    "rejuvenation_elixir": (bottle, {"shape": "heart", "liquid": "purple_liquid", "stopper": "gem", "gem": "amethyst", "metal": "gold"}),
    "antidote": (pouch, {"mat": "linen", "spill": "white", "tie": "forest"}),
    "return_scroll": (scroll, {"seal": "tide", "ribbon": "navy"}),
    # bh-006 consumables
    "town_portal": (scroll, {"seal": "portal", "ribbon": "violet", "rod": "blackiron", "glow": "portal", "paper": "ochre"}),
    "minor_health_potion": (bottle, {"shape": "vial", "liquid": "red_liquid"}),
    "superior_health_potion": (bottle, {"shape": "facet", "liquid": "red_liquid", "stopper": "gem", "gem": "ruby", "filigree": "gold", "metal": "gold"}),
    "minor_mana_potion": (bottle, {"shape": "vial", "liquid": "blue_liquid", "tie": "navy"}),
    "superior_mana_potion": (bottle, {"shape": "facet", "liquid": "blue_liquid", "stopper": "gem", "gem": "sapphire", "filigree": "silver", "metal": "silver"}),
    "swiftfoot_tonic": (bottle, {"shape": "tall", "liquid": "green_liquid", "wing": "silver", "stopper": "cork", "tie": "forest"}),
    "ironskin_brew": (stein, {"mat": "stone", "band": "iron", "lid": "iron", "liquid": "silver_liquid"}),
    "berserker_draught": (bottle, {"shape": "gourd", "liquid": "orange_liquid", "glass": "horn", "stopper": "wax", "wax": "crimson", "tie": "redleather"}),
    "sages_infusion": (bottle, {"shape": "bulb", "liquid": "purple_liquid", "stopper": "metal", "metal": "silver", "label": "paper"}),
    "emberward_potion": (bottle, {"shape": "flask", "liquid": "amber_liquid", "label": "crimson", "stopper": "wax", "wax": "crimson"}),
    "frostward_potion": (bottle, {"shape": "flask", "liquid": "ice_liquid", "label": "navy", "stopper": "wax", "wax": "navy"}),
    "stormward_potion": (bottle, {"shape": "flask", "liquid": "yellow_liquid", "label": "black", "stopper": "wax", "wax": "ochre"}),
    "fortune_elixir": (bottle, {"shape": "round", "liquid": "gold_liquid", "stopper": "gem", "gem": "topaz", "emboss": "gold", "filigree": "gold"}),
    "scholars_tea": (tin, {"mat": "forest", "lid": "brass", "label": "paper"}),
    "featherweight_draught": (bottle, {"shape": "tall", "liquid": "silver_liquid", "feather": "white", "stopper": "cork"}),
    "whetstone": (stone_bar, {"mat": "slate", "wrap": "leather"}),
    "firebomb": (bomb, {"kind": "pot"}),
    "frost_flask": (bomb, {"kind": "frost"}),
    "smoke_pellet": (pouch, {"mat": "black", "pellets": "smoke", "tie": "rope"}),
    "phoenix_feather": (feather, {"mat": "flame", "tip": "flame_tip"}),
    # materials
    "iron_shard": (shards, {"mat": "iron", "count": 4}),
    "arcane_dust": (pouch, {"mat": "violet", "spill": "amethyst", "tie": "gold"}),
    "ember_core": (core, {"glow": "ember"}),
    "bone_fragment": (bone, {"broken": True}),
    "frost_crystal": (cluster, {"mat": "ice", "count": 6}),
    "storm_essence": (jar, {"inner": "storm", "bolt": True}),
    "shadow_silk": (bundle, {"mat": "black", "tie": "silver", "sheen": "shadow"}),
    "beast_hide": (bundle, {"mat": "hide", "roll": True, "tie": "leather"}),
    "aether_shard": (cluster, {"mat": "aether", "count": 3, "scale": 1.2, "base": "slate", "seed": 8}),
    # quest
    "quest_seal_key": (seal_key, {}),
    "quest_tablet": (tablet, {}),
    "quest_crown_fragment": (crown_fragment, {}),
    # gold drops
    "gold_pile": (coins, {}),
}


# ---- bh-007: ingredients, refined stock, champion essence, recipe scrolls --------------------------------------------

def fang(s):
    """Curved teeth lying on their side (wolf fang, orc tusk)."""
    parts = []
    big = s.get("big", 1.0)
    rng = np.random.default_rng(s.get("seed", 3))
    for k in range(s.get("count", 2)):
        a = k * 2.4 + rng.random() * 0.5
        L = 0.075 * big * (1.0 - 0.18 * k)
        pts = []
        for i in range(9):
            t = i / 8
            pts.append((L * t - L * 0.5, 0.02 * big * math.sin(t * 1.9), 0.012 * big + 0.01 * big * math.sin(math.pi * t)))
        radii = [0.011 * big * (1 - 0.9 * (i / 8)) + 0.0008 for i in range(9)]
        p = K.tube(pts, radii, s.get("mat", "bone"), n=10, up=(0, 0, 1))
        p.rot(Rz(math.degrees(a))).move((0.018 * k, -0.012 * k, 0))
        parts.append(p)
        if s.get("root"):
            c = np.array(pts[0])
            parts.append(K.sphere(radii[0] * 1.05, tuple(c), s["root"], 8, 6).rot(Rz(math.degrees(a))).move((0.018 * k, -0.012 * k, 0)))
    return _ground(parts)


def coil(s):
    """A coiled cord (ogre sinew)."""
    parts = []
    pts = []
    for i in range(60):
        t = i / 59
        a = t * 5.5 * math.pi
        r = 0.045 - 0.018 * t
        pts.append((r * math.cos(a), r * math.sin(a), 0.012 + 0.006 * math.sin(t * 9)))
    parts.append(K.tube(pts, [0.009] * len(pts), s.get("mat", "sinew"), n=8, up=(0, 0, 1)))
    parts.append(K.tube([pts[-1], (0.05, 0.03, 0.012), (0.075, 0.035, 0.008)], [0.009, 0.008, 0.005], s.get("mat", "sinew"), n=8, up=(0, 0, 1)))
    return _ground(parts)


def sprig(s):
    """A tied bundle of herb stems with leaves and flowers (silverleaf, mirebloom) or a gnarled root (emberroot)."""
    parts = []
    rng = np.random.default_rng(s.get("seed", 6))
    kind = s.get("kind", "leaf")
    if kind == "root":
        pts = [(-0.07, 0.0, 0.02), (-0.03, 0.01, 0.024), (0.0, -0.005, 0.022), (0.03, 0.008, 0.02), (0.07, -0.004, 0.014)]
        parts.append(K.tube(pts, [0.016, 0.018, 0.016, 0.012, 0.004], s.get("mat", "emberroot"), n=10, up=(0, 0, 1)))
        for k in range(6):
            c = np.array(pts[1 + k % 3])
            d = np.array([rng.random() - 0.5, rng.random() - 0.5, -0.4]) * 0.06
            parts.append(K.tube([c, c + d * 0.5, c + d], [0.005, 0.003, 0.001], s.get("mat", "emberroot"), n=5))
        for k in range(3):
            parts.append(K.box(0.01, 0.03, 0.002, (-0.07 - 0.005 * k, 0.01 * (k - 1), 0.035), "leaf").rot(Rx(60 + 10 * k), (-0.07, 0, 0.03)))
        return _ground(parts)
    # stems lying along X, fanning out from the tie
    for k in range(5):
        a = math.radians(-18 + 9 * k + rng.random() * 4)
        L = 0.11 + 0.03 * rng.random()
        p0 = np.array([-0.05, 0.0, 0.01])
        p1 = p0 + np.array([L * math.cos(a), L * math.sin(a), 0.008])
        parts.append(K.tube([p0, (p0 + p1) / 2 + np.array([0, 0, 0.006]), p1], [0.0025, 0.002, 0.0015], "stem", n=5))
        for j in range(3):
            t = 0.45 + 0.22 * j
            c = p0 + (p1 - p0) * t + np.array([0, 0, 0.006])
            side = 1 if (j + k) % 2 else -1
            leaf = K.sphere(0.012, (0, 0, 0), s.get("mat", "leaf"), 8, 5, scale=(1.8, 0.8, 0.18))
            leaf.rot(Rz(math.degrees(a) + side * 35)).move(tuple(c + np.array([0, side * 0.008, 0])))
            parts.append(leaf)
        if s.get("flower"):
            parts.append(K.sphere(0.009, tuple(p1 + np.array([0.004, 0, 0.004])), s["flower"], 8, 6, scale=(1, 1, 0.8)))
    parts.append(K.band(0.0, 0.009, 0.01, s.get("tie", "rope"), n=10).rot(Ry(90)).move((-0.035, 0.0, 0.012)))
    return _ground(parts)


def mushroom(s):
    """A small cluster of glowing caps."""
    parts = []
    for k, (x, y, h, r) in enumerate([(0.0, 0.0, 0.05, 0.028), (0.03, 0.015, 0.035, 0.02), (-0.025, 0.02, 0.03, 0.017)]):
        parts.append(K.lathe([(0, 0), (0.008, 0), (0.007, h), (0, h)], "capstem", 10).move((x, y, 0)))
        parts.append(K.lathe([(0, h - 0.004), (r, h - 0.006), (r * 0.9, h + 0.006), (r * 0.5, h + 0.014), (0, h + 0.016)], s.get("mat", "brightcap"), 14).move((x, y, 0)))
    parts.append(K.sphere(0.03, (0, 0.01, 0.0), "fur", 8, 5, scale=(1.8, 1.4, 0.25)))
    return _ground(parts)


def ingot(s):
    parts = []
    for i, (x, z) in enumerate([(-0.028, 0.0), (0.028, 0.0), (0.0, 0.028)]):
        if i >= s.get("count", 1):
            break
        prof = [(-0.05, 0.0), (0.05, 0.0), (0.042, 0.026), (-0.042, 0.026)]
        p = K.slab(prof, 0.034, s.get("mat", "steel"), axis="y")
        p.move((0, x if i < 2 else 0, z))
        parts.append(M.bevel(p, 0.002, 1))
    return _ground(parts)


def sigil(s):
    """A scorched cloth badge with an ember-stitched circle."""
    parts = [M.bevel(K.box(0.08, 0.1, 0.006, (0, 0, 0.003), s.get("mat", "black")), 0.003, 1).rot(Rz(8))]
    parts.append(K.ring_tube((0, 0, 0.007), 0.026, 0.0022, s.get("glow", "ember"), axis="z", n=20))
    parts.append(K.box(0.004, 0.034, 0.003, (0, 0, 0.007), s.get("glow", "ember")).rot(Rz(35)))
    parts.append(K.box(0.004, 0.034, 0.003, (0, 0, 0.007), s.get("glow", "ember")).rot(Rz(-35)))
    return _ground(parts)


def mote(s):
    """A drifting mote of light in a tiny wire cage."""
    parts = [K.sphere(0.022, (0, 0, 0.04), s.get("glow", "aether"), 12, 8)]
    for k in range(3):
        parts.append(K.ring_tube((0, 0, 0.04), 0.03, 0.0015, s.get("wire", "silver"), axis="z", n=18).rot(Rx(60 * k), (0, 0, 0.04)))
    parts.append(K.lathe([(0, 0), (0.018, 0), (0.02, 0.008), (0, 0.01)], s.get("wire", "silver"), 12))
    return _ground(parts)


def plate(s):
    """A hexagonal rune-carved shell plate, tilted up so its glowing runes face out."""
    parts = []
    hexo = [(0.065 * math.cos(math.radians(60 * k + 30)), 0.065 * math.sin(math.radians(60 * k + 30))) for k in range(6)]
    p = K.slab(hexo, 0.016, s.get("mat", "stone"), axis="z")
    parts.append(M.bevel(p, 0.004, 2))
    g = s.get("glow", "aether")
    parts.append(K.ring_tube((0, 0, 0.017), 0.034, 0.0028, g, axis="z", n=24))
    for k in range(3):
        parts.append(K.box(0.058, 0.005, 0.003, (0, 0, 0.018), g).rot(Rz(60 * k)))
    parts.append(K.gem((0, 0, 0.022), 0.009, g))
    for k in range(6):
        a = math.radians(60 * k)
        parts.append(K.sphere(0.004, (0.052 * math.cos(a), 0.052 * math.sin(a), 0.017), "bronze", 6, 4))
    for q in parts:
        q.rot(Rx(28))
    return _ground(parts)


GOODS.update({
    "wolf_fang": (fang, {"mat": "bone", "count": 2}),
    "goblin_resin": (jar, {"inner": "resin", "glass": "clay", "lid": "rope"}),
    "orc_tusk": (fang, {"mat": "tusk", "count": 1, "big": 1.8, "root": "horn", "seed": 5}),
    "ogre_sinew": (coil, {"mat": "sinew"}),
    "grave_dust": (pouch, {"mat": "wool", "spill": "smoke", "tie": "rope"}),
    "ghoul_bile": (bottle, {"shape": "gourd", "liquid": "bile", "glass": "horn", "stopper": "cork"}),
    "ash_sigil": (sigil, {"mat": "black", "glow": "ember"}),
    "wisp_mote": (mote, {"glow": "aether", "wire": "silver"}),
    "stolen_linen": (bundle, {"mat": "linen", "tie": "rope"}),
    "rune_plate": (plate, {"mat": "stone", "glow": "aether"}),
    "silverleaf": (sprig, {"mat": "silverleaf", "flower": "white", "tie": "rope", "seed": 11}),
    "mirebloom": (sprig, {"mat": "leaf", "flower": "mirebloom", "tie": "reed", "seed": 12}),
    "emberroot": (sprig, {"kind": "root", "mat": "emberroot", "seed": 13}),
    "brightcap": (mushroom, {"mat": "brightcap"}),
    "steel_ingot": (ingot, {"mat": "steel", "count": 1}),
    "cured_leather": (bundle, {"mat": "leather", "roll": True, "tie": "darkleather"}),
    "champion_essence": (core, {"glow": "holy", "crust": "blackiron"}),
    "recipe_berserker": (scroll, {"seal": "wax_red", "ribbon": "crimson", "paper": "paper"}),
    "recipe_sage": (scroll, {"seal": "amethyst", "ribbon": "violet", "paper": "paper"}),
    "recipe_fortune": (scroll, {"seal": "topaz", "ribbon": "ochre", "paper": "paper"}),
    "recipe_phoenix": (scroll, {"seal": "flame", "ribbon": "crimson", "paper": "ochre", "glow": "ember"}),
    "recipe_champion_weapon": (scroll, {"seal": "blackiron", "ribbon": "navy", "paper": "paper", "rod": "blackiron"}),
    "recipe_champion_armor": (scroll, {"seal": "bronze", "ribbon": "forest", "paper": "paper", "rod": "blackiron"}),
    "recipe_champion_trinket": (scroll, {"seal": "gold", "ribbon": "teal", "paper": "paper"}),
    "recipe_aetherforged": (scroll, {"seal": "aether", "ribbon": "violet", "paper": "ochre", "rod": "blackiron", "glow": "aether"}),
})


# ---- bh-012: Relic Caches, the Soul Ember and the five dungeon materials -----------------------------------------------

def coffer(s):
    """A small iron-banded relic coffer; a glowing seam under the lid and a gem lock in the front."""
    body, trim, glow = s.get("mat", "darkwood"), s.get("trim", "iron"), s.get("glow", "holy")
    parts = [M.bevel(K.box(0.11, 0.075, 0.055, (0, 0, 0.0275), body), 0.004, 1)]
    lid = K.lathe([(0, 0), (0.0375, 0), (0.0375, 0.012), (0.03, 0.026), (0.0, 0.03)], body, 16)
    lid.rot(Ry(90)).V[:, 0] *= 1.47
    parts.append(lid.move((0, 0, 0.058)))
    for x in (-0.042, 0.0, 0.042):
        parts.append(K.box(0.008, 0.079, 0.059, (x, 0, 0.0295), trim))
    parts.append(K.box(0.112, 0.077, 0.004, (0, 0, 0.057), glow))
    parts.append(K.gem((0, -0.04, 0.03), 0.009, s.get("gem", "topaz")))
    for x in (-0.053, 0.053):
        for y in (-0.036, 0.036):
            parts.append(K.sphere(0.004, (x, y, 0.004), trim, 6, 4))
    return _ground(parts)


def pearl(s):
    """A grey pearl in a half-open shell."""
    parts = [K.lathe([(0, 0), (0.045, 0.004), (0.05, 0.012), (0.04, 0.016), (0, 0.012)], s.get("shell", "bone"), 18)]
    top = K.lathe([(0, 0), (0.045, 0.004), (0.05, 0.012), (0.04, 0.016), (0, 0.012)], s.get("shell", "bone"), 18)
    top.rot(Rx(-120)).move((0, 0.048, 0.02))
    parts.append(top)
    parts.append(K.sphere(0.019, (0, 0.004, 0.03), s.get("mat", "pearl"), 14, 10))
    parts.append(K.sphere(0.008, (0.01, -0.01, 0.042), s.get("glow", "tide"), 8, 6))
    return _ground(parts)


GOODS.update({
    "relic_cache_worn": (coffer, {"mat": "darkwood", "trim": "rust", "glow": "earth", "gem": "onyx"}),
    "relic_cache_gilded": (coffer, {"mat": "redwood", "trim": "gold", "glow": "holy", "gem": "topaz"}),
    "relic_cache_radiant": (coffer, {"mat": "blackiron", "trim": "paleg", "glow": "portal", "gem": "amethyst"}),
    "soul_ember": (mote, {"glow": "tide", "wire": "paleg"}),
    "glowcap_spore": (pouch, {"mat": "forest", "spill": "venom", "tie": "rope"}),
    "tide_pearl": (pearl, {}),
    "slag_ember": (core, {"glow": "ember", "crust": "blackiron"}),
    "rime_shard": (cluster, {"mat": "ice", "count": 2, "scale": 1.7, "base": "slate", "seed": 21}),
    "star_glass": (cluster, {"mat": "portal", "count": 3, "scale": 1.2, "base": "brass", "seed": 33}),
})
