"""Weapon attack chains (4 per weapon, each ending near where the next begins), heavies, bow shots.

Every attack is keyed as: stance -> anticipation (windup) -> strike start (hit window opens) -> strike end
(window closes) -> follow-through (overshoot) -> recovery. Authored hit windows are refined in bh_library by the
measured weapon-tip speed, so the JSON windows match the visible sweep.
"""
from lib_common import anim
from lib_poses import (spin_legs, U, RELAX, tw, torso, look, hips, clav, arm, grip, fist, two_hand, foot, feet, leg_fk, mirror,
                       LEGS_FIGHT, LEGS_WIDE, LEGS_LOW, L_GUARD, ST_1H, ST_2H, ST_SPEAR, ST_DAGGER, ST_DUAL,
                       ST_STAFF, ST_WAND, ST_BOW, STANCES)

# weapon tip distance along the socket axis (m), used to measure sweeps
TIP = {"sword": 0.85, "gs": 1.28, "axe": 0.55, "spear": 1.25, "dagger": 0.3, "dual": 0.85, "staff": 0.75,
       "wand": 0.22, "bow": 0.6, "shield": 0.3, "none": 0.1}

EASE_STRIKE = "linear"


def body(legs=LEGS_FIGHT, yaw=0.0, pitch=0.0, roll=0.0, drop=0.0, fwd=0.0, side=0.0, split=(0.35, 0.3, 0.35),
         head=(0.0, 0.0), spin=0.0, lift=(0.0, 0.0), heel=(0.0, 0.0)):
    """Leg stance + additional torso twist/bend (distributed) + hips offsets; head counter-rotates to keep the
    gaze on the target (head=(yaw, pitch) extra)."""
    out = dict(legs) if not spin and not any(lift) else spin_legs(legs, spin, lift[0], lift[1], heel[0], heel[1])
    for b, k in zip(("hips", "spine", "chest"), split):
        out[b + ".yaw"] = out.get(b + ".yaw", 0.0) + yaw * k
        out[b + ".pitch"] = out.get(b + ".pitch", 0.0) + pitch * k
        out[b + ".roll"] = out.get(b + ".roll", 0.0) + roll * k
    out["hips.up"] = out.get("hips.up", 0.0) - drop
    out["hips.fwd"] = out.get("hips.fwd", 0.0) + fwd
    out["hips.side"] = out.get("hips.side", 0.0) + side
    tot = sum(out.get(b + ".yaw", 0.0) for b in ("hips", "spine", "chest")) - spin
    out.update(look(-tot * 0.75 + head[0], -pitch * 0.6 - 4 + head[1]))
    return out


def attack(name, family, length, keys, hits=(), release=None, cancel=None, combo=None, lag=None, **meta):
    lag = dict({"head": 1.0, "neck": 0.5}, **(lag or {}))
    m = dict(meta)
    if hits:
        m["hits"] = [tuple(h) for h in hits]
    if release is not None:
        m["release"] = release
    if cancel is not None:
        m["cancel_after"] = cancel
    if combo is not None:
        m["combo_window"] = combo
    m["tip"] = TIP.get(family, 0.8)
    return anim(name, length, keys, props=family, lag=lag, **m)


def chain_meta(length, strike_end, extra=6):
    """cancel_after / combo_window defaults for a chain attack (frames)."""
    cancel = min(strike_end + 5, length - 2)
    return dict(cancel=cancel, combo=(strike_end + 1, length + extra))


# =================================================================================================================
# SWORD (one-handed). Left hand: guard / shield in front of the chest.
LG = L_GUARD


def sword_chain():
    out = []
    S0 = ST_1H
    # --- sword_1: forehand diagonal cut, high right -> low left --------------------------------------------------
    w = U(body(yaw=-24, pitch=-4, drop=0.02, side=-0.02), grip("R", 75, 0.18, 1.56, 70, 48, 0, pole=20), LG)
    a = U(body(yaw=-6, pitch=2, drop=0.04, fwd=0.02), grip("R", 35, 0.42, 1.46, 25, 22, 0), LG)
    b = U(body(yaw=16, pitch=8, drop=0.07, fwd=0.05, side=0.01), grip("R", -30, 0.50, 1.08, -50, -22, 0), LG)
    ft = U(body(yaw=26, pitch=10, drop=0.08, fwd=0.05), grip("R", -58, 0.40, 0.94, -85, -34, 0), LG)
    e = U(body(yaw=18, pitch=5, drop=0.06, fwd=0.02), grip("R", -46, 0.34, 1.02, -65, -12, 0), LG)
    out.append(attack("sword_1", "sword", 17, [(0, S0), (5, w, "out"), (8, a, "in"), (10, b, EASE_STRIKE),
                                              (13, ft, "out"), (17, e)],
                      hits=[(7.5, 10.5)], **chain_meta(17, 10)))
    E1 = e
    # --- sword_2: backhand rising cut, low left -> high right ----------------------------------------------------
    w = U(body(yaw=32, pitch=10, drop=0.08, side=0.01), grip("R", -66, 0.30, 0.96, -110, -18, 0, pole=-10), LG)
    a = U(body(yaw=16, pitch=6, drop=0.07, fwd=0.02), grip("R", -25, 0.46, 1.1, -45, 4, 0), LG)
    b = U(body(yaw=-14, pitch=-2, drop=0.04, fwd=0.03), grip("R", 45, 0.46, 1.42, 50, 36, 0), LG)
    ft = U(body(yaw=-24, pitch=-4, drop=0.03), grip("R", 70, 0.30, 1.56, 80, 52, 0), LG)
    e = U(body(yaw=-18, pitch=-2, drop=0.03), grip("R", 62, 0.28, 1.46, 60, 42, 0), LG)
    out.append(attack("sword_2", "sword", 17, [(0, E1), (4, w, "out"), (7, a, "in"), (9, b, EASE_STRIKE),
                                              (12, ft, "out"), (17, e)],
                      hits=[(6.5, 9.5)], **chain_meta(17, 9)))
    E2 = e
    # --- sword_3: flat horizontal forehand, right -> left ---------------------------------------------------------
    w = U(body(yaw=-36, pitch=0, drop=0.05, side=-0.02), grip("R", 88, 0.30, 1.3, 118, 6, 0), LG)
    a = U(body(yaw=-14, pitch=3, drop=0.06, fwd=0.02), grip("R", 40, 0.46, 1.26, 50, 2, 0), LG)
    b = U(body(yaw=18, pitch=5, drop=0.07, fwd=0.04, side=0.01), grip("R", -32, 0.50, 1.22, -48, -2, 0), LG)
    ft = U(body(yaw=34, pitch=5, drop=0.07, fwd=0.03), grip("R", -76, 0.36, 1.18, -112, 0, 0), LG)
    e = U(body(yaw=24, pitch=3, drop=0.05), grip("R", -50, 0.30, 1.22, -80, 22, 0), LG)
    out.append(attack("sword_3", "sword", 18, [(0, E2), (5, w, "out"), (8, a, "in"), (10, b, EASE_STRIKE),
                                              (13, ft, "out"), (18, e)],
                      hits=[(7.5, 10.5)], **chain_meta(18, 10)))
    E3 = e
    # --- sword_4: finisher, step in with a two-beat overhead cleave ---------------------------------------------
    up = U(body(yaw=-8, pitch=-12, drop=-0.01, side=-0.02), grip("R", 25, 0.10, 1.78, 0, 118, 0, pole=15),
           LG, foot("L", 0.2, 0.13, 12, up=0.07, knee=6))
    a = U(body(yaw=-4, pitch=0, drop=0.04, fwd=0.03), grip("R", 8, 0.30, 1.66, 0, 62, 0),
          LG, foot("L", 0.3, 0.13, 12, knee=8))
    b = U(body(yaw=4, pitch=24, drop=0.17, fwd=0.07), grip("R", 2, 0.54, 1.0, 0, -34, 0),
          LG, foot("L", 0.3, 0.13, 12, knee=8))
    ft = U(body(yaw=6, pitch=28, drop=0.19, fwd=0.07), grip("R", -4, 0.50, 0.84, -4, -52, 0),
           LG, foot("L", 0.3, 0.13, 12, knee=8))
    hold = U(ft, body(yaw=6, pitch=24, drop=0.17, fwd=0.06), foot("L", 0.3, 0.13, 12, knee=8))
    back = U(body(yaw=0, pitch=8, drop=0.09, fwd=0.02), grip("R", 20, 0.40, 1.02, 0, 0, 0), LG,
             foot("L", 0.2, 0.13, 12, up=0.04, knee=6))
    out.append(attack("sword_4", "sword", 27, [(0, E3), (8, up, "out"), (12, a, "in"), (14, b, EASE_STRIKE),
                                              (17, ft, "out"), (21, hold), (24, back), (27, S0)],
                      hits=[(11.5, 14.5)], cancel=22, combo=(15, 30), footsteps=[12]))
    # --- sword_heavy: coiled wide cleave (right -> left), big anticipation ----------------------------------------
    coil = U(body(LEGS_WIDE, yaw=-50, pitch=4, drop=0.08, side=-0.04), grip("R", 110, 0.26, 1.34, 150, 20, 0),
             grip("L", 60, 0.2, 1.3, 40, 40, 0, free=1.0), foot("R", -0.2, 0.17, 38, heel=12))
    coil2 = U(coil, body(LEGS_WIDE, yaw=-56, pitch=6, drop=0.1, side=-0.05), grip("R", 118, 0.26, 1.32, 158, 22, 0))
    a = U(body(LEGS_WIDE, yaw=-22, pitch=6, drop=0.1, fwd=0.03), grip("R", 55, 0.5, 1.28, 65, 4, 0), LG)
    b = U(body(LEGS_WIDE, yaw=26, pitch=8, drop=0.12, fwd=0.06, side=0.03), grip("R", -45, 0.54, 1.2, -60, -4, 0),
          grip("L", 30, 0.2, 1.2, 40, 20, 0, free=1.0))
    ft = U(body(LEGS_WIDE, yaw=46, pitch=8, drop=0.12, fwd=0.05), grip("R", -95, 0.4, 1.12, -130, -8, 0),
           grip("L", 50, 0.2, 1.1, 40, 20, 0, free=1.0))
    rec = U(body(LEGS_WIDE, yaw=30, pitch=4, drop=0.08), grip("R", -60, 0.34, 1.14, -80, 10, 0), LG)
    out.append(attack("sword_heavy", "sword", 34, [(0, S0), (9, coil, "out"), (14, coil2), (17, a, "in"),
                                                  (20, b, EASE_STRIKE), (24, ft, "out"), (28, rec), (34, S0)],
                      hits=[(16.5, 21)], cancel=28, combo=(22, 36)))
    return out


# =================================================================================================================
# GREATSWORD (two-handed; left hand on the grip below the right)
TH = two_hand("L", -0.15)


def gs_chain():
    out = []
    S0 = ST_2H
    L = LEGS_WIDE
    # gs_1: diagonal cut high right -> low left
    w = U(body(L, yaw=-30, pitch=-6, drop=0.03, side=-0.03), grip("R", 50, 0.16, 1.62, 60, 60, 0, pole=10), TH)
    a = U(body(L, yaw=-10, pitch=2, drop=0.06, fwd=0.02), grip("R", 20, 0.36, 1.5, 20, 30, 0), TH)
    b = U(body(L, yaw=18, pitch=12, drop=0.11, fwd=0.06), grip("R", -20, 0.46, 1.0, -40, -28, 0), TH)
    ft = U(body(L, yaw=28, pitch=14, drop=0.12, fwd=0.06), grip("R", -40, 0.40, 0.9, -70, -40, 0), TH)
    e = U(body(L, yaw=20, pitch=8, drop=0.1, fwd=0.03), grip("R", -30, 0.36, 0.96, -55, -24, 0), TH)
    out.append(attack("gs_1", "gs", 21, [(0, S0), (7, w, "out"), (10, a, "in"), (13, b, EASE_STRIKE),
                                        (16, ft, "out"), (21, e)], hits=[(9.5, 13.5)], **chain_meta(21, 13)))
    # gs_2: rising backhand, low left -> high right
    w = U(body(L, yaw=36, pitch=12, drop=0.12), grip("R", -45, 0.32, 0.92, -100, -30, 0, pole=-10), TH)
    a = U(body(L, yaw=18, pitch=8, drop=0.1, fwd=0.03), grip("R", -15, 0.44, 1.05, -40, -2, 0), TH)
    b = U(body(L, yaw=-18, pitch=-2, drop=0.05, fwd=0.03), grip("R", 30, 0.42, 1.45, 45, 40, 0), TH)
    ft = U(body(L, yaw=-28, pitch=-6, drop=0.04), grip("R", 40, 0.26, 1.6, 70, 60, 0), TH)
    e = U(body(L, yaw=-22, pitch=-4, drop=0.05), grip("R", 38, 0.26, 1.52, 60, 52, 0), TH)
    out.append(attack("gs_2", "gs", 21, [(0, out[-1].keys[-1][1]), (6, w, "out"), (9, a, "in"), (12, b, EASE_STRIKE),
                                        (15, ft, "out"), (21, e)], hits=[(8.5, 12.5)], **chain_meta(21, 12)))
    # gs_3: wide horizontal sweep right -> left
    w = U(body(L, yaw=-44, pitch=2, drop=0.08, side=-0.03), grip("R", 70, 0.3, 1.28, 115, 8, 0), TH)
    a = U(body(L, yaw=-20, pitch=4, drop=0.1, fwd=0.02), grip("R", 30, 0.44, 1.24, 50, 2, 0), TH)
    b = U(body(L, yaw=24, pitch=6, drop=0.12, fwd=0.05), grip("R", -25, 0.46, 1.2, -50, -4, 0), TH)
    ft = U(body(L, yaw=42, pitch=6, drop=0.12, fwd=0.04), grip("R", -50, 0.36, 1.18, -110, -4, 0), TH)
    e = U(body(L, yaw=30, pitch=4, drop=0.1), grip("R", -35, 0.32, 1.2, -80, 16, 0), TH)
    out.append(attack("gs_3", "gs", 23, [(0, out[-1].keys[-1][1]), (7, w, "out"), (10, a, "in"), (13, b, EASE_STRIKE),
                                        (16, ft, "out"), (23, e)], hits=[(9.5, 13.5)], **chain_meta(23, 13)))
    # gs_4: finisher overhead slam with a step
    up = U(body(L, yaw=-6, pitch=-14, drop=0.0), grip("R", 10, 0.06, 1.8, 0, 122, 0, pole=10), TH,
           foot("L", 0.24, 0.16, 14, up=0.08, knee=8))
    a = U(body(L, yaw=-2, pitch=0, drop=0.06, fwd=0.03), grip("R", 4, 0.26, 1.7, 0, 64, 0), TH,
          foot("L", 0.32, 0.16, 14, knee=8))
    b = U(body(L, yaw=2, pitch=30, drop=0.22, fwd=0.08), grip("R", 0, 0.52, 0.92, 0, -40, 0), TH,
          foot("L", 0.32, 0.16, 14, knee=8))
    ft = U(body(L, yaw=2, pitch=32, drop=0.23, fwd=0.08), grip("R", 0, 0.5, 0.8, 0, -52, 0), TH,
           foot("L", 0.32, 0.16, 14, knee=8))
    back = U(body(L, yaw=0, pitch=10, drop=0.12, fwd=0.02), grip("R", 5, 0.38, 1.04, 0, 10, 0), TH,
             foot("L", 0.22, 0.16, 14, up=0.04, knee=8))
    out.append(attack("gs_4", "gs", 28, [(0, out[-1].keys[-1][1]), (9, up, "out"), (13, a, "in"), (15, b, EASE_STRIKE),
                                        (18, ft, "out"), (22, ft), (25, back), (28, S0)],
                      hits=[(12.5, 15.5)], cancel=23, combo=(16, 31), footsteps=[13]))
    # gs_heavy: full-body windup behind the back, leaping overhead crash (Judgment)
    coil = U(body(L, yaw=-30, pitch=-16, drop=0.12), grip("R", 60, -0.05, 1.7, 30, 150, 0, pole=15), TH)
    rise = U(body(L, yaw=-10, pitch=-18, drop=-0.08), grip("R", 20, 0.0, 1.9, 0, 130, 0, pole=10), TH,
             foot("L", 0.2, 0.16, 14, up=0.12, toe=-10), foot("R", -0.1, 0.17, 30, up=0.1, heel=20))
    a = U(body(L, yaw=0, pitch=0, drop=0.0, fwd=0.04), grip("R", 5, 0.25, 1.78, 0, 70, 0), TH,
          foot("L", 0.3, 0.16, 14, up=0.03), foot("R", -0.14, 0.17, 30, up=0.02))
    b = U(body(L, yaw=0, pitch=34, drop=0.3, fwd=0.1), grip("R", 0, 0.55, 0.8, 0, -45, 0), TH,
          foot("L", 0.34, 0.16, 14, knee=10), foot("R", -0.16, 0.17, 30, heel=25, knee=10))
    hold = U(b, body(L, yaw=0, pitch=36, drop=0.31, fwd=0.1), grip("R", 0, 0.52, 0.74, 0, -55, 0),
             foot("L", 0.34, 0.16, 14, knee=10), foot("R", -0.16, 0.17, 30, heel=25, knee=10))
    back = U(body(L, yaw=0, pitch=12, drop=0.14), grip("R", 5, 0.38, 1.02, 0, 5, 0), TH,
             foot("L", 0.24, 0.16, 14, up=0.03, knee=8))
    out.append(attack("gs_heavy", "gs", 40, [(0, S0), (10, coil, "out"), (15, coil), (19, rise, "out"), (22, a, "in"),
                                            (24, b, EASE_STRIKE), (29, hold), (34, back), (40, S0)],
                      hits=[(21.5, 24.5)], cancel=33, combo=(26, 42), footsteps=[24]))
    return out


# =================================================================================================================
# AXE (one-handed, chopping; left hand free for balance)
def axe_chain():
    out = []
    S0 = ST_1H
    LB = fist("L", 40, 0.26, 1.2, 0, 50, 0)
    # axe_1: forehand diagonal chop
    w = U(body(yaw=-28, pitch=-6, drop=0.02, side=-0.02), grip("R", 70, 0.12, 1.62, 60, 70, 0, pole=20), LB)
    a = U(body(yaw=-8, pitch=4, drop=0.05, fwd=0.02), grip("R", 30, 0.38, 1.46, 20, 30, 0), LG)
    b = U(body(yaw=14, pitch=12, drop=0.09, fwd=0.05), grip("R", -20, 0.5, 1.02, -30, -30, 0), LG)
    ft = U(body(yaw=20, pitch=14, drop=0.1, fwd=0.05), grip("R", -40, 0.44, 0.92, -55, -45, 0), LG)
    e = U(body(yaw=16, pitch=8, drop=0.07, fwd=0.02), grip("R", -35, 0.36, 1.0, -50, -20, 0), LG)
    out.append(attack("axe_1", "axe", 18, [(0, S0), (6, w, "out"), (9, a, "in"), (11, b, EASE_STRIKE),
                                          (14, ft, "out"), (18, e)], hits=[(8.5, 11.5)], **chain_meta(18, 11)))
    # axe_2: backhand horizontal hack, left -> right
    w = U(body(yaw=36, pitch=6, drop=0.07), grip("R", -80, 0.28, 1.2, -120, 0, 0, pole=-10), LB)
    a = U(body(yaw=16, pitch=6, drop=0.07, fwd=0.02), grip("R", -30, 0.46, 1.2, -50, 0, 0), LG)
    b = U(body(yaw=-20, pitch=2, drop=0.05, fwd=0.03), grip("R", 45, 0.46, 1.24, 55, 5, 0), LG)
    ft = U(body(yaw=-32, pitch=0, drop=0.05), grip("R", 80, 0.32, 1.28, 110, 10, 0), LB)
    e = U(body(yaw=-26, pitch=-2, drop=0.05), grip("R", 70, 0.26, 1.34, 90, 40, 0), LB)
    out.append(attack("axe_2", "axe", 18, [(0, out[-1].keys[-1][1]), (5, w, "out"), (8, a, "in"), (10, b, EASE_STRIKE),
                                          (13, ft, "out"), (18, e)], hits=[(7.5, 10.5)], **chain_meta(18, 10)))
    # axe_3: overhead vertical chop
    up = U(body(yaw=-6, pitch=-12, drop=0.01), grip("R", 30, 0.02, 1.78, 0, 125, 0, pole=15), LB)
    a = U(body(yaw=-2, pitch=0, drop=0.04, fwd=0.03), grip("R", 12, 0.3, 1.62, 0, 60, 0), LG)
    b = U(body(yaw=2, pitch=24, drop=0.14, fwd=0.06), grip("R", 6, 0.52, 0.98, 0, -40, 0), LG)
    ft = U(body(yaw=2, pitch=26, drop=0.15, fwd=0.06), grip("R", 4, 0.5, 0.86, 0, -55, 0), LG)
    e = U(body(yaw=0, pitch=12, drop=0.09, fwd=0.02), grip("R", 10, 0.42, 1.0, 0, -15, 0), LG)
    out.append(attack("axe_3", "axe", 19, [(0, out[-1].keys[-1][1]), (6, up, "out"), (9, a, "in"), (11, b, EASE_STRIKE),
                                          (14, ft, "out"), (19, e)], hits=[(8.5, 11.5)], **chain_meta(19, 11)))
    # axe_4: spinning chop finisher (full turn to the left, the axe cuts across the front twice)
    pre = U(body(yaw=-40, pitch=4, drop=0.06, side=-0.02), grip("R", 90, 0.28, 1.25, 120, 10, 0), LB)
    s1 = U(body(yaw=10, pitch=6, drop=0.08, fwd=0.03, spin=30), grip("R", 5, 0.52, 1.2, 0, 0, 0), LB)
    s2 = U(body(yaw=10, pitch=6, drop=0.09, spin=150, lift=(0.0, 0.07)), grip("R", 20, 0.52, 1.2, 20, 0, 0), LB)
    s3 = U(body(yaw=10, pitch=6, drop=0.09, spin=270, lift=(0.06, 0.0)), grip("R", 10, 0.54, 1.18, 10, 0, 0), LB)
    s4 = U(body(yaw=16, pitch=10, drop=0.11, fwd=0.05, spin=345), grip("R", -30, 0.52, 1.14, -50, -6, 0), LG)
    ft = U(body(yaw=24, pitch=10, drop=0.1, fwd=0.03, spin=360), grip("R", -70, 0.36, 1.1, -110, -6, 0), LB)
    end = U(S0, spin_legs(LEGS_FIGHT, 360))
    out.append(attack("axe_4", "axe", 27, [(0, out[-1].keys[-1][1]), (6, pre, "out"), (10, s1, "in"), (13, s2, "linear"),
                                          (16, s3, "linear"), (18, s4, "linear"), (21, ft, "out"), (27, end)],
                      hits=[(8.5, 11), (16.5, 19)], cancel=23, combo=(19, 30), footsteps=[14, 17]))
    # axe_heavy: two-handed overhead chop into the ground (Ground Fissure)
    TH1 = two_hand("L", -0.12)
    up = U(body(LEGS_WIDE, yaw=-6, pitch=-18, drop=0.04), grip("R", 10, -0.02, 1.84, 0, 135, 0, pole=15), TH1)
    a = U(body(LEGS_WIDE, yaw=-2, pitch=0, drop=0.06, fwd=0.03), grip("R", 6, 0.26, 1.72, 0, 70, 0), TH1)
    b = U(body(LEGS_WIDE, yaw=2, pitch=38, drop=0.26, fwd=0.08), grip("R", 0, 0.56, 0.72, 0, -60, 0), TH1)
    hold = U(b, body(LEGS_WIDE, yaw=2, pitch=40, drop=0.27, fwd=0.08), grip("R", 0, 0.55, 0.66, 0, -66, 0))
    back = U(body(LEGS_WIDE, yaw=0, pitch=10, drop=0.1), grip("R", 20, 0.36, 1.05, 0, 0, 0), LB)
    out.append(attack("axe_heavy", "axe", 36, [(0, S0), (12, up, "out"), (17, up), (20, a, "in"), (23, b, EASE_STRIKE),
                                              (28, hold), (32, back), (36, S0)],
                      hits=[(19.5, 23.5)], cancel=30, combo=(25, 38)))
    return out


# =================================================================================================================
# SPEAR (two-handed thrusts; right hand back on the grip, left hand forward on the shaft)
SPL = two_hand("L", 0.34, 0.0, pole=-10)


def spear_chain():
    out = []
    S0 = ST_SPEAR
    L = LEGS_WIDE

    def sp(az, r, z, yaw, pitch, roll=0.0):
        return grip("R", az, r, z, yaw, pitch, roll)
    # spear_1: quick straight thrust
    w = U(body(L, yaw=-22, pitch=-2, drop=0.1, side=-0.03), sp(70, 0.1, 1.08, -12, 4), SPL)
    a = U(body(L, yaw=-12, pitch=4, drop=0.1, fwd=0.02), sp(50, 0.26, 1.1, -8, 2), SPL)
    b = U(body(L, yaw=6, pitch=12, drop=0.13, fwd=0.08), sp(10, 0.56, 1.12, -2, 0), SPL)
    ft = U(body(L, yaw=8, pitch=13, drop=0.13, fwd=0.08), sp(6, 0.6, 1.12, -2, -1), SPL)
    e = U(body(L, yaw=-8, pitch=6, drop=0.11, fwd=0.02), sp(40, 0.3, 1.12, -8, 3), SPL)
    out.append(attack("spear_1", "spear", 15, [(0, S0), (4, w, "out"), (6, a, "in"), (8, b, EASE_STRIKE),
                                              (10, ft, "out"), (15, e)], hits=[(5.5, 8.5)], **chain_meta(15, 8)))
    # spear_2: high thrust (over a guard)
    w = U(body(L, yaw=-24, pitch=-6, drop=0.08), sp(75, 0.08, 1.3, -10, 12), SPL)
    a = U(body(L, yaw=-12, pitch=0, drop=0.09, fwd=0.02), sp(55, 0.24, 1.34, -8, 8), SPL)
    b = U(body(L, yaw=8, pitch=10, drop=0.12, fwd=0.08), sp(8, 0.58, 1.36, -2, 4), SPL)
    ft = U(body(L, yaw=10, pitch=11, drop=0.12, fwd=0.08), sp(4, 0.62, 1.36, -2, 3), SPL)
    e = U(body(L, yaw=-6, pitch=4, drop=0.1), sp(40, 0.3, 1.2, -8, 4), SPL)
    out.append(attack("spear_2", "spear", 16, [(0, out[-1].keys[-1][1]), (5, w, "out"), (7, a, "in"), (9, b, EASE_STRIKE),
                                              (11, ft, "out"), (16, e)], hits=[(6.5, 9.5)], **chain_meta(16, 9)))
    # spear_3: sweeping slash with the blade, right -> left
    w = U(body(L, yaw=-40, pitch=0, drop=0.1), sp(70, 0.2, 1.2, 70, 5, 0), SPL)
    a = U(body(L, yaw=-16, pitch=3, drop=0.11, fwd=0.02), sp(45, 0.3, 1.2, 35, 0, 0), SPL)
    b = U(body(L, yaw=26, pitch=6, drop=0.12, fwd=0.04), sp(-10, 0.34, 1.18, -45, -3, 0), SPL)
    ft = U(body(L, yaw=38, pitch=6, drop=0.12), sp(-25, 0.3, 1.16, -75, -3, 0), SPL)
    e = U(body(L, yaw=10, pitch=4, drop=0.11), sp(30, 0.24, 1.12, -20, 2, 0), SPL)
    out.append(attack("spear_3", "spear", 18, [(0, out[-1].keys[-1][1]), (5, w, "out"), (8, a, "in"), (10, b, EASE_STRIKE),
                                              (13, ft, "out"), (18, e)], hits=[(7.5, 10.5)], **chain_meta(18, 10)))
    # spear_4: lunging finisher thrust with a step
    w = U(body(L, yaw=-30, pitch=-4, drop=0.14, side=-0.04), sp(80, 0.04, 1.1, -14, 6), SPL)
    a = U(body(L, yaw=-14, pitch=6, drop=0.16, fwd=0.04), sp(55, 0.22, 1.1, -8, 2), SPL,
          foot("L", 0.3, 0.16, 14, up=0.05, knee=10))
    b = U(body(L, yaw=8, pitch=18, drop=0.24, fwd=0.14), sp(8, 0.6, 1.02, -2, -4), SPL,
          foot("L", 0.42, 0.16, 14, knee=10), foot("R", -0.2, 0.17, 30, heel=30))
    ft = U(body(L, yaw=10, pitch=20, drop=0.25, fwd=0.15), sp(4, 0.64, 1.0, -2, -5), SPL,
           foot("L", 0.42, 0.16, 14, knee=10), foot("R", -0.2, 0.17, 30, heel=30))
    back = U(body(L, yaw=-6, pitch=8, drop=0.14, fwd=0.04), sp(40, 0.26, 1.08, -8, 4), SPL,
             foot("L", 0.24, 0.16, 14, up=0.04))
    out.append(attack("spear_4", "spear", 26, [(0, out[-1].keys[-1][1]), (7, w, "out"), (10, a, "in"), (13, b, EASE_STRIKE),
                                              (16, ft, "out"), (20, ft), (23, back), (26, S0)],
                      hits=[(9.5, 13.5)], cancel=21, combo=(14, 29), footsteps=[12]))
    # spear_heavy: charged spinning sweep into a driving thrust
    coil = U(body(L, yaw=-45, pitch=-4, drop=0.16), sp(90, 0.02, 1.12, -20, 8), SPL)
    a = U(body(L, yaw=-20, pitch=6, drop=0.18, fwd=0.04), sp(60, 0.2, 1.1, -10, 3), SPL,
          foot("L", 0.34, 0.16, 14, up=0.05, knee=10))
    b = U(body(L, yaw=10, pitch=20, drop=0.26, fwd=0.14), sp(6, 0.62, 1.04, -2, -3), SPL,
          foot("L", 0.44, 0.16, 14, knee=10), foot("R", -0.2, 0.17, 30, heel=35))
    b2 = U(b, sp(4, 0.66, 1.04, -2, -3), body(L, yaw=12, pitch=21, drop=0.27, fwd=0.15))
    back = U(body(L, yaw=-6, pitch=8, drop=0.14, fwd=0.04), sp(40, 0.26, 1.08, -8, 4), SPL,
             foot("L", 0.26, 0.16, 14, up=0.04))
    out.append(attack("spear_heavy", "spear", 36, [(0, S0), (10, coil, "out"), (17, coil), (20, a, "in"),
                                                  (23, b, EASE_STRIKE), (27, b2), (31, back), (36, S0)],
                      hits=[(19.5, 24)], cancel=30, combo=(25, 38), footsteps=[21]))
    return out


# =================================================================================================================
# DAGGER (fast, low stance)
def dagger_chain():
    out = []
    S0 = ST_DAGGER
    L = LEGS_LOW
    LD = fist("L", 20, 0.28, 1.2, 0, 60, 0)
    # dagger_1: quick forehand slash
    w = U(body(L, yaw=-24, pitch=2, drop=0.0), grip("R", 70, 0.26, 1.28, 80, 20, 0), LD)
    a = U(body(L, yaw=-6, pitch=6, drop=0.02, fwd=0.02), grip("R", 30, 0.44, 1.2, 30, 5, 0), LD)
    b = U(body(L, yaw=18, pitch=8, drop=0.03, fwd=0.04), grip("R", -30, 0.46, 1.08, -40, -10, 0), LD)
    e = U(body(L, yaw=16, pitch=6, drop=0.02), grip("R", -40, 0.34, 1.06, -60, 5, 0), LD)
    out.append(attack("dagger_1", "dagger", 13, [(0, S0), (3, w, "out"), (5, a, "in"), (7, b, EASE_STRIKE),
                                                (13, e, "out")], hits=[(4.5, 7.5)], **chain_meta(13, 7)))
    # dagger_2: backhand slash
    w = U(body(L, yaw=26, pitch=6, drop=0.02), grip("R", -70, 0.3, 1.1, -100, 5, 0), LD)
    a = U(body(L, yaw=10, pitch=6, drop=0.02, fwd=0.02), grip("R", -25, 0.44, 1.14, -35, 5, 0), LD)
    b = U(body(L, yaw=-16, pitch=4, drop=0.02, fwd=0.03), grip("R", 40, 0.44, 1.22, 50, 10, 0), LD)
    e = U(body(L, yaw=-12, pitch=4, drop=0.01), grip("R", 45, 0.34, 1.16, 30, 10, 0), LD)
    out.append(attack("dagger_2", "dagger", 13, [(0, out[-1].keys[-1][1]), (3, w, "out"), (5, a, "in"),
                                                (7, b, EASE_STRIKE), (13, e, "out")],
                      hits=[(4.5, 7.5)], **chain_meta(13, 7)))
    # dagger_3: straight stab
    w = U(body(L, yaw=-20, pitch=0, drop=0.03, side=-0.02), grip("R", 70, 0.12, 1.14, -5, 5, 0), LD)
    a = U(body(L, yaw=-8, pitch=6, drop=0.04, fwd=0.03), grip("R", 40, 0.3, 1.14, -4, 2, 0), LD)
    b = U(body(L, yaw=12, pitch=14, drop=0.06, fwd=0.09), grip("R", 2, 0.6, 1.14, 0, -2, 0), LD)
    e = U(body(L, yaw=0, pitch=6, drop=0.03, fwd=0.02), grip("R", 25, 0.36, 1.08, 0, 8, 0), LD)
    out.append(attack("dagger_3", "dagger", 14, [(0, out[-1].keys[-1][1]), (4, w, "out"), (6, a, "in"),
                                                (8, b, EASE_STRIKE), (14, e, "out")],
                      hits=[(5.5, 8.5)], **chain_meta(14, 8)))
    # dagger_4: finisher double strike: spinning backhand + stab
    s1 = U(body(L, yaw=-30, pitch=4, drop=0.02), grip("R", 80, 0.28, 1.2, 100, 10, 0), LD)
    s2 = U(body(L, yaw=60, pitch=8, drop=0.04, fwd=0.02), grip("R", -40, 0.46, 1.18, -60, 0, 0), LD,
           foot("R", -0.1, 0.16, 50, heel=10))
    s3 = U(body(L, yaw=20, pitch=4, drop=0.02), grip("R", 60, 0.14, 1.22, -5, 8, 0), LD)
    s4 = U(body(L, yaw=12, pitch=16, drop=0.08, fwd=0.1), grip("R", 2, 0.6, 1.1, 0, -4, 0), LD,
           foot("L", 0.24, 0.16, 18, knee=12))
    e = U(body(L, yaw=4, pitch=10, drop=0.05, fwd=0.04), grip("R", 20, 0.4, 1.06, 0, 4, 0), LD,
          foot("L", 0.2, 0.16, 18, knee=12))
    out.append(attack("dagger_4", "dagger", 22, [(0, out[-1].keys[-1][1]), (3, s1, "out"), (5, U(s1, body(L, yaw=-10)), "in"),
                                                (8, s2, EASE_STRIKE), (11, s3, "out"), (14, s4, EASE_STRIKE),
                                                (18, e, "out"), (22, S0)],
                      hits=[(4.5, 8.5), (11.5, 14.5)], cancel=17, combo=(15, 25)))
    # dagger_heavy: dashing lunge stab (the game moves the capsule during the dash)
    crouch = U(body(L, yaw=-20, pitch=16, drop=0.12), grip("R", 70, 0.1, 1.05, -5, 5, 0),
               fist("L", 30, 0.3, 1.1, 0, 30, 0), foot("R", -0.2, 0.17, 30, heel=25))
    dash = U(body(L, yaw=0, pitch=28, drop=0.16, fwd=0.1), grip("R", 40, 0.22, 1.02, -4, 2, 0),
             arm("L", -30, -40, 20), foot("L", 0.38, 0.16, 14, knee=12), foot("R", -0.25, 0.17, 30, heel=40))
    stab = U(body(L, yaw=14, pitch=22, drop=0.14, fwd=0.14), grip("R", 2, 0.62, 1.08, 0, -4, 0),
             arm("L", -40, -60, 30), foot("L", 0.42, 0.16, 14, knee=12), foot("R", -0.25, 0.17, 30, heel=40))
    back = U(body(L, yaw=0, pitch=8, drop=0.06), grip("R", 25, 0.36, 1.06, 0, 8, 0), LD, foot("L", 0.2, 0.16, 18))
    out.append(attack("dagger_heavy", "dagger", 32, [(0, S0), (8, crouch, "out"), (12, crouch), (16, dash, "in"),
                                                    (19, stab, EASE_STRIKE), (23, stab), (28, back), (32, S0)],
                      hits=[(16.5, 20)], cancel=26, combo=(21, 34), footsteps=[16, 20]))
    return out


# =================================================================================================================
# DUAL (a sword in each hand): alternate forehands, cross cut, spinning double strike
def dual_chain():
    out = []
    S0 = ST_DUAL
    LR = grip("L", 30, 0.3, 1.14, 0, 34, 0)       # left blade ready
    RR = grip("R", 35, 0.3, 1.12, 5, 38, 0)
    # dual_1: right forehand diagonal
    w = U(body(yaw=-24, pitch=-4, drop=0.02), grip("R", 75, 0.18, 1.52, 70, 45, 0, pole=20), LR)
    a = U(body(yaw=-6, pitch=2, drop=0.04, fwd=0.02), grip("R", 35, 0.42, 1.42, 25, 20, 0), LR)
    b = U(body(yaw=16, pitch=8, drop=0.07, fwd=0.05), grip("R", -30, 0.48, 1.08, -50, -22, 0),
          grip("L", 40, 0.26, 1.2, 20, 40, 0))
    e = U(body(yaw=14, pitch=5, drop=0.05), grip("R", -40, 0.34, 1.04, -60, -8, 0), grip("L", 45, 0.26, 1.24, 30, 45, 0))
    out.append(attack("dual_1", "dual", 15, [(0, S0), (4, w, "out"), (7, a, "in"), (9, b, EASE_STRIKE),
                                            (15, e, "out")], hits=[(6.5, 9.5)], **chain_meta(15, 9)))
    # dual_2: left forehand diagonal (mirror of dual_1's strike, starting from dual_1's end)
    mw = U(body(yaw=24, pitch=-4, drop=0.02), grip("R", -40, 0.32, 1.06, -60, -6, 0),
           mirror(grip("R", 75, 0.18, 1.52, 70, 45, 0, pole=20)))
    ma = U(body(yaw=6, pitch=2, drop=0.04, fwd=0.02), grip("R", -20, 0.3, 1.1, -40, 5, 0),
           mirror(grip("R", 35, 0.42, 1.42, 25, 20, 0)))
    mb = U(body(yaw=-16, pitch=8, drop=0.07, fwd=0.05), grip("R", 20, 0.3, 1.14, 10, 25, 0),
           mirror(grip("R", -30, 0.48, 1.08, -50, -22, 0)))
    me = U(body(yaw=-12, pitch=5, drop=0.05), RR, mirror(grip("R", -40, 0.34, 1.04, -60, -8, 0)))
    out.append(attack("dual_2", "dual", 15, [(0, e), (4, mw, "out"), (7, ma, "in"), (9, mb, EASE_STRIKE),
                                            (15, me, "out")], hits=[(6.5, 9.5)], hand="L", **chain_meta(15, 9)))
    # dual_3: cross cut, both blades from high outside to low inside (X)
    w = U(body(yaw=0, pitch=-8, drop=0.02), grip("R", 70, 0.16, 1.58, 60, 50, 0, pole=20),
          grip("L", 70, 0.16, 1.58, 60, 50, 0, pole=20))
    a = U(body(yaw=0, pitch=2, drop=0.05, fwd=0.03), grip("R", 30, 0.42, 1.44, 25, 20, 0),
          grip("L", 30, 0.42, 1.44, 25, 20, 0))
    b = U(body(yaw=0, pitch=12, drop=0.1, fwd=0.06), grip("R", -25, 0.46, 1.06, -45, -24, 0),
          grip("L", -25, 0.46, 1.1, -45, -24, 0))
    ft = U(body(yaw=0, pitch=14, drop=0.11, fwd=0.06), grip("R", -40, 0.38, 0.98, -70, -30, 0),
           grip("L", -40, 0.38, 1.02, -70, -30, 0))
    e = U(body(yaw=0, pitch=8, drop=0.07), grip("R", -30, 0.34, 1.04, -50, -10, 0),
          grip("L", -30, 0.34, 1.08, -50, -10, 0))
    out.append(attack("dual_3", "dual", 18, [(0, me), (5, w, "out"), (8, a, "in"), (10, b, EASE_STRIKE),
                                            (13, ft, "out"), (18, e)], hits=[(7.5, 10.5)], **chain_meta(18, 10)))
    # dual_4: spinning double strike finisher (full turn right->left with both blades out)
    pre = U(body(yaw=-40, pitch=2, drop=0.06), grip("R", 90, 0.3, 1.26, 120, 8, 0), grip("L", -30, 0.3, 1.2, -60, 8, 0))
    s1 = U(body(yaw=10, pitch=6, drop=0.08, spin=40), grip("R", 0, 0.5, 1.22, -10, 0, 0),
           grip("L", 70, 0.46, 1.22, 100, 0, 0))
    s2 = U(body(yaw=10, pitch=6, drop=0.09, spin=180, lift=(0.0, 0.07)), grip("R", 10, 0.52, 1.2, 0, 0, 0),
           grip("L", 70, 0.46, 1.22, 100, 0, 0))
    s3 = U(body(yaw=16, pitch=10, drop=0.11, fwd=0.04, spin=330), grip("R", -20, 0.5, 1.16, -40, -6, 0),
           grip("L", 50, 0.46, 1.2, 80, 0, 0))
    s4 = U(body(yaw=20, pitch=8, drop=0.1, spin=355), grip("R", -40, 0.4, 1.12, -70, -6, 0),
           grip("L", 30, 0.4, 1.16, 40, 10, 0))
    end = U(S0, spin_legs(LEGS_FIGHT, 360))
    out.append(attack("dual_4", "dual", 26, [(0, e), (6, pre, "out"), (10, s1, "in"), (14, s2, "linear"),
                                            (18, s3, "linear"), (21, s4, "out"),
                                            (26, end)],
                      hits=[(9.5, 13), (14.5, 18.5)], cancel=22, combo=(19, 29), footsteps=[14, 18]))
    # dual_heavy: both blades raised, crashing double overhead
    up = U(body(yaw=0, pitch=-14, drop=0.0), grip("R", 30, 0.06, 1.78, 0, 120, 0, pole=15),
           grip("L", 30, 0.06, 1.78, 0, 120, 0, pole=15), foot("L", 0.2, 0.13, 12, up=0.07))
    a = U(body(yaw=0, pitch=2, drop=0.05, fwd=0.03), grip("R", 18, 0.3, 1.66, 0, 62, 0), grip("L", 18, 0.3, 1.66, 0, 62, 0),
          foot("L", 0.3, 0.13, 12))
    b = U(body(yaw=0, pitch=28, drop=0.2, fwd=0.08), grip("R", 12, 0.52, 0.96, 0, -38, 0), grip("L", 12, 0.52, 0.96, 0, -38, 0),
          foot("L", 0.3, 0.13, 12, knee=8))
    hold = U(b, body(yaw=0, pitch=30, drop=0.21, fwd=0.08))
    back = U(body(yaw=0, pitch=8, drop=0.08), grip("R", 30, 0.36, 1.08, 0, 20, 0), grip("L", 30, 0.36, 1.1, 0, 20, 0),
             foot("L", 0.2, 0.13, 12, up=0.04))
    out.append(attack("dual_heavy", "dual", 34, [(0, S0), (11, up, "out"), (15, up), (18, a, "in"), (20, b, EASE_STRIKE),
                                                (25, hold), (29, back), (34, S0)],
                      hits=[(17.5, 20.5)], cancel=28, combo=(22, 36), footsteps=[18]))
    return out


# =================================================================================================================
# STAFF (ranged: each swing launches a bolt at `release`; the staff head also sweeps a melee arc)
def staff_chain():
    out = []
    S0 = ST_STAFF
    L = LEGS_FIGHT
    SL = two_hand("L", -0.32, 0.0, pole=-10)
    # staff_1: forward thrust of the staff head
    w = U(body(L, yaw=-20, pitch=-4, drop=0.04), grip("R", 70, 0.16, 1.2, -10, 30, 0), SL)
    a = U(body(L, yaw=6, pitch=8, drop=0.06, fwd=0.05), grip("R", 20, 0.46, 1.28, -4, 22, 0), SL)
    e = U(body(L, yaw=0, pitch=4, drop=0.04), grip("R", 40, 0.34, 1.2, 0, 50, 0), SL)
    out.append(attack("staff_1", "staff", 16, [(0, S0), (5, w, "out"), (8, a, "in"), (16, e, "out")],
                      hits=[(5.5, 8.5)], release=8, **chain_meta(16, 8)))
    # staff_2: sweeping swing right -> left, bolt at mid-swing
    w = U(body(L, yaw=-36, pitch=0, drop=0.05), grip("R", 80, 0.24, 1.24, 80, 30, 0), SL)
    a = U(body(L, yaw=-10, pitch=4, drop=0.06, fwd=0.02), grip("R", 30, 0.42, 1.26, 20, 20, 0), SL)
    b = U(body(L, yaw=22, pitch=6, drop=0.07, fwd=0.03), grip("R", -20, 0.4, 1.22, -45, 20, 0), SL)
    e = U(body(L, yaw=14, pitch=4, drop=0.05), grip("R", -10, 0.34, 1.2, -30, 45, 0), SL)
    out.append(attack("staff_2", "staff", 17, [(0, out[-1].keys[-1][1]), (5, w, "out"), (8, a, "in"), (10, b, EASE_STRIKE),
                                              (17, e, "out")], hits=[(7.5, 10.5)], release=9, **chain_meta(17, 10)))
    # staff_3: overhead arc forward
    w = U(body(L, yaw=-8, pitch=-12, drop=0.02), grip("R", 40, 0.1, 1.62, 0, 110, 0), SL)
    a = U(body(L, yaw=0, pitch=4, drop=0.05, fwd=0.03), grip("R", 20, 0.36, 1.5, 0, 40, 0), SL)
    b = U(body(L, yaw=4, pitch=14, drop=0.09, fwd=0.06), grip("R", 12, 0.5, 1.2, 0, 0, 0), SL)
    e = U(body(L, yaw=0, pitch=6, drop=0.05), grip("R", 30, 0.38, 1.2, 0, 40, 0), SL)
    out.append(attack("staff_3", "staff", 18, [(0, out[-1].keys[-1][1]), (6, w, "out"), (9, a, "in"), (11, b, EASE_STRIKE),
                                              (18, e, "out")], hits=[(8.5, 11.5)], release=11, **chain_meta(18, 11)))
    # staff_4: raise and slam the staff butt into the ground (shockwave)
    up = U(body(L, yaw=0, pitch=-10, drop=-0.01), grip("R", 20, 0.3, 1.62, 0, 85, 0), two_hand("L", -0.18),
           foot("L", 0.18, 0.13, 12, up=0.05))
    b = U(body(L, yaw=0, pitch=16, drop=0.16, fwd=0.05), grip("R", 10, 0.42, 1.12, 0, 84, 0), two_hand("L", -0.18),
          foot("L", 0.24, 0.13, 12, knee=8))
    hold = U(b, body(L, yaw=0, pitch=18, drop=0.17, fwd=0.05))
    out.append(attack("staff_4", "staff", 26, [(0, out[-1].keys[-1][1]), (9, up, "out"), (13, up), (15, b, EASE_STRIKE),
                                              (20, hold), (26, S0)], hits=[(12.5, 15.5)], release=15, cancel=21,
                      combo=(16, 29), footsteps=[15]))
    # staff_heavy: gather above the head, then drive the staff forward (big bolt)
    up = U(body(L, yaw=-4, pitch=-14, drop=0.0), grip("R", 20, 0.14, 1.72, 0, 95, 0), fist("L", 0, 0.34, 1.56, 0, 80, 0))
    gather = U(up, body(L, yaw=-8, pitch=-16, drop=0.02), grip("R", 25, 0.12, 1.76, 0, 100, 0))
    a = U(body(L, yaw=8, pitch=10, drop=0.08, fwd=0.07), grip("R", 12, 0.52, 1.34, 0, 12, 0), SL,
          foot("L", 0.24, 0.13, 12, knee=8))
    hold = U(a, grip("R", 10, 0.55, 1.33, 0, 10, 0))
    out.append(attack("staff_heavy", "staff", 36, [(0, S0), (10, up, "out"), (20, gather), (24, a, "in"), (30, hold),
                                                  (36, S0)], hits=[(20.5, 24.5)], release=24, cancel=29,
                      combo=(26, 38), footsteps=[24]))
    return out


# =================================================================================================================
# WAND (ranged flicks; release at the end of the flick)
def wand_chain():
    out = []
    S0 = ST_WAND
    LH = fist("L", 10, 0.26, 1.2, -10, 60, 0)

    def wd(az, r, z, yaw, pitch, roll=0.0):
        return grip("R", az, r, z, yaw, pitch, roll)
    # wand_1: flick forward from the shoulder
    w = U(body(yaw=-18, pitch=-4, drop=0.03), wd(60, 0.2, 1.5, 30, 70), LH)
    a = U(body(yaw=4, pitch=6, drop=0.05, fwd=0.03), wd(15, 0.52, 1.36, 0, 5), LH)
    e = U(body(yaw=0, pitch=3, drop=0.04), wd(25, 0.4, 1.2, 0, 10), LH)
    out.append(attack("wand_1", "wand", 14, [(0, S0), (4, w, "out"), (7, a, "in"), (14, e, "out")],
                      hits=[(4.5, 7.5)], release=7, **chain_meta(14, 7)))
    # wand_2: backhand flick across
    w = U(body(yaw=24, pitch=2, drop=0.04), wd(-50, 0.3, 1.34, -80, 20, 0), LH)
    a = U(body(yaw=-6, pitch=4, drop=0.05, fwd=0.03), wd(25, 0.52, 1.3, 20, 0, 0), LH)
    e = U(body(yaw=-4, pitch=3, drop=0.04), wd(30, 0.4, 1.2, 10, 10), LH)
    out.append(attack("wand_2", "wand", 14, [(0, out[-1].keys[-1][1]), (4, w, "out"), (7, a, "in"), (14, e, "out")],
                      hits=[(4.5, 7.5)], release=7, **chain_meta(14, 7)))
    # wand_3: off-hand push + wand thrust (two beats; release on the thrust)
    push = U(body(yaw=10, pitch=4, drop=0.05, fwd=0.03), wd(40, 0.2, 1.3, 10, 40),
             fist("L", -5, 0.5, 1.34, 0, 80, 0))
    w = U(body(yaw=-16, pitch=0, drop=0.04), wd(60, 0.16, 1.4, 20, 50), fist("L", 20, 0.24, 1.26, 0, 60, 0))
    a = U(body(yaw=6, pitch=8, drop=0.06, fwd=0.04), wd(10, 0.56, 1.34, 0, 2), fist("L", 30, 0.2, 1.2, 0, 50, 0))
    e = U(body(yaw=0, pitch=3, drop=0.04), wd(25, 0.4, 1.2, 0, 10), LH)
    out.append(attack("wand_3", "wand", 17, [(0, out[-1].keys[-1][1]), (4, push, "out"), (8, w, "out"), (11, a, "in"),
                                            (17, e, "out")], hits=[(8.5, 11.5)], release=11, **chain_meta(17, 11)))
    # wand_4: finisher: trace a circle overhead then point both hands forward
    c1 = U(body(yaw=-10, pitch=-8, drop=0.02), wd(40, 0.2, 1.72, 0, 80), fist("L", 0, 0.3, 1.5, 0, 80, 0))
    c2 = U(body(yaw=10, pitch=-8, drop=0.02), wd(-10, 0.24, 1.7, -30, 70), fist("L", -10, 0.34, 1.46, 0, 80, 0))
    c3 = U(body(yaw=0, pitch=-4, drop=0.03), wd(20, 0.3, 1.6, 20, 60), fist("L", 0, 0.34, 1.4, 0, 70, 0))
    a = U(body(yaw=4, pitch=10, drop=0.08, fwd=0.06), wd(10, 0.56, 1.36, 0, 0), fist("L", 5, 0.52, 1.34, 0, 80, 0),
          foot("L", 0.2, 0.13, 12, knee=8))
    hold = U(a, wd(10, 0.58, 1.36, 0, 0))
    out.append(attack("wand_4", "wand", 25, [(0, out[-1].keys[-1][1]), (5, c1), (9, c2), (12, c3, "out"), (15, a, "in"),
                                            (19, hold), (25, S0)], hits=[(12.5, 15.5)], release=15, cancel=20,
                      combo=(16, 28)))
    # wand_heavy: draw a long rune, hold, then release a heavy bolt with both arms forward
    up = U(body(yaw=-16, pitch=-10, drop=0.03), wd(70, 0.1, 1.72, 30, 100), fist("L", -20, 0.3, 1.2, 0, 60, 0))
    sweep = U(body(yaw=14, pitch=0, drop=0.05), wd(-30, 0.44, 1.3, -40, 10), fist("L", -20, 0.3, 1.24, 0, 60, 0))
    back = U(body(yaw=-24, pitch=-4, drop=0.06), wd(80, 0.12, 1.42, 20, 50), fist("L", 10, 0.4, 1.3, 0, 80, 0))
    a = U(body(yaw=6, pitch=12, drop=0.09, fwd=0.07), wd(8, 0.58, 1.34, 0, 0), fist("L", 8, 0.54, 1.3, 0, 80, 0),
          foot("L", 0.22, 0.13, 12, knee=8))
    hold = U(a, wd(8, 0.6, 1.34, 0, 0))
    out.append(attack("wand_heavy", "wand", 36, [(0, S0), (8, up, "out"), (14, sweep), (20, back, "out"), (24, a, "in"),
                                                (30, hold), (36, S0)], hits=[(20.5, 24.5)], release=24, cancel=30,
                      combo=(26, 38)))
    return out


# =================================================================================================================
# BOW (bow in the left hand; right hand draws to the anchor at the jaw)
def bow_set():
    out = []
    S0 = ST_BOW
    # turned three-quarters: left shoulder toward the target
    Lb = U(feet(0.08, -0.1, 0.14, 0.15, 30, 50, 8, 10), hips(0, 0, -0.05))
    aim = U(Lb, torso(-38, 2, 0, -8, 1, 0, -10, 1, 0), look(55, -2))
    BOWARM = grip("L", -52, 0.58, 1.44, -52, 84, 0, pole=0, free=0.6)          # bow arm extended to the target
    NOCK = grip("R", -40, 0.34, 1.4, -60, 20, 0, pole=10, free=1.0)             # right hand on the string at the bow
    ANCHOR = grip("R", 10, 0.14, 1.52, -50, 10, 0, pole=35, free=1.0)           # full draw at the jaw
    reach = U(S0, grip("R", 70, 0.2, 1.3, 0, 60, 0, free=1.0), look(20, 0))     # reach back to the quiver
    pre = U(aim, BOWARM, NOCK)
    full = U(aim, BOWARM, ANCHOR, clav("R", 4, -8))
    rel = U(aim, BOWARM, grip("R", 45, 0.08, 1.56, -20, 10, 0, pole=40, free=1.0), clav("R", 2, -12),
            torso(-40, 0, 0, -8, 0, 0, -12, -2, 0))
    # bow_1: quick shot
    out.append(attack("bow_1", "bow", 16, [(0, S0), (3, U(pre, grip("R", 20, 0.3, 1.36, -30, 20, 0, free=1.0))),
                                          (5, pre), (9, full, "out"), (10, full), (11, rel, "out"), (16, U(aim, BOWARM, ANCHOR, grip("R", 40, 0.2, 1.4, 0, 30, 0, free=1.0)))],
                      release=10.5, cancel=13, combo=(11, 19)))
    # bow_2: second quick shot (nock from the quiver again)
    out.append(attack("bow_2", "bow", 16, [(0, out[-1].keys[-1][1]), (3, U(aim, BOWARM, grip("R", 70, 0.12, 1.34, 0, 60, 0, free=1.0))),
                                          (6, pre), (9, full, "out"), (10, full), (11, rel, "out"), (16, S0)],
                      release=10.5, cancel=13, combo=(11, 19)))
    # bow_draw_hold: full draw held (loop), slight strain tremble
    hold2 = U(full, grip("R", 12, 0.13, 1.52, -50, 10, 0, pole=35, free=1.0), torso(-39, 2.5, 0, -8, 1, 0, -10, 1.5, 0))
    out.append(attack("bow_draw_hold", "bow", 40, [(0, full), (20, hold2), (40, full)]))
    out[-1].loop = True
    # bow_release: loose and follow-through
    out.append(attack("bow_release", "bow", 15, [(0, full), (1, rel, "out"), (6, U(rel, clav("R", 0, -14))),
                                                (15, S0)], release=0.5, cancel=8))
    return out


def build():
    out = []
    out += sword_chain()
    out += gs_chain()
    out += axe_chain()
    out += spear_chain()
    out += dagger_chain()
    out += dual_chain()
    out += staff_chain()
    out += wand_chain()
    out += bow_set()
    return out
