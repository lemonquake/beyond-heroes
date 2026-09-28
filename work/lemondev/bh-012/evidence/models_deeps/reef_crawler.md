# Reef Crawler (`reef_crawler`)

- Script: `tools/blender/creatures/build_reef_crawler.py` (imports creature_kit_c + kit_deeps; no shared script edited)
- GLB: `game/assets/characters/reef_crawler.glb` + `.glb.import`
- Triangles: 11192; 38 bones (root non-deform); 9 materials `BH_*__reef_crawler`
- Size: 1.62 m wide (leg tips), 0.87 m tall (coral top), 1.29 m long (big pincer tip to rear)
- Clips (30 fps, in place): generic `idle(loop) idle_look walk(loop, 1.4 m/s) run(loop, 3.8) run_combat(loop, 3.4) hit_light hit_heavy stagger_small knockback death death_back alert`
  + `crab_snap` 0.8 s hits [0.367, 0.467] (right pincer jab + snap), `crab_slam` 1.4 s hits [0.8, 0.933] (both pincers hammer down),
  `crab_guard` 1.2 s no hits (pincers folded up in front of the face 0.3-0.9 s).
- creature_meta.json: merged `crab_snap / crab_slam / crab_guard` under `animations` and `models.reef_crawler` (same pattern as broodmother); diff vs the pre-merge copy: only those keys added, nothing else changed.
- Palette: drowned blue-grey shell, pale crust mottles and underside, barnacle white, bleached coral, kelp green, dark claw tips, teal BH_Emissive eyes + coral polyps. Right pincer 1.3x the left.

## Evidence
`reef_crawler_rest_iso.png` (5 views + gameplay iso 26 m), `reef_crawler_clips.png`. Godot: `logs/godot_check.txt`.

## Build log
```
[reef_crawler] numpy-vs-Blender pose check: worst bone head/tail error 0.000 mm
[reef_crawler] mesh 11192 tris, 6409 verts, 38 bones, 15 clips; rest bounds x -0.810..0.810 y -0.893..0.398 z 0.007..0.870
[reef_crawler] foot slip walk: max 12.23 mm/frame, mean 0.32, stance 0.58
[reef_crawler] foot slip run: max 0.00 mm/frame, mean 0.00, stance 0.42
[reef_crawler] foot slip run_combat: max 0.00 mm/frame, mean 0.00, stance 0.42
[reef_crawler] worst IK reach miss per clip (mm): idle 0.0, idle_look 0.0, walk 0.0, run 0.0, run_combat 0.0, hit_light 0.0, hit_heavy 0.0, stagger_small 0.0, knockback 0.0, death 7.9, death_back 9.5, alert 0.0, crab_snap 0.0, crab_slam 0.0, crab_guard 0.0
[compose] A:\Python\beyond-heroes\work\lemondev\bh-012\evidence\models_deeps\reef_crawler\reef_crawler_rest.png (2520, 510)
[compose] A:\Python\beyond-heroes\work\lemondev\bh-012\evidence\models_deeps\reef_crawler\reef_crawler_clips.png (1800, 1647)
[reef_crawler] meta merged -> A:\Python\beyond-heroes\game\assets\characters\creature_meta.json
[reef_crawler] -> A:\Python\beyond-heroes\game\assets\characters\reef_crawler.glb (1.93 MB)
[reef_crawler] check_lengths: 15 animations in the GLB; mismatches: []
[reef_crawler]   idle             want  3.000s got 3
[reef_crawler]   idle_look        want  2.500s got 2.5
[reef_crawler]   walk             want  0.733s got 0.7333333333333333
[reef_crawler]   run              want  0.400s got 0.4
[reef_crawler]   run_combat       want  0.400s got 0.4
[reef_crawler]   hit_light        want  0.400s got 0.4
[reef_crawler]   hit_heavy        want  0.600s got 0.6
[reef_crawler]   stagger_small    want  0.800s got 0.8
[reef_crawler]   knockback        want  0.900s got 0.9
[reef_crawler]   death            want  1.500s got 1.5
[reef_crawler]   death_back       want  1.500s got 1.5
[reef_crawler]   alert            want  1.000s got 1
[reef_crawler]   crab_snap        want  0.800s got 0.8
[reef_crawler]   crab_slam        want  1.400s got 1.4
[reef_crawler]   crab_guard       want  1.200s got 1.2
```

## Known limitations
- walk foot-slip metric max 12 mm/frame on one touchdown frame (mean 0.32 mm); run/run_combat 0.
- death / death_back legs curl in FK (IK reach not applied while curled, by design, 8-10 mm).
- Rig pivot/legs authored at 1/0.82 and scaled uniformly (SIZE constant) - edit SIZE to rescale.
