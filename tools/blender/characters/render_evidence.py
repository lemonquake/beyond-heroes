"""Evidence renders (EEVEE) for C6: hero turnarounds with starting weapons, attack contact sheets at hit time,
locomotion / idle / reaction sheets, weapons sheet.

xvfb-run -a -s "-screen 0 1920x1080x24" blender -b --factory-startup --python render_evidence.py -- <modes> [--res N]
  [--cell N] [--out DIR] [--char knight,mage]
modes: heroes | attacks | loco | idles | reactions | casts | weapons | all
Hit-time frames come from game/assets/characters/anim_meta.json (middle of each measured hit window / release).
Sheets are composed with compose_sheets.py (system python3 + PIL).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

import bpy  # noqa: E402

import bh_library as L  # noqa: E402
import bh_materials as MT  # noqa: E402
import bh_mesh as M  # noqa: E402
import bh_render as RR  # noqa: E402
import bh_weapons as W  # noqa: E402
import preview_chars as PC  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


OUT = opt("--out", os.path.join(ROOT, "work", "lemondev", "bh-002", "evidence", "characters"))
RES = int(opt("--res", "1024"))
CELL = int(opt("--cell", "384"))
CHARS = opt("--char", "knight,mage").split(",")
MODES = argv or ["all"]
FR = os.path.join(os.environ.get("BH_SCRATCH", "/tmp/claude-0/c6"), "frames")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FR, exist_ok=True)
META = json.load(open(os.path.join(ROOT, "game", "assets", "characters", "anim_meta.json")))["animations"]
LIB = {a.name: a for a in L.library()}
START = {"knight": ("idle_shield", "sword", "shield"), "mage": ("idle_staff", "staff", None)}


def hit_frames(name):
    m = META[name]
    fr = [int(round((a + b) / 2 * 30)) for a, b in m.get("hits", [])]
    if "release" in m:
        fr.append(int(round(m["release"] * 30)))
    if not fr:
        fr = [int(round(LIB[name].meta.get("key", LIB[name].length / 2)))]
    return fr


class Shoot:
    def __init__(self, char, res, weapons):
        self.st = PC.Stage(char, res=res, samples=16, weapons=weapons)
        self.char = char
        # brighter studio world so dark metals read (the game uses its own lighting)
        w = bpy.context.scene.world
        w.node_tree.nodes["Background"].inputs[0].default_value = (0.11, 0.115, 0.14, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    def frame(self, anim, f, view, path, props=None, **cam):
        st = self.st
        an = LIB[anim]
        r, l = props if props is not None else an.meta.get("props", (None, None))
        if anim.startswith("dual"):
            r, l = "sword", "sword"
        st.set_props(r, l)
        st.play(an, f)
        st.camera(view, **cam)
        return st.render(path)


def sheet(paths, labels, name, cols, title):
    PC.compose(paths, labels, os.path.join(OUT, name + ".png"), cols=cols, title=title)


def heroes():
    for c in CHARS:
        idle, r, l = START[c]
        sh = Shoot(c, RES, [x for x in (r, l) if x])
        ps = []
        for view in ("front", "34", "back"):
            p = sh.frame(idle, 0, view, os.path.join(OUT, f"{c}_{view}.png"), props=(r, l), dist=5.2)
            ps.append(p)
        ps.append(sh.frame("idle", 0, "34", os.path.join(FR, f"{c}_bare.png"), props=(None, None), dist=5.2,
                           yaw_add=-70))
        sheet(ps, ["front", "3/4", "back", "no weapons, idle (armor/outfit detail)"], f"{c}_turnaround", 4,
              f"{c}: {idle} with starting weapons")


ATTACKS = {
    "knight": {"sword": ["sword_1", "sword_2", "sword_3", "sword_4", "sword_heavy"],
               "greatsword": ["gs_1", "gs_2", "gs_3", "gs_4", "gs_heavy"],
               "axe": ["axe_1", "axe_2", "axe_3", "axe_4", "axe_heavy"],
               "spear": ["spear_1", "spear_2", "spear_3", "spear_4", "spear_heavy"],
               "dagger": ["dagger_1", "dagger_2", "dagger_3", "dagger_4", "dagger_heavy"],
               "dual": ["dual_1", "dual_2", "dual_3", "dual_4", "dual_heavy"],
               "bow": ["bow_1", "bow_2", "bow_draw_hold", "bow_release"],
               "shield_special": ["shield_bash", "parry", "charge_release", "special_attack", "whirlwind",
                                  "leap_slam"]},
    "mage": {"staff": ["staff_1", "staff_2", "staff_3", "staff_4", "staff_heavy"],
             "wand": ["wand_1", "wand_2", "wand_3", "wand_4", "wand_heavy"]},
}


def attacks():
    for c in CHARS:
        sets = ATTACKS.get(c, {})
        if not sets:
            continue
        sh = Shoot(c, CELL, list(W.WEAPONS))
        for fam, names in sets.items():
            ps, ls = [], []
            for n in names:
                for f in hit_frames(n):
                    p = sh.frame(n, f, "34", os.path.join(FR, f"{c}_{n}_{f:03d}.png"))
                    ps.append(p)
                    ls.append(f"{n} {f / 30:.2f}s")
            sheet(ps, ls, f"attacks_{fam}", 6, f"{c}: {fam} at hit / release time (anim_meta.json)")


def multi(name, c, anims, n_frames, view="34", cols=8, title="", weapons=None):
    sh = Shoot(c, CELL, weapons or list(W.WEAPONS))
    ps, ls = [], []
    for a in anims:
        an = LIB[a]
        L_ = an.length if not an.loop else an.length - 1
        frames = [int(round(L_ * i / max(n_frames - 1, 1))) for i in range(n_frames)] if n_frames > 1 else \
            [int(an.meta.get("key", an.length // 2))]
        for f in frames:
            ps.append(sh.frame(a, f, view, os.path.join(FR, f"{c}_{a}_{f:03d}_{view}.png")))
            ls.append(f"{a} {f / 30:.2f}s")
    sheet(ps, ls, name, cols, title)


def loco():
    multi("locomotion_side", CHARS[0], ["walk", "run", "walk_back", "run_combat", "walk_hurt", "run_hurt"], 6,
          view="side", cols=6, title="locomotion (side view, one cycle, 6 evenly spaced frames)")
    multi("locomotion_misc", CHARS[0], ["strafe_l", "strafe_r", "dodge_roll", "dodge_step", "run_start", "run_stop",
                                        "turn_l", "turn_r"], 4, view="34", cols=8,
          title="strafes, dodges, starts/stops, turns")
    if len(CHARS) > 1:
        multi("locomotion_mage", CHARS[1], ["walk", "run"], 6, view="side", cols=6, title="mage walk / run")


def idles():
    names = ["idle", "idle_look", "idle_adjust", "idle_knight", "idle_mage", "idle_hurt", "idle_1h", "idle_shield",
             "idle_2h", "idle_spear", "idle_dagger", "idle_bow", "idle_staff", "idle_wand", "idle_dual",
             "idle_combat_hurt"]
    for c in CHARS:
        sh = Shoot(c, CELL, list(W.WEAPONS))
        ps, ls = [], []
        for a in names:
            an = LIB[a]
            f = an.length // 3
            ps.append(sh.frame(a, f, "34", os.path.join(FR, f"{c}_{a}_{f:03d}.png")))
            ls.append(f"{a} {f / 30:.2f}s")
        sheet(ps, ls, f"idles_{c}", 8, f"{c}: idle and stance variants")


def reactions():
    names = ["hit_light", "hit_heavy", "hit_front", "hit_back", "hit_left", "hit_right", "stagger_small",
             "stagger_heavy", "knockback", "launch", "wall_impact", "knockdown", "getup", "death", "revive",
             "block_impact"]
    c = CHARS[0]
    sh = Shoot(c, CELL, list(W.WEAPONS))
    ps, ls = [], []
    for a in names:
        an = LIB[a]
        fs = [int(an.length * 0.3), int(an.length * 0.75)] if a in ("knockback", "death", "knockdown", "wall_impact",
                                                                      "stagger_heavy", "getup", "revive") \
            else [int(an.meta.get("key", min(5, an.length)))]
        for f in fs:
            ps.append(sh.frame(a, f, "wide", os.path.join(FR, f"{c}_{a}_{f:03d}.png")))
            ls.append(f"{a} {f / 30:.2f}s")
    sheet(ps, ls, "reactions", 8, f"{c}: hit reactions, stagger, knockback, death")


def casts():
    names = ["cast_quick", "cast_heavy", "cast_channel", "cast_area", "cast_weapon", "cast_ultimate", "war_cry",
             "blink", "interact_pickup", "interact_chest", "interact_talk", "interact_teleport", "alert", "taunt",
             "boss_slam", "boss_sweep", "boss_roar", "boss_charge", "boss_summon", "charge_hold", "block_loop"]
    c = CHARS[-1]
    sh = Shoot(c, CELL, list(W.WEAPONS))
    ps, ls = [], []
    for a in names:
        f = hit_frames(a)[0]
        ps.append(sh.frame(a, f, "34", os.path.join(FR, f"{c}_{a}_{f:03d}.png")))
        ls.append(f"{a} {f / 30:.2f}s")
    sheet(ps, ls, "casts_skills_misc", 7, f"{c}: casts, skills, interactions, enemy/boss clips (key frames)")


def weapons():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cam = RR.setup_scene(res=CELL, samples=24)
    w = bpy.context.scene.world
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.17, 0.2, 1)
    bpy.data.objects["Ground"].hide_render = True
    mats = MT.make_materials("knight", vertex_color=False)
    ps, ls = [], []
    for name in W.WEAPONS:
        ob = M.build_static(name, W.WEAPONS[name](), mats)
        zs = [v.co.z for v in ob.data.vertices]
        Lz = max(zs) - min(zs)
        ob.location = (0, 0, 1.0 - (max(zs) + min(zs)) / 2)
        yaw = 25 if name == "shield" else (0 if name == "bow" else 35)
        RR.place_camera(cam, (0, 0, 1.0), 6.0, yaw, 12, ortho=max(Lz * 1.1, 0.42))
        p = os.path.join(FR, f"weapon_{name}.png")
        RR.render(p)
        ps.append(p)
        ls.append(f"{name}  {Lz:.2f} m, {M.tri_count(ob)} tris")
        bpy.data.objects.remove(ob)
    sheet(ps, ls, "weapons", 7, "weapons (origin = grip, +Z = blade/shaft; each framed to its own length)")


def main():
    modes = MODES
    if "all" in modes:
        modes = ["heroes", "weapons", "attacks", "loco", "idles", "reactions", "casts"]
    for m in modes:
        globals()[m]()


main()
