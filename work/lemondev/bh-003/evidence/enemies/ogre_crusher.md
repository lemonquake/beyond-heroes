# ogre_crusher (Builder C)

- Source: `tools/blender/characters/enemy_ogre_crusher.py`
- GLB: `game/assets/characters/ogre_crusher.glb` (exported with `build.py -- ogre_crusher`; "clip lengths verified (46 clips)")
- Standing height: **2.98 m**, modelled at true size (use model_scale 1.0)
- Triangles: **7,570**. This is under the 10k–16k brute budget: the silhouette is made of big shapes and nothing more was needed.
- Materials (`__ogre_crusher`): BH_Skin (pale grey-olive hide), BH_Flesh (lip, scars), BH_Hair (patchy tufts), BH_Rust (collar, chain, shackles), BH_DarkSteel (club bands and spikes, collar studs), BH_Wood (club), BH_Cloth_Primary (loincloth), BH_Leather (rope belt, club grips), BH_Bone (teeth, claws), BH_Shadow, BH_Emissive (dull small eyes)
- Clips: base set plus `gs_1 boss_slam cast_heavy boss_roar` (idle stance: `idle_2h`)
- Features: huge pot belly, hunched upper back, a tiny head sunk forward between the shoulders, an underbite with four upward teeth, a broken iron slave collar (open at the right front) with a chain hanging down the belly, iron shackle cuffs with broken chain stubs on both wrists, a loincloth on a rope belt, huge three-toed bare feet, and arms whose hands reach the knees. The tree-trunk club (1.58 m, 3 iron bands, 7 spikes, branch stubs, a two-hand handle down to -0.62 m) is rigid to `weapon.R`.
- Evidence: `ogre_crusher_rest_iso.png`, `ogre_crusher_clips.png` (idle_2h, walk, boss_slam, death_crumple)
- Known issues:
  - In `walk` the long arm swing brings the club head close to the ground and it may graze it at the back of the swing.
  - The shared animations were made for human proportions. With the ogre's arm ratio (x2.3) the attacks read as heavy swings; I checked `boss_slam` and `gs_1` in previews.
