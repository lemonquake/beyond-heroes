# BH-024 — Leggings, the complete worn wardrobe, Unbound items

State: **IMPLEMENTED — VERIFIED IN THE GAME'S RENDERER AND BY TESTS** (no independent blind critic; no physical phone
test). Baseline: `main` at `649fc21` (BH-023). Engine: Godot 4.7.2 (Linux headless + Xvfb/lavapipe for captures),
Blender 5.2.2.

## What the run was asked

1. Continue where the previous run left off.
2. A new equipment slot for leg armour ("Pants"; named **Leggings**), at least 30 unique leggings including set pieces,
   a leggings piece for each of the 15 boss collections, the character model able to wear them, the Inventory UI and the
   merchants updated.
3. Legendary equipment from `models/special_weapon/`, and an `alj` code giving both pieces as variants without
   restrictions.

## 1. Where BH-023 left off — finished

BH-023 built the customisable hero body and the worn-gear pipeline but exported only three worn models (iron_hauberk,
iron_helm, padded_gambeson); the manifest's fallbacks pointed at eight models that did not exist, so every class wore the
knight's hauberk and iron helm (its own evidence, `bh-023/evidence/shots/gear_front.png`, shows a mage in mail).
Boots and jewellery had no builders; 14 of the 16 body garments had none.

Now every wearable base has its own worn model — 98 pieces: 16 armours and inner garments (`hero_wear_torso.py`, rewritten:
shirts, vests, a brigandine, three plate cuirasses with pauldrons and faulds, robes and an open coat), 12 helms,
10 gloves, 10 boots and 10 rings/pendants/charms (`hero_wear_ends.py`, boots and jewellery new), 34 leggings and the shared
`_breeches`, `_under_legs`, `_under_body`, `_under_hands`, `_under_feet`, `_shoes`.

Also fixed: `test_bh023.gd` called `SaveSystem.save_hero(SLOT, h)` with its arguments swapped. Under Godot 4.7.2 that is
a parse error that aborts the test runner (every suite after `test_bh022` never ran).

## 2. Leggings

Read docs/LEGGINGS.md for the player-facing summary. Code:

| Area | Where |
| --- | --- |
| Slot, name, category | `src/core/bh.gd` (`leggings` between `armor` and the gloves) |
| Catalogue: 20 class leggings, 2 set pieces, 8 uniques | `src/data/data_leggings.gd` (new) |
| Depth leg pieces (4, level 44) | `tools/blender/items/depth_catalog.py` → `src/data/data_depth_equipment.gd`, `depth_specs.json` |
| Boss Legguards (15) | `src/data/data_boss_sets.gd` (from `BH.SLOTS`; label, armour budget 24) |
| Affixes, powers, licences, relics, crystals, crafting, appraisal lines, names | `data_items.gd`, `data_relics.gd`, `data_crystals.gd`, `data_crafting.gd`, `data_lape_lines.gd` |
| Loot and class fit | `item_generator.gd` (class_fit), `auto_loot_rules.gd`, `inventory.gd` (sort order, Armor filter) |
| Merchants | `src/data/data_shops.gd` (five merchants, specials) |
| Paper dolls, glyph, tooltips | `inventory_window.gd`, `tempo_window.gd`, `tips.gd`, `assets/ui/slots/glyph_leggings.png` (`tools/ui_art/raster_slots.py`) |
| Fallback 2D icons | `assets/ui/icons/items/leggings_{plate,cloth,leather}.svg` (`tools/ui_art/bh024_leggings.py`) |
| Starting kits | `src/data/data_classes.gd` |
| Multiplayer | `src/net/net.gd` PROTOCOL 11 |

Art:

- Item models (the dropped pair) and 3D icons: `tools/blender/items/item_gear.py` `legs` + 34 `GEAR` specs;
  `build_items.py -- all <ids>`; icons composed with `icons_post.game_icon`.
- Worn models: `tools/blender/hero/hero_wear_legs.py`. Cloth cut from the hero's legs (tucked in at 3.5 mm at the waist,
  full thickness below the body garments' hems, within 6.5 mm below the calf so boots close over it) plus plates, knee
  cops, laces, wraps, belts, panels, pouches, sheaths, feathers. Outer parts are separate meshes the game leaves off
  under what is worn over them (`HeroWear.plan` → `skip`): `waist` under any shirt/coat, `hip` under a skirt below 0.80 m,
  `knee` under a robe below 0.45 m, `ankle_L/R` inside a boot. Body garments record their skirt height in the manifest
  (`@item(..., skirt=)`).
- Boss Legguards: `tools/blender/items/boss_regalia.py` `legguard()` (knights: three-lame cuisses and a fauld; mages:
  silk thigh wraps, an outer panel and an apron; rangers/shadowblades: strapped leather guards with a plate, emblem and a
  quiver or sheathed knife). Authored on the hero's own legs; `BossSetVisuals` scales them 1.15 round the hips for the
  armoured class bodies (`CLASS_LEGS_FIT`). Worn over `_under_legs` in the set's colour.
- Worn plate material: `hero_wear_kit.plate()` — the item colour lifted, metallic ≤ 0.55 (fully metallic plates reflected
  the dark sky and read as black in the game).

## 3. Special weapons — waiting for the models

`models/special_weapon/` is not in the repository on any branch (checked twice, 30 September 2026). Built without them:
Unbound items (`ItemInstance.unbound`: no level, attribute or rank requirement anywhere they are checked; saved as `ub`;
tooltip line), the empty `DataSpecialWeapons` table, and the `alj` code (adds every special weapon as Unbound; replies
"no special weapons are in this build yet" while the table is empty). docs/SPECIAL_WEAPONS.md lists the five steps to
add the two weapons once the files are pushed.

## Reproduce

```
B=blender-5.2.2 ; G=Godot 4.7.2
$B -b --factory-startup --python tools/blender/hero/hero_body.py -- export --clips=idle   # only for work/.../hero_mesh.npz; restore hero.glb + hero_meta.json from git afterwards
$B -b --factory-startup --python tools/blender/hero/hero_wear.py -- all                   # 98 worn pieces + manifest
BH_WEAR_SHOTS=front BH_WEAR_CLIPS=run $B -b --python tools/blender/hero/hero_wear.py -- preview a+b+c ...
$G --headless --path game res://tests/tools/dump_items.tscn                               # items.json
$B -b --factory-startup --python tools/blender/items/build_items.py -- all <leggings ids>
BH_REGALIA_SLOTS=leggings BH_REGALIA_RAW=work/lemondev/bh-024/scratch/icons_raw $B -b --python tools/blender/items/boss_regalia.py -- models icons noweapons
python tools/ui_art/bh024_leggings.py
$G --headless --path game --import
$G --path game res://tests/tools/capture_bh024.tscn -- --mode=legs|outfits|sets [...]   (Xvfb + lavapipe)
$G --headless --path game res://tests/tools/item_catalogue.tscn                          # docs/ITEM_CATALOGUE.txt
```

## Evidence

- `evidence/shots/` (game renderer): `legs_a/_b` (all 34 leggings), `outfits`, `sets` (15 collections with Legguards),
  `crimson_glory`, `starfall_hunter`, `gear24` (starting kits: the mage now in her robe and hood).
- `evidence/ui/` (game UI, `tests/tools/capture_bh024_ui.tscn`): the Inventory paper doll with the Leggings slot, a
  leggings tooltip, the Oathbound unique compared with the worn pair, and Brannoc's rack with two pairs of leggings.
- `evidence/blender/`: outfits front and running (16 body garments with leggings, boots, gloves, helms), all 34 worn
  leggings; `evidence/item_icons_*.png`, `svg_fallback_icons.png`, `slot_glyph.png`.

## Tests

New `game/tests/unit/test_bh024.gd` (14 tests, 1,219 checks, all passing): slot and saves, starting kits, the catalogue (unique names,
icons, item and worn models, weights, class split), set and depth pieces, boss Legguards (models follow both thighs),
loot and affixes, merchants, paper dolls, the hide rules, worn models on the body (budget 6,500 triangles), boss Legguards
on the hero, Unbound items (no requirements, saved), `alj`. Updated: `test_bh023` (save call), `test_boss_sets` (202
pieces; 14/13 per collection), `test_armory_cheats` (20 codes), `test_stats` (14 slots), `test_boss_set_visuals` (12 worn
pieces with the Legguards), `test_dungeon_growth` (84 depth designs).

Full-suite comparison, the same 50 suites on this tree and on a clean checkout of `649fc21` (Godot 4.7.2 headless;
`test_enemies` left out of both because it crashes the runner on the baseline too, a freed-instance lambda in
`area_effects.gd`):

| Suite | Baseline | This tree |
| --- | --- | --- |
| test_balance | 14 failures | 14 (same) |
| test_bh016 | 14 | 14 (same) |
| test_bh017 | 1 (tempering 1.0943 vs 1.0847) | 1 (same) |
| test_class_rework | 2 | 2 (same) |
| test_enemies2 | 8 | 8 (same) |
| test_inventory_overhaul | 15 | 15 (same) |
| test_dungeon_growth | 1 (greater-depth guardian abilities, random) | 1 (same) |
| test_bh019 | 3 (Lape offers one ranger/shadowblade piece; a script error) | 0 |
| test_bh023, test_bh024 | parse error / absent | pass |

No suite fails on this tree that passes on the baseline.

## Limits

- No blind critic review; no physical Android playtest; lavapipe frame times are not representative.
- `output/pdf/Beyond-Heroes-Boss-Collections.pdf` was not regenerated (needs reportlab, the Windows fonts it names, and a
  fresh set capture); `tools/create_boss_sets_pdf.py` already lists the Legguards.
- Leggings rarely clip when mixed across layers the rules do not know (a plate cuisse under a very short tunic that is not
  a "skirt"), and the torso's own trims are simple cords.
- A hero who completed a boss collection before BH-024 needs its Legguards again for the full-collection effect.
