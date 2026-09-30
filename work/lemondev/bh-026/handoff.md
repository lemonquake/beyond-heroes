# BH-026 — The Ember Dragon set (Aljay's DragonForge sculpts)

State: **IMPLEMENTED — VERIFIED BY TESTS AND IN THE GAME'S RENDERER.** Baseline: `main` at `8991893` (BH-025). Engine:
Godot 4.7.2, Blender 5.2.

## What was asked

Put the DragonForge 3D models from `models/special_weapons/` in the game — a different line from the Dragonforge boss
collection, the Ember Dragon series — as the last Legendary set Aljay wore in his final battle while still human. `alj` gives
the set as custom copies wearable even at Class E, with 4 sockets. Models must fit. Knight-type classes only. Push to
main, build the EXE and the APK.

## What was done

- **The set** (`game/src/data/data_special_weapons.gd`): Ember Dragonslayer (sword), Aegis of Fragnir (shield), Ember
  Dragonhide (cuirass); Legendary, level 30, 40 Strength, set `ember_dragon` with 2- and 3-piece bonuses (the full set
  ignites). Story pieces (`ItemBaseDef.story`): never loot, stock or crafts.
- **Knights only**: `ItemBaseDef.wearers` = knight, swordsman, warden. Heroes: `Equipment.wearer` (set from the class in
  `HeroData.setup`). Tempos: `TempoRules.equip_error`. Tooltip and Lape's appraisal show the line.
- **`alj`**: Unbound copies with four open sockets. Unbound now means no level or attribute requirement and **Class E**
  at most (was: no class requirement at all); Tempos skip their rarity ceiling for Unbound gear.
- **Art**: `tools/blender/items/special_set.py` (item models, icons), `tools/blender/hero/hero_wear_special.py` (the
  cuirass fitted to the hero: bound in the idle pose, inverse-skinned to the T-pose; see docs/SPECIAL_WEAPONS.md).
  Knight-type Tempos wear the cuirass on the chest bone (`BossSetVisuals._wear_special`). Vertex-coloured sculpts use
  the new `BH_Baked` material (`MaterialLibrary._baked_mat`).

## Interpretation calls

- "Knight-type classes" = the Knight hero class plus the vanguard Tempo classes on the knight rig (Swordsman, Warden).
- "Wearable even with Class E" = Class E is the minimum; an Unranked hero (no guild) cannot wear the Unbound copies.
- The set is three pieces because the folder holds three models.

## Evidence

- `evidence/shots/hero_set.png` (front, side, back), `hero_action.png` (swing, run, heavy), `tempos.png` — Godot
  renderer, `tests/tools/capture_bh026.tscn`.
- `game/tests/unit/test_bh026.gd` (10 tests): pieces, models and icons (vertex colours drawn), grip and shield
  conventions, the worn cuirass (skinned, shape keys, under 7,200 triangles), a Tempo wearing it, knights only (heroes
  and every Tempo class), never generated, `alj` (three Unbound Legendary copies, 4 empty sockets, saved), worn at level
  1 / Class E with the full-set flag, refused when Unranked, refused for a mage. `test_bh024` updated for Class E.

## Limits

- The cuirass is exact in the idle pose; elsewhere linear blend skinning bends the pauldrons with the arms, and in poses
  with the arms raised high the shoulder plates stretch. Not reviewed by a blind critic or on a phone.
- The sculpt's chest is shaped for a slimmer, female-shaped torso; on bulky body-slider settings the gap to the skin is
  kept by the build shape keys, not re-fitted.
- The Tempo cuirass is rigid on the chest (like the boss regalia on class bodies).
