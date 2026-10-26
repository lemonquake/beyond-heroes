# Hero bodies and bow motion

Ported on 2026-10-26 from the author's local Warriors of Aether project. The
source project is read only. `manifest.json` records source and output SHA-256,
triangle counts and embedded map sizes. `tools/port_hero_models.py` regenerates
the three GLBs. Geometry, skin weights, skeletons and all embedded clips are
unchanged; embedded images are limited to 1024 pixels and repacked as PNG.

| Beyond Heroes class | Source asset and author | License and changes already present in WOA |
| --- | --- | --- |
| Knight | Ser Emelrich, “Bulky Knight”, OptiCube (Arthur Krut), [source](https://sketchfab.com/3d-models/002a90cbf12941b792f9685546a7502c) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). White steel/cream cloth, axe removed, fitted and retargeted to the hero rig by the project author. 26,947 triangles. |
| Mage | Azrin, “Dark Fantasy Sorceress, Crystal Staff”, s8819296, [source](https://sketchfab.com/3d-models/a307ea3800d748c487d26235bb43ecc0) | CC BY 4.0. Red/black recolour, staff removed, fitted and retargeted by the project author. 52,000 triangles. |
| Shadowblade | Caziel, “Corrupted Fallen Priest - Dark Fantasy”, s8819296, [source](https://sketchfab.com/3d-models/1ab734d8c4464ae49d5b5091f3ea2afc) | CC BY 4.0. Fitted and retargeted by the project author. 40,000 triangles. |
| Hunter | Jayla / Blood Ranger, author-owned `assets/characters/hero/hero.glb`, source look/outfit/dyes in WOA `src/core/game_settings.gd` | Shared body is byte-identical to Beyond Heroes `assets/characters/hero.glb`. Source look, long crimson hair and leather outfit are constructed by `HeroModels.blood_ranger`. Existing fitted equipment meshes are reused. |

The 132 embedded hero animations and `hero_anims_fixed.res` / body collision
repairs are by the project author, retargeted in Warriors of Aether. The four
Blood Ranger bow clips (`bow_idle`, `bow_shoot`, `bow_hold`, `bow_loose`) are the
actual local WOA motion-capture resources, with the source hero's collision
corrections. WOA identifies its motion-capture library as Mixamo-derived. These
clips are private game assets, excluded from loose public Git distribution;
ship them only inside the game, consistent with the source project's handling.
`tests/tools/port_hero_animations.gd` extracts only these four clips from the
author's local source library. No paid-provider job or new download is used.

A clean checkout requires that private extraction before playing or exporting:

```powershell
& "<Godot console executable>" --headless --path "<Warriors of Aether project>" -s "<Beyond Heroes>/game/tests/tools/port_hero_animations.gd"
& "<Godot console executable>" --headless --editor --path "<Beyond Heroes>/game" --import
```

The extractor derives its destination from its own script path; `-- --out=<roles
directory>` can select another destination. It records the source library,
source collision library and output SHA-256 in `bow_manifest.json`. Missing bow
resources emit a clear runtime error, and release export preflight must require
this file rather than shipping the previous bow clips silently.

At runtime only the bow clips are remapped to existing Beyond Heroes clip
names. A two-part time mapping preserves the original gameplay release times
(0.350 seconds for a basic shot; 0.017 seconds for the charged release) and clip
durations. The body motions and source collision-corrected arm poses are kept.
Bows attach to `weapon.L`, as in the source; every equipped bow remains its
actual item model. Crossbows and other weapons keep their existing sockets.

Class models have fixed cosmetic outfits. Equipped weapons, gems, special item
effects and boss-set regalia remain dynamic. Custom hero retains body sliders,
hair and all fitted worn equipment. Missing model-choice data in an existing
save continues to select Custom hero. New hero selection starts with Class model.
