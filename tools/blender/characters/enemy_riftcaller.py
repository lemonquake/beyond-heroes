"""Riftcaller (bh-013, Builder A; SUMMONER that tears open a Void Rift): a tall (~2.0 m), lean void-priest with no
weapon, only casting hands. Floor-length black robe with deep-violet trims and a violet tabard cut to a sharp point,
sharp angular shoulder plates of black-violet metal rising into swept spikes (with a glowing violet seam), a deep cowl
split at the crown into two tall swept points and open at the front over a starry void where the face should be (dark
void with emissive violet star points). Forearms wrapped in dark bands with glowing violet sigils, black gloves with
long fingers, both hands open. A torn cape (cape bones) whose outside is black and whose inner lining is a dark-blue
star field (tiny emissive specks); the cape flares at the sides so the lining shows from the front.

Clips: cast_quick, cast_area, cast_heavy, cast_ultimate, boss_summon, blink (+ the shared enemy base clips).
Robe / hood helpers: enemy_ashen_cultist; kit: enemy_bandit_cutthroat (SB) + kit_a_common + kit_e_orrery specks;
cape bones + secondary motion from char_knight."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import char_knight as KN
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_e_orrery as O

SCALE = 2.0 / 1.87
PROPS = proportions(SCALE, shoulder_x=0.176 * SCALE, hip_x=0.09 * SCALE, upper_len=0.3 * SCALE,
                    fore_len=0.285 * SCALE, hand_len=0.11 * SCALE)
EXTRA_BONES = [(n, tuple(np.array(h) * SCALE), tuple(np.array(t) * SCALE), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PREVIEW_HEIGHT = 2.5
PALETTE = "riftcaller"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.022, 0.018, 0.03), 0.0, 0.9, None, 0.0, 1.0),       # black robe, cowl, cape outside
    "BH_Cloth_Secondary": ((0.16, 0.035, 0.25), 0.0, 0.85, None, 0.0, 1.0),     # deep violet tabard / trims
    "BH_Stone": ((0.02, 0.03, 0.1), 0.0, 0.85, None, 0.0, 1.0),                 # cape lining: dark-blue star field
    "BH_DarkSteel": ((0.07, 0.05, 0.1), 1.0, 0.42, None, 0.0, 1.0),             # angular shoulder plates, clasps
    "BH_Leather": ((0.03, 0.025, 0.035), 0.0, 0.7, None, 0.0, 1.0),             # gloves, forearm bands, boots
    "BH_Shadow": ((0.012, 0.004, 0.02), 0.0, 0.8, None, 0.0, 1.0),              # the void under the cowl
    "BH_Emissive": ((0.8, 0.3, 1.0), 0.0, 0.4, (0.82, 0.3, 1.0), 10.0, 1.0),    # violet stars, sigils, seams
}
CLIPS = ["cast_quick", "cast_area", "cast_heavy", "cast_ultimate", "boss_summon", "blink"]

TORSO = [(r[0], r[1] * 0.88, r[2] * 0.86, r[3] * 0.92, r[4] * 0.6) for r in K.TORSO]
G = 0.012
# deep cowl, a wider front opening (the void shows)
HOOD = [(z, rx * 1.1, ryf * 1.15, ryb * 1.08, cy - 0.01, min(th + 12, 58) if 1.55 < z < 1.83 else th)
        for (z, rx, ryf, ryb, cy, th) in C.HOOD_DEEP]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def secondary(anim, frames):
    return KN.secondary(anim, frames)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    # ---- robes
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", g=G, rows=TORSO, v_open=0.0)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", z_top=1.07, z_bot=0.05, flare=0.13, folds=0.012,
                 g=G - 0.02)
    tabard(sb)
    belt(sb)
    cape(sb)
    for s in ("L", "R"):
        shoulder_plate(sb, s)
    # ---- cowl over the void
    cowl(sb)
    # ---- arms: short bell sleeves to the elbow, wrapped forearms with sigils, open gloved hands
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", cuff_r=0.075, end=0.22)
        forearm_bands(sb, s)
        for prt in A.open_palm(sb.b, s, "BH_Leather", s=SCALE):
            sb.add_real(prt, "hand." + s)
        for prt in A.bony_fingers(sb.b, s, "BH_Leather", length=0.1 * SCALE, r=0.0072 * SCALE, curl=0.55, spread=1.1,
                                  open_hand=True, nails="BH_DarkSteel"):
            sb.add_real(prt, "hand." + s)
    # ---- legs (hidden) + pointed boots
    K.trousers(sb, "BH_Cloth_Primary", loose=0.85)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.35, cuff=False)


# ================================================================================================= robes
def centre_w(leg=0.5):
    """Centre panels between the legs: both thighs share the leg influence (no tearing down the middle)."""
    base = HS.cloth_w(chest_z=1.3, belt_z=1.03, leg=0.0)

    def wfn(V):
        out = base(V)
        for i, v in enumerate(V):
            if v[2] < 1.0:
                s_ = float(smoothstep(1.0, 0.5, v[2])) * leg
                out[i] = {"hips": 1 - s_, "thigh.L": s_ / 2, "thigh.R": s_ / 2} if s_ > 1e-3 else {"hips": 1.0}
        return out
    return wfn


def tabard(sb):
    """Violet tabard down the front, cut to a sharp point at the shins, edged in black, a glowing rift seam."""
    def fn(u, v):
        zb = 0.3 + 0.28 * abs(u - 0.5) * 2
        z = 1.44 + (zb - 1.44) * v
        hw = 0.085 + 0.03 * v
        x = (u - 0.5) * 2 * hw
        if z >= 1.03:
            y = front_y(TORSO, x, z) - G - 0.012
        else:
            y = front_y(TORSO, x, 1.03) - G - 0.012 - 0.09 * (1.03 - z) ** 1.1
        return (x, y, z)
    V, F = M.grid(fn, 7, 13)
    w = centre_w(0.5)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="tabard"), 0.008, offset=1.0), weights=w)
    for k in (0.0, 1.0):
        edge = np.array([fn(k, v) for v in np.linspace(0, 1, 12)]) + np.array([0, -0.008, 0])
        sb.add(A.tube(edge, 0.006, "BH_Cloth_Primary", n=4), weights=w)
    hem = np.array([fn(u, 1.0) for u in np.linspace(0, 1, 7)]) + np.array([0, -0.008, 0])
    sb.add(A.tube(hem, 0.006, "BH_Cloth_Primary", n=4), weights=w)
    # the rift: a jagged glowing seam down the tabard
    seam = [(0.0, 0.1), (0.03, 0.22), (-0.02, 0.34), (0.025, 0.46), (-0.015, 0.6), (0.01, 0.72), (0.0, 0.84)]
    pts = [np.array(fn(0.5 + dx / 0.2, v)) + np.array([0, -0.011, 0]) for dx, v in seam]
    sb.add(A.tube(pts, (0.007, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)), weights=w)


def belt(sb):
    V, F = K.band(TORSO, 1.0, 1.05, G + 0.028, G - 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Leather", name="belt"), "hips")
    y = front_y(TORSO, 0, 1.025) - G - 0.04
    V, F = M.prism([(-0.05, 0.0), (0.0, -0.035), (0.05, 0.0), (0.0, 0.05)], 0.014, axis="y")
    sb.add(M.Part(V, F, "BH_DarkSteel", name="clasp").move((0, y, 1.025)), "hips")
    sb.add(O.speck((0, y - 0.01, 1.03), 0.014, "BH_Emissive", seed=3), "hips")


def cape_w():
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z > 1.42:
                out.append({"chest": 1.0})
            elif z > 1.3:
                t = float(smoothstep(1.3, 1.42, z))
                out.append({"chest": t, "cape.1": 1 - t})
            elif z > 1.14:
                out.append({"cape.1": 1.0})
            elif z > 1.0:
                t = float(smoothstep(1.0, 1.14, z))
                out.append({"cape.1": t, "cape.2": 1 - t})
            else:
                out.append({"cape.2": 1.0})
        return out
    return wfn


def cape(sb):
    """Torn cape from the shoulders to the calves, wide, the sides sweeping forward so the star-field lining shows.
    Two single-sided sheets: black outside, dark-blue lining with emissive star specks inside."""
    def fn(u, v):
        zb = 0.32 + HS.ragged(u, 2.2, 0.26, 5)
        z = 1.48 + (zb - 1.48) * v
        side = (u - 0.5) * 2                       # -1 .. 1
        half = 0.2 + 0.2 * v ** 0.8
        x = side * half
        yb = back_y(TORSO, np.clip(x, -0.15, 0.15) * 0.95, min(max(z, 1.3), 1.48)) + 0.04
        y = yb + 0.2 * v ** 1.3 + 0.02 * math.sin(u * math.pi * 7) * v
        y -= 0.16 * abs(side) ** 2.2 * v ** 0.9          # the sides sweep forward
        y -= 0.05 * abs(side) ** 3 * (1 - v) ** 2        # wrap the shoulders
        return (x, y, z)
    V, F = M.grid(fn, 15, 13)
    w = cape_w()
    outer = M.Part(V, F, "BH_Cloth_Primary", name="cape")          # normals face back/out
    inner = M.Part(V.copy(), F, "BH_Stone", name="cape_lining").flip()
    # push the lining a few mm toward the body along the (outer) surface normal
    N = np.zeros_like(V)
    for f in F:
        a, b_, c = V[f[0]], V[f[1]], V[f[2]]
        n = np.cross(b_ - a, c - a)
        for i in f:
            N[i] += n
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    if np.mean(N[:, 1]) < 0:        # make N point outward (+Y, away from the body)
        N = -N
        outer.flip()
        inner.flip()
    inner.V = inner.V - N * 0.006
    Vi = inner.V.copy()                  # (sb.add scales the parts in place)
    sb.add(outer, weights=w)
    sb.add(inner, weights=w)
    rng = np.random.default_rng(13)
    for k in range(56):
        u, v = rng.random(), 0.06 + 0.88 * rng.random()
        i = min(int(round(u * 14)), 14) + 15 * min(int(round(v * 12)), 12)
        p = Vi[i] - N[i] * 0.003
        r = 0.006 + 0.008 * rng.random() ** 2
        if k % 4 == 0:
            sb.add(O.star4(p, r * 1.6, -N[i], "BH_Emissive", thick=0.0015), weights=w)
        else:
            sb.add(O.disc(p, -N[i], r * 0.6, 0.0015, "BH_Emissive", n=5), weights=w)
    # violet hem band along the top edge (at the shoulders)
    top = np.array([fn(u, 0.0) for u in np.linspace(0, 1, 11)]) + np.array([0, 0.004, 0.005])
    sb.add(A.tube(top, 0.012, "BH_Cloth_Secondary", n=5), "chest")


def shoulder_plate(sb, s):
    """Angular black-violet shoulder plate: faceted shell over the shoulder, two stacked lames on the upper arm, a
    swept spike rising up-out-back, and a glowing violet seam."""
    sx = 1 if s == "L" else -1
    sh = sb.head("upper_arm." + s)
    el = sb.head("forearm." + s)
    armd = normalize(el - sh)
    nrm = normalize(np.array([sx * 0.7, 0.0, 1.0]))
    c = sh + np.array([sx * 0.01, 0.0, 0.012])
    sb.add(O.dome(c, nrm, 0.115, "BH_DarkSteel", n=6, rings=2, depth=0.55, up=(0, 1, 0)), "shoulder." + s)
    for k in (1, 2):
        cc = sh + armd * (0.05 * k) + np.array([sx * 0.02, 0.0, 0.0])
        sb.add(O.dome(cc, normalize(nrm + np.array([sx * 0.4 * k, 0, 0])), 0.1 - 0.012 * k, "BH_DarkSteel", n=6,
                      rings=2, depth=0.5, up=(0, 1, 0)), "upper_arm." + s)
    # swept spikes (angular shards)
    base = c + nrm * 0.05
    sb.add(A.shard(base, normalize(np.array([sx * 0.55, 0.25, 1.0])), 0.26, 0.042, "BH_DarkSteel", sides=4,
                   up=(0, 1, 0), mid=0.25), "shoulder." + s)
    sb.add(A.shard(base + np.array([sx * 0.04, -0.03, -0.02]), normalize(np.array([sx * 1.0, -0.15, 0.55])), 0.15,
                   0.03, "BH_DarkSteel", sides=4, up=(0, 1, 0), mid=0.25), "shoulder." + s)
    sb.add(A.shard(base + np.array([sx * 0.0, 0.04, -0.02]), normalize(np.array([sx * 0.45, 0.8, 0.6])), 0.14,
                   0.028, "BH_DarkSteel", sides=4, up=(0, 0, 1), mid=0.25), "shoulder." + s)
    # glowing seam across the top of the shell
    seam = [c + R_axis((0, 1, 0), -sx * a) @ np.array([0, 0, 0.0]) + normalize(
        R_axis((0, 1, 0), sx * a) @ nrm) * 0.066 for a in (-45, -20, 0, 20, 45)]
    sb.add(A.tube(seam, 0.005, "BH_Emissive", n=4), "shoulder." + s)


def cowl(sb):
    C.hood(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", rows=HOOD, lining="BH_Shadow")
    hw = C.HOOD_W
    # the split crown: two tall swept points rising from the top of the cowl, violet-edged
    for sx in (1, -1):
        pts = [(sx * 0.035, 0.03, 1.8), (sx * 0.06, 0.06, 1.88), (sx * 0.08, 0.1, 1.96), (sx * 0.085, 0.15, 2.02),
               (sx * 0.075, 0.2, 2.05)]
        sb.add(A.tube(pts, [(0.045, 0.02), (0.042, 0.018), (0.032, 0.014), (0.018, 0.009), (0.004, 0.003)],
                      "BH_Cloth_Primary", n=6, up=(sx, 0, 0)), "head")
        edge = [np.array(p) + np.array([-sx * 0.036, -0.004, 0.0]) * (1 - i / 4) for i, p in enumerate(pts)]
        sb.add(A.tube(edge, 0.005, "BH_Cloth_Secondary", n=4), "head")
    # the void: dark volume filling the cowl, star points scattered over its front, a few bright four-point stars
    sb.add(O.ball((0, -0.012, 1.7), 0.098, "BH_Shadow", n=12, rings=8, scale=(0.95, 1.0, 1.18)), "head")
    V, F = M.tube([(0, 0.0, 1.46), (0, -0.005, 1.62)], [(0.058, 0.058), (0.068, 0.068)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Shadow", name="neckvoid"), weights=K.HEAD_W)
    rng = np.random.default_rng(7)
    for k in range(22):
        a = math.radians(-90 + (rng.random() - 0.5) * 110)
        e = (rng.random() - 0.45) * 1.25
        d = np.array([math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)])
        p = np.array([0, -0.012, 1.7]) + d * np.array([0.093, 0.098, 0.115]) * 0.99
        sb.add(O.speck(p, 0.004 + 0.005 * rng.random(), "BH_Emissive", seed=k), "head")
    for p, r in (((-0.03, -0.108, 1.72), 0.03), ((0.035, -0.104, 1.69), 0.022), ((0.0, -0.11, 1.64), 0.016)):
        sb.add(O.star4(np.array(p), r, (0, -1, 0), "BH_Emissive", thick=0.003), "head")
    # a pendant clasp at the throat
    sb.add(O.star4(np.array((0, -0.13, 1.5)), 0.03, (0, -1, 0.2), "BH_DarkSteel", thick=0.01), "chest")
    sb.add(O.speck((0, -0.14, 1.5), 0.012, "BH_Emissive", seed=41), "chest")


def forearm_bands(sb, s):
    """Dark bands wrapped round the bare forearm, two glowing rings and small sigil marks between them."""
    fa, ha = "forearm." + s, "hand." + s
    el, wr = sb.head(fa), sb.head(ha)
    d = normalize(wr - el)
    V, F = M.tube([el + (wr - el) * 0.12, wr + d * 0.01], [(0.044, 0.046), (0.034, 0.036)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Leather", name="forearm"), fa)
    K.wrap_band(sb, fa, ha, 0.2, 0.95, 0.043, "BH_Cloth_Secondary", turns=3.5, width=0.022, thick=0.006)
    side = normalize(np.cross(d, (0, 1, 0)))
    fw = np.cross(side, d)
    for u in (0.35, 0.8):
        c = el + (wr - el) * u
        r = 0.05 - 0.008 * u
        sb.add(O.ring(c, d, r, 0.0045, "BH_Emissive", n=12, m=4), fa)
    for k in range(5):     # sigil marks: short angled strokes round the band
        a = 2 * math.pi * k / 5
        nr = side * math.cos(a) + fw * math.sin(a)
        c = el + (wr - el) * 0.57
        p0 = c + nr * 0.049 - d * 0.03
        p1 = c + nr * 0.049 + d * 0.0 + np.cross(d, nr) * 0.012
        p2 = c + nr * 0.047 + d * 0.03
        sb.add(A.tube([p0, p1, p2], (0.0035, 0.002), "BH_Emissive", n=3, up=tuple(nr)), fa)
