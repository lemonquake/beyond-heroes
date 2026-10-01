"""Kalvex, the Engine Heart (bh-029, Builder M6, BOSS of the Obsidian Engine): the Engine's own warden, a ~4.2 m
construct of knapped black glass on a frame of old copper. Its chest IS a furnace: a great round firebox ringed in
copper and riveted plates, a grille of heavy bars across its mouth and behind them the molten core (BH_WeakPoint:
"strike the heart through the grille"), with an ash-mouth of real orange coals glowing under it. Two tall stepped
smokestacks rise behind its shoulders (the silhouette key from the gameplay camera), a ring of shard spikes between
them. A small glass head sunk between massive shoulders, its face a copper grille with white light burning behind the
bars, a stepped crown of glass. Its arms are pistons: copper cylinder housings on the upper arms, polished piston rods
driving out of copper sleeves on the forearms, slave pistons alongside; each forearm ends in a huge hammer head (a
copper-banded block with a knapped obsidian striking face and a white glyph). A segmented copper crank-drum waist,
glass tassets, pillar legs with shin pistons on slab feet. White molten seams through the glass everywhere (bh-029:
every glow white; only the ash-mouth fire is orange).

Built at true size on the shared skeleton with custom construct proportions (head top ~4.15 m, stacks ~4.6 m); every
part rigid to one bone; no weapon sockets (the hammers are the hands).
Clips: boss_charge boss_slam boss_summon cast_area cast_heavy cast_ultimate gs_1 (+ boss_roar, boss_sweep, gs_2)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as GK  # noqa: E402
import enemy_rune_golem as RG  # noqa: E402
import kit_a_common as A  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402
import enemy_obsidian_golem as OG  # noqa: E402
from enemy_obsidian_golem import Facet, flimb, fprism, seam, jag, addp  # noqa: E402

PROPS = proportions(
    2.2,
    pelvis_h=1.72, hip_h=1.64, knee_h=0.9, ankle_h=0.21, hip_x=0.4, ball_fwd=0.42, ball_h=0.07, toe_len=0.2,
    heel_back=0.18,
    hips_len=0.3, spine_len=0.46, chest_len=1.02, neck_len=0.1, head_len=0.52,
    clav_x0=0.18, clav_drop=0.3, shoulder_x=0.98, upper_len=0.78, fore_len=0.86, hand_len=0.32, grip_x=0.2,
    grip_drop=0.04,
)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 4.9

PALETTE = "engine_heart"
PALETTE_COLORS = {
    "BH_Stone": OG.GLASS,                                                    # knapped black glass
    "BH_Horn": ((0.06, 0.052, 0.08), 0.3, 0.06, None, 0.0, 1.0),             # shard spikes
    "BH_DarkSteel": ((0.02, 0.02, 0.024), 0.3, 0.35, None, 0.0, 1.0),        # inner glass core, joint balls
    "BH_Bronze": ((0.5, 0.24, 0.11), 1.0, 0.42, None, 0.0, 1.0),             # copper frame, housings, stacks
    "BH_Gold": ((0.64, 0.37, 0.16), 1.0, 0.3, None, 0.0, 1.0),               # bright copper rims / seam lips
    "BH_Steel": ((0.5, 0.5, 0.52), 1.0, 0.22, None, 0.0, 1.0),               # polished piston rods
    "BH_Rust": ((0.11, 0.1, 0.1), 0.8, 0.6, None, 0.0, 1.0),                 # blackened iron: grille bars, rivets
    "BH_Shadow": ((0.012, 0.011, 0.012), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Coals": ((0.62, 0.16, 0.05), 0.0, 0.7, (1.0, 0.32, 0.06), 4.0, 1.0),   # the ash-mouth fire (real fire)
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),     # seams, face grille light: white
    "BH_WeakPoint": ((1.0, 1.0, 1.0), 0.0, 0.3, (1.0, 1.0, 1.0), 6.0, 1.0),    # the molten core (its heart)
}
CLIPS = ["boss_charge", "boss_slam", "boss_summon", "cast_area", "cast_heavy", "cast_ultimate", "gs_1",
         "boss_roar", "boss_sweep", "gs_2"]

P = RG.P
FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
zh, zs, zc, zn, zhd = L["hips"], L["spine"], L["chest"], L["neck"], L["head"]
HEAD_DY, HEAD_DZ = -0.18, -0.16
PELV = [(zh - 0.32, 0.46, 0.33, 0.33), (zh - 0.14, 0.6, 0.41, 0.4), (zh + 0.14, 0.62, 0.42, 0.41),
        (zh + 0.26, 0.56, 0.38, 0.38)]
CHEST = [(zc - 0.14, 0.66, 0.46, 0.46, 0.0), (zc + 0.08, 0.86, 0.6, 0.56, -0.02), (zc + 0.44, 1.02, 0.7, 0.66, -0.04),
         (zc + 0.78, 1.06, 0.68, 0.7, -0.02), (zn - 0.06, 0.98, 0.58, 0.66, 0.01), (zn + 0.1, 0.66, 0.42, 0.5, 0.03)]
HEADR = [(-0.16, 0.26, 0.28, 0.25, -0.06), (0.0, 0.3, 0.33, 0.29, -0.07), (0.22, 0.31, 0.34, 0.3, -0.07),
         (0.36, 0.28, 0.31, 0.27, -0.07), (0.44, 0.2, 0.22, 0.2, -0.06)]


def ring_pts(c, r, n, axis="y", a0=0.0):
    """Circle points round c in the XZ plane (axis y) - for rims on front faces."""
    return [np.asarray(c, float) + np.array([r * math.cos(a), 0.0, r * math.sin(a)])
            for a in np.linspace(a0, a0 + 2 * math.pi, n)]


def build(body: Body):
    add = body.add
    core_w = GK.zspec_w([(zh + 0.06, "hips"), (zs + 0.06, "spine"), (zc - 0.06, "spine"), (zc + 0.14, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.08), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.4)], [(0.44, 0.32)] * 4, n=8,
                  up=(0, -1, 0), p=2.0)
    add(P(V, F, "BH_DarkSteel", "core"), weights=core_w)
    pelvis(body)
    crank_drum(body)
    chest(body)
    stacks(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        hammer(body, s)
        leg(body, s)


def pelvis(body):
    add = body.add
    pv = Facet(PELV, n=8, seed=11)
    add(pv.part, "hips")
    add(pv.band(zh + 0.16, 0.1, 0.02, mat="BH_Bronze"), "hips")
    add(pv.band(zh - 0.18, 0.05, 0.016, mat="BH_Gold"), "hips")
    addp(body, seam(pv.fpts([(-0.25, zh + 0.0), (-0.08, zh - 0.08), (0.06, zh + 0.02), (0.24, zh - 0.06)], 0.004),
                    FRONT, 0.026), "hips")
    # glass tassets with copper caps (front pair + side pair per leg)
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        tw = (lambda V, lb=lb: [{"hips": 0.55, lb: 0.45}] * len(V))
        for (x, y, w, rz, ln) in ((0.3, -0.44, 0.42, 10, 0.6), (0.64, -0.08, 0.36, 76, 0.5)):
            c = np.array([sx * x, y, zh - 0.3])
            R = Rz(sx * rz) @ Rx(10)
            V, F = M.prism(np.array([(-w / 2, 0.26), (w / 2, 0.26), (w / 2 * 0.85, -0.12), (0.0, -0.26 - ln * 0.25),
                                     (-w / 2 * 0.85, -0.12)]), 0.11, axis="y")
            add(P(V, F, "BH_Stone", "tasset").rot(R).move(c), weights=tw)
            add(RG.slab((w * 0.95, 0.14, 0.07), c + R @ np.array([0, 0, 0.25]), R=R, mat="BH_Bronze", bev=0.01),
                weights=tw)
            addp(body, seam([c + R @ np.array([-w * 0.25, -0.062, 0.15]), c + R @ np.array([0.0, -0.064, -0.05]),
                             c + R @ np.array([w * 0.2, -0.062, -0.18])], R @ np.array([0, -1.0, 0]), 0.02), weights=tw)


def crank_drum(body):
    """The waist: stacked copper drums (a crankcase) with obsidian plates bolted between."""
    add = body.add
    for k, z in enumerate((zs - 0.04, zs + 0.15, zs + 0.34)):
        rows = [(z - 0.08, 0.52 + 0.04 * k, 0.4 + 0.03 * k, 0.4 + 0.03 * k), (z + 0.08, 0.54 + 0.04 * k, 0.42 + 0.03 * k,
                                                                              0.42 + 0.03 * k)]
        dr = Facet(rows, n=12, seed=20 + k, amp=0.0, mat="BH_Bronze")
        add(dr.part, "spine")
        add(dr.band(z, 0.035, 0.014, mat="BH_Gold"), "spine")
        for a in np.linspace(0, 2 * math.pi, 9, endpoint=False):
            q = np.array([(0.55 + 0.04 * k) * math.sin(a), -(0.43 + 0.03 * k) * math.cos(a), z + 0.05])
            add(A.ball(q, 0.025, "BH_Rust", n=6, rings=4), "spine")
    for sx in (1, -1):
        c = np.array([sx * 0.36, -0.42, zs + 0.15])
        add(RG.slab((0.3, 0.1, 0.5), c, R=Rz(sx * 22), mat="BH_Stone", bev=0.012), "spine")
        addp(body, seam([c + (sx * -0.06, -0.06, 0.18), c + (sx * 0.02, -0.065, 0.02), c + (sx * -0.03, -0.062, -0.16)],
                        FRONT, 0.02), "spine")


def chest(body):
    add = body.add
    ch = Facet(CHEST, n=12, seed=31, amp=0.05)
    add(ch.part, "chest")
    add(ch.band(zc - 0.1, 0.08, 0.024, mat="BH_Bronze"), "chest")
    add(ch.band(zn + 0.03, 0.08, 0.02, mat="BH_Bronze"), "chest")
    # ---- the furnace mouth: copper-rimmed round firebox in the breast
    zf = zc + 0.52
    yf = ch.front(0, zf)
    R0 = 0.4
    add(A.ball((0, yf + 0.06, zf), R0 * 1.05, "BH_Shadow", n=16, rings=8, scale=(1, 0.32, 1)), "chest")
    add(A.ball((0, yf + 0.0, zf), R0 * 0.72, "BH_WeakPoint", n=14, rings=8, scale=(1, 0.42, 1)), "chest")
    rim = ring_pts((0, yf - 0.05, zf), R0 * 1.02, 25)
    add(A.tube(rim, (0.07, 0.06), "BH_Bronze", n=6, cap=False), "chest")
    rim = ring_pts((0, yf - 0.1, zf), R0 * 1.1, 25)
    add(A.tube(rim, 0.03, "BH_Gold", n=5, cap=False), "chest")
    for k in range(12):                         # rivets round the rim
        a = 2 * math.pi * k / 12
        add(A.ball((R0 * 1.18 * math.cos(a), yf - 0.06, zf + R0 * 1.18 * math.sin(a)), 0.035, "BH_Rust", n=6, rings=4),
            "chest")
    # grille: heavy iron bars across the mouth (vertical) + one cross bar
    for x in np.linspace(-R0 * 0.75, R0 * 0.75, 6):
        h = math.sqrt(max(R0 ** 2 - x ** 2, 0.01)) * 0.98
        add(A.tube([(x, yf - 0.1, zf - h), (x, yf - 0.13, zf), (x, yf - 0.1, zf + h)], 0.03, "BH_Rust", n=6), "chest")
    add(A.tube([(-R0, yf - 0.15, zf), (R0, yf - 0.15, zf)], 0.035, "BH_Rust", n=6), "chest")
    # riveted copper plates framing the furnace (stepped corners)
    for sx in (1, -1):
        for sz in (1, -1):
            c = np.array([sx * 0.46, ch.front(sx * 0.46, zf + sz * 0.42) - 0.01, zf + sz * 0.42])
            add(RG.slab((0.3, 0.07, 0.22), c, R=Ry(sx * sz * 18), mat="BH_Bronze", bev=0.012), "chest")
            add(A.ball(c + (0, -0.05, 0), 0.03, "BH_Rust", n=6, rings=4), "chest")
    # ash-mouth under the furnace: a low grated slot with real orange coals
    za = zc + 0.05
    ya = ch.front(0, za)
    add(RG.slab((0.5, 0.1, 0.16), (0, ya - 0.0, za), mat="BH_Shadow", bev=0.01), "chest")
    for k in range(6):
        add(A.ball((-0.18 + 0.072 * k, ya - 0.035, za - 0.02 + 0.02 * ((k * 3) % 2)), 0.045, "BH_Coals", n=6, rings=4),
            "chest")
    add(RG.slab((0.58, 0.08, 0.04), (0, ya - 0.06, za + 0.09), mat="BH_Bronze", bev=0.008), "chest")
    for x in np.linspace(-0.2, 0.2, 5):
        add(A.tube([(x, ya - 0.07, za - 0.08), (x, ya - 0.07, za + 0.08)], 0.016, "BH_Rust", n=5), "chest")
    # molten seams through the glass, radiating from the furnace rim
    for (a, b, n, sd, br) in (((0.36, zf + 0.3), (0.9, zn - 0.08), 6, 1, ()), ((-0.36, zf + 0.3), (-0.86, zn - 0.04), 6, 2, (2,)),
                              ((0.46, zf - 0.1), (0.98, zc + 0.2), 6, 3, ()), ((-0.46, zf - 0.12), (-0.96, zc + 0.24), 6, 4, ()),
                              ((0.0, zf + R0 + 0.12), (0.06, zn + 0.0), 4, 5, ()), ((0.28, za + 0.06), (0.62, zc - 0.1), 4, 6, ()),
                              ((-0.28, za + 0.06), (-0.6, zc - 0.08), 4, 7, ())):
        q = jag((a[0], 0, a[1]), (b[0], 0, b[1]), n, 0.06, FRONT, sd)
        addp(body, seam(ch.fpts([(p[0], p[2]) for p in q], 0.004), FRONT, 0.03, broken=br), "chest")
    # back: seams + the stack mounts, collar plates round the head
    for sx, sd in ((1, 11), (-1, 12)):
        q = jag((sx * 0.1, 0, zc + 0.05), (sx * 0.7, 0, zn - 0.2), 6, 0.06, BACK, sd)
        addp(body, seam(ch.bpts([(p[0], p[2]) for p in q], 0.004), BACK, 0.028), "chest")
        add(RG.slab((0.3, 0.7, 0.16), (sx * 0.62, 0.02, zn + 0.02), R=Ry(sx * 20), mat="BH_Bronze", bev=0.014), "chest")
    body._ch = ch


def stacks(body):
    """Two tall stepped smokestacks behind the shoulders, a ring of glass spikes between them."""
    add = body.add
    ch = body._ch
    for sx in (1, -1):
        zb = zc + 0.5
        base = np.array([sx * 0.46, ch.back(sx * 0.46, zb) - 0.1, zb])
        d = normalize(np.array([sx * 0.12, 0.28, 1.0]))
        top = base + d * 1.75
        V, F = M.tube([base, base + (top - base) * 0.4, top], [(0.17, 0.17), (0.15, 0.15), (0.14, 0.14)], n=10,
                      up=(1, 0, 0))
        add(P(V, F, "BH_Bronze", "stack"), "chest")
        for u in (0.15, 0.45, 0.75):
            q = base + (top - base) * u
            V, F = M.tube([q - d * 0.03, q + d * 0.03], [(0.185, 0.185)] * 2, n=10, up=(1, 0, 0))
            add(P(V, F, "BH_Rust", "stackring"), "chest")
        # stepped crown cap: two widening courses, a glowing white throat (heat shimmer of the core)
        for i, (r, h) in enumerate(((0.22, 0.08), (0.27, 0.07))):
            q = top + d * (0.04 + 0.075 * i)
            V, F = M.tube([q - d * h / 2, q + d * h / 2], [(r, r)] * 2, n=8, up=(1, 0, 0), p=2.0)
            add(P(V, F, "BH_Stone", "stackcap"), "chest")
        add(A.tube([top + d * 0.1, top + d * 0.16], 0.12, "BH_Shadow", n=10), "chest")
        add(A.tube([top + d * 0.12, top + d * 0.17], 0.08, "BH_Emissive", n=8), "chest")
        # a copper seam glyph up the stack
        side = normalize(np.cross(d, (1, 0, 0)))
        q = [base + (top - base) * u + side * 0.155 * (-1) for u in (0.2, 0.32, 0.6, 0.7)]
        addp(body, seam(q, -side, 0.018), "chest")
    # ring of shard spikes between the stacks, along the top of the back
    for k, (x, z, dx, ln) in enumerate(((0.0, zn - 0.1, 0.0, 0.85), (0.18, zn - 0.26, 0.3, 0.6), (-0.18, zn - 0.26, -0.3, 0.6),
                                        (0.0, zc + 0.36, 0.0, 0.5))):
        b0 = np.array([x, ch.back(x, z) - 0.06, z])
        addp(body, A.cluster(b0, (dx, 0.8, 1.0), ln, "BH_Horn", count=3 if k == 0 else 2, seed=50 + k, spread=18),
             "chest")


def head(body):
    add = body.add
    z0 = zhd + HEAD_DZ
    rows = [(z0 + r[0], r[1], r[2], r[3], r[4] + HEAD_DY) for r in HEADR]
    hd = Facet(rows, n=8, seed=41, amp=0.04)
    add(hd.part, "head")
    # grille face: a white light plate recessed behind heavy copper bars, a brow ledge over it
    zg = z0 + 0.14
    yg = hd.front(0, zg)
    add(RG.slab((0.4, 0.06, 0.3), (0, yg + 0.02, zg), mat="BH_Shadow", bev=0.008), "head")
    add(RG.slab((0.32, 0.03, 0.2), (0, yg - 0.005, zg + 0.02), mat="BH_Emissive", bev=0.006), "head")
    for x in np.linspace(-0.15, 0.15, 5):
        add(A.tube([(x, yg - 0.03, zg - 0.15), (x, yg - 0.04, zg + 0.15)], 0.022, "BH_Bronze", n=5), "head")
    add(RG.slab((0.46, 0.12, 0.08), (0, yg - 0.04, zg + 0.19), R=Rx(-12), mat="BH_Stone", bev=0.01), "head")
    add(RG.slab((0.44, 0.1, 0.06), (0, yg - 0.03, zg - 0.18), mat="BH_Bronze", bev=0.008), "head")
    # stepped glass crown with a seam
    zt = z0 + 0.44
    for i, (w, h) in enumerate(((0.5, 0.08), (0.62, 0.07), (0.42, 0.08))):
        add(RG.slab((w, w * 0.9, h), (0, HEAD_DY - 0.02, zt + 0.07 * i), mat="BH_Stone" if i != 1 else "BH_Bronze",
                    bev=0.01), "head")
    addp(body, A.cluster((0, HEAD_DY + 0.04, zt + 0.2), (0, 0.4, 1.0), 0.4, "BH_Horn", count=3, seed=44, spread=26),
         "head")
    for sx in (1, -1):
        V, F = M.lathe([(0.0, -0.04), (0.12, -0.04), (0.13, 0.0), (0.11, 0.04), (0.0, 0.04)], 10)
        add(P(V, F, "BH_Bronze", "earvalve").rot(Ry(90 * sx)).move((sx * 0.32, HEAD_DY + 0.02, z0 + 0.16)), "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    Au, Af = body.axes(ua), body.axes(fa)
    ul, fl = body.p["upper_len"], body.p["fore_len"]
    add(GK.blob(sh, 0.34, "BH_DarkSteel", n=10, rings=6), ua)
    # upper arm: copper cylinder housing with an obsidian plate over the outside
    add(body.limb(ua, [(0.05, 0.27, 0.27), (0.5, 0.29, 0.29), (0.95, 0.27, 0.27)], "BH_Bronze", n=12, p=2.0), ua)
    for u in (0.12, 0.5, 0.88):
        c = sh + (el - sh) * u
        add(RG.joint_ring(c, el - sh, 0.3, w=0.05, mat="BH_Gold"), ua)
    add(flimb(body, ua, [(0.2, 0.32, 0.2), (0.5, 0.35, 0.22), (0.8, 0.3, 0.2)], n=6, front=tuple(Au[:, 2])), ua)
    addp(body, seam(body.lpt(ua, jag((0, 0.24 * ul, 0.24), (0.02, 0.76 * ul, 0.24), 5, 0.04, (0, 0, 1), 60 + (sx > 0))),
                    Au[:, 2], 0.024), ua)
    # stepped pauldron (glass courses + copper lip) with shard spikes
    c = sh + np.array([sx * 0.06, 0.0, 0.26])
    R = Ry(-sx * 14)
    for i, (w, d_, h) in enumerate(((0.8, 0.86, 0.22), (0.64, 0.7, 0.15), (0.46, 0.52, 0.12))):
        add(RG.slab((w, d_, h), c + R @ np.array([sx * 0.02 * i, 0, 0.17 * i]), R=R, bev=0.02), sh_b)
    add(RG.slab((0.84, 0.9, 0.06), c + R @ np.array([0, 0, -0.13]), R=R, mat="BH_Bronze", bev=0.01), sh_b)
    top = c + R @ np.array([sx * 0.06, 0, 0.42])
    addp(body, A.cluster(top, (sx * 0.6, 0.2, 1.0), 0.55, "BH_Horn", count=3, seed=70 + (sx > 0), spread=24), sh_b)
    fr = c + R @ np.array([0, -0.44, 0.0])
    addp(body, seam([fr + R @ np.array([-0.32, -0.004, 0.05]), fr + R @ np.array([-0.1, -0.004, -0.04]),
                     fr + R @ np.array([0.1, -0.004, 0.05]), fr + R @ np.array([0.32, -0.004, -0.04])],
                    R @ np.array([0, -1.0, 0]), 0.022), sh_b)
    # elbow: a big joint ball in a copper yoke
    add(GK.blob(el, 0.3, "BH_DarkSteel", n=10, rings=6), fa)
    add(RG.joint_ring(el + (wr - el) * 0.04, wr - el, 0.32, w=0.12, mat="BH_Bronze"), fa)
    # forearm piston: copper sleeve (proximal), a gland ring, the polished rod driving out (distal)
    add(body.limb(fa, [(0.06, 0.3, 0.3), (0.5, 0.32, 0.32), (0.56, 0.32, 0.32)], "BH_Bronze", n=12, p=2.0), fa)
    add(RG.joint_ring(el + (wr - el) * 0.58, wr - el, 0.34, w=0.07, mat="BH_Gold"), fa)
    add(body.limb(fa, [(0.58, 0.17, 0.17), (1.0, 0.17, 0.17)], "BH_Steel", n=10, p=2.0), fa)
    for u in (0.18, 0.38):
        add(RG.joint_ring(el + (wr - el) * u, wr - el, 0.33, w=0.04, mat="BH_Rust"), fa)
    # obsidian armour plate over the outer sleeve with a seam
    add(flimb(body, fa, [(0.08, 0.36, 0.2), (0.3, 0.38, 0.22), (0.52, 0.35, 0.2)], n=6, front=tuple(Af[:, 2])), fa)
    addp(body, seam(body.lpt(fa, jag((0, 0.1 * fl, 0.235), (0.02, 0.5 * fl, 0.235), 4, 0.04, (0, 0, 1), 64 + (sx > 0))),
                    Af[:, 2], 0.022), fa)
    # slave pistons: two thin cylinders along the forearm sides (housing on the sleeve, rod into the hammer)
    fwd = Af.T @ np.array([0, -1.0, 0])
    tx = 1.0 if fwd[0] > 0 else -1.0
    for sz in (1, -1):
        a = body.lpt(fa, [(tx * 0.0 + sz * 0.0, 0.2 * fl, sz * 0.36)])[0]
        b = body.lpt(fa, [(0.0, 0.62 * fl, sz * 0.36)])[0]
        cc = body.lpt(fa, [(0.0, 1.04 * fl, sz * 0.3)])[0]
        add(A.tube([a, b], 0.075, "BH_Bronze", n=8), fa)
        add(A.tube([b, cc], 0.035, "BH_Steel", n=6), fa)
        add(A.ball(a, 0.08, "BH_Rust", n=6, rings=4), fa)


def hammer(body, s):
    """Hammer head on the end of the piston (rigid to hand.<s>; bone-local x across, y along the hand, z = back of
    the hand): a copper-banded block, knapped obsidian striking face on the distal end, a white glyph in it."""
    add = body.add
    ha = "hand." + s
    Ax = body.axes(ha)
    add(RG.local_box(body, ha, (0.42, 0.2, 0.42), (0, 0.06, 0), mat="BH_Rust", bev=0.02), ha)
    o = body.head(ha)
    a = o + Ax @ np.array([0, 0.1, 0])
    b = o + Ax @ np.array([0, 0.78, 0])
    add(fprism(a, b, [(0.38, 0.38), (0.42, 0.42), (0.44, 0.44), (0.42, 0.42)], n=8, mat="BH_Stone",
               up=tuple(Ax[:, 2])), ha)
    for y in (0.2, 0.46, 0.7):
        add(A.tube([o + Ax @ np.array([0, y - 0.035, 0]), o + Ax @ np.array([0, y + 0.035, 0])], 0.46, "BH_Bronze", n=8),
            ha)
    # striking face: a raised stepped boss + glyph
    add(fprism(o + Ax @ np.array([0, 0.78, 0]), o + Ax @ np.array([0, 0.88, 0]), [(0.34, 0.34), (0.28, 0.28)], n=8,
               mat="BH_Stone", up=tuple(Ax[:, 2])), ha)
    yface = 0.885
    sq = [(-0.12, yface, -0.1), (-0.12, yface, 0.1), (0.0, yface, 0.1), (0.0, yface, -0.04), (0.12, yface, -0.04),
          (0.12, yface, 0.1)]
    addp(body, seam(body.lpt(ha, sq), Ax[:, 1], 0.02), ha)
    # rivet studs + shard spurs on the back of the block
    for y in (0.33, 0.58):
        for x in (-0.24, 0.24):
            add(A.ball(o + Ax @ np.array([x, y, 0.42]), 0.04, "BH_Rust", n=6, rings=4), ha)
    for k, y in enumerate((0.3, 0.58)):
        add(A.shard(o + Ax @ np.array([0, y, 0.38]), Ax @ np.array([0, 0.3, 1.0]), 0.3 - 0.05 * k, 0.07, "BH_Horn",
                    sides=4), ha)
    addp(body, seam([o + Ax @ np.array([-0.3, y, -0.43]) for y in (0.25, 0.4, 0.55)] +
                    [o + Ax @ np.array([0.1, 0.62, -0.43])], -Ax[:, 2], 0.02), ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(GK.blob(hip, 0.32, "BH_DarkSteel", n=10, rings=6), th)
    add(flimb(body, th, [(0.05, 0.32, 0.33), (0.5, 0.36, 0.37), (0.92, 0.31, 0.32)], n=8), th)
    add(RG.joint_ring(hip + (k - hip) * 0.86, k - hip, 0.34, w=0.08, mat="BH_Bronze"), th)
    addp(body, seam(jag(hip + (sx * 0.35, -0.04, -0.15), k + (sx * 0.33, -0.04, 0.2), 5, 0.04, np.array([sx, 0, 0.0]),
                        90 + sx), np.array([sx, 0, 0.0]), 0.024), th)
    add(GK.blob(k + (0, -0.03, 0), 0.3, "BH_DarkSteel", n=10, rings=6), sh)
    add(flimb(body, sh, [(0.06, 0.31, 0.32), (0.4, 0.35, 0.36), (0.85, 0.36, 0.37), (1.0, 0.33, 0.34)], n=8), sh)
    add(RG.joint_ring(k + (a - k) * 0.84, a - k, 0.38, w=0.09, mat="BH_Bronze"), sh)
    # knee cap of glass + shin piston (housing up top, polished rod down to the ankle)
    V, F = M.prism(np.array([(-0.22, -0.16), (0.22, -0.16), (0.25, 0.1), (0.0, 0.24), (-0.25, 0.1)]), 0.14, axis="y")
    add(P(V, F, "BH_Stone", "knee").rot(Rx(-8)).move(k + (0, -0.33, 0.0)), sh)
    hp = k + (0, -0.42, -0.14)
    add(A.tube([hp, hp + (a - k) * 0.4], 0.09, "BH_Bronze", n=8), sh)
    add(A.tube([hp + (a - k) * 0.4, a + (0, -0.36, 0.18)], 0.045, "BH_Steel", n=6), sh)
    add(A.ball(hp, 0.1, "BH_Rust", n=6, rings=4), sh)
    addp(body, seam(jag(k + (sx * 0.34, -0.12, -0.16), a + (sx * 0.34, -0.12, 0.3), 4, 0.04, np.array([sx, -0.3, 0]),
                        94 + sx), np.array([sx, -0.3, 0]), 0.022), sh)
    # slab foot of glass with a copper toe band
    hx = body.p["hip_x"] * sx
    V, F = M.tube([(hx, 0.2, 0.13), (hx, -0.08, 0.15), (hx, -0.34, 0.12)], [(0.32, 0.13), (0.34, 0.15), (0.31, 0.12)],
                  n=8, up=(0, 0, 1), p=2.0)
    add(P(V, F, "BH_Stone", "foot"), ft)
    add(RG.slab((0.6, 0.12, 0.15), (hx, -0.32, 0.26), R=Rx(-30), mat="BH_Bronze", bev=0.012), ft)
    V, F = M.tube([(hx, -0.36, 0.1), (hx, -0.62, 0.07)], [(0.3, 0.1), (0.24, 0.06)], n=8, up=(0, 0, 1), p=2.0)
    add(P(V, F, "BH_Stone", "toe"), toe)
