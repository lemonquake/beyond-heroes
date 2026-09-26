# ashen_acolyte

- GLB: `game/assets/characters/ashen_acolyte.glb` (module `enemy_ashen_acolyte.py`)
- Standing height: **1.70 m** (bare head); `model_scale` 1.0.
- Triangles: 8,432.
- Materials (`__ashen_acolyte`): BH_Cloth_Primary (pale ash robe), BH_Cloth_Secondary (red sash, hem, sigils), BH_Horn (stole, book pages), BH_Bone (ash face paint), BH_Ichor (eye band, soot stroke), BH_Leather (book cover, sandal wraps), BH_Skin, BH_Shadow, BH_Bronze (censer), BH_DarkSteel (chain), BH_Emissive (ember vents/coal of the censer).
- Clips: base set + `cast_quick cast_area cast_weapon` (idle `idle_staff`).
- Extra bone: `censer` (child of `hand.R`, head at the right grip). `secondary()` keeps the chain and censer hanging with gravity, swings them back against the hand's horizontal velocity (up to 40 deg), and blends to rigid-with-the-hand when the hand is below ~0.5 m, so it lies on the ground in deaths instead of pointing through the floor. Verified in cast_quick, cast_weapon, run and both death_crumple views.
- Features (reads as "support" next to the cultist): lighter and slimmer (narrower torso and shoulders), paler robe, no hood, shaved head with an ash-white painted upper face, black eye band and a soot stroke over the crown, red waist sash with long tails, pale stole with red sigils, bronze censer on a 0.34 m chain (right hand), hymn-book held by the spine (left hand).
- Weapons are mesh parts rigidly weighted to `weapon.R`/`weapon.L` (socket mapping GLB (x,y,z) -> bone (x,z,-y), same as `preview_chars.attach`). The module's `finish_mesh` hook sets `use_deform=True` on the two weapon bones (they are in `bh_skeleton.DEFORM_EXCLUDE`; without it Blender leaves weapon vertices in the T-pose). Verified in the re-imported GLB for the cutthroat: weapon.R / weapon.L vertex groups present.
- Evidence: `ashen_acolyte_rest_iso.png`, `ashen_acolyte_clips.png` (idle_staff, cast_quick, cast_weapon, run, death_crumple), `ashen_acolyte_closeup_idle_staff.png`.
- Known issues: the censer can clip the robe or legs in some frames because it is a single rigid bone (no collision). The face paint is subtle in the Workbench preview.
