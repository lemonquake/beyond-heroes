# Clockwork Sentry (`clockwork_sentry`)
- Module `tools/blender/characters/enemy_clockwork_sentry.py` (+ shared `kit_e_orrery.py`); GLB `game/assets/characters/clockwork_sentry.glb` (+ `.glb.import`, necromancer settings, no uid)
- 16002 tris; height 1.96 m to the head finial (~1.9 m body). 45 clips = 42 enemy base + `bow_release bow_1 sword_1`.
- Materials (`__clockwork_sentry`): BH_Bronze polished brass, BH_Horn tarnished brass, BH_DarkSteel iron, BH_Gold rivets/hubs, BH_Steel bayonet, BH_Shadow recesses, BH_Emissive violet-white (0.75, 0.55, 1.0) lens eye, chest gear core, crossbow string + bolt head.
- Distinct: riveted barrel torso with a round window onto a glowing gear core, one big lens eye, three back exhaust stacks; the LEFT forearm is a crossbow (weapon.L: lock, tiller, brass prod, glowing string, loaded bolt; no left hand) that points at the target in bow_1 / bow_release; bayonet in the right hand (weapon.R) for sword_1.
- Construct: every piece rigid to one bone, iron ball joints cover the gaps (no skin stretch).
- Build log: `logs/build_clockwork_sentry.log`. Evidence: `clockwork_sentry_rest_iso.png`, `clockwork_sentry_clips.png`, `godot_check.txt`.
- Limitations: the bow clips' right hand "draws a string" in the air (reads as cranking); idle stance should be `idle_bow`.
