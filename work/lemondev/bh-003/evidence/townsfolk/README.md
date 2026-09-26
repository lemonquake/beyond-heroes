# Townsfolk models (builder D)

Nine civilian models, one module each in `tools/blender/characters/town_<id>.py`. The registry strips the `town_`
prefix: the registry key and GLB name are `<id>` (e.g. `town_elder.py` -> `elder` -> `game/assets/characters/elder.glb`).
Every model exports only the 6 `CLIPS_ONLY` clips (idle, idle_look, idle_adjust, interact_talk, walk,
interact_pickup). Every export printed "clip lengths verified (6 clips)" after the exporter fix.

Height = the highest vertex in the rest pose (hats and feathers included). Tintable = the share of the surface area
that uses `BH_Cloth_Primary` (exported without a palette suffix so the NPC `tint` colours it). Solidified cloth counts
both faces.

| key | glb | height (m) | tris | tintable (m², share) | notes |
|---|---|---|---|---|---|
| matron | matron.glb | 1.74 | 7 588 | 2.82, 56 % (dress + sleeves) | apron with bib, sleeves rolled up, indigo headscarf with a knot at the nape, keys and a pouch on the belt |
| smith | smith.glb | 1.82 | 6 636 | 1.66, 40 % (shirt + trousers) | leather apron is 39 %, nearly as large; bald, spade beard, bare forearms, gloves, hammer (R hip), tongs (L hip) |
| elder | elder.glb | 1.68 | 8 936 | 2.71, 53 % (long dress) | stooped (hump, head forward), two-layer shawl with a point at the back, grey braid, shell necklace, staff in the right hand |
| scholar | scholar.glb | 1.79 | 8 394 | 3.52, 57 % (robe) | wide sleeves, short cape + lowered hood, spectacles, trimmed beard, satchel with scrolls (R), book (L) |
| fisher | fisher.glb | 1.91 (hat) | 7 580 | 1.40, 33 % (vest + trousers) | wide conical hat (0.62 m across), bare chest and arms, net bundle over the L shoulder, sandals |
| merchant | merchant.glb | 1.79 | 7 662 | 2.19, 40 % (long over-vest) | portly, red sash, rolled cap, moustache, coin purse (R front), ledger (L hip) |
| officer | officer.glb | 1.77 | 9 950 | 2.30, 38 % (long coat) | steel breastplate, silver sash, short dark cape, gloves, tall boots, hair knot, sheathed sword on the L hip (on `hips`) |
| bard | bard.glb | 2.04 (feather) | 7 442 | 0.98, 27 % (doublet) | about 1.80 m to the cap; puffed sleeves, saffron scarf, beret with a feather, lute on the back |
| traveler | traveler.glb | 1.79 (hood) | 8 196 | 2.41, 39 % (cloak, mantle, hood) | hood up, torn cloak hem, scarf, pack + bedroll, wrapped boots |

Sheets: `<key>_rest.png` (T-pose, 4 views + gameplay iso camera), `<key>_idle_interact_talk_walk.png` (clips at 0 / 0.5),
`<key>_posed4.png` (idle pose, 4 views, closer camera, back-face culling on).

## Known issues
- The elder's staff is rigid to `hand.R`, not `weapon.R`. `weapon.R` is in `bh_skeleton.DEFORM_EXCLUDE`, so the
  Blender armature modifier ignores its vertex group. In a test the staff stayed in T-pose space. The staff is upright
  in idle. In interact_talk and walk it swings with the hand, and in interact_pickup it tips toward horizontal.
- Long skirts and robes (matron, elder, scholar) are weighted to hips, thighs and shins. In walk a heel can poke a few
  cm through the back hem. In interact_pickup the skirt deforms, but it stays closed.
- The shawls and capes (elder, scholar, officer, traveler) use chest/shoulder weights. When an arm reaches down they
  crease at the shoulder.
- The smith's apron and the officer's scabbard are rigid or skirt-weighted. No clipping large enough to see showed
  up in the previewed clips.
- Faces are simple (dark eye dots, a nose and a brow ridge). They are made to read at dialogue distance, not in
  close-up.
