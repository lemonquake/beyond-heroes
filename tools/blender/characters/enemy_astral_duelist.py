"""Astral Duelist (bh-012, Builder E; The Shattered Orrery, blinking duelist): a lean, elegant ~1.9 m figure whose body
is dark star-flecked glass (starglass: BH_Stone + tiny BH_Emissive specks) under silver half-armour: a filigreed
left breastplate, a tall left pauldron, silver vambrace on the sword arm, knee cops and greaves, a gorget and a belt
with a left tasset. Silver filigree curls trace the bare glass. The head carries a featureless mirror-smooth face plate
(BH_Aether palette entry = mirror silver with a faint pale glow). A short cape of midnight cloth with a violet hem
hangs from the shoulders. Weapon: a long thin rapier (weapon.R) with a silver basket hilt and a violet glowing edge.

Clips: sword_1, sword_2, sword_3 (quick combo), sword_heavy, dagger_heavy (dash lunge). Kit: kit_e_orrery.py."""
import math

import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import Body, torso_loft, front_y, back_y, fist, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_hollow_soldier as HS
import kit_e_orrery as O

KD = 1.9 / 1.8
PROPS = proportions(KD, shoulder_x=0.178 * KD, hip_x=0.094 * KD, upper_len=0.3 * KD, fore_len=0.28 * KD,
                    hand_len=0.105 * KD)
PALETTE = "astral_duelist"
PALETTE_COLORS = {
    "BH_Stone": O.STARGLASS,                                             # starglass body
    "BH_Steel": ((0.78, 0.8, 0.86), 1.0, 0.25, None, 0.0, 1.0),          # silver armour + filigree
    "BH_Aether": ((0.8, 0.82, 0.92), 0.55, 0.1, (0.42, 0.38, 0.58), 1.0, 1.0),   # mirror face plate
    "BH_Cloth_Primary": O.MIDNIGHT,                                      # cape
    "BH_Cloth_Secondary": O.VIOLET,                                      # cape hem / lining
    "BH_Gold": O.GOLD,                                                   # small accents
    "BH_DarkSteel": O.IRON,
    "BH_Emissive": O.GLOW,                                               # star flecks, blade edge
}
CLIPS = ["sword_1", "sword_2", "sword_3", "sword_heavy", "dagger_heavy"]

TORSO = [(r[0], r[1] * 0.9, r[2] * 0.9, r[3] * 0.92, r[4] * 0.6) for r in K.TORSO]
TORSO_W = K.TORSO_W


def finish_mesh(mesh_ob):
    arm = mesh_ob.parent
    for bn in ("weapon.L", "weapon.R"):
        if bn in arm.data.bones and bn in mesh_ob.vertex_groups:
            arm.data.bones[bn].use_deform = True


def socket_parts(body, side, parts):
    A = body.axes("weapon." + side)
    o = body.head("weapon." + side)
    for p in parts:
        loc = np.stack([p.V[:, 0], p.V[:, 2], -p.V[:, 1]], 1)
        p.V = o + loc @ A.T
    return parts


# ================================================================================================= rapier
def rapier():
    parts = []
    parts.append(WP._blade(0.07, 1.0, 0.026, 0.012, 0.0045, tip=0.1, n_sec=6, fuller=False, mat="BH_Steel"))
    for sx in (1, -1):   # violet glowing edges
        V, F = M.box(0.005, 0.005, 0.82, center=(sx * 0.0155, 0, 0.47))
        e = O.P(V, F, "BH_Emissive", "edge")
        e.V[:, 0] = e.V[:, 0] - sx * (e.V[:, 2] - 0.06) * 0.0105 / 0.82 * (e.V[:, 2] > 0.4)
        parts.append(e)
    parts.append(O.tube([(0, 0, 0.9), (0, 0, 1.005)], [0.004, 0.001], "BH_Emissive", n=4))
    parts.append(O.ring((0, 0, 0.055), (0, 0, 1), 0.045, 0.006, "BH_Steel", n=18, m=5))      # cup rim
    parts.append(O.dome((0, 0, 0.045), (0, 0, 1), 0.045, "BH_Steel", n=16, rings=3, depth=0.28))
    parts.append(O.tube([(-0.075, 0, 0.05), (0.075, 0, 0.05)], [0.007, 0.007], "BH_Steel", n=6))   # quillons
    for sx in (1, -1):
        parts.append(O.ball((sx * 0.078, 0, 0.05), 0.011, "BH_Gold", n=6, rings=4))
    # basket bars sweeping from the cup down to the pommel around the knuckle side
    for k, ang in enumerate((-35, 0, 35)):
        a = math.radians(ang)
        pts = []
        for t in np.linspace(0, 1, 7):
            r = 0.044 * (1 - t) + 0.012 * t + 0.03 * math.sin(math.pi * t)
            pts.append((r * math.cos(a), r * math.sin(a) * 0.7, 0.05 - 0.16 * t))
        parts.append(O.tube(pts, 0.004, "BH_Steel", n=4))
    parts.append(WP._grip(-0.1, 0.04, 0.012, 5, mat="BH_DarkSteel"))
    parts.append(WP._pommel(-0.12, 0.018, mat="BH_Gold"))
    return parts


# ================================================================================================= helpers
def curl(center, normal, r0, turns, mat="BH_Steel", rt=0.0035, up=(0, 0, 1), flip=1.0, n=16):
    """Filigree curl: a flat spiral in the plane normal to `normal`."""
    R = np.stack([normalize(np.cross(up, normal)), normalize(up), normalize(normal)], 1)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = flip * 2 * math.pi * turns * t
        r = r0 * (1 - 0.8 * t)
        pts.append(np.asarray(center, float) + R @ np.array([r * math.cos(a), r * math.sin(a), 0.0]))
    return O.tube(pts, rt, mat, n=4)


def on_front(x, z, g):
    return np.array([x, front_y(TORSO, x, z) - g, z])


# ================================================================================================= build
def build(real: Body):
    b = O.ScaledP(real, KD)
    add = b.add
    specks = []
    # ---------------------------------------------------------------- starglass body
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.9], n=24, cap0=True, cap1=True)
    torso = O.P(V, F, "BH_Stone", "torso")
    add(torso.copy(), weights=TORSO_W)
    specks.append((O.surface_specks(torso, 44, 0.006, seed=3, lift=0.004), TORSO_W))
    V, F = M.tube([(0, 0.0, 1.46), (0, -0.005, 1.54), (0, -0.01, 1.62)], [(0.045, 0.043), (0.04, 0.038), (0.042, 0.04)],
                  n=10, up=(0, -1, 0))
    add(O.P(V, F, "BH_Stone", "neck"), weights=K.HEAD_W)
    head_rows = [(r[0], r[1] * 0.93, r[2] * 0.95, r[3] * 0.93) + tuple(r[4:]) for r in K.HEAD]
    V, F = torso_loft(head_rows, n=20, p=2.1, cap0=True, cap1=True)
    hp = O.P(V, F, "BH_Stone", "head")
    add(hp.copy(), "head")
    specks.append((O.surface_specks(hp, 12, 0.005, seed=5, lift=0.003, zmin=1.72), None))
    # mirror face plate: smooth oval shell over the face
    rows = []
    for z in np.linspace(1.6, 1.795, 7):
        fr = np.linspace(-0.2, 0.2, 11)
        rr = K.ring_frac(head_rows, z, 0.011, fr % 1.0, p=2.1)
        rows.append(rr)
    V, F = M.loft(rows, cap0=False, cap1=False, closed=False)
    add(M.solidify(O.P(V, F, "BH_Aether", "faceplate"), 0.006, offset=1.0), "head")
    edge = [r[0] for r in rows] + [r[-1] for r in rows[::-1]]
    add(O.tube(np.array(edge) + np.array([0, 0.004, 0]), 0.004, "BH_Steel", n=4), "head")
    # a slim silver crest running back over the crown
    crest = [(0, -0.05, 1.8), (0, 0.0, 1.83), (0, 0.06, 1.815), (0, 0.1, 1.76)]
    add(O.tube(crest, [(0.006, 0.014)] * 4, "BH_Steel", n=6), "head")
    # ---------------------------------------------------------------- arms (smooth glass tubes)
    for sx, s in ((1, "L"), (-1, "R")):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = b.head(ua), b.head(fa), b.head(ha)
        pts = [sh + np.array([-sx * 0.035, 0, 0.02]), sh, sh + (el - sh) * 0.45, el, el + (wr - el) * 0.5,
               wr + (wr - el) * 0.05]
        prof = [(0.042, 0.046), (0.05, 0.052), (0.043, 0.045), (0.036, 0.038), (0.034, 0.035), (0.026, 0.028)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        w = b.seg_weights(["chest", "shoulder." + s, ua, fa, ha], power=9)
        armp = O.P(V, F, "BH_Stone", "arm")
        add(armp.copy(), weights=w)
        specks.append((O.surface_specks(armp, 20, 0.005, seed=10 + sx, lift=0.003), w))
        for prt in fist(b.std, s, "BH_Steel", "BH_Stone", gauntlet=True, scale=1.0):
            add(prt, ha)
        # vambrace (both forearms), filigree curl on it
        add(O.tube([el + (wr - el) * 0.35, el + (wr - el) * 0.97], [0.041, 0.034], "BH_Steel", n=12), fa)
        add(O.ring(el + (wr - el) * 0.97, wr - el, 0.035, 0.005, "BH_Gold", n=12, m=4), fa)
    # left pauldron: tall layered silver shell + couter
    sh = b.head("upper_arm.L")
    for k, (dz, r) in enumerate(((0.035, 0.085), (-0.0, 0.092), (-0.035, 0.096))):
        nrm = normalize(np.array([0.6, 0.0, 1.0]))
        add(O.dome(sh + np.array([0.012 * k, 0, dz]), nrm, r, "BH_Steel", n=16, rings=4, depth=0.6), "shoulder.L"
            if k == 0 else "upper_arm.L")
    add(O.ring(sh + np.array([0, 0, 0.035]), normalize(np.array([0.6, 0, 1.0])), 0.085, 0.005, "BH_Gold", n=18, m=4),
        "shoulder.L")
    # high flared collar plate standing behind the left side of the head
    V, F = M.box(0.012, 0.13, 0.12)
    add(O.P(V, F, "BH_Steel", "flare").rot(Ry(-18)).move(sh + np.array([-0.035, 0.02, 0.1])), "shoulder.L")
    el = b.head("forearm.L")
    add(O.dome(el + np.array([0.0, 0.03, 0.0]), (0.3, 1.0, 0.0), 0.045, "BH_Steel", n=12, rings=3, depth=0.5),
        "forearm.L")
    # ---------------------------------------------------------------- breastplate (left half) + filigree
    rings = []
    for z in np.linspace(1.18, 1.47, 7):
        rings.append(K.ring_frac(TORSO, z, 0.012, np.linspace(-0.035, 0.3, 11) % 1.0))
    for r_ in rings:
        pass
    V, F = M.loft([np.array(r_) for r_ in rings], cap0=False, cap1=False, closed=False)
    plate = M.solidify(O.P(V, F, "BH_Steel", "breastplate"), 0.008, offset=1.0)
    add(plate, weights=K.zspec_w([(1.2, "spine"), (1.3, "chest")]))
    edge = [r_[0] for r_ in rings]
    add(O.tube(np.array(edge) + np.array([0, -0.006, 0]), 0.005, "BH_Gold", n=4),
        weights=K.zspec_w([(1.2, "spine"), (1.3, "chest")]))
    # filigree on the bare right chest / abdomen (silver curls over the glass)
    for (x, z, r0, fl) in ((-0.07, 1.4, 0.035, 1), (-0.1, 1.3, 0.03, -1), (-0.05, 1.2, 0.028, 1), (0.02, 1.08, 0.03, -1),
                           (-0.08, 1.1, 0.024, 1)):
        c = on_front(x, z, 0.004)
        add(curl(c, (0, -1, 0.0), r0, 1.4, flip=fl), weights=TORSO_W)
    for (x, z) in ((0.06, 1.38), (0.1, 1.28)):   # small glowing studs on the plate
        add(O.ball(on_front(x, z, 0.024), 0.008, "BH_Emissive", n=6, rings=4), "chest")
    # gorget
    add(O.ring((0, -0.005, 1.475), (0, 0, 1), 0.09, 0.014, "BH_Steel", n=20, m=6, flat=0.8), "chest")
    # belt + left tasset
    V, F = K.band(TORSO, 0.99, 1.03, 0.018, 0.0, n=24)
    add(O.P(V, F, "BH_DarkSteel", "belt"), "hips")
    add(O.ball(on_front(0, 1.01, 0.026), 0.016, "BH_Gold", n=8, rings=5), "hips")
    for k in range(3):
        V, F = M.box(0.13, 0.014, 0.075)
        tp = O.P(V, F, "BH_Steel", "tasset").rot(Rx(12)).rot(Rz(35)).move((0.1 + 0.01 * k, -0.07 - 0.005 * k,
                                                                            0.95 - 0.06 * k))
        add(M.bevel(tp, 0.004, 1), weights=O.const_w({"hips": 0.55, "thigh.L": 0.45}))
    # ---------------------------------------------------------------- legs
    for sx, s in ((1, "L"), (-1, "R")):
        th, sh_ = "thigh." + s, "shin." + s
        h, k, a = b.head(th), b.head(sh_), b.tail(sh_)
        pts = [h + (0, 0, 0.06), h + (k - h) * 0.45, k, k + (a - k) * 0.45, a + (0, 0, 0.02)]
        V, F = M.tube(pts, [(0.078, 0.08), (0.062, 0.065), (0.047, 0.05), (0.047, 0.05), (0.032, 0.034)], n=12,
                      up=(0, -1, 0))
        w = b.seg_weights([th, sh_], power=10)
        lp = O.P(V, F, "BH_Stone", "leg")
        add(lp.copy(), weights=w)
        specks.append((O.surface_specks(lp, 26, 0.005, seed=20 + sx, lift=0.003), w))
        # pelvis seat
        # knee cop + greave
        add(O.dome(k + (0, -0.03, 0.0), (0, -1, 0.1), 0.048, "BH_Steel", n=12, rings=4, depth=0.55), sh_)
        add(O.ring(k + (0, -0.052, 0.0), (0, -1, 0.1), 0.02, 0.005, "BH_Gold", n=10, m=4), sh_)
        rings = []
        for u in np.linspace(0.18, 0.9, 5):
            c = k + (a - k) * u
            rr = 0.052 - 0.014 * u
            rings.append(np.array([c + np.array([rr * 1.05 * math.cos(t), -rr * 1.1 * math.sin(t), 0.0])
                                   for t in np.linspace(math.radians(-20), math.radians(200), 9)]))
        V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
        add(M.solidify(O.P(V, F, "BH_Steel", "greave"), 0.006, offset=-1.0), sh_)
        add(curl(h + (k - h) * 0.45 + np.array([0, -0.064, 0]), (0, -1, 0), 0.028, 1.3, flip=sx), weights=w)
        # pointed sabatons
        hx = b.p["hip_x"] * sx
        V, F = M.sphere(1.0, 10, 5, scale=(0.05, 0.12, 0.045))
        add(O.P(V, F, "BH_Steel", "foot").move((hx, -0.03, 0.045)), "foot." + s)
        V, F = M.lathe([(0.0, 0.0), (0.042, 0.02), (0.03, 0.08), (0.0, 0.12)], 8)
        toe = O.P(V, F, "BH_Steel", "toe").scale((1, 1, 1)).rot(Rx(90)).scale((1.0, 1.0, 0.7))
        add(toe.move((hx, -0.1, 0.03)), "toe." + s)
    # pelvis
    V, F = torso_loft([(0.86, 0.13, 0.085, 0.09, 0.0), (0.92, 0.14, 0.092, 0.098, 0.0), (0.99, 0.135, 0.09, 0.095, 0.0)],
                      n=20)
    add(O.P(V, F, "BH_Stone", "seat"), weights=b.skirt_weights(0.98, 0.84, max_leg=0.7, center_w=0.05))
    # ---------------------------------------------------------------- cape (midnight, violet hem)
    def fn(u, v):
        z = 1.47 + (0.68 - 1.47) * v - 0.03 * math.sin(u * math.pi) * v
        hw = 0.15 + 0.1 * v
        x = (u - 0.5) * 2 * hw
        zz = max(z, 1.02)
        y = back_y(TORSO, max(min(x, 0.14), -0.14), zz) + 0.028 + (0.07 * (1.02 - z) if z < 1.02 else 0.0)
        y += 0.012 * math.sin(u * math.pi * 4) * v
        return (x, y, z)
    V, F = M.grid(fn, 9, 10)
    cape = O.P(V, F, "BH_Cloth_Primary", "cape").flip()
    cw = HS.cloth_w(chest_z=1.3, belt_z=1.03, leg=0.45)
    add(M.solidify(cape, 0.01, offset=1.0), weights=cw)
    hem = np.array([fn(u, 1.0) for u in np.linspace(0, 1, 13)]) + np.array([0, 0.004, 0.012])
    add(O.tube(hem, (0.006, 0.014), "BH_Cloth_Secondary", n=6), weights=cw)
    for sx in (1, -1):   # clasps at the shoulders
        add(O.disc((sx * 0.13, -0.02, 1.47), (sx * 0.3, -1, 0.6), 0.022, 0.01, "BH_Gold", n=10), "chest")
        add(O.tube([(sx * 0.13, -0.02, 1.47), (sx * 0.14, 0.09, 1.47)], 0.006, "BH_Cloth_Secondary", n=4), "chest")
    # ---------------------------------------------------------------- star flecks + weapon
    for plist, w in specks:
        for p in plist:
            if w is None:
                add(p, "head")
            else:
                add(p, weights=w)
    for p in socket_parts(b.std, "R", rapier()):
        add(p, "weapon.R")
