class_name DataLootPools
## bh-033: data-driven material and supply pools (LootPools resolves them). Equipment is not in these pools; it keeps its
## own rarity/class rolls (Loot.equipment_for). Entries are [base id, chance per kill, min count, max count].
##
## Layers and precedence, resolved per kill (docs/LOOT_POOLS.md):
##   1. Monster   EnemyDef.loot — authored parts and quest items. Always rolled; nothing below may remove or double it.
##   2. Family    FAMILY — what that kind of creature carries (metal-bearing fighters: Iron Shards; beasts: hide).
##                ADDS entries the monster table does not already list. `metal` entries apply only to humanoid bodies,
##                so a skeletal hound or a wisp never drops scrap iron.
##   3. Theme     THEME — the dungeon theme's ordinary supplies. ADDS, skipping items already granted by layers 1-2.
##   4. Dungeon   DUNGEON — INHERITS its theme, then `add` (extra entries), `weight` (multiply a theme or signature
##                entry's chance) and `exclude` (drop a theme entry). Every dungeon's `material` is its SIGNATURE entry.
##   5. Map       MAP — overworld region supplies, the same shape as a dungeon pool without a theme.
##   6. Completion BOSS_COMPLETION / USURPER_COMPLETION / CHEST_SUPPLY — reliable progression supplies on top.
## Unknown families, themes or maps resolve to an empty layer — never to a random global drop.

## Family salvage. "metal": humanoid bodies only.
const FAMILY := {
	&"bandit": [[&"iron_shard", 0.30, 1, 2, "metal"], [&"stolen_linen", 0.12, 1, 1]],
	&"orc": [[&"iron_shard", 0.35, 1, 2, "metal"]],
	&"goblin": [[&"iron_shard", 0.25, 1, 2, "metal"]],
	&"ogre": [[&"iron_shard", 0.30, 1, 2, "metal"]],
	&"gigas": [[&"iron_shard", 0.35, 1, 3, "metal"]],
	&"kharvenn": [[&"iron_shard", 0.30, 1, 2, "metal"]],
	&"cultist": [[&"iron_shard", 0.15, 1, 1, "metal"]],
	&"undead": [[&"iron_shard", 0.18, 1, 2, "metal"], [&"bone_fragment", 0.20, 1, 2]],
	&"construct": [[&"iron_shard", 0.40, 1, 3, "metal"]],
	&"wirewright": [[&"iron_shard", 0.35, 1, 2, "metal"]],
	&"wiresick": [[&"iron_shard", 0.20, 1, 1, "metal"]],
	&"infernal": [[&"iron_shard", 0.15, 1, 1, "metal"]],
	&"jade": [[&"iron_shard", 0.15, 1, 1, "metal"]],
	&"beast": [[&"beast_hide", 0.30, 1, 2]],
	&"corrupted": [[&"beast_hide", 0.15, 1, 1]],
	&"fungal": [[&"brightcap", 0.12, 1, 1]],
	&"aether": [[&"arcane_dust", 0.20, 1, 2]],
	&"drowned": [[&"stolen_linen", 0.08, 1, 1]],
}

## Dungeon theme supplies: the ordinary drops of every floor that shares the theme.
const THEME := {
	&"fungal": [[&"brightcap", 0.10, 1, 2], [&"silverleaf", 0.08, 1, 2]],
	&"drowned": [[&"mirebloom", 0.10, 1, 2], [&"stolen_linen", 0.06, 1, 1]],
	&"ember": [[&"iron_shard", 0.18, 1, 2], [&"emberroot", 0.08, 1, 1], [&"ember_core", 0.04, 1, 1]],
	&"rime": [[&"frost_crystal", 0.07, 1, 1], [&"iron_shard", 0.10, 1, 1]],
	&"orrery": [[&"arcane_dust", 0.12, 1, 2], [&"iron_shard", 0.08, 1, 1]],
	&"hideout": [[&"iron_shard", 0.18, 1, 2], [&"stolen_linen", 0.10, 1, 1]],
	&"crypt": [[&"grave_dust", 0.14, 1, 2], [&"iron_shard", 0.08, 1, 1]],
	&"hive": [[&"arcane_dust", 0.10, 1, 1], [&"brightcap", 0.08, 1, 1]],
	&"mire": [[&"mirebloom", 0.12, 1, 2], [&"ghoul_bile", 0.05, 1, 1]],
	&"thorn": [[&"beast_hide", 0.12, 1, 2], [&"silverleaf", 0.10, 1, 2]],
	&"sandtomb": [[&"grave_dust", 0.12, 1, 2], [&"arcane_dust", 0.08, 1, 1]],
	&"storm": [[&"storm_essence", 0.06, 1, 1], [&"iron_shard", 0.10, 1, 1]],
	&"umbral": [[&"shadow_silk", 0.06, 1, 1], [&"grave_dust", 0.10, 1, 1]],
	&"crystal": [[&"frost_crystal", 0.06, 1, 1], [&"arcane_dust", 0.10, 1, 1]],
	&"gilded": [[&"iron_shard", 0.15, 1, 2], [&"arcane_dust", 0.08, 1, 1]],
	&"cavern": [[&"iron_shard", 0.12, 1, 2], [&"ember_core", 0.04, 1, 1]],
	&"abyss": [[&"shadow_silk", 0.05, 1, 1], [&"arcane_dust", 0.10, 1, 1]],
	&"prism": [[&"frost_crystal", 0.08, 1, 1], [&"arcane_dust", 0.12, 1, 2]],
	&"underworld": [[&"grave_dust", 0.12, 1, 2], [&"shadow_silk", 0.06, 1, 1]],
	&"aether": [[&"arcane_dust", 0.14, 1, 2], [&"wisp_mote", 0.06, 1, 1]],
	&"eclipse": [[&"shadow_silk", 0.06, 1, 1], [&"wisp_mote", 0.05, 1, 1]],
	&"solar": [[&"ember_core", 0.05, 1, 1], [&"emberroot", 0.08, 1, 1]],
	# bh-042: the Abyss themes
	&"hollow": [[&"grave_dust", 0.14, 1, 2], [&"bone_fragment", 0.12, 1, 2], [&"shadow_silk", 0.06, 1, 1]],
	&"sunless": [[&"mirebloom", 0.10, 1, 2], [&"tide_pearl", 0.06, 1, 1], [&"shadow_silk", 0.05, 1, 1]],
	&"ashgrave": [[&"iron_shard", 0.18, 1, 2], [&"ember_core", 0.07, 1, 1], [&"slag_ember", 0.06, 1, 1]],
	&"weeping": [[&"frost_crystal", 0.08, 1, 1], [&"rime_shard", 0.08, 1, 1], [&"grave_dust", 0.08, 1, 2]],
	&"throne": [[&"shadow_silk", 0.07, 1, 1], [&"aether_shard", 0.05, 1, 1], [&"wisp_mote", 0.06, 1, 1]],
	&"jade": [[&"arcane_dust", 0.10, 1, 1], [&"iron_shard", 0.10, 1, 1]],
	&"obsidian": [[&"iron_shard", 0.18, 1, 2], [&"ember_core", 0.04, 1, 1]],
	&"vein": [[&"shadow_silk", 0.05, 1, 1], [&"iron_shard", 0.10, 1, 1]],
}

## Chance per kill of a dungeon's signature material (its `material`), before DUNGEON weights.
const SIGNATURE_CHANCE := 0.08

## Per-dungeon composition on top of the inherited theme. Dungeons not listed inherit their theme plus signature as-is.
const DUNGEON := {
	# bh-013 hideouts share a theme; the cellars are a thieves' den, the warcamp an orc armoury.
	&"cellars": {"add": [[&"stolen_linen", 0.08, 1, 1]], "weight": {&"iron_shard": 1.0}},
	&"burrows": {"exclude": [&"stolen_linen"], "add": [[&"wolf_fang", 0.10, 1, 1]]},
	&"warcamp": {"add": [[&"orc_tusk", 0.08, 1, 1]], "weight": {&"iron_shard": 1.4}},
	&"ember": {"weight": {&"iron_shard": 1.3}},
	&"barrow": {"add": [[&"bone_fragment", 0.10, 1, 2]]},
	&"ossuary": {"add": [[&"bone_fragment", 0.12, 1, 2]]},
	&"reliquary": {"weight": {&"grave_dust": 0.5}},
}

## Overworld region supplies (MapDef.id). Herbs also grow in patches (GatherNode); these are the monster share.
const MAP := {
	&"westreach": [[&"silverleaf", 0.05, 1, 1]],
	&"ruined_forest": [[&"beast_hide", 0.06, 1, 1]],
	&"catacombs": [[&"grave_dust", 0.08, 1, 1]],
}

## A dungeon lord's fall (once per hero: the boss never returns). Counts scale with the dungeon tier (bh-012 = tier 1).
## Each row: [base id, min, max]; "signature" stands for the dungeon's material.
const BOSS_COMPLETION := [[&"signature", 3, 5], [&"steel_ingot", 1, 2], [&"arcane_dust", 2, 4]]
## Every later raid's champion (the Usurper holding the sanctum): a smaller, still reliable share.
const USURPER_COMPLETION := [[&"signature", 1, 2], [&"iron_shard", 3, 5]]
## A dungeon chest's supplies by chest tier (0 plain, 1 sealed, 2 vault).
const CHEST_SUPPLY := [[[&"iron_shard", 2, 4]], [[&"iron_shard", 3, 5], [&"signature", 1, 1]], [[&"steel_ingot", 1, 2], [&"signature", 2, 3]]]

## Bounded bad-luck protection: after this many kills in a row that could have dropped the item but did not, the next
## eligible kill drops its minimum count. Applies only to these progression staples.
const PITY := {&"iron_shard": 5, &"beast_hide": 6}
