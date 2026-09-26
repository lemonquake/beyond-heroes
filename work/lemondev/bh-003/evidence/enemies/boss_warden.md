# boss_warden — Morthar, the Hollow Warden (builder A)

- GLB: `game/assets/characters/boss_warden.glb`, module `enemy_boss_warden.py`
- Standing height: **2.29 m** at model scale to the horn tips (helm/crown top ~2.06 m; skeleton `proportions(2.0/1.8)`); brief says game x2.2
- Tris: 16,256 (boss budget <= 24k)
- Materials (`__boss_warden`): BH_Steel (tarnished), BH_DarkSteel, BH_Gold (aged trim), BH_Cloth_Primary (royal violet-black), BH_Leather, BH_Bone, BH_Shadow (cavity), BH_Emissive (violet: heart, eyes, helm crack, pauldron channels, sword runes), **BH_WeakPoint** (rune on the back plate, default contract colours kept so it stands out)
- Clips: base set + `boss_sweep boss_slam boss_charge cast_heavy boss_roar boss_summon`; idle stance `idle_2h`
- Extra bones: `cape.1`, `cape.2` (knight layout scaled x1.11). `secondary()` = knight cape logic + a gravity fold: when the lower cape would point upward (hips above shoulders, e.g. death_crumple), cape.2 folds down so the cape drapes over the body instead of standing up.
- Distinctive: gold-trimmed oath-plate breastplate split open down the front over a hollow cavity (dark, inner ribs, violet grave-light heart); great helm with violet eyes behind the slit and a glowing crack, gold crown (one point broken) with two tall swept horns and a central crest blade; big layered pauldrons with violet channels and spikes; faulds, mail skirt, torn tabard; cape torn in two halves hanging from the shoulders, the tear leaving the back rune bare; weak-point rune (ring + glyph in a gold setting) between the shoulder blades; huge dark greatsword with violet rune dashes on both flats in the right fist.
- Evidence: `boss_warden_rest_iso.png`, `boss_warden_clips.png` (idle_2h, boss_sweep, boss_slam, death_crumple), `boss_warden_closeup.png`, `boss_warden_cape_deaths.png` (death_crumple, death, idle_2h with the cape fold)
- Known issues: the back rune is smallish at gameplay distance (~0.2 m wide at model scale, ~0.5 m after x2.2); the cape halves can overlap it in the run/charge flare. Rune is weighted to `chest`.
