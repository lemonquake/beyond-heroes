# hollow_soldier (builder A)

- GLB: `game/assets/characters/hollow_soldier.glb`, module `tools/blender/characters/enemy_hollow_soldier.py`
- Standing height: **1.82 m** (sole to kettle-helm top; standard 1.8 m skeleton, `proportions()`); suggested `model_scale` 1.0
- Tris: 9,230 (fodder budget 6k–12k)
- Materials (`__hollow_soldier`): BH_Bone, BH_Rust, BH_DarkSteel (verdigris iron), BH_Cloth_Primary (rotten crimson), BH_Leather, BH_Shadow, BH_Emissive (teal eyes)
- Clips: base enemy set (42) + `sword_1 sword_2 sword_heavy`; idle stance `idle_1h`
- Distinctive: full skeleton (skull with agape jaw, vertebrae, ribcage, pelvis, radius/ulna); surcoat torn off the left chest so ribs and spine show; tattered hem; dented kettle helm tipped back; one rusted pauldron (left), right shoulder bare bone; right leather bracer; rotten boots; notched, bent-tip rusty arming sword in the right fist; teal glow in the sockets.
- Evidence: `hollow_soldier_rest_iso.png`, `hollow_soldier_clips.png` (idle_1h, sword_1, sword_heavy, death_crumple), `hollow_soldier_closeup.png`
- Notes / known issues:
  - The sword is weighted to `weapon.R`; `finish_mesh` turns `use_deform` on for the weapon sockets (they are non-deform in bh_skeleton), otherwise the sword stays in T-pose.
  - Eye glow is small and sits under the helm brim: clearly visible in the front/close views; at the zoomed gameplay-angle render it is barely readable.
  - Surcoat panels are skinned (hips -> thighs blend); some cloth/leg interpenetration in wide lunges.
