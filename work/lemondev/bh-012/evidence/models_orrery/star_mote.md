# Starmote (`star_mote`, floating)
- Script `tools/blender/creatures/build_star_mote.py` (wisp convention, imports kit_e_orrery); GLB `game/assets/characters/star_mote.glb` (+ `.glb.import` from aether_wisp)
- 6200 tris: core 1352, ring_1 1008, ring_2 1432, ring_3 1352, ribbons 1056. ~1.1 m across (ring radii 0.32 / 0.43 / 0.54), ribbons hang to -0.85 m. No armature, no clips.
- Nodes: `core` (violet-white faceted star crystal in a brass three-hoop cage), `ring_1..3` (thin brass orrery rings in local XY, tilts (22,0) / (-14,32) / (38,-26) deg on the node transforms; planet beads: starglass, tarnished-brass planet with its own gold ring, a tiny glowing moon), `ribbons` (four trailing star-dust strands of sparks).
- Materials (`__star_mote`): BH_Emissive star/sparks, BH_Bronze, BH_Horn, BH_Gold, BH_Stone starglass, BH_Aether pale moon glow.
- Evidence: `star_mote_rest_iso.png` (3 close views + gameplay cam 16 / 22 m, 3x zoom crops), `logs/build_star_mote.log`, `godot_check.txt`.
- Limitations: character_visual.gd's floating OmniLight is hard-coded aether cyan; a violet light (0.75, 0.55, 1.0) would match this model.
