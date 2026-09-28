"""Brakka Durnhelm, the Forgemaster (BOSS; Builder C, bh-012, Emberforge Depths). Dwarf-king proportions (~2.1 m
authored to the chimney tops, short thick legs, a huge barrel chest and arms; the game scales it ~2x): blackened
forge-plate armour studded with glowing rivets, a furnace backpack with a glowing grate and two tall smoking chimneys,
a braided beard of iron wire with embers caught in it, a crowned helm whose visor slit glows orange, and a colossal
two-handed forge hammer (greatsword clips, weapon.R). Silhouette keys at gameplay distance: the twin chimneys and the
hammer head."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, dome, fist  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import kit_ember as E  # noqa: E402

PROPS = proportions(
    1.0,
    pelvis_h=0.78, hip_h=0.74, knee_h=0.42, ankle_h=0.1, hip_x=0.17, ball_fwd=0.18, ball_h=0.03, toe_len=0.09,
    heel_back=0.07,
    hips_len=0.12, spine_len=0.22, chest_len=0.42, neck_len=0.1, head_len=0.26,
    clav_x0=0.06, clav_drop=0.08, shoulder_x=0.37, upper_len=0.36, fore_len=0.34, hand_len=0.13, grip_x=0.095,
    grip_drop=0.024,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 2.3

PALETTE = "forgemaster"
PALETTE_COLORS = {
    "BH_DarkSteel": ((0.075, 0.07, 0.07), 1.0, 0.45, None, 0.0, 1.0),     # blackened forge-plate
    "BH_Steel": ((0.3, 0.29, 0.28), 1.0, 0.4, None, 0.0, 1.0),            # iron-wire beard, edges
    "BH_Bronze": ((0.42, 0.24, 0.1), 1.0, 0.42, None, 0.0, 1.0),          # crown, trims, buckle
    "BH_Leather": ((0.13, 0.075, 0.04), 0.0, 0.7, None, 0.0, 1.0),        # straps, gambeson skirt
    "BH_Cloth_Primary": ((0.2, 0.05, 0.03), 0.0, 0.9, None, 0.0, 1.0),    # smouldering red undercoat
    "BH_Rust": ((0.2, 0.1, 0.05), 0.55, 0.78, None, 0.0, 1.0),            # furnace box, chimneys
    "BH_Stone": ((0.1, 0.09, 0.085), 0.0, 0.9, None, 0.0, 1.0),           # soot / coal
    "BH_Shadow": ((0.02, 0.016, 0.015), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": E.EMBER,
}
CLIPS = ["gs_1", "gs_2", "gs_heavy", "boss_slam", "boss_sweep", "boss_charge", "boss_roar", "boss_summon",
         "cast_heavy"]

zh, zs, zc, zn, zhd = L["hips"], L["spine"], L["chest"], L["neck"], L["head"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows(g=0.0):
    return [
        (zh - 0.1, 0.26 + g, 0.22 + g, 0.2 + g, 0.0, 0.0),
        (zh + 0.04, 0.29 + g, 0.27 + g, 0.21 + g, 0.04, 0.0),
        (zs + 0.08, 0.32 + g, 0.31 + g, 0.23 + g, 0.06, -0.01),     # belly
        (zc + 0.05, 0.36 + g, 0.32 + g, 0.26 + g, 0.06, -0.01),
        (zc + 0.22, 0.4 + g, 0.31 + g, 0.28 + g, 0.05, 0.0),        # barrel chest
        (zn - 0.1, 0.42 + g, 0.27 + g, 0.3 + g, 0.02, 0.02),
        (zn - 0.02, 0.34 + g, 0.2 + g, 0.24 + g, 0.0, 0.03),
        (zn + 0.04, 0.16 + g, 0.13 + g, 0.14 + g, 0.0, 0.03),
    ]


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    rows = torso_rows()
    # red undercoat body, plated over
    V, F = torso_loft(rows, n=24, p=2.4, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Cloth_Primary", name="torso"), weights=TW)
    plate(body, rows, TW)
    belt_and_faulds(body)
    head(body)
    beard(body)
    backpack(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)
    K.weapon_to_socket(body, "R", great_hammer())


def plate(body, rows, TW):
    add = body.add
    pr = torso_rows(0.025)
    # breastplate (chest) + belly plate (spine), split so the torso can bend
    br = [r for r in pr if r[0] >= zc - 0.02]
    V, F = torso_loft(br, n=28, p=2.6, cap0=False, cap1=False)
    add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="breast"), 0.01, 1),
        weights=K.zspec_w([(zc + 0.02, "spine"), (zc + 0.12, "chest")]))
    bl = torso_rows(0.03)
    bl = [(z, rx, ryf, ryb, k, cy) for (z, rx, ryf, ryb, k, cy) in bl if zh <= z <= zc + 0.06]
    V, F = torso_loft(bl, n=28, p=2.6, cap0=False, cap1=False)
    add(M.Part(V, F, "BH_DarkSteel", name="belly"), weights=K.zspec_w([(zs - 0.02, "hips"), (zs + 0.06, "spine"),
                                                                       (zc - 0.02, "spine"), (zc + 0.06, "chest")]))
    # bronze trim ridges + glowing rivets along the plate edges and the sternum
    for z in (zc + 0.03, zn - 0.06):
        ring = [E.torso_point(pr, f, z, 0.012, 2.6)[0] for f in np.linspace(0, 1, 29)]
        add(K.rtube(ring, 0.016, "BH_Bronze", n=5, cap=False), "chest")
        for f in np.linspace(0, 1, 14, endpoint=False):
            q, n = E.torso_point(pr, f, z, 0.026, 2.6)
            add(E.rivet_on(q, n, 0.017, "BH_Emissive"), "chest")
    for z in np.linspace(zc + 0.1, zn - 0.14, 4):
        q, n = E.torso_point(pr, 0.0, z, 0.012, 2.6)
        add(E.rivet_on(q, n, 0.02, "BH_Emissive"), "chest")
    # anvil emblem on the breast (bronze) with a glowing seam
    y0 = E.torso_point(pr, 0.0, zc + 0.24, 0.0, 2.6)[0][1] - 0.02
    anv = np.array([(-0.12, 0.05), (0.12, 0.05), (0.08, 0.0), (0.04, -0.01), (0.05, -0.07), (-0.05, -0.07),
                    (-0.04, -0.01), (-0.16, 0.02)])
    V, F = M.prism(anv[::-1], 0.02, axis="y", center=0.0)
    add(M.Part(V, F, "BH_Bronze", name="anvil").move((0, y0, zc + 0.24)), "chest")
    add(K.rtube([(-0.08, y0 - 0.012, zc + 0.26), (0.08, y0 - 0.012, zc + 0.26)], 0.008, "BH_Emissive", n=4), "chest")
    # heat seams between the plate lames on the belly
    for z in (zs + 0.02, zs + 0.13):
        ring = [E.torso_point(bl, f, z, 0.004, 2.6)[0] for f in np.linspace(-0.3, 0.3, 13)]
        add(K.rtube(ring, 0.01, "BH_Emissive", n=4),
            weights=K.zspec_w([(zs - 0.02, "hips"), (zs + 0.06, "spine")]))


def belt_and_faulds(body):
    add = body.add
    z = zh + 0.02
    rows = torso_rows(0.045)
    ring = [E.torso_point(rows, f, z, 0.0, 2.4)[0] for f in np.linspace(0, 1, 29)]
    V, F = M.tube(ring, [(0.03, 0.05)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False, p=3)
    add(M.Part(V, F, "BH_Leather", name="belt"), "hips")
    yb = E.torso_point(rows, 0.0, z, 0.03, 2.4)[0][1]
    V, F = M.box(0.18, 0.04, 0.13, center=(0, yb, z))
    add(M.bevel(M.Part(V, F, "BH_Bronze", name="buckle"), 0.01, 1), "hips")
    V, F = M.box(0.1, 0.02, 0.06, center=(0, yb - 0.025, z))
    add(M.Part(V, F, "BH_Emissive", name="buckle_glow"), "hips")
    # plated faulds: front / side lames over the short thighs (hips -> thighs)
    for i, f in enumerate(np.linspace(-0.3, 0.3, 7)):
        q, n = E.torso_point(rows, f % 1.0, z - 0.04, 0.0, 2.4)
        side = 1 if q[0] >= 0 else -1
        lb = "thigh.L" if side > 0 else "thigh.R"
        for k in range(2):
            c = q + n * (0.012 + 0.012 * k) + np.array([0, 0, -0.1 - 0.11 * k])
            ang = math.degrees(math.atan2(n[0], -n[1]))
            p = M.bevel(M.Part(*M.box(0.15, 0.03, 0.13), "BH_DarkSteel", name="fauld"), 0.006, 1)
            p.rot(Rz(ang) @ Rx(12)).move(c)
            wl = min(1.0, abs(q[0]) / 0.18) * 0.5
            add(p, weights=lambda V, lb=lb, wl=wl, k=k: [{"hips": 1 - wl - 0.15 * k, lb: wl + 0.15 * k}] * len(V))
            add(E.rivet_on(c + n * 0.018 + np.array([0, 0, 0.04]), n, 0.011, "BH_Emissive"),
                weights=lambda V, lb=lb, wl=wl, k=k: [{"hips": 1 - wl - 0.15 * k, lb: wl + 0.15 * k}] * len(V))
    # leather skirt under the faulds at the back
    def fn(u, v):
        a = math.pi * (0.15 + 0.7 * u)
        r = 1.0 + 0.1 * v
        return (0.3 * r * math.cos(a), 0.24 * r * math.sin(a) + 0.02, zh + 0.02 - 0.3 * v)
    V, F = M.grid(fn, 9, 4)
    sk = M.Part(V, F, "BH_Leather", name="skirt")
    sk.flip()
    add(M.solidify(sk, 0.012, offset=1.0), weights=K.seat_w(body, zh, zh - 0.3, 0.7, center_w=0.1))


def head(body):
    add = body.add
    z0 = zhd
    # neck + head core (mostly hidden by the helm and beard)
    V, F = M.tube([(0, 0.03, zn - 0.04), (0, 0.0, zn + 0.05), (0, -0.02, z0 + 0.05)],
                  [(0.13, 0.12), (0.12, 0.11), (0.12, 0.12)], n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Leather", name="neck"),
        weights=K.zspec_w([(zn - 0.01, "chest"), (zn + 0.04, "neck"), (z0 + 0.0, "neck"), (z0 + 0.04, "head")]))
    c = np.array([0, -0.01, z0 + 0.12])
    # helm: dome + face plate with a glowing visor slit + cheek guards
    V, F = dome(c + (0, 0, -0.02), (0, 0, 1), 0.155, a_max=100, n=22, rings=8, scale=(1.0, 1.08, 1.05))
    add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="helm"), 0.012, offset=-1.0), "head")
    V, F = M.lathe([(0, -0.12), (0.16, -0.12), (0.17, -0.02), (0.16, 0.0), (0, 0.0)], 22)
    face = M.Part(V, F, "BH_DarkSteel", name="helmbase").scale((1.0, 1.08, 1.0)).move(c + (0, 0, 0.02))
    add(face, "head")
    yv = c[1] - 0.176
    V, F = M.box(0.26, 0.03, 0.042, center=(0, yv + 0.002, c[2] - 0.02))
    add(M.Part(V, F, "BH_Emissive", name="visor"), "head")
    V, F = M.box(0.03, 0.03, 0.08, center=(0, yv + 0.004, c[2] - 0.075))
    add(M.Part(V, F, "BH_Emissive", name="visor_v"), "head")
    V, F = M.box(0.34, 0.03, 0.02, center=(0, yv - 0.006, c[2] + 0.005))
    add(M.bevel(M.Part(V, F, "BH_Bronze", name="brow"), 0.005, 1), "head")
    V, F = M.tube([(0, yv - 0.012, c[2] - 0.1), (0, yv - 0.02, c[2] + 0.02), (0, -0.05, c[2] + 0.17),
                   (0, 0.1, c[2] + 0.12)], [(0.014, 0.014)] * 4, n=5, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Bronze", name="crest"), "head")
    # crown: bronze band with seven spikes, glowing studs
    zc0 = c[2] + 0.07
    ring = [(0.168 * math.cos(a), 0.18 * math.sin(a) - 0.01, zc0) for a in np.linspace(0, 2 * math.pi, 25)]
    V, F = M.tube(ring, [(0.012, 0.03)] * len(ring), n=4, up=(0, 0, 1), cap0=False, cap1=False, p=4)
    add(M.Part(V, F, "BH_Bronze", name="crown"), "head")
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * 0.42
        b = np.array([0.17 * math.cos(a), 0.18 * math.sin(a) - 0.01, zc0 + 0.02])
        h = 0.14 if k == 3 else (0.1 if k in (2, 4) else 0.075)
        add(K.cone(b, b + np.array([0.02 * math.cos(a), 0.02 * math.sin(a), h]), 0.026, "BH_Bronze", n=4), "head")
        add(K.blob(b + np.array([0.012 * math.cos(a), 0.012 * math.sin(a), -0.012]), 0.012, "BH_Emissive", n=6,
                   rings=4), "head")


def beard(body):
    """Iron-wire beard: a big wedge mass under the helm and three long braids with iron rings and ember beads."""
    add = body.add
    z0 = zhd
    bw = K.zspec_w([(zn - 0.2, "chest"), (z0 - 0.02, "neck"), (z0 + 0.04, "head")])
    V, F = M.tube([(0, -0.15, z0 + 0.04), (0, -0.24, z0 - 0.05), (0, -0.33, z0 - 0.16), (0, -0.4, zn - 0.2)],
                  [(0.15, 0.07), (0.18, 0.08), (0.17, 0.07), (0.09, 0.04)], n=14, up=(0, -1, 0))
    b = M.Part(V, F, "BH_Steel", name="beard")
    E.jitter(b, 0.006, seed=4)
    add(b, weights=bw)
    # wire strands (grooves) down the mass
    for x in np.linspace(-0.11, 0.11, 6):
        add(K.rtube([(x, -0.25, z0 - 0.02), (x * 1.1, -0.35, z0 - 0.14), (x * 0.6, -0.42, zn - 0.18)],
                    0.008, "BH_DarkSteel", n=4), weights=bw)
    cw = K.zspec_w([(zn - 0.4, "chest"), (zn - 0.1, "chest"), (z0 + 0.0, "neck")])
    for i, x in enumerate((-0.09, 0.0, 0.09)):
        top = np.array([x, -0.4, zn - 0.16])
        ln = 0.42 if i == 1 else 0.34
        pts = [top + (0, -0.02 * t, -ln * t) for t in np.linspace(0, 1, 9)]
        fr = torso_rows(0.075)
        pts = [np.array([p[0], min(p[1], K.front_of(fr, p[0], p[2], p=2.4)), p[2]]) for p in pts]
        # braid: two twisted strands
        for ph in (0.0, math.pi):
            tw = [np.asarray(p) + 0.017 * np.array([math.cos(8 * t + ph), 0.0, 0.0]) for t, p in
                  zip(np.linspace(0, 3.2, len(pts)), pts)]
            add(K.rtube(tw, 0.02, "BH_Steel", n=5), weights=cw)
        for t in (0.35, 0.7):
            q = np.asarray(pts[int(t * (len(pts) - 1))])
            add(K.rtube([q + (0, 0, -0.018), q + (0, 0, 0.018)], 0.03, "BH_Bronze", n=7), weights=cw)
        add(K.blob(np.asarray(pts[-1]) + (0, 0, -0.02), 0.028, "BH_Emissive", n=7, rings=5), weights=cw)
    for (x, z) in ((-0.07, z0 - 0.06), (0.06, z0 - 0.1), (0.0, zn - 0.08), (0.1, z0 - 0.0), (-0.12, zn - 0.02)):
        add(K.blob((x, K.front_of(torso_rows(0.1), x, z, p=2.4) if z < zn else -0.3, z), 0.016, "BH_Emissive", n=6, rings=4), weights=bw)


def backpack(body):
    """Furnace backpack: iron box on the back with a glowing grate and two tall chimneys (rigid on the chest)."""
    add = body.add
    rows = torso_rows()
    yb = max(r[3] + r[5] for r in rows) + 0.02
    c = np.array([0, yb + 0.2, zc + 0.2])
    V, F = M.box(0.62, 0.36, 0.58, center=c)
    add(M.bevel(M.Part(V, F, "BH_Rust", name="furnace"), 0.03, 2), "chest")
    for dz in (-0.2, 0.0, 0.2):
        V, F = M.box(0.66, 0.39, 0.04, center=c + (0, 0, dz))
        add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="hoop"), 0.008, 1), "chest")
        for sx in (1, -1):
            for dy in (-0.12, 0.0, 0.12):
                add(E.rivet_on(c + (sx * 0.33, dy, dz), (sx, 0, 0), 0.014, "BH_Emissive"), "chest")
    # grate on the back face: glowing coals behind iron bars
    yg = c[1] + 0.18
    V, F = M.box(0.36, 0.02, 0.28, center=(0, yg + 0.002, c[2] - 0.05))
    add(M.Part(V, F, "BH_Emissive", name="coals"), "chest")
    for x in np.linspace(-0.15, 0.15, 6):
        V, F = M.box(0.025, 0.035, 0.3, center=(x, yg + 0.016, c[2] - 0.05))
        add(M.Part(V, F, "BH_DarkSteel", name="bar"), "chest")
    for (sx, sz, dx, dz) in ((0.44, 0.04, 0, 0.17), (0.44, 0.04, 0, -0.17), (0.04, 0.34, 0.2, 0), (0.04, 0.34, -0.2, 0)):
        V, F = M.box(sx, 0.045, sz, center=(dx, yg + 0.016, c[2] - 0.05 + dz))
        add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="grateframe"), 0.005, 1), "chest")
    # coal heap glowing on top between the chimneys
    add(K.blob(c + (0, 0.04, 0.3), 0.12, "BH_Stone", scale=(1.6, 1.0, 0.45), n=10, rings=5), "chest")
    for k, (dx, dy) in enumerate(((0.05, 0.02), (-0.07, 0.06), (0.0, -0.05))):
        add(K.blob(c + (dx, 0.04 + dy, 0.34), 0.035, "BH_Emissive", n=6, rings=4), "chest")
    # chimneys: tall, slightly flared, glowing at the mouth, tilted a little outward
    for sx in (1, -1):
        b = c + np.array([sx * 0.2, 0.06, 0.27])
        top = b + np.array([sx * 0.07, 0.06, 0.62])
        pts = [b, b + (top - b) * 0.5, top]
        V, F = M.tube(pts, [(0.075, 0.075), (0.07, 0.07), (0.075, 0.075)], n=12, up=(0, -1, 0), cap0=False, cap1=False)
        add(M.solidify(M.Part(V, F, "BH_Rust", name="chimney"), 0.012, offset=-1.0), "chest")
        for t in (0.25, 0.65):
            q = b + (top - b) * t
            V, F = M.tube([q - (0, 0, 0.02), q + (0, 0, 0.02)], [(0.088, 0.088)] * 2, n=12, up=(0, -1, 0))
            add(M.Part(V, F, "BH_DarkSteel", name="chimband"), "chest")
        # flared cap + glowing throat + smoke-stained cowl
        V, F = M.lathe([(0.075, 0.0), (0.11, 0.05), (0.12, 0.07), (0.1, 0.075), (0.065, 0.02)], 12, cap=False)
        add(M.Part(V, F, "BH_DarkSteel", name="chimcap").move(top), "chest")
        V, F = M.lathe([(0.0, -0.08), (0.066, -0.06), (0.068, 0.02), (0.0, 0.0)], 10)
        add(M.Part(V, F, "BH_Emissive", name="throat").move(top), "chest")
        for p in E.flame(top + (0, 0, 0.0), 0.16, 0.045, tongues=3, seed=11 + sx):
            add(p, "chest")
    # straps over the shoulders to the front plate
    for sx in (1, -1):
        pts = [c + (sx * 0.22, -0.18, 0.28), (sx * 0.26, 0.05, zn + 0.03), (sx * 0.27, -0.2, zn - 0.02),
               (sx * 0.24, -0.33, zn - 0.16)]
        add(K.rtube(pts, (0.035, 0.014), "BH_Leather", n=4, up=(0, 0, 1)), "chest")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    K.arm(body, s, [(0.13, 0.13), (0.12, 0.12), (0.1, 0.1), (0.1, 0.1), (0.1, 0.1), (0.075, 0.075)],
          "BH_Cloth_Primary", n=12)
    # huge layered pauldron (on the shoulder bone)
    pc = sh + np.array([sx * 0.02, 0.0, 0.08])
    for k, (r, dz) in enumerate(((0.21, -0.02), (0.185, -0.09), (0.16, -0.15))):
        V, F = dome(pc + (sx * 0.03 * k, 0, dz), (sx * 0.45, 0, 1), r, a_max=75, n=18, rings=5,
                    scale=(1.0, 1.1, 0.8))
        add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="pauldron"), 0.018, offset=1.0),
            weights=lambda V, s=s: [{"shoulder." + s: 0.7, "upper_arm." + s: 0.3}] * len(V))
    ring = [pc + np.array([sx * 0.02, 0, 0]) + R @ np.array([0.205 * math.cos(a), 0.225 * math.sin(a), 0.0])
            for R in [Ry(-sx * 24)] for a in np.linspace(0, 2 * math.pi, 21)]
    add(K.rtube([q + (0, 0, 0.06) for q in ring], 0.014, "BH_Bronze", n=4, cap=False),
        weights=lambda V, s=s: [{"shoulder." + s: 0.7, "upper_arm." + s: 0.3}] * len(V))
    for a in np.linspace(0, 2 * math.pi, 8, endpoint=False):
        q = pc + np.array([sx * 0.02, 0, 0.06]) + Ry(-sx * 24) @ np.array([0.175 * math.cos(a), 0.19 * math.sin(a), 0.0])
        add(K.blob(q + (0, 0, 0.03), 0.017, "BH_Emissive", n=6, rings=4),
            weights=lambda V, s=s: [{"shoulder." + s: 0.7, "upper_arm." + s: 0.3}] * len(V))
    # rerebrace + couter + vambrace
    add(body.limb(ua, [(0.35, 0.14, 0.14), (0.95, 0.125, 0.125)], "BH_DarkSteel", n=12), ua)
    add(K.blob(el, 0.13, "BH_DarkSteel", scale=(1, 1, 1), n=12, rings=6), fa)
    add(body.limb(fa, [(0.12, 0.125, 0.13), (0.6, 0.14, 0.145), (0.95, 0.15, 0.15)], "BH_DarkSteel", n=12), fa)
    V, F = M.tube([el + (wr - el) * 0.92, wr + (wr - el) * 0.08], [(0.165, 0.165)] * 2, n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Bronze", name="cuff"), fa)
    A = body.axes(fa)
    fl = body.p["fore_len"]
    for u in (0.35, 0.6, 0.85):
        add(E.rivet_on(body.lpt(fa, [(0, u * fl, 0.15)])[0], A[:, 2], 0.016, "BH_Emissive"), fa)
    # big gauntleted fist
    for prt in fist(body, s, "BH_DarkSteel", "BH_DarkSteel", gauntlet=True, scale=1.75):
        add(prt, ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh = "thigh." + s, "shin." + s
    K.leg(body, s, [(0.17, 0.17), (0.16, 0.16), (0.135, 0.135), (0.13, 0.13), (0.13, 0.13), (0.095, 0.095)],
          "BH_Leather", n=12, top_up=0.06)
    k, a = body.head(sh), body.tail(sh)
    add(K.blob(k + (0, -0.06, 0.01), 0.1, "BH_DarkSteel", scale=(1.1, 0.8, 1.0), n=10, rings=6), sh)
    add(body.limb(sh, [(0.12, 0.15, 0.15), (0.5, 0.155, 0.16), (0.88, 0.12, 0.125)], "BH_DarkSteel", n=12), sh)
    add(E.rivet_on(k + (0, -0.13, -0.12), (0, -1, 0), 0.018, "BH_Emissive"), sh)
    # heavy square sabatons
    hx = body.p["hip_x"] * sx
    V, F = M.box(0.22, 0.3, 0.1, center=(hx, -0.03, 0.05))
    add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="sabaton"), 0.02, 1), "foot." + s)
    V, F = M.box(0.2, 0.13, 0.08, center=(hx, -0.24, 0.04))
    add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="toecap"), 0.02, 1), "toe." + s)
    V, F = M.box(0.23, 0.44, 0.02, center=(hx, -0.08, 0.01))
    add(M.Part(V, F, "BH_Shadow", name="sole"), "foot." + s)


def great_hammer():
    """Colossal two-handed forge hammer. Weapon space: grip at origin (right hand), +Z along the haft; the left hand
    grips lower on the haft. Head faces +-X: a glowing flat striking face on +X, an anvil-horn peen on -X."""
    parts = []
    V, F = M.lathe([(0, -0.62), (0.04, -0.62), (0.045, -0.57), (0.034, -0.52), (0.034, 1.1), (0, 1.12)], 10)
    parts.append(E.P(V, F, "BH_DarkSteel", "haft"))
    for z0, z1 in ((-0.5, -0.18), (-0.12, 0.14)):
        V, F = M.lathe([(0, z0), (0.038, z0), (0.038, z1), (0, z1)], 10)
        parts.append(E.P(V, F, "BH_Leather", "wrap"))
    for z in (0.3, 0.6, 0.85):
        V, F = M.lathe([(0, z - 0.025), (0.046, z - 0.025), (0.05, z), (0.046, z + 0.025), (0, z + 0.025)], 10)
        parts.append(E.P(V, F, "BH_Bronze", "band"))
    V, F = M.lathe([(0, -0.7), (0.06, -0.66), (0.065, -0.62), (0.03, -0.6), (0, -0.6)], 10)
    parts.append(E.P(V, F, "BH_Bronze", "pommel"))
    zc = 1.12
    V, F = M.box(0.46, 0.3, 0.32, center=(0.03, 0, zc))
    parts.append(M.bevel(E.P(V, F, "BH_DarkSteel", "block"), 0.025, 2))
    V, F = M.box(0.1, 0.36, 0.38, center=(0.28, 0, zc))
    parts.append(M.bevel(E.P(V, F, "BH_DarkSteel", "face"), 0.02, 1))
    V, F = M.box(0.02, 0.3, 0.32, center=(0.337, 0, zc))
    parts.append(E.P(V, F, "BH_Emissive", "hotface"))
    rings = [np.array([(x, y, zc + z) for y, z in ((w, t), (-w, t), (-w, -t), (w, -t))])
             for x, w, t in ((-0.2, 0.14, 0.15), (-0.3, 0.11, 0.1), (-0.4, 0.07, 0.05), (-0.46, 0.03, 0.02))]
    V, F = M.loft(rings)
    parts.append(E.P(V, F, "BH_DarkSteel", "horn"))
    for sy in (1, -1):
        # glowing rune channel on each broad side + bronze corner plates
        y = sy * 0.152
        parts.append(K.rtube([(-0.15, y, zc - 0.08), (-0.02, y, zc + 0.1), (0.12, y, zc - 0.08), (0.2, y, zc + 0.06)],
                             0.014, "BH_Emissive", n=4))
        for sz in (1, -1):
            V, F = M.box(0.1, 0.02, 0.1, center=(0.2, sy * 0.19, zc + sz * 0.15))
            parts.append(E.P(V, F, "BH_Bronze", "corner"))
    V, F = M.lathe([(0, zc - 0.2), (0.07, zc - 0.2), (0.07, zc + 0.19), (0, zc + 0.19)], 10)
    parts.append(E.P(V, F, "BH_Bronze", "collar"))
    return parts
