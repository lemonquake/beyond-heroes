"""Goblin Summoner (bh-010, Builder A; goblin support / summoner): a stooped, scrawny grey-green goblin witch-doctor.
A carved wooden tribal mask pushed up on top of its head with a tall fan of red and black feathers (the silhouette
key), white bone paint on the face, drooping ears with bone plugs, a ragged hide cloak over the shoulders and back,
a hide war-drum slung on the left hip (bone drumstick in the belt), a belt of trinkets (teeth, coins, a glowing
bottle, little bones) and a crooked forked staff with a rat skull lashed in the fork and smoking pouches glowing with
sickly green embers. ~1.15 m to the crown of the head (the feathers rise to ~1.4 m). Kit: greenskin_kit."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, dome, smoothstep, front_y, back_y  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import enemy_bandit_cutthroat as BK  # noqa: E402
import kit_a_common as A  # noqa: E402

S = 0.64
PROPS = proportions(
    S,
    pelvis_h=0.49, hip_h=0.465, knee_h=0.26, ankle_h=0.05, ball_fwd=0.1, ball_h=0.02, toe_len=0.055,
    heel_back=0.04, hip_x=0.08,
    hips_len=0.07, spine_len=0.12, chest_len=0.145, neck_len=0.05, head_len=0.2,
    clav_x0=0.025, clav_drop=0.03, shoulder_x=0.115, upper_len=0.22, fore_len=0.21, hand_len=0.08, grip_x=0.06,
    grip_drop=0.013,
)
L = K.levels(PROPS)

PALETTE = "goblin_summoner"
PALETTE_COLORS = {
    "BH_Skin": ((0.1, 0.14, 0.085), 0.0, 0.6, None, 0.0, 1.0),              # grey-green
    "BH_Flesh": ((0.05, 0.065, 0.04), 0.0, 0.6, None, 0.0, 1.0),            # inner ears, mottling
    "BH_Fur": ((0.22, 0.14, 0.075), 0.0, 0.95, None, 0.0, 1.0),             # tan hide (cloak, loincloth)
    "BH_Leather": ((0.075, 0.045, 0.025), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Bone": ((0.62, 0.57, 0.44), 0.0, 0.6, None, 0.0, 1.0),              # bone paint, skull, teeth
    "BH_Wood": ((0.13, 0.08, 0.04), 0.0, 0.75, None, 0.0, 1.0),             # mask, staff, drum shell
    "BH_Cloth_Primary": ((0.46, 0.07, 0.03), 0.0, 0.85, None, 0.0, 1.0),    # red feathers / red paint
    "BH_Cloth_Secondary": ((0.2, 0.16, 0.085), 0.0, 0.95, None, 0.0, 1.0),  # burlap pouches
    "BH_Horn": ((0.44, 0.36, 0.23), 0.0, 0.75, None, 0.0, 1.0),             # drum heads
    "BH_Hair": ((0.025, 0.025, 0.03), 0.0, 0.6, None, 0.0, 1.0),            # black feathers
    "BH_Gold": ((0.6, 0.42, 0.16), 1.0, 0.35, None, 0.0, 1.0),              # coins
    "BH_Shadow": ((0.025, 0.02, 0.015), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.55, 1.0, 0.25), 0.0, 0.4, (0.5, 1.0, 0.2), 7.0, 1.0),  # sickly green embers / eyes
}

CLIPS = ["staff_1", "cast_quick", "cast_area", "cast_weapon", "boss_summon"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    # narrow chest, pot belly, hunched upper back
    return [
        (zh - 0.05, 0.084, 0.06, 0.064, 0.0, 0.0),
        (zh + 0.02, 0.088, 0.072, 0.064, 0.06, 0.0),
        (zs + 0.03, 0.088, 0.086, 0.06, 0.14, -0.006),
        (zs + 0.09, 0.09, 0.078, 0.07, 0.08, 0.0),
        (zc + 0.05, 0.1, 0.066, 0.088, 0.03, 0.012),
        (zn - 0.05, 0.112, 0.06, 0.095, 0.01, 0.024),
        (zn - 0.015, 0.098, 0.054, 0.08, 0.0, 0.026),
        (zn + 0.01, 0.052, 0.04, 0.05, 0.0, 0.014),
    ]


ROWS = torso_rows()
HEAD = [  # (dz, rx, ryf, ryb, keel, cy): long lower face, narrow jaw, domed skull, head jutting forward
    (-0.036, 0.026, 0.026, 0.026, 0.0, -0.036),
    (-0.016, 0.048, 0.064, 0.036, 0.1, -0.034),
    (0.008, 0.064, 0.078, 0.048, 0.12, -0.028),
    (0.035, 0.074, 0.084, 0.062, 0.1, -0.02),
    (0.065, 0.082, 0.08, 0.078, 0.06, -0.012),
    (0.1, 0.086, 0.074, 0.088, 0.02, -0.004),
    (0.135, 0.082, 0.064, 0.086, 0.0, 0.0),
    (0.165, 0.064, 0.05, 0.07, 0.0, 0.004),
    (0.186, 0.032, 0.026, 0.036, 0.0, 0.006),
]
HDY = -0.022      # head carried forward


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    V, F = torso_loft(ROWS, n=20, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    rng = np.random.default_rng(8)
    for i in range(5):   # mottling on the back
        z = L["spine"] + 0.03 + 0.18 * rng.random()
        x = (rng.random() - 0.5) * 0.14
        add(K.blob((x, back_y(ROWS, x, z) - 0.004, z), 0.024 + 0.01 * rng.random(), "BH_Flesh",
                   scale=(1.2, 0.35, 0.9), n=8, rings=4), weights=TW)
    # white bone paint: ribs painted across the chest
    for k in range(3):
        z = L["chest"] + 0.02 + 0.035 * k
        for sx in (1, -1):
            pts = [(sx * (0.012 + 0.07 * t), front_y(ROWS, 0.07 * t, z - 0.02 * t * t) - 0.003, z - 0.02 * t * t)
                   for t in np.linspace(0, 1, 5)]
            add(K.rtube(pts, (0.007, 0.003), "BH_Bone", n=4, up=(0, -1, 0)), weights=TW)

    loincloth(body)
    trinket_belt(body)
    drum(body)

    for s in ("L", "R"):
        K.leg(body, s, [(0.048, 0.05), (0.042, 0.044), (0.032, 0.034), (0.034, 0.034), (0.032, 0.034),
                        (0.021, 0.023)], "BH_Skin", bow=0.04, n=10)
        K.bare_foot(body, s, "BH_Skin", length=0.19, width=0.04, height=0.043, claw_mat="BH_Bone", toes=3,
                    toe_r=0.012)
        k = body.head("shin." + s)
        sx = 1 if s == "L" else -1
        add(K.blob(k + (sx * 0.042, -0.02, 0), 0.03, "BH_Skin", n=8, rings=5),
            weights=lambda V, s=s: [{"thigh." + s: 0.5, "shin." + s: 0.5}] * len(V))
        # bone anklet
        a = body.tail("shin." + s)
        for j in range(6):
            ang = 2 * math.pi * j / 6
            add(K.blob(a + (0.032 * math.cos(ang), 0.032 * math.sin(ang), 0.035), 0.009, "BH_Bone", n=5, rings=3),
                "shin." + s)

    for s in ("L", "R"):
        K.arm(body, s, [(0.034, 0.034), (0.028, 0.029), (0.024, 0.025), (0.026, 0.026), (0.028, 0.026),
                        (0.02, 0.019)], "BH_Skin", n=10, deltoid=0.035)
        K.hand(body, s, "BH_Skin", scale=0.95, claws="BH_Bone")
        fa, ha = body.head("forearm." + s), body.head("hand." + s)
        for u in (0.7, 0.82):   # bone bangles
            q = fa + (ha - fa) * u
            d = normalize(ha - fa)
            V, F = M.tube([q - d * 0.008, q + d * 0.008], [(0.032, 0.032)] * 2, n=10, up=(0, -1, 0))
            add(M.Part(V, F, "BH_Bone" if u < 0.8 else "BH_Leather", name="bangle"), "forearm." + s)

    cloak(body)
    head(body)
    mask_and_feathers(body)
    necklace(body)
    K.weapon_to_socket(body, "R", rat_staff())


# ================================================================================================= clothing
def _seat(z_top, z_bot, leg, cw):
    def wfn(V):
        out = []
        for v in V:
            s = float(smoothstep(z_top, z_bot, v[2])) * leg
            side = float(smoothstep(-cw, cw, v[0]))
            d = {"hips": 1 - s}
            if s * side > 1e-3:
                d["thigh.L"] = s * side
            if s * (1 - side) > 1e-3:
                d["thigh.R"] = s * (1 - side)
            out.append(d)
        return out
    return wfn


def loincloth(body):
    add = body.add
    zh = L["hips"]
    V, F = torso_loft([(zh - 0.085, 0.092, 0.07, 0.072, 0.0), (zh - 0.03, 0.094, 0.072, 0.072, 0.0),
                       (zh + 0.035, 0.092, 0.074, 0.07, 0.0)], n=20)
    add(M.Part(V, F, "BH_Fur", name="seat"), weights=_seat(zh + 0.02, zh - 0.09, 0.7, 0.03))
    for k, (ang, ln, w) in enumerate(((-90, 0.21, 0.1), (90, 0.22, 0.12), (-30, 0.15, 0.06), (210, 0.15, 0.06))):
        a = math.radians(ang)
        c = np.array([0.092 * math.cos(a), 0.078 * math.sin(a), zh + 0.01])
        out = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        tan = np.array([-out[1], out[0], 0.0])

        def fn(u, v, c=c, out=out, tan=tan, ln=ln, w=w, k=k):
            end = ln * (1 - 0.25 * abs(math.sin(u * 7 + k)))
            return c + tan * (u - 0.5) * w * (1 - 0.3 * v) + out * (0.012 + 0.03 * v) + np.array([0, 0, -end * v])
        V, F = M.grid(fn, 4, 5)
        fl = M.Part(V, F, "BH_Fur", name="flap")
        if np.dot(np.cross(fl.V[1] - fl.V[0], fl.V[4] - fl.V[0]), out) < 0:
            fl.flip()
        centre = abs(math.cos(a)) < 0.5      # front / back flaps hang between the legs: soft L/R blend
        add(M.solidify(fl, 0.008, offset=1.0),
            weights=_seat(zh, zh - 0.22, 0.45, 0.09) if centre else _seat(zh, zh - 0.22, 0.7, 0.02))


def trinket_belt(body):
    add = body.add
    zh = L["hips"]
    z = zh + 0.03
    belt = K.rtube([(0.098 * math.cos(a), 0.08 * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, 17)], 0.009,
                   "BH_Leather", n=6, up=(0, 0, 1), cap=False)
    add(belt, "hips")
    w = _seat(zh, zh - 0.2, 0.4, 0.03)
    # trinkets round the front / sides (angles: -90 = front)
    items = ((-125, "teeth"), (-100, "coin"), (-60, "bottle"), (-35, "bones"), (-150, "coin"), (-10, "teeth"),
             (200, "bones"))
    for ang, kind in items:
        a = math.radians(ang)
        p = np.array([0.104 * math.cos(a), 0.086 * math.sin(a), z - 0.004])
        out = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        if kind == "teeth":
            add(K.rtube([p, p + (0, 0, -0.05)], 0.0025, "BH_Leather", n=4), weights=w)
            for j in range(3):
                q = p + out * 0.004 + np.array([0, 0, -0.018 - 0.015 * j])
                add(K.cone(q, q + out * 0.004 + np.array([0, 0, -0.022]), 0.005, "BH_Bone", n=4), weights=w)
        elif kind == "coin":
            add(K.rtube([p, p + (0, 0, -0.035)], 0.0025, "BH_Leather", n=4), weights=w)
            V, F = M.lathe([(0.0, -0.002), (0.017, -0.002), (0.017, 0.002), (0.0, 0.002)], 8)
            add(M.Part(V, F, "BH_Gold", name="coin").rot(Rx(90)).rot(Rz(ang + 90)).move(p + (0, 0, -0.05) + out * 0.004),
                weights=w)
        elif kind == "bottle":
            c = p + out * 0.016 + np.array([0, 0, -0.035])
            V, F = M.lathe([(0.0, -0.028), (0.018, -0.026), (0.021, -0.01), (0.016, 0.01), (0.007, 0.018),
                            (0.007, 0.03), (0.0, 0.03)], 8)
            add(M.Part(V, F, "BH_Emissive", name="bottle").move(c), weights=w)
            add(K.blob(c + (0, 0, 0.033), 0.008, "BH_Wood", n=5, rings=3), weights=w)
        else:
            for j, dx in enumerate((-0.01, 0.008)):
                q = p + out * 0.006 + np.array([dx, 0, -0.01])
                add(K.rtube([q, q + (dx * 0.5, 0, -0.06)], 0.005, "BH_Bone", n=5), weights=w)
                add(K.blob(q + (dx * 0.5, 0, -0.062), 0.008, "BH_Bone", n=5, rings=3), weights=w)
    # bone drumstick tucked through the belt at the back-left
    q = np.array([0.07, 0.08, z])
    add(K.rtube([q + (-0.02, 0.01, 0.1), q, q + (0.02, -0.005, -0.1)], [0.009, 0.008, 0.007], "BH_Bone", n=6), "hips")
    add(K.blob(q + (-0.022, 0.012, 0.11), 0.017, "BH_Bone", n=7, rings=4), "hips")


def drum(body):
    """Hide war-drum slung on the left hip (axis tilted), cord lacing, strap over the right shoulder."""
    add = body.add
    zh = L["hips"]
    c = np.array([0.165, -0.005, zh - 0.03])
    R = Ry(70) @ Rx(-12)
    h, r = 0.12, 0.09
    parts = []
    V, F = M.lathe([(0.0, -h / 2), (r * 0.92, -h / 2), (r, -h * 0.25), (r * 1.04, 0.0), (r, h * 0.25),
                    (r * 0.92, h / 2), (0.0, h / 2)], 14)
    parts.append(M.Part(V, F, "BH_Wood", name="drum"))
    for sz in (1, -1):
        V, F = M.lathe([(0.0, sz * (h / 2 + 0.004)), (r * 0.97, sz * (h / 2 + 0.002)), (r * 0.97, sz * (h / 2 - 0.006))],
                       14, cap=False)
        hd = M.Part(V, F, "BH_Horn", name="drumhead")
        if sz < 0:
            hd.flip()
        parts.append(hd)
        V, F = M.lathe([(r * 0.99, sz * h / 2 - 0.006), (r * 1.03, sz * h / 2), (r * 0.99, sz * h / 2 + 0.006),
                        (r * 0.95, sz * h / 2)], 14, cap=False)
        parts.append(M.Part(V, F, "BH_Leather", name="hoop"))
    zig = []
    for j in range(13):
        a = 2 * math.pi * j / 12
        zz = (h / 2 - 0.004) * (1 if j % 2 == 0 else -1)
        zig.append((r * 1.03 * math.cos(a), r * 1.03 * math.sin(a), zz))
    parts.append(K.rtube(zig, 0.003, "BH_Leather", n=4, up=(0, 0, 1)))
    # painted red hand-mark on the outer head
    parts.append(K.blob((0, 0, h / 2 + 0.005), 0.028, "BH_Cloth_Primary", scale=(1.0, 0.8, 0.12), n=8, rings=3))
    for p in parts:
        p.rot(R).move(c)
        add(p, "hips")
    # baldric: drum -> across the back -> over the right shoulder -> down the chest -> drum
    zn, zc = L["neck"], L["chest"]
    pts = [c + (-0.02, 0.03, 0.05), (0.06, back_y(ROWS, 0.06, zh + 0.12) + 0.008, zh + 0.12),
           (-0.04, back_y(ROWS, -0.04, zc + 0.08) + 0.008, zc + 0.08), (-0.085, 0.03, zn - 0.02),
           (-0.08, -0.04, zn - 0.035), (-0.03, front_y(ROWS, -0.03, zc + 0.08) - 0.008, zc + 0.08),
           (0.06, front_y(ROWS, 0.06, zh + 0.1) - 0.008, zh + 0.1), c + (-0.03, -0.03, 0.05)]
    add(K.rtube(pts, (0.01, 0.004), "BH_Leather", n=5, up=(0, 0, 1), p=3.0), weights=K.torso_w(PROPS))


def cloak_w():
    zc, zs, zh = L["chest"], L["spine"], L["hips"]
    base = K.zspec_w([(zh + 0.01, "hips"), (zs + 0.03, "spine"), (zc - 0.01, "spine"), (zc + 0.06, "chest")])

    def wfn(V):
        W = base(V)
        out = []
        for v, w in zip(V, W):
            if v[2] < zh:
                s = float(smoothstep(zh, zh - 0.25, v[2])) * 0.35
                side = float(smoothstep(-0.05, 0.05, v[0]))
                w = {k: x * (1 - s) for k, x in w.items()}
                if s * side > 1e-3:
                    w["thigh.L"] = s * side
                if s * (1 - side) > 1e-3:
                    w["thigh.R"] = s * (1 - side)
            out.append(w)
        return out
    return wfn


def cloak(body):
    """Ragged hide cloak: shoulder mantle (open at the front, bone toggle) + a back panel to the knees."""
    add = body.add
    zn, zc, zs, zh = L["neck"], L["chest"], L["spine"], L["hips"]
    rings = []
    for k, (z, g) in enumerate(((zn + 0.008, 0.012), (zn - 0.03, 0.02), (zn - 0.07, 0.04), (zc + 0.03, 0.058))):
        fr = np.linspace(0.12, 0.88, 17)
        r = BK.ring_frac(ROWS, max(z, zn - 0.01) if k == 0 else z, g, fr, p=2.2)
        r[:, 2] = z
        if k == 3:
            r[:, 2] -= np.array([0.03 * abs(math.sin(i * 1.9)) for i in range(len(fr))])
        rings.append(r)
    V, F = M.loft(rings[::-1], cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_Fur", name="mantle"), 0.01, offset=1.0), weights=K.torso_w(PROPS))
    add(K.rtube([rings[0][0] + (0, -0.006, 0), (0, front_y(ROWS, 0, zn - 0.012) - 0.02, zn - 0.02),
                 rings[0][-1] + (0, -0.006, 0)], 0.005, "BH_Leather", n=4), "chest")
    add(K.rtube([(-0.018, front_y(ROWS, 0, zn - 0.02) - 0.03, zn - 0.02),
                 (0.018, front_y(ROWS, 0, zn - 0.02) - 0.03, zn - 0.02)], 0.009, "BH_Bone", n=6), "chest")

    def fn(u, v):
        zt = zc + 0.05
        zb = zh - 0.24 + 0.07 * abs(math.sin(u * 11.0 + 0.7)) + 0.03 * math.sin(u * 23.0)
        z = zt + (zb - zt) * v
        hw = 0.1 + 0.07 * v
        x = (u - 0.5) * 2 * hw
        zq = max(z, zs)
        y = back_y(ROWS, x * 0.9, zq) + 0.03 + 0.05 * v
        return (x, y, z)
    V, F = M.grid(fn, 8, 8)
    add(M.solidify(M.Part(V, F, "BH_Fur", name="cloak").flip(), 0.009, offset=1.0), weights=cloak_w())
    # stitched hide patches
    for (u, v) in ((0.3, 0.3), (0.7, 0.6)):
        q = np.array(fn(u, v))
        add(K.blob(q + (0, 0.008, 0), 0.03, "BH_Horn", scale=(1.0, 0.25, 0.8), n=8, rings=4), weights=cloak_w())


# ================================================================================================= head
def head(body):
    add = body.add
    z0 = L["head"]
    H = K.head_rows(HEAD, z0, sx=1.08, sy=1.06, sz=1.05, dy=HDY)
    V, F = M.tube([(0, 0.02, L["neck"] - 0.02), (0, 0.0, L["neck"] + 0.03), (0, -0.018 + HDY, z0 + 0.02)],
                  [(0.034, 0.032), (0.03, 0.028), (0.033, 0.031)], n=10, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(L["neck"] - 0.01, "chest"), (L["neck"] + 0.02, "neck"), (z0, "neck"), (z0 + 0.02, "head")]))
    V, F = torso_loft(H, n=20, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    zb = z0 + 0.082
    yb = K.front_of(H, 0, zb) + 0.004
    add(K.rtube([(-0.055, yb + 0.018, zb - 0.01), (-0.022, yb - 0.004, zb + 0.002), (0.0, yb, zb - 0.004),
                 (0.022, yb - 0.004, zb + 0.002), (0.055, yb + 0.018, zb - 0.01)], 0.012, "BH_Skin", n=6,
                up=(0, -1, 0)), "head")
    for sx in (1, -1):
        ye = K.front_of(H, 0.03, z0 + 0.062)
        add(K.blob((sx * 0.03, ye + 0.006, z0 + 0.062), 0.018, "BH_Shadow", scale=(1.2, 0.5, 0.8), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.031, ye - 0.001, z0 + 0.062), 0.009, "BH_Emissive", scale=(1.2, 0.6, 0.9), n=6,
                   rings=4), "head")
        # white bone-paint stripes down the cheeks
        for j in range(2):
            x = sx * (0.04 + 0.014 * j)
            pts = [(x, K.front_of(H, x, z) - 0.001, z) for z in (z0 + 0.045, z0 + 0.02, z0 - 0.005)]
            add(K.rtube(pts, (0.0045, 0.002), "BH_Bone", n=4, up=(0, -1, 0)), "head")
    # long thin hooked nose with a bone ring
    yn = K.front_of(H, 0, z0 + 0.06)
    tip = (0, yn - 0.085, z0 + 0.012)
    add(K.rtube([(0, yn + 0.005, z0 + 0.074), (0, yn - 0.045, z0 + 0.058), (0, yn - 0.08, z0 + 0.03), tip],
                [(0.012, 0.011), (0.014, 0.012), (0.012, 0.01), (0.006, 0.005)], "BH_Skin", n=8, up=(0, 0, 1)),
        "head")
    add(K.rtube([np.array(tip) + (0, 0.012, -0.004) + 0.012 * np.array([0, math.cos(a), math.sin(a)])
                 for a in np.linspace(0, 2 * math.pi, 9)], 0.0028, "BH_Bone", n=4, cap=False), "head")
    # grin with lower tusks
    zm = z0 - 0.008
    ym = K.front_of(H, 0, zm)
    mouth = [(x, K.front_of(H, x, zm + 5 * x * x) + 0.001, zm + 5 * x * x) for x in np.linspace(-0.045, 0.045, 7)]
    add(K.rtube(mouth, (0.005, 0.004), "BH_Shadow", n=5), "head")
    for sx in (1, -1):
        add(K.cone((sx * 0.02, ym + 0.006, zm - 0.01), (sx * 0.024, ym - 0.004, zm + 0.02), 0.0055, "BH_Bone", n=5),
            "head")
    # drooping ears with bone plugs
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.055)
        root = (sx * (rx - 0.012), cy + 0.012, z0 + 0.055)
        add(K.ear(root, 0.25, 0.11, "BH_Skin", out=(sx * 1.0, 0.3, -0.12), up=(0, 0.2, 1), droop=0.05, thick=0.012,
                  back=0.015), "head")
        add(K.ear(np.array(root) + (sx * 0.028, -0.009, 0.0), 0.18, 0.06, "BH_Flesh", out=(sx * 1.0, 0.3, -0.12),
                  up=(0, 0.2, 1), droop=0.035, thick=0.004), "head")
        plug = np.array(root) + np.array([sx * 0.085, 0.024, -0.01])
        V, F = M.lathe([(0.0, -0.01), (0.012, -0.01), (0.012, 0.01), (0.0, 0.01)], 8)
        add(M.Part(V, F, "BH_Bone", name="plug").rot(Rx(90)).move(plug + (0, -0.004, 0)), "head")


def mask_and_feathers(body):
    """Carved wooden mask pushed up on the crown (face tilted up and forward) with a fan of feathers behind it."""
    add = body.add
    z0 = L["head"]
    top = z0 + 0.19
    parts = []

    # mask shell in local space: face toward -Y, height along Z, then rotated up by 62 deg about X
    def fn(u, v):
        x = (u - 0.5) * 0.13 * (0.75 + 0.25 * math.sin(math.pi * v))
        z = -0.1 + 0.2 * v
        ax = abs(x) / 0.07
        y = -0.03 * (1 - ax * ax) + 0.01 * (v - 0.5) ** 2
        return (x, y, z)
    V, F = M.grid(fn, 7, 8)
    parts.append(M.solidify(M.Part(V, F, "BH_Wood", name="mask"), 0.012, offset=-1.0))
    for sx in (1, -1):
        parts.append(A.ball((sx * 0.03, -0.036, 0.025), 0.02, "BH_Shadow", n=7, rings=4, scale=(1.1, 0.4, 0.75)))
        parts.append(A.ball((sx * 0.034, -0.036, -0.01), 0.018, "BH_Bone", n=6, rings=3, scale=(0.9, 0.25, 0.4)))
        parts.append(A.tube([(sx * 0.02, -0.034, -0.055), (sx * 0.028, -0.05, -0.1)], [0.008, 0.001], "BH_Bone", n=4))
    parts.append(A.tube([(0, -0.03, 0.09), (0, -0.045, 0.02), (0, -0.05, -0.025)], [0.008, 0.014, 0.01],
                        "BH_Cloth_Primary", n=5))    # red painted nose ridge
    parts.append(A.ball((0, -0.03, -0.07), 0.02, "BH_Shadow", n=7, rings=4, scale=(1.4, 0.4, 0.5)))  # mouth hole
    for sx in (1, -1):   # white paint zigzag on the brow
        parts.append(A.tube([(sx * 0.012, -0.036, 0.07), (sx * 0.035, -0.037, 0.06), (sx * 0.05, -0.034, 0.075)],
                            0.0045, "BH_Bone", n=4))
    for p in parts:
        p.rot(Rx(-72)).move((0, -0.03 + HDY, top + 0.03))
        add(p, "head")
    # leather strap round the head
    H = K.head_rows(HEAD, z0, sx=1.08, sy=1.06, sz=1.05, dy=HDY)
    zb = z0 + 0.12
    from bh_body import interp_rows
    r = interp_rows(H, zb)
    ring = [(r[1] * 1.04 * math.cos(a), r[5] + (r[3] if math.sin(a) > 0 else r[2]) * 1.04 * math.sin(a),
             zb + 0.02 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)]
    add(K.rtube(ring, 0.007, "BH_Leather", n=5, up=(0, 0, 1), cap=False), "head")
    # feather fan behind the mask
    base = np.array([0, 0.015 + HDY, top + 0.01])
    for k in range(7):
        a = math.radians(-60 + 20 * k)
        d = normalize(np.array([math.sin(a), 0.35, math.cos(a)]))
        ln = 0.22 - 0.04 * abs(k - 3) / 3
        mat = "BH_Cloth_Primary" if k % 2 == 0 else "BH_Hair"
        add(A.feather(base + d * 0.02, d, ln, 0.05, mat, side=(math.cos(a), 0, -math.sin(a)), bend=-0.12), "head")
        add(A.tube([base, base + d * 0.03], 0.004, "BH_Bone", n=4), "head")
    add(A.ball(base, 0.022, "BH_Bone", n=7, rings=4), "head")
    # two feathers dangling from the right side of the strap
    for j, (dz, mat) in enumerate(((0.0, "BH_Hair"), (-0.02, "BH_Cloth_Primary"))):
        b = np.array([-r[1] - 0.005, 0.01 + HDY, zb + dz])
        add(A.feather(b, (-0.3, 0.2 + 0.1 * j, -1.0), 0.12, 0.035, mat, side=(0, 1, 0), bend=0.05), "head")


def necklace(body):
    add = body.add
    zn = L["neck"]
    pts = []
    for a in np.linspace(math.radians(-170), math.radians(-10), 11):
        pts.append(np.array([0.075 * math.cos(a), 0.012 + 0.07 * math.sin(a), zn - 0.01 + 0.03 * math.sin(a)]))
    add(K.rtube(pts, 0.003, "BH_Leather", n=4), "chest")
    for i, p in enumerate(pts[1:-1]):
        out = normalize(np.array([p[0], p[1] - 0.012, 0.0]))
        add(K.cone(p, p + out * 0.006 + np.array([0, 0, -0.03 - 0.008 * (i % 2)]), 0.0055, "BH_Bone", n=4), "chest")


# ================================================================================================= staff
def rat_staff():
    """Crooked forked staff (weapon space, grip at origin, +Z up): a rat skull lashed into the fork, smoking hide
    pouches glowing with green embers hanging under it, feathers and a bone bead string."""
    parts = []
    pts, prof = [], []
    for i in range(12):
        u = i / 11
        z = -0.62 + 1.02 * u
        pts.append((0.018 * math.sin(u * 9.0) + 0.012 * math.sin(u * 3.1), 0.012 * math.cos(u * 6.0), z))
        r = 0.013 + 0.0025 * math.sin(u * 23) + 0.004 * u
        prof.append((r, r))
    V, F = M.tube(pts, prof, n=7, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    top = np.array(pts[-1])
    # knots
    for u in (0.3, 0.62):
        i = int(u * 11)
        parts.append(A.ball(pts[i], 0.02, "BH_Wood", n=6, rings=4, scale=(1.0, 0.8, 1.3)))
    # fork: two crooked prongs
    fork = []
    for sx in (1, -1):
        pr = [top, top + (sx * 0.035, 0.0, 0.06), top + (sx * 0.06, 0.005, 0.13), top + (sx * 0.05, 0.0, 0.2)]
        parts.append(A.taper(pr, 0.014, 0.005, "BH_Wood", n=6))
        fork.append(pr)
    # rat skull in the fork (snout forward = -Y), green eyes
    c = top + np.array([0.0, -0.005, 0.12])
    parts.append(A.ball(c, 0.034, "BH_Bone", n=8, rings=5, scale=(0.9, 1.1, 0.8)))
    parts.append(A.taper([c + (0, -0.02, -0.004), c + (0, -0.06, -0.014), c + (0, -0.095, -0.024)], 0.022, 0.006,
                         "BH_Bone", n=6))
    for sx in (1, -1):
        parts.append(A.ball(c + (sx * 0.02, -0.022, 0.008), 0.012, "BH_Shadow", n=6, rings=4, scale=(0.8, 0.8, 0.9)))
        parts.append(A.ball(c + (sx * 0.022, -0.028, 0.008), 0.006, "BH_Emissive", n=5, rings=3))
        parts.append(A.taper([c + (sx * 0.004, -0.092, -0.028), c + (sx * 0.004, -0.098, -0.05)], 0.004, 0.001,
                             "BH_Bone", n=4))    # incisors
    # lashing (cord wraps) at the fork
    for dz in (0.0, 0.03):
        ring = [top + (0.028 * math.cos(a), 0.024 * math.sin(a), 0.03 + dz) for a in np.linspace(0, 2 * math.pi, 9)]
        parts.append(A.tube(ring, 0.004, "BH_Leather", n=4, up=(0, 0, 1), cap=False))
    # smoking pouches with green embers
    for k, (a, ln) in enumerate(((30, 0.08), (150, 0.11), (270, 0.065))):
        r = math.radians(a)
        t = top + np.array([0.022 * math.cos(r), 0.022 * math.sin(r), -0.01])
        b = t + np.array([0.015 * math.cos(r), 0.015 * math.sin(r), -ln])
        parts.append(A.tube([t, b], 0.0028, "BH_Leather", n=4, up=(1, 0, 0)))
        pc = b + np.array([0, 0, -0.03])
        parts.append(A.ball(pc, 0.03, "BH_Cloth_Secondary", n=8, rings=5, scale=(1.0, 1.0, 1.15)))
        parts.append(A.tube([b + (0, 0, -0.004), b + (0, 0, 0.006)], 0.012, "BH_Cloth_Secondary", n=6))
        # glowing ember holes + a curl of green smoke
        out = np.array([math.cos(r), math.sin(r), 0.0])
        parts.append(A.ball(pc + out * 0.027, 0.012, "BH_Emissive", n=6, rings=4, scale=(0.5, 0.5, 0.8)))
        sm = [pc + out * 0.03, pc + out * 0.05 + (0, 0, 0.03), pc + out * 0.04 + (0.01, 0, 0.07),
              pc + out * 0.06 + (0, 0.01, 0.11)]
        parts.append(A.taper(sm, 0.01, 0.003, "BH_Emissive", n=5))
    # feathers + bone beads at the fork
    parts.append(A.feather(top + (0.03, 0.01, 0.0), (0.4, 0.2, -1.0), 0.13, 0.034, "BH_Cloth_Primary",
                           side=(0, 1, 0)))
    parts.append(A.feather(top + (-0.03, 0.01, -0.01), (-0.45, 0.2, -1.0), 0.11, 0.03, "BH_Hair", side=(0, 1, 0)))
    for j in range(4):
        parts.append(A.ball(top + (0.036, 0.012, -0.03 - 0.018 * j), 0.008, "BH_Bone", n=5, rings=3))
    # butt: bound with leather
    V, F = M.lathe([(0, -0.66), (0.015, -0.64), (0.018, -0.6), (0.0, -0.58)], 7)
    parts.append(M.Part(V, F, "BH_Leather", name="butt"))
    V, F = M.lathe([(0, -0.07), (0.018, -0.07), (0.019, 0.07), (0, 0.07)], 8)
    parts.append(M.Part(V, F, "BH_Leather", name="grip"))
    return parts
