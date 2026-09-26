"""Townsfolk: the elder (Elder Maelis, Keeper of the Hearth).

An elderly woman, a little stooped (rounded upper back, head carried forward), in a long dress (BH_Cloth_Primary,
tinted) under a layered shawl that drops to a point down the back, a long grey braid over the shawl, a shell
necklace and a gnarled walking staff in the right hand (rigid to hand.R: weapon.R is a non-deforming bone, see the report).
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp

PROPS = proportions(0.92, shoulder_x=0.166 * 0.92, hip_x=0.095 * 0.92)
PALETTE = "town_elder"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.10, 0.13, 0.08)),              # preview: moss-green dress
    "BH_Cloth_Accent": pal((0.30, 0.20, 0.10), 0.92),         # warm brown woollen shawl
    "BH_Cloth_Secondary": pal((0.42, 0.36, 0.26), 0.92),      # undershawl / collar
    "BH_Skin": pal((0.42, 0.26, 0.17), 0.6),
    "BH_Hair": pal((0.40, 0.39, 0.37), 0.7),                  # grey
    "BH_Bone": pal((0.72, 0.64, 0.52), 0.5),                  # shells
    "BH_Wood": pal((0.16, 0.10, 0.05), 0.75),                 # staff
})

E_TORSO = K.torso_rows(chest=0.88, waist=0.95, hip=1.06, depth=1.0, bust=0.012, hump=0.028, shoulder=0.9)
FWD = -0.028          # head carried forward (stoop)


def build(body):
    k = Kit(body)
    rows = E_TORSO
    # ---- long dress
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", n=24, cap1=True, name="bodice")
    sk_rows = K.flare_rows(1.07, 0.06, (0.152, 0.104, 0.116), (0.235, 0.215, 0.235), n=8, curve=0.9)
    sk, _ = K.skirt(sk_rows, "BH_Cloth_Primary", folds=8, amp=0.01)
    k.add(sk, w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))
    K.band(k, rows, 1.06, 1.085, "BH_Cloth_Secondary", g_out=0.012, g_in=0.004, n=24, bev=0.0)
    # sash tails at the left hip
    q, ang = K.on_ring(rows, 1.07, 0.014, 0.2)
    q = np.asarray(q)
    k.add(rope([q, q + (0.01, -0.01, -0.12), q + (0.02, -0.014, -0.24)], 0.011, "BH_Cloth_Secondary"),
          w=k.skirt_w(1.02, 0.6, max_leg=0.5))
    # ---- arms: long sleeves to the wrist, hands
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.4, 0.05, 0.052), (1.0, 0.045, 0.047), (1.6, 0.042, 0.044),
                                         (1.93, 0.046, 0.047)], "BH_Cloth_Primary", n=12)
        K.arm_ring(k, s, 1.9, 0.047, 0.03, "BH_Cloth_Secondary", name="cuff")
        K.mitten(k, s, size=0.95, curl=2.2 if s == "R" else 1.0)
    for s in "LR":
        K.leg_tube(k, s, [(0.15, 0.065, 0.065), (1.0, 0.045, 0.047), (1.9, 0.035, 0.037)], "BH_Cloth_Secondary", n=8)
    K.shoes(k, "BH_Leather", sole="BH_Wood", width=0.9)
    # ---- shawl (two layers) + necklace
    shawl(k, rows)
    necklace(k, rows)
    # ---- head, hair, braid
    hr = K.head(k, jaw=0.92, width=0.95, fwd=FWD, nose=1.05, brow=0.8, neck_r=0.045)
    hair(k, hr)
    staff(k)
    K.check_normals(body, "elder")


def shawl_w(k):
    def wfn(V):
        out = []
        for v in V:
            s = float(smoothstep(0.12 * k.s, 0.26 * k.s, abs(v[0])))
            side = "L" if v[0] > 0 else "R"
            d = {"chest": 1.0 - 0.5 * s}
            lo = float(smoothstep(1.25 * k.s, 1.12 * k.s, v[2]))       # lowest point follows the spine
            if lo > 0:
                d["chest"] -= 0.4 * lo
                d["spine"] = 0.4 * lo
            if s > 1e-4:
                d["shoulder." + side] = 0.3 * s
                d["upper_arm." + side] = 0.2 * s
            out.append(d)
        return out
    return wfn


def shawl_surface(nu, nv, gap, r0, r1, drop_front, drop_side, drop_back, z0, back_hug=1.0):
    rings = []
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for i in range(nu):
            th = gap + (2 * math.pi - 2 * gap) * i / (nu - 1)
            st, ct = math.sin(th), math.cos(th)     # ct > 0 front, ct < 0 back
            rx = r0[0] + (r1[0] - r0[0]) * v
            if ct > 0:
                ry = r0[1] + (r1[1] - r0[1]) * v
                drop = lerp(drop_side, drop_front, ct * ct)
            else:
                # at the back the shawl hugs the (rounded) back instead of flaring out
                ry = r0[2] + (r1[2] - r0[2]) * v * (1 - back_hug * 0.55 * ct * ct)
                drop = lerp(drop_side, drop_back, ct ** 4)
            z = z0 - drop * v ** 1.6
            ring.append((rx * st, 0.012 - ry * ct, z))
        rings.append(np.array(ring))
    return rings[::-1]


def shawl(k, rows):
    # outer shawl: covers the shoulders and upper arms, a long point down the back, loose ends in front
    rings = shawl_surface(44, 8, math.radians(10), (0.10, 0.085, 0.09), (0.30, 0.20, 0.24),
                          0.34, 0.23, 0.52, 1.575)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sh = M.solidify(P_(V, F, "BH_Cloth_Accent", "shawl"), 0.012, offset=1.0)
    k.add(sh, w=shawl_w(k))
    hem = rings[0]
    V, F = M.tube(hem, [(0.01, 0.01)] * len(hem), n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Cloth_Accent", "shawl_hem"), w=shawl_w(k))
    # fringe tassels along the back point
    for i in range(0, len(hem), 3):
        p = hem[i]
        if p[2] > 1.25 or p[1] < 0.05:
            continue
        k.add(rope([p, p + (0, 0.004, -0.05)], 0.004, "BH_Cloth_Accent", n=4), w=shawl_w(k))
    # inner layer: short collar shawl in linen
    rings = shawl_surface(36, 5, math.radians(22), (0.09, 0.075, 0.085), (0.22, 0.16, 0.16), 0.12, 0.1, 0.12, 1.60)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "collar"), 0.01, offset=1.0), w=shawl_w(k))
    # wooden toggle pin closing the shawl on the chest
    V, F = M.tube([(-0.035, -0.19, 1.39), (0.035, -0.19, 1.395)], [(0.008, 0.008)] * 2, n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Wood", "pin"), "chest")


def necklace(k, rows):
    pts = []
    for a in np.linspace(-0.9, 0.9, 11):
        x = 0.07 * math.sin(a)
        z = 1.47 - 0.05 * math.cos(a) ** 2
        pts.append((x, front_y(rows, x, z) - 0.026, z))
    k.add(rope(pts, 0.003, "BH_Leather"), "chest")
    for i, (x, z) in enumerate(((-0.045, 1.44), (-0.02, 1.425), (0.0, 1.418), (0.02, 1.425), (0.045, 1.44))):
        y = front_y(rows, x, z) - 0.03
        s = 0.013 if i == 2 else 0.009
        V, F = M.sphere(s, 8, 5, center=(x, y, z - s * 0.6), scale=(1, 0.5, 1.2))
        k.add(P_(V, F, "BH_Bone", "shell"), "chest")


def hair(k, hr):
    line = K.hairline(1.74, 1.67, 1.61)
    V, F = K.head_shell(hr, lambda v: 0.012 + 0.004 * (1 - v), line, nu=24, nv=6, top_bulge=0.01)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.008, offset=-1.0), "head")
    # centre parting ridge
    V, F = M.tube([(0, -0.07 + FWD, 1.765), (0, -0.02 + FWD, 1.815), (0, 0.04 + FWD, 1.815)], [(0.004, 0.003)] * 3,
                  n=5, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Skin", "parting"), "head")
    # long braid: from the nape down the back over the shawl
    yb = K.back_y(hr, 0, 1.64) + 0.01
    pts = [(0.0, yb, 1.64), (0.0, yb + 0.04, 1.54), (0.0, 0.17, 1.44), (0.0, 0.2, 1.33), (0.0, 0.205, 1.22),
           (0.0, 0.2, 1.12)]
    wf = k.zw([(1.40, "chest"), (1.52, "neck"), (1.60, "head")])
    pts = np.array(pts)
    # continuous braid: dense polyline with a lobed radius (reads as plaits), slight side-to-side weave
    dense = []
    prof = []
    for i in range(len(pts) - 1):
        for t in np.linspace(0, 1, 6, endpoint=False):
            j = len(dense)
            c = pts[i] + (pts[i + 1] - pts[i]) * t
            dense.append(c + (0.006 * math.sin(j * math.pi / 2), 0, 0))
            r = 0.026 * (1 - 0.3 * j / (6 * len(pts)))
            lobe = 0.8 + 0.2 * abs(math.cos(j * math.pi / 3))
            prof.append((r * lobe, r * 0.75 * lobe))
    dense.append(pts[-1])
    prof.append((0.014, 0.012))
    V, F = M.tube(dense, prof, n=8, up=(0, 1, 0))
    k.add(P_(V, F, "BH_Hair", "braid"), w=wf)
    k.add(rope([pts[-1] + (0, 0, 0.012), pts[-1] - (0, 0, 0.004)], 0.02, "BH_Cloth_Secondary"), w=wf)
    V, F = M.sphere(0.017, 8, 5, center=pts[-1] + (0, 0.004, -0.04), scale=(1, 0.8, 1.6))
    k.add(P_(V, F, "BH_Hair", "tuft"), w=wf)


def staff(k):
    """Gnarled walking staff, upright in the modeling pose, rigid to weapon.R."""
    b = k.b
    g = b.head("weapon.R")
    top = g + np.array([0.0, -0.035, 0.36 * k.s])
    foot = np.array([g[0] - 0.03, g[1] - 0.09, 0.0])
    d = normalize(top - foot)
    L = np.linalg.norm(top - foot)
    pts = []
    for t in np.linspace(0, 1, 9):
        p = foot + (top - foot) * t
        p = p + np.array([0.008 * math.sin(t * 11), 0.006 * math.cos(t * 7), 0])
        pts.append(p)
    prof = [(0.017, 0.017)] * 7 + [(0.021, 0.021), (0.024, 0.024)]
    V, F = M.tube(pts, prof, n=8, up=(0, -1, 0))
    b.add(P_(V, F, "BH_Wood", "staff"), "hand.R")
    # knotted crook at the top
    c = top + np.array([0.0, 0.0, 0.03])
    V, F = M.sphere(0.035, 10, 6, center=c, scale=(1.0, 0.9, 1.1))
    b.add(K.outward(P_(V, F, "BH_Wood", "knob")), "hand.R")
    # small shell charm tied under the knob
    k.b.add(rope([c + (0.03, 0, -0.02), c + (0.045, -0.005, -0.09)], 0.003, "BH_Leather"), "hand.R")
    V, F = M.sphere(0.014, 8, 5, center=c + (0.046, -0.005, -0.1), scale=(1, 0.5, 1.2))
    k.b.add(P_(V, F, "BH_Bone", "charm"), "hand.R")
