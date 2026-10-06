# Fabled Arms and the Item Summoner (bh-039)

## Fabled Arms

Fifty-four named weapons, Legendary to Primordial, each with its own model, icon, lore and signature strike.

| Tier | Arms | Level | Strike chance | Rest between strikes | Strength (share of the hit) |
|---|---|---|---|---|---|
| Legendary | 10 | 35 | 10% | 1.4 s | 80% |
| Aether | 8 | 50 | 12% | 1.25 s | 100% |
| Cosmic | 8 | 70 | 13% | 1.1 s | 120% |
| Divine | 10 | 80 | 15% | 1.0 s | 140% |
| Eternal | 8 | 90 | 15% | 1.0 s | 140% |
| Primordial | 10 | 100 | 16% | 0.9 s | 170% |

Each strike kind also scales the strength (`FabledProcs.KINDS`). The lower tiers share a pool of strikes in their own
colours: burst, wave, spikes, orbs, chain, meteor, vortex, blades, comet and echo. Every Divine and Primordial arm has
a strike of its own:

- **Divine:** seraph wings that sweep shut and heal, a descending halo, a lance of dawn, a choir of bells that stuns,
  a ring of holy swords, a storm of feathers, a dawn pillar, a sanctuary, an aurora veil, and scales of penance
  (stronger the more wounded the target).
- **Primordial:** a magma fissure, the first serpent coiling up, a titan's fist from the ground, primeval roots that
  bind, a meteor swarm, a tidal maw, an obsidian burst, an ashen tempest, dragon breath, and a genesis bloom that heals.

Held arms carry moving pieces (`FabledFx.held`): halos, wings, orbiting stones and shards, serpent coils, feathers,
leaves, embers, drips, sun and rune discs. The Cosmic and higher arms also get their tier's Ascendant light.

**Where they drop:** Legendary and Aether arms are uniques (elite and boss special rolls). A Cosmic-or-better Ascendant
weapon drop is one of the tier's Fabled arms half of the time.

**Files:**
- Data: `game/src/data/data_fabled.gd`
- Strikes: `game/src/combat/fabled_procs.gd`
- Effects: `game/src/vfx/fabled_fx.gd`
- Models and icons: `tools/blender/items/fabled_arms.py`

To rebuild the models and icons:

```
blender -b --factory-startup --python tools/blender/items/fabled_arms.py -- models icons
python tools/blender/items/fabled_arms.py post
```

Contact sheets are in `output/bh-039/fabled_<tier>.png`.

## Item Summoner (Debug console, Items page)

**Filters:**
- Category, weapon type and source chips (Ordinary, Uniques, Set pieces, Ascendant, Fabled Arms, Story).
- Class, element, native rarity and level range.
- A word search over names, ids, powers and lore.

The list shows every match, with icons and rarity colours. Click an item to preview it; double-click to summon it.

**Forge:**
- **Rarity:** any of the 14 tiers, applied exactly. A Primordial iron sword is Primordial and carries the Eruption
  power. Picking a base with a rarity of its own selects that rarity first.
- Item level, quality, sockets with a crystal to fill them, and count.
- Up to three chosen enchantments and three chosen powers.
- Perfect rolls, Unbound, Equip at once and Lock.
- **Preview:** the card shows the exact item Summon gives. Reroll draws another.

**Shortcuts:**
- Full Gear for My Class.
- Every Weapon Type.
- Random Fabled Arm, or All Fabled of This Rarity.
- Strike Test fires the picked arm's strike at the nearest monster.
- Recent summons can be clicked to reselect them.

**Generator change:** `ItemGenerator.generate(..., force := true)` is used only by the summoner. Drops still never make
Ascendant plain bases.
