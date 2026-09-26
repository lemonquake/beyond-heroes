# goblin_skulker (Builder C)

- Source: `tools/blender/characters/enemy_goblin_skulker.py` (+ shared helpers `tools/blender/creatures/greenskin_kit.py`)
- GLB: `game/assets/characters/goblin_skulker.glb` (exported with `build.py -- goblin_skulker`; "clip lengths verified (45 clips)")
- Standing height: **1.12 m** (top of the helmet, rest bounds). Modelled at true size.
- Triangles: **6,638** (fodder budget 6k–12k)
- Materials (`__goblin_skulker`): BH_Skin (olive), BH_Flesh (dark mottling, inner ears), BH_Rust (helmet), BH_DarkSteel, BH_Steel (knife), BH_Cloth_Primary (loincloth), BH_Cloth_Secondary (loot sack, pot rags), BH_Leather, BH_Stone (fired-clay fire-pots), BH_Emissive (orange: rag flames + eyes), BH_Bone (claws, teeth), BH_Wood, BH_Shadow, BH_Gold (ear ring, loot candlestick)
- Clips: the 42-clip enemy base set plus `dagger_1 dagger_2 cast_quick` (idle stance: `idle_dagger`)
- Features: long arms (the hands hang near the knees), bowed legs (mesh bow of 4.5 cm at the knee), big bare clawed feet, huge sideways ears, long hooked nose, glowing eyes, an oversized dented kettle helmet tipped back, a loot sack on the back with its strap across the chest, three clay fire-pots with burning rags on the belt, a notched knife in the right hand (rigid to `weapon.R`)
- Proportions: `proportions(0.64, pelvis_h=0.50, head_len=0.19, upper_len=0.215, fore_len=0.205, …)`
- Evidence: `goblin_skulker_rest_iso.png`, `goblin_skulker_clips.png` (idle_dagger, walk, dagger_1, death_crumple)
- Known issues / notes:
  - The weapon sockets `weapon.L/R` are switched to deform in `finish_mesh` (the knife is weighted to `weapon.R`, as the contract asks). The Godot skin is unaffected.
  - At the iso camera the goblin reads as helmet, sack and ears; the face is too small to read at that distance.
  - Seams are visible where the arm and leg tubes meet the torso (low-poly joints); they are not visible at gameplay distance.
