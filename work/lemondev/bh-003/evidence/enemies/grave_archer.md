# grave_archer (builder A)

- GLB: `game/assets/characters/grave_archer.glb`, module `enemy_grave_archer.py`
- Standing height: **1.89 m** to the hood point (skull top ~1.82 m; standard 1.8 m skeleton); suggested `model_scale` 1.0
- Tris: 9,090 (ranged budget 6k–12k)
- Materials (`__grave_archer`): BH_Bone, BH_Cloth_Primary (moss green), BH_Cloth_Secondary (sinew/string), BH_Leather, BH_Wood (arrow shafts), BH_Hair (black fletching), BH_DarkSteel, BH_Shadow, BH_Emissive (teal eyes)
- Clips: base set + `bow_release bow_draw_hold`; idle stance `idle_bow`
- Extra bones: `cape.1`, `cape.2` (knight cape layout) with the knight's secondary motion (hangs, flares with speed).
- Distinctive: lean skeleton, deep ragged moss-green hood with dark lining and trailing point, bare skull with the jaw hanging open, teal eyes; ragged capelet and long cloak; baldric across the bare ribcage; quiver on the back (over the right shoulder) with black-fletched arrows; bone-and-sinew longbow (knobbed bone limbs, sinew wraps, bone tips) in the left hand on `weapon.L`, string on the archer side; leather bracer on the bow arm; rag front skirt, leg wraps, boots.
- Evidence: `grave_archer_rest_iso.png`, `grave_archer_clips.png` (idle_bow, bow_draw_hold, bow_release, death_crumple), `grave_archer_closeup.png`
- Known issues: the bowstring is rigid mesh (does not follow the drawing hand); no arrow mesh in the hand (the game spawns the projectile); cloak can clip the legs in fast lunges (same as the knight's cape).
