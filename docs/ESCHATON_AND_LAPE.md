# Eschaton and Lape's new table (bh-041)

## The name

**Eschaton** (rarity 14, the fifteenth tier): *the last things*. Primordial is the oldest thing in the world; Eschaton
is the last thing it will ever make. It sits above every Ascendant tier, and no monster carries it. Only Lape the
Ancient makes it, and only from the highest-tier lots laid in his dishes.

- Colour: mirror chrome (`BH.RARITY_COLORS[14]`), with the spectrum running through it: the name in a tooltip cycles
  through cool tints, slot frames shimmer, offer cards have a spectrum border.
- Base power: **x2.30** (Primordial x1.85), eight enchantments, two Legendary and two Aether powers, quality 28-38 %,
  up to eight sockets.
- Signature power **Unmaking** on every piece: hits may open a chrome rift on the target. It implodes for every element
  at once on all enemies within 4.5 m and breaks their armour for 4 s. Each Eschaton piece worn makes it more frequent
  and stronger (5 % + 3.5 % per piece, at most 45 %; 140 % + 15 % per piece of the hit, at most 320 %), and a 6-piece
  collection counts double.
- Wearing one: level 110 and a Class SSS hero (`DataGuilds.rank_for_rarity`).

## The catalogue: 470 pieces (`game/src/data/data_eschaton.gd`)

| | Knight | Mage | Ranger | Shadowblade |
|---|---|---|---|---|
| Collections (helm, armour, inner garment, leggings, gauntlets, boots, jewel) | 10 | 10 | 10 | 10 |
| Shields | 10 | — | — | — |
| Weapons: 10 of each type the class masters | sword, greatsword, axe, greataxe, spear, club, javelin (70) | staff, wand (20) | bow, crossbow, javelin, spear, dagger (50) | dagger, claw, knuckles, sword (40) |

Each collection is a set: two pieces add +26 % damage and +16 % health; four pieces add a class power (a stronger
version of the Ascendant 4-piece powers); six pieces make Unmaking answer twice as often and add +52 % elemental
damage and +78 % critical damage. The weapons are named for their class's collections (Doomsday Blade, Last Word Wand,
Extinction Arbalest, Quietus Talons ...).

Models and icons: `tools/blender/items/eschaton_regalia.py` (all 550 GLBs, including the right-hand gauntlets and
right-foot boots, in ~6 minutes) and `tools/blender/items/eschaton_icons.py` (game icons with star glints). The armour
uses the regalia builders fitted to the hero skeleton, in mirror chrome (`BH_Chrome`) over black chrome
(`BH_BlackChrome`). It carries the eclipse emblem, a floating halo of chrome blades behind the helm, blades on the
pauldrons, and light seams. Every weapon has a floating ring of chrome shards. The slot frame is
`tools/ui_art/eschaton_frame.py`.

The game's chrome: `MaterialLibrary._chrome_mat`, a clear-coated mirror metal with a faint light of its own so it
reads in dark dungeons. `AscendantFx` mode 4 adds a thin film of the spectrum sliding with the view, white glints
sweeping the surface, flashing star sparkles, and an eclipse sigil under a dropped piece.

## Lape's new table (`game/src/core/items/lape_trade.gd`)

What the hero lays down steers what he makes. `LapeTrade.essence()` reads the lot: kinds of gear, elements (bases and
set crystals), sets, Ascendant and Fabled pieces, filled sockets. Then `draw_offers()` deals **three to five offers**
(by the lot's worth) from these kinds:

| Kind | When | What |
|---|---|---|
| Crafted | always fills the table | a licensed piece for the hero's class; kinds of gear laid down come up three times as often; now and then a tier higher (12 %) or lower (18 %) |
| Reforged | Elite..Legendary plain pieces laid down (45 %) | one of them, made again one tier higher, keeping its sockets |
| Set-mending | Ascendant or Eschaton collection pieces laid down (65 %) | a piece of that collection that is neither laid down nor worn |
| Fabled | a Fabled arm laid down (55 %) | another Fabled arm of its tier for the hero's class |
| Ascendant | Ascendant work laid down (50 %) | an Ascendant piece up to the best tier laid down |
| Hoard | crystals set in the lot, or a leading element (35 %) | two to four crystals of that element |
| **Eschaton** | `eschaton_chance(lot)` | a piece for the hero's class, leaning to the kinds laid down |

`eschaton_chance = 1 - e^(-score / 24)`, at most 75 %, where each piece scores Legendary 0.05, Aether 0.25, Cosmic 1,
Divine 2, Eternal 4, Primordial 8, Eschaton 10. So three Primordial pieces give 63 % per look, one Primordial 28 %,
three Eternal 39 %, three Cosmic 12 %, three Aether 3 %. A lucky look may hold two. The table shows the chance as soon
as the lot is laid down.

- The same lot always gets the same first look, whatever order the dishes are filled in.
- **Ask Lape to Look Again** pays him to look at the same lot again (6 % of its worth, more each time) and deals a new
  set of offers.
- There is always a weapon among the offers, and the gold is always there.
- His words: he remarks on what the lot has in common (three of a kind, one collection, one element, Ascendant,
  Fabled, many crystals, a scattered lot, and an omen when the last work is close). He has lines for every Ascendant
  tier's offer, for the Eschaton revelation, for a paid second look, and for when the last work leaves his table.

## The draw (`game/src/ui/widgets/eschaton_reveal.gd`)

When a look holds an Eschaton piece, the table goes dark:

1. An eclipse opens: a black sun in a white corona, blades of light turning one way and the spectrum the other.
2. A white flash and a camera shake, with thunder, a chime and the legendary drop sound.
3. The piece bursts out of the eclipse in a spray of star glints.
4. **ESCHATON** slams down letter by letter in chrome, then "The last work · <name>".

A click (or seven seconds) returns to the table, scrolled to the Eschaton card. Taking it plays a shorter burst and
raises a pillar of chrome light over the hero.
