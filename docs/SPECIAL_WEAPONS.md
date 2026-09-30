# The Ember Dragon set and the `alj` code (bh-024, bh-026)

The sculpts in `models/special_weapons/` are in the game as the **Ember Dragon** set: three Legendary pieces forged at
the Dragonforge — the last Legendary set Aljay wore while he was still human, in his last battle as a man (the Night of
Black Wings, docs/LORE.md §10). They are a different line from the Dragonforge boss collection (`boss_dragonforge_*`).

| Piece | Source | Kind | In the game |
| --- | --- | --- | --- |
| **Ember Dragonslayer** | `dragonforge_ember_dragonslayer.obj` | Sword (one-handed), fire edge | 1.12 m, held at its grip; its painted colours |
| **Aegis of Fragnir** | `dragonforge_aegis_of_fragnir.zip` | Shield | 0.84 m, the 1.9 M-triangle sculpt reduced to 12,000; its painted colours |
| **Ember Dragonhide** | `dragonforge_ember_dragonhide.obj` | Cuirass (armour slot) | fitted to the hero's body, skinned, follows the body sliders |

## Rules

- **Knights only.** The Knight among heroes, and the knight-type Tempos (Swordsman, Warden). Other classes are refused
  with "Knights only (Tempos: Swordsman, Warden)" (`ItemBaseDef.wearers`, `Equipment.wearer`, `TempoRules.equip_error`).
- **Legendary story pieces.** Level 30, 40 Strength, the Legendary gate (Class B). They are never loot, merchant stock
  or crafts (`ItemBaseDef.story`).
- **Set bonuses.** 2 pieces: +10% Defense and +8% maximum health. 3 pieces: +15% Fire damage and +10% Fire resistance;
  hits have a 15% chance to ignite enemies.
- The sword: the sword's level-30 damage curve +15%, 1.35 attacks a second, 35% fire. The shield: 46 Defense, 20% block
  chance, 35% block strength, +10% Fire resistance. The cuirass: 66 Defense, +10% Fire resistance, +5% maximum health.

## `alj`

Typing `alj` gives the hero the whole set as **Unbound** copies (`DataSpecialWeapons.unbound`):

- no level and no attribute requirement;
- wearable from **Class E** (the lowest guild class) instead of Class B — an Unranked hero registers with a guild first;
- **four sockets** open and empty (Legendary pieces can have up to six);
- still knights only; a Tempo may wear them whatever the Tempo rarity ceiling, as long as its hero is Class E.

The code needs three free bag cells; it adds nothing otherwise. Given to a non-knight, the reply says who can wear them.

## Art

- Item models and icons: `tools/blender/items/special_set.py`
  (`blender -b --factory-startup --python tools/blender/items/special_set.py -- models icons`, then
  `icons_post.game_icon` on `work/lemondev/bh-026/scratch/icons_raw/<id>.png` → `game/assets/ui/icons/items3d/<id>.png`).
  The sword and shield keep the sculpts' vertex colours; their material `BH_Baked__it_<id>` is drawn with the vertex
  colour as albedo (`MaterialLibrary._baked_mat`).
- The worn cuirass: `tools/blender/hero/hero_wear_special.py`
  (`blender -b --factory-startup --python tools/blender/hero/hero_wear.py -- ember_dragonhide`). The sculpt was made for
  arms hanging at the sides, so it is fitted to the hero standing in the game's idle pose — placed on the trunk, its
  lean corrected, pushed at least 10 mm out of the skin — skinned by the nearest skin (never the forearms, hands or
  shins; the upper arms only above the ribs), and carried back to the T-pose by inverse skinning. In the idle pose it is
  exactly the fitted sculpt; the pauldrons ride the upper arms. Dragon-scale plates, bronze ridges and horns.
- A knight-type Tempo wears the cuirass's item model on its chest bone, scaled out to the armoured body
  (`BossSetVisuals._wear_special`).

Evidence: `work/lemondev/bh-026/evidence/shots/` (`tests/tools/capture_bh026.tscn`). Tests: `tests/unit/test_bh026.gd`.
