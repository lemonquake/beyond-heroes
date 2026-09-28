# Rime Weaver (`rime_weaver`)
- Script: `tools/blender/creatures/build_rime_weaver.py` -> `game/assets/characters/rime_weaver.glb` (+ `.glb.import`). Reuses build_broodmother's 8-leg rig/choreography by import (not edited) at S = 0.7: bones and all translation channels scaled in its own evaluate().
- 5734 tris, 43 bones, 15 clips; leg span ~1.8 m, abdomen top ~0.75 m. numpy-vs-Blender pose check 0.001 mm.
- Clips: generic set + `weaver_bite` 0.8 s hit [0.367,0.467], `weaver_spit` 1.2 s hit [0.6,0.667] (rear + spit; web projectile spawned by the game), `weaver_pounce` 1.4 s hit [0.8,0.9]. walk ground_speed 1.12, run 3.5, run_combat 3.22 m/s. Merged into creature_meta.json (weaver_* keys + models.rime_weaver only; other keys verified intact).
- Palette (`__rime_weaver`): pale faceted ice carapace/gem BH_Stone, deep-blue legs/underside BH_Horn, white frost spikes BH_Hair, blue eyes + gem girdle/seams/knee crystals BH_Emissive
- Evidence: `rime_weaver_rest_iso.png`, `rime_weaver_clips.png`, `logs/build_rime_weaver.log`
- Limitations: pounce leaps forward in place-and-return (same as broodmother); walk stance-foot slip max 7 mm/frame.
