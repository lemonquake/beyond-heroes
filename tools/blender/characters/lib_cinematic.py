"""bh-021 cinematic clips (cs_*) for the legends' cutscenes. Only characters that list them in CLIPS / CLIPS_ONLY
export them (build_chars skips cs_* for the full hero set).

  Aljay (Dusk-Piercer in the right hand)   cs_aj_kneel* cs_aj_rise cs_aj_point* cs_aj_clutch cs_aj_charge* cs_aj_chained*
                                           cs_aj_dragged cs_aj_stand*
  Roydo (Dawnmaul in the right hand)       cs_ro_land cs_ro_shoulder* cs_ro_slam cs_ro_brace* cs_ro_fall cs_ro_stand*
  Paul David                               cs_pd_idle* cs_pd_shard* cs_pd_hand cs_pd_gesture* cs_pd_branded cs_pd_reach
                                           cs_pd_ready* (Stormwake in the right hand)
  Kethrax (chain-mace in the right hand)   cs_kx_emerge cs_kx_pull* cs_kx_bind cs_kx_kneel
(* = loop; the game's CutsceneActor.LOOPS lists the same set.) One-shots end on a held pose the next clip starts from.
"""
import math

import bh_gait as G
from lib_attacks import body
from lib_common import anim, breath, sway
from lib_poses import (U, RELAX, torso, look, hips, clav, arm, grip, fist, two_hand, foot, feet, leg_fk,
                       LEGS_FIGHT, LEGS_WIDE, LEGS_LOW)


def shake(amp=1.0, period=3.0):
    """Tremor layer (strain): small fast jitters in the torso, head and arms."""
    def fn(f, c):
        a = math.sin(f * 2 * math.pi / period) * amp
        b = math.sin(f * 2 * math.pi / (period * 1.37) + 1.1) * amp
        c["chest.roll"] += 0.8 * a
        c["spine.pitch"] += 0.6 * b
        c["head.yaw"] += 1.2 * b
        c["head.pitch"] += 0.8 * a
        c["clav.L.raise"] += 1.5 * a
        c["clav.R.raise"] -= 1.5 * b
    return fn


# kneeling on the right knee, left foot forward (from the getup library's kneel)
LEGS_KNEEL = U(hips(0, 0.06, -0.5), foot("L", 0.34, 0.13, 10, knee=6), foot("R", -0.26, 0.14, 14, heel=45, knee=4))
LEGS_KNEEL_LOW = U(hips(0, 0.08, -0.56), foot("L", 0.36, 0.14, 12, knee=8), foot("R", -0.3, 0.15, 16, heel=55, knee=4))


# ============================================================================================================ Aljay
def aljay():
    out = []
    # kneel: lance planted upright at his right side, head bowed, left hand on the left knee
    kn = U(RELAX, LEGS_KNEEL_LOW, torso(0, 18, 0, 0, 12, 0, 0, 10, 0), look(0, 34),
           grip("R", 72, 0.3, 0.96, 10, 128, 0, pole=0), fist("L", 18, 0.34, 0.62, 0, -30))
    kn2 = U(kn, torso(0, 20, 0, 0, 13, 0, 0, 11, 2), look(0, 36, 2))
    out.append(anim("cs_aj_kneel", 60, [(0, kn), (30, kn2)], loop=True, props="spear", layers=[breath(30, 1.6)]))
    # rise: slow ascent, the head lifts, the lance sweeps down to point at the host
    half = U(RELAX, hips(0, 0.03, -0.3), foot("L", 0.26, 0.14, 12, knee=8), foot("R", -0.16, 0.15, 16, heel=25, knee=6),
             torso(0, 12, 0, 0, 8, 0, 0, 6, 0), look(0, 18), grip("R", 70, 0.3, 1.1, 10, 112), fist("L", 30, 0.3, 0.84, 0, -20))
    up = U(RELAX, LEGS_WIDE, torso(-10, -6, 0, -4, -4, 0, 4, -6, 0), look(10, -12),
           grip("R", 66, 0.3, 1.16, 6, 74), fist("L", 40, 0.26, 1.02, 0, 0))
    point = aj_point()
    out.append(anim("cs_aj_rise", 84, [(0, kn), (10, kn), (34, half, "out"), (50, up), (58, U(up, look(8, -18))),
                                       (68, U(point, grip("R", 40, 0.4, 1.3, -10, 30)), "in"), (76, point, "out"), (84, point)],
                    props="spear", layers=[breath(28, 1.2)]))
    out.append(anim("cs_aj_point", 60, [(0, point), (30, U(point, body(LEGS_WIDE, yaw=-22, pitch=-3, drop=0.13)))], loop=True,
                    props="spear", layers=[breath(30, 1.3)]))
    # clutch: the wrath rises; the left claw digs into the heart, he folds forward, shakes, and straightens again
    fold = U(RELAX, LEGS_WIDE, torso(-10, 30, 6, -4, 22, 0, 0, 16, 0), look(-4, 30, 6), hips(0, 0.04, -0.16),
             grip("R", 60, 0.34, 0.9, 10, 20), fist("L", -30, 0.14, 1.28, -20, 40))
    steady = U(RELAX, LEGS_WIDE, torso(-8, -8, 0, -2, -6, 0, 0, -6, 0), look(0, -16), hips(0, 0, -0.1),
               grip("R", 60, 0.34, 1.1, 8, 30), fist("L", 40, 0.34, 1.0, 0, 10))
    out.append(anim("cs_aj_clutch", 96, [(0, point), (14, fold, "out"), (54, U(fold, torso(-10, 36, 8, -4, 26, 0, 0, 18, 0))),
                                         (74, steady, "in"), (96, steady)], props="spear",
                    layers=[_ramped(shake(1.6, 3.0), 10, 18, 52, 64), breath(24, 2.0)]))
    # charge: lance couched under the right arm, head down, running hard (in place)
    g = G.Gait(frames=20, speed=6.5, duty=0.28, lift=0.2, bob=0.028, bob_phase="run", drop=0.12, reach_bias=-0.1,
               toe_strike=5, heel_off=45, lean=22, pelvis_yaw=10, arm_el=-50, elbow=80, arm_swing=0, upper=False)
    couch = U(grip("R", 25, 0.26, 1.1, -4, 20, 0, pole=0), fist("L", 50, 0.28, 1.12, 0, 20), look(0, -14))
    a = anim("cs_aj_charge", 20, [(0, couch), (20, couch)], loop=True, layers=[g.layer()], props="spear")
    a.meta.update(g.meta())
    a.gait = g
    out.append(a)
    # chained: arms hauled back and out by the chains, chest forced forward, roaring against them
    ch1 = U(RELAX, LEGS_WIDE, hips(0, -0.04, -0.14), torso(0, -18, 0, 0, -12, 0, 0, -10, 0), look(0, -24),
            arm("L", 10, -60, 30), arm("R", 10, -60, 30), clav("L", 10, -20), clav("R", 10, -20))
    ch2 = U(ch1, torso(6, -10, -6, 2, -6, 0, 4, -4, 0), arm("L", -5, -40, 40), arm("R", 20, -75, 20), look(10, -14, -6),
            hips(0.02, -0.02, -0.12))
    ch3 = U(ch1, torso(-6, -14, 6, -2, -8, 0, -4, -6, 0), arm("L", 22, -75, 20), arm("R", -4, -42, 40), look(-10, -20, 6))
    out.append(anim("cs_aj_chained", 60, [(0, ch1), (16, ch2), (32, ch1), (46, ch3), (60, ch1)], loop=True,
                    layers=[shake(1.2, 2.6)]))
    # dragged: knees buckle, hauled backward, one arm still reaching forward
    dr1 = U(RELAX, hips(0, -0.1, -0.5), torso(0, -24, 0, 0, -10, 0, 0, -8, 0), look(0, -10),
            leg_fk("L", 70, 110, 10), leg_fk("R", 50, 90, 10), arm("L", 20, -80, 20), arm("R", 10, 80, 20))
    dr2 = U(RELAX, hips(0, -0.2, -0.72), torso(0, -48, 0, 0, -10, 0, 0, -8, 0), look(0, 10),
            leg_fk("L", 50, 60, 10), leg_fk("R", 30, 40, 10), arm("L", 40, -90, 20), arm("R", 30, 85, 10))
    out.append(anim("cs_aj_dragged", 54, [(0, ch1), (10, dr1, "in"), (30, dr2), (54, dr2)], layers=[shake(0.8, 2.4)]))
    # stand: the lance grounded upright like a banner staff, the other fist at his side
    st = U(RELAX, feet(0.06, -0.06, 0.15, 0.15, 12, 16), hips(0, 0, -0.03), look(0, -6),
           grip("R", 70, 0.3, 1.2, 8, 88, 0), fist("L", 90, 0.24, 0.96, 0, -60))
    out.append(anim("cs_aj_stand", 72, [(0, st), (36, U(st, look(4, -8)))], loop=True, props="spear",
                    layers=[breath(36, 1.2), sway(72, 0.6)]))
    return out


def aj_point():
    return U(RELAX, body(LEGS_WIDE, yaw=-24, pitch=-4, drop=0.12), grip("R", 20, 0.46, 1.34, -6, 6, 0, pole=-10),
             arm("L", -10, 30, 30, 0, -10), look(24, -8))


def _ramped(fn, f0, f1, f2, f3):
    from lib_common import ramp_layer
    return ramp_layer(fn, f0, f1, f2, f3)


# ============================================================================================================ Roydo
def roydo():
    out = []
    crouch = U(RELAX, hips(0, 0.08, -0.62), foot("L", 0.3, 0.2, 18, knee=14), foot("R", -0.2, 0.2, 26, heel=40, knee=10),
               torso(0, 38, 0, 0, 16, 0, 0, 12, 0), look(0, -20), grip("R", 20, 0.48, 0.42, 0, -70), two_hand("L", -0.25))
    impact = U(crouch, hips(0, 0.1, -0.7), torso(0, 44, 0, 0, 18, 0, 0, 14, 0))
    rise = U(RELAX, LEGS_WIDE, torso(0, 4, 0, 0, 2, 0, 0, 0, 0), look(0, -6), grip("R", 50, 0.34, 1.2, 40, 60), fist("L", 40, 0.28, 1.04, 0, 20))
    sh = ro_shoulder()
    out.append(anim("cs_ro_land", 60, [(0, impact), (4, crouch, "out"), (14, crouch), (34, rise, "out"), (46, sh), (60, sh)],
                    props="gs", layers=[breath(20, 1.6)]))
    out.append(anim("cs_ro_shoulder", 72, [(0, sh), (36, U(sh, look(6, -8)))], loop=True, props="gs", layers=[breath(36, 1.3), sway(72, 0.5)]))
    # slam: both hands raise the hammer high overhead, then drive it into the ground in front
    raise_ = U(RELAX, body(LEGS_WIDE, yaw=0, pitch=-18, drop=0.04), grip("R", 20, 0.08, 1.9, 0, 130, 180), two_hand("L", -0.22),
               look(0, 18))
    slam = U(RELAX, body(LEGS_WIDE, yaw=0, pitch=40, drop=0.32, fwd=0.08), grip("R", 10, 0.52, 0.7, 0, 10, 180), two_hand("L", -0.24),
             look(0, -6), foot("L", 0.34, 0.17, 14, knee=12))
    out.append(anim("cs_ro_slam", 54, [(0, sh), (14, raise_, "out"), (22, U(raise_, body(LEGS_WIDE, yaw=0, pitch=-22, drop=0.0))),
                                       (27, slam, "in"), (40, slam), (54, U(slam, body(LEGS_WIDE, yaw=0, pitch=30, drop=0.28)))],
                    props="gs", hits=[(25, 28)], release=27, key=27))
    # brace: the last stand, the haft held across the body in both hands, pushing into the host
    br = U(RELAX, body(LEGS_LOW, yaw=-8, pitch=14, drop=0.18, fwd=0.04), grip("R", 50, 0.44, 1.12, 80, 10, 90),
           two_hand("L", 0.35, 0, pole=-10), look(8, -16))
    br2 = U(br, body(LEGS_LOW, yaw=-4, pitch=18, drop=0.2, fwd=0.06), grip("R", 50, 0.47, 1.1, 80, 8, 90))
    out.append(anim("cs_ro_brace", 40, [(0, br), (20, br2)], loop=True, props="gs", layers=[shake(0.9, 3.2), breath(20, 1.8)]))
    # fall: struck, down on one knee, leaning on the hammer planted head-down, head bowed
    fk = U(RELAX, LEGS_KNEEL_LOW, torso(0, 24, 4, 0, 14, 0, 0, 10, 0), look(0, 30, 6), grip("R", 40, 0.42, 1.0, 0, 12, 0),
           fist("L", 20, 0.34, 0.6, 0, -30))
    out.append(anim("cs_ro_fall", 50, [(0, br), (6, U(br, torso(0, -20, 0, 0, -10, 0, 0, -8, 0)), "out"), (22, fk, "in"), (50, fk)],
                    props="gs", layers=[_ramped(shake(1.0, 3.0), 20, 26, 40, 50)]))
    # stand: the hammer planted head-down in front, both hands on the end of the haft
    st = U(RELAX, feet(0.06, -0.06, 0.16, 0.16, 12, 16), hips(0, 0, -0.03), look(0, -4),
           grip("R", 5, 0.3, 1.28, 0, -88, 0), fist("L", -5, 0.3, 1.3, 0, -60))
    out.append(anim("cs_ro_stand", 72, [(0, st), (36, U(st, look(-4, -6)))], loop=True, props="gs",
                    layers=[breath(36, 1.2), sway(72, 0.5)]))
    return out


def ro_shoulder():
    # the hammer rests on the right shoulder, head behind him; the left fist on the hip
    return U(RELAX, feet(0.08, -0.08, 0.16, 0.17, 12, 18), hips(0, 0, -0.04), torso(-6, -4, 0, -2, -2, 0, 0, -2, 0),
             grip("R", 80, 0.2, 1.36, 160, 30, 90, pole=10), fist("L", 110, 0.24, 1.02, 0, -40), look(-8, -8))


# ============================================================================================================ Paul David
def paul():
    out = []
    idle = U(RELAX, feet(0.04, -0.04, 0.12, 0.13, 10, 14), fist("L", -150, 0.14, 1.0, 0, -40, w=1.0), fist("R", -150, 0.14, 1.0, 0, -40),
             torso(0, 2, 0, 0, 0, 0, 0, 0, 0), look(8, -4))
    out.append(anim("cs_pd_idle", 120, [(0, idle), (60, U(idle, look(14, -2), hips(0.01, 0, 0)))], loop=True,
                    layers=[breath(40, 1.0), sway(120, 0.8)]))
    shard = U(RELAX, feet(0.04, -0.04, 0.12, 0.13, 10, 14), torso(0, 10, 0, 0, 6, 0, 0, 6, 0), look(-6, 34),
              fist("L", 20, 0.3, 1.12, -20, 60), fist("R", 30, 0.26, 1.08, 30, 40))
    out.append(anim("cs_pd_shard", 60, [(0, shard), (30, U(shard, look(-4, 36)))], loop=True, layers=[breath(30, 1.0)]))
    # hand: raise the branded right hand, look at its back, close it slowly, lower it
    h1 = U(RELAX, feet(0.04, -0.04, 0.12, 0.13, 10, 14), look(-10, 14), fist("R", 10, 0.3, 1.46, -30, 80, 90),
           fist("L", -150, 0.14, 1.0, 0, -40))
    h2 = U(h1, fist("R", 5, 0.28, 1.44, -40, 80, 60), look(-12, 16), torso(0, 4, 0, 0, 2, 0, 0, 2, 0))
    h3 = U(h2, fist("R", 20, 0.26, 1.2, -10, 40, 90), look(-4, 20))
    out.append(anim("cs_pd_hand", 90, [(0, idle), (20, h1, "out"), (50, h2), (70, h3), (90, h3)], layers=[breath(30, 1.1)]))
    # gesture: explaining — an open sweep of the right hand, the left following
    g1 = U(RELAX, feet(0.04, -0.04, 0.12, 0.13, 10, 14), fist("R", 40, 0.44, 1.2, 30, 20, -60), fist("L", -150, 0.14, 1.0, 0, -40), look(4, 0))
    g2 = U(g1, fist("R", 70, 0.46, 1.24, 60, 20, -80), torso(-6, 0, 0, -4, 0, 0, -4, 0, 0), look(12, -2))
    g3 = U(g1, fist("R", 20, 0.4, 1.12, 10, 30, -40), fist("L", 40, 0.36, 1.1, -10, 30), look(-4, 2))
    out.append(anim("cs_pd_gesture", 90, [(0, g1), (24, g2), (48, g3), (72, U(g1, look(0, -2)))], loop=True, layers=[breath(45, 1.0)]))
    # branded: the brand burns — he grabs his right wrist and folds over it
    b1 = U(RELAX, body(LEGS_FIGHT, yaw=10, pitch=26, drop=0.14), fist("R", 10, 0.3, 1.08, 0, 20), fist("L", -10, 0.26, 1.06, 20, 10),
           look(-6, 20))
    out.append(anim("cs_pd_branded", 50, [(0, U(RELAX, LEGS_FIGHT)), (6, U(b1, torso(0, -14, 0, 0, -8, 0, 0, -6, 0)), "out"),
                                          (18, b1, "in"), (50, U(b1, body(LEGS_FIGHT, yaw=12, pitch=30, drop=0.16)))],
                    layers=[_ramped(shake(1.4, 2.6), 14, 20, 40, 50)]))
    # reach: lunge forward, the right hand stretched toward something being taken
    r1 = U(RELAX, body(LEGS_WIDE, yaw=0, pitch=18, drop=0.16, fwd=0.1), arm("R", 16, 88, 6, 0, -10), arm("L", -40, -40, 30),
           look(0, -20), foot("L", 0.42, 0.14, 12, knee=10))
    out.append(anim("cs_pd_reach", 40, [(0, U(RELAX, LEGS_FIGHT)), (14, r1, "out"), (40, U(r1, arm("R", 20, 90, 4)))]))
    # ready: Stormwake raised, point angled up at the host, the left hand open in guard
    rd = U(RELAX, body(LEGS_FIGHT, yaw=-14, pitch=4, drop=0.1), grip("R", 45, 0.3, 1.3, -10, 50, 0, pole=5),
           fist("L", -10, 0.3, 1.24, -15, 70), look(14, -6))
    out.append(anim("cs_pd_ready", 40, [(0, rd), (20, U(rd, body(LEGS_FIGHT, yaw=-16, pitch=5, drop=0.11)))], loop=True, props="sword",
                    layers=[breath(20, 1.3)]))
    return out


# ============================================================================================================ Kethrax
def kethrax():
    out = []
    low = U(RELAX, hips(0, 0.06, -0.58), foot("L", 0.24, 0.18, 14, knee=12), foot("R", -0.14, 0.18, 20, heel=30, knee=10),
            torso(0, 44, 0, 0, 16, 0, 0, 12, 0), look(0, 10), arm("L", -70, 40, 40), arm("R", -70, 40, 40))
    spread = U(RELAX, LEGS_WIDE, torso(0, -14, 0, 0, -8, 0, 0, -8, 0), look(0, -20), arm("L", 20, -10, 40, 0, -40),
               arm("R", 20, -10, 40, 0, -40), clav("L", 14, -10), clav("R", 14, -10))
    out.append(anim("cs_kx_emerge", 70, [(0, low), (10, low), (40, U(spread, look(0, -6)), "out"), (52, spread), (70, U(spread, look(0, -26)))],
                    layers=[breath(20, 1.4)]))
    # pull: hauling the chains in hand over hand, leaning back
    p1 = U(RELAX, body(LEGS_WIDE, yaw=0, pitch=-14, drop=0.16, fwd=-0.06), fist("L", 10, 0.44, 1.1, 0, 0), fist("R", -10, 0.3, 1.0, 0, 0),
           look(0, -6))
    p2 = U(RELAX, body(LEGS_WIDE, yaw=0, pitch=-20, drop=0.18, fwd=-0.08), fist("L", 10, 0.26, 1.0, 0, 0), fist("R", -10, 0.46, 1.12, 0, 0),
           look(0, -8))
    out.append(anim("cs_kx_pull", 40, [(0, p1), (20, p2), (40, p1)], loop=True, layers=[shake(0.6, 3.0)]))
    # bind: both arms whip forward to cast the chains, then yank back
    w = U(RELAX, body(LEGS_WIDE, yaw=0, pitch=-10, drop=0.1), fist("L", 60, 0.16, 1.5, 0, 90), fist("R", 60, 0.16, 1.5, 0, 90), look(0, -10))
    t = U(RELAX, body(LEGS_WIDE, yaw=0, pitch=24, drop=0.2, fwd=0.08), arm("L", 0, 90, 4), arm("R", 0, 90, 4), look(0, -18))
    out.append(anim("cs_kx_bind", 44, [(0, U(RELAX, LEGS_WIDE)), (10, w, "out"), (17, t, "in"), (26, t), (44, p2)], release=17, key=17))
    # kneel: beaten, down on one knee, a hand on the ground, the head lifting for his last words
    kd = U(RELAX, LEGS_KNEEL_LOW, torso(0, 34, 6, 0, 16, 0, 0, 12, 0), look(0, 24), fist("L", 30, 0.4, 0.34, 0, -80),
           arm("R", -70, 20, 30))
    kl = U(kd, torso(0, 20, 4, 0, 8, 0, 0, 4, 0), look(0, -10))
    out.append(anim("cs_kx_kneel", 80, [(0, U(RELAX, LEGS_WIDE)), (8, U(RELAX, body(LEGS_WIDE, pitch=-20, drop=0.1)), "out"),
                                        (24, kd, "in"), (50, kd), (70, kl), (80, kl)], layers=[breath(18, 2.0)]))
    return out


def build():
    return aljay() + roydo() + paul() + kethrax()
