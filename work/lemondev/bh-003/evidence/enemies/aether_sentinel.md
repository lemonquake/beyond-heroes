# aether_sentinel (builder A)

- GLB: `game/assets/characters/aether_sentinel.glb`, module `enemy_aether_sentinel.py`
- Standing height: **2.14 m** at model scale to the bronze crest (head block top ~2.04 m; skeleton `proportions(2.0/1.8)`); brief says game x1.25
- Tris: 8,300 (below the elite 10k–16k band on purpose: big blocky shapes, no small detail; can be densified if the orchestrator wants the band met)
- Materials (`__aether_sentinel`): BH_Stone, BH_Bronze (verdigris-dulled), BH_Aether (core, seams, visor, spine column), BH_Wood (maul haft), BH_Shadow
- Clips: base set + `gs_1 boss_slam cast_heavy`; idle stance `idle_shield`
- Distinctive: floating stone torso blocks (pelvis / abdomen / chest, each on its own bone, bronze bands) with gaps showing a cyan Aether spine column; glowing Aether core in a bronze ring on the chest with radiating seams; faceless stone head with a single glowing visor slit and bronze crest fin; boulder pauldrons with Aether lines; pillar limbs with bronze joint balls and rings, Aether seams on forearms/thighs/shins; stone fists; stone slab shield with bronze frame and Aether rune on `weapon.L`; bronze-headed maul on `weapon.R`.
- Evidence: `aether_sentinel_rest_iso.png`, `aether_sentinel_clips.png` (idle_shield, gs_1, boss_slam, death_crumple), `aether_sentinel_closeup.png`
- Known issues: `gs_1` and `boss_slam` are two-handed library clips, so the left hand (with the slab shield) joins the maul grip: the shield swings with the strike and is raised overhead in boss_slam. Reads as a shield-bash/slam but is not physically clean. A one-handed maul clip set would fix it (library change, not mine).
