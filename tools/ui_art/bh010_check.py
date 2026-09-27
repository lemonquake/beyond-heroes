"""bh-010: list every required UI art id that is missing from game/assets/ui (and flag bad backdrop sizes).

Usage: python tools/ui_art/bh010_check.py      -> prints "MISSING: none" when everything exists.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", "game", "assets", "ui"))

SKILLS = """
zeal blessed_hammer heavens_fist
aura_might aura_cinders aura_winter aura_fervor aura_mending aura_defiance aura_thorns aura_clarity
arms_mastery shield_mastery iron_skin oathbound toughness second_wind retaliation crusader_resolve
blizzard flame_sentinel frost_orb
pyre_mastery frost_mastery storm_mastery tide_stone_mastery inner_fire mana_shield spell_echo arcane_precision
power_shot multishot frost_arrow blast_arrow arrow_rain deadeye storm_javelin snare_trap blast_trap vault hunters_mark
keen_eye deadly_aim light_feet piercing_arrows fleet_foot survivalist patient_hunter trapmaster
twin_fang venom_strike shadow_step fan_of_knives crippling_star eviscerate death_blossom smoke_veil blade_sentinel dread_mark quickstep
blade_mastery lethality evasion venomcraft ruthless shadow_discipline opportunist fleet_step
""".split()
TALENTS = """
r_dex r_bow r_crit r_focus r_evasion r_speed r_traps r_elemental_arrows keystone_sniper keystone_windrunner keystone_traplord
s_agi s_dagger s_crit s_combo s_evasion s_stealth s_poison s_bleed keystone_deathmark keystone_phantom keystone_plague
""".split()
STATUS = """
webbed feared marked stealth poised steady aura_might aura_cinders aura_winter aura_fervor aura_mending aura_defiance
aura_thorns aura_clarity bone_ward frenzy rune_immune
""".split()

REQUIRED = ([f"icons/skills/{i}.svg" for i in SKILLS] + [f"icons/talents/{i}.svg" for i in TALENTS]
            + [f"icons/status/{i}.svg" for i in STATUS]
            + ["icons/classes/ranger.svg", "icons/classes/shadowblade.svg", "portraits/ranger.svg", "portraits/shadowblade.svg",
               "tree/tree_bg_ranger.png", "tree/tree_bg_shadowblade.png"])


def check():
    missing = [p for p in REQUIRED if not os.path.isfile(os.path.join(UI, p))]
    bad = []
    try:
        from PIL import Image
        for p in ("tree/tree_bg_ranger.png", "tree/tree_bg_shadowblade.png"):
            fp = os.path.join(UI, p)
            if os.path.isfile(fp):
                im = Image.open(fp)
                amin = im.convert("RGBA").getextrema()[3][0]
                if im.size != (1600, 900) or amin != 255:
                    bad.append(f"{p}: size={im.size} min_alpha={amin}")
    except ImportError:
        pass
    return missing, bad


if __name__ == "__main__":
    m, b = check()
    print(f"required: {len(REQUIRED)} (skills {len(SKILLS)}, talents {len(TALENTS)}, status {len(STATUS)}, classes 2, portraits 2, tree 2)")
    print("MISSING:", "none" if not m else "")
    for p in m:
        print("  ", p)
    print("BAD BACKDROPS:", "none" if not b else "")
    for p in b:
        print("  ", p)
    sys.exit(1 if (m or b) else 0)
