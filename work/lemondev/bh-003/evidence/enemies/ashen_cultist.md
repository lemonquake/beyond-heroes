# ashen_cultist

- GLB: `game/assets/characters/ashen_cultist.glb` (module `enemy_ashen_cultist.py`)
- Standing height: **1.77 m** (hood peak); `model_scale` 1.0.
- Triangles: 10,892 (a little above the 6-12k fodder midpoint, inside budget).
- Materials (`__ashen_cultist`): BH_Cloth_Primary (ash-grey robe), BH_Cloth_Secondary (ember-orange trim), BH_Bone (ceramic mask), BH_Horn (prayer papers), BH_Ichor (soot, charred wraps, mask crack), BH_Leather (rope, boots), BH_Skin, BH_Shadow (hood interior), BH_Emissive (orange embers: brazier, mask eyes, cracks in the charred hand), BH_DarkSteel (brazier cage), BH_Wood.
- Clips: base set + `cast_quick cast_area` (idle `idle_staff`).
- Features: ankle-length robe (four leg-weighted panels, ragged ember-trimmed hem), ember stole stripes down the front, deep hood with orange edge trim, cracked pale ash-mask with ember eye-glints and a mouth slit, rope belt with five cords of scorched paper prayers (two more hang from the hood at the chest), wide bell sleeves, charred and bandaged left hand with ember cracks, 1.2 m ritual staff with an iron brazier cage of glowing coals and a flame tongue.
- Weapons are mesh parts rigidly weighted to `weapon.R`/`weapon.L` (socket mapping GLB (x,y,z) -> bone (x,z,-y), same as `preview_chars.attach`). The module's `finish_mesh` hook sets `use_deform=True` on the two weapon bones (they are in `bh_skeleton.DEFORM_EXCLUDE`; without it Blender leaves weapon vertices in the T-pose). Verified in the re-imported GLB for the cutthroat: weapon.R / weapon.L vertex groups present.
- Evidence: `ashen_cultist_rest_iso.png`, `ashen_cultist_clips.png` (idle_staff, cast_quick, cast_area, death_crumple), `ashen_cultist_closeup_idle_staff.png`.
- Known issues: the library's cast clips hold the weapon hand low, so the brazier points down or sideways while casting (it reads as a gesture, not a bug). The front robe panels have a small centre gap that shows the dark trousers in wide strides. The robe/hood helpers in this file are imported by `enemy_ashen_acolyte.py`.
