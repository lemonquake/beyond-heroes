"""Rime Weaver (bh-012, Builder D, Rimeglass Barrow): a crystalline ice spider ~1.8 m across (leg span), with its own
8-leg rig, skinned mesh and baked procedural clips.

  blender -b --factory-startup --python build_rime_weaver.py -- [--evidence DIR] [--no-export] [--clips a,b]

Rig and motion: the Broodmother's 8-leg rig and clip choreography (build_broodmother.py, imported, not edited) at
S = 0.7 scale: every bone position and every translation channel (body offsets, foot offsets) is multiplied by S in
this module's evaluate(); angles are unchanged. Legs are solved per frame with creature_kit_c.plane_leg.
Conventions: Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under the pedicel, meters, 30 fps, in place.

Look: translucent-looking pale-blue faceted carapace with white frost spikes, a cluster of glowing blue eyes, ice-fang
chelicerae, deep-blue faceted legs sheathed in ice crystals, and an abdomen cut like an ice gem (8-sided brilliant
cut) with a glowing girdle and seams (the light from within).

Clips: generic set + weaver_bite, weaver_spit (rears and spits a frost web; the game spawns the web projectile at the
hit time), weaver_pounce.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature_kit_c as K  # noqa: E402
from creature_kit_c import Xf, Rx, Ry, Rz, spine_rot, FPS  # noqa: E402
import build_broodmother as BM  # noqa: E402

import numpy as np  # noqa: E402

CID = "rime_weaver"
S = 0.7
OUT_GLB = os.path.join(K.CHAR_OUT, f"{CID}.glb")
PALETTE = {
    "BH_Stone": ((0.62, 0.84, 0.96), 0.0, 0.08, (0.18, 0.4, 0.55), 0.5, 1.0),   # pale faceted ice carapace / gem
    "BH_Horn": ((0.12, 0.27, 0.44), 0.0, 0.2, None, 0.0, 1.0),                  # deep-blue ice legs / underside
    "BH_Hair": ((0.88, 0.94, 1.0), 0.0, 0.3, None, 0.0, 1.0),                   # white frost spikes
    "BH_Shadow": ((0.01, 0.02, 0.04), 0.0, 0.3, None, 0.0, 1.0),                # mouth
    "BH_Emissive": ((0.55, 0.88, 1.0), 0.0, 0.3, (0.45, 0.8, 1.0), 7.0, 1.0),  # eyes, gem glow
}

# ------------------------------------------------------------------------------------------------ rig (scaled)
BONES = {b: (tuple(np.array(h) * S), tuple(np.array(t) * S), p) for b, (h, t, p) in BM.BONES.items()}
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
H0, T0 = BM.H, BM.T                       # brood-unit rest (mesh authoring space)
LEGS, LEG_IDS = BM.LEGS, BM.LEG_IDS
PIVOT = BM.PIVOT * S
NEUTRAL = {k: T[v[3]].copy() for k, v in LEGS.items()}
OUTW = BM.OUTW
BETA = BM.BETA
CURL = BM.CURL
FLOOR = 0.012


def evaluate(c):
    X = {}
    g = c.get
    t = S * np.array([g("body.side", 0.0), -g("body.fwd", 0.0), g("body.up", 0.0)])
    X["root"] = Xf.move(t) @ Xf.about(spine_rot(c, "body"), PIVOT)
    RIG.fk(X, "body", spine_rot(c, "ceph"))
    RIG.fk(X, "abdomen", spine_rot(c, "abd"), s=1.0 + g("abd.scale", 0.0))
    for s, sx in (("L", 1.0), ("R", -1.0)):
        RIG.fk(X, f"chel.{s}", Rx(-g("chel", 0.0) - g("chel." + s, 0.0)) @ Ry(-sx * g("chel.spread", 0.0)))
        RIG.fk(X, f"fang.{s}", Rx(-110.0 * g("fang", 0.0)) @ Rz(sx * 12.0 * g("fang", 0.0)))
        RIG.fk(X, f"palp.1.{s}", Rx(-g("palp", 0.0) - g("palp." + s, 0.0)) @ Rz(sx * g("palp.out", 0.0)))
        RIG.fk(X, f"palp.2.{s}", Rx(g("palp.fold", 0.0) + g("palp.fold." + s, 0.0)))
    fol_all = g("legs.follow", 0.0)
    for k in LEG_IDS:
        cx, fe, ti, ta = LEGS[k]
        off = S * np.array([0.0, -(g(k + ".f", 0.0) + g("legs.f", 0.0)), g(k + ".up", 0.0) + g("legs.up", 0.0)])
        off = off + OUTW[k] * S * (g(k + ".side", 0.0) + g("legs.spread", 0.0))
        tw = NEUTRAL[k] + off
        w = min(max(fol_all + g(k + ".follow", 0.0), 0.0), 1.0)
        tgt = tw * (1 - w) + X["root"].apply(tw) * w
        tgt[2] = max(tgt[2], FLOOR)
        curl = min(max(g("legs.curl", 0.0) + g(k + ".curl", 0.0), 0.0), 1.0)
        K.plane_leg(RIG, X, X["body"], [fe, ti, ta], tgt, beta=BETA[k] + g(k + ".beta", 0.0), curl=curl,
                    curl_ang=CURL, coxa=cx)
    return X


def foot(X, k):
    return RIG.tail(X, LEGS[k][3])


def clips():
    """The Broodmother's choreography (brood units; evaluate() scales), attacks renamed to the weaver_ stem."""
    out = []
    for c in BM.clips():
        if c.name == "spider_brood":
            continue
        if c.name.startswith("spider_"):
            c.name = "weaver_" + c.name[len("spider_"):]
        if "ground_speed" in c.meta:
            c.meta["ground_speed"] = round(c.meta["ground_speed"] * S, 3)
        out.append(c)
    return out


# ------------------------------------------------------------------------------------------------ mesh
def build_mesh():
    """Authored in brood units (BM rest positions), scaled by S before binding."""
    import bh_mesh as M
    import kit_a_common as A
    raw = []                      # (part, bind kwargs)
    rng = np.random.default_rng(23)

    def add(p, **kw):
        raw.append((p, kw))
        return p

    def ring(y, zc, rx, rt, rb, n=10, jit=0.0, seed=0):
        a = np.linspace(0, 2 * math.pi, n, endpoint=False) + 0.3
        r = np.random.default_rng(seed)
        return np.array([(rx * math.cos(t) * (1 + jit * (r.random() - 0.5)), y,
                          zc + (rt if math.sin(t) > 0 else rb) * math.sin(t) * (1 + jit * (r.random() - 0.5)))
                         for t in a])

    def shard(base, d, ln, r, mat="BH_Hair", sides=4):
        return A.shard(base, d, ln, r, mat, sides=sides)

    # ---- cephalothorax: faceted ice carapace + deep-blue sternum
    CEPH = [(0.05, 0.56, 0.05, 0.035, 0.035), (0.0, 0.57, 0.15, 0.09, 0.1), (-0.12, 0.575, 0.23, 0.14, 0.14),
            (-0.26, 0.58, 0.25, 0.17, 0.155), (-0.4, 0.585, 0.235, 0.165, 0.16), (-0.5, 0.59, 0.2, 0.14, 0.14),
            (-0.57, 0.59, 0.15, 0.115, 0.11), (-0.62, 0.58, 0.09, 0.07, 0.07), (-0.645, 0.575, 0.03, 0.025, 0.025)]
    V, F = M.loft([ring(*r, n=10, jit=0.12, seed=i) for i, r in enumerate(CEPH)], cap0=True, cap1=True)
    add(M.recalc_normals(M.Part(V, F, "BH_Stone", name="carapace")), bone="body")
    V, F = M.loft([ring(y, zc - 0.015, rx * 0.8, 0.02, rb * 0.9, n=10) for (y, zc, rx, rt, rb) in CEPH[1:7]],
                  cap0=True, cap1=True)
    add(M.recalc_normals(M.Part(V, F, "BH_Horn", name="sternum")), bone="body")
    # dorsal frost spikes + a crest of crystals along the midline
    for (x, y, h, d) in ((0.0, -0.2, 0.2, (0, 0.5, 1)), (0.1, -0.3, 0.13, (0.7, 0.3, 1)), (-0.1, -0.3, 0.13,
                         (-0.7, 0.3, 1)), (0.16, -0.14, 0.12, (1, 0.4, 0.7)), (-0.16, -0.14, 0.12, (-1, 0.4, 0.7)),
                         (0.0, -0.38, 0.12, (0, -0.2, 1)), (0.12, -0.46, 0.08, (0.8, -0.2, 0.8)),
                         (-0.12, -0.46, 0.08, (-0.8, -0.2, 0.8))):
        z = 0.585 + 0.16 * math.sqrt(max(0.0, 1 - (x / 0.25) ** 2)) - 0.02
        add(shard((x, y, z), d, h, h * 0.18, "BH_Hair" if abs(x) > 0 else "BH_Stone", sides=5), bone="body")
    add(A.shard((0.0, -0.1, 0.72), (0, 0.8, 1), 0.16, 0.025, "BH_Emissive", sides=4), bone="body")
    # ---- eyes: a cluster of glowing blue eyes (2 big + 6 small) on an ocular mound
    V, F = M.sphere(0.08, 10, 6, center=(0, -0.575, 0.665), scale=(1.3, 1.0, 0.65))
    add(M.Part(V, F, "BH_Stone", name="ocular"), bone="body")
    for (x, y, z, r) in ((0.034, -0.635, 0.66, 0.03), (0.09, -0.61, 0.665, 0.02), (0.045, -0.6, 0.705, 0.021),
                         (0.1, -0.57, 0.7, 0.017)):
        for sx in (1, -1):
            V, F = M.sphere(r, 8, 5, center=(sx * x, y, z))
            add(M.Part(V, F, "BH_Emissive", name="eye"), bone="body")
    V, F = M.sphere(0.05, 8, 5, center=(0, -0.6, 0.47), scale=(1.1, 0.7, 0.7))
    add(M.Part(V, F, "BH_Shadow", name="mouth"), bone="body")
    # ---- chelicerae: faceted ice blocks with long ice fangs; palps
    for s, sx in (("L", 1), ("R", -1)):
        ch = "chel." + s
        pts = [H0[ch] + (0, 0.02, 0.02), H0[ch] * 0.5 + T0[ch] * 0.5 + (sx * 0.008, -0.012, 0), T0[ch] + (0, 0.005, 0.01)]
        V, F = M.tube(pts, [(0.05, 0.056), (0.05, 0.05), (0.034, 0.032)], n=6, up=(0, -1, 0))
        add(M.Part(V, F, "BH_Stone", name="chel"), bone=ch)
        add(shard(H0[ch] + (sx * 0.04, -0.03, 0.02), (sx * 0.6, -0.6, 0.4), 0.07, 0.012), bone=ch)
        fg = "fang." + s
        a, b = H0[fg], T0[fg]
        d = b - a
        add(A.shard(a - d * 0.1, d, np.linalg.norm(d) * 1.6, 0.02, "BH_Hair", sides=5), bone=fg)
        p1, p2 = "palp.1." + s, "palp.2." + s
        V, F = M.tube([H0[p1], T0[p1], T0[p2]], [(0.028, 0.028), (0.024, 0.024), (0.018, 0.018)], n=6, up=(1, 0, 0))
        add(M.Part(V, F, "BH_Horn", name="palp"), chain=[p1, p2], blend=0.3)
        add(A.shard(T0[p2] - (T0[p2] - T0[p1]) * 0.2, T0[p2] - T0[p1], 0.08, 0.02, "BH_Stone", sides=4), bone=p2)
    # ---- abdomen: a brilliant-cut ice gem (8 facets round, crown + pavilion) glowing from within
    prof = [(0.0, 0.0), (0.2, 0.07), (0.36, 0.22), (0.44, 0.42), (0.44, 0.5), (0.4, 0.66), (0.28, 0.84),
            (0.12, 0.96), (0.0, 1.0)]
    V, F = M.lathe(prof, 8, a0=22.5, a1=382.5)
    gem = M.Part(V, F, "BH_Stone", name="gem")
    gem.rot(Rx(-90))                                   # lathe +Z -> +Y (front -> back)
    gem.scale((1.0, 1.02, 0.86))
    gem.move((0.0, 0.03, 0.72))
    gem.rot(Rx(8), center=(0.0, 0.03, 0.72))           # rear rises a little
    add(M.recalc_normals(gem), bone="abdomen")
    # glowing girdle + facet seams (light from within) slightly proud of the surface
    def gem_pt(r, t, ang, lift=0.012):
        x, y, z = (r + lift) * math.cos(ang), t * 1.02 + 0.03, (r + lift) * math.sin(ang) * 0.86 + 0.72
        return np.array(Rx(8) @ (np.array([x, y, z]) - (0, 0.03, 0.72))) + (0, 0.03, 0.72)
    for t, r in ((0.46, 0.44),):
        pts = [gem_pt(r, t, math.radians(22.5 + 45 * i)) for i in range(9)]
        V, F = M.tube(pts, [(0.016, 0.016)] * len(pts), n=4, up=(0, 1, 0), cap0=False, cap1=False)
        add(M.Part(V, F, "BH_Emissive", name="girdle"), bone="abdomen")
    for ang in (67.5, 112.5, 22.5, 157.5):
        pts = [gem_pt(rr, tt, math.radians(ang)) for rr, tt in ((0.2, 0.07), (0.36, 0.22), (0.44, 0.42),
                                                               (0.4, 0.66), (0.28, 0.84), (0.12, 0.96))]
        V, F = M.tube(pts, [(0.008, 0.008)] * len(pts), n=4, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Emissive", name="seam"), bone="abdomen")
    V, F = M.sphere(0.07, 8, 5, center=gem_pt(0.0, 0.6, math.radians(90), 0.0) + (0, 0, 0.36))
    add(M.Part(V, F, "BH_Emissive", name="table_glow").scale((1.3, 1.6, 0.35), center=V.mean(0)), bone="abdomen")
    # frost crystals on the gem crown
    for (t, ang, ln) in ((0.3, 70, 0.16), (0.36, 110, 0.14), (0.62, 80, 0.2), (0.7, 100, 0.12), (0.52, 40, 0.1),
                         (0.52, 140, 0.1), (0.85, 90, 0.12)):
        base = gem_pt(0.4 if t < 0.8 else 0.28, t, math.radians(ang), -0.02)
        nrm = K.unit(base - np.array([0, base[1], 0.72]))
        add(shard(base, nrm + np.array([0, 0.3, 0.3]), ln, ln * 0.17, "BH_Hair" if ln < 0.13 else "BH_Stone",
                  sides=5), bone="abdomen")
    V, F = M.tube([(0, 0.07, 0.6), (0, 0.02, 0.575), (0, -0.04, 0.565)], [(0.06, 0.05), (0.05, 0.045), (0.06, 0.05)],
                  n=8, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Horn", name="pedicel"), bones=["body", "abdomen"], power=4)
    # spinnerets (ice)
    for sx in (1, -1):
        add(A.shard((sx * 0.03, 1.0, 0.62), (sx * 0.2, 1.0, -0.4), 0.08, 0.02, "BH_Stone", sides=4), bone="abdomen")
    # ---- legs: faceted deep-blue segments, ice sheaths + frost spikes, glowing knee crystals
    for k, (cx, fe, ti, ta) in LEGS.items():
        n = int(k[1])
        sc = BM.LEG_SPEC[n][2]
        pts, prof = [H0[cx] - K.unit(H0[cx] - H0[cx] + (T0[cx] - H0[cx])) * 0.02], [(0.046 * sc, 0.046 * sc)]
        for b, nseg, r0, r1 in ((cx, 2, 0.05, 0.048), (fe, 4, 0.046, 0.036), (ti, 4, 0.035, 0.026),
                                (ta, 4, 0.024, 0.01)):
            for i in range(1, nseg + 1):
                t = i / nseg
                pts.append(H0[b] * (1 - t) + T0[b] * t)
                r = (r0 * (1 - t) + r1 * t) * (0.85 + 0.15 * sc)
                prof.append((r, r * 1.1))
        prof[-1] = (0.004, 0.004)
        V, F = M.tube(pts, prof, n=6, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Horn", name="leg"), chain=[cx, fe, ti, ta], blend=0.28)
        # ice sheaths on femur and tibia (hexagonal crystal sleeves)
        for b, t0, t1, r in ((fe, 0.2, 0.75, 0.056), (ti, 0.15, 0.65, 0.043)):
            q0, q1 = H0[b] * (1 - t0) + T0[b] * t0, H0[b] * (1 - t1) + T0[b] * t1
            V, F = M.tube([q0, (q0 + q1) / 2, q1], [(r * 0.7, r * 0.7), (r, r), (r * 0.6, r * 0.6)], n=6,
                          up=(0, 0, 1))
            add(M.Part(V, F, "BH_Stone", name="sheath"), bone=b)
        V, F = M.sphere(0.04, 6, 4, center=T0[fe])
        add(M.Part(V, F, "BH_Emissive", name="knee"), chain=[fe, ti], blend=0.5)
        # frost spikes along the femur / tibia tops
        for b, cnt, ln in ((fe, 3, 0.09), (ti, 2, 0.07)):
            d = RIG.rdir(b)
            side = K.unit(np.cross(d, [0, 0, 1.0]))
            up = K.unit(np.cross(side, d))
            if up[2] < 0:
                up = -up
            for i in range(cnt):
                t = (i + 0.6) / (cnt + 0.4)
                base = H0[b] * (1 - t) + T0[b] * t + up * 0.03
                add(shard(base, up * 1.0 + d * 0.6 + side * (rng.random() - 0.5) * 0.6, ln * (0.8 + 0.4 * rng.random()),
                          0.012), bone=b)
        d = RIG.rdir(ta)
        add(A.shard(T0[ta] - d * 0.06, d, 0.08, 0.012, "BH_Hair", sides=4), bone=ta)
    # scale to the weaver and bind on the scaled rig
    parts = []
    for p, kw in raw:
        p.V = p.V * S
        K.bind(p, RIG, **kw)
        parts.append(p)
    return parts


# ------------------------------------------------------------------------------------------------ main
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--clips", default="")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    import bh_mesh as M
    C = clips()
    only = set(x for x in a.clips.split(",") if x) or None
    arm, mesh, acts = K.build_all(CID, RIG, evaluate, C, build_mesh, PALETTE, only=only, ao=(16, 0.22, 0.55))
    tris = M.tri_count(mesh)
    print(f"[{CID}] mesh {tris} tris, {len(mesh.data.vertices)} verts, {len(RIG.ORDER)} bones, {len(acts)} clips")
    for c in C:
        if "ground_speed" in c.meta:
            v = K.foot_slide(c, evaluate, foot, LEG_IDS, c.meta["ground_speed"], FLOOR + 0.012)
            print(f"[{CID}] foot slip {c.name}: max {v[0] * 1000:.2f} mm/frame, mean {v[1] * 1000:.2f}, "
                  f"stance {v[2]:.2f}")
    for c in C:
        print(f"[{CID}] clip {c.name} frames {c.frames} loop {c.loop} hits {c.meta.get('hits')} "
              f"gs {c.meta.get('ground_speed')}")
    if a.evidence:
        base = a.evidence
        K.evidence_rest(CID, arm, 0.35, 3.4, "Rime Weaver - rest (4 views + 3/4 + gameplay iso 26 m / 55 deg)",
                        base=base)
        spec = [("idle", [0.0]), ("walk", [0, 0.25, 0.5]), ("run", [0.25]),
                ("weaver_bite", [0, 7 / 24, 11 / 24, 14 / 24]),
                ("weaver_spit", [12 / 36, 16 / 36, 18 / 36, 27 / 36]),
                ("weaver_pounce", [10 / 42, 14 / 42, 19 / 42, 24 / 42]),
                ("death", [0.45, 1.0]), ("death_back", [1.0]), ("alert", [0.3]), ("hit_heavy", [0.22])]
        K.evidence_clips(CID, arm, acts, spec, 0.4, 4.4, "Rime Weaver - clips (view yaw 55)", yaw=55, cols=6,
                         base=base)
    if not a.no_export and not only:
        K.merge_meta(CID, C, "tools/blender/creatures/build_rime_weaver.py",
                     {"tris": tris, "bones": len(RIG.ORDER), "leg_span_m": 1.8})
        bad, got = K.export(CID, arm, mesh, acts, OUT_GLB)
        assert not bad, bad


if __name__ == "__main__":
    main()
