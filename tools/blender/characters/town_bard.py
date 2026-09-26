"""Townsfolk: the bard (Ciro Balintad).

A lean young man in a fitted doublet with a short flared skirt and puffed upper sleeves (BH_Cloth_Primary, tinted),
slim hose and soft boots, a bright scarf knotted at the throat, a floppy feathered cap over shaggy hair, and a lute
slung across the back on a strap.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, interp_rows, smoothstep
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from char_mage import ring_frac

PROPS = proportions(0.98, shoulder_x=0.183 * 0.98, hip_x=0.097 * 0.98)
PALETTE = "town_bard"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.30, 0.04, 0.05)),              # preview: wine-red doublet
    "BH_Cloth_Secondary": pal((0.55, 0.48, 0.34), 0.88),      # linen under-sleeves
    "BH_Cloth_Accent": pal((0.75, 0.42, 0.03), 0.8),          # bright saffron scarf
    "BH_Cloth_Dark": pal((0.06, 0.07, 0.10), 0.9),            # hose, cap
    "BH_Skin": pal((0.50, 0.32, 0.21), 0.55),
    "BH_Hair": pal((0.05, 0.035, 0.025), 0.6),
    "BH_Bone": pal((0.80, 0.78, 0.72), 0.6),                  # feather
    "BH_Wood": pal((0.30, 0.16, 0.06), 0.45),                 # lute (varnished)
    "BH_Gold": pal((0.70, 0.50, 0.20), 0.35, 1.0),
})

B_TORSO = K.torso_rows(chest=0.95, waist=0.88, hip=0.95, depth=0.95, shoulder=0.98)


def build(body):
    k = Kit(body)
    rows = B_TORSO
    # ---- doublet with a short flared skirt, buttons, belt
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", n=24, cap1=True, name="doublet")
    r0 = interp_rows(rows, 1.0)
    sk_rows = K.flare_rows(1.02, 0.84, (r0[1] + 0.004, r0[2] + 0.004, r0[3] + 0.004), (0.2, 0.16, 0.17), n=4)
    sk, _ = K.skirt(sk_rows, "BH_Cloth_Primary", folds=8, amp=0.012, n=28, gap=0.02)
    k.add(sk, w=k.skirt_w(1.0, 0.8, max_leg=0.6))
    for z in np.linspace(1.12, 1.46, 6):
        V, F = M.sphere(0.008, 6, 4, center=(0, front_y(rows, 0, z) - 0.005, z), scale=(1, 0.5, 1))
        k.add(P_(V, F, "BH_Gold", "button"), w=k.torso_w())
    K.band(k, rows, 1.02, 1.045, "BH_Leather", g_out=0.014, g_in=0.004, n=24)
    q, ang = K.on_ring(rows, 1.0, 0.03, 0.17)
    for prt in K.pouch(q, ang, (0.06, 0.03, 0.06)):
        k.add(prt, "hips")
    # ---- sleeves: puffed upper (slashed look), fitted linen forearm
    for s in "LR":
        K.sleeve(k, s, [(-0.2, 0.03, 0.034), (-0.12, 0.058, 0.06), (0.05, 0.074, 0.076), (0.3, 0.07, 0.072),
                        (0.52, 0.05, 0.052)], "BH_Cloth_Primary", n=14)
        K.arm_ring(k, s, 0.5, 0.052, 0.04, "BH_Gold", name="band")
        K.sleeve(k, s, [(0.45, 0.046, 0.048), (1.0, 0.042, 0.044), (1.6, 0.036, 0.036), (1.9, 0.036, 0.034)],
                 "BH_Cloth_Secondary", n=10, name="undersleeve")
        K.arm_ring(k, s, 1.9, 0.042, 0.035, "BH_Cloth_Secondary", name="ruffle")
        K.mitten(k, s)
    # ---- slim hose + soft boots
    K.trousers(k, "BH_Cloth_Dark", knee_r=0.047, ankle_r=0.038, t_end=1.6, n=10)
    K.shoes(k, "BH_Leather", sole="BH_Wood", shaft=0.24, shaft_r=0.046, width=0.95)
    for s in "LR":
        b = k.b
        kn, a = b.head("shin." + s), b.tail("shin." + s)
        c = a + (kn - a) * 0.62
        V, F = M.tube([c - (0, 0, 0.02), c + (0, 0, 0.035)], [(0.052, 0.056), (0.064, 0.068)], n=12, up=(0, -1, 0),
                      cap0=False, cap1=False)
        b.add(M.solidify(P_(V, F, "BH_Leather", "boot_flare"), 0.005, offset=-1.0), "shin." + s)
    # ---- scarf
    scarf(k, rows)
    # ---- lute on the back
    lute(k, rows)
    # ---- head: shaggy hair, feathered cap
    hr = K.head(k, jaw=0.94, width=0.96, nose=1.0, brow=0.9, neck_r=0.047)
    hair(k, hr)
    cap(k, hr)
    K.check_normals(body, "bard")


def scarf(k, rows):
    # thick wrap around the neck
    ring = []
    for a in np.linspace(0, 2 * math.pi, 21):
        ring.append((0.068 * math.sin(a), -0.004 - 0.064 * math.cos(a), 1.525 + 0.012 * math.cos(a)))
    prof = [(0.026, 0.02)] * len(ring)
    V, F = M.tube(ring, prof, n=8, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Accent", "scarf"), w=k.zw([(1.5, "chest"), (1.56, "neck")]))
    # knot at the throat and two loose ends, one longer, falling on the chest
    V, F = M.sphere(0.026, 8, 6, center=(0.02, -0.085, 1.5), scale=(1.1, 0.8, 1.0))
    k.add(P_(V, F, "BH_Cloth_Accent", "knot"), "chest")
    for dx, L, w in ((0.03, 0.26, 0.04), (0.0, 0.18, 0.034)):
        pts = []
        for t in np.linspace(0, 1, 5):
            z = 1.49 - L * t
            x = dx + 0.035 * t
            pts.append((x, front_y(rows, x, z) - 0.02 - 0.008 * t, z))
        V, F = M.tube(pts, [(w / 2, 0.005)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "scarf_end"), w=k.torso_w())
        V, F = M.box(w * 1.05, 0.012, 0.012, center=pts[-1] + np.array([0, 0, -0.004]))
        k.add(P_(V, F, "BH_Gold", "fringe"), w=k.torso_w())


def lute(k, rows):
    # body: pear-shaped bowl lying on the back, neck rising over the right shoulder
    c = np.array([0.03, back_y(rows, 0, 1.2) + 0.075, 1.18])
    axis = normalize(np.array([-0.35, 0.05, 1.0]))            # toward the neck (up, to the right)
    prof = [(0.0, -0.2), (0.07, -0.19), (0.12, -0.15), (0.155, -0.08), (0.16, 0.0), (0.14, 0.07), (0.1, 0.13),
            (0.055, 0.17), (0.035, 0.19), (0.0, 0.195)]
    V, F = M.lathe(prof, 18)
    V = V * np.array([0.45, 1.0, 1.0])                        # flat bowl: local X -> world +Y (away from back)
    body_p = P_(V, F, "BH_Wood", "lute")
    R = K.M_align_z(axis, (0, 1, 0))
    body_p.rot(R).move(c)
    k.add(K.outward(body_p), "chest")
    # soundboard + rose (dark), facing outward (away from the back)
    V, F = M.sphere(0.035, 10, 4, scale=(0.2, 1, 1))
    k.add(P_(V, F, "BH_Shadow", "rose").rot(R).move(c + R @ np.array([0.072, 0.0, 0.04])), "chest")
    # neck + pegbox bent back
    n0 = c + axis * 0.18
    n1 = c + axis * 0.47
    V, F = M.tube([n0, n1], [(0.025, 0.014), (0.02, 0.012)], n=6, up=(0, 1, 0), p=3.0)
    k.add(P_(V, F, "BH_Wood", "lute_neck"), "chest")
    pb = n1 + normalize(np.array([0.0, 0.8, 0.4])) * 0.1
    V, F = M.tube([n1, pb], [(0.02, 0.012), (0.016, 0.01)], n=6, up=(0, 0, 1), p=3.0)
    k.add(P_(V, F, "BH_Wood", "pegbox"), "chest")
    # strings
    V, F = M.tube([c + R @ np.array([0.074, 0, -0.12]), n1 + R @ np.array([0.014, 0, 0])], [(0.008, 0.002)] * 2, n=4,
                  up=(0, 1, 0), p=3.0)
    k.add(P_(V, F, "BH_Bone", "strings"), "chest")
    # strap: from the pegbox over the right shoulder, across the chest to the left hip, around to the bowl bottom
    pts = [n0 + np.array([0, -0.02, 0.0]), (-0.13, 0.03, 1.535), (-0.12, -0.08, 1.49)]
    for t in np.linspace(0.1, 1, 6):
        x = lerp(-0.12, 0.15, t)
        z = lerp(1.47, 1.02, t)
        pts.append((x, front_y(rows, x * 0.95, z) - 0.018, z))
    pts.append((0.16, 0.05, 0.99))
    pts.append(c + R @ np.array([0, 0.0, -0.2]) + np.array([0, -0.02, 0]))
    V, F = M.tube(pts, [(0.016, 0.004)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Leather", "strap"), w=k.torso_w())


def hair(k, hr):
    line = K.hairline(1.74, 1.64, 1.59, sharp=0.9)
    V, F = K.head_shell(hr, lambda v: 0.016 + 0.006 * (1 - v), line, nu=24, nv=5, top_bulge=0.01)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.01, offset=-1.0), "head")
    # shaggy locks at the nape and over the ears
    for u in (0.36, 0.43, 0.5, 0.57, 0.64):
        q = ring_frac(hr, 1.62, 0.022, [u], p=2.1)[0]
        V, F = M.sphere(0.02, 6, 4, center=q + (0, -0.006, -0.005), scale=(1, 0.6, 1.4))
        k.add(P_(V, F, "BH_Hair", "lock"), w=k.zw([(1.56, "neck"), (1.62, "head")]))


def cap(k, hr):
    # floppy beret tilted to the right, with a long feather sweeping back
    tilt = Ry(-12) @ Rx(-6)
    c = np.array([0.0, 0.0, 1.785])
    prof = [(0.0, 0.085), (0.06, 0.08), (0.11, 0.06), (0.13, 0.035), (0.125, 0.015), (0.09, 0.0), (0.084, -0.01),
            (0.0, -0.012)]
    V, F = M.lathe(prof, 20)
    cp = P_(V, F, "BH_Cloth_Dark", "cap").scale((1.0, 0.95, 1.0))
    cp.rot(tilt).move(c + np.array([-0.012, 0.004, 0.0]))
    k.add(K.outward(cp), "head")
    band_ring = [c + tilt @ np.array([0.087 * math.cos(a), 0.083 * math.sin(a), -0.002]) + np.array([-0.012, 0.004, 0])
                 for a in np.linspace(0, 2 * math.pi, 21)]
    V, F = M.tube(band_ring, [(0.008, 0.008)] * len(band_ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Gold", "cap_band"), "head")
    # feather: quill from the left side of the cap sweeping up and back
    base = c + tilt @ np.array([0.09, -0.02, 0.01])
    pts = [base, base + (0.035, 0.03, 0.12), base + (0.045, 0.12, 0.21), base + (0.04, 0.24, 0.24), base + (0.03, 0.34, 0.2)]
    prof = [(0.006, 0.006), (0.03, 0.018), (0.036, 0.022), (0.03, 0.018), (0.006, 0.005)]
    V, F = M.tube(pts, prof, n=6, up=(1, 0, 0), p=3.0)
    k.add(P_(V, F, "BH_Bone", "feather"), "head")
    V, F = M.tube(pts[:4], [(0.003, 0.004)] * 4, n=4, up=(1, 0, 0))
    k.add(P_(V, F, "BH_Cloth_Accent", "quill"), "head")
