# Skaldra, the Winter Crown (`winter_crown`, BOSS)
- Module: `tools/blender/characters/enemy_winter_crown.py` -> `game/assets/characters/winter_crown.glb` (+ `.glb.import`)
- Triangles 12862 (boss budget 35k); author height ~2.1 m to the head (K 1.16), icicle crown to ~2.45 m; game scales ~1.9x
- Clips (52): base set + `spear_1 spear_2 spear_heavy boss_sweep boss_slam cast_heavy cast_area cast_ultimate boss_summon boss_roar`
- Weapon: long glaive (silver haft, curved blue-ice blade with a glowing core, ice butt spike), rigid on weapon.R, ~2.35 m authored x1.16
- Palette (`__winter_crown`): pale ice-plate (BH_Steel), deep ice-blue gown (BH_Cloth_Primary), pale veil (BH_Cloth_Secondary), frost-white feathers (BH_Horn), porcelain mask (BH_Bone), glassy ice (BH_Stone), blue eye-lights / crown cores / glaive core (BH_Emissive x9)
- Distinct/readability: tall slender queen, sunburst crown of 13 icicle spikes (tallest at the brow, glowing cores), feather fan behind the head, long gown with a floor train, cracked porcelain mask (one crack leaks light), long glowing glaive.
- Evidence: `winter_crown_rest_iso.png` (idle_spear), `winter_crown_clips.png` (all 10 attack/cast clips + death_back), `logs/build_winter_crown.log`
- Limitations: gown train is hips/thigh weighted and lifts off / dips through the floor in crouches and deaths; glaive goes through the floor in boss_slam/cast_area crouches (shared library hand pose); feather fan is chest-rigid.
