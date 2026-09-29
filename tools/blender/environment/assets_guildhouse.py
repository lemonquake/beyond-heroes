"""The Guild House (run bh-016): the big shared common hall of Malasugue between Swordfin Hall and Lantern House.

14.7 x 8.7 m: wide stone ground floor, timber-framed upper storey, slate gable roof (ridge along X), tall arched double
door at x=0 on the -Y face, two arched windows either side, a big hanging signboard carrying both crests (silver
swordfish on blue on the left, gold lantern on violet on the right), a blue banner pole on the left and a violet one on
the right, a brick chimney with a glowing top. Origin at the bottom centre of the footprint (recenter=False).
Sockets: door, door_light, banner_l, banner_r, sign_light.
"""
import math

from kit import *  # noqa
from masonry import *  # noqa
from registry import asset
from assets_props import plank, flame_tip
from assets_town import timber_frame
from assets_town2 import (swordfish, lantern_emblem, hang_lantern, wide_window, slate_roof, chimney, banner_pole,
                          pillar_round)


def _arched_window(k, M, spring, ri=0.45, ro=0.72, bottom=1.2):
    """Ground-floor arched stone window in a wall plane at M (faces -Y): arch ring, glass, iron bars, sill."""
    arch_ring(k, 0, spring, ri, ro, 0.7, n=7, mat="BH_Stone", M=M)
    k.put(box(ri * 2, 0.36, spring - bottom), "BH_Glass", M=M @ T(0, 0, (spring + bottom) / 2), uvoff=False)
    k.put(cyl(ri, 0.36, 12), "BH_Glass", M=M @ TRS(0, 0.18, spring, 90, 0, 0), uvoff=False)
    for dx in (-0.15, 0.15):
        k.put(box(0.04, 0.4, spring - bottom + 0.4), "BH_Iron", M=M @ T(dx, 0, (spring + bottom) / 2 + 0.2))
    k.put(box(1.1, 0.5, 0.12, bev=0.02), "BH_Stone", M=M @ T(0, -0.02, bottom - 0.05), tint=0.95)


@asset("guild_house", "town2")
def guild_house(k):
    from assets_arch import door_cuts
    r = k.r
    L, W = 14.0, 8.0            # wall centre lines; outer stone faces at +-7.35 / +-4.35
    h0, h1 = 3.7, 2.3           # stone ground floor, timber upper storey
    ph = 3.0                    # roof rise
    yF = -W / 2 - 0.35          # front stone face
    w, spring, r_in, r_out = 2.2, 1.9, 1.1, 1.5
    zr = h0 + 0.25 + h1         # eave line on the timber storey
    win_x = (4.4, 6.1)
    wspring = 2.5

    # ---- stone ground floor ------------------------------------------------------------------------------------
    cf = door_cuts(w, spring, r_out)
    for sx in (-1, 1):
        for x in win_x:
            cf += [RectCut(sx * x - 0.45, sx * x + 0.45, 1.2, wspring), CircleCut(sx * x, wspring, 0.5)]
    back_x = (-5.3, -2.1, 2.1, 5.3)
    cb = [RectCut(x - 0.4, x + 0.4, 1.9, 3.3) for x in back_x]
    for (sy, cuts) in ((-1, cf), (1, cb)):
        M = T(0, sy * W / 2, 0)
        masonry(k, -L / 2 - 0.35, L / 2 + 0.35, 0, h0, 0.7, M=M, cuts=cuts, quoin="both", course=(0.46, 0.64),
                blen=(0.9, 1.6), chip_rng=(0, 0), jamb_quoin_z=spring if sy < 0 else None,
                zbreaks=(spring,) if sy < 0 else (), core_cuts=door_cuts(w, spring, r_in + 0.08) if sy < 0 else None)
    side_y = (-1.6, 1.6)
    cs = []
    for y in side_y:
        cs += [RectCut(y - 0.45, y + 0.45, 1.2, wspring), CircleCut(y, wspring, 0.5)]
    for sx in (-1, 1):
        M = T(sx * L / 2, 0, 0) @ R(0, 0, 90)
        masonry(k, -W / 2 + 0.35, W / 2 - 0.35, 0, h0, 0.7, M=M, cuts=cs, quoin=None, course=(0.46, 0.64),
                blen=(0.9, 1.6), chip_rng=(0, 0))
    # arched windows: front (four), sides (two each); back windows are plain wide windows
    for sx in (-1, 1):
        for x in win_x:
            _arched_window(k, T(sx * x, -W / 2, 0), wspring)
        for y in side_y:
            _arched_window(k, T(sx * L / 2, y, 0) @ R(0, 0, 90), wspring)
    for x in back_x:
        wide_window(k, T(x, W / 2 + 0.1, 2.6) @ R(0, 0, 180), 0.8, 1.4, shutters=False)

    # ---- arched double door -------------------------------------------------------------------------------------
    arch_ring(k, 0, spring, r_in, r_out, 0.7, n=13, mat="BH_Stone")
    for sx in (-1, 1):
        n = 3
        pw = (w / 2 - 0.02) / n
        for i in range(n):
            plank(k, pw - 0.01, 0.08, spring, M=T(sx * (0.01 + pw * (i + 0.5)), -W / 2 + 0.05, spring / 2), tint=(0.5, 0.7))
        for z in (0.5, 1.5):
            k.put(box(w / 2 - 0.1, 0.04, 0.09), "BH_Iron", M=T(sx * w / 4, -W / 2 - 0.01, z))
        k.put(torus(0.08, 0.014, 10, 4), "BH_Iron", M=TRS(sx * 0.2, -W / 2 - 0.04, 1.2, 90, 0, 0))
    semi = [(math.cos(a) * r_in, math.sin(a) * r_in) for a in [math.pi * i / 12 for i in range(13)]]
    k.put(prism(semi, 0.1), "BH_WoodDark", M=T(0, -W / 2 + 0.05, spring), tint=0.5)
    for i in range(5):
        a = math.pi * (i + 1) / 6
        k.put(box(0.04, 0.12, r_in - 0.1), "BH_Iron",
              M=T(0, -W / 2 - 0.0, spring) @ R(0, 90 - math.degrees(a), 0) @ T(0, 0, (r_in - 0.1) / 2))
    # broad threshold slab in two steps
    k.put(box(w + 2.6, 1.3, 0.1, bev=0.02), "BH_Stone", M=T(0, yF - 0.55, 0.05), tint=0.9)
    k.put(box(w + 1.4, 0.8, 0.2, bev=0.02), "BH_Stone", M=T(0, yF - 0.3, 0.1), tint=0.95)
    for sx in (-1, 1):
        pillar_round(k, sx * 2.0, yF - 0.32, h0 - 0.3)

    # ---- timber upper storey -----------------------------------------------------------------------------------
    k.put(box(L + 0.8, W + 0.8, 0.25, bev=0.03), "BH_WoodDark", M=T(0, 0, h0 + 0.12), tint=0.6)
    timber_frame(k, L + 0.4, W + 0.4, h0 + 0.25, h1)
    yU = -(W + 0.4) / 2
    zw = h0 + 0.25 + h1 / 2
    for sx in (-1, 1):
        for x in win_x:
            wide_window(k, T(sx * x, yU - 0.1, zw), 0.9, 1.3, shutters=False)
        for y in (-1.6, 1.6):
            wide_window(k, T(sx * ((L + 0.4) / 2 + 0.1), y, zw) @ R(0, 0, 90 * sx), 0.9, 1.15, shutters=False)
    for x in back_x:
        wide_window(k, T(x, (W + 0.4) / 2 + 0.1, zw) @ R(0, 0, 180), 0.8, 1.15, shutters=False)
    # gable end triangles (plaster, timber king post) at both X ends
    for sx in (-1, 1):
        t = prism([(-(W + 0.4) / 2, 0), ((W + 0.4) / 2, 0), (0, ph)], 0.2)
        k.put(t, "BH_Stone", M=T(sx * (L + 0.4) / 2, 0, zr) @ R(0, 0, 90), tint=1.2)
        k.put(box(0.26, 0.2, ph * 0.85), "BH_WoodDark", M=T(sx * (L + 0.5) / 2, 0, zr + ph * 0.42), tint=0.6)
        for sy in (-1, 1):
            d = math.hypot((W + 0.4) / 2, ph)
            k.put(box(0.26, d, 0.2), "BH_WoodDark",
                  M=TRS(sx * (L + 0.5) / 2, sy * (W + 0.4) / 4, zr + ph / 2, -sy * math.degrees(math.atan2(ph, (W + 0.4) / 2)), 0, 0),
                  tint=0.6)
        wide_window(k, T(sx * ((L + 0.4) / 2 + 0.1), 0, zr + 1.1) @ R(0, 0, 90 * sx), 0.7, 0.8, shutters=False)

    # ---- slate roof + chimney ---------------------------------------------------------------------------------
    slate_roof(k, L + 0.4, W + 0.4, zr - 0.05, ph, over=0.6, gable_over=0.35)
    # two lit dormers on the front slope
    zp = lambda y: (zr - 0.05) + ph * (1 - abs(y) / ((W + 0.4) / 2))
    dy0, dy1 = -2.7, -0.4
    zt = zp(dy0) + 1.2
    for sx in (-1, 1):
        dx = sx * 5.25
        k.put(box(1.5, 1.8, zt - (zp(dy0) - 0.1)), "BH_Stone", M=T(dx, dy0 + 0.9, (zt + zp(dy0) - 0.1) / 2), tint=1.15)
        k.put(prism([(-0.75, 0), (0.75, 0), (0, 0.6)], 0.12), "BH_Stone", M=T(dx, dy0 - 0.03, zt), tint=1.2)
        for px in (-0.75, 0.75):
            k.put(box(0.13, 0.15, zt - zp(dy0) + 0.2), "BH_WoodDark", M=T(dx + px, dy0 - 0.02, (zt + zp(dy0) - 0.2) / 2), tint=0.6)
        wide_window(k, T(dx, dy0 - 0.02, zp(dy0) + 0.65), 0.7, 0.75, shutters=False)
        k.put(box(1.7, 0.16, 0.14), "BH_WoodDark", M=T(dx, dy0 - 0.03, zt + 0.02), tint=0.55)
        hw, rise = 0.95, 0.65
        d = math.hypot(hw, rise)
        for sd in (-1, 1):
            k.put(box(d + 0.1, dy1 - dy0 + 0.35, 0.08), "BH_StoneDark",
                  M=TRS(dx + sd * hw / 2, (dy0 + dy1) / 2 - 0.05, zt + rise / 2 + 0.03, 0, sd * math.degrees(math.atan2(rise, hw)), 0), tint=0.7)
            k.put(box(0.1, dy1 - dy0 + 0.4, 0.1), "BH_WoodDark",
                  M=TRS(dx + sd * (hw + 0.02), (dy0 + dy1) / 2 - 0.05, zt - 0.04, 0, 0, 0), tint=0.5)
        k.put(box(0.16, dy1 - dy0 + 0.35, 0.12), "BH_WoodDark", M=T(dx, (dy0 + dy1) / 2 - 0.05, zt + rise + 0.06), tint=0.5)
    chimney(k, -4.6, 1.5, 10.6, w=1.1, d=0.95, z0=7.0)
    # warm chimney top: glowing embers in the flue with a few flame tongues
    k.put(box(0.6, 0.5, 0.06), "BH_Flame", M=T(-4.6, 1.5, 10.6 + 0.24), tint=1.0, uvoff=False)
    for dx, dy, hh in ((-0.12, 0.0, 0.16), (0.08, 0.05, 0.22), (0.16, -0.08, 0.12)):
        flame_tip(k, T(-4.6 + dx, 1.5 + dy, 10.6 + 0.27), hh)

    # ---- hanging signboard (both crests) ----------------------------------------------------------------------
    ys = yF - 1.15                      # sign plane
    sw, sh, sz1 = 4.0, 1.6, 5.2        # board width, height, top edge
    sz0 = sz1 - sh
    rail_z = sz1 + 0.17
    for sx in (-1, 1):
        # projecting arm from the timber wall + knee brace
        k.put(box(0.16, abs(ys - yU) + 0.1, 0.16), "BH_WoodDark", M=T(sx * 2.25, (ys + yU) / 2, rail_z), tint=0.55)
        d = math.hypot(1.0, 0.7)
        k.put(box(0.12, d, 0.12), "BH_WoodDark",
              M=TRS(sx * 2.25, yU - 0.5, rail_z - 0.4, -math.degrees(math.atan2(0.7, 1.0)), 0, 0), tint=0.55)
        k.put(ico(0.08, 1), "BH_Iron", M=T(sx * 2.25, ys, rail_z))
        # chains from the rail to the board
        for cx in (sx * (sw / 2 - 0.25),):
            k.put(tube([(cx, ys, rail_z - 0.02), (cx, ys, sz1 + 0.03)], 0.014, 5), "BH_Iron")
    k.put(cyl(0.05, sw + 0.7, 8), "BH_WoodDark", M=TRS(-(sw + 0.7) / 2, ys, rail_z, 0, 90, 0), tint=0.5)
    # board: dark timber frame, blue and violet panels, centre divider
    zc = (sz0 + sz1) / 2
    k.put(box(sw + 0.16, 0.12, sh + 0.16, bev=0.02), "BH_WoodDark", M=T(0, ys, zc), tint=0.55)
    k.put(box(sw / 2 - 0.08, 0.05, sh - 0.14), "BH_ClothBlue", M=T(-sw / 4 - 0.02, ys - 0.055, zc), tint=0.95)
    k.put(box(sw / 2 - 0.08, 0.05, sh - 0.14), "BH_ClothViolet", M=T(sw / 4 + 0.02, ys - 0.055, zc), tint=0.95)
    k.put(box(0.1, 0.09, sh, bev=0.01), "BH_WoodDark", M=T(0, ys - 0.06, zc), tint=0.5)
    for sx in (-1, 1):  # trim rails top/bottom
        k.put(box(sw / 2 - 0.05, 0.03, 0.05), "BH_Silver" if sx < 0 else "BH_Gold",
              M=T(sx * (sw / 4 + 0.02), ys - 0.085, sz1 - 0.1), tint=0.85)
        k.put(box(sw / 2 - 0.05, 0.03, 0.05), "BH_Silver" if sx < 0 else "BH_Gold",
              M=T(sx * (sw / 4 + 0.02), ys - 0.085, sz0 + 0.1), tint=0.85)
    swordfish(k, T(-sw / 4 - 0.02, ys - 0.13, zc + 0.02) @ R(0, -12, 0), 1.6, 0.06, "BH_Silver", 1.0)
    lantern_emblem(k, T(sw / 4 + 0.02, ys - 0.11, zc - 0.55), 1.2, "BH_Gold", 0.05)
    # small lanterns under the board corners; the light socket sits below the middle
    for sx in (-1, 1):
        k.put(tube([(sx * (sw / 2 - 0.15), ys - 0.03, sz0 - 0.02), (sx * (sw / 2 - 0.15), ys - 0.03, sz0 - 0.12)], 0.014, 5), "BH_Iron")
        hang_lantern(k, T(sx * (sw / 2 - 0.15), ys - 0.03, sz0 - 0.1), 0.42)

    # ---- door lantern from the keystone ------------------------------------------------------------------------
    k.put(tube([(0, yF, spring + r_out + 0.05), (0, yF - 0.45, spring + r_out + 0.05)], 0.02, 5), "BH_Iron")
    hang_lantern(k, T(0, yF - 0.45, spring + r_out), 0.55)

    # ---- banner poles: blue/silver swordfish on the left, violet/gold lantern on the right ---------------------
    yp = yF - 0.9
    bl = banner_pole(k, -3.3, yp, 5.8, 1.0, 3.2, "BH_ClothBlue", "BH_Silver")
    br = banner_pole(k, 3.3, yp, 5.8, 1.0, 3.2, "BH_ClothViolet", "BH_Gold", finial="BH_Gold")
    swordfish(k, T(bl[0], bl[1] - 0.035, bl[2] - 1.15), 0.75, 0.025, "BH_Silver", 0.9)
    lantern_emblem(k, T(br[0], br[1] - 0.035, br[2] - 1.55), 0.8, "BH_Gold", 0.03)

    k.sockets.append(("door", (0.0, yF - 1.0, 0.0)))
    k.sockets.append(("door_light", (0.0, yF - 0.45, spring + r_out - 0.45)))
    k.sockets.append(("banner_l", bl))
    k.sockets.append(("banner_r", br))
    k.sockets.append(("sign_light", (0.0, ys - 0.2, sz0 - 0.3)))

    # ---- collision ----------------------------------------------------------------------------------------------
    k.col_box(L + 0.7, W + 0.7, h0 + h1, T(0, 0, (h0 + h1) / 2))
    for sx in (-1, 1):
        k.col_box(0.8, 0.8, h0 - 0.3, T(sx * 2.0, yF - 0.32, (h0 - 0.3) / 2))
        k.col_box(0.55, 0.55, 6.2, T(sx * 3.3, yp, 3.1))
    return dict(recenter=False, damp=0.3, damp_h=1.2)
