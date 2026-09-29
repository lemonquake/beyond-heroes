# bh-018 contract — socket crystals: 32 item models + 32 icons

Beyond Heroes gets a socketing system. Crystals are set into equipment sockets. There are 8 families × 4 grades =
32 items. The user asked for **"unique epic icons"** for every one — each icon must be instantly distinguishable
(family by colour + motif, grade by form + size + ornament), rich, glowing, jewel-like. Put real effort into these.

## Item ids (exactly these): `<family>_<grade>`
Families: `ember` (fire), `aqua` (water), `nova` (starlight), `thundra` (lightning), `vipera` (poison),
`bloodrift` (lifesteal), `essencerift` (manasteal), `aetherift` (rare, prismatic, the strongest).
Grades: `fragment` < `shard` < `crystalline` < `orbital`. Display names: "Ember Fragment", "Ember Shard",
"Ember Crystalline", "Ember Orbital", ... (e.g. `aetherift_orbital` = "Aetherift Orbital").

## Visual language
Grade = form (same across families):
- **Fragment** — a single rough, broken chip of crystal: jagged, irregular, small, one or two fracture planes, dull edges.
- **Shard** — a clean, elongated double-terminated crystal spike (hexagonal prism with pointed ends), bright facets.
- **Crystalline** — a cluster of 4–6 faceted crystals of varied height growing from a small rock/geode base; inner glow.
- **Orbital** — a polished, faceted gem-sphere (or cut brilliant) with the family's core light inside, circled by 1–2
  thin orbiting rings and 3–5 tiny satellite gems — the "orbit". The most ornate; clearly the top grade.

Family = colour + inner motif (visible in the icon at 64 px):
| family | colours | inner motif / accent |
|---|---|---|
| ember | deep red → orange → yellow-white core | a flame tongue inside, ember specks |
| aqua | deep sea blue → cyan | a water droplet / bubbles inside, wave ripple |
| nova | white-gold, pale yellow | a four/eight-point star burst inside, radiant rays |
| thundra | electric yellow with violet edges | a forked lightning vein through the crystal |
| vipera | venom green, black-green | a serpent-eye slit / fang, dripping venom bead |
| bloodrift | dark crimson, near-black | a jagged dark rift crack glowing red, blood drop |
| essencerift | azure-violet (mana) | a rift crack glowing blue-violet, swirling motes |
| aetherift | iridescent prismatic cyan↔magenta↔gold | a rift of white light, rainbow facets, tiny halo |

## Deliverables
1. Models: `game/assets/items/<id>.glb` — built in the item pipeline (`tools/blender/items/`: read `README.md`,
   `item_kit.py`, `item_goods.py`; palette materials `BH_<base>__it_<key>` keep their colours and soft emission in game).
   Stands on its base at z = 0, largest dimension 0.18 (fragment) .. 0.32 m (orbital); ≤ 3k triangles each; add them in a
   new file `tools/blender/items/item_crystals.py` and hook it into `build_items.py` the same way the other registries are.
2. Icons: `game/assets/ui/icons/crystals/<id>.png`, **256 × 256**, transparent or dark-framed like the game's existing
   item icons (see `game/assets/ui/icons/items3d/*.png` and `icons_post.py`), but "epic": dramatic rim light, the
   crystal's own glow bloom, a soft halo in the family colour behind it, a few sparkles; Orbital icons may break the
   frame with their rings. Render with EEVEE/Cycles from the models (preferred) and post-process in Python/PIL.
3. A contact sheet of all 32 icons (8 rows × 4 columns, family per row) at
   `work/lemondev/bh-018/evidence/crystals/crystal_icons_sheet.png`, and a sheet of model renders.
4. Blender 5.2 at `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`; system Python 3 with PIL/numpy.
   Do not edit game code (`game/src/**`); the Orchestrator wires the items into the game.
