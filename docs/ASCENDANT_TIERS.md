# Ascendant tiers: Cosmic, Divine, Eternal, Primordial (bh-034)

Four rarities above Legendary and Aether, found only on **dungeon bosses of level 70 and above**. Every tier has ten
collections (three knight, three mage, two ranger, two shadowblade); every collection is a nine-piece set, so every tier
has **ten pieces of every equipment type**: helm, armour, inner garment, leggings, gauntlets, boots, jewel, shield and
weapon, 360 pieces in all. Data: `game/src/data/data_ascendant.gd`. Models and icons: `tools/blender/items/ascendant_regalia.py`.
Effects: `game/src/vfx/ascendant_fx.gd`. Tests: `game/tests/unit/test_bh034.gd`.

| Tier | Boss level | Chance per dungeon boss | Base power | Signature power | Guild rank to wear | Look |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Cosmic | 70+ | 5 % | x1.25 | **Starfall**: a star falls on the target, Light damage within 3 m | Class S | night-sky steel, a drifting nebula and twinkling stars in the metal, orbit rings |
| Divine | 80+ | 2.5 % | x1.40 | **Judgement**: a pillar of holy light, Light damage within 2.5 m and a heal | Class SS | white-gold plate, a light sweeping up the armour, halos and wings |
| Eternal | 90+ | 1.2 % | x1.60 | **Echo**: the blow lands again, every cooldown slips 0.15 s | Class SSS | rose-gold and pearl, ripples of time rising through it, clock-dial crowns |
| Primordial | 100+ | 0.5 % | x1.85 | **Eruption**: Fire and Earth erupt within 4 m and set the target burning | Class SSS | obsidian and bone, molten cracks breathing in it, shard crowns |

* The tiers are tried from the top on every kill of a dungeon boss of high enough level; magic find raises the odds up to
  x1.5. A level-120 lord leaves an Ascendant piece about one kill in eleven. The collection favours the hero's class three
  to one; a non-knight is never given a shield, nor another class's weapon.
* **Base power**: the piece's weapon damage or Defense (after item-level scaling) is multiplied by its tier.
* **Rolls**: six or seven enchantments at the top of their tiers (Primordial seven), a random Legendary and Aether power,
  high quality, more sockets (up to 8), and the tier's signature power on every piece.
* **Signature power**: each piece of a tier worn adds one to its power, a 6-piece set two more. Chance and strength grow
  with the count and are capped (Starfall/Judgement 8 % at one piece to 40 %; Echo 10 % to 45 %; Eruption 6.5 % to 35 %).
* **Sets**: 2 pieces: more damage and health (Cosmic +10 %/+6 % up to Primordial +20 %/+12 %); 4 pieces: the
  collection's class power (below); 6 pieces: the signature power answers twice as often, plus elemental and critical damage.
* **On the ground**: an animated sigil of the tier (turning stars, a sunburst, a clock dial whose hands move, cracked
  ground glowing like a forge), a column of its light seen across the map, its motes, and a line in the log.
* **Worn**: the same moving light on every piece and held weapon, motes around the helm, armour, gauntlets and weapon.
* **In the bag**: the slot frame has the tier's colours and corner marks with two motes of light running round it; the
  tooltip names the tier and its power, and the name breathes.
* Ordinary loot never rolls these rarities; the Debug console's equipment drop floor set to an Ascendant tier forces a
  piece from any boss (testing). Network protocol 18.

## The forty collections

### Cosmic

| Collection | Class | Weapon | Jewel | Element | 4-piece bonus |
| --- | --- | --- | --- | --- | --- |
| Starfall Vanguard | knight | sword | ring | Light | Blocking releases a shockwave of 100% weapon damage (1 s cooldown). |
| Nebula Warlord | knight | greatsword | ring | Dark | Every fifth attack staggers hard and releases a radiant shockwave. |
| Orbit Sentinel | knight | spear | ring | Lightning | Take 25% less damage while below 35% health. |
| Astral Magister | mage | staff | ring | Light | Every 10 s your next skill releases a pulse of 180% spell damage around you. |
| Voidweaver | mage | wand | pendant | Dark | At maximum Arcane Charge your spells cost no Mana. |
| Eclipse Oracle | mage | staff | pendant | Lightning | Chain Lightning chains 4 more times against Wet targets. |
| Comet Strider | ranger | bow | pendant | Lightning | Critical hits chain 70% of their damage as lightning to 3 enemies. |
| Meteor Marksman | ranger | crossbow | brooch | Fire | Hits have a 25% chance to ignite. |
| Nightsky Reaver | shadowblade | dagger | brooch | Dark | Critical hits restore 4% of maximum health. |
| Starless Stalker | shadowblade | claw | brooch | Dark | Dodging leaves a crackling trail that Shocks enemies. |

### Divine

| Collection | Class | Weapon | Jewel | Element | 4-piece bonus |
| --- | --- | --- | --- | --- | --- |
| Seraph Paladin | knight | sword | ring | Light | Valor never decays and you start every fight with 40 Valor. |
| Archon Crusader | knight | greataxe | ring | Light | Cleave releases a travelling wave of 120% of its damage as Light. |
| Dawnward Templar | knight | club | ring | Fire | Kills restore 6% of maximum health. |
| Hierophant | mage | staff | ring | Light | Spell hits restore 3 Mana. |
| Lightbinder | mage | wand | pendant | Light | Firebolt always splits into three projectiles. |
| Cantor of Dawn | mage | staff | pendant | Fire | Burning spreads to a nearby enemy every second. |
| Zenith Archer | ranger | bow | pendant | Light | Critical hits flare 60% of their damage as Light onto enemies within 5 m. |
| Verdict Arbalist | ranger | crossbow | brooch | Lightning | Critical hits reduce every skill cooldown by 0.5 seconds. |
| Sanctified Shade | shadowblade | dagger | brooch | Light | Critical hits restore 5% of maximum health. |
| Penitent Talon | shadowblade | claw | brooch | Fire | Dodging grants 30% more movement speed for 2 seconds. |

### Eternal

| Collection | Class | Weapon | Jewel | Element | 4-piece bonus |
| --- | --- | --- | --- | --- | --- |
| Chronoguard | knight | greatsword | ring | Water | Critical hits reduce every skill cooldown by 0.6 seconds. |
| Everlasting Bulwark | knight | sword | ring | Ice | Blocking releases a shockwave of 140% weapon damage (1 s cooldown). |
| Aeonbreaker | knight | axe | ring | Wind | Take 30% less damage while below 35% health. |
| Timeweaver | mage | staff | ring | Water | Standing still for 1 s quadruples Mana regeneration. |
| Hourglass Sage | mage | wand | pendant | Ice | Frozen enemies explode on death for 50% of their maximum health as Ice. |
| Undying Seer | mage | staff | pendant | Dark | Every 10 s your next skill releases a pulse of 240% spell damage around you. |
| Evertide Hunter | ranger | bow | pendant | Water | Kills restore 6% of maximum health. |
| Endless Volley | ranger | crossbow | brooch | Wind | Critical hits chain 90% of their damage as lightning to 3 enemies. |
| Stillhour Assassin | shadowblade | dagger | brooch | Ice | Frozen enemies explode on death for 50% of their maximum health as Ice. |
| Ouroboros Fang | shadowblade | claw | brooch | Water | Critical hits restore 6% of maximum health. |

### Primordial

| Collection | Class | Weapon | Jewel | Element | 4-piece bonus |
| --- | --- | --- | --- | --- | --- |
| Worldforger | knight | greatsword | ring | Fire | Every fifth attack staggers hard and releases a radiant shockwave. |
| Titanblood Champion | knight | sword | ring | Fire | Kills restore 8% of maximum health. |
| Firstflame Warlord | knight | greataxe | ring | Earth | Cleave releases a travelling wave of 160% of its damage as Light. |
| Ashborn Archmage | mage | staff | ring | Fire | Burning spreads to a nearby enemy every second. |
| Primeval Shaman | mage | wand | pendant | Earth | Every 10 s your next skill releases a pulse of 300% spell damage around you. |
| Magma Oracle | mage | staff | pendant | Fire | At maximum Arcane Charge your spells cost no Mana. |
| Wildroot Hunter | ranger | bow | pendant | Earth | Hits have a 35% chance to ignite. |
| Cinderbolt Ballista | ranger | crossbow | brooch | Fire | Critical hits flare 90% of their damage as Light onto enemies within 5 m. |
| Abyssal Fang | shadowblade | dagger | brooch | Dark | Critical hits restore 7% of maximum health. |
| Elder Wyrm Talon | shadowblade | claw | brooch | Fire | Dodging leaves a crackling trail that Shocks enemies. |
