# Boss equipment sets

Fifteen complete collections contain 202 distinct pieces. They begin dropping when the defeated boss encounter is **actually level 30**; the ordinary +2 boss item-level bonus cannot unlock them early.

Each eligible encounter drops **exactly one piece from one randomly selected boss set**, in addition to ordinary equipment, materials and other rewards. It replaces that encounter's generic set-piece roll, so there is no second set piece in the same reward bundle.

## Where to collect them

Eligible encounters are level-30-or-higher bosses (including dungeon lords), repeatable dungeon Usurpers occupying a defeated lord's sanctum, and named Depth Guardians. Ordinary monsters, ordinary elites and ordinary camp minibosses cannot produce these collections. Chest, Relic Cache, merchant and crafting generation also exclude them. Selling a boss piece and buying that same item back does not create a new drop.

Dungeon lords stay defeated in the existing progression system. Return after a dungeon recovers to fight its Usurper, or progress into its depths for a named Depth Guardian; these repeatable encounters make full collections attainable. The actual enemy must still be level 30 or higher.

## Collection odds

All fifteen sets remain possible for every hero. Random set selection multiplies these weights:

- A set suited to the hero's class has **2×** the usual weight.
- A currently owned but incomplete set has **4×** the usual weight, including a collection suited to another class.
- Within the selected set, each missing piece has **6×** the weight of each already owned piece.

The bonuses combine: a class-matched, partially owned set has weight 8 versus weight 1 for an unstarted collection from another class. A completed set loses the partial-set bonus. These are weighted random drops; duplicates and unrelated sets remain possible. They are not guaranteed follow-up pieces.

Ownership counts distinct base items in the bag, worn equipment, bound Tempos, the Spirit Hall, pending equipment recovery and the local Hero's Vault. Owning several copies of the same piece does not multiply its weight. Items left on the ground, sold to a merchant or held by another multiplayer player do not count.

## Wearing a complete set

Each collection has a main weapon, helm, inner garment, armor, Legguards (bh-024: the Leggings slot), left and right gauntlets, left and right greaves, signet, seal, pendant and brooch. One-handed collections also have a shield: **14 pieces** in total. Bow, crossbow, staff, spear and greatsword collections use both hands and have **13 pieces**, with no shield. Each piece has a specific equipment slot.

The Legguards follow each set's class: knights wear three-lame cuisses and a fauld across the hips, mages silk thigh wraps under an embroidered panel and a front apron, rangers and shadowblades strapped leather thigh guards with a plate and the set's emblem (rangers carry a quiver of spare bolts on the thigh, shadowblades a sheathed knife). On the hero they sit over a plain under-layer in the set's colour. Heroes who completed a collection before bh-024 need its Legguards for the full-collection effect again.

Pieces are **Master** rarity, require at least level 30 and retain the existing **Class D** hero-rank requirement. Each requires 32 of its class's principal attribute (Strength for Knight, Intelligence for Mage, Dexterity for Ranger and Shadowblade). Item level is the defeated encounter's level +2, capped by the existing equipment cap, so later drops scale under the normal damage, defense and affix rules. Higher-level pieces can have higher level requirements.

Bonuses accumulate at **3 pieces**, **6 pieces** and the **full collection**. Duplicate copies of one base never count twice. Removing a piece immediately updates the active bonuses.

At three pieces: Knight collections give +10% Defense and +8% maximum health; Ranger collections give +12% projectile damage and +25 Accuracy; Mage collections give +10% maximum Mana and +8% cast speed; Shadowblade collections give +8% attack speed and +12% Evasion. At six pieces, each set adds +12% damage and +6% resistance for its listed element.

## Collections

| Set | Suggested class | Weapon | Element | Pieces | Full-set effect |
| --- | --- | --- | --- | ---: | --- |
| Dragonforge | Knight | Axe | Fire | 14 | Hits have a 15% chance to ignite enemies. |
| Truth of Raikuru | Ranger | Crossbow | Lightning | 13 | Critical hits chain 30% of their damage as lightning. |
| Crimson Glory | Knight | Sword | Fire | 14 | Blocks release a 60% weapon-damage shockwave (1 s cooldown). |
| Grievance of the Fairy | Ranger | Bow | Earth | 13 | Kills restore 2.5% of maximum health. |
| Wailing Mistress | Mage | Staff | Dark | 13 | Spell hits restore 1.5 Mana. |
| Winter Court | Mage | Wand | Ice | 14 | Enemies that hit you are Chilled. |
| Sunken Crown | Knight | Spear | Water | 13 | Take 15% less damage while below 35% health. |
| Thunder Abbot | Mage | Staff | Lightning | 13 | Chain Lightning gains 2 extra jumps against Wet targets. |
| Ashfall Pilgrim | Mage | Wand | Fire | 14 | Fire hits spread Burning from burning targets to nearby foes. |
| Starfall Hunter | Ranger | Crossbow | Light | 13 | Critical hits reduce skill cooldowns by 0.25 seconds. |
| Gale Nomad | Ranger | Bow | Wind | 13 | Dodging grants 18% more movement speed for 2 seconds. |
| Obsidian Oath | Knight | Greatsword | Dark | 13 | Every fifth attack releases a staggering radiant shockwave. |
| Pale Requiem | Shadowblade | Dagger | Ice | 14 | Critical hits restore 2.5% of maximum health. |
| Serpent Veil | Shadowblade | Claw | Earth | 14 | Evading an attack restores 4 Mana. |
| Eclipse Dancer | Shadowblade | Dagger | Dark | 14 | Dodging leaves a lightning trail that Shocks enemies. |
The full-set effects use existing combat behaviors. Individual pieces still roll normal Master affixes; a full collection does not grant every set's effect at once.

## Appearance (BH-022)

Every collection was rebuilt as fitted, textured regalia in Blender (`tools/blender/items/boss_regalia.py`). Each piece is
modelled around the standard hero skeleton, so one model is both the worn piece and the dropped item:

- Knights wear closed great helms, engraved cuirasses with gorgets and fauld lames, layered pauldrons that move with the
  upper arms, mail skirts and tassets on the thighs, gauntlets with plated hands, greaves with knee cops and sabatons.
- Rangers wear sallets or circlets, riveted brigandines with a baldric, spaulders, leather tassets and split cloaks.
- Mages wear hoods, crowns or a pilgrim's hat, a soft mantle over a bodice, robes with front and back panels and
  bell sleeves.
- Shadowblades wear hoods (or a cobra's hood), fitted harnesses with crossed straps, an asymmetric pauldron and scarves.
- Each set has its own crest and emblem (dragon, storm halo, sunburst, leaf wings, tears, ice crown, trident and coral,
  twin orbiting rings, flame, stars, feathers, obsidian shards, antlers, serpent, eclipse), repeated on the chest,
  belt, shield, signet, seal, pendant and brooch.
- Materials use the legend texture sets (engraved plate, dragon scale, mail, worn leather, storm wool, bone) through a
  box-projected UV map; gems and glows keep their emission.

Pauldrons, hand plates, sabatons and tassets are separate parts that follow their own bones. The seven shields carry the
set emblem in relief. Icons are rendered with the same studio lighting and backdrop as all other 3D item icons.

Showcase: `output/pdf/Beyond-Heroes-Boss-Collections.pdf` (`python tools/create_boss_sets_pdf.py`).

## Verification

The dedicated `test_boss_sets.gd` suite checks complete legal equipment, all bonus thresholds, saving, exact level eligibility, repeatable encounters, one-piece reward bundles, ownership sources and exclusion from generic rewards. A seeded 10,000-drop sample checks that all sets remain possible and that collection weighting favors missing pieces without preventing duplicates. `test_bh022.gd` checks that every piece has a model and icon, that worn parts ride the arm, hand, foot and thigh bones, and that the textured palettes apply. Numerical simulation does not certify visual quality or frame rate.
