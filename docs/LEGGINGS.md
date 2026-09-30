# Leggings (bh-024)

Beyond Heroes now has a fourteenth equipment slot, **Leggings**, between Armor and the gloves. It takes any leg armour:
plate cuisses, mail chausses, silk trousers, hide leggings, dark wrapped leggings. Every class starts in a pair, every
armour merchant stocks them, monsters drop them, crafters make them, and they are worn on the hero's body model.

## The slot

- Slot and category id `leggings`, shown as **Leggings** (the empty slot shows a pair of trousers).
- Inventory (I) and Tempo (O) paper dolls: clothing down the left (helm, inner garment, armour, leggings, glove I,
  boot I), jewellery down the right (accessories I-IV, glove II, boot II), so the paired slots sit side by side.
- Leggings roll every armour enchantment (resistances, life, mana, attributes, regeneration, status resistance and the
  rest), plus Evasion ("of Shadows' Step") and Knockback Resistance ("of the Anchor"). They can carry Mythical
  (Frostguard, Windswift, Bastion), Legendary (Echoing, Stormstriding, Valorous, Stillwater, Wallbreaker's, Bloodthirsty),
  Aether (Riftwalker's) and relic powers (Windrunner's, Unbowed), and the Order of the Dawn, Wardens' Guild and Hunters'
  Lodge licences. Socket crystals act in leggings as in armour.
- Weight: heavy leggings 4.5-9, cloth 1.6.
- Multiplayer protocol 11 (a Leggings slot and its items travel between players).
- Saves from before bh-024 load with the slot empty. New heroes start in their class's first pair: Iron Cuisses
  (Knight), Linen Trousers (Mage), Hide Leggings (Ranger), Cutpurse Trousers (Shadowblade).

## The catalogue: 34 unique leggings and 15 Legguards

| Level | Knight (plate) | Mage (silk) | Ranger (hide) | Shadowblade (dark leather) |
| ---: | --- | --- | --- | --- |
| 1 | Iron Cuisses | Linen Trousers | Hide Leggings | Cutpurse Trousers |
| 6 | Mail Chausses | Scholar's Breeches | Tracker's Breeches | Nightweave Leggings |
| 12 | Riveted Legplates | Arcanist Legwraps | Stag-Hide Chaps | Silent-Step Breeches |
| 18 | Warden Cuisses | Magister Silks | Longstrider Leggings | Duskrunner Leggings |
| 30 | Knight-Commander's Cuisses | Aethersilk Trousers | Windrunner Leggings | Veilstalker Leggings |
| 44 (depth) | Deepwarden Cuisses | Prismkeeper Legwraps | Vaultpath Leggings | Gloomthread Leggings |

Set pieces: **Aether Guardian Cuisses** (the Aether Guardian set now has six pieces; wearing all six adds +8% maximum HP
and +10% Knockback Resistance) and **Starbound Sage Leggings** (six pieces; all six add +8% Cast Speed and +1.5 Mana
Regeneration). Brannoc sells both set pieces (and Seris the Sage's) once the Catacombs ritual has been seen.

Named uniques (drop like the other named uniques, from elites and bosses):

| Unique | Rarity | Class | Level | Power |
| --- | --- | --- | ---: | --- |
| Rimewalkers | Mythical | Knight | 10 | Frostguard: enemies that hit you are Chilled |
| Windswift | Mythical | Ranger | 10 | Windswift: after dodging, 20% more Movement Speed for 2 s (also sold by the Hooded Stranger) |
| Oathbound | Legendary | Knight | 16 | Valorous: Valor never decays, fights start at 30 Valor |
| Echoing Bastion | Legendary | Knight | 20 | Echoing: blocking releases a 60% weapon-damage shockwave |
| Stillwater | Legendary | Mage | 14 | Stillwater: Mana regeneration tripled while standing still |
| Bloodrunner | Legendary | Shadowblade | 16 | Bloodthirsty: kills restore 4% of maximum HP |
| Stormstriders | Aether | Ranger | 14 | Stormstriding: dodging or blinking leaves a Shocking trail |
| Riftwalker | Aether | Mage | 18 | Riftwalker's: Blink leaves a Frost Nova |

Boss collections: each of the fifteen sets gained its **Legguards** (level 30, Master, boss-only, like the rest of the
collection); see docs/BOSS_SETS.md. Collections now have 14 pieces (13 for two-handed ones).

Full stats: docs/ITEM_CATALOGUE.txt, section 4 ("Leggings").

## Where to buy them

| Merchant | Stock |
| --- | --- |
| Brannoc's Forge (Malasugue) | 2 leggings in every rack (class-matched), Aether Guardian Cuisses (after the ritual), Knight-Commander's Cuisses (level 28+) |
| Seris' Arcana (Malasugue) | 1 pair of silks, Starbound Sage Leggings (after the ritual), Aethersilk Trousers (level 28+) |
| Taicho's Arms Exchange (Olivar) | 2 premium pairs (Advanced and better) |
| Stonehand's Field Kit (Wyman) | 2 pairs |
| The Hooded Stranger | leggings in the rare pool; Windswift (after the Warden falls) |

## On the hero

Every leggings base has its own item model (the model on the ground, `tools/blender/items/item_gear.py` `legs`), its own
3D icon, and its own **worn model** fitted to the hero body (`tools/blender/hero/hero_wear_legs.py`): cloth cut from the
hero's own legs so it bends with them and follows the body sliders, with plates, knee cops, laces, wraps, belts, panels,
pouches, sheaths and feathers built on top.

Body garments now stop at the hips. Legs are covered by the Leggings; a hero in a shirt or coat without leggings gets
plain breeches (`_breeches`), and boss Legguards sit over a plain under-layer in the set's colour (`_under_legs`).

What is worn over a pair of leggings hides the parts that would poke through it (HeroWear.plan):

| Worn over them | Hidden |
| --- | --- |
| any shirt, coat or armour | the belt, buckle, sash, hanging panel and tassets |
| a skirt, tail or fauld reaching below 0.80 m (hauberk, plate faulds, robes, coats) | thigh plates, leather guards, pouches, sheaths, feathers |
| a robe or long coat reaching below 0.45 m | knee cops and knee pads |
| a boot on that foot | the ankle cuff and the wraps below the calf |
