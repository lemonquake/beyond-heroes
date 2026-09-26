# bandit_cutthroat

- GLB: `game/assets/characters/bandit_cutthroat.glb` (module `tools/blender/characters/enemy_bandit_cutthroat.py`)
- Standing height: **1.76 m** (top of hair); model at true size, `model_scale` 1.0.
- Triangles: 8,814 (fodder budget 6-12k).
- Materials (`__bandit_cutthroat`): BH_Leather (jerkin), BH_Horn (light leather patches, bandolier, boot straps), BH_Cloth_Primary (faded red scarf), BH_Cloth_Secondary (shirt/trousers), BH_Skin, BH_Hair, BH_Bone (bandages), BH_Shadow (eye sockets, non-emissive), BH_Steel, BH_DarkSteel, BH_Wood.
- Clips: base enemy set + `dagger_1 dual_2 wand_1` (idle stance `idle_dagger`).
- Features: sleeveless patched jerkin with a laced V and split skirt, faded red scarf over nose/mouth with a knot and tails at the back, bandolier (left shoulder to right hip) holding five throwing knives, bare arms with spiral bandages on both forearms, leather bracer on the left, curved single-edged knife in the right fist and a short dagger in the left, belt with two pouches and an empty sheath.
- Weapons are mesh parts rigidly weighted to `weapon.R`/`weapon.L` (socket mapping GLB (x,y,z) -> bone (x,z,-y), same as `preview_chars.attach`). The module's `finish_mesh` hook sets `use_deform=True` on the two weapon bones (they are in `bh_skeleton.DEFORM_EXCLUDE`; without it Blender leaves weapon vertices in the T-pose). Verified in the re-imported GLB for the cutthroat: weapon.R / weapon.L vertex groups present.
- Evidence: `bandit_cutthroat_rest_iso.png`, `bandit_cutthroat_clips.png` (idle_dagger, dagger_1, dual_2, wand_1, death_crumple), `bandit_cutthroat_closeup_idle_dagger.png`.
- Known issues: the throwing knives on the bandolier are small and vanish at gameplay distance (the red scarf and the two blades carry the read). This file also holds Builder B's shared kit (`SB`, arms/legs/boots/head helpers); the other five Builder-B modules import it, so do not delete or rename it.
