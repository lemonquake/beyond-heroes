"""The Beyond Heroes humanoid action library (one shared set, evaluated per rig) and its metadata sidecar.

library() -> list of bh_anim.Anim (cached). write_meta(path) measures every animation on the standard rig
(foot contacts, ground speeds, weapon-tip sweeps) and writes game/assets/characters/anim_meta.json.
"""
import json
import os

FPS = 30

REQUIRED = (
    "idle idle_look idle_adjust idle_knight idle_mage idle_hurt "
    "idle_1h idle_shield idle_2h idle_spear idle_dagger idle_bow idle_staff idle_wand idle_dual idle_combat_hurt "
    "walk run walk_back strafe_l strafe_r run_combat walk_hurt run_hurt run_start run_stop turn_l turn_r "
    "dodge_roll dodge_step "
    + " ".join(f"{w}_{i}" for w in ("sword", "gs", "axe", "spear", "dagger", "dual", "staff", "wand")
               for i in range(1, 5)) +
    " bow_1 bow_2 bow_draw_hold bow_release "
    "sword_heavy gs_heavy axe_heavy spear_heavy dagger_heavy dual_heavy staff_heavy wand_heavy "
    "charge_hold charge_release special_attack block_loop block_impact parry shield_bash "
    "cast_quick cast_heavy cast_channel cast_area cast_weapon cast_ultimate whirlwind leap_slam war_cry blink "
    "hit_light hit_heavy hit_front hit_back hit_left hit_right "
    "stagger_small stagger_heavy knockback launch wall_impact knockdown getup death revive "
    "interact_pickup interact_chest interact_talk interact_teleport "
    "alert taunt boss_slam boss_sweep boss_roar boss_charge boss_summon"
).split()

_LIB = None


def library(partial=False):
    global _LIB
    if _LIB is None:
        import importlib
        mods = []
        for m in ("lib_idles", "lib_loco", "lib_attacks", "lib_actions"):
            try:
                mods.append(importlib.import_module(m))
            except ModuleNotFoundError as e:
                if not partial:
                    raise
                print("[library] missing module", e)
        out = []
        for m in mods:
            out.extend(m.build())
        names = [a.name for a in out]
        dup = {n for n in names if names.count(n) > 1}
        assert not dup, f"duplicate animations: {dup}"
        missing = [n for n in REQUIRED if n not in names]
        if missing and not partial:
            raise AssertionError(f"library incomplete, missing: {missing}")
        _LIB = out
    return _LIB


# ----------------------------------------------------------------------------------------------------------------
def _sec(f):
    return round(float(f) / FPS, 3)


def measure(anim, rig=None):
    """Seconds-based metadata for one animation, measured on the rig (standard proportions by default)."""
    import bh_anim as A
    import bh_diag as DG
    import bh_skeleton as S
    rig = rig or A.Rig(S.proportions())
    m = anim.meta
    out = {"length": _sec(anim.length), "loop": bool(anim.loop)}
    frames = None
    if m.get("hits"):
        frames = DG.eval_frames(anim, rig)
        side = m.get("hand", "R")
        bone_side = "L" if m.get("hit_bone") == "weapon.L" else side
        P = DG.weapon_tip(frames, rig, bone_side, m.get("tip", 0.8))
        wins = DG.refine_hits(P, m["hits"])
        out["hits"] = [[a, b] for a, b in wins]
        v = DG.tip_speed(P)
        out["tip_speed_peak"] = round(float(v.max()), 2)
    for k in ("release",):
        if k in m:
            out[k] = _sec(m[k])
    if "cancel_after" in m:
        out["cancel_after"] = _sec(m["cancel_after"])
    if "combo_window" in m:
        a, b = m["combo_window"]
        out["combo_window"] = [_sec(a), _sec(b)]
    if "iframes" in m:
        out["iframes"] = [_sec(x) for x in m["iframes"]]
    if "parry" in m:
        out["parry_window"] = [_sec(x) for x in m["parry"]]
    if "airborne" in m:
        out["airborne"] = [_sec(x) for x in m["airborne"]]
    for k in ("travel", "turn", "turn_per_loop"):
        if k in m:
            out[k] = m[k]
    if "footsteps" in m:
        out["footsteps"] = [_sec(f) for f in m["footsteps"]]
    if getattr(anim, "gait", None) is not None:
        frames = frames or DG.eval_frames(anim, rig)
        g = DG.measure_gait(anim, rig, frames)
        out["ground_speed"] = round(g["speed"], 3)
        out["foot_slide_max"] = round(g["slide_max"], 4)
        out["direction_deg"] = anim.gait.dir
    elif "ground_speed" in m:
        out["ground_speed"] = m["ground_speed"]
    wpn = m.get("props")
    if wpn and any(wpn):
        out["props"] = {"R": wpn[0], "L": wpn[1]}
    return out


def write_meta(path, rig=None):
    lib = library()
    data = {"fps": FPS, "generator": "tools/blender/characters/bh_library.py",
            "notes": {
                "space": "in place; hips move vertically only (plus small weight shifts). turn_l/turn_r end rotated "
                         "by 'turn' degrees; whirlwind turns 360 per loop.",
                "hits": "seconds at 1.0x, measured from the weapon-tip sweep (tip speed >= 55% of peak inside the "
                        "authored strike segment)",
                "ground_speed": "m/s for the standard 1.8 m rig, measured from planted sole points; scale with the "
                                "model scale",
                "sockets": "weapon.R / weapon.L share one rest frame: +Y blade, +Z back of hand. Attach weapon GLBs "
                           "with an identity transform (shield faces outward from the left forearm).",
            },
            "animations": {}}
    for a in lib:
        data["animations"][a.name] = measure(a, rig)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    print(f"[meta] {len(lib)} animations -> {path}")
    return data
