# The Astrarch (`astrarch`, boss)
- Module `tools/blender/characters/enemy_astrarch.py`; GLB `game/assets/characters/astrarch.glb` (+ `.glb.import`)
- 22244 tris (boss budget 35k). Authored ~2.45 m to the crown tip, 2.84 m to the top of the halo ring (game scales ~2x). 51 clips = base + `staff_1 staff_heavy cast_heavy cast_area cast_ultimate cast_channel boss_slam boss_sweep boss_summon boss_roar`.
- Materials (`__astrarch`): BH_Bronze / BH_Horn brass, BH_DarkSteel iron, BH_Gold crown + studs, BH_Stone starglass planet, BH_Emissive violet lens / ring edges / moon, BH_WeakPoint white-gold star core (chest cage centre, local ~(0, 0, 1.70) m authored = 1.33 std x 1.278), BH_Aether white-gold sceptre sun.
- Distinct: open armillary cage torso around a blazing star core, crowned lens head, two big orrery halo rings behind the back (rigid on chest, violet-lit inner edges, planets + glowing moon), segmented brass arms with ring pauldrons, tall sun sceptre (weapon.R).
- Evidence: `astrarch_rest_iso.png` (gameplay cam: halo + core read), `astrarch_clips.png`, `logs/build_astrarch.log`, `godot_check.txt`.
- Limitations: the halo follows the chest, so it tilts flat over the body in boss_slam / cast_ultimate crouches and dips into the floor in deaths; skirt plates are blended hips/thigh.
