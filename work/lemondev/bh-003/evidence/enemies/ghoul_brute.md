# ghoul_brute

- GLB: `game/assets/characters/ghoul_brute.glb` (module `enemy_ghoul_brute.py`)
- Standing height: **2.01 m** model (top of the head/hump); the contract suggests game `model_scale` ~1.35 (about 2.7 m in game).
- Triangles: 11,274 (brute budget 10-16k).
- Materials (`__ghoul_brute`): BH_Skin (grey-green), BH_Fur (grave-moss), BH_Flesh (swollen club flesh, split veins), BH_Bone (bone spurs, underbite teeth, fungus caps, claws, toenails), BH_Cloth_Primary (torn trousers), BH_Leather (rope belt), BH_Rust (cleaver), BH_Wood, BH_Shadow (mouth, sockets), BH_Emissive (tiny sickly-green eyes).
- Clips: base set + `axe_2 boss_slam boss_charge devour` (idle `idle_2h`).
- Proportions: scale 1.2, wide shoulders (0.225), longer arms, wide hips. The hunch is built in the mesh: a tall moss-covered hump behind the shoulders rises to head height, and the head and neck are pushed 0.17 m forward and 0.15 m down from the head bone.
- Features: barrel belly, moss clumps over the hump, shoulders and nape with pale fungus caps, low, forward-thrust head with a heavy brow, squashed nose, gaping underbite mouth with lower tusks and patchy tufts. The right forearm swells into a lumpy flesh club (on `weapon.R`) with nine bone spurs and knuckle bones. Clawed left fist, torn trousers with ragged hems above bare shins and feet, rope belt with a rusty cleaver on the left hip.
- Weapons are mesh parts rigidly weighted to `weapon.R`/`weapon.L` (socket mapping GLB (x,y,z) -> bone (x,z,-y), same as `preview_chars.attach`). The module's `finish_mesh` hook sets `use_deform=True` on the two weapon bones (they are in `bh_skeleton.DEFORM_EXCLUDE`; without it Blender leaves weapon vertices in the T-pose). Verified in the re-imported GLB for the cutthroat: weapon.R / weapon.L vertex groups present.
- Evidence: `ghoul_brute_rest_iso.png`, `ghoul_brute_clips.png` (idle_2h, axe_2, boss_slam, boss_charge, devour, death_crumple), `ghoul_brute_closeup_idle.png` (taken before the final moss/torso resolution bump, same shapes).
- Known issues: in `idle_2h` the left hand reaches to the club's grip point (library two-hand IK), so the left arm crosses the body. The head is offset from the head bone, so large head pitches swing it through a wider arc than on a standard humanoid.
