# bh-042 asset sources (the Abyss)

Everything here is CC0. `sources.json` records every downloaded file (source, page, URL, date, size, SHA-256).
The large originals are not committed (see `.gitignore`); every script below fetches them again.

| Script | Does |
|---|---|
| `oga_fetch.py` | the OpenGameArt creatures into `oga/` (`previews/oga_scan.py` found them) |
| `ph_textures.py` | Poly Haven stone texture sets → `game/assets/textures/ph_*` |
| `ph_props.py fetch` / `blender -b -P ph_props.py -- convert` | Poly Haven props → `game/assets/environment/ph_*.glb` |
| `boss_specs.py` | writes `specs/rig_<id>.json` and `specs/conv_<id>.json` |
| `blender -b --factory-startup -P rig_to_hero.py -- specs/rig_<id>.json` | puts a creature on the hero skeleton (all 132 clips) → `out/<id>.glb` |
| `godot --headless --path game res://tests/tools/convert_creature.tscn -- --spec=specs/conv_<id>.json` | the game scene `game/assets/characters/bh042/<id>.scn` |
| `export_blend.py`, `export_skull.py` | the dragon (own clips) and the Weeping Shroud's skull |
| `render_poses.py`, `front.py`, `measure.py`, `sheet.py` | contact sheets and measured views (joint landmarks of unrigged meshes) |

Rejected along the way (in the bh-042 handoff): Quaternius Ultimate Monsters and the KayKit characters were too
cartoonish for the user; the free tier of Quaternius' Fantasy Outfits holds only rangers and peasants; the demon statue's
left arm is sculpted into its wing, so it could not be rigged cleanly.
