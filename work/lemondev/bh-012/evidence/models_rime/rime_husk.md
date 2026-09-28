# Rimebound Husk (`rime_husk`)
- Module: `tools/blender/characters/enemy_rime_husk.py` (also holds the shared ice helpers) -> `game/assets/characters/rime_husk.glb` (+ `.glb.import`, same settings as the other enemies, uid/path left for Godot)
- Triangles 8780 (budget 20k); height ~1.8 m (K 1.0 standard skeleton); weapon rigid on weapon.R
- Clips (45): 42 shared enemy base clips + `sword_1 sword_2 sword_heavy` (hits from anim_meta.json)
- Palette (`__rime_husk`): blue-grey dead skin (BH_Skin), deep-blue frost-stiff rags (BH_Cloth_Primary/Secondary), glassy pale ice (BH_Stone, faint emission), frost-white hair (BH_Hair), old steel sword, faint blue eye-light (BH_Emissive 0.45,0.8,1.0 x5)
- Distinct from frost_revenant: no armour or helm; a gaunt bare corpse, asymmetric - left arm locked in faceted ice blocks, right leg sheathed in ice, a big ice crust with tall shards on the back, lank frozen hair strands, icicles from the jaw and both elbows, snapped sword continued by an ice spur.
- Evidence: `rime_husk_rest_iso.png` (T-pose, idle_1h 4 yaws, head close-ups, gameplay cam 16/22 m), `rime_husk_clips.png`, `logs/build_rime_husk.log`
- Build: `[rime_husk] mesh 8780 tris ... baked 45 actions ... clip lengths verified (45 clips) -> rime_husk.glb (2.8 MB)`
- Limitations: ice blocks are rigid per bone, so the left-elbow blocks interpenetrate on deep bends; icicles are rigid (point along the limb in some poses); loin panels stretch in run like other cloth-panel enemies.
