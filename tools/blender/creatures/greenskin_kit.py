"""Shared modeling helpers for Builder C's humanoid enemies (goblin_skulker, orc_reaver, ogre_crusher).

Organic bodies on the shared humanoid skeleton: skin torso loft, continuous arm / leg tubes (smooth weights),
bare feet, heads from cross-section rows, weapons authored in socket space. Everything is in MODEL space (the
bh_body modelling pose: arms hanging, legs straight) and is added through bh_body.Body.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, interp_rows, smoothstep, M_align_z, fist
from bh_math import normalize, Rx, Ry, Rz, R_axis


# ------------------------------------------------------------------------------------------------ landmarks
def levels(p):
    """Heights of the spine joints for a proportions dict."""
    zh = p["pelvis_h"]
    zs = zh + p["hips_len"]
    zc = zs + p["spine_len"]
    zn = zc + p["chest_len"]
    zhd = zn + p["neck_len"]
    return dict(hips=zh, spine=zs, chest=zc, neck=zn, head=zhd, top=zhd + p["head_len"],
                shoulder=zn - p["clav_drop"])


def zspec_w(spec):
    """Blend bones along height: spec = [(z, bone), ...] ascending; smoothstep between consecutive entries."""
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z <= spec[0][0]:
                out.append({spec[0][1]: 1.0})
                continue
            if z >= spec[-1][0]:
                out.append({spec[-1][1]: 1.0})
                continue
            d = None
            for (z0, b0), (z1, b1) in zip(spec, spec[1:]):
                if z0 <= z <= z1:
                    if b0 == b1:
                        d = {b0: 1.0}
                    else:
                        t = float(smoothstep(z0, z1, z))
                        d = {b0: 1 - t, b1: t}
                    break
            out.append({k: x for k, x in d.items() if x > 1e-4})
        return out
    return wfn


def torso_w(p, shoulder_blend=True):
    """Torso skin: hips -> spine -> chest by height, plus the upper-outer chest blended into shoulder.L/R."""
    L = levels(p)
    base = zspec_w([(L["hips"] + 0.01 * p["pelvis_h"], "hips"), (L["spine"] + 0.25 * p["spine_len"], "spine"),
                    (L["chest"] - 0.1 * p["spine_len"], "spine"), (L["chest"] + 0.35 * p["chest_len"], "chest"),
                    (L["neck"] + 0.2 * p["neck_len"], "chest"), (L["neck"] + 0.9 * p["neck_len"], "neck")])
    sx = p["shoulder_x"]

    def wfn(V):
        W = base(V)
        if not shoulder_blend:
            return W
        out = []
        for v, w in zip(V, W):
            a = float(smoothstep(0.45 * sx, 1.0 * sx, abs(v[0]))) * float(
                smoothstep(L["chest"] + 0.3 * p["chest_len"], L["shoulder"], v[2]))
            if a > 1e-3:
                sb = "shoulder.L" if v[0] > 0 else "shoulder.R"
                w = {k: x * (1 - 0.8 * a) for k, x in w.items()}
                w[sb] = w.get(sb, 0.0) + 0.8 * a
            out.append(w)
        return out
    return wfn


def seat_w(body, z_top, z_bot, max_leg=0.75, center_w=None):
    cw = center_w if center_w is not None else 0.5 * body.p["hip_x"]
    return body.skirt_weights(z_top, z_bot, max_leg=max_leg, center_w=cw)


# ------------------------------------------------------------------------------------------------ primitives
def part(VF, mat, name="part"):
    return M.Part(VF[0], VF[1], mat, name=name)


def rtube(pts, radii, mat, n=8, up=None, cap=True, p=2.0):
    """Tube along a polyline with per-point radius (float or (rx, ry))."""
    pts = np.asarray(pts, float)
    if np.ndim(radii) == 0 or isinstance(radii, tuple):   # scalar or (rx, ry) tuple = constant; list = per point
        radii = [radii] * len(pts)
    prof = [(r, r) if np.ndim(r) == 0 else tuple(r) for r in radii]
    if up is None:
        d = normalize(pts[-1] - pts[0])
        up = (0, 0, 1) if abs(d[2]) < 0.85 else (0, -1, 0)
    V, F = M.tube(pts, prof, n=n, up=up, cap0=cap, cap1=cap, p=p)
    return M.Part(V, F, mat)


def blob(center, r, mat, scale=(1, 1, 1), n=10, rings=6, rot=None):
    V, F = M.sphere(r, n, rings, scale=scale)
    prt = M.Part(V, F, mat, name="blob")
    if rot is not None:
        prt.rot(rot)
    return prt.move(center)


def cone(base, tip, r0, mat, n=6, r1=0.0005):
    return rtube([base, tip], [r0, r1], mat, n=n)


def jitter(part, amp, seed=1, axis_scale=(1, 1, 1)):
    rng = np.random.default_rng(seed)
    part.V = part.V + rng.normal(size=part.V.shape) * amp * np.asarray(axis_scale, float)
    return part


def dent(part, center, radius, depth):
    """Push vertices near `center` toward the part's centroid (dents in helmets / pots)."""
    c = np.asarray(center, float)
    cen = part.V.mean(0)
    d = np.linalg.norm(part.V - c, axis=1)
    f = np.clip(1 - d / radius, 0, 1) ** 2
    dirn = cen - part.V
    dirn /= np.maximum(np.linalg.norm(dirn, axis=1, keepdims=True), 1e-9)
    part.V = part.V + dirn * (f * depth)[:, None]
    return part


# ------------------------------------------------------------------------------------------------ body pieces
def arm(body, s, prof, mat, n=12, deltoid=None, deltoid_mat=None):
    """Continuous skin arm from the shoulder to the wrist. prof: radii (rx, ry) at 6 stations
    (shoulder, mid upper, above elbow, elbow, mid forearm, wrist)."""
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    pts = [sh + (sh - el) * 0.08, sh + (el - sh) * 0.4, sh + (el - sh) * 0.82, el,
           el + (wr - el) * 0.45, wr + (wr - el) * 0.04]
    V, F = M.tube(pts, prof, n=n, up=(0, -1, 0))
    body.add(M.Part(V, F, mat, name="arm"), weights=body.seg_weights([ua, fa], power=10))
    if deltoid:
        c = sh + (el - sh) * 0.12 + np.array([0.0, 0.0, deltoid * 0.1])
        V, F = M.sphere(deltoid, 12, 7, center=c, scale=(1.0, 1.05, 0.95))
        body.add(M.Part(V, F, deltoid_mat or mat, name="deltoid"),
                 weights=lambda V, s=s: [{"shoulder." + s: 0.35, "upper_arm." + s: 0.65}] * len(V))


def hand(body, s, mat, scale=1.0, claws=None):
    for prt in fist(body, s, mat, mat, gauntlet=False, scale=scale):
        body.add(prt, "hand." + s)
    if claws:
        A = body.axes("weapon." + s)
        o = body.head("weapon." + s)
        xs = 1.0 if s == "R" else -1.0
        for k in range(4):
            y = (-0.03 + 0.02 * k) * scale
            b = o + A @ (np.array([0.045 * xs, y, -0.005]) * scale)
            t = o + A @ (np.array([0.05 * xs, y, -0.035]) * scale)
            body.add(cone(b, t, 0.006 * scale, claws, n=5), "hand." + s)


def leg(body, s, prof, mat, bow=0.0, n=12, top_up=0.04):
    """Skin leg hip -> ankle. prof: 6 radii stations (hip, mid thigh, above knee, knee, calf, ankle).
    bow: lateral outward offset at the knee (bow-legged)."""
    th, sh = "thigh." + s, "shin." + s
    h, k, a = body.head(th), body.head(sh), body.tail(sh)
    sx = 1.0 if s == "L" else -1.0
    us = [0.0, 0.45, 0.85, 1.0, 1.45, 1.97]
    pts = []
    for u in us:
        if u <= 1:
            q = h + (k - h) * u
        else:
            q = k + (a - k) * (u - 1)
        b = bow * math.sin(math.pi * min(u, 2.0) / 2.0)
        pts.append(q + np.array([sx * b, 0.0, 0.0]))
    pts[0] = pts[0] + np.array([0, 0, top_up])
    V, F = M.tube(pts, prof, n=n, up=(0, -1, 0))
    body.add(M.Part(V, F, mat, name="leg"), weights=body.seg_weights([th, sh], power=10))
    return pts


def bare_foot(body, s, mat, length, width, height, claw_mat=None, toes=3, toe_r=None):
    """Bare foot: sole slab bound to foot.<s>, toe digits bound to toe.<s>."""
    p = body.p
    hx = p["hip_x"] * (1 if s == "L" else -1)
    ball = -p["ball_fwd"]
    heel = p["heel_back"]

    def rings(spec):
        R = []
        for y, w, top in spec:
            pts = []
            for i in range(12):
                ang = 2 * math.pi * i / 12
                c, sn = math.cos(ang), math.sin(ang)
                x = w * np.sign(c) * abs(c) ** 0.8
                z = top / 2 + top / 2 * np.sign(sn) * abs(sn) ** 0.7
                pts.append((hx + x, y, max(z, 0.004)))
            R.append(np.array(pts))
        return R
    a_h = p["ankle_h"]
    spec = [(heel * 1.1, width * 0.55, height * 0.8), (heel * 0.2, width * 0.8, height * 1.2 + a_h * 0.5),
            (ball * 0.45, width, height * 1.0), (ball * 0.95, width * 1.08, height * 0.75)]
    V, F = M.loft(rings(spec)[::-1])
    body.add(M.Part(V, F, mat, name="foot"), "foot." + s)
    tr = toe_r or width * 0.3
    tl = length - (heel + p["ball_fwd"])
    for i in range(toes):
        f = (i - (toes - 1) / 2) / max(toes - 1, 1)
        x = hx + f * width * 1.35
        y0 = ball * 0.9
        pts = [(x, y0, height * 0.45), (x + f * 0.1 * tl, y0 - tl * 0.6, height * 0.35),
               (x + f * 0.15 * tl, y0 - tl, height * 0.2)]
        body.add(rtube(pts, [tr, tr * 0.9, tr * 0.7], mat, n=7), "toe." + s)
        if claw_mat:
            tip = np.array(pts[-1])
            body.add(cone(tip + (0, tl * 0.05, 0.004), tip + (0, -tl * 0.28, -0.006), tr * 0.55, claw_mat, n=5),
                     "toe." + s)


def head_rows(rows, z0, sx=1.0, sy=1.0, sz=1.0, dy=0.0):
    """rows relative (dz, rx, ryf, ryb, keel, cy) -> absolute torso_loft rows."""
    return [(z0 + r[0] * sz, r[1] * sx, r[2] * sy, r[3] * sy, r[4], r[5] * sy + dy) for r in rows]


def front_of(rows, x, z, p=2.1):
    """Front surface y of a head/torso loft (rows with cy) at (x, z)."""
    r = interp_rows(rows, z)
    _, rx, ryf, ryb, keel = r[:5]
    cy = r[5] if len(r) > 5 else 0.0
    ax = min(abs(x) / rx, 0.999)
    yy = ryf * (1 - ax ** p) ** (1 / p)
    c = ax ** (p / 2)
    yy *= 1 + keel * max(0.0, 1 - c * 1.6) ** 2
    return cy - yy


def side_of(rows, z, p=2.1):
    r = interp_rows(rows, z)
    return r[1], (r[5] if len(r) > 5 else 0.0)


def ear(root, length, width, mat, out=(1, 0, 0), up=(0, 0, 1), droop=0.0, thick=0.012, n=9, back=0.0):
    """Pointed leaf ear from `root` toward `out` (world dir), flat in the plane spanned by out and up."""
    o = normalize(np.asarray(out, float))
    u = normalize(np.asarray(up, float) - o * np.dot(up, o))
    nrm = np.cross(o, u)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        # leaf outline: top edge and bottom edge
        pts.append((t, width * (0.5 * math.sin(math.pi * min(t * 1.25, 1.0)) * (1 - t) ** 0.4)))
    top = [(t * length, w) for t, w in pts]
    bot = [(t * length, -0.6 * w) for t, w in pts[::-1]]
    outline = np.array(top + bot[1:-1])
    area = 0.5 * np.sum(outline[:, 0] * np.roll(outline[:, 1], -1) - np.roll(outline[:, 0], -1) * outline[:, 1])
    if area < 0:
        outline = outline[::-1]
    V, F = M.prism(outline, thick, axis="z")
    # bend: droop the tip down, sweep back
    Vn = []
    for x, y, z in V:
        t = x / length
        Vn.append(np.asarray(root, float) + o * x + u * (y - droop * t * t * length) + nrm * (z + back * t * t * length))
    return M.Part(np.array(Vn), F, mat, name="ear")


def weapon_to_socket(body, side, parts, bone=None):
    """Weapon parts built like bh_weapons (grip at origin, long axis +Z, flats +-Y) -> model space in the
    weapon.<side> socket (socket local = (x, z, -y), identical to the Godot identity attachment). Rigid to
    weapon.<side> (see finish_mesh: the socket bones are switched to deform)."""
    A = body.axes("weapon." + side)
    o = body.head("weapon." + side)
    for p in parts:
        V = p.V
        loc = np.stack([V[:, 0], V[:, 2], -V[:, 1]], 1)
        p.V = o + loc @ A.T
        body.add(p, bone or ("weapon." + side))


def make_socket_deform(mesh_ob, sides=("R", "L")):
    """finish_mesh hook: the shared skeleton marks weapon.L/R non-deforming; in-mesh weapons are weighted to them, so
    switch them to deform (glTF exports all bones either way; this keeps Blender previews and the skin consistent)."""
    arm = mesh_ob.parent
    for s in sides:
        b = arm.data.bones.get("weapon." + s)
        if b is not None:
            b.use_deform = True
