"""Idles, class personality idles and weapon stance idles (all loops)."""
from lib_common import anim, breath, sway
from lib_poses import (U, RELAX, tw, torso, look, hips, clav, arm, grip, two_hand, foot, feet, STANCES,
                       ST_1H, ST_SHIELD, ST_2H, ST_SPEAR, ST_DAGGER, ST_BOW, ST_STAFF, ST_WAND, ST_DUAL, ST_HURT)


def stance_idle(name, base, props, length=72, amp=1.0, weapon_bob=0.012):
    """Combat stance loop: breathing, small bounce on the knees, weapon tip drifting."""
    k1 = U(base, {"hips.up": base.get("hips.up", 0) - 0.008})
    for s in "LR":
        if base.get(f"hik.{s}", 0) > 0.5:
            k1[f"hik.{s}.z"] = base[f"hik.{s}.z"] - weapon_bob
            k1[f"hik.{s}.pitch"] = base[f"hik.{s}.pitch"] - 3
    return anim(name, length, [(0, base), (length / 2, k1)], loop=True, props=props,
                lag={"hik": 3, "chest": 1, "head": 2}, layers=[breath(length / 2, 0.9 * amp)])


def build():
    out = []
    # ---- idle: relaxed breathing with a slow weight shift ----------------------------------------------------
    base = U(RELAX)
    shift = U(RELAX, hips(0.012, 0, -0.016), torso(0, 0, 1.2, 0, 0, -0.6, 0, 0, -0.5),
              foot("R", 0.0, 0.12, 8, knee=6))
    out.append(anim("idle", 120, [(0, base), (60, shift)], loop=True,
                    layers=[breath(40, 1.0)], lag={"head": 3, "arm": 4}))

    # ---- idle_look: glance left, back, look right over the shoulder ------------------------------------------
    L1 = U(RELAX, look(55, 4, 3), torso(8, 0, 0, 6, 0, 0, 10, 0, 0), hips(-0.006, 0, -0.014))
    L2 = U(RELAX, look(-60, -6, -2), torso(-8, 0, 0, -6, 0, 0, -12, 0, 0), hips(0.008, 0, -0.016),
           foot("R", -0.02, 0.13, 14))
    L3 = U(RELAX, look(-8, 12, 0))
    out.append(anim("idle_look", 120, [(0, RELAX), (10, RELAX), (22, L1), (46, L1), (58, RELAX), (68, L2),
                                       (90, L2), (102, L3), (112, RELAX)], loop=True,
                    layers=[breath(40, 0.9)], lag={"chest": 2, "spine": 1}))

    # ---- idle_adjust: tug the left gauntlet, then straighten the belt ----------------------------------------
    A1 = U(RELAX, grip("L", 10, 0.24, 1.14, -30, 10, 0, pole=5), grip("R", -30, 0.30, 1.16, -60, 10, 0, pole=5),
           look(-6, 22), torso(-4, 6, 0, 0, 4, 0, 0, 4, 0))
    A2 = U(A1, grip("R", -22, 0.26, 1.13, -60, 5, 0, pole=5), grip("L", 18, 0.30, 1.16, -25, 20, 0, pole=5))
    A3 = U(RELAX, grip("L", 60, 0.20, 1.0, -70, -10, 0, pole=0), grip("R", 60, 0.20, 1.0, -70, -10, 0, pole=0),
           look(0, 25), torso(0, 8, 0, 0, 6, 0, 0, 4, 0), hips(0, 0, -0.02))
    A4 = U(A3, hips(0, 0, -0.005), torso(0, 3, 0, 0, 2, 0, 0, -3, 0), look(0, 10))
    out.append(anim("idle_adjust", 120, [(0, RELAX), (8, RELAX), (20, A1), (28, A2), (34, A1), (40, A2), (50, A1),
                                         (62, RELAX), (72, A3), (82, A4), (88, A3), (98, A4), (110, RELAX)],
                    loop=True, layers=[breath(40, 0.8)], lag={"head": 2}))

    # ---- idle_knight: plant the sword, rest both hands on the pommel, roll the shoulders ---------------------
    carry = U(RELAX, grip("R", 50, 0.24, 1.0, 5, -20, 0, pole=0))
    lift = U(RELAX, grip("R", 20, 0.36, 1.18, -2, -70, 0, pole=5), look(0, 12), hips(0, 0, -0.03),
             torso(0, 6, 0, 0, 4, 0, 0, 2, 0))
    plant = U(RELAX, grip("R", 0, 0.36, 0.93, 0, -86, 0, pole=5), two_hand("L", -0.1, 0, pole=5),
              look(0, 6), hips(0, 0, -0.035), torso(0, 5, 0, 0, 3, 0, 0, 3, 0),
              feet(0.0, 0.0, 0.16, 0.16, 12, 12))
    press = U(plant, hips(0, 0.01, -0.05), torso(0, 8, 0, 0, 5, 0, 0, 5, 0), look(0, 14))
    rollA = U(plant, clav("L", 12, 6), clav("R", 12, 6), look(0, -8), torso(0, 3, 0, 0, 1, 0, 0, -3, 0))
    rollB = U(plant, clav("L", 4, -10), clav("R", 4, -10), look(0, -12, 0), torso(0, 2, 0, 0, 0, 0, 0, -5, 0))
    rollC = U(plant, clav("L", -6, 4), clav("R", -6, 4), look(18, 4, 8))
    rollD = U(plant, look(-18, 4, -8))
    out.append(anim("idle_knight", 150, [(0, carry), (10, carry), (22, lift), (32, plant, "out"), (36, press),
                                         (44, plant), (56, rollA), (64, rollB), (72, rollC), (84, rollD), (96, plant),
                                         (106, press), (118, plant), (128, lift), (140, carry)],
                    loop=True, props=("sword", None), layers=[breath(50, 1.0)], lag={"head": 2, "clav": 1}))

    # ---- idle_mage: conjure an orb in the left palm, turn it, let it fade ------------------------------------
    rest = U(RELAX, grip("R", 62, 0.26, 1.12, 8, 84, 0, pole=5))
    raise_ = U(rest, grip("L", 5, 0.32, 1.18, -30, 5, 0, pole=15), look(-8, 16), hips(0, 0, -0.02))
    cup = U(rest, grip("L", 0, 0.36, 1.24, -40, 10, 0, pole=15), look(-6, 18))
    turn1 = U(cup, grip("L", -8, 0.36, 1.28, -55, 15, 0, pole=20), look(-10, 16, 4))
    turn2 = U(cup, grip("L", 8, 0.38, 1.24, -20, 5, 0, pole=10), look(-2, 20, -4))
    fade = U(cup, grip("L", 10, 0.42, 1.32, -30, 25, 0, pole=10), look(-4, 8), torso(0, -3, 0, 0, -2, 0, 0, -3, 0))
    out.append(anim("idle_mage", 150, [(0, rest), (12, rest), (26, raise_), (36, cup), (52, turn1), (68, turn2),
                                       (84, turn1), (98, cup), (112, fade, "out"), (126, rest)],
                    loop=True, props=("staff", None), layers=[breath(50, 1.0)], lag={"head": 3, "chest": 1}))

    # ---- idle_ranger (one-shot fidget, 3.5 s): shade the eyes and scan the horizon, then reach over the right
    # shoulder, draw an arrow halfway from the quiver and slide it back. Bow carried low in the left hand. -------
    def fist(s_, az, r, z, yaw, pitch, roll=0.0, pole=0.0):
        return grip(s_, az, r, z, yaw, pitch, roll, pole, free=1.0)
    bow_low = grip("L", 42, 0.2, 0.97, 12, 74, 0, pole=5)
    carry = U(RELAX, bow_low)
    shade = U(carry, fist("R", -16, 0.17, 1.765, -80, -12, 0, pole=30), look(0, -10), clav("R", 6, 4),
              torso(0, -2, 0, 0, -2, 0, 0, -3, 0), hips(0, 0, -0.016))
    scanL = U(shade, look(34, -9, 3), torso(8, -2, 0, 6, -2, 0, 10, -3, 0), hips(-0.006, 0, -0.018),
              foot("R", -0.01, 0.13, 12))
    scanR = U(shade, look(-36, -8, -3), torso(-8, -2, 0, -6, -2, 0, -10, -3, 0), hips(0.008, 0, -0.018),
              foot("L", 0.01, 0.13, 12))
    reach = U(carry, fist("R", 128, 0.17, 1.6, 30, 62, 0, pole=60), clav("R", 14, -8), look(-28, 4, -6),
              torso(-6, 2, 0, -4, 2, 0, -8, 2, -4), hips(0.004, 0, -0.02))
    draw = U(reach, fist("R", 132, 0.17, 1.72, 30, 66, 0, pole=62), clav("R", 18, -10), look(-32, -2, -6))
    out.append(anim("idle_ranger", 105, [(0, RELAX), (8, carry), (18, shade, "out"), (26, shade), (40, scanL),
                                         (48, scanL), (62, scanR), (68, shade), (74, carry), (82, reach, "out"),
                                         (88, draw, "out"), (93, draw), (97, reach, "in"), (105, RELAX)],
                    loop=False, props=(None, "bow"), layers=[breath(35, 0.9)], lag={"head": 2, "chest": 1}))

    # ---- idle_shadowblade (one-shot fidget, 3.5 s): toss the dagger end over end and catch it, flip it to a
    # reverse grip, roll the neck and shoulders, sink into a low ready crouch, then rise and flip it back. ------
    held = U(RELAX, fist("R", 22, 0.3, 1.14, 0, 28, 0, pole=5))
    toss = U(held, fist("R", 24, 0.32, 1.24, 0, 40, 0, pole=5), look(4, 6), hips(0, 0, -0.01))
    catch = U(held, fist("R", 22, 0.3, 1.11, 0, 24, 0, pole=5), look(2, 10), hips(0, 0, -0.02))
    rev = U(held, fist("R", 30, 0.28, 1.12, 0, 20, 0, pole=10))
    rollA = U(rev, look(28, 8, 18), clav("L", 10, 4), clav("R", -4, 4))
    rollB = U(rev, look(0, -14, 0), clav("L", 14, -6), clav("R", 14, -6), torso(0, -2, 0, 0, -2, 0, 0, -4, 0))
    rollC = U(rev, look(-28, 8, -18), clav("R", 12, 4), clav("L", -4, 4))
    low = U(rev, hips(-0.01, 0.02, -0.11), feet(0.12, -0.14, 0.15, 0.16, 16, 28, 10, 12),
            torso(-12, 12, 0, -2, 8, 0, 4, 6, 0), look(10, -10), fist("R", 36, 0.34, 1.02, 10, 12, 0, pole=12),
            fist("L", -4, 0.3, 1.14, -15, 60, 0, pole=10))
    rise = U(held, fist("R", 24, 0.3, 1.16, 0, 30, 0, pole=5))
    spin = [(0, 0.0), (21, 0.0), (35, 720.0), (44, 720.0), (50, 900.0), (84, 900.0), (90, 1080.0), (105, 1080.0)]

    def dagger_spin(f, c, spin=spin):
        # dagger turns end over end about the knuckle axis of the weapon socket (piecewise linear, whole turns)
        for (a, va), (b, vb) in zip(spin, spin[1:]):
            if a <= f <= b:
                c["wpn.R.x"] += va + (vb - va) * (f - a) / (b - a)
                return
    out.append(anim("idle_shadowblade", 105,
                    [(0, RELAX), (10, held), (18, held), (21, toss, "out"), (29, toss), (35, catch, "in"),
                     (40, held), (44, held), (50, rev, "out"), (58, rollA), (66, rollB), (74, rollC), (80, rev),
                     (86, low, "out"), (92, low), (98, rise), (105, RELAX)],
                    loop=False, props=("dagger", None), layers=[breath(35, 0.9), dagger_spin],
                    lag={"head": 2, "clav": 1}))

    # ---- idle_hurt: hunched, hand on the ribs, heavy breathing -----------------------------------------------
    H0 = U(RELAX, hips(0.01, -0.01, -0.07), torso(-6, 16, 8, -2, 12, 5, 4, 10, 4),
           grip("L", -70, 0.10, 1.22, -60, 30, 0, pole=15), arm("R", -72, 14, 30, 0, 10),
           feet(0.05, -0.05, 0.14, 0.14, 12, 18, 8, 10), look(6, 10, -6))
    H1 = U(H0, torso(-4, 20, 9, -2, 14, 6, 4, 12, 5), hips(0.012, -0.01, -0.08), look(4, 14, -8))
    out.append(anim("idle_hurt", 60, [(0, H0), (30, H1)], loop=True, layers=[breath(20, 2.0, hurt=True)],
                    lag={"head": 2, "arm": 2}))

    # ---- stance idles ----------------------------------------------------------------------------------------
    out.append(stance_idle("idle_1h", ST_1H, "sword"))
    out.append(stance_idle("idle_shield", ST_SHIELD, "shield"))
    out.append(stance_idle("idle_2h", ST_2H, "gs", length=80))
    out.append(stance_idle("idle_spear", ST_SPEAR, "spear", length=80))
    out.append(stance_idle("idle_dagger", ST_DAGGER, "dagger", length=60, amp=1.2))
    out.append(stance_idle("idle_bow", ST_BOW, "bow", length=90))
    out.append(stance_idle("idle_staff", ST_STAFF, "staff", length=90))
    out.append(stance_idle("idle_wand", ST_WAND, "wand", length=80))
    out.append(stance_idle("idle_dual", ST_DUAL, "dual", length=70))
    hurt = stance_idle("idle_combat_hurt", ST_HURT, "sword", length=60, amp=1.6)
    hurt.layers.append(breath(20, 1.4, hurt=True))
    out.append(hurt)
    return out
