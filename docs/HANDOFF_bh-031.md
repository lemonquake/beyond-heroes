# bh-031 handoff: one body for everyone, the female figure, ID portraits

## The female figure (from `models/female_generic.obj`)

The scan (about 1M vertices, vertex colours, no rig, short arms) is not a second body. The hero body is fitted onto
it and stored as one more shape key, `female`, so everything that already works on the hero works on her too: every
clip, every worn piece, hair, beards, the face drawn by the skin shader and the creator's sliders.

- Pipeline: `tools/blender/hero/hero_female_src.py` (decimate in Blender) -> `hero_female.py` (plain Python, numpy +
  scipy): scale to 1.80 m, torso centred, arms straightened and stretched along the bone so the wrist lands on the
  rig's wrist (factor 1.37), legs onto the hero's leg line, then a shrink-wrap (8 rounds, the last ones unsmoothed).
  The head and fists keep the hero's shape (the face is drawn at fixed landmarks; every clip holds a weapon in a
  fist). The coarse chest could not hold the cups, so `hero_src.load()` refines the chest triangles and
  `hero_female.bust()` flattens the pectorals and lays round cups on top.
- `hero_shapes.FEMALE_FACE` softens the face through the face keys (narrower jaw, lighter brow, fuller lips).
- `HeroLook`: slider `female` (0..1, "Figure: Masculine / Feminine" on the creator's Body page), presets
  Shieldmaiden, Huntress, Matron; `HeroLook.feminize()`; random looks are women half the time. Optional save key.
- The skin shader draws a wrap top in the smallclothes colour (`top_wrap`, from the female weight).
- Clips: `fem_idle` (contrapposto), `fem_walk`, `fem_stroll`, `fem_run` (pelvis sway and turn, shoulders
  counter-turning, steps nearer one line, arms closer), layered over the hero's own clips in
  `hero_female_anims.py`. `CharacterVisual._loco_clip` picks `fem_*` for a look with female >= 0.5.
- All 119 worn models were rebuilt (`hero_wear.py -- all`) and carry the `female` key.

## Everyone on the hero body (`Persona`, `DataPersonas`)

- `Persona.apply(visual, persona)`: look, worn item bases (recoloured), boss collection, hand weapons, stance.
- `HeroWear` dyes: `cloth`, `trim` (dark cloth), `leather`, `metal`, `gold`. `HeroBody.layer_dye` gives the inner
  garment a linen-leaning shade and the legs a darker one (`inner` / `legs` override).
- **Townsfolk**: all 54 personas hand-authored in `DataPersonas.NPCS` (55 NPC entries; Ilsa appears twice). Sizes keep
  name plates right (`Npc._size()`).
- **Humanoid monsters**: 70 of them. Family templates (bandit, undead, cultist, corrupted, goblin, orc, ogre, beast,
  drowned, infernal, aether, wiresick, kharvenn, jade, gigas, construct) varied by id, plus per-monster clothes in
  `ENEMIES`. Bosses wear a boss collection (Morthar and Kethrax: Obsidian Oath; Ossric: Sunken Crown; Brakka:
  Dragonforge ...). Size comes from the old model's height (`OLD_HEIGHT`). Zarael families keep white glows.
  Not people, still on their own models (`NOT_PEOPLE`): golems and sentinels, fungal and thorn folk, the bloated
  abominations, the giants' spawn and heart, the wirewright constructs, the Jade Guardian.
- **Tempos**: the hero body, a face from their uid (pale, eyes lit in the class colour) and class garb in empty slots
  (`Persona.setup_tempo`, `tempo_equipment`). QuakeAllies keep their hero's own look.
- **Cutscenes**: `CutscenePlayer.actor()` and `legend()` route through `DataPersonas.for_model` / personas
  (`CutsceneActor.make_persona` copies the old model's `cs_*` clips onto the hero rig). Paul David and Kethrax look
  as they do in the world. Aljay and Roydo (flashback legends) keep their models.
- Multiplayer: the dyes travel in `appearance["dye"]` (no protocol change; older peers ignore the key).

### Cost

The worn pieces of a persona are baked into one skinned mesh (`HeroWear.merge`, shape keys applied, cached and shared
by every wearer of that outfit). 60 humanoid monsters on Ruined Forest, vsync off (`tests/tools/bench_bh031.tscn`):
old models 7.3-7.6 ms a frame, 1,272 draw calls; personas 8.6-8.9 ms, 1,577 draw calls (12.2 ms / 2,443 before the
merge). Setting up one monster costs about 5.5 ms against 2.4 ms on an old model.

## Portraits

- `PortraitStudio`: an ID shot (head and shoulders, key / rim / fill light, a warm vignette quad behind) rendered in
  its own SubViewport world. Needs the real renderer.
- `tests/tools/bake_portraits.tscn` bakes `assets/ui/portraits/npc/<id>.png` for every persona in `NPCS`;
  `Database` points every NPC's `portrait` there, so dialogue, shops and the Lape window use them. Re-bake after
  changing a townsperson, then `--import`.
- Player: `HeroData.id_pic` (optional save field), kept current by `IdPicture.refresh` when the look or worn gear
  changes. `ProfilePicture.portrait()` and the shared picture in multiplayer use the profile picture first, then the
  ID picture, then the class portrait. Save cards (`MainMenu.hero_picture`) show it; older saves get one rendered
  live. The official server sends it in each character's summary (`service.py _card_picture`, restart the server).

## Evidence and tests

`work/lemondev/bh-031/evidence/` (`capture_bh031.tscn --mode=female|walk`, `capture_bh031_people.tscn --mode=npcs|enemies`,
`capture_bh031_game.tscn --phase=town|monsters|cards`). Tests: `tests/unit/test_bh031.gd`.

## Notes

- A female look keeps the hero's skull and drawn face, softened by `FEMALE_FACE`; the scan's own face is not used.
- `game/assets/ui/portraits/*.svg` remain for the class portraits, Tempo legends and fallbacks.
