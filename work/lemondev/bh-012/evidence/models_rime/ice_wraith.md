# Ice Wraith (`ice_wraith`)
- Script: `tools/blender/creatures/build_ice_wraith.py` -> `game/assets/characters/ice_wraith.glb` (+ `.glb.import`); static, no armature, no clips (wisp convention)
- Nodes: `core` 2.4k tris (frost veil hood open at the front, skull-like ice mask with 2 blue eye-lights + icicle fangs, ragged mantle, crown crystals), `ring_1/2/3` (9/11/7 icicle shards, radius 0.5/0.64/0.8 m, tilts (14,0)/(-12,28)/(32,-20) deg, every 3rd shard emissive), `ribbons` (6 tattered frost-cloth tails with icicle tips). Total 4216 tris.
- Size ~1.8 m: hood crest +0.6 m, ribbon tips about -1.15 m below the origin (= creature centre). At the game's 1.2 m hover the tails end just above the floor.
- Palette (`__ice_wraith`): pale frost veil BH_Cloth_Primary, deeper blue tails BH_Cloth_Secondary, ice BH_Stone (faint emission), BH_Shadow hood lining, BH_Emissive eyes/core (0.45,0.8,1.0 x9)
- Evidence: `ice_wraith_rest_iso.png` (4 views, mask close-up, gameplay cam 16/22 m; ground at -1.2 m), `logs/build_ice_wraith.log`
