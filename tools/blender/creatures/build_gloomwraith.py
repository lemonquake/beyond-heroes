"""Gloomwraith (bh-013, Builder D): phase-shifting wraith, ~2.0 m tall. Static multi-node FLOATING model animated by the
game (wisp convention, same as build_ice_wraith.py).

  "<blender>" -b --factory-startup --python build_gloomwraith.py -- [--out game/assets/characters/gloomwraith.glb]
                                                                    [--preview DIR] [--no-export]

Nodes (all meshes, no armature, origin = creature centre, Blender Z-up -> glTF Y-up, face toward -Y = Godot +Z):
  core      tall peaked hood (crown drooping forward) with a black void face and two pale violet eyes, ragged indigo
            capelet over a narrowing violet-black robe, two tattered sleeves held forward/out with long skeletal
            forearms and splayed clawed bone hands (claw tips at about +-0.7 m, 0.55 m in front)
  ring_1    ghost-lantern chain around the waist: a sagging iron chain (r 0.46 m) with 5 small glowing violet lanterns;
            node at z -0.15, tilted (10, -8) deg; lies in its local XY plane (Blender) = XZ (Godot), spun about local +Y
  ring_2    four drifting violet soul-flames (r 0.62 m) at shoulder height, tilted (-14, 18) deg
  ribbons   seven long twisting shroud-wisps trailing below the robe to ~1.2 m under the origin, glowing violet at the tips
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_d13_float as K  # noqa: E402
from kit_d13_float import M, P, np, blob, place, rag, orient  # noqa: E402

CID = "gloomwraith"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.085, 0.065, 0.17), 0.0, 0.9, None, 0.0, 1.0),        # deep indigo shroud
    "BH_Cloth_Secondary": ((0.15, 0.085, 0.26), 0.0, 0.85, None, 0.0, 1.0),      # violet-black robe / under-tatters
    "BH_Shadow": ((0.005, 0.0, 0.015), 0.0, 0.9, None, 0.0, 1.0),                # void face, hood lining
    "BH_Bone": ((0.6, 0.58, 0.66), 0.0, 0.6, None, 0.0, 1.0),                    # skeletal hands
    "BH_Horn": ((0.04, 0.03, 0.06), 0.0, 0.3, None, 0.0, 1.0),                   # black claw tips
    "BH_DarkSteel": ((0.1, 0.09, 0.13), 0.85, 0.45, None, 0.0, 1.0),             # lantern chain / caps
    "BH_Aether": ((0.55, 0.32, 0.95), 0.0, 0.4, (0.55, 0.3, 1.0), 3.5, 1.0),     # ghost-lantern glass, wisp tips
    "BH_Emissive": ((0.9, 0.8, 1.0), 0.0, 0.3, (0.85, 0.7, 1.0), 10.0, 1.0),     # eyes
}


# ------------------------------------------------------------------------------------------------ core
def core_parts():
    parts = []
    RP = [(0.0, 0.015), (0.14, 0.09), (0.34, 0.17), (0.6, 0.195), (0.82, 0.2), (1.0, 0.27)]

    def hood(u, v, inner=False):
        op = 10 + 44 * math.sin(math.pi * min(max((v - 0.22) / 0.72, 0.0), 1.0)) ** 0.7
        a = math.radians(op + (360 - 2 * op) * u)          # 0 = front (-Y)
        r = float(np.interp(v, [q[0] for q in RP], [q[1] for q in RP]))
        r *= 1.0 + 0.05 * math.sin(a * 4 + v * 9) * v
        if inner:
            r *= 0.87
        z = 0.84 - 0.52 * v
        x = r * math.sin(a)
        y = -r * math.cos(a) - 0.16 * (1 - v) ** 2.6 + 0.04 * (1 - v)
        return (x, y, z)
    V, F = M.grid(hood, 18, 13)
    parts.append(M.solidify(orient(P(V, F, "BH_Cloth_Primary", "hood"), (0, 0.0, 0.5)), 0.012, offset=1.0))
    V, F = M.grid(lambda u, v: hood(u, 0.2 + 0.8 * v, True), 18, 9)
    parts.append(orient(P(V, F, "BH_Shadow", "lining"), (0, 0.0, 0.5), inward=True))
    parts.append(blob((0, -0.05, 0.53), (0.13, 0.1, 0.17), "BH_Shadow", 12, 8, "void"))
    for sx in (1, -1):                                   # slanted almond eyes
        e = blob((0, 0, 0), (0.034, 0.012, 0.014), "BH_Emissive", 8, 5, "eye")
        e.rot(K.Ry(-sx * 18)).move((sx * 0.048, -0.158, 0.555))
        parts.append(e)
    # ragged capelet over the shoulders
    def cape(u, v):
        a = 2 * math.pi * u
        r = 0.23 + 0.2 * v ** 0.9
        z = 0.38 - (0.2 + rag(u, 2.1, 0.2, 9)) * v
        return (r * math.sin(a), -r * math.cos(a) + 0.03 * v, z)
    V, F = M.grid(cape, 28, 6, closed_u=True)
    parts.append(M.solidify(orient(P(V, F, "BH_Cloth_Primary", "cape"), (0, 0, 0.4)), 0.012, offset=1.0))
    # robe body narrowing downward, ragged hem
    RR = [(0.0, 0.24), (0.3, 0.29), (0.6, 0.22), (1.0, 0.14)]

    def robe(u, v):
        a = 2 * math.pi * u
        r = float(np.interp(v, [q[0] for q in RR], [q[1] for q in RR])) * (1 + 0.06 * math.sin(a * 7 + v * 5))
        z = 0.3 - (0.78 + rag(u, 0.7, 0.24, 7)) * v
        return (r * math.sin(a), -r * math.cos(a) + 0.05 * v * v, z)
    V, F = M.grid(robe, 26, 9, closed_u=True)
    parts.append(M.solidify(orient(P(V, F, "BH_Cloth_Secondary", "robe"), (0, 0, 0.0)), 0.012, offset=1.0))
    # arms held out: tattered sleeves, skeletal forearms, splayed clawed hands
    for sx in (1, -1):
        S = np.array([sx * 0.24, -0.02, 0.27])
        E = np.array([sx * 0.45, -0.3, 0.15])
        W = np.array([sx * 0.6, -0.52, 0.1])
        d = K.normalize(E - S)
        pts = [S, S + (E - S) * 0.5 + (0, 0, 0.02), E]
        V, F = M.tube(pts, [(0.075, 0.075), (0.085, 0.08), (0.115, 0.11)], n=10, up=(0, 0, 1), cap1=False)
        sl = P(V, F, "BH_Cloth_Primary", "sleeve")
        parts.append(M.solidify(sl, 0.01, offset=0.0))
        for k in range(2):                                 # tatters hanging from the sleeve opening
            o = E + (sx * 0.02 * (k * 2 - 1), 0.03 * (k * 2 - 1), -0.07)
            ln = 0.26 + 0.1 * k
            def tat(u, v, o=o, ln=ln, k=k):
                w = 0.09 * (1 - 0.7 * v)
                return (o[0] + (u - 0.5) * w * 0.4 + 0.03 * v * sx, o[1] + (u - 0.5) * w + 0.05 * v * v,
                        o[2] - ln * v - (rag(u, k + 2.0, 0.05, 2) if v > 0.99 else 0.0))
            parts.append(K.sheet(tat, 3, 5, "BH_Cloth_Primary", 0.008, "tatter"))
        dw = K.normalize(W - E)
        side = K.normalize(np.cross(dw, (0, 0, 1)))
        for k, off in enumerate((0.014, -0.014)):
            a0 = E - dw * 0.06 + side * off
            V, F = M.tube([a0, W + side * off * 0.6], [(0.017 - 0.004 * k, 0.017 - 0.004 * k)] * 2, n=6,
                          up=(0, 0, 1))
            parts.append(P(V, F, "BH_Bone", "forearm"))
        palm = W + dw * 0.04
        pb = blob((0, 0, 0), (0.062, 0.056, 0.024), "BH_Bone", 8, 5, "palm")
        pb.V = pb.V @ K.Rz(math.degrees(math.atan2(dw[1], dw[0])) - 90).T + palm
        parts.append(pb)
        for f, fa in enumerate((-34, -12, 10, 32, 72)):        # four fingers + thumb (inner side)
            thumb = f == 4
            fd = K.Rz(fa * sx) @ dw
            base = palm + fd * 0.04 + (0, 0, 0.005)
            L = 0.14 if thumb else 0.26 - 0.025 * abs(f - 1.5)
            p1 = base + fd * L * 0.4
            p2 = p1 + fd * L * 0.33 + (0, 0, -0.03)
            p3 = p2 + fd * L * 0.2 + (0, 0, -0.07)
            V, F = M.tube([base, p1, p2], [(0.014, 0.013), (0.012, 0.011), (0.01, 0.009)], n=5, up=(0, 0, 1))
            parts.append(P(V, F, "BH_Bone", "finger"))
            V, F = M.tube([p2, (p2 + p3) / 2 + fd * 0.01, p3], [(0.01, 0.009), (0.007, 0.006), (0.0008, 0.0008)],
                          n=5, up=(0, 0, 1))
            parts.append(P(V, F, "BH_Horn", "claw"))
    return parts


# ------------------------------------------------------------------------------------------------ rings / ribbons
def lantern(scale=1.0):
    ps = []
    V, F = M.lathe([(0, 0.0), (0.008, -0.004), (0.01, -0.02), (0.045, -0.045), (0.04, -0.056), (0, -0.056)], 6)
    ps.append(P(V, F, "BH_DarkSteel", "lcap"))
    V, F = M.lathe([(0.03, -0.052), (0.037, -0.1), (0.028, -0.148)], 6, a0=30)
    ps.append(P(V, F, "BH_Aether", "lglass"))
    V, F = M.lathe([(0, -0.144), (0.036, -0.144), (0.03, -0.16), (0, -0.185)], 6)
    ps.append(P(V, F, "BH_DarkSteel", "lbase"))
    for k in range(3):
        a = 2 * math.pi * k / 3
        c = np.array([0.038 * math.cos(a), 0.038 * math.sin(a), 0])
        V, F = M.tube([c + (0, 0, -0.05), c * 1.12 + (0, 0, -0.1), c + (0, 0, -0.15)], [(0.005, 0.005)] * 3, n=4)
        ps.append(P(V, F, "BH_DarkSteel", "lbar"))
    for p in ps:
        p.V *= scale
    return ps


def ring1_parts(radius=0.46, n=5):
    parts = []
    pts = []
    N = 60
    for i in range(N):
        t = i / N
        a = 2 * math.pi * t
        frac = (t * n) % 1.0
        pts.append((radius * math.cos(a), radius * math.sin(a), -0.05 * math.sin(math.pi * frac)))
    pts.append(pts[0])
    V, F = M.tube(pts, [(0.009, 0.006)] * len(pts), n=4, up=(0, 0, 1), twist=[i * 0.9 for i in range(len(pts))])
    parts.append(P(V, F, "BH_DarkSteel", "chain"))
    for i in range(n):
        a = 2 * math.pi * i / n
        for p in lantern(1.35):
            parts.append(p.move((radius * math.cos(a), radius * math.sin(a), 0.0)))
    return parts


def ring2_parts(radius=0.62, n=4):
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n + 0.4
        V, F = M.lathe([(0, -0.035), (0.028, -0.018), (0.024, 0.03), (0.01, 0.08), (0, 0.12)], 6)
        p = P(V, F, "BH_Aether", "soulflame")
        tangent = np.array([math.sin(a), -math.cos(a), 0.15])       # tail trails behind the orbit direction
        parts.append(place(p, tangent, (radius * math.cos(a), radius * math.sin(a), 0.03 * math.sin(3 * a))))
        parts.append(blob((radius * math.cos(a), radius * math.sin(a), 0.03 * math.sin(3 * a)), (0.018,) * 3,
                          "BH_Emissive", 6, 4, "soulcore"))
    return parts


def ribbon_parts():
    parts = []
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.2
        x0, y0 = 0.14 * math.cos(a), 0.14 * math.sin(a)
        ln = 0.82 + 0.1 * ((k * 5) % 3) / 2

        def fn(u, v, a=a, x0=x0, y0=y0, k=k, ln=ln):
            w = 0.2 * (1 - 0.85 * v)
            tw = a + 1.6 * v                                    # twist around the trailing axis
            tx, ty = -math.sin(tw), math.cos(tw)
            conv = 1 - 0.6 * v
            sway = 0.07 * math.sin(v * 5 + k * 1.3) * v
            x = x0 * conv + (u - 0.5) * w * tx + sway
            y = y0 * conv + 0.2 * v * v + (u - 0.5) * w * ty
            z = -0.3 - ln * v
            return (x, y, z)
        parts.append(K.sheet(lambda u, v, fn=fn: fn(u, 0.72 * v), 3, 9, "BH_Cloth_Primary" if k % 2 else
                             "BH_Cloth_Secondary", 0.008, "wisp"))
        parts.append(K.sheet(lambda u, v, fn=fn: fn(u, 0.72 + 0.28 * v), 3, 4, "BH_Aether", 0.006, "wisp_tip"))
    return parts


def build():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K.MT.make_materials(CID, vertex_color=False, extra=PALETTE_COLORS)
    obs = [K.node("core", core_parts(), mats, sharp=40)]
    obs.append(K.node("ring_1", ring1_parts(), mats, loc=(0, 0, -0.15), rot=(10, -8, 0), sharp=30, ao=(8, 0.05, 0.3)))
    obs.append(K.node("ring_2", ring2_parts(), mats, loc=(0, 0, 0.2), rot=(-14, 18, 0), sharp=30, ao=(6, 0.05, 0.2)))
    obs.append(K.node("ribbons", ribbon_parts(), mats, sharp=60, ao=(8, 0.1, 0.3)))
    return obs


if __name__ == "__main__":
    K.run(CID, build, dict(ground_z=-1.2, look=(0, 0, -0.15), dist=5.0, close=((0, -0.2, 0.45), 1.5, 20, 10)))
