# Astral Duelist (`astral_duelist`)
- Module `tools/blender/characters/enemy_astral_duelist.py`; GLB `game/assets/characters/astral_duelist.glb` (+ `.glb.import`)
- 9072 tris; height 1.94 m (crest). 47 clips = base + `sword_1 sword_2 sword_3 sword_heavy dagger_heavy`.
- Materials (`__astral_duelist`): BH_Stone starglass body (dark glass, faint emission) with ~180 BH_Emissive star flecks, BH_Steel silver half-armour + filigree, BH_Aether mirror face plate (pale silver, faint violet glow; unknown base name so the game keeps its PBR), BH_Cloth_Primary midnight cape, BH_Cloth_Secondary violet hem, BH_Gold accents, BH_Emissive rapier edges.
- Distinct: lean dark glass body under asymmetric silver armour (left breastplate + tall pauldron), featureless pale mirror face, short midnight cape, long thin rapier with a basket hilt and violet glowing edges.
- Skinned glass body (smooth seg weights), armour rigid, cape on the shared cloth weights (chest -> spine -> hips/thighs).
- Evidence: `astral_duelist_rest_iso.png`, `astral_duelist_clips.png`, `logs/build_astral_duelist.log`, `godot_check.txt`.
- Limitations: `dagger_heavy` (lunge) uses the dagger hand pose, so the rapier points down/back during the dash; cape stretches a little in run.
