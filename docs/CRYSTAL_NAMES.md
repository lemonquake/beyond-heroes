# Crystal-infused names and socket visuals (BH-022)

Equipment with crystals set in its sockets is named after them: *Iron Longsword of the Nova Blast*. The rules live in
`game/src/core/items/crystal_names.gd` (`CrystalNames`).

## How the name is chosen

Each crystal adds its grade + 1 to its family's **power** in the piece (Fragment 1, Shard 2, Crystalline 3, Orbital 4).
Families are ranked by power; ties follow the crystal order Ember, Aqua, Nova, Thundra, Vipera, Bloodrift,
Essencerift, Aetherift.

| Crystals set | Suffix |
| --- | --- |
| one family | its own name; the tier is the best crystal's grade, raised by total power 3 / 6 / 10 |
| two families | the pair's hybrid name; *Grand* at combined power 4+, *Eternal* at 8+ |
| three families | the top pair's name with the third family's epithet: *of the Venomous Nova Blast* |
| four families | *of the Fourfold* + pair name |
| five to seven | *of the Prismatic* + pair name |

Empty sockets do not change a name. The crystal suffix replaces an affix suffix (*Flaming Sword of the Nova Blast*);
set pieces, uniques and named items add it after their name. Every combination of 1–7 families at every grade is
covered by `tests/unit/test_bh022.gd`.

### Single families (tier 0 → 3)

| Family | Tier 0 | Tier 1 | Tier 2 | Tier 3 |
| --- | --- | --- | --- | --- |
| Ember | of Embers | of the Burning | of the Blaze | of the Inferno |
| Aqua | of the Spring | of the Tide | of the Deep | of the Maelstrom |
| Nova | of Starlight | of the Nova | of the Dawnstar | of the Supernova |
| Thundra | of Sparks | of Thunder | of the Tempest | of the Storm Throne |
| Vipera | of Venom | of the Viper | of the Basilisk | of the Hydra |
| Bloodrift | of Leeching | of the Bloodletter | of the Crimson Rift | of the Blood Sovereign |
| Essencerift | of Whispers | of the Mindrift | of the Soul Siphon | of the Starved Void |
| Aetherift | of the Aether | of Riftlight | of the Worldtear | of the Firmament |

### Hybrids (all 28 pairs)

| | Aqua | Nova | Thundra | Vipera | Bloodrift | Essencerift | Aetherift |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Ember** | Scalding Tide | Nova Blast | Firestorm | Brimstone Fang | Blood Pyre | Soulfire | Phoenix Rift |
| **Aqua** | | Moontide | Stormsurge | Blackwater | Red Tide | Drowned Mind | Starlit Deep |
| **Nova** | | | Thunderstar | Plague Star | Blood Moon | Eclipse | Heavenfall |
| **Thundra** | | | | Venom Storm | Crimson Thunder | Mindstorm | Skyrend |
| **Vipera** | | | | | Blood Viper | Nightshade | Rift Serpent |
| **Bloodrift** | | | | | | Devourer | Bleeding Sky |
| **Essencerift** | | | | | | | Astral Mind |

Third-family epithets: Burning, Tidal, Radiant, Thundering, Venomous, Bloodthirsty, Whispering, Aetheric.

## What you see

* **Item cells and equipment slots** show a row of bronze socket bezels along the bottom (two rows above four
  sockets); each set crystal sits in its bezel, cut by grade (rough Fragment, long Shard, step-cut Crystalline,
  brilliant Orbital with a coloured halo). A piece holding crystals glows softly in their blended colour.
* **Tooltips** show the sockets as a strip, the infusion line (*Infused of the Grand Nova Blast*), and the name.
* **Held weapons** shed motes of the infusion colour along the blade, denser with more crystal power.

Sprites: `tools/ui_art/bh022_sockets.py` → `game/assets/ui/slots/socket_*.png`.
