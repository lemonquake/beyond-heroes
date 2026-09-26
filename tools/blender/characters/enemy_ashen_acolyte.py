"""Ashen Acolyte (Ashen Circle, support/healer): slighter than the cultist, pale ash-grey robe with no hood, a bare
shaved head with an ash-painted face, a red waist sash with long tails, a pale stole, a long bronze censer on a chain
glowing with embers (right hand) and a hymn-book (left hand). Robe helpers: enemy_ashen_cultist; kit:
enemy_bandit_cutthroat."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz, R_axis, slerp_mat
from bh_skeleton import proportions, joints
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C

SCALE = 1.70 / 1.826
PROPS = proportions(SCALE, shoulder_x=0.178 * SCALE, hip_x=0.095 * SCALE)
PALETTE = "ashen_acolyte"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.3, 0.29, 0.275), 0.0, 0.92, None, 0.0, 1.0),      # pale ash robe
    "BH_Cloth_Secondary": ((0.38, 0.03, 0.025), 0.0, 0.85, None, 0.0, 1.0),   # red sash
    "BH_Horn": ((0.42, 0.37, 0.28), 0.0, 0.8, None, 0.0, 1.0),                # stole / hymn-book pages
    "BH_Bone": ((0.62, 0.61, 0.58), 0.0, 0.8, None, 0.0, 1.0),                # ash face paint
    "BH_Ichor": ((0.03, 0.025, 0.022), 0.0, 0.8, None, 0.0, 1.0),             # soot marks / eye paint
    "BH_Leather": ((0.09, 0.05, 0.03), 0.0, 0.66, None, 0.0, 1.0),            # book cover, sandals
    "BH_Skin": ((0.45, 0.32, 0.25), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.024, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Bronze": ((0.42, 0.26, 0.11), 1.0, 0.42, None, 0.0, 1.0),             # censer
    "BH_DarkSteel": ((0.12, 0.115, 0.11), 1.0, 0.5, None, 0.0, 1.0),          # chain
    "BH_Emissive": ((1.0, 0.4, 0.08), 0.0, 0.4, (1.0, 0.42, 0.1), 8.0, 1.0),  # embers
}
CLIPS = ["cast_quick", "cast_area", "cast_weapon"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# censer chain bone: head at the right grip (rest), parented to hand.R; secondary() makes it hang with gravity
_J = joints(PROPS)
_GRIP_R = _J["weapon.R"][0]
EXTRA_BONES = [("censer", tuple(_GRIP_R), tuple(_GRIP_R + np.array([0.0, 0.0, -0.4 * SCALE])), "hand.R", (0, -1, 0))]
CHAIN = 0.34


def _model_hand_R():
    from bh_anim import Rig, DEFAULTS
    from bh_body import MODEL_POSE
    c = dict(DEFAULTS)
    c.update(MODEL_POSE)
    Q, t, D = Rig(PROPS).evaluate(c)
    return D["hand.R"].R


def secondary(anim, frames):
    """Pendulum: the censer keeps its modelled (hanging) world orientation, swings back against the hand's
    horizontal velocity, and follows the hand rigidly when the hand is near the ground (deaths / knockdowns)."""
    Rm = _model_hand_R()
    n = len(frames)
    heads = np.array([fr[3]["hand.R"].apply(_GRIP_R) for fr in frames])
    loop = bool(getattr(anim, "loop", False))
    out = []
    vel = np.zeros((n, 3))
    for f in range(n):
        a, b = max(f - 1, 0), min(f + 1, n - 1)
        if loop and n > 2:
            a, b = (f - 1) % (n - 1), (f + 1) % (n - 1)
        vel[f] = (heads[b] - heads[a]) * 30.0 / max(1, (b - a) % max(n - 1, 1) or 2)
    sm = vel.copy()
    for f in range(n):   # light smoothing (lag)
        sm[f] = vel[max(f - 3, 0):f + 1].mean(0)
    for f in range(n):
        Rp = frames[f][3]["hand.R"].R
        v = sm[f].copy()
        v[2] = 0.0
        sp = float(np.linalg.norm(v))
        Rs = np.eye(3)
        if sp > 1e-3:
            axis = normalize(np.cross(np.array([0, 0, -1.0]), -v))
            Rs = R_axis(axis, min(40.0, 22.0 * sp))
        hang = Rs @ Rm
        w = float(smoothstep(0.3, 0.65, heads[f][2]))
        Rw = slerp_mat(Rp, hang, w)
        out.append({"censer": Rp.T @ Rw})
    return out


# slighter torso (narrower shoulders / chest)
TORSO = [(r[0], r[1] * 0.92, r[2] * 0.93, r[3] * 0.93, r[4]) for r in K.TORSO]
G = 0.012


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Horn", g=G, rows=TORSO, v_open=0.05)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", flare=0.1, folds=0.01, g=G - 0.005)
    stole(sb)
    sash(sb)
    # head: shaved, ash-painted face
    K.neck_and_head(sb)
    face_paint(sb)
    # arms: narrow sleeves (bell cuffs), bare hands
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Horn", cuff_r=0.07, end=0.78)
        K.add_fist(sb, s, "BH_Skin", "BH_Skin")
    K.trousers(sb, "BH_Cloth_Primary", loose=0.92)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.3, cuff=False, wraps="BH_Leather")
    censer(sb)
    K.add_weapon(sb, "L", hymn_book())


def stole(sb):
    """Pale stole around the neck hanging down the front in two strips to the knees."""
    V, F = M.tube([(0, 0.01, 1.47), (0, 0.004, 1.52)], [(0.095, 0.085), (0.075, 0.07)], n=16, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Horn", name="stole_collar"), "chest")
    for sx in (1, -1):
        side = "L" if sx > 0 else "R"
        top, low, ups_t, ups_l = [], [], [], []
        for t in np.linspace(0, 1, 11):
            z = 1.5 - 0.95 * t
            x = sx * (0.065 + 0.012 * t)
            if z >= 0.98:
                y = front_y(TORSO, x, z) - G - 0.012
                top.append((x, y, z))
            if z <= 1.06:
                y0 = front_y(TORSO, x, 1.0) - G - 0.016
                low.append((x, y0 - 0.08 * (1.0 - min(z, 1.0)) ** 1.2, z))
        sb.add(K.strip(top, 0.05, 0.006, "BH_Horn", ups=[(0, -1, 0)] * len(top)), weights=C.ROBE_W)
        sb.add(K.strip(low, 0.05, 0.006, "BH_Horn", ups=[(0, -1, 0)] * len(low)),
               weights=C.robe_panel_w(sb, side, False))
        # red sigil stitched near the hem of each strip
        q = np.array(low[-2]) + (0, -0.006, 0)
        V, F = M.box(0.03, 0.005, 0.03, center=q)
        sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="sigil").rot(Ry(45), center=q),
               weights=C.robe_panel_w(sb, side, False))


def sash(sb):
    V, F = K.band(TORSO, 0.98, 1.08, G + 0.02, G - 0.002, n=28)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="sash"), "hips")
    p, _ = K.on_ring(TORSO, 1.03, G + 0.03, 0.87)       # knot on the right hip
    V, F = M.sphere(0.03, 8, 5, center=p, scale=(1.0, 0.8, 1.0))
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="sash_knot"), "hips")
    for dx, ln in ((0.015, 0.45), (-0.02, 0.36)):
        pts = [p + (dx, -0.01, -0.02), p + (dx * 1.5, -0.02, -ln * 0.5), p + (dx * 2, -0.015, -ln)]
        sb.add(K.strip(pts, 0.05, 0.006, "BH_Cloth_Secondary", ups=[(-0.7, -0.7, 0)] * 3),
               weights=C.robe_panel_w(sb, "R", False, leg_max=0.5))


def face_paint(sb):
    """Ash-white paint over the upper face, a black band across the eyes, a soot stroke down the crown."""
    def fn(u, v):
        x = (u - 0.5) * 0.15
        z = 1.66 + 0.1 * v
        q = K.ring_frac(K.HEAD, z, 0.0015, [(x / 0.15) * 0.22 % 1.0], p=2.1)[0]
        return (q[0], q[1], z)
    V, F = M.grid(fn, 9, 6)
    sb.add(M.Part(V, F, "BH_Bone", name="paint").flip(), "head")
    V, F = M.tube([(-0.058, -0.064, 1.7), (0.0, -0.079, 1.702), (0.058, -0.064, 1.7)], [(0.013, 0.004)] * 3, n=4,
                  up=(0, 0, 1), p=3.0)
    sb.add(M.Part(V, F, "BH_Ichor", name="eyeband"), "head")
    pts = [K.ring_frac(K.HEAD, z, 0.002, [0.0], p=2.1)[0] for z in (1.74, 1.77, 1.8)] + [(0, 0.0, 1.823)]
    sb.add(K.strip(pts, 0.022, 0.004, "BH_Ichor", ups=[(0, -1, 0.5), (0, -1, 1), (0, -0.5, 1), (0, 0, 1)]), "head")


def censer(sb):
    """Handle in the right fist (weapon.R); chain + lantern-shaped bronze censer with glowing vents hang straight
    down from the grip in the modelling pose, on the `censer` bone."""
    V, F = M.lathe([(0.0, -0.05), (0.012, -0.05), (0.013, 0.05), (0.0, 0.05)], 8)
    K.add_weapon(sb, "R", [M.Part(V, F, "BH_Bronze", name="grip")])
    g = sb.head("weapon.R")
    L = CHAIN / SCALE
    n = 10
    for i in range(n):
        z = -0.03 - L * i / (n - 1)
        V, F = M.lathe([(0.009, -0.0045), (0.013, 0.0), (0.009, 0.0045)], 8, cap=False)
        link = M.Part(V, F, "BH_DarkSteel", name="link").scale((1.0, 1.7, 1.0)).rot(Ry(90))
        link.rot(Rz(90 * (i % 2))).move(g + (0, 0, z))
        sb.add(link, "censer")
    c = g + (0, 0, -0.03 - L - 0.09)
    prof = [(0.0, -0.1), (0.018, -0.088), (0.03, -0.07), (0.06, -0.03), (0.068, 0.0), (0.066, 0.03), (0.05, 0.06),
            (0.02, 0.075), (0.0, 0.09)]
    V, F = M.lathe([(r, -z) for r, z in prof[::-1]], 10)
    sb.add(M.Part(V, F, "BH_Bronze", name="censer").move(c), "censer")
    V, F = M.lathe([(0.069, -0.012), (0.071, 0.0), (0.069, 0.012)], 10, cap=False)
    sb.add(M.Part(V, F, "BH_Emissive", name="vents").move(c + (0, 0, 0.02)), "censer")
    for k in range(5):
        a = 2 * math.pi * k / 5
        V, F = M.box(0.012, 0.012, 0.03, center=c + (0.057 * math.cos(a), 0.057 * math.sin(a), -0.025))
        sb.add(M.Part(V, F, "BH_Emissive", name="slit"), "censer")
    V, F = M.sphere(0.018, 6, 4, center=c + (0, 0, -0.105))
    sb.add(M.Part(V, F, "BH_Bronze", name="finial"), "censer")
    # ember smoke wisp above the lid
    V, F = M.lathe([(0.0, 0.07), (0.02, 0.1), (0.012, 0.14), (0.0, 0.16)], 6)
    sb.add(M.Part(V, F, "BH_Emissive", name="ember_top").move(c), "censer")


def hymn_book():
    """Weapon space (left hand: knuckles on -X). Held by the spine: covers extend distal-down (-X)."""
    parts = []
    w, t, h = 0.15, 0.045, 0.21
    V, F = M.box(w, t, h, center=(-w / 2 + 0.01, 0, 0))
    parts.append(M.bevel(M.Part(V, F, "BH_Leather", name="cover"), 0.006, 1))
    V, F = M.box(w * 0.94, t * 1.08, h * 0.93, center=(-w / 2 + 0.002, 0, 0))
    parts.append(M.Part(V, F, "BH_Horn", name="pages"))
    V, F = M.box(0.04, t * 1.12, 0.04, center=(-w * 0.6, 0, 0))
    parts.append(M.Part(V, F, "BH_Bronze", name="clasp"))
    # red ribbon marker
    V, F = M.box(0.012, 0.003, 0.08, center=(-w * 0.3, 0, -h / 2 - 0.035))
    parts.append(M.Part(V, F, "BH_Cloth_Secondary", name="ribbon"))
    return parts
