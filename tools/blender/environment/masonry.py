"""Masonry generators: stone-course walls from individually varied blocks, arch rings, quoins, capstones, slabs."""
import math

from mathutils import Vector

from kit import (box, hexa, prism, chip, jitter, T, R, TRS, lerp, tb)


def split_lengths(r, total, lo, hi, avoid=(), tries=12, min_gap=0.14):
    """Random lengths in ~[lo, hi] summing to total; tries to keep joints away from `avoid` positions (relative)."""
    best = None
    for _ in range(tries):
        n = max(1, int(round(total / ((lo + hi) / 2))))
        w = [r.uniform(lo, hi) for _ in range(n)]
        s = sum(w)
        w = [x * total / s for x in w]
        joints = []
        acc = 0.0
        for x in w[:-1]:
            acc += x
            joints.append(acc)
        bad = sum(1 for j in joints for a in avoid if abs(j - a) < min_gap)
        if best is None or bad < best[0]:
            best = (bad, w, joints)
        if bad == 0:
            break
    return best[1], best[2]


def course_heights(r, total, lo, hi):
    w, _ = split_lengths(r, total, lo, hi)
    return w


class RectCut:
    def __init__(self, x0, x1, z0, z1):
        self.x0, self.x1, self.z0, self.z1 = x0, x1, z0, z1

    def occ(self, zb, zt):
        if zt <= self.z0 + 1e-4 or zb >= self.z1 - 1e-4:
            return None
        return (self.x0, self.x0, self.x1, self.x1)


class CircleCut:
    """Occupies the disc of radius R above z=cz (below cz it spans the full width 2R)."""

    def __init__(self, cx, cz, R_):
        self.cx, self.cz, self.R = cx, cz, R_

    def hw(self, z):
        if z <= self.cz:
            return self.R
        d = z - self.cz
        return math.sqrt(max(0.0, self.R * self.R - d * d))

    def occ(self, zb, zt):
        if zb >= self.cz + self.R - 1e-4 or zt <= self.cz + 1e-3:
            return None
        hb, ht = self.hw(zb), self.hw(zt)
        # Block ends are straight lines between bottom and top; for the upper part of the circle the chord can
        # cut into the arch, so push the ends out to the max width inside the band.
        hmid = self.hw((zb + zt) / 2)
        hb2 = max(hb, hmid + (hmid - (hb + ht) / 2))
        ht2 = max(ht, 0.0)
        return (self.cx - hb2, self.cx - ht2, self.cx + hb2, self.cx + ht2)


def free_segments(x0, x1, zb, zt, cuts, gap):
    occ = [c.occ(zb, zt) for c in cuts]
    occ = sorted([o for o in occ if o], key=lambda o: min(o[0], o[1]))
    merged = []
    for o in occ:
        if merged and min(o[0], o[1]) <= max(merged[-1][2], merged[-1][3]):
            m = merged[-1]
            merged[-1] = (min(m[0], o[0]), min(m[1], o[1]), max(m[2], o[2]), max(m[3], o[3]))
        else:
            merged.append(o)
    segs = []
    cur = (x0, x0)
    for (lb, lt, rb, rt) in merged:
        segs.append((cur[0], cur[1], lb - gap, lt - gap))
        cur = (rb + gap, rt + gap)
    segs.append((cur[0], cur[1], x1, x1))
    return [s for s in segs if min(s[2] - s[0], s[3] - s[1]) > 0.12 or max(s[2] - s[0], s[3] - s[1]) > 0.3]


def block_between(k, xlb, xlt, xrb, xrt, zb, zt, y0, y1, mat, tint, bev=0.035, chips=1, chipd=0.06, jit=0.006,
                  M=None, group=None, proud=0.0):
    r = k.r
    # small per-face protrusion variation
    fy = r.uniform(-0.012, 0.012) - proud
    by = r.uniform(-0.012, 0.012) + proud
    c = [(xlb, y0 + fy, zb), (xrb, y0 + fy, zb), (xrb, y1 + by, zb), (xlb, y1 + by, zb),
         (xlt, y0 + fy, zt), (xrt, y0 + fy, zt), (xrt, y1 + by, zt), (xlt, y1 + by, zt)]
    t = hexa(c, bev)
    n = chips if isinstance(chips, int) else r.randint(*chips)
    if n:
        chip(t, r, n, chipd)
    if jit:
        jitter(t, r, jit)
    k.put(t, mat, M=M, tint=tint, group=group)


def masonry(k, x0, x1, z0, z1, thick, mat="BH_StoneDark", tint=(0.72, 0.92), course=(0.36, 0.52), blen=(0.45, 1.0),
            gap=0.022, bev=0.035, cuts=(), quoin=None, quoin_mat="BH_Stone", quoin_len=(0.85, 0.5),
            M=None, top_profile=None, core=True, core_mat="BH_StoneDark", courses=None, chip_rng=(0, 2),
            end_quoin_tint=(0.95, 1.0), skip=None, jamb_quoin_z=None, zbreaks=(), core_cuts=None):
    """Lay courses of blocks from x0..x1 (local X), z0..z1, thickness along Y centred at 0.
    quoin: None | 'start' | 'end' | 'both' -> lighter alternating long/short blocks at those ends.
    top_profile(x)->z : blocks above are omitted (broken walls). skip(i_course, x_mid)->bool drops blocks.
    Returns list of course z-levels."""
    r = k.r
    if courses:
        hs = courses
    else:
        brk = [z0] + sorted(b for b in zbreaks if z0 + 0.2 < b < z1 - 0.2) + [z1]
        hs = []
        for a, b in zip(brk[:-1], brk[1:]):
            if b - a < course[0] * 0.8:
                hs.append(b - a)
            else:
                hs += course_heights(r, b - a, *course)
    zs = [z0]
    for h in hs:
        zs.append(zs[-1] + h)
    prev_joints = []
    y0, y1 = -thick / 2, thick / 2
    for ci in range(len(hs)):
        zb, zt = zs[ci] + gap / 2, zs[ci + 1] - gap / 2
        segs = free_segments(x0, x1, zs[ci], zs[ci + 1], cuts, gap)
        joints_this = []
        for (slb, slt, srb, srt) in segs:
            L = (srb + srt) / 2 - (slb + slt) / 2
            if L <= 0.05:
                continue
            ends = []
            q_start = quoin in ("start", "both") and abs(slb - x0) < 1e-6
            q_end = quoin in ("end", "both") and abs(srb - x1) < 1e-6
            if jamb_quoin_z is not None and zs[ci + 1] <= jamb_quoin_z + 0.05:
                q_start = q_start or abs(slb - x0) > 1e-6
                q_end = q_end or abs(srb - x1) > 1e-6
            lead = quoin_len[ci % 2] if q_start else 0.0
            tail = quoin_len[(ci + 1) % 2] if q_end else 0.0
            inner = L - lead - tail
            if inner < 0.2:
                lead = tail = 0.0
                inner = L
            avoid = [j - (slb + lead) for j in prev_joints]
            ws, _ = split_lengths(r, inner, blen[0], blen[1], avoid=avoid)
            pieces = ([("q", lead)] if lead else []) + [("b", w) for w in ws] + ([("q", tail)] if tail else [])
            acc = 0.0
            slm = (slb + slt) / 2
            last = len(pieces) - 1
            for pi, (kind, w) in enumerate(pieces):
                a0, a1 = acc, acc + w
                acc = a1
                if pi == 0:
                    xlb, xlt = slb, slt
                else:
                    xlb = xlt = slm + a0 + gap / 2
                if pi == last:
                    xrb, xrt = srb, srt
                else:
                    xrb = xrt = slm + a1 - gap / 2
                xm = (xlb + xrb) / 2
                joints_this.append(xrb + gap / 2)
                if top_profile is not None and zb + 0.12 > top_profile(xm):
                    continue
                if skip is not None and skip(ci, xm):
                    continue
                if kind == "q":
                    tt = r.uniform(*end_quoin_tint)
                    block_between(k, xlb, xlt, xrb, xrt, zb, zt, y0 - 0.015, y1 + 0.015, quoin_mat, tt, bev * 1.2,
                                  r.randint(0, 1), 0.05, M=M)
                else:
                    tt = r.uniform(*tint)
                    block_between(k, xlb, xlt, xrb, xrt, zb, zt, y0, y1, mat, tt, bev, r.randint(*chip_rng), 0.06,
                                  M=M)
        if core:
            ci_ = 0.07
            for (slb, slt, srb, srt) in free_segments(x0, x1, zs[ci], zs[ci + 1], core_cuts if core_cuts is not None else cuts, 0.0):
                zc1 = zs[ci + 1]
                if top_profile is not None:
                    zc1 = min(zc1, max(zs[ci], min(top_profile(x) for x in (slb, (slb + srb) / 2, srb)) - 0.05))
                if zc1 - zs[ci] > 0.05:
                    c = [(slb + 0.01, y0 + ci_, zs[ci]), (srb - 0.01, y0 + ci_, zs[ci]), (srb - 0.01, y1 - ci_, zs[ci]),
                         (slb + 0.01, y1 - ci_, zs[ci]),
                         (slt + 0.01, y0 + ci_, zc1), (srt - 0.01, y0 + ci_, zc1), (srt - 0.01, y1 - ci_, zc1),
                         (slt + 0.01, y1 - ci_, zc1)]
                    k.put(hexa(c), core_mat, M=M, tint=0.38)
        prev_joints = joints_this
    return zs


def arch_ring(k, cx, cz, r_in, r_out, thick, n=11, mat="BH_Stone", alt_mat=None, tint=(0.92, 1.0), gap=0.02,
              key_extra=0.1, M=None, proud=0.03, a0=0.0, a1=math.pi, bev=0.035):
    """Voussoir ring in the XZ plane (arch spanning along X), thickness along Y. alt_mat alternates colours."""
    r = k.r
    for i in range(n):
        t0 = lerp(a0, a1, i / n) + (gap / r_in / 2 if i else 0)
        t1 = lerp(a0, a1, (i + 1) / n) - (gap / r_in / 2 if i < n - 1 else 0)
        ro = r_out + (key_extra if i == n // 2 else r.uniform(-0.03, 0.05))
        # outer edge of a voussoir ends on a horizontal/vertical-ish step for a stepped extrados look
        pts = [(cx + math.cos(t0) * r_in, cz + math.sin(t0) * r_in), (cx + math.cos(t1) * r_in, cz + math.sin(t1) * r_in),
               (cx + math.cos(t1) * ro, cz + math.sin(t1) * ro), (cx + math.cos(t0) * ro, cz + math.sin(t0) * ro)]
        y0, y1 = -thick / 2 - proud, thick / 2 + proud
        c = [(pts[0][0], y0, pts[0][1]), (pts[1][0], y0, pts[1][1]), (pts[1][0], y1, pts[1][1]), (pts[0][0], y1, pts[0][1]),
             (pts[3][0], y0, pts[3][1]), (pts[2][0], y0, pts[2][1]), (pts[2][0], y1, pts[2][1]), (pts[3][0], y1, pts[3][1])]
        t = hexa(c, bev)
        chip(t, r, r.randint(0, 1), 0.05)
        jitter(t, r, 0.005)
        m = alt_mat if (alt_mat and i % 2) else mat
        k.put(t, m, M=M, tint=r.uniform(*tint))


def capstones(k, x0, x1, z, thick, h=0.2, over=0.06, mat="BH_Stone", lens=(0.55, 0.95), tint=(0.95, 1.0), M=None,
              gap=0.02):
    r = k.r
    ws, _ = split_lengths(r, x1 - x0, *lens)
    acc = x0
    for w in ws:
        t = box(w - gap, thick + over * 2, h, bev=0.03)
        chip(t, r, r.randint(0, 2), 0.05)
        jitter(t, r, 0.005)
        k.put(t, mat, M=(M or T()) @ TRS(acc + w / 2, r.uniform(-0.01, 0.01), z + h / 2, 0, r.uniform(-0.6, 0.6),
                                          r.uniform(-0.8, 0.8)), tint=r.uniform(*tint))
        acc += w


def slab_floor(k, sx, sy, z, th=0.09, rows=(0.5, 0.9), lens=(0.55, 1.1), mat="BH_Stone", gap=0.025, tint=(0.82, 1.0),
               sink=0.02, crack_p=0.12, missing=0.0, M=None, along_x=True):
    """Flagstone field of individually bevelled slabs covering [-sx/2,sx/2]x[-sy/2,sy/2] with top at z."""
    r = k.r
    rws, _ = split_lengths(r, sy, *rows)
    yy = -sy / 2
    prev = []
    for rw in rws:
        ws, joints = split_lengths(r, sx, *lens, avoid=[p + sx / 2 for p in prev])
        xx = -sx / 2
        for w in ws:
            cx, cy = xx + w / 2, yy + rw / 2
            xx += w
            if r.random() < missing:
                continue
            dz = -r.uniform(0, sink)
            if r.random() < crack_p and w > 0.5:
                # cracked slab: two pieces separated by a slanted crack line
                s_ = r.uniform(0.35, 0.65) * w - w / 2
                off = r.uniform(-0.12, 0.12)
                ya, yb = -rw / 2 + gap / 2, rw / 2 - gap / 2
                xa, xb = -w / 2 + gap / 2, w / 2 - gap / 2
                for (l0, l1, r0, r1) in ((xa, xa, s_ - off - 0.012, s_ + off - 0.012), (s_ - off + 0.012, s_ + off + 0.012, xb, xb)):
                    c = [(l0, ya, -th), (r0, ya, -th), (r1, yb, -th), (l1, yb, -th),
                         (l0, ya, 0), (r0, ya, 0), (r1, yb, 0), (l1, yb, 0)]
                    t = hexa(c, 0.02)
                    jitter(t, r, 0.004)
                    k.put(t, mat, M=(M or T()) @ TRS(cx, cy, z + dz - r.uniform(0, 0.015), r.uniform(-1, 1),
                                                      r.uniform(-1, 1), 0), tint=r.uniform(*tint))
                continue
            t = box(w - gap, rw - gap, th, bev=0.025)
            chip(t, r, r.randint(0, 2), 0.04)
            jitter(t, r, 0.004)
            k.put(t, mat, M=(M or T()) @ TRS(cx, cy, z - th / 2 + dz, r.uniform(-0.7, 0.7), r.uniform(-0.7, 0.7),
                                              r.uniform(-0.6, 0.6)), tint=r.uniform(*tint))
        prev = [j - sx / 2 for j in joints]
        yy += rw
