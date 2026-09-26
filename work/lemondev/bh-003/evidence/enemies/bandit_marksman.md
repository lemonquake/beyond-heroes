# bandit_marksman

- GLB: `game/assets/characters/bandit_marksman.glb` (module `enemy_bandit_marksman.py`)
- Standing height: **1.75 m** (hat crown); `model_scale` 1.0.
- Triangles: 8,062.
- Materials (`__bandit_marksman`): BH_Cloth_Primary (green-brown cape/hood/mantle), BH_Cloth_Secondary (tunic), BH_Leather (hat, bracer, quiver, boots), BH_Horn (straps, hat band), BH_Fur (trousers), BH_Skin, BH_Hair, BH_Shadow, BH_Wood (bow, arrows), BH_Bone (fletching, hat feather), BH_DarkSteel, BH_Gold (bow riser bands).
- Clips: base set + `bow_release bow_draw_hold` (idle `idle_bow`).
- Extra bones: `cape.1`, `cape.2` (same layout and `secondary()` as the knight's cape; the knight's function is reused).
- Features: wide-brim leather hat with a pinched crown and feather, bearded face, green shoulder mantle, hood lying down behind the neck, back cape with a ragged hem, leather bracer on the bow arm, recurve bow (bh_weapons.bow, 12% longer) in the left fist, hip quiver on the right with five arrows, quiver strap across the chest.
- Weapons are mesh parts rigidly weighted to `weapon.R`/`weapon.L` (socket mapping GLB (x,y,z) -> bone (x,z,-y), same as `preview_chars.attach`). The module's `finish_mesh` hook sets `use_deform=True` on the two weapon bones (they are in `bh_skeleton.DEFORM_EXCLUDE`; without it Blender leaves weapon vertices in the T-pose). Verified in the re-imported GLB for the cutthroat: weapon.R / weapon.L vertex groups present.
- Evidence: `bandit_marksman_rest_iso.png`, `bandit_marksman_clips.png` (idle_bow, bow_draw_hold, bow_release, death_crumple), `bandit_marksman_closeup_idle_bow.png`.
- Known issues: no arrow in the drawing hand (the game can spawn an arrow projectile). The quiver is rigid to the hips and can touch the right thigh in wide strides.
