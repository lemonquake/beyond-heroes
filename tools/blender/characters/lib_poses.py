"""Pose building blocks for the Beyond Heroes action library (semantic channels, see bh_anim docstring).

All helpers return partial channel dicts; combine with P(a, b, c, key=value) (later wins).
Right-handed conventions: main weapon in the right hand (weapon.R), shield/bow/off-hand in the left (weapon.L).
"""
import math

from bh_anim import P, mirror_pose, DEFAULTS


def U(*dicts, **kw):
    """Union of pose dicts (later wins) + keyword overrides with '_' -> '.'."""
    return P(*dicts, **kw)


# ---------------------------------------------------------------------------------------------------------------
# body
def tw(yaw=0.0, pitch=0.0, roll=0.0, w=(0.3, 0.3, 0.4)):
    """Distribute a torso twist/bend over hips, spine, chest."""
    out = {}
    for b, k in zip(("hips", "spine", "chest"), w):
        out[b + ".yaw"] = yaw * k
        out[b + ".pitch"] = pitch * k
        out[b + ".roll"] = roll * k
    return out


def torso(hy=0.0, hp=0.0, hr=0.0, sy=0.0, sp=0.0, sr=0.0, cy=0.0, cp=0.0, cr=0.0):
    return {"hips.yaw": hy, "hips.pitch": hp, "hips.roll": hr, "spine.yaw": sy, "spine.pitch": sp,
            "spine.roll": sr, "chest.yaw": cy, "chest.pitch": cp, "chest.roll": cr}


def look(yaw=0.0, pitch=0.0, roll=0.0):
    return {"neck.yaw": yaw * 0.4, "neck.pitch": pitch * 0.45, "neck.roll": roll * 0.4,
            "head.yaw": yaw * 0.6, "head.pitch": pitch * 0.55, "head.roll": roll * 0.6}


def hips(side=0.0, fwd=0.0, up=0.0):
    return {"hips.side": side, "hips.fwd": fwd, "hips.up": up}


def clav(s, raise_=0.0, fwd=0.0):
    return {f"clav.{s}.raise": raise_, f"clav.{s}.fwd": fwd}


def arm(s, el=-78.0, az=8.0, bend=14.0, tw_=0.0, flex=6.0, dev=0.0, ftw=0.0):
    """FK arm (disables hand IK)."""
    return {f"arm.{s}.el": el, f"arm.{s}.az": az, f"arm.{s}.tw": tw_, f"fore.{s}.bend": bend,
            f"fore.{s}.tw": ftw, f"hand.{s}.flex": flex, f"hand.{s}.dev": dev, f"hik.{s}": 0.0, f"armik.{s}": 0.0}


def grip(s, az, r, z, yaw, pitch, roll=0.0, pole=0.0, w=1.0, x=0.0, fwd=0.0, free=0.5):
    """Hand IK: weapon socket at polar (az, r, z) in chest space, blade direction yaw/pitch.
    roll: knuckle/edge rotation about the blade as an OFFSET from the natural grip (knuckles along the arm).
    free (0..1): how far (x 90 deg) the solver may rotate the grip about the blade to relieve the wrist."""
    return {f"hik.{s}": w, f"hik.{s}.az": az, f"hik.{s}.r": r, f"hik.{s}.z": z, f"hik.{s}.yaw": yaw,
            f"hik.{s}.pitch": pitch, f"hik.{s}.roll": roll, f"hik.{s}.pole": pole, f"hik.{s}.x": x,
            f"hik.{s}.fwd": fwd, f"hik.{s}.rollfree": free, f"armik.{s}": 0.0}


def fist(s, az, r, z, yaw, pitch, roll=0.0, pole=0.0, w=1.0):
    """Empty hand placed by IK with a fully free grip roll (natural wrist)."""
    return grip(s, az, r, z, yaw, pitch, roll, pole, w, free=1.0)


def two_hand(s="L", at=-0.13, rot=0.0, pole=0.0, w=1.0):
    """Hand `s` grips the other hand's weapon `at` meters along the weapon axis (negative = toward the pommel)."""
    return {f"armik.{s}": w, f"armik.{s}.grip": at, f"armik.{s}.rot": rot, f"armik.{s}.pole": pole,
            f"hik.{s}": 0.0}


def free_hand(s):
    return {f"hik.{s}": 0.0, f"armik.{s}": 0.0}


def foot(s, fwd=0.0, out=0.115, yaw=7.0, up=0.0, heel=0.0, toe=0.0, knee=4.0, w=1.0):
    return {f"legik.{s}": w, f"foot.{s}.fwd": fwd, f"foot.{s}.out": out, f"foot.{s}.yaw": yaw,
            f"foot.{s}.up": up, f"foot.{s}.heel": heel, f"foot.{s}.toe": toe, f"knee.{s}.out": knee}


def leg_fk(s, flex=0.0, knee=0.0, point=0.0, abd=0.0, tw_=0.0):
    return {f"legik.{s}": 0.0, f"thigh.{s}.flex": flex, f"shin.{s}.knee": knee, f"foot.{s}.point": point,
            f"thigh.{s}.abd": abd, f"thigh.{s}.tw": tw_}


def feet(lf=0.0, rf=0.0, lo=0.115, ro=0.115, ly=7.0, ry=7.0, lk=4.0, rk=4.0):
    return U(foot("L", lf, lo, ly, knee=lk), foot("R", rf, ro, ry, knee=rk))


def mirror(p):
    return mirror_pose(p)


# ---------------------------------------------------------------------------------------------------------------
# stances
RELAX = U(hips(0, 0, -0.012), arm("L", -80, 6, 12, 0, 6), arm("R", -80, 6, 12, 0, 6),
          feet(0.0, 0.0, 0.12, 0.12, 8, 8), look(0, -2))

# free left hand guard (fist forward at chest height) used by 1h stances without shield
L_GUARD = grip("L", -2, 0.30, 1.22, -15, 70, 0, pole=10)
# shield raised in front of the chest (shield face forward)
L_SHIELD = grip("L", -6, 0.34, 1.26, -8, 84, 0, pole=-5)
L_SHIELD_LOW = grip("L", 10, 0.30, 1.08, -5, 80, 0, pole=0)

# fighting stance legs: left foot forward
LEGS_FIGHT = U(feet(0.13, -0.15, 0.13, 0.15, 12, 32, 6, 10), hips(-0.01, 0.0, -0.065),
               torso(-14, 4, 0, -4, 3, 0, 6, 2, 0))
LEGS_WIDE = U(feet(0.16, -0.18, 0.16, 0.17, 14, 35, 8, 12), hips(-0.01, 0.0, -0.1),
              torso(-18, 6, 0, -6, 4, 0, 8, 3, 0))
LEGS_LOW = U(feet(0.12, -0.16, 0.16, 0.17, 18, 30, 12, 12), hips(0, 0.02, -0.13),
             torso(-10, 10, 0, 0, 8, 0, 4, 6, 0))

SWORD_READY = grip("R", 40, 0.30, 1.10, 10, 38, 0, pole=0)
SWORD_HIGH = grip("R", 55, 0.24, 1.36, -15, 55, 0, pole=10)

ST_1H = U(RELAX, LEGS_FIGHT, SWORD_READY, L_GUARD, look(8, -4))
ST_SHIELD = U(RELAX, LEGS_FIGHT, SWORD_HIGH, L_SHIELD, look(10, -4))
ST_2H = U(RELAX, LEGS_WIDE, grip("R", 8, 0.33, 1.07, -6, 38, 0, pole=-5), two_hand("L", -0.14), look(12, -4))
ST_SPEAR = U(RELAX, LEGS_WIDE, grip("R", 55, 0.18, 1.04, -16, 6, 0, pole=0),
             two_hand("L", 0.42, 180, pole=-20), look(14, -4))
ST_DAGGER = U(RELAX, LEGS_LOW, grip("R", 30, 0.34, 1.02, 0, 12, 0, pole=10), L_GUARD, look(6, -8))
ST_BOW = U(RELAX, feet(0.05, -0.08, 0.13, 0.14, 10, 25), hips(0, 0, -0.035), torso(-6, 2, 0, -2, 1, 0, 2, 1, 0),
           grip("L", 50, 0.26, 1.0, 20, 70, 0, pole=5), arm("R", -76, 12, 22, 0, 8), look(4, -3))
ST_STAFF = U(RELAX, feet(0.06, -0.08, 0.13, 0.13, 10, 22), hips(0, 0, -0.03), torso(-6, 2, 0, -2, 1, 0, 2, 1, 0),
             grip("R", 62, 0.28, 1.14, 8, 84, 0, pole=5), arm("L", -70, 30, 45, 0, 0), look(4, -3))
ST_WAND = U(RELAX, LEGS_FIGHT, grip("R", 30, 0.36, 1.12, 0, 5, 0, pole=5),
            grip("L", 10, 0.26, 1.2, -10, 60, 0, pole=10), look(8, -4))
ST_DUAL = U(RELAX, LEGS_FIGHT, grip("R", 35, 0.32, 1.12, 5, 40, 0, pole=0),
            grip("L", 25, 0.34, 1.14, 0, 32, 0, pole=0), look(6, -4))
ST_HURT = U(RELAX, LEGS_FIGHT, hips(0.0, 0.0, -0.1), torso(-10, 14, 6, -2, 10, 4, 4, 8, 2),
            grip("R", 38, 0.30, 1.0, 12, 18, 0, pole=0), grip("L", -40, 0.14, 1.2, -20, 20, 0, pole=10),
            look(6, 4, -4))

STANCES = {
    "sword": ST_1H, "shield": ST_SHIELD, "gs": ST_2H, "axe": ST_1H, "spear": ST_SPEAR, "dagger": ST_DAGGER,
    "dual": ST_DUAL, "staff": ST_STAFF, "wand": ST_WAND, "bow": ST_BOW, "none": RELAX,
}

# weapon props shown on each animation family in previews (right hand, left hand)
PROPS = {
    "sword": ("sword", None), "shield": ("sword", "shield"), "gs": ("greatsword", None), "axe": ("axe", None),
    "spear": ("spear", None), "dagger": ("dagger", None), "dual": ("sword", "sword"), "staff": ("staff", None),
    "wand": ("wand", None), "bow": (None, "bow"), "none": (None, None),
}


def spin_legs(legs, ang, lift_L=0.0, lift_R=0.0, heel_L=0.0, heel_R=0.0):
    """Rotate the foot placements of a leg stance by `ang` degrees about the body axis (CCW = to the left) and add
    +ang to the pelvis yaw: used for spinning attacks (feet step around, the torso stays aligned)."""
    out = dict(legs)
    a = math.radians(ang)
    for s, sx, lift, heel in (("L", 1.0, lift_L, heel_L), ("R", -1.0, lift_R, heel_R)):
        fwd = legs.get(f"foot.{s}.fwd", DEFAULTS[f"foot.{s}.fwd"])
        o = legs.get(f"foot.{s}.out", DEFAULTS[f"foot.{s}.out"])
        yaw = legs.get(f"foot.{s}.yaw", DEFAULTS[f"foot.{s}.yaw"])
        x, y = sx * o, -fwd
        xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        out[f"foot.{s}.out"] = sx * xr
        out[f"foot.{s}.fwd"] = -yr
        out[f"foot.{s}.yaw"] = yaw + sx * ang
        out[f"foot.{s}.up"] = lift
        out[f"foot.{s}.heel"] = heel
        out[f"legik.{s}"] = 1.0
    out["hips.yaw"] = legs.get("hips.yaw", 0.0) + ang
    return out
