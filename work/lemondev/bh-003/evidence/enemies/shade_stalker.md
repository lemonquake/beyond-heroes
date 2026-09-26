# shade_stalker

- GLB: `game/assets/characters/shade_stalker.glb` (module `enemy_shade_stalker.py`)
- Standing height: **1.80 m** (hood peak); `model_scale` 1.0.
- Triangles: 8,448.
- Materials (`__shade_stalker`): BH_Shadow (smoke-black body and rags, faint violet emission 0.5), BH_Cloth_Primary (slightly lighter binding strips), BH_Cloth_Secondary (face wrap, hood lining), BH_Emissive (violet eye-slits, rune grooves on the blades), BH_Skin (grey fingers), BH_DarkSteel (blackened blades).
- Clips: base set + `dagger_heavy dagger_1` (idle `idle_dagger`).
- Proportions: very lean torso, long limbs (upper arm 0.31, forearm 0.30, hand 0.11, neck 0.14 x scale), narrow shoulders and hips.
- Features: body bound in spiral strips (torso, arms, legs), crossed chest binding, tight pointed hood with two glowing violet eye-slits and face bands, a hood tail down the back, twelve ragged strips hanging from the hips (leg-weighted), three trailing rags per forearm, long curved blackened daggers in both hands with violet rune grooves.
- Weapons are mesh parts rigidly weighted to `weapon.R`/`weapon.L` (socket mapping GLB (x,y,z) -> bone (x,z,-y), same as `preview_chars.attach`). The module's `finish_mesh` hook sets `use_deform=True` on the two weapon bones (they are in `bh_skeleton.DEFORM_EXCLUDE`; without it Blender leaves weapon vertices in the T-pose). Verified in the re-imported GLB for the cutthroat: weapon.R / weapon.L vertex groups present.
- Evidence: `shade_stalker_rest_iso.png`, `shade_stalker_clips.png` (idle_dagger, dagger_1, dagger_heavy, run, death_crumple).
- Known issues: the forearm rags are rigid to the forearm (no extra bones), so they stick out when the arm is raised instead of trailing. At gameplay distance it is a dark silhouette with small violet eyes (intended: "almost invisible until it strikes"); the orchestrator may want a runtime rim or VFX.
