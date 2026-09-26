"""Charged attacks, shield, casts, skills, hit reactions, stagger/physics, interaction and enemy/boss actions."""
import math

import bh_gait as G
from lib_attacks import body, attack, TIP, EASE_STRIKE
from lib_common import anim, breath
from lib_poses import (spin_legs, U, RELAX, tw, torso, look, hips, clav, arm, grip, fist, two_hand, foot, feet, leg_fk,
                       mirror, LEGS_FIGHT, LEGS_WIDE, LEGS_LOW, L_GUARD, L_SHIELD, ST_1H, ST_SHIELD, ST_2H, ST_STAFF)

S0 = ST_1H
LG = L_GUARD


# =================================================================================================================
def charged():
    out = []
    # charge_hold: weapon drawn far back over the right shoulder, weight loaded on the back leg (loop)
    h0 = U(body(LEGS_WIDE, yaw=-40, pitch=4, drop=0.1, side=-0.04), grip("R", 100, 0.16, 1.5, 120, 45),
           fist("L", 10, 0.36, 1.28, -20, 60), foot("R", -0.2, 0.17, 38, heel=10))
    h1 = U(h0, body(LEGS_WIDE, yaw=-42, pitch=5, drop=0.11, side=-0.045), grip("R", 102, 0.16, 1.49, 122, 46))
    a = anim("charge_hold", 40, [(0, h0), (20, h1)], loop=True, props="sword", layers=[breath(20, 1.4)],
             lag={"hik": 2})
    a.meta["tip"] = TIP["sword"]
    out.append(a)
    # charge_release: explosive horizontal cleave from the charged pose
    s1 = U(body(LEGS_WIDE, yaw=-10, pitch=6, drop=0.12, fwd=0.04), grip("R", 50, 0.5, 1.3, 55, 5), LG,
           foot("L", 0.3, 0.16, 14, knee=10))
    s2 = U(body(LEGS_WIDE, yaw=34, pitch=10, drop=0.15, fwd=0.08), grip("R", -50, 0.52, 1.2, -70, -4), LG,
           foot("L", 0.3, 0.16, 14, knee=10), foot("R", -0.22, 0.17, 30, heel=25))
    ft = U(body(LEGS_WIDE, yaw=50, pitch=10, drop=0.15, fwd=0.07), grip("R", -95, 0.38, 1.12, -130, -8),
           fist("L", 40, 0.2, 1.1, 30, 20), foot("L", 0.3, 0.16, 14, knee=10), foot("R", -0.22, 0.17, 30, heel=25))
    rec = U(body(LEGS_WIDE, yaw=24, pitch=4, drop=0.08), grip("R", -40, 0.34, 1.12, -60, 10), LG,
            foot("L", 0.2, 0.16, 14, up=0.03))
    out.append(attack("charge_release", "sword", 26, [(0, h0), (2, h0), (5, s1, "in"), (8, s2, EASE_STRIKE),
                                                     (12, ft, "out"), (18, rec), (26, S0)],
                      hits=[(3.5, 8.5)], cancel=18, footsteps=[6]))
    # special_attack: spinning double strike (two full turns, blade extended)
    pre = U(body(yaw=-40, pitch=4, drop=0.07), grip("R", 90, 0.28, 1.26, 120, 10), LG)
    k = [(0, S0), (6, pre, "out")]
    for i, (f, ang, lift) in enumerate([(9, 60, (0, 0)), (12, 180, (0, 0.06)), (15, 300, (0.06, 0)),
                                        (18, 420, (0, 0.06)), (21, 540, (0.06, 0)), (24, 660, (0, 0.05)),
                                        (27, 720, (0, 0))]):
        k.append((f, U(body(yaw=12, pitch=8, drop=0.1, spin=ang, lift=lift), grip("R", 5, 0.56, 1.2, 5, -2),
                       fist("L", 70, 0.3, 1.3, 60, 30)), "linear"))
    k.append((30, U(body(yaw=24, pitch=8, drop=0.09, spin=720), grip("R", -50, 0.4, 1.12, -80, -6), LG), "out"))
    k.append((38, U(S0, spin_legs(LEGS_FIGHT, 720))))
    out.append(attack("special_attack", "sword", 38, k, hits=[(8.5, 17), (18, 27.5)], cancel=31,
                      footsteps=[12, 15, 18, 21, 24]))
    return out


# =================================================================================================================
def shield():
    out = []
    B = ST_SHIELD
    blk = U(body(LEGS_WIDE, yaw=-10, pitch=10, drop=0.12), grip("L", -4, 0.4, 1.32, -6, 84, pole=-10, free=1.0),
            grip("R", 60, 0.22, 1.36, -30, 50), look(8, -8))
    blk2 = U(blk, body(LEGS_WIDE, yaw=-11, pitch=11, drop=0.125))
    out.append(anim("block_loop", 40, [(0, blk), (20, blk2)], loop=True, props="shield",
                    layers=[breath(20, 1.0)]))
    hit = U(body(LEGS_WIDE, yaw=-4, pitch=-6, drop=0.1, fwd=-0.05), grip("L", -2, 0.3, 1.36, -4, 90, pole=-10, free=1.0),
            grip("R", 64, 0.2, 1.38, -30, 55), look(8, 2), foot("R", -0.24, 0.17, 30, heel=12))
    out.append(anim("block_impact", 14, [(0, blk), (2, hit, "out"), (6, U(hit, body(LEGS_WIDE, yaw=-6, pitch=4, drop=0.13))),
                                         (14, blk)], props="shield", lag={"head": 1}))
    # parry: sweep the shield outward (to the left) to knock the blow aside, sword ready to riposte
    p1 = U(body(LEGS_WIDE, yaw=-18, pitch=6, drop=0.1), grip("L", -30, 0.34, 1.34, -40, 80, pole=-10, free=1.0),
           grip("R", 60, 0.24, 1.3, -20, 45))
    p2 = U(body(LEGS_WIDE, yaw=16, pitch=4, drop=0.1), grip("L", 60, 0.4, 1.36, 50, 70, pole=0, free=1.0),
           grip("R", 40, 0.36, 1.36, -10, 30))
    out.append(anim("parry", 16, [(0, B), (3, p1, "out"), (6, p2, "linear"), (9, U(p2, grip("L", 70, 0.36, 1.32, 60, 70, free=1.0)), "out"),
                                  (16, B)], props="shield", key=6, hits=[(3.5, 7)], cancel_after=10, parry=[2, 8]))
    # shield_bash: step in and punch the shield forward
    w = U(body(LEGS_WIDE, yaw=-30, pitch=0, drop=0.1, side=-0.03), grip("L", 40, 0.2, 1.3, 10, 84, free=1.0),
          grip("R", 70, 0.2, 1.3, 0, 40))
    b = U(body(LEGS_WIDE, yaw=16, pitch=16, drop=0.16, fwd=0.12), grip("L", -5, 0.54, 1.34, -6, 88, free=1.0),
          grip("R", 70, 0.18, 1.28, 0, 40), foot("L", 0.38, 0.16, 14, knee=10), foot("R", -0.24, 0.17, 30, heel=35))
    out.append(attack("shield_bash", "shield", 24, [(0, B), (6, w, "out"), (9, b, "in"), (13, U(b, body(LEGS_WIDE, yaw=18, pitch=17, drop=0.16, fwd=0.12))),
                                                   (18, U(B, foot("L", 0.2, 0.13, 12, up=0.03))), (24, B)],
                      hits=[(7.5, 10.5)], cancel=16, footsteps=[9]))
    out[-1].meta["tip"] = 0.0
    out[-1].meta["hit_bone"] = "weapon.L"
    return out


# =================================================================================================================
def casts():
    out = []
    R0 = U(RELAX, feet(0.06, -0.06, 0.13, 0.13, 10, 18), hips(0, 0, -0.03))
    # cast_quick: off-hand thrust forward (release at full extension)
    w = U(body(LEGS_FIGHT, yaw=-20, pitch=-2, drop=0.03), fist("L", 50, 0.2, 1.36, 20, 60), arm("R", -70, 20, 40))
    a = U(body(LEGS_FIGHT, yaw=10, pitch=6, drop=0.05, fwd=0.04), fist("L", 0, 0.56, 1.4, 0, 80), arm("R", -70, -10, 30))
    out.append(anim("cast_quick", 15, [(0, R0), (4, w, "out"), (7, a, "in"), (10, a), (15, R0)], release=7,
                    cancel_after=10, key=7))
    # cast_heavy: gather both hands at the chest, push both forward
    g = U(body(LEGS_FIGHT, yaw=-6, pitch=-6, drop=0.05), fist("L", 10, 0.16, 1.3, -40, 30), fist("R", 10, 0.16, 1.3, -40, 30))
    g2 = U(g, body(LEGS_FIGHT, yaw=-8, pitch=-8, drop=0.07), fist("L", 5, 0.14, 1.32, -40, 30), fist("R", 5, 0.14, 1.32, -40, 30))
    a = U(body(LEGS_FIGHT, yaw=4, pitch=10, drop=0.08, fwd=0.06), fist("L", 5, 0.56, 1.36, 0, 80), fist("R", 5, 0.56, 1.36, 0, 80),
          foot("L", 0.22, 0.13, 12, knee=8))
    out.append(anim("cast_heavy", 28, [(0, R0), (8, g, "out"), (14, g2), (17, a, "in"), (22, a), (28, R0)], release=17,
                    cancel_after=22, key=17))
    # cast_channel: both hands forward, sustained with tremor (loop)
    c1 = U(body(LEGS_FIGHT, yaw=4, pitch=8, drop=0.07, fwd=0.03), fist("L", 8, 0.5, 1.34, 0, 80), fist("R", 8, 0.5, 1.34, 0, 80))
    c2 = U(c1, fist("L", 6, 0.49, 1.35, 0, 82), fist("R", 10, 0.49, 1.33, 0, 78), body(LEGS_FIGHT, yaw=5, pitch=9, drop=0.075, fwd=0.03))
    out.append(anim("cast_channel", 30, [(0, c1), (8, c2), (15, c1), (23, c2)], loop=True, layers=[breath(15, 1.2)]))
    # cast_area: both hands raised, then driven down to the ground (ring bursts on impact)
    up = U(body(LEGS_WIDE, yaw=0, pitch=-12, drop=0.02), fist("L", 50, 0.2, 1.8, 0, 90), fist("R", 50, 0.2, 1.8, 0, 90),
           look(0, 20))
    down = U(body(LEGS_WIDE, yaw=0, pitch=40, drop=0.34, fwd=0.04), fist("L", 20, 0.46, 0.66, 0, -80),
             fist("R", 20, 0.46, 0.66, 0, -80), look(0, -10))
    out.append(anim("cast_area", 30, [(0, R0), (9, up, "out"), (12, up), (15, down, "in"), (21, down), (30, R0)],
                    release=15, cancel_after=22, key=15))
    # cast_weapon: raise the weapon skyward (weapon skill empower)
    raise_ = U(body(LEGS_FIGHT, yaw=-4, pitch=-10, drop=0.03), grip("R", 30, 0.14, 1.8, 0, 88), fist("L", 10, 0.3, 1.3, 0, 60),
               look(0, 18))
    out.append(anim("cast_weapon", 24, [(0, S0), (8, raise_, "out"), (15, U(raise_, grip("R", 30, 0.14, 1.84, 0, 90))),
                                        (24, S0)], props="sword", release=10, cancel_after=16, key=10))
    # cast_ultimate: gather, big two-hand overhead, then slam forward/down
    g = U(body(LEGS_WIDE, yaw=-10, pitch=8, drop=0.14), fist("L", 40, 0.18, 1.0, 0, -30), fist("R", 40, 0.18, 1.0, 0, -30),
          look(0, -12))
    up = U(body(LEGS_WIDE, yaw=0, pitch=-18, drop=-0.02), fist("L", 20, 0.1, 1.92, 0, 100), fist("R", 20, 0.1, 1.92, 0, 100),
           look(0, 25), foot("L", 0.14, 0.16, 14, heel=15), foot("R", -0.16, 0.17, 28, heel=25))
    up2 = U(up, body(LEGS_WIDE, yaw=0, pitch=-20, drop=-0.03))
    slam = U(body(LEGS_WIDE, yaw=0, pitch=34, drop=0.26, fwd=0.08), fist("L", 10, 0.56, 0.9, 0, -30),
             fist("R", 10, 0.56, 0.9, 0, -30), look(0, 6), foot("L", 0.28, 0.16, 14, knee=10))
    out.append(anim("cast_ultimate", 40, [(0, R0), (8, g, "out"), (17, up, "out"), (24, up2), (27, slam, "in"),
                                          (33, slam), (40, R0)], release=27, cancel_after=34, key=27))
    return out


# =================================================================================================================
def skills():
    out = []
    # whirlwind: continuous spin, blade extended (loop = one full turn)
    k = []
    n = 6
    for i in range(n + 1):
        ang = 360.0 * i / n
        lift = (0.05, 0.0) if i % 2 else (0.0, 0.05)
        if i in (0, n):
            lift = (0.0, 0.0)
        k.append((20 * i / n, U(body(LEGS_WIDE, yaw=10, pitch=10, drop=0.12, spin=ang, lift=lift),
                                grip("R", 0, 0.58, 1.18, 0, -4), fist("L", 80, 0.32, 1.28, 70, 20)), "linear"))
    a = anim("whirlwind", 20, k, loop=True, props="sword", hits=[(0, 10), (10, 20)], turn_per_loop=360)
    a.meta["tip"] = TIP["sword"]
    # the loop is a full turn: last key == first key rotated by 360 (identical rotation), keep as keyed
    out.append(a)
    # leap_slam: crouch, jump (in place, hips rise), crash down with the weapon
    c = U(body(LEGS_WIDE, yaw=-6, pitch=24, drop=0.22), grip("R", 70, 0.2, 1.0, 20, -20), fist("L", 20, 0.3, 1.0, 0, 20))
    air = U(body(LEGS_WIDE, yaw=0, pitch=-16, drop=-0.45), grip("R", 20, 0.08, 1.8, 0, 120), fist("L", 20, 0.1, 1.7, 0, 110),
            foot("L", 0.1, 0.16, 12, up=0.4, toe=-25, w=1), foot("R", -0.1, 0.16, 20, up=0.35, toe=-30, w=1), look(0, 10))
    air2 = U(air, body(LEGS_WIDE, yaw=0, pitch=-8, drop=-0.3), grip("R", 10, 0.3, 1.8, 0, 60),
             foot("L", 0.2, 0.16, 12, up=0.22), foot("R", -0.12, 0.16, 20, up=0.2))
    land = U(body(LEGS_WIDE, yaw=0, pitch=36, drop=0.34, fwd=0.06), grip("R", 5, 0.56, 0.8, 0, -45),
             fist("L", 40, 0.36, 0.9, 0, 0), foot("L", 0.26, 0.16, 14, knee=12), foot("R", -0.18, 0.17, 28, heel=20, knee=12))
    out.append(attack("leap_slam", "sword", 36, [(0, S0), (6, c, "out"), (9, c), (14, air, "out"), (18, air2),
                                                (21, land, "in"), (28, land), (36, S0)],
                      hits=[(18.5, 21.5)], cancel=29, footsteps=[21], airborne=[10, 21]))
    # war_cry: chest out, arms flung wide, roar skyward
    g = U(body(LEGS_WIDE, yaw=0, pitch=16, drop=0.12), arm("L", -50, 60, 100), arm("R", -50, 60, 100), look(0, -16))
    cry = U(body(LEGS_WIDE, yaw=0, pitch=-16, drop=0.08), arm("L", 10, -20, 70, 0, -20), arm("R", 10, -20, 70, 0, -20),
            clav("L", 14, -10), clav("R", 14, -10), look(0, 28))
    out.append(anim("war_cry", 34, [(0, S0), (8, g, "out"), (13, cry, "in"), (26, U(cry, look(0, 32))), (34, S0)],
                    release=13, cancel_after=26, key=13, props="sword"))
    # blink: compress, vanish (hands cross over the chest), reappear expanding
    comp = U(body(LEGS_FIGHT, yaw=0, pitch=18, drop=0.14), fist("L", -40, 0.16, 1.32, -60, 40), fist("R", -40, 0.16, 1.32, -60, 40),
             look(0, -12))
    burst = U(body(LEGS_FIGHT, yaw=0, pitch=-8, drop=0.02), arm("L", -30, -10, 20), arm("R", -30, -10, 20), look(0, 6))
    out.append(anim("blink", 15, [(0, RELAX), (4, comp, "out"), (6, comp), (8, burst, "in"), (15, RELAX)], release=6,
                    cancel_after=10, key=6, iframes=[3, 9]))
    return out


# =================================================================================================================
def reactions():
    out = []
    B = U(RELAX, feet(0.06, -0.08, 0.13, 0.14, 10, 20), hips(0, 0, -0.03))

    def react(name, length, peak, recoil=None, **meta):
        keys = [(0, B), (2, peak, "out")]
        if recoil is not None:
            keys.append((5, recoil))
        keys.append((length, B))
        out.append(anim(name, length, keys, lag={"head": 1.0, "arm": 1.0, "neck": 0.5}, key=2, **meta))

    react("hit_light", 12, U(B, torso(0, -6, 0, 0, -4, 0, 0, -3, 0), look(0, -8), hips(0, -0.02, -0.04)))
    react("hit_heavy", 18, U(B, torso(0, -16, 4, 0, -10, 2, 0, -8, 0), look(-10, -16), hips(0, -0.06, -0.07),
                             arm("L", -40, 40, 50), arm("R", -40, 30, 40), foot("L", 0.02, 0.13, 10, heel=10)),
          U(B, torso(0, 8, 0, 0, 6, 0, 0, 4, 0), hips(0, -0.03, -0.09), look(0, 8)))
    react("hit_front", 14, U(B, torso(0, -14, 0, 0, -8, 0, 0, -6, 0), look(0, -14), hips(0, -0.05, -0.05),
                             arm("L", -50, 30, 40), arm("R", -50, 30, 40)),
          U(B, torso(0, 4, 0, 0, 2, 0, 0, 2, 0), hips(0, -0.03, -0.06)))
    react("hit_back", 14, U(B, torso(0, 20, 0, 0, 10, 0, 0, 8, 0), look(0, 16), hips(0, 0.05, -0.06),
                            arm("L", -60, -30, 30), arm("R", -60, -30, 30)),
          U(B, torso(0, 6, 0, 0, 3, 0, 0, 2, 0), hips(0, 0.02, -0.06)))
    # hit from the left: torso bends away (to the right), head snaps right
    react("hit_left", 14, U(B, torso(-14, 0, -12, -6, 0, -8, -6, 0, -6), look(-20, 0, -10), hips(-0.05, 0, -0.05),
                            arm("L", -40, 20, 50), arm("R", -60, 20, 20)),
          U(B, torso(-4, 2, -2, 0, 0, -2, 0, 0, 0), hips(-0.02, 0, -0.05)))
    out.append(anim("hit_right", 14, [(f, mirror(p), e) for f, p, e in out[-1].keys], lag={"head": 1.0, "arm": 1.0}, key=2))
    return out


def lying(pitch=-90.0, arms="spread"):
    """Lying on the back (pelvis on the ground, legs FK)."""
    p = U(RELAX, hips(0, 0, -0.84), torso(0, pitch, 0, 0, 6, 0, 0, 4, 0), look(20, 8),
          leg_fk("L", 12, 18, 30, 8), leg_fk("R", 28, 50, 20, 4))
    if arms == "spread":
        p.update(U(arm("L", -20, -20, 30, 0, 10), arm("R", -30, -50, 40, 0, 10)))
    return p


def physics():
    out = []
    B = U(RELAX, feet(0.06, -0.08, 0.13, 0.14, 10, 20), hips(0, 0, -0.03))
    # stagger_small: rocked back, one step back to catch balance
    k1 = U(B, torso(0, -14, 0, 0, -8, 0, 0, -6, 0), hips(0, -0.06, -0.05), look(0, -10), arm("L", -40, 50, 40), arm("R", -45, 45, 40),
           foot("R", -0.08, 0.14, 20, up=0.06))
    k2 = U(B, torso(0, 8, 0, 0, 4, 0, 0, 2, 0), hips(0, -0.06, -0.1), foot("R", -0.26, 0.15, 22, heel=15, knee=8),
           arm("L", -55, 40, 40), arm("R", -55, 40, 40))
    out.append(anim("stagger_small", 20, [(0, B), (3, k1, "out"), (8, k2), (13, U(k2, hips(0, -0.04, -0.07))), (20, B)],
                    footsteps=[8], lag={"head": 1, "arm": 1.5}))
    # stagger_heavy: two stumbling steps back, arms windmilling
    k1 = U(B, torso(0, -22, 4, 0, -10, 2, 0, -8, 0), hips(0, -0.08, -0.05), look(8, -16), arm("L", -10, 60, 30), arm("R", -20, 40, 40),
           foot("L", 0.0, 0.14, 12, up=0.08))
    k2 = U(B, torso(0, -8, -4, 0, -4, 0, 0, -4, 0), hips(0, -0.1, -0.1), foot("L", -0.24, 0.15, 14, knee=8),
           foot("R", -0.02, 0.15, 20, up=0.08), arm("L", 10, 20, 40), arm("R", -50, 60, 40))
    k3 = U(B, torso(0, 14, 2, 0, 8, 0, 0, 6, 0), hips(0, -0.1, -0.14), foot("L", -0.24, 0.15, 14, knee=8),
           foot("R", -0.36, 0.16, 24, heel=15, knee=10), arm("L", -60, 50, 50), arm("R", -60, 40, 50), look(0, 10))
    out.append(anim("stagger_heavy", 32, [(0, B), (3, k1, "out"), (9, k2), (15, k3), (22, U(k3, hips(0, -0.08, -0.1))),
                                          (32, B)], footsteps=[9, 15], lag={"head": 1, "arm": 2}))
    # knockback: thrown backward, airborne, lands on the back (in place; the game moves the capsule)
    hit = U(B, torso(0, -30, 0, 0, -14, 0, 0, -10, 0), hips(0, -0.1, 0.0), look(0, -20), arm("L", 0, 40, 30), arm("R", 0, 40, 30),
            foot("L", 0.1, 0.14, 12, up=0.1, toe=-10), foot("R", 0.05, 0.14, 14, up=0.06, toe=-10))
    fly = U(RELAX, hips(0, 0, -0.2), torso(0, -60, 0, 0, 10, 0, 0, 10, 0), look(0, 20), arm("L", 20, 30, 50), arm("R", 30, 20, 50),
            leg_fk("L", 60, 70, 20), leg_fk("R", 40, 50, 20))
    land = lying()
    bounce = U(land, hips(0, 0, -0.78), torso(0, -84, 0, 0, 8, 0, 0, 6, 0))
    out.append(anim("knockback", 36, [(0, B), (3, hit, "out"), (10, fly), (18, land, "in"), (21, bounce, "out"), (25, land),
                                      (36, land)], lag={"head": 1.5, "arm": 2}, travel=3.0, key=18))
    # launch: airborne flail (loop)
    f1 = U(RELAX, hips(0, 0, 0.0), torso(0, -40, 10, 0, 8, 0, 0, 8, 0), look(10, 16), arm("L", 30, 30, 40), arm("R", 10, 60, 70),
           leg_fk("L", 50, 80, 30), leg_fk("R", 20, 40, 20))
    f2 = U(RELAX, hips(0, 0, 0.0), torso(0, -50, -10, 0, 10, 0, 0, 10, 0), look(-10, 20), arm("L", 10, 60, 70), arm("R", 30, 30, 40),
           leg_fk("L", 25, 40, 20), leg_fk("R", 55, 80, 30))
    out.append(anim("launch", 24, [(0, f1), (12, f2)], loop=True, lag={"arm": 2, "head": 1}))
    # wall_impact: back slams into a surface, head snaps, slides down into a slump
    slam = U(B, torso(0, -18, 0, 0, -10, 0, 0, -8, 0), hips(0, -0.06, -0.02), look(0, -24), arm("L", -30, -40, 20), arm("R", -30, -40, 20))
    rebound = U(B, torso(0, 16, 0, 0, 10, 0, 0, 8, 0), hips(0, -0.04, -0.12), look(0, 20), arm("L", -60, 20, 30), arm("R", -60, 20, 30))
    slump = U(RELAX, hips(0, -0.1, -0.62), torso(0, -8, 4, 0, 14, 0, 0, 12, 0), look(10, 26, 10),
              foot("L", 0.32, 0.15, 30, toe=10, knee=15), foot("R", 0.26, 0.17, 10, toe=5, knee=5),
              arm("L", -70, 10, 20), arm("R", -60, 30, 30))
    out.append(anim("wall_impact", 32, [(0, B), (2, slam, "out"), (6, rebound), (14, U(rebound, hips(0, -0.08, -0.3))),
                                        (22, slump, "out"), (32, slump)], lag={"head": 1.5, "arm": 2}, key=2))
    # knockdown: legs taken out, falls on the back
    k1 = U(B, torso(0, -20, 0, 0, -10, 0, 0, -8, 0), hips(0, 0.0, -0.1), look(0, -12), arm("L", -10, 40, 30), arm("R", -10, 40, 30),
           foot("L", 0.2, 0.14, 12, up=0.1), foot("R", 0.16, 0.14, 14, up=0.05))
    k2 = U(RELAX, hips(0, 0.0, -0.55), torso(0, -50, 0, 0, 10, 0, 0, 10, 0), look(0, 20), arm("L", -20, 10, 40), arm("R", -20, 10, 40),
           leg_fk("L", 70, 40, 20), leg_fk("R", 60, 50, 20))
    out.append(anim("knockdown", 24, [(0, B), (3, k1, "out"), (9, k2, "in"), (13, lying(), "in"), (16, U(lying(), hips(0, 0, -0.8))),
                                      (24, lying())], lag={"head": 1.5, "arm": 2}, key=13))
    # getup: from the back -> sit up -> knee -> stand
    sit = U(RELAX, hips(0, 0.0, -0.8), torso(0, -20, 0, 0, 20, 0, 0, 14, 0), look(0, 6), leg_fk("L", 70, 110, -10, 8), leg_fk("R", 30, 40, 20, 6),
            arm("L", -70, -40, 20), arm("R", -70, -40, 20))
    kneel = U(RELAX, hips(0, 0.05, -0.5), torso(0, 20, 0, 0, 10, 0, 0, 6, 0), look(0, -6),
              foot("L", 0.34, 0.13, 10, knee=6), foot("R", -0.24, 0.14, 14, heel=40, knee=4),
              arm("L", -70, 40, 60), arm("R", -80, 10, 20))
    rise = U(RELAX, hips(0, 0.02, -0.16), torso(0, 16, 0, 0, 6, 0, 0, 4, 0), foot("L", 0.2, 0.13, 10), foot("R", -0.1, 0.14, 14, heel=10),
             arm("L", -70, 30, 40), arm("R", -70, 20, 30))
    out.append(anim("getup", 28, [(0, lying()), (6, sit, "out"), (13, kneel), (21, rise), (28, B)], lag={"head": 1, "arm": 1.5},
                    footsteps=[13, 22]))
    # death: stagger, drop to the knees, topple backward and lie still
    d1 = U(B, torso(0, -12, 6, 0, -6, 0, 0, -6, 0), hips(0, -0.04, -0.06), look(10, -14), arm("L", -60, 60, 60), arm("R", -50, 40, 40))
    knees = U(RELAX, hips(0, 0.0, -0.56), torso(0, 10, 4, 0, 10, 0, 0, 10, 0), look(0, 20, 6),
              leg_fk("L", 80, 150, 20), leg_fk("R", 75, 150, 20), arm("L", -80, 10, 10), arm("R", -84, 5, 10))
    tip = U(RELAX, hips(0, 0.0, -0.66), torso(0, -40, 0, 0, 10, 0, 0, 8, 0), look(0, 10), leg_fk("L", 60, 110, 20), leg_fk("R", 50, 100, 20),
            arm("L", -30, 20, 20), arm("R", -30, 20, 20))
    dead = lying(arms="spread")
    out.append(anim("death", 46, [(0, B), (5, d1, "out"), (14, knees, "in"), (20, knees), (28, tip, "in"), (33, dead, "in"),
                                  (36, U(dead, hips(0, 0, -0.8))), (46, dead)], lag={"head": 2, "arm": 2.5}, key=33))
    # revive: from the death pose, rise up with the chest lifted (light), stand
    lift = U(sit, torso(0, -10, 0, 0, 10, 0, 0, 6, 0), look(0, 20), arm("L", -30, 40, 50), arm("R", -30, 40, 50))
    out.append(anim("revive", 46, [(0, dead), (10, dead), (18, lift, "out"), (27, kneel), (36, rise), (46, B)],
                    lag={"head": 1.5, "arm": 2}, key=18))
    return out


# =================================================================================================================
def interaction():
    out = []
    B = RELAX
    # interact_pickup: crouch, reach down to the ground with the right hand, rise
    down = U(RELAX, hips(0, 0.02, -0.46), torso(0, 34, 0, 0, 18, 0, 0, 10, 0), look(0, 10),
             foot("L", 0.18, 0.14, 12, knee=8), foot("R", -0.1, 0.15, 18, heel=30, knee=8),
             fist("R", 25, 0.36, 0.52, 0, -60), arm("L", -40, 60, 70))
    out.append(anim("interact_pickup", 30, [(0, B), (10, down, "out"), (15, U(down, fist("R", 25, 0.34, 0.5, 0, -70))),
                                            (23, U(RELAX, fist("R", 20, 0.26, 1.12, -30, 30))), (30, B)], key=14, release=14))
    # interact_chest: kneel, both hands under the lid, lift it up
    k = U(RELAX, hips(0, 0.02, -0.34), torso(0, 22, 0, 0, 12, 0, 0, 8, 0), look(0, 20),
          foot("L", 0.16, 0.16, 10, knee=8), foot("R", -0.14, 0.16, 16, heel=25, knee=8),
          fist("L", -10, 0.46, 0.76, 0, 10), fist("R", -10, 0.46, 0.76, 0, 10))
    lift = U(k, hips(0, 0.0, -0.22), torso(0, 4, 0, 0, 2, 0, 0, 0, 0), look(0, 12),
             fist("L", -10, 0.44, 1.2, 0, 60), fist("R", -10, 0.44, 1.2, 0, 60))
    out.append(anim("interact_chest", 36, [(0, B), (10, k, "out"), (14, k), (22, lift, "in"), (26, lift), (36, B)],
                    key=22, release=20))
    # interact_talk: conversational gestures (loop)
    t1 = U(RELAX, fist("R", 20, 0.36, 1.18, 0, 40), look(0, 2))
    t2 = U(RELAX, fist("R", 30, 0.4, 1.24, 20, 60), fist("L", 40, 0.3, 1.1, -10, 40), look(6, -4, 3), torso(0, 0, 0, 3, 0, 0, 4, -1, 0))
    t3 = U(RELAX, fist("L", 20, 0.36, 1.18, 0, 40), look(-6, 3), torso(0, 0, 0, -2, 0, 0, -3, 0, 0))
    out.append(anim("interact_talk", 90, [(0, t1), (18, t2), (36, U(t2, fist("R", 25, 0.42, 1.2, 10, 50))), (54, t3),
                                          (72, U(RELAX, look(0, -3)))], loop=True, layers=[breath(45, 1.0)]))
    # interact_teleport: raise the right hand to the waystone, brace the stance, light engulfs
    raise_ = U(body(LEGS_WIDE, yaw=0, pitch=-4, drop=0.08), fist("R", 20, 0.44, 1.72, 0, 90), arm("L", -60, -20, 40),
               look(0, 22))
    brace = U(raise_, body(LEGS_WIDE, yaw=0, pitch=6, drop=0.14), fist("R", 20, 0.46, 1.76, 0, 90), arm("L", -40, -40, 50),
              look(0, 16))
    out.append(anim("interact_teleport", 36, [(0, B), (10, raise_, "out"), (18, brace), (30, U(brace, body(LEGS_WIDE, yaw=0, pitch=8, drop=0.15))),
                                              (36, brace)], key=18, release=18))
    return out


# =================================================================================================================
def boss():
    out = []
    B = ST_1H
    # alert: startled hop, weapon snaps up
    j = U(body(LEGS_FIGHT, yaw=0, pitch=-10, drop=-0.03), grip("R", 50, 0.3, 1.4, -10, 50), fist("L", 10, 0.3, 1.34, 0, 60),
          look(0, 10), foot("L", 0.14, 0.13, 12, up=0.04), foot("R", -0.15, 0.15, 30, up=0.03))
    out.append(anim("alert", 18, [(0, RELAX), (3, U(RELAX, hips(0, 0, -0.06), look(0, -4)), "out"), (6, j, "out"),
                                  (11, U(B, hips(0, 0, -0.1))), (18, B)], props="sword", key=6))
    # taunt: beat the chest twice, beckon
    t1 = U(body(LEGS_FIGHT, yaw=6, pitch=-8, drop=0.05), grip("R", 60, 0.2, 1.1, 20, 10), fist("L", -10, 0.2, 1.36, -40, 30),
           look(0, 10))
    t2 = U(t1, fist("L", -10, 0.12, 1.34, -40, 30), torso(4, -10, 0, 0, -4, 0, 0, -6, 0))
    beck = U(body(LEGS_FIGHT, yaw=0, pitch=-4, drop=0.05), grip("R", 60, 0.2, 1.1, 20, 10), fist("L", 10, 0.46, 1.36, 0, 60),
             look(0, 6))
    beck2 = U(beck, fist("L", 10, 0.34, 1.44, 0, 90))
    out.append(anim("taunt", 46, [(0, B), (6, t1), (9, t2, "in"), (12, t1), (15, t2, "in"), (18, t1), (26, beck), (31, beck2),
                                  (36, beck), (46, B)], props="sword", key=9))
    # boss_slam: two-handed overhead hammer-fist slam (weapon or fists)
    up = U(body(LEGS_WIDE, yaw=0, pitch=-20, drop=0.0), fist("L", 20, 0.0, 1.96, 0, 110), fist("R", 20, 0.0, 1.96, 0, 110),
           look(0, 16), foot("L", 0.16, 0.16, 14, heel=10))
    slam = U(body(LEGS_WIDE, yaw=0, pitch=48, drop=0.36, fwd=0.08), fist("L", 10, 0.56, 0.5, 0, -60),
             fist("R", 10, 0.56, 0.5, 0, -60), look(0, -4), foot("L", 0.3, 0.16, 14, knee=12))
    out.append(anim("boss_slam", 42, [(0, B), (12, up, "out"), (20, U(up, body(LEGS_WIDE, yaw=0, pitch=-24, drop=-0.02))),
                                      (24, slam, "in"), (32, slam), (42, B)], props="sword",
                    hits=[(21.5, 25)], release=24, cancel_after=34, key=24))
    # boss_sweep: wide 180-degree horizontal sweep with the weapon
    w = U(body(LEGS_WIDE, yaw=-60, pitch=6, drop=0.12), grip("R", 100, 0.3, 1.2, 140, 0), fist("L", 40, 0.2, 1.2, 40, 30))
    s1 = U(body(LEGS_WIDE, yaw=-20, pitch=8, drop=0.14), grip("R", 40, 0.54, 1.12, 60, -4), fist("L", 60, 0.2, 1.2, 40, 30))
    s2 = U(body(LEGS_WIDE, yaw=40, pitch=10, drop=0.15, fwd=0.04), grip("R", -40, 0.54, 1.1, -60, -6), fist("L", 60, 0.2, 1.2, 40, 30))
    ft = U(body(LEGS_WIDE, yaw=60, pitch=8, drop=0.14), grip("R", -90, 0.4, 1.1, -130, -6), fist("L", 60, 0.2, 1.2, 40, 30))
    out.append(attack("boss_sweep", "sword", 36, [(0, B), (12, w, "out"), (16, w), (19, s1, "in"), (23, s2, EASE_STRIKE),
                                                 (27, ft, "out"), (36, B)], hits=[(18.5, 24)], cancel=30))
    # boss_roar: rear back, then roar forward with arms flared
    rear = U(body(LEGS_WIDE, yaw=0, pitch=16, drop=0.14), arm("L", -60, 40, 90), arm("R", -60, 40, 90), look(0, -20))
    roar = U(body(LEGS_WIDE, yaw=0, pitch=-14, drop=0.1), arm("L", -10, -30, 50, 0, -30), arm("R", -10, -30, 50, 0, -30),
             clav("L", 16, -12), clav("R", 16, -12), look(0, 24))
    out.append(anim("boss_roar", 46, [(0, B), (10, rear, "out"), (15, roar, "in"), (36, U(roar, look(0, 28))), (46, B)],
                    props="sword", release=15, key=15, layers=[]))
    # boss_charge: head-down charging run (loop, in place)
    g = G.Gait(frames=20, speed=6.0, duty=0.26, lift=0.2, bob=0.025, bob_phase="run", drop=0.1, reach_bias=-0.12,
               toe_strike=5, heel_off=45, lean=24, pelvis_yaw=12, arm_el=-50, elbow=80, arm_swing=26, upper=True)
    a = anim("boss_charge", 20, [(0, {}), (20, {})], loop=True, layers=[g.layer()], props="sword")
    a.meta.update(g.meta())
    a.gait = g
    out.append(a)
    # boss_summon: arms rise to the sky, then drive down to call minions
    up = U(body(LEGS_WIDE, yaw=0, pitch=-14, drop=0.06), arm("L", 60, 0, 20, 0, 0), arm("R", 60, 0, 20, 0, 0),
           clav("L", 18, 0), clav("R", 18, 0), look(0, 30))
    down = U(body(LEGS_WIDE, yaw=0, pitch=24, drop=0.2), fist("L", 60, 0.4, 0.8, 30, -60), fist("R", 60, 0.4, 0.8, 30, -60),
             look(0, -4))
    out.append(anim("boss_summon", 46, [(0, B), (14, up, "out"), (24, U(up, look(0, 34))), (29, down, "in"), (38, down),
                                        (46, B)], props="sword", release=29, key=29))
    return out


def build():
    out = []
    out += charged()
    out += shield()
    out += casts()
    out += skills()
    out += reactions()
    out += physics()
    out += interaction()
    out += boss()
    return out
