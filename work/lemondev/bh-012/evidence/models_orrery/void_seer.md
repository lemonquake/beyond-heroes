# Void Seer (`void_seer`)
- Module `tools/blender/characters/enemy_void_seer.py`; GLB `game/assets/characters/void_seer.glb` (+ `.glb.import`)
- 12966 tris; height 1.96 m (hood peak). 47 clips = base (incl. `cast_channel`) + `staff_1 cast_quick cast_heavy cast_area blink`.
- Materials (`__void_seer`): BH_Cloth_Primary midnight robes, BH_Cloth_Secondary violet stole, BH_Bronze brass thread / astrolabes / telescope, BH_Horn tarnished brass, BH_Gold, BH_Leather dark gloves, BH_DarkSteel, BH_Shadow void in the hood, BH_Emissive lens-eye, constellation star nodes, staff star.
- Distinct: tall hooded astronomer, deep hood with nothing but void and one big glowing violet lens-eye (brass rimmed, lens-flare star), brass constellation embroidery on the stole, chest + belt astrolabes, telescope staff with an armillary head.
- Robes/hood from the ashen_cultist helpers (same deformation behaviour as necromancer/cultist).
- Evidence: `void_seer_rest_iso.png`, `void_seer_clips.png`, `logs/build_void_seer.log`, `godot_check.txt`.
- Limitations: robe hem stretch in deep crouches (cast_area) like the other robed casters; staff dips below ground when lying in deaths.
