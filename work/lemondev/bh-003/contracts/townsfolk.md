# Contract — townsfolk models (builder D)

Read first: `docs/LORE.md` (sections 5, 6, 8), `tools/blender/characters/README.md`, `char_mage.py` / `char_knight.py`
(complete DSL examples), `bh_body.py`, `bh_mesh.py`, `bh_skeleton.py`, `bh_materials.py`, and
`work/lemondev/bh-003/contracts/enemies.md` (same module interface and export/preview commands).

Today every townsperson is either the armoured knight or the robed mage model with a tint — a blacksmith in full
plate. Build a set of **civilian body models** for the people of Malasugue (a warm, weathered fishing town on a
tropical-temperate island; see LORE §6 and §8). Each model is reused by several NPCs, recoloured by the game.

## Module interface (per model) — `tools/blender/characters/town_<id>.py`

- `PROPS`, `PALETTE = "town_<id>"`, `PALETTE_COLORS` (skin, hair, leather, metal, accessories), `build(body)`.
- `TINTABLE = ("BH_Cloth_Primary",)` — the main garment uses `BH_Cloth_Primary` and is exported **without** the
  palette suffix, so each NPC can recolour it (NPC `tint`). Make that garment the biggest colour area. Everything else
  uses palette colours.
- `CLIPS_ONLY = ["idle", "idle_look", "idle_adjust", "interact_talk", "walk", "interact_pickup"]` — townsfolk export
  only these.
- No weapons in the hands (they are civilians), unless a prop is part of the character (a smith's hammer hanging from
  the belt, a walking staff held in the right hand is fine — then weight it to `weapon.R` and check `interact_talk`).
- Export: `python3 build.py -- <id>` → `game/assets/characters/<id>.glb`. Preview with
  `python3 preview_enemy.py <id> --iso` and `--clips idle,interact_talk --frames 0,0.5` and look at them.
- Triangles: 5k–10k each. Faces are seen from the dialogue camera distance only as silhouettes: give each model a
  strong silhouette (hat, apron, shawl, coat cut, hair).

## The set (id — look — used by)

| id | Look | Used by (orchestrator assigns) |
|---|---|---|
| `town_elder` | Elderly woman, stooped a little, layered shawl over a long dress, long grey braid, walking staff (right hand), shell necklace | Elder Maelis |
| `town_scholar` | Robed man with a short cape, spectacles, satchel of scrolls and a book at the hip, neat beard | Archivist Oren Vale, Keeper Thadric Moll, Aurand Quell |
| `town_smith` | Broad, muscular, bald with a thick beard, bare forearms, heavy leather apron, gloves, hammer and tongs hanging from the belt | Brannoc, Dax Harrowby |
| `town_matron` | Woman in a working dress with an apron, sleeves rolled, headscarf, keys at the belt | Hesta Brindle, Tessaly Grane, Ilvena Hald |
| `town_fisher` | Weathered old man, oilskin sou'wester rain hat, rolled trousers, open vest, a coiled net over one shoulder, bare feet or sandals | Old Marrow |
| `town_merchant` | Portly trader in a vest and sash, rolled cap, coin purse and ledger at the belt | Tovin, Lio Sanvar (younger tint) |
| `town_officer` | Guild officer: long coat over a light breastplate, sash across the chest, short cape, gloves, a sheathed sword at the hip (scabbard on `hips`) | Commander Rhea Talvanne, Venna Kail |
| `town_bard` | Lean young man with a feathered cap, doublet, lute slung on the back, bright scarf | Fennick Arlow |
| `town_traveler` | Road-worn woman in a hooded travel cloak with a pack and bedroll, wrapped boots, scarf (a refugee from Emberhal) | Zerin Ven |

Female/male builds differ through `PROPS` (shoulder width, hip width, height) and mesh shaping; keep them respectful
and period-appropriate (no exaggerated anatomy).

## Evidence

PNG sheets into `work/lemondev/bh-003/evidence/townsfolk/`, and one `README.md` there listing each model: height, tris,
tintable area, notes.
